"""vnsynth: a small language for writing electronic music as code.

A song is a Python script that builds patterns with a compact mini-notation
and renders them through synthesizers, 1920s record samples and effects:

    from vnsynth import *
    s = Song(bpm=84, bars=16, key="A minor")
    s.chords("pad", "Am7 Fmaj7 C Gadd9", inst=shimmer_pad, bars_per_chord=2)
    s.notes("lead", MOTIFS["aron"], inst=glass_keys, octave=5, every=4)
    s.notes("bass", "a1 ~ ~ a1 ~ ~ e2 ~ | f1 ~ ~ f1 ~ ~ c2 ~", inst=sub_bass)
    s.drums("kick: x..x..x. | snare: ....x... | hat: .x.x.x.x", gain=0.6)
    s.sample("record", "april_showers_1921", start=31.0, length=4.0,
             at_bar=0, every=4, fx=["78rpm", "reverse"], gain=0.4)
    s.render("audio/morning.ogg")

Mini-notation (per bar, bars separated by `|`): note names with octave
(`a3`, `c#4`, `eb5`), `~` rest, `_` hold the previous note one step longer.
Steps divide the bar evenly. Scale degrees (`1`..`7`, `1'` one octave up,
`1,` one octave down) work against the song key; an accidental after the
degree shifts it (`7b`, `4#`), and `@n` is n semitones from the key root
(`@-1`, chromatic in any mode). `c4+e4+g4` plays several notes at once.
Drums use `x` hit, `X` accent, `.` rest (kick, softkick, snare, brush, clap,
rim, hat, openhat, shaker, tom, heartbeat, tick, wood, snap).

Samples: `fx` chains 78rpm, reverse, dreamy, telephone, far, lofi, glitch,
stutter, wobble, warble, pitch-5, stretch3, lp900/hp300/bp1200, tremolo4,
swell, fadeout, arch, crackle, gain0.5. `fit=4` stretches the processed
slice to exactly 4 bars so it locks in as a loop; `at_bar` may be a list.

Per-track processing: `s.fx(name, lp=, hp=, sweep_lp=[(bar, hz), ...],
tremolo=(rate, depth), autopan=rate, crush=True, width=)`. Raw signals go in
with `s.add(name, signal, t)`.

Mixdown (`render`) carves a pocket for the game's machine voices (a dip
around 1.9 and 3.2 kHz, a soft top end) and normalises every cue to the same
loudness (`loudness=-18` dBFS), with a loop-safe peak limiter.

Rendering makes seamless loops: the tail (reverb and delay) is folded back
onto the start, so a cue loops without a click or a dropout.
"""

import math
import os
import shutil
import subprocess
import tempfile
import wave

import numpy as np

SR = 32000
HERE = os.path.dirname(os.path.abspath(__file__))
SAMPLE_DIR = os.path.join(HERE, "samples")
BUILD_DIR = os.path.join(HERE, "build")
RNG = np.random.default_rng(1)

NOTE_INDEX = {"c": 0, "d": 2, "e": 4, "f": 5, "g": 7, "a": 9, "b": 11}
SCALES = {"major": [0, 2, 4, 5, 7, 9, 11], "minor": [0, 2, 3, 5, 7, 8, 10],
          "dorian": [0, 2, 3, 5, 7, 9, 10], "lydian": [0, 2, 4, 6, 7, 9, 11],
          "mixolydian": [0, 2, 4, 5, 7, 9, 10], "phrygian": [0, 1, 3, 5, 7, 8, 10]}
CHORD_SHAPES = {"": [0, 4, 7], "m": [0, 3, 7], "7": [0, 4, 7, 10], "maj7": [0, 4, 7, 11],
                "m7": [0, 3, 7, 10], "sus2": [0, 2, 7], "sus4": [0, 5, 7], "add9": [0, 4, 7, 14],
                "madd9": [0, 3, 7, 14], "dim": [0, 3, 6], "m9": [0, 3, 7, 10, 14],
                "maj9": [0, 4, 7, 11, 14], "6": [0, 4, 7, 9], "m6": [0, 3, 7, 9],
                "maj7#11": [0, 4, 7, 11, 18], "m11": [0, 3, 7, 10, 17], "7sus4": [0, 5, 7, 10], "aug": [0, 4, 8],
                "m7b5": [0, 3, 6, 10], "5": [0, 7, 12], "6add9": [0, 4, 7, 9, 14], "mmaj7": [0, 3, 7, 11],
                "sus2add11": [0, 2, 7, 17], "add11": [0, 4, 7, 17]}


def midi_to_hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def parse_note(tok, key_root=57, scale=None):
    """'a3' -> MIDI; scale degrees '1'..'7' with ' (up) and , (down)."""
    tok = tok.strip()
    octv = tok.count("'") - tok.count(",")
    if tok[0] == "@":      # @-3 = three semitones below the key root (mode-free, chromatic)
        return key_root + int(tok[1:].rstrip("',")) + 12 * octv
    if tok[0].isdigit():   # scale degree, optional accidental after it: 7b, 4#, 6b,
        deg = int(tok[0]) - 1
        acc = tok[1:].count("#") - tok[1:].count("b")
        sc = scale or SCALES["minor"]
        return key_root + sc[deg % 7] + 12 * (deg // 7 + octv) + acc
    name = tok[0].lower()
    i = 1
    acc = 0
    while i < len(tok) and tok[i] in "#b":
        acc += 1 if tok[i] == "#" else -1
        i += 1
    octave = int(tok[i:]) if i < len(tok) else 4
    return 12 * (octave + 1) + NOTE_INDEX[name] + acc


def parse_chord(tok, octave=3):
    root = tok[0].upper()
    i = 1
    acc = 0
    while i < len(tok) and tok[i] in "#b":
        acc += 1 if tok[i] == "#" else -1
        i += 1
    shape = tok[i:]
    base = 12 * (octave + 1) + NOTE_INDEX[root.lower()] + acc
    return [base + iv for iv in CHORD_SHAPES.get(shape, CHORD_SHAPES[""])]


# ---------------------------------------------------------------- oscillators

def t_axis(n):
    return np.arange(n) / SR


def osc(kind, freq, n, phase=0.0, detune_cents=0.0):
    f = freq * 2 ** (detune_cents / 1200)
    ph = (phase + f * t_axis(n)) % 1.0
    if kind == "sine":
        return np.sin(2 * np.pi * ph)
    if kind == "tri":
        return 4 * np.abs(ph - 0.5) - 1
    if kind == "square":
        return np.where(ph < 0.5, 1.0, -1.0) * 0.7
    if kind == "saw":
        # gently band-limited: fewer partials up high (wavetable, same sound as
        # summing the partials but O(n))
        harmonics = max(1, min(24, int(SR / 2.5 / max(f, 1))))
        tab = _saw_table(harmonics)
        ph = (phase / (2 * np.pi) + f * t_axis(n)) % 1.0
        return np.interp(ph * _TAB_N, _TAB_X, tab) * 0.6
    raise ValueError(kind)


_TAB_N = 4096
_TAB_X = np.arange(_TAB_N + 1)
_saw_tables = {}


def _saw_table(harmonics):
    if harmonics not in _saw_tables:
        p = np.arange(_TAB_N + 1) / _TAB_N
        _saw_tables[harmonics] = sum(np.sin(2 * np.pi * k * p) / k for k in range(1, harmonics + 1))
    return _saw_tables[harmonics]


def adsr(n, a=0.01, d=0.1, s=0.7, r=0.2, hold=None):
    """Envelope n samples long; `hold` = seconds before release."""
    hold = (n / SR - r) if hold is None else hold
    t = t_axis(n)
    env = np.where(t < a, t / max(a, 1e-4), 1.0)
    env = np.where((t >= a) & (t < a + d), 1 - (1 - s) * (t - a) / max(d, 1e-4), env)
    env = np.where((t >= a + d) & (t < hold), s, env)
    rel = np.clip(1 - (t - hold) / max(r, 1e-4), 0, 1) * s
    return np.where(t >= hold, rel, env)


# ---------------------------------------------------------------- filters

def biquad(x, kind, freq, q=0.707, gain_db=0.0):
    w = 2 * np.pi * min(freq, SR * 0.45) / SR
    alpha = np.sin(w) / (2 * q)
    cw = np.cos(w)
    if kind == "lp":
        b = [(1 - cw) / 2, 1 - cw, (1 - cw) / 2]
        a = [1 + alpha, -2 * cw, 1 - alpha]
    elif kind == "hp":
        b = [(1 + cw) / 2, -(1 + cw), (1 + cw) / 2]
        a = [1 + alpha, -2 * cw, 1 - alpha]
    elif kind == "bp":
        b = [alpha, 0, -alpha]
        a = [1 + alpha, -2 * cw, 1 - alpha]
    elif kind == "peak":
        A = 10 ** (gain_db / 40)
        b = [1 + alpha * A, -2 * cw, 1 - alpha * A]
        a = [1 + alpha / A, -2 * cw, 1 - alpha / A]
    elif kind in ("lowshelf", "highshelf"):
        A = 10 ** (gain_db / 40)
        sq = 2 * np.sqrt(A) * alpha
        if kind == "lowshelf":
            b = [A * ((A + 1) - (A - 1) * cw + sq), 2 * A * ((A - 1) - (A + 1) * cw), A * ((A + 1) - (A - 1) * cw - sq)]
            a = [(A + 1) + (A - 1) * cw + sq, -2 * ((A - 1) + (A + 1) * cw), (A + 1) + (A - 1) * cw - sq]
        else:
            b = [A * ((A + 1) + (A - 1) * cw + sq), -2 * A * ((A - 1) + (A + 1) * cw), A * ((A + 1) + (A - 1) * cw - sq)]
            a = [(A + 1) - (A - 1) * cw + sq, 2 * ((A - 1) - (A + 1) * cw), (A + 1) - (A - 1) * cw - sq]
    else:
        raise ValueError(kind)
    b = np.array(b) / a[0]
    a = np.array(a) / a[0]
    return _iir(x, b, a)


def _iir(x, b, a):
    try:
        from scipy.signal import lfilter
        return lfilter(b, a, x, axis=0)
    except ImportError:
        y = np.zeros_like(x)
        x1 = x2 = y1 = y2 = 0.0
        for i in range(len(x)):
            y0 = b[0] * x[i] + b[1] * x1 + b[2] * x2 - a[1] * y1 - a[2] * y2
            x2, x1, y2, y1 = x1, x[i], y1, y0
            y[i] = y0
        return y


def lowpass(x, f, q=0.707):
    return biquad(x, "lp", f, q)


def highpass(x, f, q=0.707):
    return biquad(x, "hp", f, q)


def bandpass(x, f, q=1.0):
    return biquad(x, "bp", f, q)


def sweep(x, kind, freqs, q=0.707, block=256):
    """Time-varying filter: `freqs` is an array (one cutoff per sample, or any
    length - it is resampled). Filtered block by block with carried state."""
    from scipy.signal import lfilter
    n = len(x)
    freqs = np.interp(np.linspace(0, len(freqs) - 1, n), np.arange(len(freqs)), freqs)
    y = np.zeros_like(x)
    zi = None
    for a0 in range(0, n, block):
        seg = x[a0:a0 + block]
        f = freqs[min(n - 1, a0 + block // 2)]
        w = 2 * np.pi * min(f, SR * 0.45) / SR
        alpha = np.sin(w) / (2 * q)
        cw = np.cos(w)
        if kind == "lp":
            b = np.array([(1 - cw) / 2, 1 - cw, (1 - cw) / 2])
        elif kind == "hp":
            b = np.array([(1 + cw) / 2, -(1 + cw), (1 + cw) / 2])
        else:
            b = np.array([alpha, 0, -alpha])
        a = np.array([1 + alpha, -2 * cw, 1 - alpha])
        b, a = b / a[0], a / a[0]
        if zi is None:
            zi = np.zeros((2,) + seg.shape[1:])
        y[a0:a0 + block], zi = lfilter(b, a, seg, axis=0, zi=zi)
    return y


# ---------------------------------------------------------------- instruments
# Each instrument: f(freq, dur_seconds, vel) -> mono numpy array (may be
# longer than dur: the release rings out).

def shimmer_pad(freq, dur, vel=1.0):
    n = int((dur + 1.6) * SR)
    s = sum(osc("saw", freq, n, phase=RNG.random(), detune_cents=c) for c in (-14, -6, 0, 7, 15))
    s += 0.4 * osc("saw", freq * 2, n, detune_cents=4)
    s = lowpass(lowpass(s, 1200 + 400 * vel, 0.9), 2600, 0.7)
    lfo = 1 + 0.25 * np.sin(2 * np.pi * 0.23 * t_axis(n))
    return s * adsr(n, 0.9, 0.5, 0.75, 1.5, hold=dur) * lfo * 0.10 * vel


def warm_pad(freq, dur, vel=1.0):
    n = int((dur + 1.2) * SR)
    s = osc("tri", freq, n) + 0.5 * osc("tri", freq * 1.002, n) + 0.3 * osc("sine", freq / 2, n)
    s = lowpass(s, 1100, 0.7)
    return s * adsr(n, 0.6, 0.4, 0.8, 1.1, hold=dur) * 0.20 * vel


def dream_guitar(freq, dur, vel=1.0):
    """Karplus-Strong pluck, chorused later by the mix: the dream-pop guitar."""
    n = int((dur + 2.0) * SR)
    period = max(2, int(SR / freq))
    buf = RNG.uniform(-1, 1, period)
    k = max(2, period // 5)                     # a soft thumb pluck, not a pick: smooth the excitation
    buf = np.convolve(np.concatenate([buf, buf[:k]]), np.ones(k) / k, "valid")[:period] * 2.2
    out = np.zeros(n)
    for i in range(0, n, period):
        seg = buf[: min(period, n - i)]
        out[i:i + len(seg)] = seg
        buf = 0.497 * (buf + np.roll(buf, 1))
    out = lowpass(out, min(2200, freq * 5), 0.6)
    return out * adsr(n, 0.004, 0.3, 0.6, 1.5, hold=dur + 0.5) * 1.2 * vel


def glass_keys(freq, dur, vel=1.0):
    """FM bell / electric piano."""
    n = int((dur + 1.8) * SR)
    t = t_axis(n)
    idx = 1.3 * np.exp(-t * 3.5) + 0.15
    s = np.sin(2 * np.pi * freq * t + idx * np.sin(2 * np.pi * freq * 3.5 * t))
    s += 0.25 * np.sin(2 * np.pi * freq * 2 * t)
    s = lowpass(s, 2400, 0.7)
    return s * np.exp(-t * 1.6) * adsr(n, 0.004, 0.1, 1.0, 0.4, hold=dur + 1.2) * 0.22 * vel


def music_box(freq, dur, vel=1.0):
    n = int((dur + 1.5) * SR)
    t = t_axis(n)
    s = np.sin(2 * np.pi * freq * t) + 0.4 * np.sin(2 * np.pi * freq * 4.1 * t) * np.exp(-t * 8)
    return s * np.exp(-t * 2.8) * np.clip(t / 0.003, 0, 1) * 0.28 * vel


def soft_lead(freq, dur, vel=1.0):
    n = int((dur + 0.6) * SR)
    t = t_axis(n)
    vib = 1 + 0.006 * np.sin(2 * np.pi * 5.2 * t) * np.clip(t / 0.4, 0, 1)
    ph = np.cumsum(freq * vib) / SR
    s = np.where(ph % 1 < 0.42, 1.0, -1.0) + 0.6 * np.sin(2 * np.pi * ph)
    s = lowpass(s, 2200, 0.8)
    return s * adsr(n, 0.05, 0.2, 0.7, 0.5, hold=dur) * 0.09 * vel


def choir(freq, dur, vel=1.0):
    """Wordless 'ooh': a buzz through dark vowel formants (kept below the game's voices)."""
    n = int((dur + 1.5) * SR)
    src = sum(osc("saw", freq, n, detune_cents=c) for c in (-8, 0, 9))
    s = bandpass(src, 420, 3) + 0.6 * bandpass(src, 850, 4) + 0.08 * bandpass(src, 2400, 6)
    return s * adsr(n, 0.8, 0.3, 0.8, 1.4, hold=dur) * 0.22 * vel


def sub_bass(freq, dur, vel=1.0):
    n = int((dur + 0.15) * SR)
    s = osc("sine", freq, n) + 0.25 * osc("tri", freq * 2, n)
    return s * adsr(n, 0.006, 0.08, 0.85, 0.12, hold=dur) * 0.27 * vel


def acid_bass(freq, dur, vel=1.0):
    n = int((dur + 0.1) * SR)
    t = t_axis(n)
    s = osc("saw", freq, n)
    # moving filter: one sweep per note
    out = np.zeros(n)
    blocks = 8
    for k in range(blocks):
        a, b = k * n // blocks, (k + 1) * n // blocks
        out[a:b] = lowpass(s[a:b], 300 + 1400 * np.exp(-3 * k / blocks) * vel, 3.0)[: b - a]
    return np.tanh(out * 1.5) * adsr(n, 0.003, 0.15, 0.5, 0.06, hold=dur) * 0.22


def arp_pluck(freq, dur, vel=1.0):
    n = int((dur + 0.5) * SR)
    t = t_axis(n)
    s = osc("square", freq, n) * 0.5 + osc("saw", freq * 1.003, n) * 0.5
    s = lowpass(s, 900 + 2600 * np.exp(-t * 9).mean(), 1.2)
    return s * np.exp(-t * 7) * 0.55 * vel


def vocal_chop(freq, dur, vel=1.0):
    """A pitched breathy 'ooh' for dream-pop hooks."""
    n = int((dur + 0.8) * SR)
    src = osc("saw", freq, n) + RNG.normal(0, 0.3, n)
    s = bandpass(src, 420, 5) + 0.8 * bandpass(src, 900, 6)
    return s * adsr(n, 0.04, 0.2, 0.6, 0.6, hold=dur) * 0.55 * vel


def felt_piano(freq, dur, vel=1.0):
    """A soft, close-miked felt piano: inharmonic partials, dark, damped on release."""
    n = int((dur + 1.2) * SR)
    t = t_axis(n)
    B = 0.0004
    s = np.zeros(n)
    for k in range(1, 9):
        fk = freq * k * math.sqrt(1 + B * k * k)
        if fk > 5000:
            break
        s += np.sin(2 * np.pi * fk * t + k) * (1 / k ** 1.6) * np.exp(-t * (0.9 + 0.7 * k) * (freq / 440) ** 0.3)
    att = np.clip(t / 0.006, 0, 1)
    return s * att * adsr(n, 0.001, 0.0, 1.0, 0.45, hold=dur + 0.1) * 0.24 * vel


def mallet(freq, dur, vel=1.0):
    """Clean vibraphone: pure bar partials, soft motor tremolo."""
    n = int((dur + 2.0) * SR)
    t = t_axis(n)
    s = np.sin(2 * np.pi * freq * t) * np.exp(-t * 1.1)
    s += 0.25 * np.sin(2 * np.pi * freq * 3.98 * t) * np.exp(-t * 5)
    s += 0.06 * np.sin(2 * np.pi * freq * 9.9 * t) * np.exp(-t * 14)
    trem = 1 - 0.18 * (1 - np.cos(2 * np.pi * 4.6 * t)) / 2
    return s * trem * np.clip(t / 0.002, 0, 1) * adsr(n, 0.001, 0, 1, 0.8, hold=dur + 1.0) * 0.24 * vel


def flute(freq, dur, vel=1.0):
    """Breathy, round lead that sits under the voice band."""
    n = int((dur + 0.5) * SR)
    t = t_axis(n)
    vib = 1 + 0.005 * np.sin(2 * np.pi * 4.8 * t) * np.clip((t - 0.25) / 0.5, 0, 1)
    ph = np.cumsum(freq * vib) / SR
    s = np.sin(2 * np.pi * ph) + 0.18 * np.sin(4 * np.pi * ph) + 0.05 * np.sin(6 * np.pi * ph)
    breath = bandpass(RNG.normal(0, 1, n), min(freq * 2, 5000), 2.0) * 0.18
    return (s + breath) * adsr(n, 0.09, 0.2, 0.85, 0.35, hold=dur) * 0.16 * vel


def strings(freq, dur, vel=1.0):
    """A slow string ensemble: detuned saws, soft attack, gentle vibrato."""
    n = int((dur + 1.4) * SR)
    t = t_axis(n)
    s = sum(osc("saw", freq, n, phase=RNG.random() * 6, detune_cents=c) for c in (-9, -3, 4, 10))
    s = lowpass(s, 1400 + 300 * vel, 0.6)
    s = lowpass(s, 2200, 0.7)
    return s * adsr(n, 0.5, 0.3, 0.85, 1.2, hold=dur) * 0.105 * vel


def soft_brass(freq, dur, vel=1.0):
    """Muted horn section: a saw whose filter opens with the swell."""
    n = int((dur + 0.5) * SR)
    t = t_axis(n)
    s = osc("saw", freq, n, detune_cents=-5) + osc("saw", freq, n, detune_cents=6)
    cut = 350 + 900 * np.clip(t / 0.18, 0, 1) * np.exp(-t * 0.8) + 200
    s = sweep(s, "lp", cut[::64], 0.9)
    return s * adsr(n, 0.06, 0.25, 0.75, 0.3, hold=dur) * 0.155 * vel


def deep_drone(freq, dur, vel=1.0):
    """Vast, slow drone: root, fifth and sub through a breathing filter."""
    n = int((dur + 3.0) * SR)
    t = t_axis(n)
    s = osc("saw", freq, n, detune_cents=-4) + osc("saw", freq, n, detune_cents=5) + 0.6 * osc("saw", freq * 1.4983, n)
    s += 1.2 * osc("sine", freq / 2, n)
    lfo = 260 + 220 * (1 - np.cos(2 * np.pi * 0.07 * t + RNG.random() * 6)) / 2
    s = sweep(s, "lp", lfo[::256], 1.1)
    return s * adsr(n, 2.5, 1.0, 0.9, 3.0, hold=dur) * 0.14 * vel


def organ(freq, dur, vel=1.0):
    """Soft drawbar organ with a slow rotary shimmer."""
    n = int((dur + 1.0) * SR)
    t = t_axis(n)
    rot = 1 + 0.002 * np.sin(2 * np.pi * 0.8 * t)
    ph = np.cumsum(freq * rot) / SR
    s = np.sin(2 * np.pi * ph) + 0.5 * np.sin(4 * np.pi * ph) + 0.25 * np.sin(6 * np.pi * ph) + 0.4 * np.sin(np.pi * ph)
    return s * (1 + 0.1 * np.sin(2 * np.pi * 6.2 * t)) * adsr(n, 0.15, 0.2, 0.9, 0.9, hold=dur) * 0.10 * vel


def pulse_blip(freq, dur, vel=1.0):
    """The System: a soft, exact sine ping with a small square edge."""
    n = int(0.6 * SR)
    t = t_axis(n)
    s = np.sin(2 * np.pi * freq * t) + 0.15 * osc("square", freq, n) * np.exp(-t * 40)
    s = lowpass(s, 2500)
    return s * np.exp(-t * 9) * np.clip(t / 0.002, 0, 1) * 0.35 * vel


def round_bass(freq, dur, vel=1.0):
    """Plucked electric bass, warm, short filter decay."""
    n = int((dur + 0.2) * SR)
    t = t_axis(n)
    s = osc("saw", freq, n) * 0.6 + osc("sine", freq, n)
    cut = 250 + 900 * np.exp(-t * 12)
    s = sweep(s, "lp", cut[::128], 0.8)
    return s * adsr(n, 0.004, 0.2, 0.65, 0.12, hold=dur) * 0.27 * vel


def glass_harmonica(freq, dur, vel=1.0):
    """Bowed glass: slow-blooming pure partials, cold and radiant."""
    n = int((dur + 2.2) * SR)
    t = t_axis(n)
    s = np.sin(2 * np.pi * freq * t) + 0.3 * np.sin(2 * np.pi * freq * 2.004 * t) + 0.12 * np.sin(2 * np.pi * freq * 3.01 * t)
    s *= 1 + 0.08 * np.sin(2 * np.pi * 3.1 * t)
    return s * adsr(n, 0.35, 0.3, 0.8, 1.8, hold=dur) * 0.14 * vel


INSTRUMENTS = {f.__name__: f for f in (shimmer_pad, warm_pad, dream_guitar, glass_keys, music_box,
                                       soft_lead, choir, sub_bass, acid_bass, arp_pluck, vocal_chop,
                                       felt_piano, mallet, flute, strings, soft_brass, deep_drone, organ,
                                       pulse_blip, round_bass, glass_harmonica)}


# ---------------------------------------------------------------- drums

def drum(kind, vel=1.0):
    if kind == "kick":
        n = int(0.45 * SR)
        t = t_axis(n)
        f = 48 + 120 * np.exp(-t * 28)
        s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7)
        return np.tanh(s * 1.6) * 0.75 * vel
    if kind == "snare":
        n = int(0.35 * SR)
        t = t_axis(n)
        s = lowpass(highpass(RNG.normal(0, 1, n), 1500), 7000) * np.exp(-t * 14) * 0.5
        s += np.sin(2 * np.pi * 190 * t) * np.exp(-t * 22) * 0.5
        return s * 0.6 * vel
    if kind == "clap":
        n = int(0.3 * SR)
        t = t_axis(n)
        bursts = sum(np.where((t > o) & (t < o + 0.01), 1.0, 0.0) for o in (0, 0.012, 0.024))
        s = bandpass(RNG.normal(0, 1, n), 1200, 1.2) * (bursts + np.exp(-t * 18) * (t > 0.024))
        return s * 0.5 * vel
    if kind == "hat":
        n = int(0.08 * SR)
        t = t_axis(n)
        return lowpass(highpass(RNG.normal(0, 1, n), 6500), 8500) * np.exp(-t * 60) * 0.2 * vel
    if kind == "openhat":
        n = int(0.35 * SR)
        t = t_axis(n)
        return lowpass(highpass(RNG.normal(0, 1, n), 6000), 8500) * np.exp(-t * 9) * 0.14 * vel
    if kind == "softkick":    # round, felted kick for the slow cues
        n = int(0.5 * SR)
        t = t_axis(n)
        f = 44 + 70 * np.exp(-t * 22)
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 6) * np.clip(t / 0.003, 0, 1) * 0.7 * vel
    if kind == "brush":       # a brushed snare swish
        n = int(0.28 * SR)
        t = t_axis(n)
        return lowpass(bandpass(RNG.normal(0, 1, n), 4500, 0.7), 7000) * np.sin(np.pi * np.clip(t / 0.28, 0, 1)) ** 0.5 \
            * np.exp(-t * 9) * 0.7 * vel
    if kind == "heartbeat":   # lub-dub
        n = int(0.7 * SR)
        t = t_axis(n)
        beat = lambda t0, a: np.where(t >= t0, np.sin(2 * np.pi * (52 + 30 * np.exp(-(t - t0) * 30)) * (t - t0))
                                      * np.exp(-(t - t0) * 16) * a, 0)
        return np.tanh(2 * (beat(0, 1.0) + beat(0.22, 0.7))) * 0.75 * vel
    if kind == "tick":        # a quiet clock tick
        n = int(0.05 * SR)
        t = t_axis(n)
        return (bandpass(RNG.normal(0, 1, n), 4800, 4) * 0.7 + 0.5 * np.sin(2 * np.pi * 1250 * t)) * np.exp(-t * 160) \
            * np.clip(t / 0.0008, 0, 1) * 0.24 * vel
    if kind == "wood":        # woodblock
        n = int(0.12 * SR)
        t = t_axis(n)
        return (np.sin(2 * np.pi * 820 * t) + 0.4 * np.sin(2 * np.pi * 1310 * t)) * np.exp(-t * 45) * 0.28 * vel
    if kind == "snap":
        n = int(0.15 * SR)
        t = t_axis(n)
        return bandpass(RNG.normal(0, 1, n), 3800, 2) * np.exp(-t * 40) * 0.45 * vel
    if kind == "rim":
        n = int(0.06 * SR)
        t = t_axis(n)
        return (bandpass(RNG.normal(0, 1, n), 4200, 3) * 0.6 + np.sin(2 * np.pi * 820 * t)) * np.exp(-t * 70) * 0.3 * vel
    if kind == "shaker":
        n = int(0.1 * SR)
        t = t_axis(n)
        return lowpass(highpass(RNG.normal(0, 1, n), 5000), 8000) * np.sin(np.pi * t / 0.1) * 0.12 * vel
    if kind == "tom":
        n = int(0.4 * SR)
        t = t_axis(n)
        f = 110 + 60 * np.exp(-t * 15)
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 8) * 0.5 * vel
    raise ValueError(kind)


# ---------------------------------------------------------------- samples

_sample_cache = {}


def load_sample(name):
    """A 1920s recording from examples/music/samples (decoded with ffmpeg)."""
    if name in _sample_cache:
        return _sample_cache[name]
    path = None
    for ext in (".flac", ".ogg", ".wav"):
        p = os.path.join(SAMPLE_DIR, name + ext)
        if os.path.exists(p):
            path = p
            break
    if path is None:
        raise FileNotFoundError(f"sample {name} not in {SAMPLE_DIR}")
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "s16le", "-ac", "1", "-ar", str(SR), "-"],
                       capture_output=True, check=True)
    data = np.frombuffer(r.stdout, "<i2").astype(np.float64) / 32768
    _sample_cache[name] = data
    return data


_flux_cache = {}


def _flux(name):
    """Onset strength of a recording, 200 frames per second."""
    if name not in _flux_cache:
        x = load_sample(name)
        hop = SR // 200
        frames = len(x) // hop - 4
        idx = np.arange(frames)[:, None] * hop + np.arange(4 * hop)[None, :]
        spec = np.abs(np.fft.rfft(x[idx] * np.hanning(4 * hop), axis=1))
        f = np.maximum(0, np.diff(np.log1p(spec * 30), axis=0)).sum(1)
        _flux_cache[name] = np.concatenate([[0], f])
    return _flux_cache[name]


def snap(name, t, search=0.5):
    """The strongest note onset in a recording within `search` s after t, so
    a slice starts on a beat instead of mid-note."""
    f = _flux(name)
    a = int(t * 200)
    return (a + int(np.argmax(f[a:a + int(search * 200)]))) / 200


def beat_period(name, t, span=8.0, lo=80, hi=240):
    """Local beat length (seconds) of a recording around t, from the
    autocorrelation of its onsets, searched between lo and hi BPM."""
    f = _flux(name)[int(t * 200):int((t + span) * 200)]
    f = f - f.mean()
    ac = np.correlate(f, f, "full")[len(f) - 1:]
    lags = np.arange(len(ac)) / 200
    ok = (lags > 60 / hi) & (lags < 60 / lo)
    return float(lags[ok][np.argmax(ac[ok])])


def sample_fx(x, fx):
    for f in fx or ():
        if f == "78rpm":       # the narrow, crackly band of a shellac record
            # band-limited like shellac, but centred low so it stays out of the voices' formants
            x = biquad(lowpass(highpass(x, 260, 0.8), 2400, 0.9), "peak", 1900, 0.9, -5.0) * 1.4
            x = x + lowpass(RNG.normal(0, 0.004, len(x)) + (RNG.random(len(x)) < 0.0008) * RNG.normal(0, 0.1, len(x)),
                            2800)
        elif f == "reverse":
            x = x[::-1].copy()
        elif f == "dreamy":    # smeared and dark, like a memory
            x = lowpass(x, 1800, 0.6)
        elif f == "telephone":
            x = lowpass(bandpass(x, 850, 1.3), 2000) * 2.2
        elif f.startswith("pitch"):   # pitch-7 = down a fifth, pitch+12 = octave up
            semis = float(f[5:])
            ratio = 2 ** (semis / 12)
            idx = np.arange(0, len(x) - 1, ratio)
            x = np.interp(idx, np.arange(len(x)), x)
        elif f.startswith("stretch"):  # granular time stretch, e.g. stretch2 = twice as long
            factor = float(f[7:])
            x = granular_stretch(x, factor)
        elif f == "stutter":
            g = int(0.09 * SR)
            x = np.concatenate([x[:g]] * 4 + [x])
        elif f == "wobble":    # tape wow
            t = t_axis(len(x))
            idx = np.clip(np.arange(len(x)) + 60 * np.sin(2 * np.pi * 0.6 * t), 0, len(x) - 1)
            x = np.interp(idx, np.arange(len(x)), x)
        elif f == "warble":    # deeper, slower, seasick tape
            t = t_axis(len(x))
            idx = np.clip(np.arange(len(x)) + 160 * np.sin(2 * np.pi * 0.27 * t) + 40 * np.sin(2 * np.pi * 1.3 * t),
                          0, len(x) - 1)
            x = np.interp(idx, np.arange(len(x)), x)
        elif f[:2] in ("lp", "hp", "bp") and f[2:].isdigit():   # lp900, hp300, bp1200
            x = biquad(x, f[:2], float(f[2:]), 0.707 if f[:2] != "bp" else 0.9)
        elif f == "lofi":      # sample-rate and bit reduction, then smoothed
            hold = 4
            x = np.repeat(x[::hold], hold)[:len(x)]
            x = np.round(x * 96) / 96
            x = lowpass(x, 3800, 0.6)
        elif f == "glitch":    # buffer stutters, skips and reversed grains
            x = glitch(x)
        elif f.startswith("tremolo"):
            rate = float(f[7:] or 4)
            x = x * (0.6 + 0.4 * np.sin(2 * np.pi * rate * t_axis(len(x))))
        elif f == "swell":     # rises out of nothing
            x = x * np.sin(np.linspace(0, np.pi / 2, len(x))) ** 2
        elif f == "fadeout":
            x = x * np.cos(np.linspace(0, np.pi / 2, len(x))) ** 2
        elif f == "arch":      # in and out like a breath
            x = x * np.sin(np.linspace(0, np.pi, len(x)))
        elif f == "crackle":
            x = x + lowpass(RNG.normal(0, 0.003, len(x)) + (RNG.random(len(x)) < 0.0012) * RNG.normal(0, 0.08, len(x)),
                            2800)
        elif f == "far":       # very distant, another room
            x = lowpass(highpass(x, 350), 1600) * 1.3
        elif f.startswith("gain"):
            x = x * float(f[4:])
    return x


def glitch(x, seed=3):
    rng = np.random.default_rng(seed + len(x) % 97)
    out = []
    i = 0
    while i < len(x):
        g = int(rng.uniform(0.04, 0.16) * SR)
        seg = x[i:i + g].copy()
        r = rng.random()
        if r < 0.22:            # stutter
            seg = np.concatenate([seg[: g // 3]] * int(rng.integers(2, 5)))
        elif r < 0.32:
            seg = seg[::-1]
        elif r < 0.40:
            seg = seg * 0
        f = min(64, len(seg) // 4)
        if f > 1:
            seg[:f] *= np.linspace(0, 1, f)
            seg[-f:] *= np.linspace(1, 0, f)
        out.append(seg)
        i += g
    return np.concatenate(out)[: len(x) * 2]


def granular_stretch(x, factor, grain=0.12):
    g = int(grain * SR)
    hop_out = g // 4
    hop_in = hop_out / factor
    win = np.hanning(g)
    n_out = int(len(x) * factor) + g
    out = np.zeros(n_out)
    pos_in = 0.0
    pos_out = 0
    while pos_out + g < n_out and int(pos_in) + g < len(x):
        jitter = int(RNG.integers(-g // 8, g // 8 + 1))
        a = int(np.clip(pos_in + jitter, 0, len(x) - g))
        out[pos_out:pos_out + g] += x[a:a + g] * win
        pos_in += hop_in
        pos_out += hop_out
    return out * 0.5


# ---------------------------------------------------------------- effects

def chorus(x, depth=0.003, rate=0.6, mix=0.5):
    n = len(x)
    t = t_axis(n)
    d = (depth * SR) * (1 + np.sin(2 * np.pi * rate * t)) / 2 + 20
    idx = np.arange(n) - d
    wet = np.interp(np.clip(idx, 0, n - 1), np.arange(n), x)
    return x * (1 - mix) + wet * mix


def make_ir(seconds=4.0, bright=0.5, seed=7):
    rng = np.random.default_rng(seed)
    n = int(seconds * SR)
    t = t_axis(n)
    env = np.exp(-t * 6.9 / seconds)
    ir = np.stack([rng.normal(0, 1, n), rng.normal(0, 1, n)], 1) * env[:, None]
    ir[:, 0] = lowpass(ir[:, 0], 2000 + 6000 * bright)
    ir[:, 1] = lowpass(ir[:, 1], 2000 + 6000 * bright)
    ir[: int(0.012 * SR)] *= np.linspace(0, 1, int(0.012 * SR))[:, None]
    return ir / np.sqrt((ir ** 2).sum(0)).max() * 3


def convolve(x, ir):
    """FFT convolution of a mono/stereo signal with a stereo IR."""
    n = len(x) + len(ir) - 1
    size = 1 << (n - 1).bit_length()
    if x.ndim == 1:
        x = np.stack([x, x], 1)
    out = np.zeros((n, 2))
    for c in range(2):
        X = np.fft.rfft(x[:, c], size)
        I = np.fft.rfft(ir[:, c], size)
        out[:, c] = np.fft.irfft(X * I, size)[:n]
    return out


def pingpong(x, time, feedback=0.45, mix=0.35, tone=3000):
    if x.ndim == 1:
        x = np.stack([x, x], 1)
    d = int(time * SR)
    n = len(x) + d * 8
    out = np.zeros((n, 2))
    out[:len(x)] = x
    tap = lowpass(x.mean(1), tone)
    g = mix
    for k in range(1, 9):
        ch = k % 2
        start = d * k
        out[start:start + len(tap), ch] += tap * g
        g *= feedback
        tap = lowpass(tap, tone)
    return out


def pan(x, p):
    """p in -1..1 -> stereo."""
    l = math.cos((p + 1) * math.pi / 4)
    r = math.sin((p + 1) * math.pi / 4)
    return np.stack([x * l, x * r], 1)


# ---------------------------------------------------------------- the song

class Song:
    def __init__(self, bpm=90, bars=16, key="A minor", beats_per_bar=4, swing=0.0):
        self.bpm = bpm
        self.bars = bars
        self.bpb = beats_per_bar
        self.bar_s = 60.0 / bpm * beats_per_bar
        self.length_s = bars * self.bar_s
        self.swing = swing
        root, mode = (key.split() + ["minor"])[:2]
        self.key_root = parse_note(root.lower() + "3")
        self.scale = SCALES.get(mode, SCALES["minor"])
        self.tracks = {}       # name -> dict(dry=stereo array, reverb=amount, delay=amount, duck=...)
        self.kick_times = []

    # -- helpers -----------------------------------------------------------

    def _buf(self, name, reverb=0.3, delay=0.0, duck=0.0, chorus_mix=0.0, gain=1.0, pan_=0.0):
        if name not in self.tracks:
            self.tracks[name] = dict(dry=np.zeros((self.n_loop + int(8 * SR), 2)), reverb=reverb,
                                     delay=delay, duck=duck, chorus=chorus_mix, gain=gain, pan=pan_)
        return self.tracks[name]

    def _place(self, tr, sig, t, gain=1.0):
        i = int(t * SR)
        if sig.ndim == 1:
            sig = pan(sig, tr["pan"])
        n = min(len(sig), len(tr["dry"]) - i)
        if n > 0:
            tr["dry"][i:i + n] += sig[:n] * gain

    def _steps(self, pattern):
        return [bar.split() for bar in pattern.split("|")]

    # -- writing music -----------------------------------------------------

    def notes(self, name, pattern, inst=glass_keys, octave=0, start_bar=0, end_bar=None, every=None,
              vel=1.0, transpose=0, reverb=0.35, delay=0.0, duck=0.0, chorus_mix=0.0, gain=1.0, pan_=0.0,
              legato=0.9):
        """Play a mini-notation pattern, repeating it from start_bar to end_bar.
        `every` = bars between repeats (default: the pattern's length)."""
        tr = self._buf(name, reverb, delay, duck, chorus_mix, gain, pan_)
        bars = self._steps(pattern)
        span = every or len(bars)
        end_bar = self.bars if end_bar is None else end_bar
        b0 = start_bar
        while b0 < end_bar:
            for bi, steps in enumerate(bars):
                bar = b0 + bi
                if bar >= end_bar:
                    break
                step_s = self.bar_s / max(1, len(steps))
                k = 0
                while k < len(steps):
                    tok = steps[k]
                    held = 1
                    while k + held < len(steps) and steps[k + held] == "_":
                        held += 1
                    if tok not in ("~", "_"):
                        for chord_tok in tok.split("+"):   # c4+e4+g4 = several notes at once
                            m = parse_note(chord_tok, self.key_root, self.scale) + transpose + 12 * octave
                            t = bar * self.bar_s + k * step_s
                            if self.swing and k % 2 == 1:
                                t += step_s * self.swing
                            sig = inst(midi_to_hz(m), step_s * held * legato, vel)
                            self._place(tr, sig, t)
                    k += held
            b0 += span

    def chords(self, name, progression, inst=shimmer_pad, octave=3, bars_per_chord=1, start_bar=0,
               end_bar=None, vel=1.0, rhythm=None, reverb=0.5, delay=0.0, duck=0.0, chorus_mix=0.3,
               gain=1.0, pan_=0.0, spread=True):
        """Chord names in order ('Am7 Fmaj7 C G'), looping. `rhythm` (e.g. 'x..x..x.')
        retriggers the chord inside each bar instead of holding it."""
        tr = self._buf(name, reverb, delay, duck, chorus_mix, gain, pan_)
        prog = progression.split()
        end_bar = self.bars if end_bar is None else end_bar
        bar = start_bar
        i = 0
        while bar < end_bar:
            notes = parse_chord(prog[i % len(prog)], octave)
            dur = self.bar_s * bars_per_chord
            hits = [(0, dur)]
            if rhythm:
                steps = len(rhythm)
                hits = [(k * self.bar_s / steps, self.bar_s / steps * 0.9)
                        for b in range(bars_per_chord) for k, c in enumerate(rhythm) if c in "xX"
                        for _ in [b]]
                hits = [(b * self.bar_s + off, d) for b in range(bars_per_chord)
                        for off, d in [(k * self.bar_s / steps, self.bar_s / steps * 0.9)
                                       for k, c in enumerate(rhythm) if c in "xX"]]
            for off, d in hits:
                for j, m in enumerate(notes):
                    sig = inst(midi_to_hz(m), d, vel)
                    if spread:
                        sig = pan(sig, (j / max(1, len(notes) - 1) - 0.5) * 0.7)
                    self._place(tr, sig, bar * self.bar_s + off, 1.0 / math.sqrt(len(notes)))
            bar += bars_per_chord
            i += 1

    def drums(self, pattern, start_bar=0, end_bar=None, gain=0.8, reverb=0.12, swing=None):
        """'kick: x...x... | snare: ....x... | hat: x.x.x.x.' repeated each bar."""
        end_bar = self.bars if end_bar is None else end_bar
        sw = self.swing if swing is None else swing
        for part in pattern.split("|"):
            if ":" not in part:
                continue
            kind, steps = part.split(":", 1)
            kind, steps = kind.strip(), steps.strip().replace(" ", "")
            tr = self._buf("drums_" + kind, reverb, 0, 0, 0, gain, {"hat": 0.2, "openhat": -0.2, "shaker": 0.35}.get(kind, 0))
            step_s = self.bar_s / len(steps)
            for bar in range(start_bar, end_bar):
                for k, c in enumerate(steps):
                    if c in "xX":
                        t = bar * self.bar_s + k * step_s + (step_s * sw if k % 2 else 0)
                        self._place(tr, drum(kind, 1.0 if c == "X" else 0.75), t)
                        if kind == "kick":
                            self.kick_times.append(t)

    def sample(self, name, source, start=0.0, length=2.0, at_bar=0, every=None, end_bar=None, fx=(),
               gain=0.5, reverb=0.4, delay=0.0, pan_=0.0, fade=0.05, fit=None, duck=0.0, chorus_mix=0.0):
        """Place a slice of a 1920s recording (start/length in seconds of the
        original), repeating every `every` bars. `at_bar` may be a list of bars.
        `fit` = bars: after the fx, stretch the slice (pitch kept) to exactly
        that many bars, so a record fragment locks into the cue as a loop."""
        tr = self._buf(name, reverb, delay, duck, chorus_mix, gain, pan_)
        src = load_sample(source)
        a = int(start * SR)
        x = src[a:a + int(length * SR)].copy()
        f = int(fade * SR)
        if f and len(x) > 2 * f:
            x[:f] *= np.linspace(0, 1, f)
            x[-f:] *= np.linspace(1, 0, f)
        x = sample_fx(x, fx)
        if fit:
            target = int(fit * self.bar_s * SR)
            ratio = target / max(1, len(x))
            if abs(ratio - 1) > 0.02:
                x = granular_stretch(x, ratio, grain=0.09) * 1.4
            x = np.interp(np.linspace(0, len(x) - 1, target), np.arange(len(x)), x)
            f = min(int(0.03 * SR), target // 4)
            x[:f] *= np.linspace(0, 1, f)
            x[-f:] *= np.linspace(1, 0, f)
        end_bar = self.bars if end_bar is None else end_bar
        if isinstance(at_bar, (list, tuple)):
            for b in at_bar:
                self._place(tr, x, b * self.bar_s)
            return
        bar = at_bar
        while bar < end_bar:
            self._place(tr, x, bar * self.bar_s)
            if not every:
                break
            bar += every

    def add(self, name, sig, t=0.0, at_bar=None, gain=1.0, reverb=0.3, delay=0.0, duck=0.0, chorus_mix=0.0, pan_=0.0):
        """Place any raw signal (mono or stereo numpy array) at time t seconds
        (or at a bar, or a list of bars)."""
        tr = self._buf(name, reverb, delay, duck, chorus_mix, gain, pan_)
        if at_bar is None:
            self._place(tr, sig, t)
        else:
            for b in (at_bar if isinstance(at_bar, (list, tuple)) else [at_bar]):
                self._place(tr, sig, b * self.bar_s)

    def fx(self, name, lp=None, hp=None, sweep_lp=None, tremolo=None, autopan=None, crush=False, width=None):
        """Per-track processing at mixdown. sweep_lp = [(bar, hz), ...] breakpoints;
        tremolo = (rate_hz, depth); autopan = rate_hz."""
        self.tracks[name].update(lp=lp, hp=hp, sweep_lp=sweep_lp, tremolo=tremolo, autopan=autopan,
                                 crush=crush, width=width)

    @property
    def n_loop(self):
        """Loop length in samples (whole 128-sample blocks, see render)."""
        return int(round(self.length_s * SR / 128)) * 128

    def bar_time(self, bar):
        return bar * self.bar_s

    def texture(self, name, kind="vinyl", gain=0.3):
        """Continuous beds: vinyl crackle, tape hiss, rain, distant room tone."""
        tr = self._buf(name, 0.2, 0, 0, 0, gain, 0)
        n = self.n_loop
        if kind == "vinyl":
            x = RNG.normal(0, 0.006, n) + (RNG.random(n) < 0.0006) * RNG.normal(0, 0.25, n)
            x = bandpass(x, 2000, 0.6)
        elif kind == "hiss":
            x = highpass(RNG.normal(0, 0.01, n), 3000)
        elif kind == "rain":
            x = lowpass(RNG.normal(0, 0.05, n), 3500) + (RNG.random(n) < 0.002) * RNG.normal(0, 0.1, n)
        elif kind == "room":
            x = lowpass(RNG.normal(0, 0.03, n), 300)
        elif kind == "softrain":   # rain on a window: dark wash plus scattered drops
            x = lowpass(highpass(RNG.normal(0, 0.035, n), 400), 2600)
            drops = (RNG.random(n) < 0.0015) * RNG.normal(0, 0.12, n)
            x = x + bandpass(drops, 1800, 1.5)
        elif kind == "wind":
            w = RNG.normal(0, 0.05, n)
            mod = 700 + 500 * np.sin(2 * np.pi * np.linspace(0, 3, n))
            x = sweep(w, "bp", mod[::512], 1.5) * (0.6 + 0.4 * np.sin(2 * np.pi * np.linspace(0, 2, n)))
        elif kind == "hum":        # fluorescent ward hum
            t = t_axis(n)
            x = sum(np.sin(2 * np.pi * 60 * k * t) / k ** 1.3 for k in (1, 2, 3, 4, 6)) * 0.012
            x += highpass(RNG.normal(0, 0.003, n), 2000)
        elif kind == "sea":
            w = lowpass(RNG.normal(0, 0.06, n), 900)
            x = w * (0.5 + 0.5 * np.sin(2 * np.pi * np.linspace(0, round(self.length_s / 7), n)) ** 2)
        elif kind == "tape":
            x = lowpass(highpass(RNG.normal(0, 0.008, n), 1500), 6000)
        else:
            raise ValueError(kind)
        self._place(tr, np.stack([x, np.roll(x, 777)], 1), 0)

    def motif(self, name, motif, **kw):
        """Shorthand: play one of the shared MOTIFS."""
        self.notes(name, MOTIFS[motif], **kw)

    # -- mixdown -----------------------------------------------------------

    def _loop_rate(self, rate):
        """Nearest LFO rate that completes whole cycles in the loop."""
        return max(1, round(rate * self.length_s)) / self.length_s

    def _track_fx(self, x, tr, n_total):
        t = t_axis(n_total)
        if tr.get("hp"):
            x = highpass(x, tr["hp"])
        if tr.get("lp"):
            x = lowpass(x, tr["lp"])
        if tr.get("sweep_lp"):
            pts = sorted(tr["sweep_lp"])
            xs = [p[0] * self.bar_s for p in pts]
            fs = [math.log(p[1]) for p in pts]
            curve = np.exp(np.interp(t[::256], xs, fs, period=self.length_s))
            x = sweep(x, "lp", curve, 0.8)
        if tr.get("crush"):
            x = np.repeat(x[::4], 4, axis=0)[:len(x)]
            x = lowpass(np.round(x * 64) / 64, 4000, 0.6)
        if tr.get("tremolo"):
            rate, depth = tr["tremolo"]
            r = self._loop_rate(rate)
            x = x * (1 - depth * (1 - np.cos(2 * np.pi * r * t)) / 2)[:, None]
        if tr.get("autopan"):
            r = self._loop_rate(tr["autopan"])
            p = np.sin(2 * np.pi * r * t) * 0.6
            m = x.mean(1)
            x = np.stack([m * np.cos((p + 1) * np.pi / 4), m * np.sin((p + 1) * np.pi / 4)], 1) * 1.41
        if tr.get("width") is not None:
            mid, side = (x[:, 0] + x[:, 1]) / 2, (x[:, 0] - x[:, 1]) / 2 * tr["width"]
            x = np.stack([mid + side, mid - side], 1)
        return x

    def render(self, path, master_gain=0.85, reverb_seconds=4.5, reverb_bright=0.45, loop=True,
               lowpass_master=None, duck_amount=0.0, loudness=-18.0, voice_pocket=True, verb_level=0.55):
        """Mix, fold the tails for a seamless loop, carve a pocket for the
        game's machine voices (1-3 kHz dip, soft top end), normalise loudness
        to `loudness` (dBFS, mean of plain and K-weighted RMS) (so every cue sits at the same level) and limit
        peaks to `master_gain`."""
        # the loop length is rounded to whole 128-sample blocks (at most 2 ms):
        # the Vorbis encoder pads a final partial block with silence, which
        # would put a tiny gap at every loop point
        n_song = self.n_loop
        n_total = n_song + int(8 * SR)
        mix = np.zeros((n_total, 2))
        verb_send = np.zeros((n_total, 2))
        # sidechain envelope from the kick (dream-pop "breathing")
        duck_env = np.ones(n_total)
        for t in self.kick_times:
            for t2 in (t, t - self.length_s if t > self.length_s - 0.4 else None):
                if t2 is None:
                    continue
                i = int(t2 * SR) + (n_song if t2 < 0 else 0)
                k = np.arange(int(0.35 * SR))
                seg = 1 - np.exp(-k / (0.09 * SR))
                j = min(len(seg), n_total - i)
                if j > 0:
                    duck_env[i:i + j] = np.minimum(duck_env[i:i + j], seg[:j])
        for name, tr in self.tracks.items():
            x = tr["dry"][:n_total] * tr["gain"]
            x = self._track_fx(x, tr, n_total)
            if tr["chorus"]:
                x = np.stack([chorus(x[:, 0], mix=tr["chorus"]), chorus(x[:, 1], 0.004, 0.43, tr["chorus"])], 1)
            if tr["delay"]:
                x = pingpong(x, self.bar_s / 8 * 3, mix=tr["delay"])[:n_total]
            if tr["duck"]:
                x = x * (1 - tr["duck"] * (1 - duck_env))[:, None]
            mix += x
            verb_send += x * tr["reverb"]
            if os.environ.get("VNSYNTH_LEVELS"):
                tr["_rms"] = np.sqrt(np.mean(x[:n_song] ** 2)) + 1e-12
        ir = make_ir(reverb_seconds, reverb_bright)
        wet = convolve(lowpass(highpass(verb_send, 180), 6000), ir)[:n_total] * verb_level
        mix = mix + wet
        if os.environ.get("VNSYNTH_LEVELS"):
            total = np.sqrt(np.mean(mix[:n_song] ** 2))
            print(os.path.basename(path), " ".join(f"{k}:{20 * math.log10(v['_rms'] / total):+.0f}"
                                                   for k, v in self.tracks.items()))
        if lowpass_master:
            mix = lowpass(mix, lowpass_master)
        if loop:
            # fold the tail back onto the start so the loop is seamless
            tail = mix[n_song:]
            mix = mix[:n_song].copy()
            m = min(len(tail), n_song)
            mix[:m] += tail[:m]
        mix = master_chain(mix, voice_pocket=voice_pocket, loudness=loudness, ceiling=master_gain)
        write_audio(path, mix)
        self._write_meta(path)
        return path

    def _write_meta(self, path):
        """examples/music/build/<cue>.json: tempo and bar length, for check.py and score.md."""
        import json
        name = meta_name(path)
        os.makedirs(os.path.dirname(os.path.join(BUILD_DIR, name + ".json")), exist_ok=True)
        with open(os.path.join(BUILD_DIR, name + ".json"), "w") as f:
            json.dump(dict(bpm=self.bpm, bars=self.bars, beats_per_bar=self.bpb, bar_s=self.bar_s,
                           length_s=self.length_s, tracks=sorted(self.tracks)), f)


def k_weight(x):
    """Rough BS.1770 K-weighting, for a loudness measure closer to the ear."""
    return biquad(highpass(x, 60), "highshelf", 1500, 0.707, 4.0)


def loudness_db(x):
    """Loudness used to level the cues: mean of plain RMS and K-weighted RMS, in dBFS."""
    r1 = np.sqrt(np.mean(x ** 2)) + 1e-12
    r2 = np.sqrt(np.mean(k_weight(x) ** 2)) + 1e-12
    return 10 * math.log10(r1) + 10 * math.log10(r2)


def limiter(x, ceiling=0.89, window=0.02):
    """Loop-safe peak limiter: gain dips are computed with wrap-around."""
    from scipy.ndimage import maximum_filter1d, uniform_filter1d
    a = np.abs(x).max(1)
    w = max(3, int(window * SR))
    d = np.clip(1 - ceiling / np.maximum(a, 1e-9), 0, 1)
    d = maximum_filter1d(d, size=w, mode="wrap")
    d = uniform_filter1d(d, size=w, mode="wrap")
    return x * (1 - d)[:, None]


def master_chain(mix, voice_pocket=True, loudness=-18.0, ceiling=0.85):
    # the filters run over the loop circularly (primed with its own last
    # second), so their state at the start matches the end: no seam
    pre = min(len(mix), SR)
    mix = np.concatenate([mix[-pre:], mix])
    mix = highpass(mix, 28)
    if voice_pocket:
        mix = biquad(mix, "peak", 1900, 0.7, -4.0)        # the machine voices' formant band
        mix = biquad(mix, "peak", 3200, 1.2, -1.5)
        mix = biquad(mix, "highshelf", 7000, 0.7, -4.0)   # no harsh highs
    mix = mix[pre:]
    for _ in range(3):
        mix = mix * 10 ** ((loudness - loudness_db(mix)) / 20)
        mix = limiter(mix, ceiling)
    return np.clip(mix, -ceiling, ceiling)


def _encode(wav, path):
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", wav, "-c:a", "libvorbis", "-q:a", "5", path],
                       capture_output=True)
    if r.returncode != 0:   # ffmpeg builds without libvorbis: the native encoder
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", wav, "-c:a", "vorbis", "-strict", "-2",
                        "-b:a", "128k", path], check=True)


def _write_wav(wav, stereo):
    data = (np.clip(stereo, -1, 1) * 32767).astype("<i2")
    with wave.open(wav, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())


# render.py --masters: also (or only) write each cue as a lossless FLAC into
# this folder (examples/music/build/master/<name>.flac), which vnpack encodes
# for the 3DS instead of the shipped .ogg (vn3ds.json "audio_masters").
MASTERS = os.environ.get("VNSYNTH_MASTERS")
MASTERS_ONLY = os.environ.get("VNSYNTH_MASTERS_ONLY") == "1"


def _write_master(path, stereo):
    dest = os.path.join(MASTERS, meta_name(path) + ".flac")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        wav = os.path.join(tmp, "out.wav")
        _write_wav(wav, stereo)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", wav, "-c:a", "flac",
                        "-compression_level", "8", dest], check=True)


def write_audio(path, stereo, ceiling=0.97):
    """Write a .wav, or an .ogg (Vorbis). Lossy coding can overshoot the
    limiter on a loud transient, so the .ogg is decoded again and, if it
    would clip, re-encoded a little quieter."""
    if MASTERS:
        _write_master(path, stereo)
        if MASTERS_ONLY:
            return
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        wav = os.path.join(tmp, "out.wav")
        _write_wav(wav, stereo)
        if path.endswith(".wav"):
            shutil.copy(wav, path)
            return
        for _ in range(3):
            _encode(wav, path)
            r = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "s16le", "-"], capture_output=True)
            peak = np.abs(np.frombuffer(r.stdout, "<i2")).max() / 32768 if r.stdout else 0
            if peak <= ceiling:
                return
            stereo = stereo * (ceiling * 0.97 / peak)
            _write_wav(wav, stereo)


# ---------------------------------------------------------------- the motifs
# The recurring themes that hold the score together. Scale degrees in the
# song's key, so every cue can quote them in its own key and mode.

MOTIFS = {
    # Aron: a question that rises and doesn't land (1 - 5 - 4 - 3 ... 2)
    "aron": "1 ~ 5 ~ 4 3 ~ ~ | 2 ~ ~ ~ ~ ~ ~ ~",
    # Aron, growing: the question asked twice, reaching higher the second time
    "aron_rising": "1 ~ 5 ~ 4 3 ~ ~ | 2 ~ ~ ~ ~ ~ ~ ~ | 1 ~ 5 ~ 6 5 ~ ~ | 4 ~ ~ ~ 2 ~ ~ ~",
    # Mira: warm, a step up and a turn home (3 - 4 - 5 - 3 | 2 - 1)
    "mira": "3 4 5 ~ 3 ~ ~ ~ | 2 ~ 1 ~ ~ ~ ~ ~",
    # Mira's love theme: her turn, then an answer that climbs to the sixth
    "mira_love": "3 4 5 ~ 3 ~ ~ ~ | 2 ~ 1 ~ ~ ~ ~ ~ | 3 4 5 ~ 6 ~ 5 ~ | 3 ~ ~ 2 1 ~ ~ ~",
    # The System: three pulses and a step down, mechanical (the 7:07 figure)
    "system": "1 1 1 ~ 7, ~ ~ ~",
    # 7:07: two notes a seventh apart, a clock that's slightly wrong
    "clock": "1 ~ ~ 7 ~ ~ 1 ~",
    # The Lantern Watch: three soft flickers and a rising answer
    "lantern": "5 ~ 5 ~ 5 ~ 6 1' | ~ ~ ~ ~ ~ ~ ~ ~",
    # Lord Ashveil: a slow chromatic descent (root down four semitones), velvet and hungry.
    # '@n' = n semitones from the key root, so it is chromatic in any mode.
    "ashveil": "1 ~ ~ ~ @-1 ~ ~ ~ | @-2 ~ ~ ~ @-3 ~ @-4 ~",
    # Ashveil as a child's music box: the same descent, skipping, with a little hungry leap up
    "ashveil_box": "1' ~ @11 ~ @10 ~ @9 ~ | @8 ~ ~ 5 1' ~ ~ ~",
    # The light / the architect: the Aron motif answered and completed
    "light": "1 ~ 5 ~ 4 3 ~ ~ | 2 ~ 3 ~ 5 ~ 1' ~",
    # Theo: a shrug and a grin, bluesy (the flat third bends to the major)
    "theo": "5, ~ 1 ~ @3 @4 1 ~ | 6, ~ 1 ~ ~ ~ ~ ~",
    # Miso: pounce, pause, a falling 'meow'
    "miso": "1' ~ 5 6 ~ ~ 1' ~ | 7 ~ 5 ~ ~ ~ ~ ~",
}


GAME_AUDIO = os.path.join(os.path.dirname(HERE), "demo", "game", "audio")
_OUT_OVERRIDE = []


def out(name, sub=None):
    """Where a cue renders to: the game's audio folder (or a subfolder of it,
    e.g. out("quiz", sub="minigame") -> audio/minigame/quiz.ogg)."""
    if _OUT_OVERRIDE:
        name = _OUT_OVERRIDE[-1]
    if sub:
        name = sub + "/" + name
    return os.path.join(GAME_AUDIO, name + ".ogg")


def meta_name(path):
    """A cue's name relative to the game's audio folder, without extension
    ('theme', 'minigame/quiz'): build/<name>.json holds its tempo grid."""
    rel = os.path.relpath(os.path.abspath(path), GAME_AUDIO)
    if rel.startswith(".."):
        rel = os.path.basename(path)
    return os.path.splitext(rel)[0].replace(os.sep, "/")


def reseed(seed=1):
    """Fresh, deterministic randomness for each cue (render.py calls it)."""
    global RNG
    RNG = np.random.default_rng(seed)


def render_as(cue, name):
    """An alias cue: render cues/<cue>.py again, but into audio/<name>.ogg."""
    import runpy
    _OUT_OVERRIDE.append(name)
    try:
        reseed()
        runpy.run_path(os.path.join(HERE, "cues", cue + ".py"), run_name="__main__")
    finally:
        _OUT_OVERRIDE.pop()

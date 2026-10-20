"""The minigames' sound effects -> audio/minigame/<name>.ogg

One generator for every clip, so they can all be regenerated:

    python3 examples/music/render.py minigame/sfx             # all of them
    SFX=tower_,draw_ python3 examples/music/render.py minigame/sfx   # only names with these prefixes

Each sound is a function below, registered with @sfx(loudness, peak ceiling)
and named after its file. Sections: shared (cheat, result, board_tick, board_land), The Big
Questions (quiz_*), The Tower (tower_*, D minor), Echo of a Shape (draw_*,
C lydian), Lantern Rhythm (lantern_*, E major), Crown of the Worm (snake_*,
G dorian), Miso's Hunt (miso_*, D minor), The Hungry Sky (invaders_*, B
minor; the boss in C minor), then "Round 2" for the redesigned games (the
angel host, the band, Pim's whiteboard, the shooter, packages and leaps,
apples, the platformer). Pitched sounds are written in their game's key and
timbre, so they sit inside the loop; clips the engine re-pitches (combos,
levels, voice syllables) are recorded at a neutral pitch.

Loopable clips (LOOPS: invaders_beam) are periodic in 1024-sample blocks and
written without fades or padding, so they wrap seamlessly.

Runtime-pitched clips: lantern_hit_perfect / lantern_hit_good are on E5 (the
loop's tonic; lanes play them at 1.0 / 1.2599 / 1.4983); tower_through_hoop
and tower_land are short and in D (they rise a semitone per segment, up to
2^(15/12)).

All are written as 32 kHz Vorbis (the ffmpeg encoder here only writes
stereo; both channels are the same, and the engine folds them to mono). Each
starts on its first sample with a short ramp, ends on an exact zero (no DC),
and is levelled by loudness with a peak ceiling, so the set sits evenly over
the -18 dBFS music; the rapid ones (steps, ticks, clicks) are much softer.
Every sound gets its own fixed random seed, so a partial render matches a
full one.
"""
import math
import os
import subprocess
import tempfile
import zlib

import numpy as np

import vnsynth
from vnsynth import (GAME_AUDIO, SR, _encode, _write_wav, arp_pluck, bandpass, choir, felt_piano, glass_harmonica,
                     glass_keys, glitch, highpass, loudness_db, lowpass, make_ir, mallet, midi_to_hz, soft_brass,
                     sweep, t_axis, warm_pad)
from _mg import SUB, bubble, crush, dive, pizzicato

OUT = os.path.join(GAME_AUDIO, SUB)
rng = np.random.default_rng(11)
SOUNDS = {}      # name -> (generator, loudness dBFS, peak ceiling dBFS)


def sfx(loud=-16.0, peak=-4.0):
    """Register a generator: its name is the file name."""
    def reg(fn):
        SOUNDS[fn.__name__] = (fn, loud, peak)
        return fn
    return reg


# ---------------------------------------------------------------- building blocks

def note(n):
    """MIDI note from a name like 'e5', 'c#6', 'bb4'."""
    names = {"c": 0, "d": 2, "e": 4, "f": 5, "g": 7, "a": 9, "b": 11}
    acc = n.count("#") - n.count("b", 1)
    return 12 * (int(n[-1]) + 1) + names[n[0]] + acc


def hz(n):
    return midi_to_hz(note(n)) if isinstance(n, str) else float(n)


def place(buf, sig, t, gain=1.0):
    i = int(t * SR)
    n = min(len(sig), len(buf) - i)
    if n > 0:
        buf[i:i + n] += sig[:n] * gain


def buf(seconds):
    return np.zeros(int(seconds * SR))


def noise(n):
    return rng.normal(0, 1, n)


def env(n, rate, attack=0.002):
    t = t_axis(n)
    return np.exp(-t * rate) * np.clip(t / max(attack, 1e-4), 0, 1)


def arch(n, p=1.0):
    return np.sin(np.pi * np.linspace(0, 1, n)) ** p


def glide(f0, f1, seconds, curve=1.0, harmonics=((1, 1.0),), vib=(0.0, 0.0)):
    """A tone gliding exponentially from f0 to f1 (Hz or note names); vib = (rate, depth)."""
    n = int(seconds * SR)
    u = np.linspace(0, 1, n, endpoint=False)
    f = hz(f0) * (hz(f1) / hz(f0)) ** (u ** curve)
    if vib[1]:
        f = f * (1 + vib[1] * np.sin(2 * np.pi * vib[0] * t_axis(n)))
    ph = np.cumsum(f) / SR
    return sum(a * np.sin(2 * np.pi * k * ph + k) for k, a in harmonics)


def nsweep(seconds, f0, f1, q=1.5, curve=1.0):
    """Noise through a band-pass whose centre glides from f0 to f1: whooshes."""
    n = int(seconds * SR)
    u = np.linspace(0, 1, n)
    c = f0 * (f1 / f0) ** (u ** curve)
    return sweep(noise(n), "bp", c[::32], q)


def bell(f, seconds, partials=((1, 1, 3), (2, 0.3, 5), (3, 0.12, 8)), attack=0.0015):
    """Additive bell: (ratio, amplitude, decay rate) per partial."""
    n = int(seconds * SR)
    t = t_axis(n)
    f = hz(f)
    s = sum(a * np.sin(2 * np.pi * f * r * t + r) * np.exp(-t * d) for r, a, d in partials if f * r < 7000)
    return s * np.clip(t / attack, 0, 1)


def thump(seconds=0.3, f0=150, f1=50, rate=9, drop=22):
    """A felted drum: a sine falling from f0 to f1."""
    n = int(seconds * SR)
    t = t_axis(n)
    f = f1 + (f0 - f1) * np.exp(-t * drop)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * rate) * np.clip(t / 0.0015, 0, 1)


def click(seconds=0.03, centre=3000, q=2.0, rate=200):
    n = int(seconds * SR)
    return bandpass(noise(n), centre, q) * env(n, rate, 0.0004)


def crackle(seconds, density=0.01, centre=3500, q=1.5):
    n = int(seconds * SR)
    return bandpass(noise(n) * (rng.random(n) < density), centre, q)


def knock(f, seconds=0.12, rate=40, ratio=2.7):
    """Wood: two inharmonic partials and a short knock."""
    n = int(seconds * SR)
    t = t_axis(n)
    return (np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * f * ratio * t) * np.exp(-t * rate)) \
        * np.exp(-t * rate) * np.clip(t / 0.0008, 0, 1)


def inst(fn, n, dur, vel=1.0):
    """One note of a vnsynth instrument (name or Hz)."""
    return fn(hz(n), dur, vel)


def cat_voice(seconds, f, F1, F2, amp, q1=4.0, q2=5.0, harmonics=10):
    """A synthesized cat: a pulse voice through two sliding formants.
    f, F1, F2, amp are functions of u (0..1 across the sound)."""
    n = int(seconds * SR)
    u = np.linspace(0, 1, n)
    ph = np.cumsum(f(u)) / SR
    src = sum(np.sin(2 * np.pi * k * ph) / k ** 1.1 for k in range(1, harmonics + 1))
    s = sweep(src, "bp", F1(u)[::32], q1) + 0.55 * sweep(src, "bp", F2(u)[::32], q2) + 0.15 * lowpass(src, 400)
    return s * amp(u)


def shimmer(seconds, freqs, trem=13, gain=0.04):
    n = int(seconds * SR)
    t = t_axis(n)
    s = sum(np.sin(2 * np.pi * hz(f) * t + k) for k, f in enumerate(freqs))
    return s * (1 + 0.6 * np.sin(2 * np.pi * trem * t)) / 2 * arch(n, 2) * gain


def room(x, seconds=0.5, mix=0.25, bright=0.5, seed=3):
    """A small, dark room so the sound sits in the same space as the score."""
    from scipy.signal import fftconvolve
    ir = make_ir(seconds, bright, seed=seed)[:, 0]
    wet = fftconvolve(x, ir)[:len(x)]
    return x + lowpass(wet, 5000) * mix / 3


def finish(x, length, fade_in=0.0015, fade_out=0.08):
    """Cut to `length` s, ramp in from zero, fade out to an exact zero, remove DC."""
    n = int(round(length * SR))
    x = np.concatenate([x, np.zeros(max(0, n - len(x)))])[:n]
    x = x - np.mean(x)
    fi, fo = max(2, int(fade_in * SR)), max(2, int(fade_out * SR))
    x[:fi] *= np.sin(np.linspace(0, math.pi / 2, fi)) ** 2
    x[-fo:] *= np.cos(np.linspace(0, math.pi / 2, fo)) ** 2
    x[0] = x[-1] = 0.0
    return x


def level(x, loud, peak, max_squash=4.0):
    """Loudness target (dBFS, as the cues measure it), never above `peak` dBFS.
    A spiky sound that would fall short of its loudness has its transients
    gently limited (by at most `max_squash` dB) instead of being left quiet."""
    from scipy.ndimage import maximum_filter1d, uniform_filter1d
    ceiling = 10 ** (peak / 20)
    g = min(10 ** ((loud - loudness_db(x)) / 20), ceiling / np.abs(x).max() * 10 ** (max_squash / 20))
    y = x * g
    w = max(3, int(0.004 * SR))
    d = np.clip(1 - ceiling / np.maximum(np.abs(y), 1e-9), 0, 1)
    d = uniform_filter1d(maximum_filter1d(d, size=w, mode="nearest"), size=w, mode="nearest")
    y = y * (1 - d)
    return np.clip(y, -ceiling, ceiling)


LOOPS = set()    # sounds the engine may loop: periodic, no fades, no padding


def write(name, x, loud=-15.0, peak=-3.0):
    if name in LOOPS:
        write_loop(name, x, loud, peak)
        return
    x = vnsynth.biquad(x, "highshelf", 7000, 0.7, -4.0)     # the score's soft top end
    x = level(x, loud, peak)
    x[0] = x[-1] = 0.0
    # The ffmpeg Vorbis encoder can drop a final partial 1024-sample block,
    # which would cut the fade-out short: pad with silence past the next block.
    pad = (-len(x)) % 1024 + 1024
    x = np.concatenate([x, np.zeros(pad)])
    path = os.path.join(OUT, name + ".ogg")
    os.makedirs(OUT, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        wav = os.path.join(tmp, "out.wav")
        _write_wav(wav, np.stack([x, x], 1))
        _encode(wav, path)
        r = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "s16le", "-ac", "1", "-"], capture_output=True)
        y = np.frombuffer(r.stdout, "<i2") / 32768
    if len(y) < len(x) - pad:
        print(f"    WARNING {name}: decoded {len(y)} samples, wrote {len(x) - pad}")
    x = x[:len(x) - pad]
    print(f"    {name:<22} {len(x) / SR:5.3f}s  peak {20 * np.log10(np.abs(y).max()):5.1f}  "
          f"loud {loudness_db(x):5.1f}  {os.path.getsize(path) // 1024} KB")


# ---------------------------------------------------------------- shared and The Big Questions (quiz)

@sfx(-16, -4)
def cheat():
    """The Lantern's three flickers and their rising answer (5 5 5 6 1'), as fast sparks, over a shimmer."""
    L = 0.6
    x = np.zeros(int(1.2 * SR))
    for k, (m, t) in enumerate(zip(["b5", "b5", "b5", "c#6", "e6", "g#6", "b6"],
                                   [0.0, 0.045, 0.09, 0.14, 0.19, 0.25, 0.31])):
        place(x, glass_keys(midi_to_hz(note(m)), 0.08, 0.9)[: int(0.9 * SR)], t, 0.8 - 0.05 * k)
        place(x, mallet(midi_to_hz(note(m) + 12), 0.05, 0.6)[: int(0.7 * SR)], t + 0.008, 0.25)
    n = len(x)
    t = t_axis(n)
    shim = sum(np.sin(2 * np.pi * f * t + p) for f, p in ((1975.5, 0), (2489.0, 1), (2960.0, 2), (3951.1, 3)))
    shim *= (1 + 0.6 * np.sin(2 * np.pi * 13 * t)) / 2 * np.sin(np.pi * np.clip(t / L, 0, 1)) ** 2 * 0.04
    sparkle = bandpass(rng.normal(0, 1, n) * (rng.random(n) < 0.004), 5200, 2.0) * np.exp(-t * 3) * 0.6
    x = room(x + shim + lowpass(sparkle, 7000), 0.6, 0.5, 0.6)
    return finish(x, L, fade_out=0.18)


@sfx(-16, -4)
def result():
    """A gentle reveal: 3 5 1' (E G C) on vibes and glass, the Light's last turn."""
    x = np.zeros(int(1.6 * SR))
    for k, (m, t) in enumerate(zip(["e5", "g5", "c6"], [0.0, 0.16, 0.32])):
        place(x, mallet(midi_to_hz(note(m)), 0.5, 0.85), t, 1.0 + 0.1 * k)
        place(x, glass_keys(midi_to_hz(note(m) - 12), 0.4, 0.6), t, 0.35)
    x = room(x, 0.8, 0.5)
    return finish(x, 1.0, fade_out=0.35)


@sfx(-30, -16)
def board_tick():
    """The leaderboard scrolling past a row: a tiny soft tick, 35 ms (fires 10-20 times a second)."""
    L = 0.035
    x = knock(1400, L, 140, 1.5) + 0.35 * click(L, 3200, 2.0, 350)
    return finish(lowpass(x, 4500), L, 0.0005, 0.012)


@sfx(-16, -4)
def board_land():
    """Landed on your name: a warm, golden C major bloom (C E G C'), strummed, over a soft low C."""
    L = 0.7
    x = buf(L + 2.5)
    for k, m in enumerate(["c5", "e5", "g5", "c6"]):
        place(x, inst(mallet, m, 0.4), 0.025 * k, 0.75)
        place(x, inst(glass_keys, m, 0.3, 0.7), 0.025 * k, 0.3)
    place(x, inst(felt_piano, "c4", 0.4, 0.8), 0.0, 0.5)
    place(x, bell("c3", L, ((1, 1, 3),), attack=0.006), 0.0, 0.25)
    place(x, shimmer(0.6, ["e6", "g6", "c7"], 10, 0.03), 0.05)
    return finish(room(x, 0.7, 0.45), L, 0.002, 0.25)


@sfx(-15, -3.5)
def quiz_right():
    """A bright chime: G5 then C6 (up a fourth), bell partials, a quick sparkle."""
    x = np.zeros(int(1.0 * SR))
    for m, t, g in (("g5", 0.0, 0.9), ("c6", 0.075, 1.0)):
        f = midi_to_hz(note(m))
        n = int(0.9 * SR)
        tt = t_axis(n)
        s = (np.sin(2 * np.pi * f * tt) + 0.35 * np.sin(2 * np.pi * f * 2.0 * tt) * np.exp(-tt * 6)
             + 0.18 * np.sin(2 * np.pi * f * 3.01 * tt) * np.exp(-tt * 12)
             + 0.08 * np.sin(2 * np.pi * f * 5.43 * tt) * np.exp(-tt * 25))
        place(x, s * np.exp(-tt * 5.5) * np.clip(tt / 0.0015, 0, 1), t, g)
    x = room(x, 0.5, 0.35)
    return finish(x, 0.5, fade_out=0.15)


@sfx(-15, -3)
def quiz_wrong():
    """A soft low thud: a felted drum and a muted low note, nothing harsh."""
    n = int(0.6 * SR)
    t = t_axis(n)
    f = 58 + 90 * np.exp(-t * 22)
    thud = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)
    knock = np.sin(2 * np.pi * 165 * t) * np.exp(-t * 26) * 0.5
    felt = lowpass(rng.normal(0, 1, n), 600) * np.exp(-t * 60) * 0.25
    bwom = (np.sin(2 * np.pi * 110 * t) + 0.5 * np.sin(2 * np.pi * 116.5 * t)) * np.exp(-t * 7) * 0.25
    x = lowpass(np.tanh((thud + knock + felt + bwom) * 1.2), 900)
    return finish(x, 0.4, fade_out=0.12)


@sfx(-16, -4)
def quiz_timeout():
    """A small clock bell, struck twice (ding-ding), with a little hammer buzz."""
    x = np.zeros(int(1.5 * SR))
    f0 = 1046.5
    n = int(1.2 * SR)
    t = t_axis(n)
    partials = ((1.0, 1.0, 2.6), (2.0, 0.35, 4.0), (2.42, 0.3, 5.0), (3.0, 0.15, 7.0), (4.16, 0.1, 10.0))
    bell = sum(a * np.sin(2 * np.pi * f0 * r * t + r) * np.exp(-t * d) for r, a, d in partials)
    bell *= 1 + 0.1 * np.sin(2 * np.pi * 7 * t)                 # the beat of a real bell
    hammer = bandpass(rng.normal(0, 1, n), 2500, 1.5) * np.exp(-t * 120) * 0.4
    hit = (bell + hammer) * np.clip(t / 0.001, 0, 1)
    place(x, hit, 0.0, 1.0)
    place(x, hit, 0.17, 0.85)
    x = lowpass(room(x, 0.6, 0.3), 6000)
    return finish(x, 1.0, fade_out=0.3)


@sfx(-15, -4)
def quiz_cheat_answer():
    """'Meow': a pulse voice rising then falling, its formants sliding from 'mi' to 'ow'."""
    L = 0.45
    n = int(L * SR)
    t = t_axis(n)
    u = t / L
    f = 520 + 260 * np.sin(np.pi * np.clip(u / 0.6, 0, 1)) ** 1.2 - 140 * np.clip((u - 0.45) / 0.55, 0, 1)
    f *= 1 + 0.012 * np.sin(2 * np.pi * 6.5 * t)
    ph = np.cumsum(f) / SR
    src = sum(np.sin(2 * np.pi * k * ph) / k ** 1.1 for k in range(1, 10))
    f1 = 350 + 400 * np.clip((u - 0.15) / 0.6, 0, 1)            # 'm-i' -> 'a' -> 'ow'
    f2 = 2100 - 1200 * np.clip((u - 0.1) / 0.7, 0, 1)
    s = sweep(src, "bp", f1[::32], 4.0) + 0.55 * sweep(src, "bp", f2[::32], 5.0) + 0.15 * lowpass(src, 400)
    env = np.clip(t / 0.03, 0, 1) ** 2 * np.sin(np.pi * np.clip(u, 0, 1)) ** 0.6 * (1 - 0.4 * u)
    return finish(room(s * env, 0.4, 0.3), L, fade_in=0.004, fade_out=0.06)


@sfx(-22, -10)
def quiz_tick():
    """A soft clock tick: a woody click and a short ping, 50 ms."""
    n = int(0.05 * SR)
    t = t_axis(n)
    click = bandpass(rng.normal(0, 1, n), 3600, 3) * np.exp(-t * 220)
    ping = np.sin(2 * np.pi * 1250 * t) * np.exp(-t * 110) * 0.8
    body = np.sin(2 * np.pi * 620 * t) * np.exp(-t * 140) * 0.5
    return finish(click * 0.6 + ping + body, 0.05, fade_in=0.0005, fade_out=0.015)


@sfx(-20, -9)
def quiz_move():
    """A tiny blip: a sine that hops up a fifth."""
    n = int(0.06 * SR)
    t = t_axis(n)
    f = np.where(t < 0.018, 880.0, 1318.5)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.15 * np.sin(4 * np.pi * np.cumsum(f) / SR)
    return finish(s * np.exp(-t * 45), 0.06, fade_in=0.001, fade_out=0.02)


@sfx(-18, -6)
def quiz_next():
    """A whoosh: breathy noise swept upward, in and out like a page turning."""
    L = 0.3
    n = int(L * SR)
    t = t_axis(n)
    u = t / L
    noise = rng.normal(0, 1, n)
    centre = 350 * (2600 / 350) ** (u ** 1.3)
    s = sweep(noise, "bp", centre[::32], 1.6) + 0.3 * sweep(noise, "bp", centre[::32] * 1.5, 2.5)
    s = lowpass(highpass(s, 200), 6000)
    env = np.sin(np.pi * u ** 0.8) ** 2
    return finish(s * env, L, fade_in=0.003, fade_out=0.04)




# ---------------------------------------------------------------- The Tower (tower_*, D minor)
# timbres of the tower loops: vibes, plucked arp, flute/soft lead, felt drums, wood

@sfx(-27, -15)
def tower_step():
    """A soft leafy footstep: three tiny crinkles and a felt tap (played every 0.22 s)."""
    L = 0.06
    x = buf(L)
    for t0, g in ((0.0, 1.0), (0.011, 0.55), (0.024, 0.3)):
        place(x, click(0.02, 2600, 1.2, 260), t0, g)
    place(x, thump(0.05, 330, 260, 70, 60), 0.0, 0.5)
    return finish(lowpass(x, 5000), L, 0.0005, 0.015)


@sfx(-22, -10)
def tower_aligned():
    """A tiny bright 'ting' on A5 (the fifth of D), with a faint D6 above."""
    x = bell("a5", 0.12, ((1, 1, 28), (2.76, 0.22, 60), (5.4, 0.06, 90))) + 0.3 * bell("d6", 0.12, ((1, 1, 40),))
    return finish(x, 0.12, 0.0008, 0.03)


@sfx(-18, -6)
def tower_jump():
    """A springy boing: D4 sprung up to A4 with a decaying spring wobble."""
    L = 0.2
    n = int(L * SR)
    t = t_axis(n)
    u = t / L
    f = hz("d4") * (hz("a4") / hz("d4")) ** (u ** 0.5) * (1 + 0.07 * np.sin(2 * np.pi * 26 * t) * np.exp(-t * 14))
    ph = np.cumsum(f) / SR
    s = np.sin(2 * np.pi * ph) + 0.3 * np.sin(4 * np.pi * ph) + 0.12 * np.sin(6 * np.pi * ph)
    s = lowpass(s, 3000) * np.clip(t / 0.003, 0, 1) * (1 - u) ** 0.7
    return finish(s + 0.3 * click(L, 1800, 1.5, 300), L, 0.001, 0.04)


@sfx(-18, -5)
def tower_through_hoop():
    """An airy whoosh through the ring with a D5 chime (pitched up a semitone per segment)."""
    L = 0.3
    n = int(L * SR)
    x = nsweep(L, 700, 1800, 1.4) * arch(n, 1.5) * 0.5
    place(x, bell("d5", 0.25, ((1, 1, 9), (2, 0.25, 14), (3, 0.1, 22))), 0.05, 0.9)
    place(x, bell("a5", 0.2, ((1, 1, 14),)), 0.05, 0.25)
    return finish(x, L, 0.004, 0.06)


@sfx(-18, -5)
def tower_land():
    """A leaf rustle and a soft thump on D3 (pitched up a semitone per segment)."""
    L = 0.15
    x = buf(L)
    for t0, g in ((0.0, 1.0), (0.012, 0.6), (0.03, 0.45), (0.05, 0.25)):
        place(x, click(0.03, 3000, 1.0, 120), t0, g * 0.5)
    place(x, thump(L, hz("d3") * 1.4, hz("d3"), 22, 40), 0.0, 1.0)
    return finish(lowpass(x, 5000), L, 0.001, 0.04)


@sfx(-17, -4)
def tower_bonk():
    """A comic wooden bonk: a hollow knock that drops in pitch."""
    L = 0.15
    n = int(L * SR)
    t = t_axis(n)
    f = 460 + 280 * np.exp(-t * 45)
    ph = np.cumsum(f) / SR
    s = (np.sin(2 * np.pi * ph) + 0.35 * np.sin(2 * np.pi * 2.7 * ph) * np.exp(-t * 40)) * np.exp(-t * 26)
    s = s * np.clip(t / 0.0008, 0, 1) + 0.25 * click(L, 2200, 2, 250)
    return finish(bandpass(s, 600, 0.6) * 2 + 0.3 * s, L, 0.0008, 0.03)


def wah(f0, f1, seconds, open_=1300):
    """A muted-trombone 'wah': a buzzy tone through a formant that opens and closes."""
    n = int(seconds * SR)
    u = np.linspace(0, 1, n)
    f = hz(f0) * (hz(f1) / hz(f0)) ** u
    ph = np.cumsum(f) / SR
    src = sum(np.sin(2 * np.pi * k * ph) / k for k in range(1, 14))
    centre = 350 + open_ * np.sin(np.pi * u) ** 1.5
    return sweep(src, "bp", centre[::32], 2.2) * np.clip(u / 0.08, 0, 1) * np.clip((1 - u) / 0.15, 0, 1)


@sfx(-18, -5)
def tower_miss():
    """A short descending wah-wah: E4, then D4 sagging flat."""
    L = 0.4
    x = buf(L)
    place(x, wah("e4", "e4", 0.16), 0.0)
    place(x, wah("d4", "c#4", 0.22, 1000), 0.17)
    return finish(room(x, 0.3, 0.3), L, 0.003, 0.05)


@sfx(-17, -4)
def tower_thud():
    """A dull thud with a dizzy wobble circling above it."""
    L = 0.3
    x = thump(L, 130, 50, 12)
    place(x, glide(950, 700, 0.25, vib=(10, 0.08)) * arch(int(0.25 * SR)) * 0.12, 0.04)
    return finish(x, L, 0.001, 0.06)


def beep(f, seconds, rate=12):
    """A soft square-ish beep (odd partials), for alarms."""
    n = int(seconds * SR)
    t = t_axis(n)
    s = sum(np.sin(2 * np.pi * hz(f) * k * t) / k for k in (1, 3, 5))
    return lowpass(s, 2800) * np.clip(t / 0.003, 0, 1) * np.clip((seconds - t) / 0.01, 0, 1) * np.exp(-t * rate)


@sfx(-17, -4)
def tower_faster():
    """A rising whoosh and a two-note alarm stinger (D5, A5): the tower speeds up."""
    L = 0.5
    n = int(0.42 * SR)
    x = buf(L)
    u = np.linspace(0, 1, n)
    place(x, nsweep(0.42, 300, 3200, 1.3, 1.5) * u ** 1.5 * np.clip((1 - u) / 0.15, 0, 1) * 0.7, 0.0)
    place(x, beep("d5", 0.08), 0.3, 0.6)
    place(x, beep("a5", 0.12), 0.39, 0.6)
    return finish(x, L, 0.003, 0.05)


@sfx(-17, -4)
def tower_warp():
    """A sparkly teleport upward: a D minor arpeggio flung up on glass, a warbling rise."""
    L = 0.5
    x = buf(L + 1.0)
    for k, m in enumerate(["d5", "f5", "a5", "d6", "f6", "a6"]):
        place(x, inst(glass_keys, m, 0.06, 0.8), 0.03 * k, 0.8 - 0.08 * k)
    place(x, glide(400, 2400, 0.4, 1.5, vib=(30, 0.03)) * arch(int(0.4 * SR)) * 0.12, 0.0)
    place(x, highpass(crackle(0.45, 0.01, 4500), 2000) * 0.5, 0.05)
    return finish(room(x, 0.5, 0.4), L, 0.002, 0.15)


@sfx(-16, -4)
def tower_summit():
    """A quick rising arpeggio on vibes and plucks: D F A D'."""
    L = 0.6
    x = buf(L + 1.0)
    for k, m in enumerate(["d5", "f5", "a5", "d6"]):
        place(x, inst(mallet, m, 0.3, 0.9), 0.07 * k, 0.8 + 0.1 * k)
        place(x, inst(arp_pluck, midi_to_hz(note(m) - 12), 0.1, 0.8), 0.07 * k, 0.3)
    return finish(room(x, 0.6, 0.4), L, 0.001, 0.2)


@sfx(-18, -5)
def tower_enter_hole():
    """A hollow plunk falling away into the hole."""
    L = 0.3
    n = int(L * SR)
    s = glide(620, 160, L, 0.5, ((1, 1.0), (2, 0.2))) * env(n, 9)
    s = 0.6 * s + bandpass(s, 400, 4) * 1.5 + 0.2 * click(L, 2000, 2, 300)
    return finish(s, L, 0.001, 0.06)


@sfx(-17, -4)
def tower_pop_out():
    """A cork pop and a whoosh out into the scenery."""
    L = 0.35
    x = buf(L)
    place(x, glide(500, 1100, 0.04, 0.5) * env(int(0.04 * SR), 60), 0.0, 1.0)
    place(x, highpass(click(0.01, 3000, 0.8, 500), 1500), 0.0, 0.8)
    n = int(0.3 * SR)
    place(x, nsweep(0.3, 500, 2500, 1.4) * arch(n, 1.2) * 0.45, 0.04)
    return finish(x, L, 0.0008, 0.05)


@sfx(-16, -3)
def tower_win():
    """A short fanfare: the Light's last turn (E F A D') on muted brass and vibes, landing on D major."""
    L = 1.4
    x = buf(L + 1.5)
    for m, t0, d in (("e5", 0.0, 0.09), ("f5", 0.11, 0.09), ("a5", 0.22, 0.11), ("d6", 0.36, 0.6)):
        place(x, inst(soft_brass, midi_to_hz(note(m) - 12), d, 0.9), t0, 0.9)
        place(x, inst(mallet, m, d, 0.8), t0, 0.5)
    for m in ("d4", "f#4", "a4"):
        place(x, inst(soft_brass, midi_to_hz(note(m) - 12), 0.6, 0.7), 0.36, 0.5)
    place(x, inst(glass_keys, "a6", 0.3, 0.6), 0.38, 0.3)
    place(x, thump(0.4, 120, 70, 8), 0.36, 0.6)
    return finish(room(x, 0.9, 0.5), L, 0.003, 0.45)


@sfx(-17, -4)
def tower_cheer():
    """A party horn and a tiny 'yay' from the leaves."""
    L = 0.5
    n = int(L * SR)
    t = t_axis(n)
    f = 470 * (1 + 0.08 * (1 - np.exp(-t * 30))) * (1 + 0.012 * np.sin(2 * np.pi * 18 * t))
    ph = np.cumsum(f) / SR
    src = sum(np.sin(2 * np.pi * k * ph) / k ** 0.8 for k in range(1, 16))
    horn = (bandpass(src, 1200, 1.5) + 0.4 * bandpass(src, 2400, 3)) * np.clip(t / 0.015, 0, 1) \
        * np.clip((L - t) / 0.1, 0, 1)
    x = horn * 0.8
    for f0 in (300, 345, 390):          # three little voices: 'yay'
        v = cat_voice(0.35, lambda u, f0=f0: f0 * (1 + 0.3 * u), lambda u: 500 + 300 * u, lambda u: 1900 - 600 * u,
                      lambda u: np.sin(np.pi * u) ** 0.8)
        place(x, v * 0.35, 0.05 + 0.01 * (f0 % 7))
    place(x, click(0.05, 3000, 0.8, 60) * 0.3, 0.0)
    return finish(room(x, 0.4, 0.3), L, 0.003, 0.08)


@sfx(-17, -4)
def tower_timeout():
    """A soft low buzzer (D3 and A3) under a single clock-bell D5."""
    L = 0.6
    n = int(0.45 * SR)
    t = t_axis(n)
    buzz = sum(np.sin(2 * np.pi * f * k * t) / k for f in (hz("d3"), hz("a3")) for k in (1, 3, 5, 7))
    buzz = lowpass(buzz, 1100) * (1 + 0.25 * np.sin(2 * np.pi * 25 * t)) * np.clip(t / 0.01, 0, 1) \
        * np.clip((0.45 - t) / 0.06, 0, 1) * 0.35
    x = buf(L)
    place(x, buzz, 0.0)
    place(x, bell("d5", L, ((1, 1, 4), (2.0, 0.35, 6), (2.42, 0.25, 7), (3.0, 0.12, 10))), 0.0, 0.8)
    return finish(x, L, 0.002, 0.1)


# ---------------------------------------------------------------- Echo of a Shape (draw_*, C lydian)
# felt piano, vibes, glass; paper and pencil

@sfx(-18, -5)
def draw_reveal():
    """A soft rising glassy shimmer: C E G B, bowed, blooming one after another."""
    L = 0.5
    x = buf(L)
    for k, m in enumerate(["c5", "e5", "g5", "b5"]):
        place(x, bell(m, 0.5, ((1, 1, 2), (2.004, 0.3, 3), (3.01, 0.1, 5)), attack=0.08), 0.05 * k, 0.6)
    n = int(L * SR)
    x += nsweep(L, 2000, 4500, 3.0) * np.linspace(0, 1, n) ** 2 * 0.15
    return finish(room(x, 0.6, 0.4), L, 0.01, 0.12)


@sfx(-24, -12)
def draw_tick():
    """A quiet wooden click."""
    L = 0.08
    x = knock(900, L, 70, 1.6) + 0.3 * click(L, 2500, 2, 300)
    return finish(lowpass(x, 3000), L, 0.0005, 0.02)


@sfx(-19, -6)
def draw_vanish():
    """An airy reversed whoosh falling away, with a glass note played backwards."""
    L = 0.5
    n = int(L * SR)
    u = np.linspace(0, 1, n)
    e = np.where(u < 0.4, (u / 0.4) ** 2, np.exp(-(u - 0.4) * 9))
    x = nsweep(L, 3000, 400, 1.3, 0.7) * e * 0.6
    rev = (bell("g6", 0.2, ((1, 1, 12), (2, 0.2, 20))) + bell("e6", 0.2, ((1, 0.7, 12),)))[::-1]
    place(x, rev * 0.5, 0.0)
    return finish(room(x, 0.5, 0.4), L, 0.004, 0.1)


@sfx(-27, -14)
def draw_stroke_start():
    """A soft pencil tap on paper (rapid)."""
    L = 0.06
    x = click(L, 3500, 1.5, 300) + 0.5 * bandpass(noise(int(L * SR)), 1100, 2) * env(int(L * SR), 120, 0.0005)
    x += 0.2 * thump(L, 220, 180, 120, 50)
    return finish(lowpass(x, 5000), L, 0.0005, 0.02)


@sfx(-26, -13)
def draw_stroke_end():
    """A short paper lift: a grainy scratch tail."""
    L = 0.1
    n = int(L * SR)
    grains = lowpass((rng.random(n) < 0.25).astype(float), 400) * 3
    x = bandpass(noise(n), 2800, 1.0) * grains * env(n, 35, 0.005)
    return finish(lowpass(x, 5000), L, 0.002, 0.03)


@sfx(-21, -8)
def draw_undo():
    """A quick eraser rub, rising."""
    L = 0.2
    n = int(L * SR)
    t = t_axis(n)
    x = nsweep(L, 900, 2000, 1.2) * np.abs(np.sin(2 * np.pi * 7.5 * t)) ** 1.5 * arch(n, 0.5)
    return finish(x + 0.2 * lowpass(noise(n), 500) * arch(n), L, 0.003, 0.03)


@sfx(-20, -7)
def draw_clear():
    """An eraser swipe that becomes a sheet whoosh."""
    L = 0.35
    n = int(L * SR)
    t = t_axis(n)
    rub = np.where(t < 0.12, np.abs(np.sin(2 * np.pi * 8 * t)) ** 1.5, 1.0)
    x = nsweep(L, 700, 2600, 0.8, 0.8) * rub * arch(n, 0.8) + 0.3 * lowpass(noise(n), 600) * arch(n)
    return finish(lowpass(x, 5500), L, 0.003, 0.05)


@sfx(-19, -6)
def draw_empty():
    """A dull soft 'nope': a felt thud and two muted low notes, down a semitone."""
    L = 0.15
    x = thump(L, 120, 60, 18)
    place(x, lowpass(inst(felt_piano, "c3", 0.05), 700), 0.0, 0.8)
    place(x, lowpass(inst(felt_piano, "b2", 0.05), 700), 0.06, 0.8)
    return finish(x, L, 0.001, 0.04)


@sfx(-19, -6)
def draw_time_low():
    """Two gentle warning pings on G5."""
    L = 0.4
    x = buf(L + 1)
    place(x, inst(mallet, "g5", 0.1), 0.0, 1.0)
    place(x, inst(mallet, "g5", 0.1), 0.18, 0.85)
    return finish(room(lowpass(x, 2500), 0.3, 0.3), L, 0.001, 0.12)


@sfx(-18, -5)
def draw_submit():
    """A paper slide and a soft stamp."""
    L = 0.3
    x = buf(L)
    n = int(0.18 * SR)
    place(x, nsweep(0.18, 1200, 1800, 0.9) * arch(n, 1.2) * 0.5, 0.0)
    place(x, thump(0.13, 140, 70, 25), 0.17)
    place(x, click(0.02, 1800, 1.5, 200) * 0.5, 0.17)
    return finish(x, L, 0.003, 0.04)


@sfx(-18, -5)
def draw_timeout():
    """A muted bell, falling a fourth (C6 to G5)."""
    L = 0.4
    n = int(L * SR)
    t = t_axis(n)
    f = hz("c6") * (hz("g5") / hz("c6")) ** ((t / L) ** 0.7)
    ph = np.cumsum(f) / SR
    s = (np.sin(2 * np.pi * ph) + 0.25 * np.sin(2 * np.pi * 2.4 * ph) * np.exp(-t * 9)
         + 0.1 * np.sin(2 * np.pi * 3 * ph) * np.exp(-t * 14)) * np.exp(-t * 6) * np.clip(t / 0.002, 0, 1)
    return finish(room(lowpass(s, 1800), 0.4, 0.3), L, 0.001, 0.1)


@sfx(-16, -4)
def draw_score_good():
    """A bright two-note chime, up a fifth: E5 then B5 (vibes and glass)."""
    L = 0.6
    x = buf(L + 1.5)
    for m, t0 in (("e5", 0.0), ("b5", 0.09)):
        place(x, inst(mallet, m, 0.3), t0, 1.0)
        place(x, inst(glass_keys, m, 0.2, 0.7), t0, 0.4)
    return finish(room(x, 0.6, 0.4), L, 0.001, 0.2)


@sfx(-18, -5)
def draw_score_ok():
    """A neutral single chime on D5: the second degree, Aron's unresolved note."""
    L = 0.4
    x = buf(L + 2.5)
    place(x, inst(mallet, "d5", 0.2), 0.0)
    place(x, inst(glass_keys, "d4", 0.2, 0.6), 0.0, 0.3)
    return finish(room(x, 0.4, 0.3), L, 0.001, 0.15)


@sfx(-18, -5)
def draw_score_bad():
    """A low soft descending tone: E4 sliding to C4."""
    L = 0.5
    n = int(L * SR)
    s = glide("e4", "c4", L, 0.8, ((1, 1.0), (2, 0.2)), vib=(4.5, 0.004)) * env(n, 3, 0.02)
    return finish(lowpass(s, 1200), L, 0.01, 0.12)


@sfx(-17, -4)
def draw_level_up():
    """A short ascending arpeggio, C E G, on felt piano and vibes."""
    L = 0.5
    x = buf(L + 1.5)
    for k, m in enumerate(["c5", "e5", "g5"]):
        place(x, inst(felt_piano, m, 0.2), 0.08 * k, 0.9)
        place(x, inst(mallet, m, 0.2, 0.7), 0.08 * k, 0.4)
    return finish(room(x, 0.5, 0.35), L, 0.001, 0.15)


@sfx(-16, -4)
def draw_trace():
    """A golden pen sweep (a scratchy glide up) with a lydian sparkle: C E F# G B."""
    L = 0.8
    x = buf(L + 1.5)
    n = int(0.35 * SR)
    grains = lowpass((rng.random(n) < 0.3).astype(float), 600) * 2.5
    place(x, nsweep(0.35, 1200, 4200, 1.2) * grains * arch(n) * 0.5, 0.0)
    for k, m in enumerate(["c6", "e6", "f#6", "g6", "b6"]):
        place(x, inst(glass_keys, m, 0.08, 0.7), 0.1 + 0.07 * k, 0.5)
    place(x, shimmer(0.7, ["g6", "b6", "e7"], 11, 0.05), 0.1)
    return finish(room(x, 0.7, 0.5), L, 0.002, 0.25)


# ---------------------------------------------------------------- Lantern Rhythm (lantern_*, E major)
# glass harmonica, vibes, felt piano, the warm kick; the bells sit on E5, the loop's tonic

@sfx(-25, -12)
def lantern_count():
    """A soft wooden count-in tick with a felt body (beats 1-3 of bar 1)."""
    L = 0.15
    x = knock(760, L, 50, 1.6) + 0.4 * thump(L, 200, 150, 40)
    return finish(lowpass(x, 3000), L, 0.0005, 0.05)


@sfx(-20, -7)
def lantern_go():
    """A brighter tick with a tiny E6 chime (beat 4 of bar 1)."""
    L = 0.3
    x = buf(L + 2.5)
    place(x, knock(980, 0.15, 45, 1.6), 0.0)
    place(x, inst(mallet, "e6", 0.1, 0.8), 0.004, 0.5)
    return finish(lowpass(x, 4000), L, 0.0005, 0.1)


@sfx(-17, -4)
def lantern_hit_perfect():
    """A soft glassy bell on E5, warm attack (pitched per lane: E, G#, B)."""
    L = 0.6
    x = buf(L + 2.5)
    place(x, inst(mallet, "e5", 0.3), 0.0, 1.0)
    place(x, inst(glass_keys, "e5", 0.2, 0.8), 0.0, 0.45)
    place(x, bell("e4", L, ((1, 1, 6),), attack=0.004), 0.0, 0.2)
    return finish(room(x, 0.5, 0.3), L, 0.002, 0.15)


@sfx(-19, -6)
def lantern_hit_good():
    """The same E5 bell, duller and muted (pitched per lane)."""
    L = 0.4
    x = buf(L + 2.5)
    place(x, inst(felt_piano, "e5", 0.15), 0.0, 1.0)
    place(x, inst(mallet, "e5", 0.15, 0.7), 0.0, 0.4)
    x = lowpass(x, 1300) * np.exp(-t_axis(len(x)) * 5)
    return finish(room(x, 0.3, 0.25), L, 0.002, 0.1)


@sfx(-18, -5)
def lantern_miss():
    """A lantern sputters: a small fizz, a papery puff and a low thump."""
    L = 0.5
    n = int(L * SR)
    t = t_axis(n)
    x = crackle(L, 0.012, 3200, 1.2) * np.exp(-t * 5) * 1.2
    x += bandpass(noise(n), 5000, 1.0) * np.exp(-t * 10) * 0.12
    p = int(0.09 * SR)
    place(x, lowpass(noise(p), 1500) * arch(p) * 0.5, 0.03)
    place(x, thump(0.3, 75, 52, 10), 0.04, 0.8)
    return finish(x, L, 0.002, 0.12)


@sfx(-26, -13)
def lantern_stray():
    """A quiet muffled paper tap."""
    L = 0.15
    n = int(L * SR)
    x = lowpass(noise(n), 900) * env(n, 80, 0.001) + 0.3 * thump(L, 160, 130, 40)
    return finish(x, L, 0.001, 0.05)


@sfx(-16, -4)
def lantern_streak():
    """The Lantern's rising answer as a shimmer: B5 C#6 E6 (5 6 1')."""
    L = 0.8
    x = buf(L + 2.5)
    for k, m in enumerate(["b5", "c#6", "e6"]):
        place(x, inst(glass_keys, m, 0.2, 0.8), 0.09 * k, 0.6)
        place(x, inst(mallet, m, 0.3, 0.8), 0.09 * k, 0.6)
    place(x, shimmer(0.7, ["e6", "g#6", "b6"], 12, 0.04), 0.1)
    return finish(room(x, 0.7, 0.45), L, 0.001, 0.25)


@sfx(-20, -7)
def lantern_streak_break():
    """A soft falling breathy whoosh: the flame leans and recovers."""
    L = 0.5
    n = int(L * SR)
    u = np.linspace(0, 1, n)
    x = nsweep(L, 1800, 300, 1.2, 0.8) * np.clip(u / 0.12, 0, 1) * np.exp(-u * 3)
    return finish(x, L, 0.003, 0.1)


@sfx(-18, -5)
def lantern_section():
    """A gentle swell into a chime that lands on the next downbeat (0.625 s = one beat at 96 BPM)."""
    L = 1.0
    beat = 0.625
    x = buf(L + 2.5)
    n = int(beat * SR)
    u = np.linspace(0, 1, n)
    sw = sum(bell(m, beat, ((1, 1, 0), (2.004, 0.3, 0)), attack=0.01) for m in ("e4", "g#4", "b4", "e5"))
    sw = sw * u ** 2.2 * np.clip((1 - u) / 0.04, 0, 1) * 0.3
    sw += bandpass(noise(n), 2500, 1.0) * u ** 3 * np.clip((1 - u) / 0.04, 0, 1) * 0.1
    place(x, sw, 0.0)
    place(x, inst(mallet, "e6", 0.3), beat, 0.9)
    place(x, inst(glass_keys, "e5", 0.3, 0.7), beat, 0.4)
    return finish(room(x, 0.6, 0.4), L, 0.005, 0.2)


@sfx(-17, -4)
def lantern_ember_help():
    """Ember helps: a warm swell, a choir-like hum on E major, a glint of the Lantern's answer."""
    L = 1.2
    x = buf(L + 3)
    for m in ("e3", "g#3", "b3", "e4"):
        place(x, inst(choir, m, 0.7), 0.0, 0.5)
        place(x, inst(warm_pad, m, 0.7, 0.7), 0.0, 0.4)
    place(x, inst(glass_harmonica, "c#6", 0.2, 0.6), 0.45, 0.4)
    place(x, inst(glass_harmonica, "e6", 0.3, 0.6), 0.6, 0.4)
    return finish(room(x, 0.8, 0.5), L, 0.01, 0.35)


@sfx(-16, -3)
def lantern_finale():
    """A shimmering bell cluster rising through E major and fading out."""
    L = 2.0
    x = buf(L + 2.5)
    for k, m in enumerate(["e5", "g#5", "b5", "c#6", "e6", "g#6", "b6"]):
        place(x, inst(mallet, m, 0.5), 0.07 * k, 0.7)
        place(x, inst(glass_keys, m, 0.3, 0.7), 0.07 * k + 0.01, 0.35)
    place(x, inst(glass_harmonica, "e5", 1.0, 0.7), 0.0, 0.5)
    place(x, inst(glass_harmonica, "b5", 1.0, 0.7), 0.1, 0.4)
    place(x, shimmer(1.6, ["e6", "b6", "e7"], 9, 0.04), 0.2)
    return finish(room(x, 1.2, 0.5), L, 0.002, 0.8)


# ---------------------------------------------------------------- Crown of the Worm (snake_*, G dorian)
# bubbles, pizzicato, bit-crush and pitch dives, as in the snake loop

@sfx(-27, -14)
def snake_turn():
    """A soft click (rapid)."""
    L = 0.04
    n = int(L * SR)
    x = click(L, 1800, 2, 250) + 0.4 * np.sin(2 * np.pi * 900 * t_axis(n)) * env(n, 200, 0.0005)
    return finish(x, L, 0.0005, 0.012)


def chomp():
    n = int(0.035 * SR)
    return bandpass(noise(n), 1500, 0.8) * env(n, 70, 0.001) + glide(300, 700, 0.035) * env(n, 50, 0.001) * 0.6


@sfx(-17, -4)
def snake_eat():
    """A crunchy bit-crushed bite: two quick chomps."""
    L = 0.15
    x = buf(L)
    place(x, chomp(), 0.0)
    place(x, chomp(), 0.06, 0.8)
    return finish(lowpass(crush(x, 6, 10, 5000), 5000), L, 0.001, 0.03)


@sfx(-18, -5)
def snake_boost():
    """A rising whoosh with a G4-to-G5 glide inside it, lightly crushed."""
    L = 0.3
    n = int(L * SR)
    x = nsweep(L, 400, 3500, 1.5, 1.3) * arch(n, 0.6) + 0.25 * glide("g4", "g5", L) * arch(n)
    return finish(crush(x, 3, 40, 6000), L, 0.003, 0.04)


@sfx(-21, -8)
def snake_boost_ready():
    """A tiny bright ping on D6."""
    L = 0.08
    x = bell("d6", L, ((1, 1, 40), (2, 0.2, 70)))
    return finish(x, L, 0.0008, 0.025)


@sfx(-17, -4)
def snake_filter_warn():
    """A glitchy two-tone alarm stutter, G5 and D5."""
    L = 0.6
    x = buf(L)
    t0 = 0.0
    for k, (m, d, reps) in enumerate((("g5", 0.07, 1), ("d5", 0.07, 1), ("g5", 0.025, 3), ("d5", 0.07, 1),
                                      ("g5", 0.07, 1), ("d5", 0.025, 3))):
        for r in range(reps):
            place(x, beep(m, d, 6), t0, 0.8)
            t0 += d + (0.008 if reps > 1 else 0.025)
    return finish(crush(x, 4, 16, 4500), L, 0.001, 0.05)


@sfx(-17, -4)
def snake_filter_on():
    """Static tearing open, pitch bending down."""
    L = 0.45
    n = int(L * SR)
    t = t_axis(n)
    gate = (lowpass((rng.random(n) < 0.5).astype(float), 60) > 0.45).astype(float)
    ph = np.cumsum(np.full(n, 110.0)) / SR
    buzz = sum(np.sin(2 * np.pi * k * ph) / k for k in range(1, 20))
    x = (bandpass(noise(n), 2000, 0.6) * (0.5 + 0.5 * gate) + 0.5 * buzz) * np.exp(-t * 3)
    x = dive(crush(x, 8, 8, 4500), cents=-1200, curve=1.0)
    return finish(lowpass(x, 5000), L, 0.002, 0.08)


@sfx(-18, -5)
def snake_filter_off():
    """Reversed static snapping back to clean, ending on a snap."""
    L = 0.3
    n = int(0.27 * SR)
    t = t_axis(n)
    st = crush(bandpass(noise(n), 1800, 0.6) * np.exp(-t * 9), 6, 10, 4500)[::-1]
    x = buf(L)
    place(x, st, 0.0, 0.8)
    place(x, click(0.02, 2500, 2, 300), 0.268, 1.0)
    return finish(x, L, 0.004, 0.02)


@sfx(-19, -6)
def snake_reshuffle():
    """A quick digital riffle: nine blips through G dorian."""
    L = 0.2
    x = buf(L)
    scale = ["g5", "a5", "bb5", "c6", "d6", "e6", "f6", "g6"]
    for k in range(9):
        m = scale[int(rng.integers(0, len(scale)))]
        n = int(0.016 * SR)
        place(x, np.sin(2 * np.pi * hz(m) * t_axis(n)) * env(n, 120, 0.001), 0.02 * k, 0.8)
    return finish(crush(x, 4, 24, 5000), L, 0.001, 0.03)


@sfx(-17, -4)
def snake_crown_appears():
    """A shimmering rising sparkle (G Bb D F G A) with a crushed echo: the crown pops in."""
    L = 0.9
    x = buf(L + 2.5)
    for k, m in enumerate(["g5", "bb5", "d6", "f6", "g6", "a6"]):
        place(x, inst(glass_keys, m, 0.1, 0.8), 0.06 * k, 0.6)
        place(x, inst(bubble, m, 0.1, 0.6), 0.06 * k + 0.02, 0.3)
    place(x, shimmer(0.7, ["d6", "g6", "a6"], 14, 0.04), 0.1)
    x[: int(L * SR)] += 0.25 * crush(np.concatenate([np.zeros(int(0.25 * SR)), x])[: int(L * SR)], 8, 12)
    return finish(room(x, 0.6, 0.4), L, 0.002, 0.3)


@sfx(-16, -3)
def snake_crown():
    """A triumphant fanfare on the System's three pulses: G G G, D, then G' on G major, with bubbles."""
    L = 1.5
    x = buf(L + 2.5)
    for m, t0, d in (("g4", 0.0, 0.07), ("g4", 0.1, 0.07), ("g4", 0.2, 0.07), ("d5", 0.3, 0.1), ("g5", 0.45, 0.7)):
        place(x, inst(soft_brass, midi_to_hz(note(m) - 12), d, 0.9), t0, 0.9)
        place(x, inst(pizzicato, m, d), t0, 0.6)
    for m in ("g3", "b3", "d4"):
        place(x, inst(soft_brass, m, 0.7, 0.7), 0.45, 0.45)
    for k, m in enumerate(["g5", "b5", "d6", "g6"]):
        place(x, inst(bubble, m, 0.1), 0.45 + 0.05 * k, 0.5)
    place(x, thump(0.4, 120, 70, 8), 0.45, 0.6)
    return finish(room(x, 0.9, 0.5), L, 0.003, 0.45)


@sfx(-17, -4)
def snake_rating():
    """A stamp thunk with a little sparkle."""
    L = 0.4
    x = buf(L + 2.5)
    place(x, thump(0.25, 130, 60, 16), 0.0)
    place(x, knock(400, 0.1, 40), 0.0, 0.4)
    place(x, click(0.02, 1500, 1.5, 250), 0.0, 0.5)
    place(x, inst(glass_keys, "d6", 0.05, 0.6), 0.08, 0.3)
    place(x, inst(glass_keys, "g6", 0.05, 0.6), 0.13, 0.3)
    return finish(room(x, 0.4, 0.3), L, 0.001, 0.12)


@sfx(-17, -4)
def snake_die():
    """A crunchy glitch collapse, falling: a G minor chord shredded, crushed and sunk."""
    L = 0.7
    x = buf(1.0)
    for m in ("g4", "bb4", "d5"):
        place(x, inst(glass_keys, m, 0.4), 0.0, 0.6)
    n = int(0.5 * SR)
    place(x, bandpass(noise(n), 1500, 0.7) * env(n, 6), 0.0, 0.4)
    x = glitch(x[: int(0.6 * SR)], seed=5)
    x = dive(crush(x, 8, 10, 4000), cents=-1500, curve=1.2)
    return finish(x * np.exp(-t_axis(len(x)) * 2), L, 0.002, 0.15)


@sfx(-18, -5)
def snake_shed():
    """A papery rip and an airy shimmer: the skin peels off."""
    L = 0.5
    n = int(0.28 * SR)
    t = t_axis(n)
    rip = bandpass(noise(n), 2200, 0.7) * (0.3 + 0.7 * (lowpass(rng.random(n), 300) > 0.5)) \
        * np.clip(t / 0.005, 0, 1) * np.exp(-t * 8)
    x = buf(L)
    place(x, rip, 0.0)
    place(x, shimmer(0.4, ["d6", "g6", "a6"], 12, 0.08), 0.1)
    return finish(room(lowpass(x, 5500), 0.4, 0.3), L, 0.002, 0.08)


@sfx(-21, -8)
def snake_shed_fading():
    """Three quick ticks on G6: the cheat is running out."""
    L = 0.35
    x = buf(L)
    n = int(0.05 * SR)
    tick = np.sin(2 * np.pi * hz("g6") * t_axis(n)) * env(n, 90, 0.0005) + 0.4 * click(0.05, 3500, 2, 250)
    for k in range(3):
        place(x, tick, 0.11 * k, 1.0 - 0.15 * k)
    return finish(crush(x, 2, 48, 6000), L, 0.0005, 0.05)


@sfx(-19, -6)
def snake_shed_end():
    """A soft thump: the skin turns solid again."""
    L = 0.25
    x = thump(L, 110, 55, 14) + 0.4 * knock(300, L, 35) + 0.1 * lowpass(noise(int(L * SR)), 800) * env(int(L * SR), 40)
    return finish(x, L, 0.001, 0.06)


@sfx(-19, -6)
def snake_wrap():
    """A warbly teleport blip through the wall."""
    L = 0.15
    n = int(L * SR)
    x = glide(600, 1400, L, 1.0, ((1, 1.0), (2, 0.2)), vib=(35, 0.06)) * arch(n, 0.7)
    return finish(crush(x, 4, 20, 5000), L, 0.002, 0.03)


@sfx(-21, -8)
def snake_phase():
    """A ghostly whoosh: passing through itself."""
    L = 0.12
    n = int(L * SR)
    t = t_axis(n)
    ghost = sum(np.sin(2 * np.pi * f * t) for f in (hz("g5"), hz("g5") * 1.02, hz("d6"))) * 0.3
    x = (nsweep(L, 1500, 700, 2.0) + ghost) * arch(n)
    return finish(lowpass(x, 4000), L, 0.002, 0.03)


# ---------------------------------------------------------------- Miso's Hunt (miso_*, D minor)
# pizzicato, vibes, a hint of glitch; the synthesized cat of the `miso` cues

@sfx(-28, -15)
def miso_step():
    """A soft paw pad on wood (quiet, frequent)."""
    L = 0.08
    n = int(L * SR)
    x = knock(220, L, 60, 2.1) + 0.25 * lowpass(noise(n), 1200) * env(n, 120, 0.001)
    return finish(lowpass(x, 2500), L, 0.001, 0.025)


def mrrp(seconds, f0, f1, gain=1.0):
    """A little cat chirp: a short rising 'mrr-ip' with a rolled r."""
    return cat_voice(seconds, lambda u: (f0 + (f1 - f0) * u ** 0.7) * (1 + 0.05 * np.sin(2 * np.pi * 28 * u * seconds)),
                     lambda u: 500 + 500 * u, lambda u: 1300 + 500 * u,
                     lambda u: np.clip(u / 0.15, 0, 1) * np.clip((1 - u) / 0.3, 0, 1)) * gain


@sfx(-18, -5)
def miso_pounce():
    """A quick airy whoosh and a small chirp."""
    L = 0.25
    x = buf(L)
    n = int(0.2 * SR)
    place(x, nsweep(0.2, 600, 2200, 1.3) * arch(n, 1.3) * 0.6, 0.0)
    place(x, mrrp(0.09, 700, 1050, 0.5), 0.12)
    return finish(x, L, 0.003, 0.04)


@sfx(-17, -4)
def miso_catch():
    """A bright glitchy pop: a pixel being eaten (D6, A6)."""
    L = 0.2
    x = buf(L)
    n = int(0.04 * SR)
    place(x, glide(400, 1200, 0.04, 0.5) * env(n, 50, 0.001), 0.0)
    for k, m in enumerate(["d6", "a6"]):
        m_n = int(0.04 * SR)
        place(x, np.sin(2 * np.pi * hz(m) * t_axis(m_n)) * env(m_n, 60, 0.001), 0.035 + 0.04 * k, 0.6)
    return finish(crush(x, 4, 16, 5000), L, 0.001, 0.04)


@sfx(-17, -4)
def miso_combo():
    """A rising three-note sparkle on pizzicato and glass: D F A."""
    L = 0.4
    x = buf(L + 2.5)
    for k, m in enumerate(["d5", "f5", "a5"]):
        place(x, inst(pizzicato, m, 0.1), 0.06 * k, 0.9)
        place(x, inst(glass_keys, note_hz(m, 12), 0.08, 0.6), 0.06 * k, 0.3)
    return finish(room(x, 0.4, 0.3), L, 0.001, 0.12)


def note_hz(m, semis=0):
    return midi_to_hz(note(m) + semis)


@sfx(-19, -6)
def miso_combo_break():
    """A soft falling two-note tone: A4 to F4, muted vibes."""
    L = 0.35
    x = buf(L + 2.5)
    place(x, inst(mallet, "a4", 0.1), 0.0, 1.0)
    place(x, inst(mallet, "f4", 0.15), 0.12, 0.9)
    return finish(lowpass(x, 1800), L, 0.001, 0.1)


@sfx(-20, -7)
def miso_whiff():
    """Paws landing on nothing: two soft thumps."""
    L = 0.15
    x = buf(L)
    for t0, g in ((0.0, 1.0), (0.035, 0.7)):
        place(x, thump(0.1, 160, 80, 30), t0, g)
        place(x, lowpass(noise(int(0.03 * SR)), 900) * env(int(0.03 * SR), 100), t0, 0.15)
    return finish(x, L, 0.001, 0.04)


@sfx(-18, -5)
def miso_dot_spawn():
    """A dot leaks out of the wall: crackly bit-crushed fizz with a wet seep."""
    L = 0.5
    n = int(L * SR)
    u = np.linspace(0, 1, n)
    fizz = crush(crackle(L, 0.03, 3000, 1.0) + 0.2 * bandpass(noise(n), 4000, 1.0), 6, 8, 5000) * arch(n, 0.7)
    seep = sweep(lowpass(noise(n), 1500), "bp", (400 * (900 / 400) ** u)[::32], 6.0) * arch(n, 1.5) * 2.5
    return finish(fizz * 0.7 + seep, L, 0.004, 0.08)


@sfx(-20, -7)
def miso_dot_fade():
    """A short digital fizzle down to silence: the resolution drops as it goes."""
    L = 0.3
    n = int(L * SR)
    src = (bandpass(noise(n), 2500, 1.0) * 0.5 + np.sin(2 * np.pi * hz("d6") * t_axis(n)) * 0.5) * np.exp(-t_axis(n) * 9)
    x = np.zeros(n)
    seg = n // 6
    for k in range(6):                   # coarser and coarser
        a, b = k * seg, (k + 1) * seg if k < 5 else n
        x[a:b] = crush(src, 2 + 3 * k, max(4, 32 - 5 * k), 5000)[a:b]
    return finish(lowpass(x, 5000), L, 0.002, 0.06)


@sfx(-22, -9)
def miso_dot_blink():
    """A tiny teleport zap."""
    L = 0.1
    n = int(0.04 * SR)
    x = buf(L)
    place(x, glide(2000, 600, 0.04) * env(n, 40, 0.0005), 0.0)
    place(x, click(0.02, 3000, 2, 300) * 0.4, 0.0)
    return finish(crush(x, 3, 24, 5000), L, 0.0005, 0.03)


@sfx(-19, -6)
def miso_dot_flee():
    """A skittering glitch squeak: five tiny squeaks running off."""
    L = 0.25
    x = buf(L)
    for k in range(5):
        n = int(0.025 * SR)
        f0 = 1200 + 150 * float(rng.random())
        place(x, glide(f0, f0 * 1.5, 0.025) * arch(n), 0.04 * k + 0.008 * float(rng.random()), 0.7 - 0.08 * k)
        place(x, click(0.01, 3500, 2, 400) * 0.3, 0.04 * k)
    return finish(crush(x, 3, 28, 5000), L, 0.001, 0.03)


@sfx(-18, -5)
def miso_beam_on():
    """A beam fades in: a soft airy choir swell on D minor, glass on top."""
    L = 1.0
    x = buf(L + 3)
    for m in ("d4", "f4", "a4"):
        place(x, inst(choir, m, 0.6), 0.0, 0.6)
    place(x, inst(glass_harmonica, "a5", 0.5, 0.6), 0.2, 0.35)
    n = int(L * SR)
    x[:n] += nsweep(L, 1500, 3000, 2.0) * arch(n, 2) * 0.04
    return finish(room(x, 0.7, 0.4), L, 0.01, 0.25)


@sfx(-20, -7)
def miso_beam_sweep():
    """A beam is near: a low gentle hum (D3, A3) and a slow whoosh."""
    L = 0.6
    n = int(L * SR)
    t = t_axis(n)
    hum = (np.sin(2 * np.pi * hz("d3") * t) + 0.5 * np.sin(2 * np.pi * hz("a3") * t)
           + 0.2 * np.sin(2 * np.pi * hz("d4") * t)) * (1 + 0.15 * np.sin(2 * np.pi * 3 * t))
    x = (hum * 0.6 + nsweep(L, 300, 900, 2.0) * 0.5) * arch(n, 1.2)
    return finish(x, L, 0.005, 0.08)


@sfx(-16, -4)
def miso_spotted():
    """Spotted: a bright angelic 'ting' (A6 over D6) and a startled 'mrrp?!'."""
    L = 0.6
    x = buf(L + 2.5)
    place(x, bell("a6", 0.6, ((1, 1, 5), (2.76, 0.2, 12))), 0.0, 0.6)
    place(x, inst(glass_keys, "d6", 0.2, 0.7), 0.0, 0.4)
    q = cat_voice(0.22, lambda u: 500 + 380 * u ** 1.5, lambda u: 600 + 500 * u, lambda u: 1100 + 700 * u,
                  lambda u: np.clip(u / 0.12, 0, 1) * np.clip((1 - u) / 0.2, 0, 1))
    place(x, q * 0.9, 0.14)
    return finish(room(x, 0.5, 0.3), L, 0.001, 0.12)


@sfx(-20, -7)
def miso_recover():
    """A little shake-off ruffle: the fur fluffs back."""
    L = 0.3
    n = int(L * SR)
    t = t_axis(n)
    x = (bandpass(noise(n), 2500, 0.8) * 0.6 + lowpass(noise(n), 700) * 0.4) \
        * (0.3 + 0.7 * np.abs(np.sin(2 * np.pi * 11 * t))) * arch(n, 0.8)
    return finish(lowpass(x, 5000), L, 0.004, 0.05)


@sfx(-18, -5)
def miso_phase():
    """The leak widens: a low glitch rumble (D2) with a warble."""
    L = 0.8
    n = int(L * SR)
    t = t_axis(n)
    f = hz("d2") * (1 + 0.03 * np.sin(2 * np.pi * 5 * t))
    ph = np.cumsum(f) / SR
    tone = sum(np.sin(2 * np.pi * k * ph) / k for k in range(1, 12))
    x = (lowpass(tone, 600) + 0.6 * lowpass(noise(n), 200)) * arch(n, 0.8)
    x = glitch(x, seed=9)[:n]
    return finish(crush(x, 6, 16, 2500), L, 0.004, 0.12)


@sfx(-18, -5)
def miso_nap():
    """The nap cheat: a cat yawn sinking into a soft purr."""
    L = 0.9
    x = buf(L)
    yawn = cat_voice(0.45, lambda u: 680 - 300 * u ** 0.8, lambda u: 800 - 350 * u, lambda u: 1500 - 650 * u,
                     lambda u: np.clip(u / 0.1, 0, 1) * np.clip((1 - u) / 0.35, 0, 1), q1=3.0)
    place(x, yawn * 0.8, 0.0)
    n = int(0.55 * SR)
    t = t_axis(n)
    purr = lowpass(noise(n), 400) * (0.5 + 0.5 * np.sin(2 * np.pi * 24 * t)) ** 2 \
        + 0.3 * np.sin(2 * np.pi * 48 * t) * (0.5 + 0.5 * np.sin(2 * np.pi * 24 * t))
    place(x, purr * arch(n, 0.6) * 0.8, 0.35)
    return finish(x, L, 0.004, 0.15)


@sfx(-19, -6)
def miso_wake():
    """Nap's over: a small chirpy trill rising."""
    L = 0.3
    v = cat_voice(L, lambda u: (700 + 300 * u) * (1 + 0.09 * np.sign(np.sin(2 * np.pi * 26 * u * L))),
                  lambda u: 600 + 300 * u, lambda u: 1500 + 400 * u,
                  lambda u: np.clip(u / 0.1, 0, 1) * np.clip((1 - u) / 0.25, 0, 1))
    return finish(lowpass(v, 4000), L, 0.003, 0.05)


@sfx(-20, -7)
def miso_bird():
    """A robin outside: three quick whistled phrases."""
    L = 0.4
    x = buf(L)
    for t0, f0, f1, d in ((0.0, 2800, 2200, 0.07), (0.1, 3200, 2600, 0.06), (0.19, 2500, 3100, 0.09)):
        n = int(d * SR)
        place(x, glide(f0, f1, d, 0.8, ((1, 1.0), (2, 0.05)), vib=(70, 0.02)) * arch(n, 0.8), t0, 0.7)
    return finish(room(lowpass(x, 5000), 0.4, 0.3), L, 0.002, 0.05)


@sfx(-23, -11)
def miso_tick():
    """A soft clock tick with a little tock (the last five seconds)."""
    L = 0.1
    n = int(0.05 * SR)
    x = buf(L)
    place(x, np.sin(2 * np.pi * 1100 * t_axis(n)) * env(n, 110, 0.0005) + 0.4 * click(0.05, 3000, 2, 250), 0.0)
    place(x, knock(520, 0.05, 90, 1.6) * 0.4, 0.004)
    return finish(x, L, 0.0005, 0.03)


@sfx(-17, -4)
def miso_time_up():
    """A gentle bell on D5, the hunt's tonic."""
    L = 0.6
    x = buf(L + 2.5)
    place(x, bell("d5", L, ((1, 1, 4), (2.0, 0.3, 6), (3.0, 0.1, 10)), attack=0.003), 0.0)
    place(x, inst(mallet, "d6", 0.2, 0.6), 0.0, 0.25)
    return finish(room(x, 0.6, 0.35), L, 0.002, 0.18)


@sfx(-16, -4)
def miso_meow():
    """The closing 'Meow.': clear and content, a little lower and longer than the quiz's chirp."""
    L = 0.7
    v = cat_voice(L, lambda u: (470 + 180 * np.sin(np.pi * np.clip(u / 0.55, 0, 1)) - 110 * np.clip((u - 0.5) / 0.5, 0, 1))
                  * (1 + 0.01 * np.sin(2 * np.pi * 5.5 * u * L)),
                  lambda u: 330 + 420 * np.clip((u - 0.1) / 0.55, 0, 1) - 150 * np.clip((u - 0.7) / 0.3, 0, 1),
                  lambda u: 2000 - 1150 * np.clip((u - 0.1) / 0.7, 0, 1),
                  lambda u: np.clip(u / 0.06, 0, 1) ** 2 * np.sin(np.pi * u) ** 0.5 * (1 - 0.3 * u))
    return finish(room(v, 0.5, 0.3), L, 0.004, 0.1)


# ---------------------------------------------------------------- The Hungry Sky (invaders_*: waves in B minor,
# the boss in C minor). Choir, glass, the hungry bass; most are played at rate 0.95-1.05.

@sfx(-21, -8)
def invaders_shoot():
    """A soft bright glassy 'pew' of light (F#6 falling to B5)."""
    L = 0.12
    n = int(L * SR)
    x = glide("f#6", "b5", L, 0.5, ((1, 1.0), (2, 0.15))) * env(n, 22, 0.001)
    return finish(x, L, 0.0008, 0.03)


@sfx(-19, -6)
def invaders_hit_spirit():
    """A small airy pop with a sparkle tail."""
    L = 0.3
    x = buf(L + 2.5)
    place(x, glide(500, 900, 0.03) * env(int(0.03 * SR), 60, 0.001), 0.0)
    place(x, highpass(click(0.04, 2500, 0.8, 120), 800), 0.0, 0.35)
    for k, m in enumerate(["b6", "f#6", "d7"]):
        place(x, inst(glass_keys, m, 0.04, 0.5), 0.04 + 0.04 * k, 0.45)
    return finish(room(x, 0.3, 0.3), L, 0.001, 0.1)


@sfx(-17, -4)
def invaders_hit_angel():
    """A bright chime burst (B D F#) with a feather flutter."""
    L = 0.4
    x = buf(L + 2.5)
    for k, m in enumerate(["b5", "d6", "f#6"]):
        place(x, inst(mallet, m, 0.15), 0.015 * k, 0.6)
    n = int(0.25 * SR)
    t = t_axis(n)
    place(x, bandpass(noise(n), 3000, 0.9) * np.abs(np.sin(2 * np.pi * 18 * t)) * env(n, 10, 0.01) * 0.4, 0.03)
    return finish(room(x, 0.4, 0.3), L, 0.001, 0.12)


@sfx(-19, -6)
def invaders_angel_armor():
    """A metallic 'ting': a captain's armour takes the first hit."""
    L = 0.15
    x = bell(1480, L, ((1, 1, 22), (2.41, 0.5, 30), (3.87, 0.3, 40), (5.2, 0.15, 60))) + 0.3 * click(L, 4000, 2, 300)
    return finish(x, L, 0.0005, 0.04)


@sfx(-19, -6)
def invaders_enemy_shot():
    """A low golden bell-tone launch (F#4, bending up)."""
    L = 0.25
    n = int(L * SR)
    x = glide("f#4", "a4", L, 0.4, ((1, 1.0), (2, 0.3), (3, 0.12))) * env(n, 9, 0.004)
    return finish(lowpass(x, 2200), L, 0.002, 0.05)


@sfx(-23, -10)
def invaders_wisp():
    """A faint breathy whoosh."""
    L = 0.25
    n = int(L * SR)
    return finish(nsweep(L, 1200, 2200, 1.5) * arch(n, 1.5), L, 0.003, 0.04)


@sfx(-19, -6)
def invaders_dive():
    """A rising-then-falling wing swoop."""
    L = 0.6
    n = int(L * SR)
    u = np.linspace(0, 1, n)
    centre = 500 + 1500 * np.sin(np.pi * u) ** 1.2
    flap = 0.6 + 0.4 * np.abs(np.sin(2 * np.pi * 6 * u * L))
    x = sweep(noise(n), "bp", centre[::32], 1.6) * flap * arch(n, 1.2)
    return finish(x, L, 0.004, 0.06)


@sfx(-22, -9)
def invaders_step():
    """A soft low thump as the formation steps down (B1)."""
    L = 0.12
    return finish(thump(L, hz("b2"), hz("b1"), 26, 40), L, 0.001, 0.03)


@sfx(-18, -5)
def invaders_overrun():
    """An ominous low swell: the hungry bass rising from below (B1 and C2 rubbing)."""
    L = 0.6
    n = int(L * SR)
    u = np.linspace(0, 1, n)
    x = sum(glide(f, f, L, harmonics=tuple((k, 1 / k) for k in range(1, 10))) for f in (hz("b1"), hz("c2")))
    x = sweep(x, "lp", (150 + 900 * u ** 2)[::32], 1.5) * u ** 1.5 * np.clip((1 - u) / 0.12, 0, 1)
    return finish(x, L, 0.01, 0.06)


@sfx(-18, -5)
def invaders_player_hit():
    """A crackling impact: a lantern sputters."""
    L = 0.35
    n = int(L * SR)
    t = t_axis(n)
    x = crackle(L, 0.02, 3000, 1.0) * np.exp(-t * 8) * 1.2 + thump(L, 120, 60, 14) * 0.9
    p = int(0.06 * SR)
    place(x, lowpass(noise(p), 1500) * arch(p) * 0.5, 0.01)
    return finish(x, L, 0.001, 0.08)


@sfx(-18, -5)
def invaders_life_lost():
    """A two-note falling chime: F#5 to B4."""
    L = 0.6
    x = buf(L + 2.5)
    place(x, inst(mallet, "f#5", 0.15), 0.0, 1.0)
    place(x, inst(mallet, "b4", 0.3), 0.16, 1.0)
    place(x, inst(glass_keys, "b4", 0.3, 0.6), 0.16, 0.3)
    return finish(room(x, 0.5, 0.35), L, 0.001, 0.18)


@sfx(-17, -4)
def invaders_game_over():
    """A lantern going out: the Lantern's answer slowed and sinking (C#5 B4 ... F#4), dimming."""
    L = 1.5
    x = buf(L + 2.5)
    for k, (m, t0) in enumerate((("d5", 0.0), ("c#5", 0.3), ("b4", 0.6), ("f#4", 0.9))):
        place(x, lowpass(inst(glass_harmonica, m, 0.3, 0.8), 2200 - 400 * k), t0, 0.9 - 0.1 * k)
    n = int(L * SR)
    x[:n] *= np.exp(-np.linspace(0, 1, n) * 1.2)
    return finish(room(x, 0.9, 0.4), L, 0.01, 0.45)


@sfx(-16, -4)
def invaders_wave_clear():
    """A short triumphant shimmer arpeggio: B D F# B D' F#' on glass and vibes."""
    L = 1.0
    x = buf(L + 2.5)
    for k, m in enumerate(["b4", "d5", "f#5", "b5", "d6", "f#6"]):
        place(x, inst(mallet, m, 0.3), 0.06 * k, 0.7)
        place(x, inst(glass_keys, m, 0.2, 0.6), 0.06 * k, 0.3)
    place(x, shimmer(0.8, ["b6", "f#6"], 12, 0.04), 0.15)
    return finish(room(x, 0.8, 0.45), L, 0.001, 0.3)


@sfx(-18, -5)
def invaders_wave_start():
    """'Here they come': a brief rising swell of choir and air."""
    L = 0.6
    x = buf(L + 3)
    for m in ("b3", "f#4"):
        place(x, inst(choir, m, 0.4), 0.0, 0.5)
    n = int(L * SR)
    u = np.linspace(0, 1, n)
    x[:n] = x[:n] * u + nsweep(L, 400, 2500, 1.5, 1.3) * u ** 2 * 0.3
    return finish(x, L, 0.01, 0.06)


@sfx(-16, -3)
def invaders_golden_light():
    """The cheat: a huge warm choir-like bloom on B major, glass blazing above."""
    L = 1.2
    x = buf(L + 3)
    for m in ("b2", "f#3", "b3", "d#4", "f#4"):
        place(x, inst(choir, m, 0.8), 0.0, 0.5)
        place(x, inst(warm_pad, m, 0.8, 0.8), 0.0, 0.4)
    for k, m in enumerate(["b5", "d#6", "f#6"]):
        place(x, inst(glass_harmonica, m, 0.6, 0.6), 0.1 + 0.08 * k, 0.3)
    return finish(room(x, 1.0, 0.5), L, 0.02, 0.35)


def hungry_voice(seconds, f, vowel=(380, 800), amp=None):
    """A huge child's 'oooh': a low voice through dark formants (C minor boss)."""
    amp = amp or (lambda u: np.sin(np.pi * u) ** 0.7)
    return cat_voice(seconds, f, lambda u: vowel[0] + 0 * u, lambda u: vowel[1] + 0 * u, amp, q1=3.0, q2=4.0,
                     harmonics=14)


@sfx(-16, -4)
def invaders_boss_roar():
    """The boss: a childlike but huge hungry 'oooh' (C3 sagging to Ab2) over a deep rumble."""
    L = 1.5
    n = int(L * SR)
    v = hungry_voice(L, lambda u: hz("c3") * (hz("ab2") / hz("c3")) ** (u ** 1.5) * (1 + 0.015 * np.sin(2 * np.pi * 5 * u * L)))
    v += 0.5 * hungry_voice(L, lambda u: hz("c4") * (hz("ab3") / hz("c4")) ** (u ** 1.5))
    rumble = lowpass(noise(n), 120) * 3 + 0.6 * glide("c1", "c1", L)
    return finish(room((v + rumble * 0.5) * arch(n, 0.5), 0.9, 0.4), L, 0.02, 0.3)


@sfx(-18, -5)
def invaders_boss_phase():
    """A hungry growl, a stomach rumble."""
    L = 0.8
    n = int(L * SR)
    t = t_axis(n)
    f = hz("c2") * (1 + 0.04 * np.sin(2 * np.pi * 3 * t))
    ph = np.cumsum(f) / SR
    tone = sum(np.sin(2 * np.pi * k * ph) / k for k in range(1, 14))
    gurgle = lowpass(noise(n), 300) * (0.5 + 0.5 * np.sin(2 * np.pi * 9 * t + 2 * np.sin(2 * np.pi * 1.3 * t)))
    x = sweep(tone, "lp", (200 + 300 * arch(n))[::32], 2.0) + gurgle * 1.5
    return finish(x * arch(n, 0.6), L, 0.01, 0.1)


@sfx(-19, -6)
def invaders_boss_spread():
    """A soft breath out with a scatter of light tones (C minor)."""
    L = 0.4
    n = int(L * SR)
    u = np.linspace(0, 1, n)
    x = nsweep(L, 1200, 500, 1.0) * np.clip(u / 0.05, 0, 1) * np.exp(-u * 4) * 0.7
    x = np.concatenate([x, np.zeros(int(2.5 * SR))])
    for k, m in enumerate(["g5", "eb6", "c6", "bb5", "g6"]):
        place(x, inst(music_box_hz, m, 0.05), 0.04 + 0.05 * k, 0.3)
    return finish(x, L, 0.004, 0.08)


def music_box_hz(f, dur, vel=1.0):
    from vnsynth import music_box
    return music_box(f, dur, vel)


@sfx(-18, -5)
def invaders_boss_pull():
    """A deep inhale that starts the vortex."""
    L = 1.0
    n = int(L * SR)
    u = np.linspace(0, 1, n)
    x = nsweep(L, 300, 1400, 1.2, 1.4) * u ** 1.5 * np.clip((1 - u) / 0.08, 0, 1)
    x += lowpass(noise(n), 150) * u * 1.5 * np.clip((1 - u) / 0.08, 0, 1)
    return finish(x, L, 0.02, 0.06)


@sfx(-18, -5)
def invaders_boss_pull_end():
    """A satisfied little 'mm'."""
    L = 0.4
    v = cat_voice(L, lambda u: hz("g3") * (1 + 0.06 * np.sin(np.pi * u)), lambda u: 280 + 0 * u, lambda u: 1100 + 0 * u,
                  lambda u: np.clip(u / 0.1, 0, 1) * np.clip((1 - u) / 0.3, 0, 1), q1=5.0, q2=6.0)
    return finish(lowpass(v, 1500), L, 0.004, 0.08)


@sfx(-17, -4)
def invaders_boss_spit():
    """A wet-cute 'ptoo' and two tiny sparkle pops."""
    L = 0.4
    x = buf(L + 2.5)
    place(x, click(0.015, 2500, 1.2, 300), 0.0, 0.7)
    v = cat_voice(0.14, lambda u: 420 - 120 * u, lambda u: 500 - 150 * u, lambda u: 1200 - 400 * u,
                  lambda u: np.clip(u / 0.1, 0, 1) * (1 - u) ** 1.5)
    place(x, v, 0.012, 0.8)
    for k, m in enumerate(["eb6", "g6"]):
        place(x, glide(hz(m) * 0.7, hz(m), 0.03) * env(int(0.03 * SR), 50, 0.001), 0.18 + 0.08 * k, 0.4)
    return finish(x, L, 0.0008, 0.08)


@sfx(-19, -6)
def invaders_boss_hit():
    """A dull soft thud with a pitch-bent 'hm'."""
    L = 0.15
    x = thump(L, 110, 60, 20)
    v = cat_voice(L, lambda u: 200 * (1 + 0.25 * u), lambda u: 300 + 0 * u, lambda u: 1000 + 0 * u,
                  lambda u: np.clip(u / 0.15, 0, 1) * (1 - u), q1=5.0)
    return finish(x + 0.6 * v, L, 0.001, 0.04)


@sfx(-18, -5)
def invaders_boss_gulp():
    """A gulp and slurp: the shot goes into the open mouth."""
    L = 0.25
    x = buf(L)
    n = int(0.12 * SR)
    u = np.linspace(0, 1, n)
    slurp = sweep(noise(n), "bp", (1200 - 700 * u)[::32], 3.0) * arch(n)
    place(x, slurp * 0.6, 0.0)
    m = int(0.09 * SR)
    gulp = glide(320, 140, 0.09, 0.6, ((1, 1.0), (2, 0.3))) * env(m, 20, 0.004)
    place(x, bandpass(gulp, 300, 2) * 2 + gulp * 0.5, 0.11)
    return finish(x, L, 0.002, 0.04)


@sfx(-16, -3)
def invaders_boss_defeat():
    """A big glowing release winding down: the hunger lets go, warm C major light pouring out."""
    L = 2.0
    x = buf(L + 3)
    n = int(L * SR)
    u = np.linspace(0, 1, n)
    x[:n] += nsweep(L, 2500, 300, 1.0, 0.7) * np.exp(-u * 3) * 0.4
    x[:n] += hungry_voice(L, lambda u: hz("c3") * (hz("g2") / hz("c3")) ** u, amp=lambda u: np.exp(-u * 3)) * 0.6
    for m in ("c3", "g3", "c4", "e4", "g4"):
        place(x, inst(choir, m, 1.2), 0.1, 0.4)
    for k, m in enumerate(["c6", "g5", "e5", "c5", "g4"]):
        place(x, inst(mallet, m, 0.4), 0.2 + 0.18 * k, 0.5)
    return finish(room(x, 1.2, 0.5), L, 0.004, 0.7)


@sfx(-19, -6)
def invaders_boss_sleep():
    """A tiny yawn into a soft snore: the vampire, full at last."""
    L = 1.5
    x = buf(L)
    yawn = cat_voice(0.5, lambda u: 420 - 180 * u ** 0.8, lambda u: 700 - 300 * u, lambda u: 1300 - 500 * u,
                     lambda u: np.clip(u / 0.12, 0, 1) * np.clip((1 - u) / 0.35, 0, 1), q1=3.0)
    place(x, yawn * 0.8, 0.0)
    for t0 in (0.6, 1.05):
        m = int(0.38 * SR)
        snore = lowpass(noise(m), 500) * (0.6 + 0.4 * np.sin(2 * np.pi * 30 * t_axis(m))) + \
            0.5 * glide(90, 80, 0.38, harmonics=((1, 1.0), (2, 0.5), (3, 0.3)))
        place(x, snore * arch(m, 1.5) * 0.5, t0)
    return finish(x, L, 0.004, 0.12)


# ================================================================ Round 2: the redesigned minigames

VOWELS = {"a": (750, 1200), "e": (500, 1800), "i": (320, 2300), "o": (450, 850), "u": (330, 800),
          "m": (280, 1100), "uh": (550, 1050)}


def voice(seconds, pitch, v0="a", v1=None, amp=None, breath=0.0, q=(3.5, 4.5)):
    """A cute wordless voice: `pitch` is a function of u (0..1), the formants slide from vowel v0 to v1."""
    a, b = VOWELS[v0], VOWELS[v1 or v0]
    amp = amp or (lambda u: np.clip(u / 0.1, 0, 1) * np.clip((1 - u) / 0.25, 0, 1))
    v = cat_voice(seconds, pitch, lambda u: a[0] + (b[0] - a[0]) * u, lambda u: a[1] + (b[1] - a[1]) * u, amp,
                  q1=q[0], q2=q[1])
    if breath:
        n = len(v)
        u = np.linspace(0, 1, n)
        v += bandpass(noise(n), (a[1] + b[1]) / 2, 1.2) * amp(u) * breath
    return v


def doppler(seconds, f_tone=520, band=(600, 1800, 500), shift=1.3):
    """Something flying past: a band of air rising and falling, a tone that drops as it passes."""
    n = int(seconds * SR)
    u = np.linspace(0, 1, n)
    near = np.exp(-((u - 0.5) / 0.18) ** 2)                  # loudest as it passes
    centre = np.where(u < 0.5, band[0] + (band[1] - band[0]) * (u / 0.5),
                      band[1] + (band[2] - band[1]) * ((u - 0.5) / 0.5))
    air = sweep(noise(n), "bp", centre[::32], 1.4)
    f = f_tone * shift ** (-np.arctan((u - 0.5) * 12) / (np.pi / 2))
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR)
    return (air * 0.7 + tone * 0.15) * near


def squeak(seconds, f0, f1, rough=0.3):
    """Stick-slip squeak (marker on a board, rubber soles): a buzzy tone with jittered pitch."""
    n = int(seconds * SR)
    u = np.linspace(0, 1, n)
    jitter = 1 + rough * 0.05 * lowpass(noise(n), 60) * 4
    f = (f0 + (f1 - f0) * u) * jitter
    ph = np.cumsum(f) / SR
    src = sum(np.sin(2 * np.pi * k * ph) / k ** 0.9 for k in range(1, 8))
    return bandpass(src, (f0 + f1) / 2 * 1.5, 1.2) + 0.3 * src * 0.2


# ---------------------------------------------------------------- quiz, round 2 (Adjutant Vael)

@sfx(-20, -8)
def quiz_angel_voice():
    """One sung syllable of the angel: a soft bell-like 'oo-ah', neutral pitch (A3; played at 1.2-1.45x)."""
    L = 0.08
    n = int(L * SR)
    v = voice(L, lambda u: hz("a3") * (1 + 0.04 * u), "u", "a", lambda u: np.sin(np.pi * u) ** 0.8)
    v += bell("a3", L, ((1, 1, 20), (2, 0.4, 30), (3, 0.15, 45))) * arch(n, 0.6) * 0.3
    return finish(lowpass(v, 3500), L, 0.003, 0.02)


@sfx(-21, -8)
def quiz_read_skip():
    """A quick paper flick."""
    L = 0.08
    n = int(L * SR)
    x = bandpass(noise(n), 2600, 0.9) * env(n, 60, 0.002) + 0.4 * click(L, 1800, 1.5, 300)
    return finish(lowpass(x, 5500), L, 0.001, 0.02)


@sfx(-18, -5)
def quiz_hourglass_flip():
    """An hourglass turned over: a glassy turn (two glass tones gliding) and a short hiss of sand."""
    L = 0.5
    x = buf(L)
    n = int(0.15 * SR)
    for f0, f1 in ((hz("e5"), hz("b5")), (hz("b5"), hz("e6"))):
        place(x, glide(f0, f1, 0.15, 0.5, ((1, 1.0), (2.01, 0.3))) * env(n, 12, 0.01) * 0.5, 0.0)
    m = int(0.38 * SR)
    sand = highpass(noise(m) * (rng.random(m) < 0.35), 2500) * np.clip(np.linspace(0, 1, m) / 0.1, 0, 1) \
        * np.exp(-np.linspace(0, 1, m) * 3)
    place(x, lowpass(sand, 6000) * 0.35, 0.1)
    return finish(room(x, 0.4, 0.3), L, 0.003, 0.08)


@sfx(-24, -11)
def quiz_quill_tap():
    """A light quill nib tapping parchment."""
    L = 0.05
    x = click(L, 3200, 2.0, 300) * 0.7 + knock(1250, L, 120, 1.7) * 0.4
    return finish(lowpass(x, 5500), L, 0.0005, 0.015)


@sfx(-17, -4)
def quiz_angel_pleased():
    """The angel, pleased: a warm happy 'mm!' rising, with a shimmer of small bells (E dorian)."""
    L = 0.6
    x = buf(L + 2.5)
    place(x, voice(0.3, lambda u: hz("e4") * (hz("a4") / hz("e4")) ** (u ** 0.6), "m", "m"), 0.0, 1.0)
    for k, m in enumerate(["b5", "e6", "f#6", "b6"]):
        place(x, inst(music_box_hz, m, 0.05, 0.6), 0.18 + 0.05 * k, 0.25)
    return finish(room(x, 0.5, 0.3), L, 0.003, 0.15)


@sfx(-18, -5)
def quiz_angel_sigh():
    """A soft sympathetic sigh, 'aww', falling."""
    L = 0.6
    v = voice(L, lambda u: hz("b4") * (hz("e4") / hz("b4")) ** (u ** 0.8), "a", "u",
              lambda u: np.clip(u / 0.12, 0, 1) * (1 - u) ** 0.8, breath=0.35)
    return finish(room(lowpass(v, 4000), 0.4, 0.3), L, 0.005, 0.1)


@sfx(-17, -4)
def quiz_miso_popin():
    """Miso pops in: a cartoon pop and a chirpy 'mrrp'."""
    L = 0.35
    x = buf(L)
    n = int(0.03 * SR)
    place(x, glide(300, 900, 0.03, 0.6) * env(n, 40, 0.001), 0.0)
    place(x, click(0.01, 2500, 1.0, 400) * 0.5, 0.0)
    place(x, mrrp(0.14, 650, 1000, 0.9), 0.05)
    return finish(x, L, 0.0008, 0.05)


@sfx(-17, -4)
def quiz_angel_gasp():
    """A short scandalised gasp: a sharp breath in that catches on an 'ah!'."""
    L = 0.3
    n = int(0.2 * SR)
    u = np.linspace(0, 1, n)
    x = buf(L)
    place(x, sweep(noise(n), "bp", (800 + 1200 * u)[::32], 1.5) * u ** 0.5 * np.clip((1 - u) / 0.1, 0, 1) * 0.6, 0.0)
    place(x, voice(0.1, lambda u: hz("e5") * (1 + 0.1 * u), "a", "e"), 0.17, 0.8)
    return finish(x, L, 0.004, 0.05)


@sfx(-19, -6)
def quiz_miso_popout():
    """Miso pops out: a small pop played backwards."""
    L = 0.15
    n = int(0.12 * SR)
    pop = glide(300, 900, 0.12, 0.6) * env(n, 30, 0.001)
    x = buf(L)
    place(x, pop[::-1], 0.0)
    place(x, click(0.01, 2500, 1.0, 400) * 0.4, 0.118)
    return finish(x, L, 0.004, 0.015)


# ---------------------------------------------------------------- lantern, round 2 (the band)

@sfx(-16, -4)
def lantern_stage_up():
    """The band levels up: a bright rising flourish through E major pentatonic (played at x1, x1.12, x1.26)."""
    L = 0.7
    x = buf(L + 2.5)
    for k, m in enumerate(["e5", "f#5", "g#5", "b5", "c#6", "e6"]):
        place(x, inst(mallet, m, 0.15, 0.8), 0.035 * k, 0.7)
        place(x, inst(glass_keys, m, 0.1, 0.6), 0.035 * k, 0.3)
    for m in ("e5", "g#5", "b5"):
        place(x, inst(glass_harmonica, m, 0.3, 0.6), 0.21, 0.25)
    place(x, shimmer(0.5, ["e6", "b6"], 12, 0.04), 0.2)
    return finish(room(x, 0.6, 0.4), L, 0.001, 0.2)


@sfx(-17, -4)
def lantern_band_cheer():
    """A small whoop of angels and spirits, and a few claps."""
    L = 0.8
    x = buf(L)
    for k, f0 in enumerate((290, 340, 410, 480, 560)):
        v = voice(0.45, lambda u, f0=f0: f0 * (1 + 0.5 * u ** 0.7) * (1 + 0.02 * np.sin(2 * np.pi * 6 * u)), "u", "a")
        place(x, v * 0.4, 0.03 * k + 0.01 * float(rng.random()))
    for k in range(5):
        place(x, vnsynth.drum("clap", 0.6), 0.08 + 0.11 * k + 0.02 * float(rng.random()), 0.25)
    return finish(room(x, 0.5, 0.35), L, 0.003, 0.15)


@sfx(-18, -5)
def lantern_band_gasp():
    """A soft collective 'oh!'."""
    L = 0.4
    x = buf(L)
    for k, f0 in enumerate((260, 320, 390, 450)):
        v = voice(0.28, lambda u, f0=f0: f0 * (1 + 0.15 * np.sin(np.pi * u)), "o", "o", breath=0.2)
        place(x, v * 0.45, 0.012 * k)
    return finish(room(x, 0.4, 0.3), L, 0.004, 0.08)


@sfx(-18, -5)
def lantern_whoosh_past():
    """An island flying past: a breathy doppler whoosh."""
    L = 0.6
    return finish(doppler(L, 330, (500, 1600, 400), 1.25), L, 0.005, 0.06)


# ---------------------------------------------------------------- draw, round 2 (Pim at the whiteboard)

@sfx(-19, -6)
def draw_marker_uncap():
    """A marker cap popping off."""
    L = 0.12
    x = buf(L)
    n = int(0.02 * SR)
    place(x, glide(700, 1400, 0.02, 0.5) * env(n, 80, 0.0005), 0.0)
    place(x, click(0.015, 3000, 1.2, 400) * 0.6, 0.0)
    place(x, knock(2100, 0.05, 90, 1.4) * 0.3, 0.01)
    return finish(x, L, 0.0005, 0.03)


@sfx(-21, -8)
def draw_marker_squeak():
    """A short whiteboard-marker squeak (played at varied pitch)."""
    L = 0.12
    n = int(L * SR)
    x = squeak(L, 1050, 1250, 0.6) * arch(n, 0.5)
    return finish(lowpass(x, 5000), L, 0.004, 0.03)


@sfx(-21, -8)
def draw_board_tap():
    """A marker tapping the board: a plastic tick on a hollow panel."""
    L = 0.08
    x = knock(1800, L, 110, 1.5) * 0.6 + thump(L, 260, 230, 40, 30) * 0.5 + click(L, 3000, 2, 350) * 0.3
    return finish(x, L, 0.0005, 0.02)


@sfx(-18, -5)
def draw_board_flip():
    """A board panel flipping over on its stand: a swish, a clack, a little rattle."""
    L = 0.45
    x = buf(L)
    n = int(0.25 * SR)
    place(x, nsweep(0.25, 500, 1500, 1.0) * arch(n, 1.2) * 0.4, 0.0)
    place(x, knock(520, 0.12, 35, 2.3), 0.24, 0.9)
    place(x, thump(0.15, 180, 120, 25), 0.24, 0.5)
    for k in range(3):
        place(x, knock(900 + 150 * k, 0.04, 90, 1.7), 0.31 + 0.03 * k, 0.25 - 0.06 * k)
    return finish(x, L, 0.003, 0.05)


@sfx(-20, -7)
def draw_board_wipe():
    """An eraser wiping the whiteboard: two smooth felt strokes."""
    L = 0.45
    n = int(L * SR)
    t = t_axis(n)
    strokes = np.sin(np.pi * np.clip(t / (L / 2), 0, 2) % np.pi) ** 1.2
    x = bandpass(noise(n), 1500, 0.6) * strokes * 0.8 + 0.3 * lowpass(noise(n), 500) * strokes
    return finish(lowpass(x, 5000), L, 0.004, 0.04)


@sfx(-20, -7)
def draw_paper_hold():
    """A sheet of paper rustling in the hand."""
    L = 0.35
    n = int(L * SR)
    dens = 0.02 + 0.2 * lowpass(rng.random(n), 15)
    x = bandpass(noise(n) * (rng.random(n) < dens), 3000, 0.8) * 2 + 0.2 * bandpass(noise(n), 1500, 0.7)
    return finish(lowpass(x * arch(n, 0.6), 5500), L, 0.004, 0.05)


@sfx(-20, -8)
def draw_spirit_voice():
    """Pim chattering: a short wordless voice blip, neutral pitch (D5; played at varied pitch)."""
    L = 0.07
    v = voice(L, lambda u: hz("d5") * (1 + 0.12 * np.sin(np.pi * u)), "e", "a")
    return finish(lowpass(v, 4000), L, 0.003, 0.02)


@sfx(-17, -4)
def draw_spirit_delight():
    """Pim, delighted: a little rising squeal 'eee!'."""
    L = 0.45
    v = voice(L, lambda u: hz("d5") * (hz("a5") / hz("d5")) ** (u ** 0.6) * (1 + 0.03 * np.sin(2 * np.pi * 7 * u * L)),
              "i", "e")
    return finish(room(lowpass(v, 4500), 0.3, 0.25), L, 0.003, 0.08)


@sfx(-18, -5)
def draw_spirit_hmm():
    """Pim's encouraging 'hmm!': a hummed note that lifts at the end."""
    L = 0.35
    v = voice(L, lambda u: hz("g4") * np.where(u < 0.65, 1.0, 1 + 0.25 * (u - 0.65) / 0.35), "m", "m")
    return finish(lowpass(v, 3000), L, 0.004, 0.06)


@sfx(-18, -5)
def draw_spirit_meh():
    """Pim, unimpressed: a flat deadpan 'uh.'"""
    L = 0.25
    v = voice(L, lambda u: hz("c4") * (1 - 0.06 * u), "uh", "uh", lambda u: np.clip(u / 0.08, 0, 1) * (1 - u) ** 0.5)
    return finish(lowpass(v, 3000), L, 0.004, 0.05)


@sfx(-17, -4)
def draw_spirit_oops():
    """Pim, distracted by a moth: 'oo-ps'."""
    L = 0.4
    x = buf(L)
    place(x, voice(0.16, lambda u: hz("e5") * (1 + 0.1 * u), "u", "o"), 0.0)
    place(x, voice(0.1, lambda u: hz("a4") * (1 - 0.05 * u), "o", "uh"), 0.17, 0.9)
    n = int(0.06 * SR)
    place(x, highpass(noise(n), 2500) * env(n, 40, 0.003) * 0.15, 0.26)
    return finish(lowpass(x, 5000), L, 0.003, 0.05)


# ---------------------------------------------------------------- invaders, round 2 (the scrolling shooter)

@sfx(-19, -6)
def invaders_spread():
    """A spread-shot volley: a soft fanning 'fsh' with three glints."""
    L = 0.18
    n = int(L * SR)
    x = bandpass(noise(n), 2400, 0.9) * env(n, 22, 0.003) * 0.6
    for k, m in enumerate(["f#6", "b6", "d7"]):
        m_n = int(0.05 * SR)
        place(x, glide(hz(m), hz(m) * 0.85, 0.05) * env(m_n, 50, 0.001), 0.008 * k, 0.25)
    return finish(lowpass(x, 5500), L, 0.002, 0.04)


@sfx(-19, -6)
def invaders_beam():
    """The piercing beam: a B-ish hum that loops seamlessly (0.608 s, every part repeats each 1024 samples)."""
    n = 19 * 1024                                            # 0.608 s; period 1024 samples = 31.25 Hz
    t = np.arange(n) / SR
    base = 31.25
    hum = sum(a * np.sin(2 * np.pi * base * k * t + k) for k, a in ((8, 1.0), (12, 0.55), (16, 0.45), (24, 0.3),
                                                                    (32, 0.18), (48, 0.12), (64, 0.08)))
    flutter = 1 + 0.18 * np.sin(2 * np.pi * base * t)       # one flutter per period
    period = noise(1024)                                     # sizzle: one block of noise, repeated
    spec = np.fft.rfft(period)
    f = np.fft.rfftfreq(1024, 1 / SR)
    spec *= np.exp(-((f - 3000) / 1500) ** 2)               # band-limited, done circularly
    sizzle = np.tile(np.fft.irfft(spec, 1024), n // 1024)
    sizzle /= np.abs(sizzle).max()
    return hum * flutter * 0.5 + sizzle * 0.12


LOOPS.add("invaders_beam")


@sfx(-19, -6)
def invaders_homing():
    """A homing-spark volley: twinkly seeking chirps."""
    L = 0.28
    x = buf(L)
    for k, m in enumerate(["b6", "f#6", "d7", "a6"]):
        n = int(0.04 * SR)
        f = hz(m)
        place(x, glide(f * 0.8, f * 1.1, 0.04, 0.5) * arch(n, 0.7), 0.05 * k + 0.01 * float(rng.random()), 0.6)
    return finish(room(x, 0.3, 0.25), L, 0.001, 0.05)


@sfx(-26, -13)
def invaders_rapid():
    """One rapid-fire shot: a tiny glassy tick of a pew (40 ms, very frequent)."""
    L = 0.04
    n = int(L * SR)
    x = glide("b6", "f#6", L, 0.5, ((1, 1.0), (2, 0.1))) * env(n, 70, 0.0008)
    return finish(x, L, 0.0005, 0.012)


@sfx(-19, -6)
def invaders_drop():
    """A pickup tumbling out of a defeated enemy: a glint and a little falling whistle."""
    L = 0.35
    x = buf(L)
    place(x, bell("f#6", 0.15, ((1, 1, 25),)), 0.0, 0.4)
    n = int(0.3 * SR)
    place(x, glide(1300, 700, 0.3, 1.0, ((1, 1.0), (2, 0.1)), vib=(14, 0.03)) * arch(n, 0.6) * 0.5, 0.02)
    return finish(x, L, 0.001, 0.05)


@sfx(-17, -4)
def invaders_pickup_weapon():
    """A new weapon: a rising B minor arpeggio with an upward rush."""
    L = 0.5
    x = buf(L + 2.5)
    for k, m in enumerate(["b5", "d6", "f#6", "b6"]):
        place(x, inst(glass_keys, m, 0.1, 0.8), 0.045 * k, 0.6)
        place(x, inst(mallet, m, 0.1, 0.7), 0.045 * k, 0.4)
    n = int(0.25 * SR)
    place(x, nsweep(0.25, 600, 3000, 1.4) * arch(n, 1.2) * 0.3, 0.0)
    return finish(room(x, 0.4, 0.3), L, 0.002, 0.15)


@sfx(-18, -5)
def invaders_weapon_up():
    """Same weapon again, a level up: a quick 'bling' up a fourth (F#5 to B5), neutral pitch."""
    L = 0.35
    x = buf(L + 2.5)
    place(x, inst(mallet, "f#5", 0.06), 0.0, 0.8)
    place(x, inst(mallet, "b5", 0.15), 0.06, 1.0)
    place(x, inst(glass_keys, "b6", 0.1, 0.5), 0.06, 0.2)
    return finish(x, L, 0.001, 0.12)


@sfx(-18, -5)
def invaders_weapon_down():
    """A hit costs a weapon level: a buzzy tone deflating downward."""
    L = 0.5
    n = int(L * SR)
    x = glide(700, 200, L, 0.7, ((1, 1.0), (3, 0.3), (5, 0.15)), vib=(9, 0.03)) * np.clip(np.linspace(0, 1, n) / 0.03, 0, 1) \
        * (1 - np.linspace(0, 1, n)) ** 0.8
    return finish(lowpass(x, 2500), L, 0.002, 0.06)


@sfx(-17, -4)
def invaders_pickup_heart():
    """A heart restored: a warm two-note chime rising, B4 to F#5 (the reverse of life_lost)."""
    L = 0.6
    x = buf(L + 2.5)
    place(x, inst(felt_piano, "b4", 0.2), 0.0, 0.8)
    place(x, inst(mallet, "b4", 0.15), 0.0, 0.5)
    place(x, inst(felt_piano, "f#5", 0.3), 0.13, 0.8)
    place(x, inst(mallet, "f#5", 0.3), 0.13, 0.6)
    return finish(room(x, 0.5, 0.35), L, 0.001, 0.18)


@sfx(-19, -6)
def invaders_turret_shot():
    """A halo turret angel fires its spread: a ring of the halo and three golden pews."""
    L = 0.25
    x = bell("d6", L, ((1, 1, 14), (2.76, 0.3, 25))) * 0.4
    for k, df in enumerate((0.97, 1.0, 1.03)):
        n = int(0.15 * SR)
        place(x, glide(hz("f#5") * df, hz("d5") * df, 0.15, 0.5, ((1, 1.0), (2, 0.2))) * env(n, 18, 0.002), 0.01 * k, 0.35)
    return finish(x, L, 0.001, 0.05)


@sfx(-18, -5)
def invaders_ram_charge():
    """A rammer locks on: a rising tremble."""
    L = 0.6
    n = int(L * SR)
    u = np.linspace(0, 1, n)
    trem = 0.6 + 0.4 * np.sin(2 * np.pi * np.cumsum(10 + 25 * u) / SR)
    x = glide(150, 420, L, 1.0, tuple((k, 1 / k) for k in range(1, 8))) * trem * u ** 0.7
    return finish(lowpass(x, 2500) * np.clip((1 - u) / 0.05, 0, 1), L, 0.01, 0.03)


@sfx(-18, -5)
def invaders_ram():
    """A rammer launches: a short whoosh."""
    L = 0.25
    n = int(L * SR)
    return finish(nsweep(L, 500, 2600, 1.4, 0.8) * np.clip(np.linspace(0, 1, n) / 0.1, 0, 1)
                  * np.exp(-np.linspace(0, 1, n) * 3), L, 0.003, 0.04)


@sfx(-17, -4)
def invaders_ram_hit():
    """An enemy flies into the ship: a thud with a crackle."""
    L = 0.3
    n = int(L * SR)
    x = thump(L, 140, 50, 12) + crackle(L, 0.02, 2500, 1.0) * np.exp(-t_axis(n) * 14) * 0.8
    return finish(x, L, 0.001, 0.06)


@sfx(-16, -3)
def invaders_boss_warning():
    """'Something hungry is coming...': a low C minor cluster swelling, a heartbeat, the music box descending."""
    L = 2.0
    x = buf(L + 3)
    n = int(L * SR)
    u = np.linspace(0, 1, n)
    for f in (hz("c2"), hz("g2"), hz("db3")):
        x[:n] += glide(f, f, L, harmonics=tuple((k, 1 / k) for k in range(1, 9))) * 0.25
    x[:n] = sweep(x[:n], "lp", (120 + 900 * np.sin(np.pi * u) ** 2)[::32], 1.3) * np.sin(np.pi * u) ** 0.8
    x[:n] += lowpass(noise(n), 100) * 2.0 * np.sin(np.pi * u)
    for t0 in (0.2, 0.9):
        place(x, vnsynth.drum("heartbeat", 0.8), t0, 0.5)
    for k, m in enumerate(["c6", "b5", "bb5", "a5"]):
        place(x, inst(music_box_hz, m, 0.2, 0.8), 0.6 + 0.25 * k, 0.4 - 0.05 * k)
    return finish(room(x, 1.2, 0.5), L, 0.02, 0.4)


@sfx(-18, -5)
def invaders_boss_tell():
    """The boss winds up a move: a short music-box chime on C6 (pitched per move)."""
    L = 0.3
    x = buf(L + 2.5)
    place(x, inst(music_box_hz, "c6", 0.1), 0.0, 1.0)
    place(x, inst(glass_keys, "c5", 0.1, 0.6), 0.0, 0.3)
    return finish(room(x, 0.4, 0.3), L, 0.001, 0.1)


@sfx(-17, -4)
def invaders_boss_spiral():
    """A spiral of light begins: a swirling shimmer of C minor glass."""
    L = 0.9
    x = buf(L + 2.5)
    n = int(L * SR)
    t = t_axis(n)
    for k, m in enumerate(["c6", "eb6", "g6", "c7", "g6", "eb6", "c6", "eb6", "g6", "c7"]):
        place(x, inst(glass_keys, m, 0.05, 0.6), 0.06 * k, 0.3 + 0.03 * k)
    swirl = sum(np.sin(2 * np.pi * np.cumsum(hz(m) * (1 + 0.03 * np.sin(2 * np.pi * 6 * t + j))) / SR)
                for j, m in enumerate(["g5", "c6", "eb6"]))
    x[:n] += swirl * np.linspace(0, 1, n) ** 1.5 * np.clip((1 - np.linspace(0, 1, n)) / 0.2, 0, 1) * 0.06
    return finish(room(x, 0.6, 0.4), L, 0.004, 0.2)


@sfx(-17, -4)
def invaders_boss_sweep():
    """The cape beam sweeps: a long sizzling sweep across."""
    L = 1.2
    n = int(L * SR)
    u = np.linspace(0, 1, n)
    centre = 400 + 2600 * np.sin(np.pi * u) ** 1.5
    ph = np.cumsum(np.full(n, hz("c3"))) / SR
    buzz = sum(np.sin(2 * np.pi * k * ph) / k for k in range(1, 30))
    x = sweep(buzz * 0.4 + noise(n) * 0.6, "bp", centre[::32], 1.5)
    x += crackle(L, 0.02, 3500, 1.2) * 0.5
    return finish(lowpass(x * np.clip(u / 0.08, 0, 1) * np.clip((1 - u) / 0.2, 0, 1), 6000), L, 0.004, 0.1)


@sfx(-17, -4)
def invaders_boss_stars():
    """The starfield cape lets go: a sparkly cascade down C minor pentatonic."""
    L = 1.0
    x = buf(L + 2.5)
    scale = ["c7", "bb6", "g6", "f6", "eb6", "c6", "bb5", "g5", "f5", "eb5", "c5", "bb4"]
    for k, m in enumerate(scale):
        place(x, inst(glass_keys, m, 0.05, 0.7), 0.045 * k, 0.45)
        place(x, inst(mallet, m, 0.05, 0.6), 0.045 * k + 0.01, 0.2)
    place(x, shimmer(0.8, ["c7", "g6"], 14, 0.03), 0.0)
    return finish(room(x, 0.7, 0.45), L, 0.001, 0.25)


@sfx(-17, -5)
def invaders_boss_dash_warn():
    """The dash lane is marked: a sharp double alarm blip on C6."""
    L = 0.22
    x = buf(L)
    place(x, beep("c6", 0.06, 8), 0.0, 1.0)
    place(x, beep("c6", 0.06, 8), 0.09, 1.0)
    return finish(x, L, 0.001, 0.03)


@sfx(-17, -4)
def invaders_boss_dash():
    """Ashveil whooshes across the screen: a dark doppler rush with a cape flap."""
    L = 0.5
    x = doppler(L, 130, (300, 1200, 250), 1.35) * 1.3
    n = int(L * SR)
    x += lowpass(noise(n), 300) * np.abs(np.sin(2 * np.pi * 9 * t_axis(n))) * arch(n, 2) * 0.5
    return finish(x, L, 0.005, 0.06)


@sfx(-17, -4)
def invaders_boss_tantrum():
    """A hungry tantrum: a comic wobbling 'waaah' from a huge child."""
    L = 1.0
    v = voice(L, lambda u: hz("c4") * (1 + 0.18 * np.sin(np.pi * u) + 0.05 * np.sin(2 * np.pi * 7 * u)), "a", "a",
              lambda u: np.clip(u / 0.08, 0, 1) * np.clip((1 - u) / 0.3, 0, 1))
    v += 0.5 * voice(L, lambda u: hz("c3") * (1 + 0.18 * np.sin(np.pi * u) + 0.05 * np.sin(2 * np.pi * 7 * u)), "a", "o")
    return finish(room(lowpass(v, 3500), 0.6, 0.35), L, 0.005, 0.15)


# ---------------------------------------------------------------- miso, round 2 (packages and leaps)

@sfx(-18, -5)
def miso_leap_side():
    """A left/right leap: a springy whoosh."""
    L = 0.3
    n = int(L * SR)
    x = nsweep(L, 600, 1800, 1.3) * arch(n, 1.2) * 0.6
    m = int(0.18 * SR)
    place(x, glide("d5", "a5", 0.18, 0.5, vib=(24, 0.05)) * env(m, 12, 0.003) * 0.25, 0.0)
    return finish(x, L, 0.003, 0.04)


@sfx(-19, -6)
def miso_leap_up():
    """A leap away from the camera: a whoosh fading into the distance."""
    L = 0.4
    n = int(L * SR)
    u = np.linspace(0, 1, n)
    x = sweep(nsweep(L, 1200, 700, 1.3), "lp", (5000 * (500 / 5000) ** u)[::32], 0.7) \
        * np.clip(u / 0.05, 0, 1) * (1 - u) ** 1.5
    return finish(x, L, 0.003, 0.05)


@sfx(-18, -5)
def miso_leap_down():
    """A leap toward the camera: a whoosh rushing closer."""
    L = 0.4
    n = int(L * SR)
    u = np.linspace(0, 1, n)
    x = sweep(nsweep(L, 600, 1300, 1.3), "lp", (500 * (5000 / 500) ** u)[::32], 0.7) \
        * u ** 2 * np.clip((1 - u) / 0.08, 0, 1)
    return finish(x, L, 0.01, 0.03)


@sfx(-19, -6)
def miso_land():
    """A soft paw thump on landing."""
    L = 0.15
    n = int(L * SR)
    x = thump(L, 170, 85, 22) + 0.15 * lowpass(noise(n), 1500) * env(n, 60, 0.002)
    return finish(x, L, 0.001, 0.04)


@sfx(-17, -4)
def miso_bonk():
    """A leap into the furniture: a comic hollow bonk with a wobble."""
    L = 0.3
    n = int(L * SR)
    t = t_axis(n)
    f = (330 + 200 * np.exp(-t * 40)) * (1 + 0.06 * np.sin(2 * np.pi * 14 * t) * np.exp(-t * 8))
    ph = np.cumsum(f) / SR
    s = (np.sin(2 * np.pi * ph) + 0.3 * np.sin(2 * np.pi * 2.6 * ph) * np.exp(-t * 30)) * np.exp(-t * 11)
    x = s * np.clip(t / 0.0008, 0, 1) + thump(L, 120, 60, 18) * 0.5 + click(L, 2000, 2, 300) * 0.2
    return finish(x, L, 0.0008, 0.05)


@sfx(-16, -4)
def miso_leap_multi():
    """Several packages in one leap: a bright bonus jingle (D F A D' on pizzicato, glass and bubbles)."""
    L = 0.6
    x = buf(L + 2.5)
    for k, m in enumerate(["d5", "f5", "a5", "d6"]):
        place(x, inst(pizzicato, m, 0.1), 0.05 * k, 0.8)
        place(x, inst(glass_keys, note_hz(m, 12), 0.05, 0.6), 0.05 * k, 0.25)
    for k, m in enumerate(["a6", "d7"]):
        place(x, inst(bubble, m, 0.1), 0.22 + 0.05 * k, 0.4)
    return finish(room(x, 0.5, 0.35), L, 0.001, 0.15)


@sfx(-18, -5)
def miso_pickup():
    """Grabbing a pouch or box: a crinkle and a munch (pitched per combo)."""
    L = 0.2
    x = buf(L)
    place(x, crackle(0.07, 0.15, 3000, 0.8) * env(int(0.07 * SR), 30, 0.001) * 1.5, 0.0)
    for t0 in (0.05, 0.11):
        n = int(0.05 * SR)
        place(x, lowpass(noise(n), 900) * env(n, 60, 0.002) + glide(220, 160, 0.05) * env(n, 50, 0.002) * 0.6, t0, 0.8)
    return finish(lowpass(x, 5500), L, 0.001, 0.03)


@sfx(-17, -4)
def miso_pickup_rare():
    """A golden tin: a shiny can clink, twice."""
    L = 0.4
    tin = ((1, 1, 14), (2.32, 0.6, 18), (4.25, 0.35, 26), (6.8, 0.15, 40))
    x = buf(L)
    place(x, bell(1350, L, tin) + 0.3 * click(L, 4000, 2, 400), 0.0)
    place(x, bell(1620, 0.3, tin) * 0.5, 0.07)
    return finish(x, L, 0.0005, 0.1)


@sfx(-18, -5)
def miso_package_appear():
    """A package shimmering out of the wall: a glitchy shimmer."""
    L = 0.5
    n = int(L * SR)
    t = t_axis(n)
    s = shimmer(L, ["d6", "f6", "a6"], 16, 0.4)
    gate = np.repeat((rng.random(n // 640 + 1) < 0.75).astype(float), 640)[:n]
    x = crush(s * lowpass(gate, 200) + 0.1 * crackle(L, 0.01, 4000) * arch(n), 4, 20, 5000)
    return finish(x * (0.3 + 0.7 * np.clip(t / 0.3, 0, 1)), L, 0.004, 0.08)


@sfx(-16, -4)
def miso_rare_appear():
    """A golden tin appears: a distinct sparkly chime (D6 A6 D7) with a bell ringing under it."""
    L = 0.8
    x = buf(L + 2.5)
    for k, m in enumerate(["d6", "a6", "d7"]):
        place(x, inst(glass_keys, m, 0.1, 0.8), 0.07 * k, 0.6)
    place(x, bell("d5", L, ((1, 1, 3), (2, 0.4, 5), (3, 0.15, 8))), 0.0, 0.35)
    place(x, shimmer(0.7, ["a6", "d7", "f#7"], 11, 0.03), 0.1)
    return finish(room(x, 0.7, 0.45), L, 0.001, 0.25)


@sfx(-19, -6)
def miso_package_land():
    """A package plopping onto the floor."""
    L = 0.15
    x = thump(L, 220, 110, 24)
    place(x, crackle(0.06, 0.08, 2500, 0.8) * env(int(0.06 * SR), 50) * 0.6, 0.005)
    return finish(x, L, 0.001, 0.04)


@sfx(-19, -6)
def miso_package_vanish():
    """A package dissolving back into the leak: a glitch fizzle sinking."""
    L = 0.35
    n = int(L * SR)
    src = shimmer(L, ["a6", "d6"], 20, 0.5) + bandpass(noise(n), 2500, 1.0) * 0.3 * np.exp(-t_axis(n) * 6)
    x = dive(crush(src, 6, 12, 5000), cents=-1200, curve=1.0)
    return finish(x, L, 0.003, 0.08)


# ---------------------------------------------------------------- snake, round 2 (apples and the worm king)

@sfx(-18, -5)
def snake_apple_crunch():
    """A crisp apple bite (played at random pitch): a dense crunch and a juicy thunk."""
    L = 0.15
    n = int(0.08 * SR)
    x = buf(L)
    place(x, (crackle(0.08, 0.3, 2600, 0.7) + 0.5 * crackle(0.08, 0.2, 1200, 0.9)) * env(n, 35, 0.001), 0.0)
    place(x, thump(0.1, 330, 240, 35, 40) * 0.5, 0.0)
    return finish(lowpass(x, 6000), L, 0.0008, 0.04)


@sfx(-18, -5)
def snake_golden_spawn():
    """A golden apple appears: a sparkly twinkle (G6, D7)."""
    L = 0.5
    x = buf(L + 2.5)
    place(x, inst(glass_keys, "g6", 0.05, 0.7), 0.0, 0.6)
    place(x, inst(glass_keys, "d7", 0.05, 0.7), 0.07, 0.5)
    place(x, shimmer(0.45, ["g6", "b6", "d7"], 15, 0.04), 0.02)
    return finish(room(x, 0.5, 0.4), L, 0.001, 0.15)


@sfx(-16, -4)
def snake_golden_apple():
    """Eating a golden apple: a crunch and a rich G major chime."""
    L = 0.8
    x = buf(L + 2.5)
    place(x, snake_apple_crunch() * 0.8, 0.0)
    for k, m in enumerate(["g5", "b5", "d6", "g6"]):
        place(x, inst(mallet, m, 0.3), 0.04 + 0.03 * k, 0.6)
        place(x, inst(glass_keys, m, 0.2, 0.7), 0.04 + 0.03 * k, 0.3)
    return finish(room(x, 0.6, 0.4), L, 0.001, 0.25)


@sfx(-20, -7)
def snake_golden_fade():
    """The golden apple turns red again: a soft dull downward blip."""
    L = 0.25
    n = int(L * SR)
    x = glide(700, 400, L, 0.7, ((1, 1.0), (2, 0.15))) * env(n, 10, 0.004)
    return finish(lowpass(x, 1500), L, 0.002, 0.05)


@sfx(-16, -4)
def snake_stage_next():
    """Stage clear: a short upbeat jingle (G A Bb D, G') on pizzicato and bubbles, a brass hit at the end."""
    L = 0.9
    x = buf(L + 2.5)
    for m, t0 in (("g5", 0.0), ("a5", 0.08), ("bb5", 0.16), ("d6", 0.24), ("g6", 0.36)):
        place(x, inst(pizzicato, m, 0.1), t0, 0.8)
        place(x, inst(bubble, m, 0.1), t0 + 0.01, 0.35)
    for m in ("g3", "d4", "g4"):
        place(x, inst(soft_brass, m, 0.3, 0.8), 0.36, 0.4)
    place(x, thump(0.3, 140, 70, 12), 0.36, 0.5)
    return finish(room(x, 0.6, 0.4), L, 0.001, 0.25)


@sfx(-18, -5)
def snake_leak_tires():
    """The filter lifts on its own: a glitchy wind-down sigh, like a tape running out."""
    L = 0.8
    n = int(L * SR)
    u = np.linspace(0, 1, n)
    trem = 0.6 + 0.4 * np.sin(2 * np.pi * np.cumsum(14 * (1 - u) + 2) / SR)
    src = (bandpass(noise(n), 1500, 0.8) * 0.6 + glide("d5", "d5", L, harmonics=((1, 1.0), (2, 0.3))) * 0.4) * trem
    x = dive(crush(src, 5, 14, 4500), cents=-1500, curve=1.3)
    return finish(x[: n] * (1 - u) ** 0.8, L, 0.005, 0.1)


@sfx(-17, -4)
def snake_crowd_cheer():
    """A little crowd of squeaky worm cheers as the crown lands."""
    L = 0.8
    x = buf(L)
    for k in range(7):
        f0 = 700 + 450 * float(rng.random())
        d = 0.18 + 0.12 * float(rng.random())
        v = voice(d, lambda u, f0=f0: f0 * (1 + 0.35 * u ** 0.6) * (1 + 0.04 * np.sin(2 * np.pi * 9 * u)), "i", "a")
        place(x, v * 0.35, 0.04 + 0.07 * k + 0.03 * float(rng.random()))
    return finish(room(lowpass(x, 5000), 0.5, 0.3), L, 0.003, 0.15)


# ---------------------------------------------------------------- tower, round 2 (the platformer)

@sfx(-20, -7)
def tower_skid():
    """Sneakers skidding as he turns at speed: a rubber squeak over a scrape."""
    L = 0.3
    n = int(L * SR)
    u = np.linspace(0, 1, n)
    x = squeak(L, 1900, 1500, 1.0) * 0.5 + bandpass(noise(n), 2200, 0.8) * 0.4
    return finish(lowpass(x * np.clip(u / 0.05, 0, 1) * (1 - u) ** 1.2, 5000), L, 0.003, 0.05)


@sfx(-17, -4)
def tower_bounce():
    """A red mushroom: a big rubbery boing, D4 up to D5."""
    L = 0.4
    n = int(L * SR)
    t = t_axis(n)
    u = t / L
    f = hz("d4") * 2 ** (u ** 0.4) * (1 + 0.1 * np.sin(2 * np.pi * 18 * t) * np.exp(-t * 7))
    ph = np.cumsum(f) / SR
    s = np.sin(2 * np.pi * ph) + 0.35 * np.sin(4 * np.pi * ph) + 0.15 * np.sin(6 * np.pi * ph)
    return finish(lowpass(s, 2800) * np.clip(t / 0.004, 0, 1) * (1 - u) ** 0.9 + 0.3 * thump(L, 140, 80, 20),
                  L, 0.001, 0.05)


@sfx(-17, -4)
def tower_crack():
    """A ledge starts to shake: stone cracking and grinding."""
    L = 0.6
    n = int(L * SR)
    t = t_axis(n)
    cracks = crackle(L, 0.004, 900, 1.2) * 3 + crackle(L, 0.006, 2200, 1.5)
    grind = lowpass(noise(n), 400) * (0.5 + 0.5 * np.abs(np.sin(2 * np.pi * 13 * t))) * 0.8
    return finish((cracks + grind) * arch(n, 0.5), L, 0.003, 0.08)


@sfx(-16, -4)
def tower_crumble():
    """The cracked ledge breaks and falls away: a burst of rubble, receding."""
    L = 0.9
    x = buf(L)
    for k in range(14):
        t0 = 0.5 * float(rng.random()) ** 1.5
        f0 = 80 + 160 * float(rng.random())
        place(x, thump(0.2, f0 * 1.5, f0, 18), t0, 1.0 - 0.06 * k)
        place(x, crackle(0.1, 0.05, 1800, 1.0) * 0.5, t0, 1.0 - 0.06 * k)
    n = int(L * SR)
    x = sweep(x, "lp", (4000 * (400 / 4000) ** np.linspace(0, 1, n))[::32], 0.7)
    return finish(x, L, 0.001, 0.2)


@sfx(-18, -5)
def tower_stomp():
    """Landing on a beetle or crow: a squishy pop, neutral pitch (it rises with the combo)."""
    L = 0.2
    x = buf(L)
    n = int(0.12 * SR)
    place(x, sweep(noise(n), "bp", np.linspace(900, 400, n)[::32], 3.0) * env(n, 20, 0.002) * 0.8, 0.0)
    place(x, glide(300, 120, 0.12, 0.6) * env(n, 25, 0.002) * 0.6, 0.0)
    m = int(0.03 * SR)
    place(x, glide(450, 950, 0.03, 0.6) * env(m, 50, 0.001) * 0.7, 0.05)
    return finish(x, L, 0.001, 0.04)


@sfx(-17, -4)
def tower_hurt():
    """Losing a heart: an 'oof' and a short sour sting (D and Eb)."""
    L = 0.35
    x = buf(L + 1)
    place(x, voice(0.18, lambda u: 330 * (1 - 0.25 * u), "u", "uh"), 0.0, 0.8)
    for m in ("d4", "eb4"):
        place(x, inst(soft_brass, m, 0.15, 0.8), 0.03, 0.4)
    return finish(x, L, 0.003, 0.08)


@sfx(-17, -4)
def tower_heart():
    """A heart picked up: a warm sparkle, D F# A on vibes and glass."""
    L = 0.5
    x = buf(L + 2.5)
    for k, m in enumerate(["d6", "f#6", "a6"]):
        place(x, inst(mallet, m, 0.15), 0.04 * k, 0.6)
        place(x, inst(glass_keys, m, 0.1, 0.6), 0.04 * k, 0.25)
    place(x, inst(felt_piano, "d5", 0.2), 0.0, 0.4)
    return finish(room(x, 0.5, 0.35), L, 0.001, 0.15)


@sfx(-18, -5)
def tower_falling_warn():
    """Something is falling: a whistle-down warning blip."""
    L = 0.3
    n = int(L * SR)
    x = glide(1800, 1100, L, 0.9, ((1, 1.0), (2, 0.08)), vib=(7, 0.01)) * np.clip(np.linspace(0, 1, n) / 0.05, 0, 1) \
        * np.clip((1 - np.linspace(0, 1, n)) / 0.2, 0, 1)
    place(x, beep("a5", 0.04, 20) * 0.4, 0.0)
    return finish(x, L, 0.002, 0.04)


@sfx(-17, -4)
def tower_falling_hit():
    """A falling thing smashes: a wood knock, a clatter and a tiny burst (the game varies the pitch)."""
    L = 0.3
    n = int(L * SR)
    x = knock(380, L, 30, 2.4) + crackle(L, 0.03, 2600, 1.0) * np.exp(-t_axis(n) * 12) * 0.8 + thump(L, 160, 80, 20) * 0.5
    return finish(x, L, 0.0008, 0.06)


@sfx(-16, -4)
def tower_gust():
    """The updraft cheat: a big rushing wind swell."""
    L = 1.4
    n = int(L * SR)
    u = np.linspace(0, 1, n)
    gusts = 0.7 + 0.3 * np.sin(2 * np.pi * 2.5 * u * L + 2 * np.sin(2 * np.pi * 0.7 * u * L))
    x = sweep(noise(n), "bp", (300 * 5 ** np.sin(np.pi * u * 0.8))[::32], 0.9) * gusts \
        + lowpass(noise(n), 250) * 0.8
    return finish(x * np.sin(np.pi * np.clip(u / 0.75, 0, 1) * 0.5) ** 2 * np.clip((1 - u) / 0.3, 0, 1), L, 0.01, 0.1)


@sfx(-17, -4)
def tower_fall():
    """Dropped off the screen: a descending slide whistle."""
    L = 0.9
    n = int(L * SR)
    u = np.linspace(0, 1, n)
    x = glide(1500, 300, L, 0.8, ((1, 1.0), (2, 0.05)), vib=(6, 0.012))
    x = x + bandpass(noise(n), 1200, 1.0) * 0.06
    return finish(x * np.clip(u / 0.03, 0, 1) * np.clip((1 - u) / 0.15, 0, 1), L, 0.003, 0.06)


@sfx(-17, -4)
def tower_ko():
    """Out of hearts: a balloon deflating, then a little tumble."""
    L = 0.9
    x = buf(L)
    m = int(0.35 * SR)
    place(x, lowpass(glide(420, 120, 0.35, 0.8, tuple((k, 1 / k) for k in range(1, 9)), vib=(22, 0.04)), 2000)
          * np.clip(np.linspace(1, 0, m) / 0.2, 0, 1), 0.0, 0.7)
    for k, t0 in enumerate((0.38, 0.52, 0.62, 0.69)):
        place(x, thump(0.15, 160 - 20 * k, 80, 22), t0, 0.9 - 0.18 * k)
    return finish(x, L, 0.003, 0.12)


@sfx(-17, -4)
def tower_milestone():
    """Every 50 m: a small bright two-note ding, A5 then D6."""
    L = 0.45
    x = buf(L + 2.5)
    place(x, inst(mallet, "a5", 0.08), 0.0, 0.8)
    place(x, inst(mallet, "d6", 0.2), 0.08, 1.0)
    place(x, bell("d6", 0.3, ((1, 1, 10), (2.76, 0.2, 25))), 0.08, 0.3)
    return finish(x, L, 0.001, 0.12)


def write_loop(name, x, loud, peak):
    """A loopable clip. Its content repeats every 1024 samples or a multiple,
    and its length is a whole number of 1024-sample blocks: the encoder here
    (and some decoders) may add or drop one whole final block, which then
    still lands on a period, so the wrap stays seamless either way. Filtered
    circularly, levelled by gain only (no limiter, no fades)."""
    assert len(x) % 1024 == 0, name
    n = len(x)
    x = vnsynth.biquad(np.tile(x, 3), "highshelf", 7000, 0.7, -4.0)[n:2 * n]
    g = min(10 ** ((loud - loudness_db(x)) / 20), 10 ** (peak / 20) / np.abs(x).max())
    x = x * g
    path = os.path.join(OUT, name + ".ogg")
    with tempfile.TemporaryDirectory() as tmp:
        wav = os.path.join(tmp, "out.wav")
        _write_wav(wav, np.stack([x, x], 1))
        _encode(wav, path)
        r = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "s16le", "-ac", "1", "-"], capture_output=True)
        y = np.frombuffer(r.stdout, "<i2") / 32768
    print(f"    {name:<22} {n / SR:5.3f}s  peak {20 * np.log10(np.abs(y).max()):5.1f}  "
          f"loud {loudness_db(x):5.1f}  {os.path.getsize(path) // 1024} KB  (loop, decodes to {len(y)} samples)")


# ---------------------------------------------------------------- render

def render(prefixes=()):
    """Write every registered sound (or those whose names start with one of `prefixes`)."""
    global rng
    for name, (gen, loud, peak) in SOUNDS.items():
        if prefixes and not name.startswith(tuple(prefixes)):
            continue
        seed = zlib.crc32(name.encode())
        rng = np.random.default_rng(seed)        # each sound its own randomness: partial renders match full ones
        vnsynth.reseed(seed)
        write(name, gen(), loud, peak)


if __name__ == "__main__":
    render([p for p in os.environ.get("SFX", "").split(",") if p])

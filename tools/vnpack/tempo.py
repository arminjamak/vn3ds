"""Tempo grids for music files, measured at conversion time.

The engine's musical transitions (MUSM, see docs/FORMAT.md) need each
track's bpm, beats per bar, phrase length and loop length in bars. A game
made with Snapshot's score has these written down; any other game's music
is analysed here:

    r = analyse_file(data)          # dict, or None if it can't be decoded
    entry = music_entry(r)          # vn3ds.json "music" entry, or None

Method (numpy only, deterministic; ~0.2-0.5 s of CPU for a 1-minute
track, ~0.6-1 s for 3 minutes, plus the ffmpeg decode):
  1. Onset strength: log-compressed STFT magnitudes pooled into log-spaced
     bands, spectral flux (half-wave rectified), minus a moving average.
  2. Periodicity: the envelope's autocorrelation, circular because a game
     track loops as a whole file. Each tempo is scored by a comb over the
     autocorrelation (the beat, its multiples and half-beats) times a
     log-Gaussian prior around ~100 bpm, so the octave falls in ~60-160.
  3. Loop fit: game music is usually a seamless loop of a whole number of
     bars, so the integer beat counts near length/beat are scored by the
     envelope's Fourier magnitude (beat + eighth + sixteenth harmonics) at
     that many cycles per file; the fractional peak says whether the file
     is a whole number of bars (within 3% of a bar), and if so the bpm is
     snapped so the bars fill the file exactly. Otherwise the fractional
     peak gives the bpm (snapped to a whole bpm when within 0.05).
  4. Beats per bar: the beat-synchronous accent pattern (and the
     autocorrelation at 3 vs 4 beats); 4 unless 3 is clearly stronger.
  5. Confidence: how far the onsets on the best-phased grid stand above the
     mean (contrast), times the share of up to eight stretches of the file
     in which that same grid is still the best one (stability, squared:
     catches drifting
     tempo, rubato and edited tracks that jump phase), plus 0.25 when the
     file is a whole number of bars. 0.5 is the recommended threshold.
     result["offset"] is the time of the beat nearest the file's start
     (the engine assumes 0).
"""

import math
import subprocess

import numpy as np

RATE = 22050
N_FFT = 1024
HOP = 256
FPS = RATE / HOP
MIN_SECONDS = 4.0
PHRASE_MAX_S = 8.0
BPM_MIN, BPM_MAX = 40.0, 240.0
PRIOR_BPM, PRIOR_OCT = 100.0, 1.0   # log2-Gaussian prior: centre, width in octaves
BAR_FIT = 0.03                      # loop fits if within 3% of a bar of whole bars


# --------------------------------------------------------------------------
# Onset strength
# --------------------------------------------------------------------------

def _band_matrix(n_bins, rate, n_bands=36, fmin=40.0):
    """Triangular log-spaced bands over the STFT bins."""
    freqs = np.arange(n_bins) * rate / ((n_bins - 1) * 2)
    edges = np.geomspace(fmin, min(rate / 2, 11000.0), n_bands + 2)
    m = np.zeros((n_bands, n_bins), np.float32)
    for b in range(n_bands):
        lo, mid, hi = edges[b], edges[b + 1], edges[b + 2]
        up = (freqs - lo) / (mid - lo)
        down = (hi - freqs) / (hi - mid)
        m[b] = np.clip(np.minimum(up, down), 0, None)
        if not m[b].any():
            m[b, np.argmin(np.abs(freqs - mid))] = 1.0
    return m


def onset_envelope(samples, rate=RATE):
    """Onset strength per HOP frame (float32, zero mean-ish, >= 0)."""
    x = np.asarray(samples, np.float32)
    if rate != RATE:
        # crude linear resample; analyse_file always decodes at RATE
        n = int(len(x) * RATE / rate)
        x = np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x).astype(np.float32)
    peak = float(np.max(np.abs(x))) if len(x) else 0.0
    if peak > 0:
        x = x / peak
    # a game track loops as a whole file: wrap its start onto its end so the
    # envelope is one period long (frame i starts at sample i * HOP)
    n_frames = len(x) // HOP
    if n_frames < 8:
        return np.zeros(0, np.float32)
    x = np.concatenate([x, x[:N_FFT]])
    idx = np.arange(N_FFT)[None, :] + HOP * np.arange(n_frames)[:, None]
    win = np.hanning(N_FFT).astype(np.float32)
    mag = np.abs(np.fft.rfft(x[idx] * win, axis=1)).astype(np.float32)
    bands = mag @ _band_matrix(mag.shape[1], RATE).T
    logb = np.log1p(100.0 * bands)
    flux = np.diff(logb, axis=0, prepend=logb[:1])
    env = np.maximum(flux, 0).sum(axis=1)
    # remove the slow trend (crescendos, sections) so only onsets remain
    k = int(FPS * 0.4) | 1
    trend = np.convolve(np.pad(env, k // 2, mode="wrap"), np.ones(k) / k, mode="valid")
    env = np.maximum(env - trend, 0)
    s = env.std()
    return (env / s if s > 0 else env).astype(np.float32)


# --------------------------------------------------------------------------
# Tempo
# --------------------------------------------------------------------------

def _acf(env):
    """Circular autocorrelation, normalised to acf[0] == 1."""
    e = env - env.mean()
    spec = np.fft.rfft(e)
    a = np.fft.irfft(np.abs(spec) ** 2, n=len(e))
    return a / a[0] if a[0] > 0 else a


def _at(a, lag):
    """Linear interpolation of a at fractional lags (max over +-1 frame,
    so tempo isn't penalised for falling between frames)."""
    lag = np.asarray(lag, np.float64)
    i = np.floor(lag).astype(int)
    f = lag - i
    n = len(a)
    v = (1 - f) * a[i % n] + f * a[(i + 1) % n]
    return v


def _comb(a, lag):
    """Tempo score for a beat period `lag` (frames)."""
    def pk(l):
        # small max window to tolerate tempo jitter
        return np.maximum.reduce([_at(a, l - 1), _at(a, l), _at(a, l + 1)])
    return pk(lag) + 0.5 * pk(2 * lag) + 0.25 * pk(4 * lag) + 0.25 * pk(lag / 2)


def _prior(bpm):
    return np.exp(-0.5 * (np.log2(bpm / PRIOR_BPM) / PRIOR_OCT) ** 2)


def _beat_phase(env, period):
    """Phase (frames) of the beat grid with the most onset energy."""
    n = len(env)
    nb = int(n // period)
    best, best_s = 0.0, -1.0
    for ph in np.arange(0, period, 1.0):
        pos = np.round(ph + period * np.arange(nb)).astype(int) % n
        s = env[pos].sum() + 0.5 * (env[(pos - 1) % n].sum() + env[(pos + 1) % n].sum())
        if s > best_s:
            best, best_s = ph, s
    return best


def _grid_lock(env, period, parts):
    """How well one fixed beat grid of `period` frames sits on the onsets:
    (contrast, stability, offset). contrast is the onset strength on the
    best-phased grid over the mean (1 = no beat); stability is the fraction
    of `parts` stretches of the file whose own best phase is within 10% of a
    beat of the whole file's (1 = one grid fits all of it; less = the tempo
    drifts, or the track was edited and jumps phase); offset is the time of
    the beat nearest the file's start, in seconds (negative: just before)."""
    n = len(env)
    phases = np.arange(0, period, 0.5)
    # three-frame smoothing so a beat may fall between frames
    sm = (np.roll(env, 1) + 2 * env + np.roll(env, -1)) / 4

    def best(a, b):
        k0 = np.ceil((a - phases) / period)          # first grid index >= a per phase
        m = int((b - a) // period) + 1
        pos = phases[:, None] + period * (k0[:, None] + np.arange(m)[None, :])
        valid = pos < b
        vals = np.where(valid, sm[np.clip(np.round(pos).astype(int), 0, n - 1)], 0)
        s = vals.sum(1) / np.maximum(valid.sum(1), 1)
        i = int(np.argmax(s))
        return s[i] / (sm[a:b].mean() + 1e-9), phases[i]

    contrast, ph = best(0, n)
    agree = 0
    for q in range(parts):
        d = (best(q * n // parts, (q + 1) * n // parts)[1] - ph) % period
        agree += min(d, period - d) <= 0.1 * period
    beat_s = period / FPS
    offset = ((ph * HOP + N_FFT / 2) / RATE + beat_s / 2) % beat_s - beat_s / 2
    return float(contrast), agree / parts, float(offset)


def _beat_strengths(env, period, phase):
    n = len(env)
    nb = int(n // period)
    pos = phase + period * np.arange(nb)
    out = np.empty(nb)
    w = max(1, int(period * 0.1))
    for i, p in enumerate(pos):
        c = int(round(p))
        out[i] = env[max(0, c - w):min(n, c + w + 1)].max() if c - w < n else 0.0
    return out


def _meter(env, a, period):
    """3 or 4 beats per bar, plus the evidence ratio (3-score / 4-score)."""
    phase = _beat_phase(env, period)
    s = _beat_strengths(env, period, phase)
    if len(s) < 12:
        return 4, 0.0

    def accent(m):
        # strongest beat position mod m against the rest, best phase
        means = np.array([s[p::m].mean() for p in range(m)])
        return (means.max() - np.delete(means, means.argmax()).mean()) / (s.std() + 1e-9)

    def per(m):
        x = s - s.mean()
        if len(x) <= m:
            return 0.0
        return float(np.dot(x[:-m], x[m:]) / (np.dot(x, x) + 1e-9))

    acc3, acc4 = accent(3), accent(4)
    p3, p4 = per(3), per(4)
    l3 = _at(a, 3 * period) + _at(a, 6 * period)
    l4 = _at(a, 4 * period) + _at(a, 8 * period)
    score3 = acc3 + p3 + float(l3)
    score4 = acc4 + p4 + float(l4)
    return (3 if score3 > score4 + 0.35 else 4), score3 - score4


def analyse_pcm(samples, rate=RATE):
    """Tempo grid of a mono float signal. Returns a dict:
    bpm, beats_per_bar, phrase_bars, bars (0 = not a whole number of bars),
    confidence (0..1), and diagnostics (duration, raw_bpm, fit, ...)."""
    samples = np.asarray(samples, np.float32)
    duration = len(samples) / float(rate)
    env = onset_envelope(samples, rate)
    out = dict(bpm=0.0, beats_per_bar=4, phrase_bars=1, bars=0, confidence=0.0,
               duration=round(duration, 3))
    if duration < MIN_SECONDS or len(env) < 64 or not env.any():
        return out
    a = _acf(env)
    n = len(env)

    # 1. continuous tempo estimate (comb over the ACF, octave prior)
    bpms = np.arange(BPM_MIN, BPM_MAX, 0.25)
    lags = 60.0 * FPS / bpms
    raw = _comb(a, lags)
    score = np.maximum(raw, 0) * _prior(bpms)
    i = int(np.argmax(score))
    bpm0 = float(bpms[i])
    # prominence: peak vs the median of the scored curve
    med = float(np.median(score))
    prom = (score[i] - med) / (score[i] + 1e-9)

    # 2. loop fit: beat counts per file near the estimate, scored by the
    #    envelope's Fourier magnitude at that many cycles per file and its
    #    harmonics (eighths and sixteenths give the sharpest peaks)
    cyc = (n / FPS) / duration   # envelope cycles per beat in the file
    pad = 1 << int(math.ceil(math.log2(n * 32)))
    fine = np.abs(np.fft.rfft(env - env.mean(), n=pad))
    bin_per_cycle = pad / n

    def harmonics(ks):
        ks = np.asarray(ks, np.float64)
        tot = np.zeros(len(ks))
        for h in (1, 2, 4):
            b = ks * h * cyc * bin_per_cycle
            ok = b < len(fine) - 2
            tot[ok] += _at(fine, b[ok])
        return tot

    beats0 = bpm0 * duration / 60.0
    cand = np.arange(max(1, int(beats0 * 0.985)), int(math.ceil(beats0 * 1.015)) + 1)
    kbest = int(cand[int(np.argmax(harmonics(cand)))])
    ks = np.arange(kbest - 0.6, kbest + 0.6001, 0.02)
    hk = harmonics(ks)
    j = int(np.argmax(hk))
    kfrac = float(ks[j])
    peaked = 0 < j < len(ks) - 1   # a real peak, not the window's edge
    bpb, meter_ev = _meter(env, a, duration / kbest * FPS)
    bar_beats = bpb
    # the file is a loop of whole bars if the fractional beat count is near
    # a multiple of the bar
    bars_f = kfrac / bar_beats
    fits = peaked and abs(bars_f - round(bars_f)) <= BAR_FIT and round(bars_f) >= 1
    if fits:
        # snap so a whole number of bars fills the file exactly
        bars = int(round(bars_f))
        bpm = bars * bar_beats * 60.0 / duration
    else:
        # not a loop of whole bars: refine with the fractional peak
        bpm = kfrac * 60.0 / duration if abs(kfrac - beats0) < 0.05 * beats0 else bpm0
        # music made in a DAW is usually at a whole bpm: snap when that is
        # within the measurement (it drifts < 0.1 beat over a 3-minute track)
        if abs(bpm - round(bpm)) <= 0.05:
            bpm = float(round(bpm))
        bars = 0
    bar_s = 60.0 / bpm * bpb
    phrase = 4 if 4 * bar_s <= PHRASE_MAX_S else 2 if 2 * bar_s <= PHRASE_MAX_S else 1
    if bars and bars % phrase:
        phrase = 2 if bars % 2 == 0 and 2 * bar_s <= PHRASE_MAX_S else 1

    parts = int(min(8, max(2, duration // 8)))
    contrast, stability, offset = _grid_lock(env, 60.0 / bpm * FPS, parts)
    lock = max(0.0, min(1.0, (contrast - 1.5) / 2.5))
    # a grid counts when it stands out and holds for (nearly) the whole file;
    # a whole-bar loop fit adds the rest. A clean non-looping track scores
    # 0.75, one whose grid fails in 1/8 of it ~0.57, in 1/4 of it ~0.42.
    conf = 0.75 * lock * stability ** 2 + 0.25 * (1.0 if fits else 0.0)
    out.update(bpm=round(float(bpm), 6), beats_per_bar=int(bpb), phrase_bars=int(phrase),
               bars=int(bars), confidence=round(float(conf), 3), raw_bpm=round(bpm0, 2),
               beats=round(kfrac, 3), prominence=round(float(prom), 3),
               meter_evidence=round(float(meter_ev), 3), loop_fit=bool(fits),
               contrast=round(contrast, 2), stability=round(stability, 3),
               offset=round(offset, 3))
    return out


# --------------------------------------------------------------------------
# Files and the vn3ds.json entry
# --------------------------------------------------------------------------

def decode(path_or_bytes):
    """Mono float32 PCM at RATE via ffmpeg, or None."""
    if isinstance(path_or_bytes, (bytes, bytearray, memoryview)):
        args, data = ["-i", "-"], bytes(path_or_bytes)
    else:
        args, data = ["-i", str(path_or_bytes)], None
    try:
        p = subprocess.run(["ffmpeg", "-nostdin", "-v", "error"] + args +
                           ["-ac", "1", "-ar", str(RATE), "-f", "f32le", "-"],
                           input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           timeout=120)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if p.returncode != 0 or not p.stdout:
        return None
    return np.frombuffer(p.stdout[:len(p.stdout) // 4 * 4], np.float32)


def analyse_file(path_or_bytes, name=""):
    """analyse_pcm of a file (path or bytes), or None if it can't be decoded
    or is shorter than MIN_SECONDS."""
    pcm = decode(path_or_bytes)
    if pcm is None or len(pcm) < MIN_SECONDS * RATE:
        return None
    r = analyse_pcm(pcm, RATE)
    if name:
        r["name"] = name
    return r


def music_entry(result, min_confidence=0.5):
    """The vn3ds.json "music" entry for an analysis, or None when there is no
    result or its confidence is below min_confidence (the engine then
    crossfades on the beat). result["confidence"] holds the confidence."""
    if not result or result.get("bpm", 0) <= 0 or result.get("confidence", 0) < min_confidence:
        return None
    return {"bpm": round(result["bpm"], 6), "beats_per_bar": result["beats_per_bar"],
            "phrase_bars": result["phrase_bars"], "bars": result["bars"]}

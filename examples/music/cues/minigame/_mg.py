"""Shared pieces for the minigame cues (not a cue itself: render.py skips
files starting with `_`).

- exact_bpm(): a tempo whose loop is a whole number of 128-sample blocks, so
  the bar grid and the file length agree to the sample.
- a few extra voices for the games: pizzicato, bubble, hungry_bass,
  beat_kick (a warm kick that still reads on small speakers), meow.
- crush() and dive(): the bit-crushed / detuned accents.
"""
import math

import numpy as np

from vnsynth import SR, bandpass, highpass, lowpass, sweep, t_axis

SUB = "minigame"


def exact_bpm(target, bars, beats_per_bar=4):
    """The tempo nearest `target` whose `bars` last exactly a whole number of
    128-sample blocks (the loop length vnsynth renders), so the last bar
    line falls on the last sample instead of up to 2 ms off."""
    blocks = round(bars * beats_per_bar * 60.0 / target * SR / 128)
    return bars * beats_per_bar * 60.0 * SR / (128 * blocks)


# ---------------------------------------------------------------- voices

def pizzicato(freq, dur, vel=1.0):
    """A plucked string, finger on gut: bright snap, short woody body."""
    n = int(0.7 * SR)
    t = t_axis(n)
    s = np.zeros(n)
    for k in range(1, 9):
        fk = freq * k * (1 + 0.0007 * k * k)
        if fk > 4500:
            break
        s += np.sin(2 * np.pi * fk * t + 0.7 * k) / k ** 1.25 * np.exp(-t * (7 + 5 * k) * (freq / 300) ** 0.25)
    body = bandpass(s, 330, 1.4) * 0.6
    thump = lowpass(np.random.default_rng(int(freq)).normal(0, 1, n), 900) * np.exp(-t * 90) * 0.25
    return (s + body + thump) * np.clip(t / 0.0015, 0, 1) * 0.30 * vel


def bubble(freq, dur, vel=1.0):
    """A soft bubble: a sine whose pitch rises as it pops."""
    n = int(0.3 * SR)
    t = t_axis(n)
    f = freq * (1 + 0.55 * (1 - np.exp(-t * 26)))
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.12 * np.sin(4 * np.pi * np.cumsum(f) / SR)
    return s * np.exp(-t * 16) * np.clip(t / 0.003, 0, 1) * 0.30 * vel


def hungry_bass(freq, dur, vel=1.0):
    """A low pulse with a mouth: the filter opens and closes on every note, like a gulp."""
    n = int((dur + 0.12) * SR)
    t = t_axis(n)
    ph = np.cumsum(np.full(n, freq)) / SR
    saw = sum(np.sin(2 * np.pi * k * ph) / k for k in range(1, 16) if freq * k < 4000)
    s = 0.7 * saw + 0.9 * np.sin(2 * np.pi * ph)
    open_ = np.sin(np.pi * np.clip(t / max(dur, 0.05), 0, 1)) ** 1.5
    cut = 110 + 650 * open_ * vel
    s = sweep(s, "lp", cut[::64], 2.2)
    env = np.clip(t / 0.006, 0, 1) * np.clip((dur + 0.12 - t) / 0.08, 0, 1)
    return np.tanh(s * 1.4) * env * 0.26


def beat_kick(vel=1.0):
    """A warm, round kick with a felt 'tok' on top, so the beat is still clear
    through a handheld's small speakers (they barely play below 150 Hz)."""
    n = int(0.42 * SR)
    t = t_axis(n)
    f = 52 + 115 * np.exp(-t * 24)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7.5)
    knock = np.sin(2 * np.pi * 190 * t) * np.exp(-t * 38) * 0.45
    felt = lowpass(highpass(np.random.default_rng(5).normal(0, 1, n), 700), 2200) * np.exp(-t * 160) * 0.12
    s = np.tanh((body + knock + felt) * 1.3) * np.clip(t / 0.0015, 0, 1)
    return s * 0.75 * vel


def meow(seconds=0.5, f0=620, f1=400, gain=0.25):
    """A tiny synthesized 'mew' (as in the `miso` cue): a formant glide down."""
    n = int(seconds * SR)
    t = np.arange(n) / SR
    f = f0 - (f0 - f1) * (t / seconds) ** 1.5
    src = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.3 * np.sin(4 * np.pi * np.cumsum(f) / SR)
    x = bandpass(src, 900, 2) + 0.6 * lowpass(src, 700)
    return x * np.sin(np.pi * t / seconds) ** 1.5 * gain


# ---------------------------------------------------------------- accents

def crush(x, hold=6, levels=24, tone=3600):
    """Sample-rate and bit reduction (mono or stereo), smoothed so it crunches without hiss."""
    y = np.repeat(x[::hold], hold, axis=0)[:len(x)]
    y = np.round(y * levels) / levels
    return lowpass(y, tone, 0.7)


def dive(x, cents=-300, curve=2.0):
    """A tape-stop bend: the pitch sinks by `cents` over the sound."""
    n = len(x)
    p = np.linspace(0, 1, n) ** curve
    rate = 2 ** (cents * p / 1200)
    idx = np.cumsum(rate)
    idx = idx[idx < n - 1]
    y = np.interp(idx, np.arange(n), x)
    f = min(len(y) // 4, int(0.01 * SR))
    if f > 1:
        y[-f:] *= np.linspace(1, 0, f)
    return y


def detune(x, cents):
    """Resample a whole sound sharp or flat (a sour, slightly wrong copy)."""
    r = 2 ** (cents / 1200)
    return np.interp(np.arange(0, len(x) - 1, r), np.arange(len(x)), x)


def fade_edges(x, a=0.002, b=0.02):
    fa, fb = int(a * SR), int(b * SR)
    if fa:
        x[:fa] *= np.linspace(0, 1, fa)
    if fb:
        x[-fb:] *= np.cos(np.linspace(0, math.pi / 2, fb)) ** 2
    return x

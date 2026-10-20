"""Synthesise Snapshot's machine voices: speech-like syllables in no language.

    python3 examples/make_voice_bank.py

Writes game/audio/vox/syl00..23.ogg (the bank the 3DS engine plays one
syllable at a time, pitched per character) and game/audio/vox/babble_<who>.ogg
(short loops used by Ren'Py on a PC, where there is no per-letter callback).
"""

import os
import shutil
import subprocess
import tempfile
import wave

import numpy as np
from scipy.signal import lfilter

SR = 32000
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "demo", "game", "audio", "vox")
RNG = np.random.default_rng(5)

# (F1, F2, F3) in Hz: a, e, i, o, u
VOWELS = {"a": (780, 1250, 2500), "e": (480, 1900, 2550), "i": (320, 2250, 2950),
          "o": (480, 850, 2450), "u": (340, 760, 2350)}
ONSETS = ["", "b", "d", "k", "m", "n", "s", "t", "l", "r"]


def resonator(x, f, bw):
    r = np.exp(-np.pi * bw / SR)
    c = 2 * r * np.cos(2 * np.pi * f / SR)
    return lfilter([1 - r], [1, -c, r * r], x)


def syllable(onset, vowel, f0=150.0, dur=0.15):
    n = int(dur * SR)
    t = np.arange(n) / SR
    # a little pitch movement inside the syllable makes it sound spoken
    f = f0 * (1 + 0.06 * np.sin(np.pi * t / dur) - 0.04 * t / dur)
    ph = np.cumsum(f) / SR
    pulse = (ph % 1 < 0.18).astype(float) - 0.18          # buzzy glottal pulse
    pulse = lfilter([1], [1, -0.85], pulse)                # soften it
    F1, F2, F3 = VOWELS[vowel]
    voiced = resonator(pulse, F1, 90) + 0.6 * resonator(pulse, F2, 120) + 0.25 * resonator(pulse, F3, 180)
    env = np.minimum(1, t / 0.012) * np.exp(-np.maximum(0, t - dur * 0.55) * 30)
    out = voiced * env
    if onset:
        k = int(0.035 * SR)
        noise = RNG.normal(0, 1, k)
        if onset in "bdkt":            # plosive click
            burst = resonator(noise, {"b": 600, "d": 1800, "k": 2400, "t": 3000}[onset], 400) * np.exp(-np.arange(k) / (0.006 * SR))
            out = np.concatenate([burst * 0.6, out])
        elif onset == "s":
            hiss = lfilter([1, -0.95], [1], noise) * np.hanning(k) * 0.25
            out = np.concatenate([hiss, out])
        else:                          # m n l r: a short hum into the vowel
            hum = resonator(pulse[:k], {"m": 250, "n": 300, "l": 420, "r": 500}[onset], 80) * np.hanning(k)
            out = np.concatenate([hum, out])
    # machine flavour: gentle bit-crush and a soft ring-mod shimmer
    out = out / (np.abs(out).max() + 1e-9)
    out = np.round(out * 24) / 24
    out *= 1 - 0.15 * (0.5 + 0.5 * np.sin(2 * np.pi * 37 * np.arange(len(out)) / SR))
    out = lfilter([0.3, 0.3], [1, -0.4], out)              # take the edge off the highs
    tail = int(0.02 * SR)
    out[-tail:] *= np.linspace(1, 0, tail)
    return out / (np.abs(out).max() + 1e-9) * 0.8


def write(path, mono):
    stereo = np.stack([mono, mono], 1)
    data = (np.clip(stereo, -1, 1) * 32767).astype("<i2")
    with tempfile.TemporaryDirectory() as tmp:
        wav = os.path.join(tmp, "x.wav")
        with wave.open(wav, "wb") as w:
            w.setnchannels(2)
            w.setsampwidth(2)
            w.setframerate(SR)
            w.writeframes(data.tobytes())
        ffmpeg = shutil.which("ffmpeg")
        r = subprocess.run([ffmpeg, "-v", "error", "-y", "-i", wav, "-c:a", "libvorbis", "-q:a", "3", path],
                           capture_output=True)
        if r.returncode != 0:
            subprocess.run([ffmpeg, "-v", "error", "-y", "-i", wav, "-c:a", "vorbis", "-strict", "-2",
                            "-b:a", "64k", path], check=True)


# Pitch per character (1.0 = Aron). Kept in step with vn3ds.json "voices".
PITCHES = {"a": 1.0, "m": 1.34, "th": 0.86, "dr": 0.78, "nu": 1.22, "se": 1.55, "pi": 1.85,
           "dro": 0.62, "em": 1.42, "pa": 0.52, "council": 0.45, "stranger": 0.95, "radio": 1.1}


def main():
    os.makedirs(OUT, exist_ok=True)
    bank = []
    combos = [(o, v) for v in "aeiou" for o in ("", "b", "d", "k", "m")] [:20] + [("s", "a"), ("t", "i"), ("l", "o"), ("r", "e")]
    for i, (o, v) in enumerate(combos):
        syl = syllable(o, v)
        bank.append(syl)
        write(os.path.join(OUT, f"syl{i:02d}.ogg"), syl)
    # PC babble loops: syllables strung into a 3 second phrase, per character pitch
    for who, p in PITCHES.items():
        parts = []
        for k in range(16):
            s = bank[int(RNG.integers(0, len(bank)))]
            idx = np.arange(0, len(s) - 1, p)
            s = np.interp(idx, np.arange(len(s)), s)
            parts += [s, np.zeros(int(SR * RNG.uniform(0.02, 0.09)))]
        loop = np.concatenate(parts)
        write(os.path.join(OUT, f"babble_{who}.ogg"), loop * 0.9)
    print(f"wrote {len(bank)} syllables and {len(PITCHES)} babble loops to {OUT}")


if __name__ == "__main__":
    main()

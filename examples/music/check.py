"""Sanity-check the rendered cues: python3 examples/music/check.py [cue ...]

Names as for render.py: `theme`, `minigame/quiz`, or `minigame` for all the
minigame loops (levelled against the median of the main score).

For every audio/<cue>.ogg: duration, peak (clipping), RMS and loudness
against the median of all cues, and the loop seam: the level step from the
last 50 ms into the first 50 ms must lie within the range of the steps across
the cue's own bar lines (+-3 dB), the last half second must not drop out, and
the sample jump across the wrap must be no bigger than the cue's own
largest ordinary steps (99.9th percentile) or the steps at its own bar
lines, x1.5.
Also reports the share of energy in the 1-3 kHz band the game's machine
voices use, and above 6 kHz (flagged BRIGHT above -12 / -25 dB).
"""
import json
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from vnsynth import BUILD_DIR, GAME_AUDIO, SR, k_weight, meta_name  # noqa: E402

SUBFOLDERS = ("minigame",)


def decode(path):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "s16le", "-ac", "2", "-ar", str(SR), "-"],
                       capture_output=True, check=True)
    return np.frombuffer(r.stdout, "<i2").astype(np.float64).reshape(-1, 2) / 32768


def db(x):
    return 20 * np.log10(max(x, 1e-9))


def lvl(x):
    return db(np.sqrt(np.mean(x ** 2)))


def analyse(path):
    x = decode(path)
    w = int(0.05 * SR)
    rms = np.sqrt(np.mean(x ** 2))
    krms = np.sqrt(np.mean(k_weight(x) ** 2))
    head, tail = x[:w], x[-w:]
    # The wrap should sound like any other bar line of the cue: compare the
    # level step from the last 50 ms into the first 50 ms with the same step
    # across every internal bar line (a downbeat after a decaying bar is
    # normal; a dropout or a sudden wall of sound is not).
    step = lvl(head) - lvl(tail)
    meta = os.path.join(BUILD_DIR, meta_name(path) + ".json")
    bar_s = json.load(open(meta))["bar_s"] if os.path.exists(meta) else None
    inner = []
    if bar_s:
        for k in range(1, int(len(x) / SR / bar_s + 0.01)):
            i = int(round(k * bar_s * SR))
            inner.append(lvl(x[i:i + w]) - lvl(x[i - w:i]))
    # how far the wrap falls outside the range of the cue's own bar lines
    lo, hi = (min(inner), max(inner)) if inner else (0.0, 0.0)
    seam_db = step - hi if step > hi else (step - lo if step < lo else 0.0)
    tail_drop = lvl(x[-SR // 2:]) - lvl(x)            # a dropout before the wrap
    # share of the energy in the machine voices' formant band, and in the top end
    spec = np.abs(np.fft.rfft(x.mean(1)[: SR * 30])) ** 2
    f = np.fft.rfftfreq(min(len(x), SR * 30), 1 / SR)
    vband = 10 * np.log10(spec[(f > 1000) & (f < 3000)].sum() / spec.sum())
    hi = 10 * np.log10(spec[f > 6000].sum() / spec.sum())
    # the step across the wrap, relative to the cue's own largest ordinary steps and to the steps at
    # its internal bar lines (a note attacking on the downbeat is not a click; a discontinuity is)
    steps = np.abs(np.diff(x, axis=0)).max(1)
    ref = np.percentile(steps, 99.9)
    if bar_s:
        ref = max([ref] + [steps[int(round(k * bar_s * SR)) - 2:int(round(k * bar_s * SR)) + 2].max()
                           for k in range(1, int(len(x) / SR / bar_s + 0.01))])
    jump = np.abs(x[0] - x[-1]).max() / (ref + 1e-9)
    return dict(dur=len(x) / SR, peak=db(np.abs(x).max()), rms=db(rms), lufs=db(krms), seam=seam_db, jump=jump,
                tail=tail_drop, vband=vband, hi=hi,
                clip=int((np.abs(x) > 0.995).sum()))


def loops_in(sub):
    """The looping cues of a subfolder (those with a tempo grid in build/; sound effects have none)."""
    folder = os.path.join(GAME_AUDIO, sub)
    return sorted(sub + "/" + f[:-4] for f in os.listdir(folder)
                  if f.endswith(".ogg") and os.path.exists(os.path.join(BUILD_DIR, sub, f[:-4] + ".json")))


def main():
    # names: 'theme', 'minigame/quiz', or a subfolder ('minigame') for all its loops
    args = sys.argv[1:]
    names = []
    for a in args:
        names += loops_in(a) if a in SUBFOLDERS else [a]
    main_cues = sorted(f[:-4] for f in os.listdir(GAME_AUDIO) if f.endswith(".ogg"))
    names = names or main_cues
    rows = {n: analyse(os.path.join(GAME_AUDIO, n + ".ogg")) for n in names}
    ref = rows
    if any("/" in n for n in names):
        # cues in a subfolder are levelled against the main score
        ref = {n: rows.get(n) or analyse(os.path.join(GAME_AUDIO, n + ".ogg")) for n in main_cues}
    med = np.median([r["rms"] for r in ref.values()])
    kmed = np.median([r["lufs"] for r in ref.values()])
    print(f"{'cue':<26}{'dur':>7}{'peak':>7}{'rms':>7}{'d':>6}{'krms':>7}{'d':>6}{'seam':>7}{'tail':>6}{'jump':>6}{'1-3k':>6}{'>6k':>6}  flags")
    bad = 0
    for n, r in rows.items():
        flags = []
        if r["clip"]:
            flags.append("CLIP")
        if abs(r["rms"] - med) > 3:
            flags.append("LEVEL")
        if abs(r["seam"]) > 3 or r["tail"] < -15:
            flags.append("SEAM-LEVEL")
        if r["vband"] > -12 or r["hi"] > -25:
            flags.append("BRIGHT")
        if r["jump"] > 1.5:
            flags.append("CLICK")
        if not 30 <= r["dur"] <= 66:
            flags.append("LENGTH")
        bad += bool(flags)
        print(f"{n:<26}{r['dur']:7.1f}{r['peak']:7.1f}{r['rms']:7.1f}{r['rms'] - med:+6.1f}{r['lufs']:7.1f}"
              f"{r['lufs'] - kmed:+6.1f}{r['seam']:+7.1f}{r['tail']:+6.1f}{r['jump']:6.1f}{r['vband']:6.1f}{r['hi']:6.1f}  {' '.join(flags)}")
    print(f"median rms {med:.1f} dBFS; {bad} cue(s) flagged")


if __name__ == "__main__":
    main()

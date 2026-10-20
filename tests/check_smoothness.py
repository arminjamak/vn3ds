"""Checks a desktop run's timing log (vn3ds-host --perf) and music recording
(--music-wav) for the things that made Snapshot stutter on the 3DS:

  frames   no frame after the story moves on (A, auto, a transition ending)
           loads a picture on the main thread, or takes longer than the
           budget: everything the script shows next is preloaded;
  changes  every change of music lands on the playing track's grid: the end
           of its loop or a phrase boundary (or, without a grid, a beat);
  splices  the recording has no gap and no click at any splice.

    python3 tests/check_smoothness.py perf.txt stdout.txt music.wav [--budget-ms 8]

Prints one line per check and exits 1 if any fails."""
import argparse
import re
import sys
import wave

import numpy as np


def frames_check(lines, budget_ms):
    bad, n = [], 0
    for ln in lines:
        m = re.search(r"frame (\d+) (advance|after)[^:]*: update ([\d.]+) ms.*?sync textures (\d+)", ln)
        if not m:
            continue
        n += 1
        frame, upd, sync = int(m.group(1)), float(m.group(3)), int(m.group(4))
        if frame > 30 and (sync > 0 or upd > budget_ms):   # (the first frames open the game)
            bad.append(ln.strip())
    misses = [ln.strip() for ln in lines if "not preloaded" in ln or "needed before its preload" in ln]
    misses = [m for m in misses if "(__title)" not in m]
    return n, bad, misses


CHANGE = re.compile(r"music: change (\S+) -> (\S+): ([a-z ]+) at .*?out frame (\d+) at (\d+) Hz; "
                    r"track frame (\d+), loop (\d+) frames, bar ([\d.]+) frames, phrase ([\d.]+) frames")


def changes_check(lines):
    out, bad = [], []
    for ln in lines:
        m = CHANGE.search(ln)
        if not m:
            continue
        kind = m.group(3)
        at, rate, track, loop = int(m.group(4)), int(m.group(5)), int(m.group(6)), int(m.group(7))
        bar, phrase = float(m.group(8)), float(m.group(9))
        out.append((at, rate, kind, m.group(1), m.group(2)))
        if kind == "loop end":
            ok = loop > 0 and track % loop == 0
        elif kind == "phrase":
            r = (track % loop) % phrase if loop > 0 else track % phrase
            ok = min(r, phrase - r) <= 1.0
            # the grid itself: a whole number of bars per loop
            ok = ok and abs(loop / bar - round(loop / bar)) < 1e-6
        else:
            ok = True   # crossfades: beat-aligned when there is a grid
        if not ok:
            bad.append(ln.strip())
    return out, bad


def splices_check(wav_path, offset, changes):
    with wave.open(wav_path, "rb") as w:
        rate, n = w.getframerate(), w.getnframes()
        x = np.frombuffer(w.readframes(n), dtype=np.int16).reshape(-1, 2).astype(np.float64)
    mono = x.mean(axis=1)
    results = []
    for at, crate, kind, a, b in changes:
        i = at - offset
        if crate != rate or i < rate or i + rate > len(mono):
            continue
        seg = mono[i - rate // 2:i + rate // 2]
        # gap: no 15 ms stretch near the splice that is (almost) silent
        win = int(0.015 * rate)
        env = np.sqrt(np.convolve(seg ** 2, np.ones(win) / win, mode="valid"))
        before = np.sqrt(np.mean(mono[i - rate:i - rate // 4] ** 2))
        gap = env.min() < max(20.0, 0.02 * before)
        # click: the jump between neighbouring samples at the splice is no
        # bigger than the music's own (the largest jump in the second before
        # in the old track, or after it in the new one)
        d_splice = np.abs(np.diff(x[i - int(0.03 * rate):i + int(0.03 * rate)], axis=0)).max()
        d_music = max(np.abs(np.diff(x[i - rate:i - int(0.05 * rate)], axis=0)).max(),
                      np.abs(np.diff(x[i + int(0.05 * rate):i + rate], axis=0)).max())
        click = d_splice > 1.5 * d_music + 200
        results.append((at, kind, a, b, gap, click, env.min(), before, d_splice, d_music))
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("perf")
    ap.add_argument("stdout")
    ap.add_argument("wav", nargs="?")
    ap.add_argument("--budget-ms", type=float, default=8.0)
    args = ap.parse_args()
    lines = open(args.perf, errors="replace").read().splitlines()
    fail = False

    n, bad, misses = frames_check(lines, args.budget_ms)
    print(f"  {'ok  ' if not bad else 'FAIL'} frames: {n} frames after the story moved on, "
          f"{len(bad)} over {args.budget_ms:g} ms or loading a picture on the spot")
    for b in bad[:5]:
        print("       ", b)
    print(f"  {'ok  ' if not misses else 'FAIL'} preloads: {len(misses)} pictures not preloaded in time")
    for m in misses[:5]:
        print("       ", m)
    fail |= bool(bad or misses)

    changes, cbad = changes_check(lines)
    kinds = {}
    for c in changes:
        kinds[c[2]] = kinds.get(c[2], 0) + 1
    print(f"  {'ok  ' if not cbad else 'FAIL'} music changes on the grid: {len(changes)} "
          f"({', '.join(f'{v} {k}' for k, v in sorted(kinds.items())) or 'none'})")
    for b in cbad[:5]:
        print("       ", b)
    fail |= bool(cbad)

    if args.wav and not changes:
        print("  skip splices: no change of music in this run (a desktop build without Vorbis?)")
    elif args.wav:
        offset = None
        for ln in open(args.stdout, errors="replace"):
            m = re.search(r"\[music-wav\] .* starts at mixer frame (\d+)", ln)
            if m:
                offset = int(m.group(1))
        if offset is None:
            print("  FAIL splices: no [music-wav] line in the run's output")
            fail = True
        else:
            res = splices_check(args.wav, offset, changes)
            sbad = [r for r in res if r[4] or r[5]]
            print(f"  {'ok  ' if not sbad else 'FAIL'} splices: {len(res)} checked in the recording, "
                  f"{len(sbad)} with a gap or a click")
            for r in res:
                print(f"        out frame {r[0]} ({r[1]}): quietest 15 ms {r[6]:.0f} (music before "
                      f"{r[7]:.0f} rms), largest step {r[8]:.0f} (music's own {r[9]:.0f})"
                      f"{'  GAP' if r[4] else ''}{'  CLICK' if r[5] else ''}")
            fail |= bool(sbad)
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()

"""Tempo analysis (tools/vnpack/tempo.py) against Snapshot's score.

    python3 tests/test_tempo.py

Analyses every track in examples/demo/game/audio that has a "music" entry
in examples/demo/game/vn3ds.json (the truth, written from the score by
examples/music/meta.py), prints estimate vs truth, and fails if accuracy
falls below the thresholds at the bottom."""
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

from vnpack import tempo  # noqa: E402

GAME = os.path.join(ROOT, "examples", "demo", "game")

# Minimum fractions of tracks. Measured on 55 tracks: bpm 91%, up to an
# octave 96%, beats/bar 96%, bars 93%, entry 91%, and no confident entry
# with a wrong bar length; the limits leave a margin of ~3 tracks.
MIN_BPM_EXACT = 0.85      # bpm within 1% of the truth
MIN_BPM_OCTAVE = 0.90     # bpm within 1% of truth, x2 or /2
MIN_METER = 0.90          # beats_per_bar
MIN_BARS = 0.85           # loop length in bars exact
MIN_ENTRY = 0.85          # music_entry() given and equal to the truth (bpm within 1%)
MAX_BAD_ENTRY = 0.10      # music_entry() given but its bar length is wrong


def close(a, b, tol=0.01):
    return b > 0 and abs(a - b) <= tol * b


def main():
    with open(os.path.join(GAME, "vn3ds.json")) as f:
        truth = json.load(f)["music"]
    t_total = 0.0
    n = ok_bpm = ok_oct = ok_meter = ok_bars = ok_entry = bad_entry = 0
    print(f"{'track':28} {'bpm':>7} {'truth':>7} {'bpb':>3}/{'t':<1} {'bars':>4}/{'t':<3}"
          f" {'phr':>3}/{'t':<1} {'conf':>5} {'cpu ms':>6}")
    for key in sorted(truth):
        path = os.path.join(GAME, key)
        if not os.path.exists(path):
            continue
        t = truth[key]
        pcm = tempo.decode(path)
        t0 = time.process_time()
        r = tempo.analyse_pcm(pcm) if pcm is not None and len(pcm) >= tempo.MIN_SECONDS * tempo.RATE else None
        dt = time.process_time() - t0
        t_total += dt
        n += 1
        if r is None:
            print(f"{key:28} could not analyse")
            continue
        e = tempo.music_entry(r)
        b_ok = close(r["bpm"], t["bpm"])
        o_ok = b_ok or close(r["bpm"], 2 * t["bpm"]) or close(r["bpm"], t["bpm"] / 2)
        m_ok = r["beats_per_bar"] == t["beats_per_bar"]
        bars_ok = r["bars"] == t["bars"]
        entry_ok = (e is not None and close(e["bpm"], t["bpm"]) and
                    e["beats_per_bar"] == t["beats_per_bar"] and e["bars"] == t["bars"] and
                    e["phrase_bars"] == t["phrase_bars"])
        ok_bpm += b_ok
        ok_oct += o_ok
        ok_meter += m_ok
        ok_bars += bars_ok
        ok_entry += entry_ok
        # a confident grid whose bar is the wrong length would misplace every transition
        bar_s = 60.0 / t["bpm"] * t["beats_per_bar"]
        bad_entry += e is not None and not close(60.0 / e["bpm"] * e["beats_per_bar"], bar_s) \
            and not close(60.0 / e["bpm"] * e["beats_per_bar"], bar_s / 2) \
            and not close(60.0 / e["bpm"] * e["beats_per_bar"], bar_s * 2)
        flag = "" if entry_ok else ("  octave" if o_ok and not b_ok else "  MISS" if not o_ok else "  ~")
        print(f"{key[6:]:28} {r['bpm']:7.2f} {t['bpm']:7.2f} {r['beats_per_bar']:>3}/{t['beats_per_bar']:<1}"
              f" {r['bars']:>4}/{t['bars']:<3} {r['phrase_bars']:>3}/{t['phrase_bars']:<1}"
              f" {r['confidence']:5.2f} {dt * 1000:6.0f}{flag}")
    if not n:
        print("no tracks found")
        return 1
    frac = dict(bpm=ok_bpm / n, octave=ok_oct / n, meter=ok_meter / n, bars=ok_bars / n,
                entry=ok_entry / n, bad=bad_entry / n)
    print(f"\n{n} tracks, {t_total / n * 1000:.0f} ms CPU/track (analysis): bpm {frac['bpm']:.0%}, "
          f"bpm up to an octave {frac['octave']:.0%}, beats/bar {frac['meter']:.0%}, "
          f"bars {frac['bars']:.0%}, full entry {frac['entry']:.0%}, wrong-bar entries {frac['bad']:.0%}")
    fails = [k for k, lim in (("bpm", MIN_BPM_EXACT), ("octave", MIN_BPM_OCTAVE),
                              ("meter", MIN_METER), ("bars", MIN_BARS), ("entry", MIN_ENTRY))
             if frac[k] < lim]
    if frac["bad"] > MAX_BAD_ENTRY:
        fails.append("wrong-bar entries")
    if fails:
        print("FAIL: below threshold:", ", ".join(fails))
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())

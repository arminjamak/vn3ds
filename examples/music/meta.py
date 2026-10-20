"""Writes the score's tempo grids into the game's vn3ds.json ("music"), for
the engine's musical transitions: a change of music waits for the end of the
current loop or the next phrase boundary instead of cutting (see
engine/source/music.c).

    python3 examples/music/meta.py          # update ../demo/game/vn3ds.json
    python3 examples/music/meta.py --check  # only compare

Each cue's grid comes from its render (build/<cue>.json, written by
render.py); a cue that hasn't been rendered here is read from its source,
by running it up to the Song() line. Phrases are 4 bars, or 2 (or 1) when 4
bars would take longer than PHRASE_MAX_S, so a change of music never waits
long for its moment."""
import argparse
import glob
import json
import os
import re
import runpy
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CUES = os.path.join(HERE, "cues")
BUILD = os.path.join(HERE, "build")
CONFIG = os.path.join(os.path.dirname(HERE), "demo", "game", "vn3ds.json")
PHRASE_MAX_S = 8.0


class _GotSong(Exception):
    pass


def from_source(path):
    """bpm, bars and beats per bar of a cue, from its Song(...) line."""
    sys.path[:0] = [HERE, os.path.dirname(path)]
    import vnsynth
    found = {}
    real_init = vnsynth.Song.__init__

    def grab(self, bpm=90, bars=16, key="A minor", beats_per_bar=4, swing=0.0):
        found.update(bpm=bpm, bars=bars, beats_per_bar=beats_per_bar)
        raise _GotSong()

    vnsynth.Song.__init__ = grab
    try:
        runpy.run_path(path, run_name="__main__")
    except _GotSong:
        pass
    finally:
        vnsynth.Song.__init__ = real_init
    return found or None


def grid(name, path):
    meta = os.path.join(BUILD, name + ".json")
    if os.path.exists(meta):
        with open(meta) as f:
            m = json.load(f)
        return dict(bpm=m["bpm"], bars=m["bars"], beats_per_bar=m.get("beats_per_bar", 4))
    with open(path) as f:
        alias = re.search(r'render_as\("([^"]+)"', f.read())
    if alias:
        return grid(alias.group(1), os.path.join(CUES, alias.group(1) + ".py"))
    return from_source(path)


def phrase_bars(g):
    bar_s = 60.0 / g["bpm"] * g["beats_per_bar"]
    for p in (4, 2, 1):
        if g["bars"] % p == 0 and p * bar_s <= PHRASE_MAX_S:
            return p
    return 1


def table():
    out = {}
    for path in sorted(glob.glob(os.path.join(CUES, "*.py")) + glob.glob(os.path.join(CUES, "minigame", "*.py"))):
        stem = os.path.splitext(os.path.relpath(path, CUES))[0].replace(os.sep, "/")
        if os.path.basename(stem).startswith("_") or stem.endswith("sfx"):
            continue
        g = grid(stem, path)
        if not g:
            print(f"  {stem}: no Song() found, skipped")
            continue
        out[f"audio/{stem}.ogg"] = dict(bpm=round(float(g["bpm"]), 6), beats_per_bar=int(g["beats_per_bar"]),
                                        phrase_bars=phrase_bars(g), bars=int(g["bars"]))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--check", action="store_true", help="only report whether vn3ds.json is up to date")
    args = ap.parse_args()
    with open(CONFIG) as f:
        text = f.read()
    cfg = json.loads(text)
    music = table()
    if args.check:
        same = cfg.get("music") == music
        print("vn3ds.json music table is up to date" if same else "vn3ds.json music table differs")
        sys.exit(0 if same else 1)
    cfg["music"] = music
    with open(CONFIG, "w") as f:
        f.write(json.dumps(cfg, indent=1))
    print(f"{len(music)} tracks written to {os.path.relpath(CONFIG)}")


if __name__ == "__main__":
    main()

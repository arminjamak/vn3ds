"""Render the score: python3 examples/music/render.py [--masters] [cue ...]

Each file in cues/ is one looping cue written in vnsynth. Renders them all
(or the named ones) into examples/demo/game/audio/.

The minigame cues live in cues/minigame/ and render into audio/minigame/:
name them as `minigame/quiz`, or `minigame` for all of them (their loops and
`minigame/sfx`, the shared sound effects). Files starting with `_` are
helpers, not cues.

--masters writes lossless FLAC masters into build/master/ instead (and leaves
the .ogg files alone): vnpack encodes the 3DS's audio from those when they
are there (vn3ds.json "audio_masters"), one lossy generation instead of two.
"""
import os
import runpy
import sys
import time
from concurrent.futures import ProcessPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
CUES = os.path.join(HERE, "cues")
SUBFOLDERS = ("minigame",)
sys.path.insert(0, HERE)


def render_one(path):
    t = time.time()
    for p in (HERE, os.path.dirname(path)):
        if p not in sys.path:
            sys.path.insert(0, p)
    import vnsynth
    vnsynth.reseed()
    runpy.run_path(path, run_name="__main__")
    rel = os.path.relpath(path, CUES)
    return rel, time.time() - t


def find_cues(names):
    """Cue scripts by name: 'theme', 'minigame/quiz', or a whole subfolder ('minigame')."""
    found = []
    for sub in ("",) + SUBFOLDERS:
        folder = os.path.join(CUES, sub)
        if not os.path.isdir(folder):
            continue
        for f in sorted(os.listdir(folder)):
            if not f.endswith(".py") or f.startswith("_"):
                continue
            name = (sub + "/" if sub else "") + f[:-3]
            if not names or name in names or (sub and sub in names):
                found.append(os.path.join(folder, f))
    missing = [n for n in names if n not in SUBFOLDERS and not any(
        os.path.relpath(p, CUES)[:-3].replace(os.sep, "/") == n for p in found)]
    if missing:
        sys.exit("no such cue: " + ", ".join(missing))
    return found


def main():
    args = sys.argv[1:]
    if "--masters" in args:
        # lossless masters only, into build/master/ (the game's .ogg files stay)
        args.remove("--masters")
        os.environ["VNSYNTH_MASTERS"] = os.path.join(HERE, "build", "master")
        os.environ["VNSYNTH_MASTERS_ONLY"] = "1"
    cues = find_cues(args)
    with ProcessPoolExecutor(max_workers=min(4, os.cpu_count() or 2)) as ex:
        for name, dt in ex.map(render_one, cues):
            print(f"  {name:<28} {dt:5.1f}s", flush=True)


if __name__ == "__main__":
    main()

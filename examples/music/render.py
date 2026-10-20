"""Render the score: python3 examples/music/render.py [cue ...]

Each file in cues/ is one looping cue written in vnsynth. Renders them all
(or the named ones) into examples/demo/game/audio/.
"""
import os
import runpy
import sys
import time
from concurrent.futures import ProcessPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def render_one(path):
    t = time.time()
    sys.path.insert(0, HERE)
    import vnsynth
    vnsynth.reseed()
    runpy.run_path(path, run_name="__main__")
    return os.path.basename(path), time.time() - t


def main():
    names = sys.argv[1:]
    cues = sorted(os.path.join(HERE, "cues", f) for f in os.listdir(os.path.join(HERE, "cues"))
                  if f.endswith(".py") and (not names or f[:-3] in names))
    with ProcessPoolExecutor(max_workers=min(4, os.cpu_count() or 2)) as ex:
        for name, dt in ex.map(render_one, cues):
            print(f"  {name:<28} {dt:5.1f}s", flush=True)


if __name__ == "__main__":
    main()

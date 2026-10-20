"""Pack files (tools/vnpack/packs.py, engine/source/vfs.c).

    python3 tests/test_packs.py build/snapshot

Checks a packed game folder: its PACK table covers every resource, the same
game unpacked into loose files plays identically in the desktop build (the
transcript and every frame), and changing, adding or removing one file
changes at most two packs.
"""

import hashlib
import os
import random
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from vnpack import packs  # noqa: E402

HOST = os.path.join(ROOT, "engine", "build-host", "vn3ds-host")
failed = False


def check(ok, msg):
    global failed
    print(("  ok: " if ok else "  FAIL: ") + msg)
    failed |= not ok


def play(game, out, root):
    os.makedirs(root, exist_ok=True)
    with open(os.path.join(root, "settings.cfg"), "w") as f:
        f.write("text_speed = 6\n")
    r = subprocess.run([HOST, game, "--root", root, "--out", out, "--max-lines", "25",
                        "--choices", "0,1,0,1"], capture_output=True, text=True)
    lines = [ln for ln in r.stdout.splitlines() if " ms" not in ln]
    return r.returncode, lines


def main():
    game = sys.argv[1]
    tmp = tempfile.mkdtemp(prefix="packs-")
    try:
        sections = dict(packs.read_game(os.path.join(game, "game.bin")))
        check(b"PACK" in sections, "game.bin has a PACK section")
        check(not os.path.isdir(os.path.join(game, "img")), "no loose img/ folder")
        npk = len(os.listdir(os.path.join(game, "pk")))
        check(npk >= 2, f"{npk} pack files")

        loose = os.path.join(tmp, "loose", os.path.basename(game.rstrip("/")))
        shutil.copytree(game, loose)
        n = packs.unpack(loose)
        _, res = packs.first_use(packs.read_game(os.path.join(loose, "game.bin")))
        missing = [r for r in res if r and not os.path.isfile(os.path.join(loose, r))]
        check(n > 0 and not missing, f"{n} files unpacked, every resource among them "
                                     f"({len(missing)} missing)")

        ca, la = play(game, os.path.join(tmp, "fa"), os.path.join(tmp, "ra"))
        cb, lb = play(loose, os.path.join(tmp, "fb"), os.path.join(tmp, "rb"))
        check(ca == 0 and cb == 0 and la == lb and len(la) > 20,
              f"packed and loose transcripts match ({len(la)} lines)")
        fa = sorted(os.listdir(os.path.join(tmp, "fa")))
        same = all(open(os.path.join(tmp, "fa", f), "rb").read() ==
                   open(os.path.join(tmp, "fb", f), "rb").read() for f in fa)
        check(fa == sorted(os.listdir(os.path.join(tmp, "fb"))) and same,
              f"{len(fa)} frames identical")

        # update stability: one file changed, added or removed
        order, _ = packs.first_use(packs.read_game(os.path.join(loose, "game.bin")))
        files, seen = [], set()
        for r in order:
            rel = res[r]
            if rel and rel not in seen:
                seen.add(rel)
                files.append((rel, os.path.getsize(os.path.join(loose, rel)), packs._class(rel)))
        target = 2 << 20   # small packs, so a small game still has many of them
        base = {tuple(r for r, _ in g) for g in packs.plan(files, target)}
        random.seed(7)
        worst = 0
        for trial in range(60):
            i = random.randrange(len(files))
            rel, sz, cls = files[i]
            new = f"{rel.split('/')[0]}/{hashlib.sha1(str(trial).encode()).hexdigest()[:16]}." + \
                rel.rsplit(".", 1)[1]
            g = list(files)
            if trial % 3 == 0:
                g[i] = (new, int(sz * 1.2) + 1, cls)
            elif trial % 3 == 1:
                g.insert(i, (new, sz, cls))
            else:
                del g[i]
            changed = sum(1 for p in packs.plan(g, target) if tuple(r for r, _ in p) not in base)
            worst = max(worst, changed)
        check(worst <= 2, f"one changed file changes at most {worst} packs of {len(base)}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("packs: all passed" if not failed else "packs: FAILED")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()

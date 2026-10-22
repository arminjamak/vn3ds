#!/usr/bin/env python3
"""Writes manifest.txt for a packed game, so vn3ds can download it from the web
(engine/source/fetch.h; the home screen's first-run Snapshot offer).

    python3 tools/dl_manifest.py build/snapshot

Upload the folder with its manifest.txt so that <url>/manifest.txt and
<url>/<file> resolve over plain http:// (the 3DS client does no HTTPS).
Cover and script go first, so the arriving card shows its picture and name
early. Files over 25 MB are refused: Cloudflare Pages won't serve them.
"""

import os
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vnpack.send import _files_of  # noqa: E402  (the same files a Wi-Fi send would push)

MAX_FILE = 25 * 1000 * 1000
FIRST = ("cover.thm", "game.bin")


def crc_of(path):
    c = 0
    with open(path, "rb") as f:
        while chunk := f.read(1 << 20):
            c = zlib.crc32(chunk, c)
    return c


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    folder = sys.argv[1].rstrip("/")
    game_id = os.path.basename(folder)
    files = [(rel.split("/", 1)[1], full) for rel, full in _files_of(folder, "x")
             if not rel.endswith(("/manifest.txt", "/port-report.txt"))]
    files.sort(key=lambda f: (FIRST.index(f[0]) if f[0] in FIRST else len(FIRST), f[0]))
    lines, total = [f"vn3ds-dl 1 {game_id}"], 0
    for rel, full in files:
        size = os.path.getsize(full)
        if size > MAX_FILE:
            sys.exit(f"{rel} is {size >> 20} MB: repack with a smaller --pack-mb")
        lines.append(f"{size} {crc_of(full):08x} {rel}")
        total += size
    with open(os.path.join(folder, "manifest.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"{folder}/manifest.txt: {len(files)} files, {total / 1e6:.1f} MB")


if __name__ == "__main__":
    main()

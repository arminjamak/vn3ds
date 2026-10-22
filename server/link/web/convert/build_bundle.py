#!/usr/bin/env python3
"""Packs the converter for the browser: server/link/web/convert/vnpack.zip
holds tools/vnpack (without the depth model: no 3D movies in a browser),
the bundled unrpyc, and vn3ds_browser.py. Run it whenever vnpack changes,
before publishing web/ (vn3ds.com serves these files).

    python3 server/link/web/convert/build_bundle.py"""

import os
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", "..", "..", ".."))
OUT = os.path.join(HERE, "vnpack.zip")


def add_tree(z, folder, under, keep):
    for dirpath, dirs, files in os.walk(folder):
        dirs[:] = sorted(d for d in dirs if d not in ("__pycache__", "models"))
        for name in sorted(files):
            if keep(name):
                full = os.path.join(dirpath, name)
                z.write(full, os.path.join(under, os.path.relpath(full, folder)))


def main():
    with zipfile.ZipFile(OUT + ".tmp", "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        add_tree(z, os.path.join(REPO, "tools", "vnpack"), "tools/vnpack",
                 lambda n: n.endswith((".py", ".json")))
        add_tree(z, os.path.join(REPO, "tools", "third_party", "unrpyc"), "tools/third_party/unrpyc",
                 lambda n: n.endswith(".py") or n in ("LICENSE", "LICENSE.txt"))
        z.write(os.path.join(HERE, "vn3ds_browser.py"), "vn3ds_browser.py")
    os.replace(OUT + ".tmp", OUT)
    print(f"{OUT}: {os.path.getsize(OUT) / 1e6:.1f} MB")


if __name__ == "__main__":
    sys.exit(main())

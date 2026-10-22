"""Standalone apps (vn3ds-port --app, tools/vnpack/app3dsx.py).

    python3 tests/test_app3dsx.py build/snapshot [app.3dsx]

Builds (or checks) the .3dsx of a ported game: the engine's code is copied
unchanged, the SMDH has the game's title and an icon, and every file of the
game is in the romfs under games/<id>/, found both by libctru's hash lookup
and by the folder walk the engine does for pack files (appfs_locate), with
the same bytes. With devkitPro's 3dsxtool installed, its --romfs output for
the same folder must read back the same. Then the desktop build plays the
game in single-game mode (--app), and its "Export as app" writes the same
.3dsx on the console side (engine/source/export.c).
"""

import os
import shutil
import struct
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from vnpack import app3dsx, port  # noqa: E402

HOST = os.path.join(ROOT, "engine", "build-host", "vn3ds-host")
ENGINE = os.path.join(ROOT, "engine", "vn3ds.3dsx")
failed = False


def check(ok, msg):
    global failed
    print(("  ok: " if ok else "  FAIL: ") + msg)
    failed |= not ok


def game_files(game_dir):
    out = {}
    for r, _, fs in os.walk(game_dir):
        for f in fs:
            if f not in ("port-report.txt", "savemap.json") and not f.startswith("."):
                full = os.path.join(r, f)
                out[os.path.relpath(full, game_dir).replace(os.sep, "/")] = full
    return out


def main():
    game_dir = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "build/snapshot")
    gid = os.path.basename(game_dir.rstrip("/"))
    tmp = tempfile.mkdtemp(prefix="vn3ds-app-")
    try:
        app = sys.argv[2] if len(sys.argv) > 2 else None
        if not app:
            app, size, _ = port.build_app(game_dir, gid, tmp, author="Test Author")
        blob = open(app, "rb").read()
        code, info = app3dsx.read_3dsx(app)
        ecode, _ = app3dsx.read_3dsx(ENGINE)
        check(code[0x2C:] == ecode[0x2C:] and code[:0x20] == ecode[:0x20],
              "the engine's code and relocations are unchanged")
        title, desc, author = app3dsx.read_smdh(info["smdh"])
        want, _ = port.ported_title(game_dir)
        check(title == want, f"SMDH title {title!r}")
        check(bool(author), f"SMDH author {author!r}, description {desc!r}")
        icon = app3dsx.smdh_icon(info["smdh"])
        check(len(set(icon.getdata())) > 8, "the 48x48 icon is a picture")
        romfs = blob[info["fs_offset"]:]
        found = app3dsx.read_romfs(romfs)   # asserts every entry is in the hash tables
        files = game_files(game_dir)
        same = all(f"games/{gid}/{k}" in found and
                   romfs[found[f"games/{gid}/{k}"][0]:][:found[f"games/{gid}/{k}"][1]] ==
                   open(v, "rb").read() for k, v in files.items())
        check(same and len(found) == len(files), f"all {len(files)} files are in the romfs, "
              f"byte for byte ({len(blob) / 1e6:.1f} MB)")
        hdr = struct.unpack_from("<10I", romfs)
        check(hdr[0] == 0x28 and hdr[9] % 16 == 0, "romfs header as libctru reads it")

        tool = shutil.which("3dsxtool") or "/opt/devkitpro/tools/bin/3dsxtool"
        elf = os.path.join(ROOT, "engine", "vn3ds.elf")
        if os.path.exists(tool) and os.path.exists(elf):
            tree = os.path.join(tmp, "tree", "games", gid)
            shutil.copytree(game_dir, tree, ignore=shutil.ignore_patterns("port-report.txt", "savemap.json"))
            ref = os.path.join(tmp, "ref.3dsx")
            with open(os.path.join(tmp, "app.smdh"), "wb") as f:   # (it wants one with a romfs)
                f.write(info["smdh"])
            subprocess.run([tool, elf, ref, "--smdh=" + os.path.join(tmp, "app.smdh"),
                            f"--romfs={os.path.join(tmp, 'tree')}"],
                           check=True, capture_output=True)
            _, rinfo = app3dsx.read_3dsx(ref)
            rblob = open(ref, "rb").read()[rinfo["fs_offset"]:]
            rfound = app3dsx.read_romfs(rblob)
            check(sorted(rfound) == sorted(found) and all(
                rblob[rfound[k][0]:][:rfound[k][1]] == romfs[found[k][0]:][:found[k][1]]
                for k in found), "3dsxtool --romfs holds the same files at the same paths")
        else:
            print("  (no 3dsxtool: skipped the comparison with devkitPro's romfs)")

        if os.path.exists(HOST):
            # the console's own "Export as app" (engine/source/export.c): the same romfs
            sd = os.path.join(tmp, "sd")
            os.makedirs(os.path.join(sd, "3ds"))
            shutil.copy(ENGINE, os.path.join(sd, "3ds", "vn3ds.3dsx"))
            r = subprocess.run([HOST, game_dir, "--root", os.path.join(sd, "3ds", "vn3ds"),
                                "--sdmc", sd, "--self", os.path.join(sd, "3ds", "vn3ds.3dsx"),
                                "--export"], capture_output=True, text=True)
            made = os.path.join(sd, "3ds", gid + ".3dsx")
            if os.path.exists(made):
                mcode, minfo = app3dsx.read_3dsx(made)
                mrom = open(made, "rb").read()[minfo["fs_offset"]:]
                check(mrom == romfs and mcode[0x2C:] == code[0x2C:],
                      "Export as app on the console writes the same romfs and code, beside vn3ds")
                check(os.path.exists(os.path.join(sd, "3ds", gid, "app.cfg")),
                      "the exported app is registered for vn3ds's library")
            else:
                check(False, "Export as app: " + (r.stdout + r.stderr)[-300:])
            r = subprocess.run([HOST, game_dir, "--app", "--root", os.path.join(tmp, "root"),
                                "--max-lines", "3", "--test-save"], capture_output=True, text=True)
            menu = [l for l in r.stdout.splitlines() if "[app] title menu" in l]
            items = menu[0].split(":")[1].split("(")[0].split() if menu else []
            check(r.returncode == 0 and "3" in items and "7" not in items,
                  "single-game mode: the title screen offers Open vn3ds (3), not Export as app (7)")
            check(os.path.exists(os.path.join(tmp, "root", "saves", gid, "slot01.sav")),
                  "single-game mode: saves go to the app's own folder")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()

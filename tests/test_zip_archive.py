"""An .rpa compressed inside a .zip download (as Android builds ship their
art: an .apk plus archive.rpa) is read in place: vn3ds-port writes a pointer
file instead of unpacking it, and AssetFS reads its files through
assets.InflatedMember. Run: python3 tests/test_zip_archive.py"""

import os
import pickle
import random
import shutil
import sys
import tempfile
import zipfile
import zlib

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
from vnpack import assets, port   # noqa: E402

fail = 0


def check(ok, what):
    global fail
    print(("  ok: " if ok else "  FAIL: ") + what)
    fail |= not ok


def make_rpa(path, files, key=0x42424242):
    """An RPA-3.0 archive of {name: bytes}."""
    index = {}
    with open(path, "wb") as f:
        f.write(b"RPA-3.0 %016x %08x\n" % (0, key))
        for name, data in files.items():
            index[name] = [(f.tell() ^ key, len(data) ^ key)]
            f.write(data)
        at = f.tell()
        f.write(zlib.compress(pickle.dumps(index, 2)))
        f.seek(0)
        f.write(b"RPA-3.0 %016x %08x\n" % (at, key))


def main():
    tmp = tempfile.mkdtemp()
    try:
        rnd = random.Random(7)
        files = {}
        for i in range(60):   # some compressible, some not, a few MiB in all
            n = rnd.randrange(1, 200_000)
            files[f"images/f{i}.png"] = (bytes(rnd.randrange(256) for _ in range(n // 4)) * 4
                                          if i % 2 else rnd.randbytes(n))
        rpa = os.path.join(tmp, "archive.rpa")
        make_rpa(rpa, files)
        zp = os.path.join(tmp, "game-android.zip")
        with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
            z.write(rpa, "archive.rpa")
            z.writestr("notes.txt", "install the apk")
        os.remove(rpa)

        assets.InflatedMember.CHECKPOINT = 256 << 10   # many checkpoints
        work = os.path.join(tmp, "work")
        dest = port.unpack_zip(zp, work)
        check(os.path.isfile(os.path.join(dest, "archive.rpa" + assets.RPA_REF[4:])),
              "the archive is left in the zip, a pointer file stands in for it")
        check(not os.path.exists(os.path.join(dest, "archive.rpa")), "nothing was unpacked")
        check(port.find_game_dir(dest) == dest, "the pointer counts as game files")

        fs = assets.AssetFS(dest, lambda *a: print("warn", a))
        check(len(fs.files) == len(files), f"all {len(files)} files are listed")
        names = list(files)
        rnd.shuffle(names)
        same = all(fs.read(n.lower()) == files[n] for n in names)
        check(same, "random-order reads match the originals")
        check(all(fs.read(n.lower()) == files[n] for n in sorted(names)), "in-order reads too")
        check(fs.size("images/f3.png") == len(files["images/f3.png"]), "sizes from the index")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("zip archive: " + ("FAIL" if fail else "all ok"))
    return fail


if __name__ == "__main__":
    sys.exit(main())

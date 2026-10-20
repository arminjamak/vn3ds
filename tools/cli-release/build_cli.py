"""Builds the standalone vn3ds-port command for this computer's OS and CPU.

    .venv/bin/python tools/cli-release/build_cli.py [--version 1.0.0]

Needs (see README.md in this folder):
  - a Python with PyInstaller, numpy and Pillow (the project's .venv)
  - engine/vn3ds.3dsx (make in engine/, or --engine PATH)
  - static ffmpeg and ffprobe with libx264, libvorbis and libopus in
    tools/cli-release/vendor/<target>/ (or --ffmpeg-dir DIR)

Writes tools/cli-release/dist/vn3ds-cli-<target>.tar.gz (macOS) or .zip
(Windows), holding a vn3ds/ folder with the vn3ds-port program, and prints
its SHA-256. <target> is mac-arm64, mac-x64 or windows-x64.
"""

import argparse
import hashlib
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
WORK = os.path.join(HERE, "work")
DIST = os.path.join(HERE, "dist")
NEEDED_ENCODERS = ("libx264", "libvorbis", "libopus")


def target_name():
    machine = platform.machine().lower()
    arch = "arm64" if machine in ("arm64", "aarch64") else "x64"
    if sys.platform == "darwin":
        return f"mac-{arch}"
    if os.name == "nt":
        return f"windows-{arch}"
    return f"linux-{arch}"


def version_string(given):
    if given:
        return given
    try:
        return subprocess.run(["git", "describe", "--tags", "--always", "--dirty"], cwd=REPO,
                              capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "dev"


def check_ffmpeg(folder, exe):
    paths = [os.path.join(folder, n + exe) for n in ("ffmpeg", "ffprobe")]
    for p in paths:
        if not os.path.isfile(p):
            sys.exit(f"build_cli: {p} is missing (see README.md: 'ffmpeg')")
    r = subprocess.run([paths[0], "-hide_banner", "-encoders"], capture_output=True, text=True)
    missing = [e for e in NEEDED_ENCODERS if f" {e} " not in r.stdout]
    if r.returncode != 0 or missing:
        sys.exit(f"build_cli: {paths[0]} lacks the encoders {', '.join(missing) or '?'}")
    return paths


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--version", help="version shown by vn3ds-port --version (default: git describe)")
    ap.add_argument("--target", default=target_name(), help="name for the archive (default: %(default)s)")
    ap.add_argument("--engine", default=os.path.join(REPO, "engine", "vn3ds.3dsx"))
    ap.add_argument("--ffmpeg-dir", help="folder with ffmpeg and ffprobe "
                                         "(default: tools/cli-release/vendor/<target>)")
    ap.add_argument("--keep-work", action="store_true")
    args = ap.parse_args()

    try:
        import PyInstaller  # noqa: F401
        import numpy  # noqa: F401
        import PIL  # noqa: F401
    except ImportError as e:
        sys.exit(f"build_cli: {e.name} is not installed in {sys.executable} (see README.md)")
    exe = ".exe" if os.name == "nt" else ""
    if not os.path.isfile(args.engine):
        sys.exit(f"build_cli: {args.engine} isn't built (make in engine/, or pass --engine)")
    ff_dir = args.ffmpeg_dir or os.path.join(HERE, "vendor", args.target)
    ffmpeg, ffprobe = check_ffmpeg(ff_dir, exe)
    version = version_string(args.version)

    shutil.rmtree(WORK, ignore_errors=True)
    os.makedirs(WORK)
    os.makedirs(DIST, exist_ok=True)
    with open(os.path.join(WORK, "vn3ds_build.py"), "w") as f:
        f.write(f"VERSION = {version!r}\nTARGET = {args.target!r}\n")

    sep = os.pathsep
    unrpyc = os.path.join(REPO, "tools", "third_party", "unrpyc")
    cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--onedir", "--console",
           "--name", "vn3ds-port",
           "--distpath", os.path.join(WORK, "dist"), "--workpath", os.path.join(WORK, "build"),
           "--specpath", WORK,
           "--paths", os.path.join(REPO, "tools"), "--paths", unrpyc, "--paths", WORK,
           "--collect-submodules", "vnpack", "--hidden-import", "vnpack.__main__",
           "--hidden-import", "vn3ds_build",
           # unrpyc runs in-process (--vn3ds-unrpyc), so it is frozen in too
           "--hidden-import", "unrpyc", "--hidden-import", "deobfuscate",
           "--collect-submodules", "decompiler",
           "--exclude-module", "tkinter", "--exclude-module", "matplotlib",
           "--add-data", f"{args.engine}{sep}engine",
           # ffmpeg is copied as it is (data, not analysed or re-signed)
           "--add-data", f"{ffmpeg}{sep}ffmpeg", "--add-data", f"{ffprobe}{sep}ffmpeg",
           os.path.join(HERE, "vn3ds_cli.py")]
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)

    built = os.path.join(WORK, "dist", "vn3ds-port")
    root = os.path.join(WORK, "package", "vn3ds")
    shutil.rmtree(os.path.dirname(root), ignore_errors=True)
    shutil.copytree(built, root, symlinks=True)
    for p in (os.path.join(root, "_internal", "ffmpeg", "ffmpeg" + exe),
              os.path.join(root, "_internal", "ffmpeg", "ffprobe" + exe)):
        os.chmod(p, 0o755)
    shutil.copy2(os.path.join(HERE, "THIRD_PARTY_NOTICES.md"), root)
    shutil.copytree(os.path.join(HERE, "licenses"), os.path.join(root, "licenses"))
    shutil.copy2(os.path.join(REPO, "LICENSE"), os.path.join(root, "LICENSE.txt"))
    with open(os.path.join(root, "README.txt"), "w") as f:
        f.write(f"vn3ds-port {version} ({args.target})\n\n"
                "Ports a Ren'Py visual novel to the Nintendo 3DS and puts it there:\n"
                "    vn3ds-port \"path/to/your game\"\n"
                "(drag the game into the terminal window to type its path).\n\n"
                "It finds the 3DS's SD card if it is in this computer, otherwise the 3DS\n"
                "on the Wi-Fi. Run vn3ds-port --help for the options.\n\n"
                "Bundled: ffmpeg (GPL), unrpyc (MIT), Python and its libraries; see\n"
                "THIRD_PARTY_NOTICES.md.\n")

    if args.target.startswith("windows"):
        out = os.path.join(DIST, f"vn3ds-cli-{args.target}.zip")
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            for dp, _, names in os.walk(root):
                for n in names:
                    full = os.path.join(dp, n)
                    z.write(full, os.path.relpath(full, os.path.dirname(root)))
    else:
        out = os.path.join(DIST, f"vn3ds-cli-{args.target}.tar.gz")
        with tarfile.open(out, "w:gz") as t:
            t.add(root, arcname="vn3ds")
    digest = sha256(out)
    with open(out + ".sha256", "w") as f:
        f.write(f"{digest}  {os.path.basename(out)}\n")
    if not args.keep_work:
        shutil.rmtree(os.path.join(WORK, "build"), ignore_errors=True)
    print(f"\nbuilt {out}\n  {os.path.getsize(out) / 1e6:.1f} MB, sha256 {digest}\n"
          f"  test it: {os.path.join(root, 'vn3ds-port' + exe)} --version")


if __name__ == "__main__":
    main()

"""Downloads the static ffmpeg + ffprobe that a standalone build bundles, and
checks them against the SHA-256 sums recorded here.

    python3 tools/cli-release/fetch_ffmpeg.py [mac-arm64 | mac-x64 | windows-x64]

Puts ffmpeg and ffprobe (.exe on Windows) in tools/cli-release/vendor/<target>/.
All three builds are FFmpeg 9.0.2 with libx264, libvorbis and libopus (GPL v3).
To move to newer builds, change the URLs and sums below (the builders publish
a .sha256 / checksums.sha256 next to each download) and THIRD_PARTY_NOTICES.md.
"""

import hashlib
import os
import platform
import shutil
import sys
import urllib.request
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))

MR = "https://ffmpeg.martin-riedl.de/download/macos"
BTBN = "https://github.com/BtbN/FFmpeg-Builds/releases/download/autobuild-2026-10-20-13-08"
WIN_ZIP = "ffmpeg-n9.0.2-29-g6dfaba896f-win64-gpl-9.0.zip"

# target: [(url, sha256, {name inside the zip: name to write})]
BUILDS = {
    "mac-arm64": [
        (f"{MR}/arm64/1789931890_9.0.2/ffmpeg.zip",
         "c8ed4c4e6978a03c485edbfe4e0a5dc2380f8a30bba5150531b31b094492d924", {"ffmpeg": "ffmpeg"}),
        (f"{MR}/arm64/1789931890_9.0.2/ffprobe.zip",
         "fcbe839537485eaee7a7a8bc5cbc0f90d53617e80943e8a5b2e31cb851197ea6", {"ffprobe": "ffprobe"}),
    ],
    "mac-x64": [
        (f"{MR}/amd64/1789931006_9.0.2/ffmpeg.zip",
         "7c6b4125b191cbf773832dc51f424cf2b6bb7da43007d1e066f95909e47cacd4", {"ffmpeg": "ffmpeg"}),
        (f"{MR}/amd64/1789931006_9.0.2/ffprobe.zip",
         "2322438ed2f6319a691291b247d09c69dcaa3a982460d1f269a7e1af335cfdfd", {"ffprobe": "ffprobe"}),
    ],
    "windows-x64": [
        (f"{BTBN}/{WIN_ZIP}",
         "5d2804fd10e90610657375a8777611f858426f29da61bf5f0c4f8e78798a7119",
         {WIN_ZIP[:-4] + "/bin/ffmpeg.exe": "ffmpeg.exe",
          WIN_ZIP[:-4] + "/bin/ffprobe.exe": "ffprobe.exe"}),
    ],
}


def default_target():
    arch = "arm64" if platform.machine().lower() in ("arm64", "aarch64") else "x64"
    return ("windows" if os.name == "nt" else "mac") + "-" + arch


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else default_target()
    if target not in BUILDS:
        sys.exit(f"fetch_ffmpeg: no build for {target} (have: {', '.join(BUILDS)})")
    dest = os.path.join(HERE, "vendor", target)
    dl = os.path.join(dest, "dl")
    os.makedirs(dl, exist_ok=True)
    for url, want, members in BUILDS[target]:
        path = os.path.join(dl, url.rsplit("/", 1)[1])
        if not (os.path.exists(path) and sha256(path) == want):
            print(f"downloading {url}", flush=True)
            with urllib.request.urlopen(url) as r, open(path + ".part", "wb") as f:
                shutil.copyfileobj(r, f, 1 << 20)
            os.replace(path + ".part", path)
        got = sha256(path)
        if got != want:
            os.remove(path)
            sys.exit(f"fetch_ffmpeg: {url}\n  sha256 {got}\n  expected {want}")
        print(f"  ok {os.path.basename(path)} sha256 {got}")
        with zipfile.ZipFile(path) as z:
            for member, name in members.items():
                out = os.path.join(dest, name)
                with z.open(member) as src, open(out, "wb") as f:
                    shutil.copyfileobj(src, f, 1 << 20)
                os.chmod(out, 0o755)
                print(f"  -> {out} (sha256 {sha256(out)})")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


if __name__ == "__main__":
    main()

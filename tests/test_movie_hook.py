"""Movies through another H.264 encoder (assets.H264_ENCODER), as in a web
page (server/link/web/convert/h264.js through tools/vnpack/webmovies.py).

1. A game with five movies, packed with an encoder that is told about each
   movie ahead of its turn (prefetch) and asked for it on its turn: every
   movie is started before it is collected, never more than MOVIE_PREFETCH
   ahead, and the .cvh files are the ones the usual path makes (the stand-in
   encoder runs the same x264).
2. A stream coded in parts with different settings (SPS) is refused rather
   than packed wrong.

    python3 tests/test_movie_hook.py
"""

import hashlib
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from vnpack import __main__ as vnmain  # noqa: E402
from vnpack import assets  # noqa: E402

fails = 0


def check(ok, what):
    global fails
    print(("  ok: " if ok else "  FAIL: ") + what)
    if not ok:
        fails += 1


def make_game(proj, n):
    g = os.path.join(proj, "game")
    os.makedirs(g)
    lines = ['init python:\n', '    gui.init(1280, 720)\n', 'define config.name = "Movie hook"\n']
    for i in range(n):
        ext = "webm" if i % 2 else "mp4"
        lines.append(f'image clip{i} = Movie(play="clip{i}.{ext}")\n')
        codec = ["-c:v", "libvpx", "-b:v", "500k"] if ext == "webm" else ["-c:v", "libx264", "-preset", "ultrafast"]
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
                        f"testsrc2=s=640x360:r=24:d={1 + i % 3}", "-pix_fmt", "yuv420p", *codec,
                        os.path.join(g, f"clip{i}.{ext}")], check=True)
    lines.append("label start:\n")
    for i in range(n):
        lines += [f"    scene clip{i}\n", f'    "Clip {i}."\n']
    lines.append("    return\n")
    with open(os.path.join(g, "script.rpy"), "w") as f:
        f.writelines(lines)


def cvh_digests(out):
    d = os.path.join(out, "movie-hook", "img")
    return sorted(hashlib.sha1(open(os.path.join(d, f), "rb").read()).hexdigest()
                  for f in os.listdir(d) if f.endswith(".cvh"))


def pack(proj, out):
    vnmain.main([proj, "-o", out, "-q", "--no-audio", "--no-packs", "--video-kbps", "200", "-j", "1"])


def hooked():
    tmp = tempfile.mkdtemp()
    proj = os.path.join(tmp, "proj")
    make_game(proj, 5)
    os.environ["VN3DS_CACHE"] = os.path.join(tmp, "cache")

    pack(proj, os.path.join(tmp, "plain"))
    plain = cvh_digests(os.path.join(tmp, "plain"))

    events = []
    started = {}

    def encoder(key, data, ext, w, h, fps_cap, kbps, gop_seconds, max_seconds, profile, level,
                preset, wait):
        if not wait:
            events.append(("start", key))
            started[key] = data
            return None
        events.append(("collect", key))
        if key not in started:
            return None
        stream, first, fps, _sinfo, _w, _wv = assets._encode_h264_ffmpeg(
            started.pop(key), ext, w, h, kbps, fps_cap, max_seconds, profile, level,
            gop_seconds, preset, None, False)
        return stream, first.tobytes() if hasattr(first, "tobytes") else first, fps

    old = vnmain.MOVIE_PREFETCH
    vnmain.MOVIE_PREFETCH = 2
    assets.H264_ENCODER = encoder
    try:
        pack(proj, os.path.join(tmp, "hooked"))
    finally:
        assets.H264_ENCODER = None
        vnmain.MOVIE_PREFETCH = old
    hook = cvh_digests(os.path.join(tmp, "hooked"))

    starts = [k for e, k in events if e == "start"]
    collects = [k for e, k in events if e == "collect"]
    check(len(collects) == 5 and sorted(starts) == sorted(collects),
          f"each of the 5 movies started once and collected once ({len(starts)}, {len(collects)})")
    order_ok = all(events.index(("start", k)) < events.index(("collect", k)) for k in collects)
    check(order_ok, "every movie was started before its turn")
    ahead = max_ahead = 0
    for e, _k in events:
        ahead += 1 if e == "start" else -1
        max_ahead = max(max_ahead, ahead)
    check(max_ahead <= 2, f"at most MOVIE_PREFETCH (2) under way at once (saw {max_ahead})")
    check(len(hook) == 5 and hook == plain, "the .cvh files are the same as without the hook")


def sps_guard():
    good = assets._encode_h264_ffmpeg  # a real stream, then one part with another SPS
    tmp = tempfile.mkdtemp()
    clip = os.path.join(tmp, "c.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=s=400x240:r=10:d=1",
                    "-pix_fmt", "yuv420p", "-c:v", "libx264", "-preset", "ultrafast", clip], check=True)
    data = open(clip, "rb").read()
    a = good(data, ".mp4", 400, 240, 200, 30, None, "main", "3.0", 4.0, "slower", None, False)
    b = good(data, ".mp4", 400, 240, 200, 30, None, "high", "3.1", 4.0, "slower", None, False)
    try:
        assets._pack_cvh(a[0] + b[0], a[1], a[2], 400, 240, 400, 400, 240, True, False, None,
                         1.0, 0, "pillow", 5.0)
        check(False, "a stream with two different SPS is refused")
    except OSError as e:
        check("SPS" in str(e), "a stream with two different SPS is refused")


print("movies through another encoder, started ahead of their turn")
hooked()
print("parts coded with different settings")
sps_guard()
print("movie hook: all passed" if not fails else "movie hook: FAILED")
sys.exit(1 if fails else 0)

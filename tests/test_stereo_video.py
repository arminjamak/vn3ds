"""Stereoscopic movies (vnpack --video-3d, tools/vnpack/stereo.py).

1. The view synthesis: a near square over a far, striped background lands
   where its disparity says in the right view, and the hole it leaves is
   filled with background, not with the square's colour.
2. A small game with one movie, packed with --video-3d and a stand-in depth
   (VN3DS_DEPTH_MODEL=:test: brightness as nearness, so no model is needed):
   the .cvh is side by side with the stereo flag, its poster is one view,
   and the desktop engine (decoding with ffmpeg) shows the eyes different
   views: the bright square nearer (crossed), the stripes behind the screen.
   With the 3D slider low it plays flat; a 2D build still plays as before.

    python3 tests/test_stereo_video.py
"""

import os
import shutil
import struct
import subprocess
import sys
import tempfile

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from vnpack import stereo  # noqa: E402

fails = 0


def check(ok, what):
    global fails
    print(("  ok: " if ok else "  FAIL: ") + what)
    if not ok:
        fails += 1


def synthesis():
    h, w = 60, 120
    left = np.zeros((h, w, 3), np.uint8)
    left[:, ::8] = (0, 0, 200)            # stripes on the background
    left[20:40, 50:70] = (255, 255, 0)    # a square
    disp = np.full((h, w), 6.0, np.float32)
    disp[20:40, 50:70] = -2.0
    right = stereo.right_view(left, disp)
    yel = (right[30, :, 0] > 200) & (right[30, :, 1] > 200)
    xs = np.nonzero(yel)[0]
    check(len(xs) and xs.min() == 48 and xs.max() == 67,
          f"near square moves 2 px left (x {xs.min() if len(xs) else '-'}..{xs.max() if len(xs) else '-'})")
    blue = np.nonzero(right[5, :, 2] > 150)[0]
    check(14 in blue and 22 in blue and 8 not in blue, "far stripes move 6 px right")
    hole = right[30, 68:76]
    check(not ((hole[:, 0] > 200) & (hole[:, 1] > 200)).any(),
          "the disoccluded strip is filled with background, not the square")
    again = stereo.right_view(left, disp)
    check(np.array_equal(right, again), "deterministic")


def make_game(proj):
    g = os.path.join(proj, "game")
    os.makedirs(g)
    with open(os.path.join(g, "script.rpy"), "w") as f:
        f.write('init python:\n'
                '    gui.init(1280, 720)\n'
                'define config.name = "Stereo test"\n'
                'image clip = Movie(play="clip.mp4")\n'
                "label start:\n"
                "    scene clip\n"
                "    pause 2.0\n"
                '    "A square in front of stripes."\n'
                "    return\n")
    # 1280x720, 20 fps, 3 s: dark stripes, a bright square
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
                    "color=c=0x202020:s=1280x720:r=20:d=3", "-vf",
                    "drawgrid=w=48:h=720:t=6:c=0x5060a0,drawgrid=w=70:h=720:t=9:c=0x30a050,"
                    "drawbox=x=480:y=220:w=320:h=280:c=0xf0f0f0:t=fill",
                    "-pix_fmt", "yuv420p", "-c:v", "libx264", "-preset", "ultrafast",
                    os.path.join(g, "clip.mp4")], check=True)


def pack(proj, out, *extra):
    env = dict(os.environ, VN3DS_DEPTH_MODEL=stereo.TEST_MODEL,
               PYTHONPATH=os.path.join(ROOT, "tools"))
    subprocess.run([sys.executable, "-m", "vnpack", proj, "-o", out, "-q", "--no-audio",
                    "--no-packs", "--video-kbps", "300", *extra], check=True, env=env)
    d = os.path.join(out, "stereo-test")
    cvh = [f for f in os.listdir(os.path.join(d, "img")) if f.endswith(".cvh")]
    return d, os.path.join(d, "img", cvh[0])


def play(game, frames, slider):
    host = os.path.join(ROOT, "engine", "build-host", "vn3ds-host")
    env = dict(os.environ, VN3DS_VIDEO_FFMPEG="1")
    subprocess.run([host, game, "--out", frames, "--every", "10", "--slider", str(slider),
                    "--root", frames + "_root", "--max-lines", "2"], check=True, env=env,
                   capture_output=True)
    shots = sorted(f for f in os.listdir(frames) if f.endswith("_pause.png"))
    from PIL import Image
    img = np.asarray(Image.open(os.path.join(frames, shots[-1])).convert("RGB")).astype(int)
    return img[:240, :400], img[:240, 408:808]


def shift(left, right, x0, x1, y0=100, y1=140):
    """How far right the right eye's picture of columns x0..x1 sits (px)."""
    a = left[y0:y1, x0:x1].sum(2).astype(float)
    if x1 - x0 < 8:   # an edge: where the brightness first passes 600
        def edge(eye):
            return int(np.argmax(eye[(y0 + y1) // 2, x0:x1 + 40].sum(1) > 600))
        return edge(right) - edge(left)
    best, err = 0, None
    for d in range(-16, 17):
        b = right[y0:y1, x0 + d:x1 + d].sum(2).astype(float)
        e = np.abs(a - b).mean()
        if err is None or e < err:
            best, err = d, e
    return best


def movie(tmp):
    proj = os.path.join(tmp, "proj")
    make_game(proj)
    game, cvh = pack(proj, os.path.join(tmp, "b3d"), "--video-3d")
    b = open(cvh, "rb").read()
    w, h = struct.unpack_from("<HH", b, 8)
    flags = struct.unpack_from("<I", b, 32)[0]
    mid = struct.unpack_from("<f", b, 56)[0]
    check(flags & 2 and (w, h) == (864, 240), f"stereo .cvh: {w}x{h}, flags {flags}")
    check(-2.0 < mid < 6.0, f"median disparity {mid:.2f} px in the header")
    with open(cvh[:-4] + ".ctex", "rb") as f:
        ct = f.read(36)
    pw = struct.unpack_from("<H", ct, 12)[0]
    check(pw == 216, f"poster is one view (216 px wide at half size, got {pw})")

    left, right = play(game, os.path.join(tmp, "f3d"), 1.0)
    sq, bg = shift(left, right, 130, 134), shift(left, right, 20, 120)
    check(-3 <= sq <= -1, f"square in front of the screen (right eye {sq} px)")
    check(2 <= bg <= 7 and bg - sq >= 4,
          f"stripes behind the screen and the square (right eye +{bg} px)")
    left, right = play(game, os.path.join(tmp, "f3d_mid"), 0.6)
    sq2, bg2 = shift(left, right, 130, 134), shift(left, right, 20, 120)
    check(bg2 < bg and abs((bg2 - sq2) - (bg - sq)) <= 1,
          f"slider at 0.6: the scene comes forward, its relief stays ({sq2}, +{bg2} px)")
    left, right = play(game, os.path.join(tmp, "f3d_low"), 0.2)
    sq, bg = shift(left, right, 130, 134), shift(left, right, 20, 120)
    check(sq == bg, f"slider at 0.2: flat (square {sq} px, stripes {bg} px)")

    game2, cvh2 = pack(proj, os.path.join(tmp, "b2d"))
    b2 = open(cvh2, "rb").read()
    check(struct.unpack_from("<HH", b2, 8) == (432, 240) and not
          struct.unpack_from("<I", b2, 32)[0] & 2, "without --video-3d: a mono 432x240 .cvh")
    left, right = play(game2, os.path.join(tmp, "f2d"), 1.0)
    sq, bg = shift(left, right, 130, 134), shift(left, right, 20, 120)
    check(sq == bg and sq > 4, f"mono movie: flat at the background's depth ({sq}, {bg} px)")


def scenes(tmp):
    """--scenes-3d: a still background becomes a side-by-side pair (image
    flag 8), and each eye sees its own view: the bright square in front,
    the stripes behind; with the 3D low it is flat."""
    from PIL import Image, ImageDraw
    proj = os.path.join(tmp, "sproj")
    g = os.path.join(proj, "game")
    os.makedirs(g)
    img = Image.new("RGB", (1280, 720), (0x20, 0x20, 0x20))
    d = ImageDraw.Draw(img)
    for x in range(0, 1280, 48):   # two periods, as the movie: a shift can't alias
        d.rectangle([x, 0, x + 6, 720], fill=(0x50, 0x60, 0xa0))
    for x in range(0, 1280, 70):
        d.rectangle([x, 0, x + 9, 720], fill=(0x30, 0xa0, 0x50))
    d.rectangle([480, 220, 800, 500], fill=(0xf0, 0xf0, 0xf0))
    img.save(os.path.join(g, "bg.png"))
    with open(os.path.join(g, "script.rpy"), "w") as f:
        f.write('init python:\n'
                '    gui.init(1280, 720)\n'
                'define config.name = "Scenes test"\n'
                'image bg test = "bg.png"\n'
                "label start:\n"
                "    scene bg test\n"
                "    pause 1.0\n"
                '    "A square in front of stripes."\n'
                "    return\n")
    env = dict(os.environ, VN3DS_DEPTH_MODEL=stereo.TEST_MODEL,
               PYTHONPATH=os.path.join(ROOT, "tools"))

    def pack_scene(out, *extra):
        subprocess.run([sys.executable, "-m", "vnpack", proj, "-o", out, "-q", "--no-audio",
                        "--no-packs", *extra], check=True, env=env)
        d = os.path.join(out, "scenes-test")
        widths = []
        for f in os.listdir(os.path.join(d, "img")):
            if f.endswith(".ctex"):
                with open(os.path.join(d, "img", f), "rb") as fh:
                    widths.append(struct.unpack_from("<H", fh.read(36), 12)[0])
        return d, max(widths)

    game, w3 = pack_scene(os.path.join(tmp, "s3d"), "--scenes-3d")
    game2, w2 = pack_scene(os.path.join(tmp, "s2d"))
    check(w3 == 2 * w2, f"the scene is stored as a pair side by side ({w3} px, 2D {w2} px)")
    left, right = play(game, os.path.join(tmp, "sf3d"), 1.0)
    sq, bg = shift(left, right, 130, 134), shift(left, right, 20, 120)
    check(-3 <= sq <= -1, f"scene: square in front of the screen (right eye {sq} px)")
    check(2 <= bg <= 7 and bg - sq >= 4, f"scene: stripes behind the screen (right eye +{bg} px)")
    left, right = play(game, os.path.join(tmp, "sf3d_low"), 0.2)
    sq, bg = shift(left, right, 130, 134), shift(left, right, 20, 120)
    check(sq == bg, f"scene, slider at 0.2: flat (square {sq} px, stripes {bg} px)")


def main():
    synthesis()
    if not shutil.which("ffmpeg"):
        print("  (no ffmpeg: skipping the movie test)")
    else:
        tmp = tempfile.mkdtemp()
        try:
            movie(tmp)
            scenes(tmp)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    print("stereo video: " + ("all ok" if not fails else f"{fails} FAILED"))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()

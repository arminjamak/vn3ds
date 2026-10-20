"""Test for vnpack --cg-patches: a CG variant stored as a patch over the
picture before it must look the same on screen as the variant stored whole.

    python3 tests/test_cg_patches.py [--keep DIR]   (from the repository root)

Packs a small project twice with the same JPEG settings, without and with
--cg-patches, plays both in the desktop build (engine/build-host/vn3ds-host)
and compares every dumped frame: plain, zoomed and rotated, faded, mirrored,
and with the 3D slider up. The patched frames must be within 40 dB PSNR of
the whole-image frames, and there must be no seam: along the patch's edges
the two may differ no more than inside it. With --keep the frames and 3x
crops of the patch edges are kept in DIR for looking at."""

import os
import shutil
import struct
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tests"))
from test_jpeg import picture  # noqa: E402

HOST = os.path.join(ROOT, "engine", "build-host", "vn3ds-host")
SCRIPT = """\
init python:
    gui.init(1280, 720)

transform closer:
    zoom 1.35 xalign 0.7 yalign 0.4 rotate 4

transform half:
    alpha 0.5

transform mirrored:
    xzoom -1.0

label start:
    scene cg 1
    "The whole picture."
    scene cg 2 with dissolve
    "The variant."
    show cg 2 at closer
    "Zoomed and turned."
    show cg 2 at half
    "Half faded."
    scene black
    show cg 2 at mirrored
    "Mirrored."
    scene cg 3
    "Another variant."
    return
"""

failures = []


def check(cond, msg):
    print(("  ok: " if cond else "  FAIL: ") + msg)
    if not cond:
        failures.append(msg)


def psnr(a, b):
    m = np.mean((a.astype(np.float64) - b.astype(np.float64)) ** 2)
    return 99.0 if m == 0 else 10 * np.log10(255 ** 2 / m)


def make_project(d):
    g = os.path.join(d, "game")
    os.makedirs(os.path.join(g, "images"))
    with open(os.path.join(g, "script.rpy"), "w") as f:
        f.write(SCRIPT)
    base = np.asarray(picture(1280, 720, 11), np.int16)
    v2 = base.copy()
    # a changed region (a face, a hand): a new shape with soft edges, plus
    # render noise below the threshold everywhere else
    y, x = np.mgrid[0:720, 0:1280]
    blob = np.clip(1.4 - np.hypot((x - 820) / 150.0, (y - 300) / 110.0), 0, 1)[..., None]
    v2 = v2 * (1 - blob) + np.array([230, 90, 60]) * blob
    v3 = base.copy()
    v3[100:260, 150:380] = 255 - v3[100:260, 150:380]
    rng = np.random.default_rng(3)
    for name, a in (("cg 1", base), ("cg 2", v2), ("cg 3", v3)):
        a = a + (rng.integers(-1, 2, a.shape) if name != "cg 1" else 0)
        Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save(
            os.path.join(g, "images", name + ".png"))


def layr_patches(game_bin):
    """(image index, base res, patch res, x, y, w, h) for each patch record:
    x, y in texels, w, h in logical px."""
    data = open(game_bin, "rb").read()
    out = []
    count = struct.unpack_from("<I", data, 8)[0]
    table = {data[12 + 12 * i:16 + 12 * i]: struct.unpack_from("<II", data, 16 + 12 * i)
             for i in range(count)}
    if b"LAYR" not in table:
        return out
    p = table[b"LAYR"][0]
    n = struct.unpack_from("<I", data, p)[0]
    p += 4
    for _ in range(n):
        img, nl = struct.unpack_from("<II", data, p)
        p += 8
        layers = [struct.unpack_from("<ifffffIfff", data, p + 40 * k) for k in range(nl)]
        p += 40 * nl
        if nl == 2 and layers[1][6] == 7:
            out.append((img, layers[0][0], layers[1][0], int(layers[1][7]), int(layers[1][8]),
                        layers[1][4], layers[1][5]))
    return out


def frames(build, game_id, out, root, slider):
    os.makedirs(root, exist_ok=True)
    r = subprocess.run([HOST, os.path.join(build, game_id), "--out", out, "--root", root,
                        "--slider", str(slider)], capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout[-2000:], r.stderr[-2000:])
    bad = [ln for ln in (r.stdout + r.stderr).splitlines() if "cannot load texture" in ln]
    check(r.returncode == 0 and not bad, f"{game_id} plays ({len(bad)} texture errors)")
    return sorted(f for f in os.listdir(out) if f.endswith(".png"))


def main():
    keep = sys.argv[sys.argv.index("--keep") + 1] if "--keep" in sys.argv else None
    tmp = tempfile.mkdtemp(prefix="cgpatch-")
    try:
        subprocess.run(["make", "-s", "-C", os.path.join(ROOT, "engine"), "-f", "Makefile.host"],
                       check=True)
        proj = os.path.join(tmp, "proj")
        make_project(proj)
        common = ["--jpeg", "75", "--jpeg-encoder", "ffmpeg", "--jpeg-qscale", "2",
                  "--rgb565", "--no-audio", "--id", "cgp", "-q"]
        env = dict(os.environ, PYTHONPATH=os.path.join(ROOT, "tools"))
        for tag, extra in (("whole", []), ("patched", ["--cg-patches"])):
            subprocess.run([sys.executable, "-m", "vnpack", proj, "-o", os.path.join(tmp, tag)] +
                           common + extra, check=True, env=env)

        print("packer")
        patches = layr_patches(os.path.join(tmp, "patched", "cgp", "game.bin"))
        check(len(patches) == 2, f"cg 2 and cg 3 stored as patches ({len(patches)} records)")
        check(all(x % 16 == 0 and y % 16 == 0 for _, _, _, x, y, _, _ in patches),
              "patches start on 16-pixel block boundaries: " +
              ", ".join(f"({x}, {y})" for _, _, _, x, y, _, _ in patches))

        def img_bytes(tag):
            d = os.path.join(tmp, tag, "cgp", "img")
            return sum(os.path.getsize(os.path.join(d, f)) for f in os.listdir(d))
        whole, patched = img_bytes("whole"), img_bytes("patched")
        check(patched < whole * 0.8, f"image bytes {whole} -> {patched}")

        for slider in (1.0, 0.0):
            print(f"frames: patched vs whole, 3D slider {slider:g} (both eyes)")
            fa = frames(os.path.join(tmp, "whole"), "cgp", os.path.join(tmp, "fa"),
                        os.path.join(tmp, "ra"), slider)
            fb = frames(os.path.join(tmp, "patched"), "cgp", os.path.join(tmp, "fb"),
                        os.path.join(tmp, "rb"), slider)
            check(fa == fb and len(fa) >= 6, f"{len(fa)} frames each")
            for f in fa:
                a = np.asarray(Image.open(os.path.join(tmp, "fa", f)).convert("RGB"))[:240]
                b = np.asarray(Image.open(os.path.join(tmp, "fb", f)).convert("RGB"))[:240]
                p = psnr(a, b)
                d = np.abs(a.astype(np.int16) - b.astype(np.int16)).max(-1)
                check(p > 40, f"{f}: PSNR {p:.1f} dB, largest difference {d.max()}")
            if keep:
                for tag in ("fa", "fb"):
                    shutil.copytree(os.path.join(tmp, tag),
                                    os.path.join(keep, f"{tag}_slider{slider:g}"), dirs_exist_ok=True)
        # The patch edges in the plain full-screen frames (slider 0, left eye):
        # the 1280x720 picture is 427x240 texels, drawn 426.7 px wide from
        # x = -13.3, then enlarged about the centre by 1 + 14/213.3 / 214 so
        # the stereo shift never shows an edge (render_sprite).
        need = 214.0 / (200 + 13.333)
        to_x = lambda t: 200 - (200 - (-13.333 + t * 426.667 / 427)) * need   # noqa: E731
        to_y = lambda t: 120 - (120 - t) * need   # noqa: E731
        # Seams, in the plain frames: stepping across a patch edge must change
        # the picture no more than the same step in the whole-image frame.
        for f, (_, _, _, x0, y0, pw, ph) in ((fa[2], patches[0]), (fa[6], patches[1])):
            a = np.asarray(Image.open(os.path.join(tmp, "fa", f)).convert("RGB"))[:240, :400]
            b = np.asarray(Image.open(os.path.join(tmp, "fb", f)).convert("RGB"))[:240, :400]
            a, b = a.astype(np.float64), b.astype(np.float64)
            xs, ys = to_x(x0), to_y(y0)
            xe, ye = xs + pw * need, ys + ph * need

            def steps(xs, ys, xe, ye):
                """Largest extra step (patched minus whole) across the box's edges."""
                r0, r1 = max(1, int(ys) + 2), min(239, int(ye) - 2)
                c0, c1 = max(1, int(xs) + 2), min(399, int(xe) - 2)
                worst = 0.0
                for edge in (xs, xe):           # vertical edges
                    for c in range(int(edge) - 1, int(edge) + 2):
                        if 1 <= c < 400 and r1 > r0:
                            sb = np.abs(b[r0:r1, c] - b[r0:r1, c - 1]).mean()
                            sa = np.abs(a[r0:r1, c] - a[r0:r1, c - 1]).mean()
                            worst = max(worst, sb - sa)
                for edge in (ys, ye):           # horizontal edges
                    for r in range(int(edge) - 1, int(edge) + 2):
                        if 1 <= r < 240 and c1 > c0:
                            sb = np.abs(b[r, c0:c1] - b[r - 1, c0:c1]).mean()
                            sa = np.abs(a[r, c0:c1] - a[r - 1, c0:c1]).mean()
                            worst = max(worst, sb - sa)
                return worst
            worst = steps(xs, ys, xe, ye)
            # the same measure on boxes that are not patch edges: how much the
            # two encodings differ anyway
            floor = max(steps(xs + dx, ys + dy, xe + dx, ye + dy)
                        for dx, dy in ((5, 0), (-5, 0), (0, 5), (0, -5), (9, 9), (-9, -9)))
            check(worst <= floor + 1.0,
                  f"{f}: no seam at the patch edges (steps across them at most {worst:.2f} levels "
                  f"larger than in the whole picture; {floor:.2f} across lines off the edges)")
            if keep:
                os.makedirs(keep, exist_ok=True)
                sx, sy = int(xs), int(ys)
                box = (max(0, sx - 40), max(0, sy - 30), min(400, sx + 60), min(240, sy + 50))
                for tag, arr in (("whole", a), ("patched", b)):
                    im = Image.fromarray(arr.astype(np.uint8)).crop(box)
                    im.resize((im.width * 3, im.height * 3), Image.NEAREST).save(
                        os.path.join(keep, f"{f[:-4]}_{tag}_edge_3x.png"))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("CG patch tests " + ("passed" if not failures else f"FAILED ({len(failures)})"))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

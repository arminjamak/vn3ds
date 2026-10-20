"""Tests for the engine's JPEG decoder (engine/source/jpeg.c) and the JPEG .ctex
the packager writes. Needs a C compiler, numpy and Pillow.

    python3 tests/test_jpeg.py          (from the repository root)

Checks, against Pillow's decoding of the same files, that the decoder is
accurate for 4:4:4, 4:2:2, 4:2:0 and grayscale images of awkward sizes, that
its tiled RGB565 output (with edge padding) matches its own RGB output, that
progressive files are refused, and that truncated or corrupted files never
crash it."""

import io
import os
import struct
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from vnpack.assets import encode_ctex, next_pow2, swizzle_index  # noqa: E402

failures = []


def check(cond, msg):
    print(("  ok: " if cond else "  FAIL: ") + msg)
    if not cond:
        failures.append(msg)


def psnr(a, b):
    m = np.mean((a.astype(np.float64) - b.astype(np.float64)) ** 2)
    return 99.0 if m == 0 else 10 * np.log10(255 ** 2 / m)


def picture(w, h, seed):
    """Something photo-like: smooth light, blurred texture, hard-edged shapes."""
    rng = np.random.default_rng(seed)
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    img = np.zeros((h, w, 3), np.float32)
    for c in range(3):
        img[..., c] = 128 + 90 * np.sin(x / (17 + 9 * c) + c) * np.cos(y / (23 + 5 * c))
    noise = rng.normal(0, 14, (h // 4 + 2, w // 4 + 2, 3)).astype(np.float32)
    img += np.asarray(Image.fromarray(np.clip(noise + 128, 0, 255).astype(np.uint8))
                      .resize((w, h), Image.BICUBIC), np.float32) - 128
    for _ in range(6):
        cx, cy = rng.integers(0, max(1, w)), rng.integers(0, max(1, h))
        r = rng.integers(1, max(2, min(w, h, 120) // 3))
        img[(x - cx) ** 2 + (y - cy) ** 2 < r * r] = rng.integers(0, 256, 3)
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))


def jpeg_bytes(im, **kw):
    b = io.BytesIO()
    im.save(b, "JPEG", **kw)
    return b.getvalue()


def untile565(tex, tw, th, w, h):
    v = tex[swizzle_index(tw, th)].reshape(th, tw).astype(np.int32)
    return np.stack([v >> 11, (v >> 5) & 63, v & 31], -1)


def main():
    tmp = tempfile.mkdtemp(prefix="jpegtest-")
    exe = os.path.join(tmp, "jpeg_harness")
    cc = os.environ.get("CC", "cc")
    subprocess.run([cc, "-O2", "-std=gnu11", "-Wall", "-Wextra", "-I", os.path.join(ROOT, "engine/source"),
                    "-o", exe, os.path.join(ROOT, "tests/jpeg_harness.c"),
                    os.path.join(ROOT, "engine/source/jpeg.c")], check=True)
    path = os.path.join(tmp, "t.jpg")

    def run(*args):
        return subprocess.run([exe, *map(str, args)], capture_output=True, text=True)

    def decode_rgb(data, w, h):
        open(path, "wb").write(data)
        r = run("rgb", path, path + ".rgb")
        if r.returncode:
            return None
        return np.fromfile(path + ".rgb", np.uint8).reshape(h, w, 3)

    print("accuracy against Pillow")
    variants = [("4:4:4 q92", dict(quality=92, subsampling=0), 45, 45),
                ("4:2:2 q75", dict(quality=75, subsampling=1), 33, 45),
                ("4:2:0 q82", dict(quality=82, subsampling=2, optimize=True), 33, 45),
                ("gray q80", dict(quality=80), 45, 45)]
    for w, h in [(427, 240), (400, 225), (33, 17), (17, 33), (1, 1), (8, 8), (250, 141)]:
        src = picture(w, h, w * 1000 + h)
        for name, kw, min_rgb, min_luma in variants:
            im = src.convert("L") if name.startswith("gray") else src
            data = jpeg_bytes(im, **kw)
            got = decode_rgb(data, w, h)
            if got is None:
                check(False, f"{w}x{h} {name} decodes")
                continue
            ref = np.asarray(Image.open(io.BytesIO(data)).convert("RGB"))
            p = psnr(ref, got)
            # Pillow may be built on libjpeg 9, whose chroma upsampling differs
            # from libjpeg-turbo's (which this decoder reproduces exactly), so
            # subsampled images are also judged on luma alone.
            luma = psnr(ref @ [0.299, 0.587, 0.114], got @ [0.299, 0.587, 0.114])
            check(p >= min_rgb and luma >= min_luma,
                  f"{w}x{h} {name}: PSNR {p:.1f} dB (luma {luma:.1f})")

    print("tiled RGB565 output")
    for w, h in [(427, 240), (33, 17), (1, 1), (250, 141)]:
        for name, kw in [("4:2:0", dict(quality=80, subsampling=2)), ("4:4:4", dict(quality=90, subsampling=0)),
                         ("gray", None)]:
            im = picture(w, h, w + h)
            data = jpeg_bytes(im.convert("L"), quality=80) if kw is None else jpeg_bytes(im, **kw)
            rgb = decode_rgb(data, w, h).astype(np.int32)
            for tw, th in [(next_pow2(w), next_pow2(h)), ((w + 7) // 8 * 8, (h + 7) // 8 * 8)]:
                r = run("tiled", path, tw, th, path + ".bin")
                if r.returncode:
                    check(False, f"{w}x{h} {name} into {tw}x{th}: {r.stdout.strip()}")
                    continue
                got = untile565(np.fromfile(path + ".bin", "<u2"), tw, th, w, h)
                pad = np.pad(rgb, ((0, th - h), (0, tw - w), (0, 0)), mode="edge")
                want = np.stack([np.minimum((pad[..., 0] + 4) >> 3, 31), np.minimum((pad[..., 1] + 2) >> 2, 63),
                                 np.minimum((pad[..., 2] + 4) >> 3, 31)], -1)
                diff = np.abs(got - want).max()
                check(diff <= 1, f"{w}x{h} {name} into {tw}x{th}: within {diff} RGB565 step(s), edges padded")

    print("packager")
    im = picture(427, 240, 5).convert("RGBA")
    data, opaque = encode_ctex(im, 427.0, 240.0, jpeg_quality=80)
    fmt, tw, th, w, h = struct.unpack("<HHHHH", data[6:16])
    flags, raw, stored = struct.unpack("<III", data[24:36])
    check(opaque and flags == 2 and fmt == 2 and (tw, th, w, h) == (512, 256, 427, 240) and
          raw == tw * th * 2 and stored == len(data) - 36 and data[36:38] == b"\xff\xd8",
          f"JPEG .ctex header (flags {flags}, format {fmt}, {w}x{h} in {tw}x{th}, {stored} bytes)")
    open(path, "wb").write(data[36:])
    run("tiled", path, tw, th, path + ".bin")
    got = untile565(np.fromfile(path + ".bin", "<u2"), tw, th, w, h)[:h, :w]
    got = np.stack([got[..., 0] * 255 // 31, got[..., 1] * 255 // 63, got[..., 2] * 255 // 31], -1)
    p = psnr(np.asarray(im.convert("RGB")), got)
    check(p > 30, f"decoded texture vs source: {p:.1f} dB")
    sprite = im.copy()
    sprite.putalpha(128)
    data, opaque = encode_ctex(sprite, 427.0, 240.0, jpeg_quality=80)
    check(not opaque and struct.unpack("<I", data[24:28])[0] == 1, "images with alpha stay zlib RGBA8")

    print("robustness")
    src = picture(250, 141, 9)
    open(path, "wb").write(jpeg_bytes(src, quality=80, progressive=True))
    r = run("rgb", path, path + ".rgb")
    check(r.returncode == 1 and "error -3" in r.stdout, "progressive JPEG is refused")
    for name, data in [("4:2:0", jpeg_bytes(src, quality=80, subsampling=2, optimize=True)),
                       ("4:4:4", jpeg_bytes(src, quality=90, subsampling=0)),
                       ("gray", jpeg_bytes(src.convert("L"), quality=70))]:
        open(path, "wb").write(data)
        r = run("fuzz", path, 256, 256, 3000, len(data))
        check(r.returncode == 0, f"{name}: 3000 truncated/corrupted copies, no crash ({r.stdout.strip()})")

    open(path, "wb").write(jpeg_bytes(picture(427, 240, 1), quality=80, subsampling=2, optimize=True))
    r = run("bench", path, 512, 256, 200)
    print(f"  decode 427x240 4:2:0 into 512x256: {float(r.stdout):.2f} ms on this machine")

    print("JPEG tests " + ("passed" if not failures else f"FAILED ({len(failures)})"))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

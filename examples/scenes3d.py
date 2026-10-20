"""Snapshot's places, drawn as stereoscopic depth layers.

Every scene is a stack of planes, each with a depth (positive = behind the
3DS screen, negative = in front) and an optional gentle motion. vnpack packs
each plane as its own texture (vn3ds.json "layers"), and the 3DS draws each
one with its own per-eye offset, so the scene has real background, midground
and foreground. A flattened copy goes in images/ for Ren'Py on a PC.
"""

import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1280, 720


# ---------------------------------------------------------------- helpers

def font(size):
    for p in ("/System/Library/Fonts/Supplemental/Arial.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def gradient(w, h, top, bottom):
    t = np.linspace(0, 1, h)[:, None, None]
    a = np.array(top, np.float32)[None, None, :]
    b = np.array(bottom, np.float32)[None, None, :]
    rows = (a * (1 - t) + b * t).astype(np.uint8)
    return Image.fromarray(np.repeat(rows, w, axis=1), "RGB")


def glow(img, xy, radius, color, strength=0.8):
    """Additive soft light baked into an opaque RGB image."""
    layer = Image.new("RGB", img.size, (0, 0, 0))
    d = ImageDraw.Draw(layer)
    x, y = xy
    for i in range(12, 0, -1):
        r = radius * i / 12
        c = tuple(int(v * strength * (13 - i) / 12) for v in color)
        d.ellipse([x - r, y - r, x + r, y + r], fill=c)
    layer = layer.filter(ImageFilter.GaussianBlur(radius / 6))
    a = np.asarray(img.convert("RGB"), np.int32) + np.asarray(layer, np.int32)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def light(xy, radius, color, alpha=170, size=(W, H)):
    """A transparent layer holding a soft round light (for pulsing glows)."""
    yy, xx = np.mgrid[0:size[1], 0:size[0]]
    dist = np.sqrt((xx - xy[0]) ** 2 + (yy - xy[1]) ** 2)
    a = (np.clip(1 - dist / radius, 0, 1) ** 2 * alpha).astype(np.uint8)
    arr = np.zeros((size[1], size[0], 4), np.uint8)
    arr[..., 0], arr[..., 1], arr[..., 2] = color
    arr[..., 3] = a
    return Image.fromarray(arr, "RGBA")


def stars(d, n, ymax, seed=3, xmax=W, rmax=4):
    rng = np.random.default_rng(seed)
    for _ in range(n):
        x, y = rng.integers(0, xmax), rng.integers(0, ymax)
        r = int(rng.integers(1, rmax))
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 230, 255))


def sky_stars(scene, key, depth, count, size=6, box=(0, 0, W, 420), seed=3, faint=0):
    """Stars that come out a little different every time (vn3ds.json anim
    "stars"): the 3DS scatters `count` twinkling stars of up to `size`
    virtual px in this layer's box, newly seeded at each showing. The baked
    picture is what Ren'Py on a PC shows; two invisible corner pixels pin the
    box. `faint` adds that many dim baked stars behind, the same on both."""
    x0, y0, x1, y1 = box
    if faint:
        img, d = blank()
        rng = np.random.default_rng(seed + 1000)
        for _ in range(faint):
            x, y = int(rng.integers(x0, x1)), int(rng.integers(y0, y1))
            r = int(rng.integers(1, 3))
            d.ellipse([x - r, y - r, x + r, y + r], fill=(235, 235, 255, 110))
        scene.add(key + " faint", img, depth + 0.02)
    img, d = blank()
    rng = np.random.default_rng(seed)
    for _ in range(count):
        x, y = int(rng.integers(x0, x1)), int(rng.integers(y0, y1))
        r = int(rng.integers(1, 4))
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 230, 255))
    img.putpixel((x0, y0), (255, 255, 255, 1))
    img.putpixel((x1 - 1, y1 - 1), (255, 255, 255, 1))
    scene.add(key, img, depth, STARS(count, size))
    return img


def blank():
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


class Scene:
    """A stack of depth planes. The first is opaque; the rest are transparent."""

    def __init__(self, back, depth=1.0, anim=None):
        self.layers = [["back", back.convert("RGBA"), depth, anim]]

    def new(self, key, depth, anim=None):
        img, d = blank()
        self.layers.append([key, img, depth, anim])
        return img, d

    def add(self, key, img, depth, anim=None):
        self.layers.append([key, img.convert("RGBA"), depth, anim])

    def flat(self):
        out = self.layers[0][1].copy()
        for _, img, _, _ in self.layers[1:]:
            out = Image.alpha_composite(out, img)
        return out.convert("RGB")

    def save(self, name, game_dir):
        """Write the flat image and the planes; return the vn3ds.json entry."""
        self.flat().save(os.path.join(game_dir, "images", name + ".png"))
        folder = os.path.join(game_dir, "layers", name)
        os.makedirs(folder, exist_ok=True)
        for fn in os.listdir(folder):
            os.remove(os.path.join(folder, fn))
        entry = []
        for i, (key, img, depth, anim) in enumerate(self.layers):
            rel = f"layers/{name}/{i}-{key}.png"
            img.save(os.path.join(game_dir, rel))
            item = {"file": rel, "depth": depth}
            if anim:
                item["anim"] = anim
            entry.append(item)
        return entry


def rain(seed, n, color=(150, 160, 200, 200), length=26):
    img, d = blank()
    rng = np.random.default_rng(seed)
    for _ in range(n):
        rx, ry = int(rng.integers(0, W)), int(rng.integers(0, H))
        d.line([rx, ry, rx - 6, ry + length], fill=color, width=1)
    return img


def motes(seed, n, color=(255, 240, 210, 150), rmax=4, ymin=0, ymax=H):
    img, d = blank()
    rng = np.random.default_rng(seed)
    for _ in range(n):
        x, y = int(rng.integers(0, W)), int(rng.integers(ymin, ymax))
        r = int(rng.integers(1, rmax))
        d.ellipse([x - r, y - r, x + r, y + r], fill=color)
    return img


SWAY = lambda x=3, y=1, period=7: {"type": "sway", "x": x, "y": y, "period": period}
PULSE = lambda low=0.45, period=4: {"type": "pulse", "a": low, "period": period}
BREATHE = lambda amount=0.012, period=4.5: {"type": "breathe", "a": amount, "period": period}
FALL = lambda dist=H, period=1.2: {"type": "fall", "a": dist, "period": period}
RISE = lambda dist=H, period=12: {"type": "rise", "a": dist, "period": period}
STARS = lambda count=80, size=6: {"type": "stars", "a": count, "b": size}


# ---------------------------------------------------------------- scenes

def room():
    """The tutorial room, later Aron's living room."""
    back = gradient(W, H, (236, 214, 190), (200, 170, 140))
    d = ImageDraw.Draw(back)
    d.rectangle([0, 520, W, H], fill=(120, 84, 60))
    for x in range(0, W, 80):
        d.line([x, 520, x - 60, H], fill=(104, 72, 52), width=3)
    d.rectangle([760, 110, 1120, 400], fill=(250, 245, 235))
    back.paste(gradient(320, 250, (120, 180, 240), (200, 230, 250)), (780, 130))
    s = Scene(back, 1.0)
    clouds, d = s.new("clouds", 1.25, SWAY(6, 0, 18))
    for x, y in [(840, 190), (1010, 160)]:
        for dx, dy, r in [(0, 0, 22), (22, 6, 16), (-22, 7, 15)]:
            d.ellipse([x + dx - r, y + dy - r, x + dx + r, y + dy + r], fill=(255, 255, 255, 230))
    frame, d = s.new("window", 0.95)
    d.rectangle([760, 110, 1120, 400], outline=(250, 245, 235, 255), width=20)
    d.line([940, 130, 940, 380], fill=(250, 245, 235, 255), width=12)
    d.line([780, 255, 1100, 255], fill=(250, 245, 235, 255), width=12)
    shelf, d = s.new("bookshelf", 0.45)
    d.rectangle([90, 150, 420, 520], fill=(110, 70, 45, 255))
    colors = [(200, 60, 60), (60, 120, 200), (230, 180, 60), (80, 160, 90), (150, 80, 170)]
    for row in range(4):
        y = 170 + row * 88
        d.rectangle([105, y + 76, 405, y + 84], fill=(80, 50, 30, 255))
        x, i = 110, row
        while x < 395:
            bw = 18 + (i * 7) % 14
            d.rectangle([x, y + 10 + (i * 5) % 18, x + bw, y + 76], fill=colors[i % 5] + (255,))
            x += bw + 4
            i += 1
    plant, d = s.new("plant", 0.15, SWAY(1, 0, 9))
    d.ellipse([520, 470, 700, 540], fill=(90, 140, 90, 255))
    for k in range(5):
        d.ellipse([540 + k * 28, 420 - (k % 2) * 20, 590 + k * 28, 490], fill=(70, 130, 80, 255))
    s.add("dust", motes(1, 40), -0.3, RISE(H, 40))
    return s


def park():
    back = gradient(W, H, (110, 170, 235), (225, 240, 250))
    s = Scene(back, 1.4)
    clouds, d = s.new("clouds", 1.3, SWAY(12, 0, 25))
    for x, y in [(300, 90), (900, 70), (1150, 140)]:
        for dx, dy, r in [(0, 0, 40), (40, 10, 30), (-40, 12, 28)]:
            d.ellipse([x + dx - r, y + dy - r, x + dx + r, y + dy + r], fill=(255, 255, 255, 255))
    far, d = s.new("far hill", 0.9)
    d.ellipse([-300, 380, 800, 900], fill=(110, 170, 90, 255))
    near, d = s.new("near hill", 0.5)
    d.ellipse([500, 420, 1600, 950], fill=(95, 155, 80, 255))
    d.polygon([(560, H), (720, H), (660, 470), (630, 470)], fill=(220, 200, 150, 255))
    trees, d = s.new("trees", 0.3, SWAY(2, 0, 6))
    for x, y, r in [(150, 330, 90), (1050, 300, 110), (880, 360, 70)]:
        d.rectangle([x - 12, y, x + 12, y + 180], fill=(110, 75, 50, 255))
        d.ellipse([x - r, y - r, x + r, y + r // 2], fill=(60, 130, 70, 255))
    grass, d = s.new("grass", -0.2, SWAY(2, 0, 4))
    rng = np.random.default_rng(2)
    for _ in range(90):
        x = int(rng.integers(0, W))
        d.line([x, H, x + int(rng.integers(-10, 10)), H - int(rng.integers(20, 50))], fill=(70, 140, 70, 255), width=4)
    return s


def bedroom():
    back = gradient(W, H, (90, 80, 120), (170, 130, 130))
    d = ImageDraw.Draw(back)
    d.rectangle([0, 540, W, H], fill=(80, 60, 70))
    d.rectangle([140, 90, 520, 430], fill=(60, 50, 70))
    back.paste(gradient(340, 300, (255, 170, 120), (255, 225, 170)), (160, 110))
    d.line([330, 110, 330, 410], fill=(60, 50, 70), width=10)
    d.line([160, 260, 500, 260], fill=(60, 50, 70), width=10)
    s = Scene(back, 1.0)
    s.add("dawn", light((330, 330), 330, (255, 180, 110), 120), 0.9, PULSE(0.6, 6))
    bed, d = s.new("bed", 0.35)
    d.rounded_rectangle([620, 430, 1240, 640], 30, fill=(200, 200, 225, 255))
    d.rounded_rectangle([600, 360, 660, 650], 18, fill=(110, 80, 70, 255))
    d.rounded_rectangle([660, 400, 820, 470], 25, fill=(245, 245, 255, 255))
    d.rounded_rectangle([760, 470, 1240, 600], 30, fill=(120, 140, 200, 255))
    stand, d = s.new("clock", 0.05)
    d.rectangle([1150, 330, 1260, 430], fill=(110, 80, 70, 255))
    d.rounded_rectangle([1170, 300, 1240, 335], 6, fill=(30, 30, 40, 255))
    d.text((1178, 302), "7:07", fill=(255, 90, 90, 255), font=font(26))
    s.add("dust", motes(3, 50, (255, 230, 200, 140)), -0.25, RISE(H, 30))
    return s


def kitchen():
    back = gradient(W, H, (250, 236, 210), (230, 210, 180))
    d = ImageDraw.Draw(back)
    for x in range(0, W, 64):
        for y in range(150, 330, 64):
            d.rectangle([x + 2, y + 2, x + 62, y + 62], outline=(225, 210, 190), width=2)
    d.rectangle([130, 60, 430, 300], fill=(255, 255, 255))
    back.paste(gradient(270, 210, (140, 190, 240), (210, 235, 250)), (145, 75))
    d.line([145, 150, 415, 180], fill=(40, 40, 40), width=3)
    s = Scene(back, 1.0)
    bird, d = s.new("bird", 1.05)   # perfectly still; that's the point
    d.ellipse([285, 150, 315, 170], fill=(50, 50, 60, 255))
    d.polygon([(312, 158), (326, 162), (312, 166)], fill=(230, 160, 40, 255))
    counter, d = s.new("counter", 0.4)
    d.rectangle([0, 330, W, 400], fill=(150, 110, 80, 255))
    d.rectangle([0, 400, W, H], fill=(190, 150, 110, 255))
    for x in range(40, W, 230):
        d.rectangle([x, 420, x + 200, 700], outline=(160, 120, 85, 255), width=4)
        d.ellipse([x + 92, 540, x + 108, 556], fill=(120, 90, 60, 255))
    machine, d = s.new("coffee", 0.25)
    d.rounded_rectangle([880, 190, 1010, 335], 12, fill=(60, 60, 70, 255))
    d.rectangle([915, 290, 975, 335], fill=(30, 30, 35, 255))
    d.ellipse([930, 205, 960, 235], fill=(120, 220, 255, 255))
    steam, d = s.new("steam", 0.15, RISE(140, 5))
    for k in range(4):
        d.arc([925 + k * 6, 120 - k * 30, 965 + k * 6, 170 - k * 30], 100, 260, fill=(255, 255, 255, 140), width=4)
    s.add("indicator", light((945, 220), 50, (120, 220, 255), 160), 0.24, PULSE(0.3, 2))
    return s


def street():
    back = gradient(W, H, (150, 180, 220), (230, 220, 210))
    s = Scene(back, 1.4)
    town, d = s.new("buildings", 0.8)
    xs = 0
    rng = np.random.default_rng(11)
    while xs < W:
        bw, bh = int(rng.integers(140, 260)), int(rng.integers(220, 420))
        col = tuple(int(c) for c in rng.integers(120, 200, 3)) + (255,)
        d.rectangle([xs, 520 - bh, xs + bw, 520], fill=col)
        for wx in range(xs + 20, xs + bw - 30, 50):
            for wy in range(520 - bh + 30, 500, 60):
                d.rectangle([wx, wy, wx + 26, wy + 34], fill=(240, 240, 220, 255))
        xs += bw + 6
    road, d = s.new("road", 0.35)
    d.rectangle([0, 520, W, H], fill=(90, 90, 100, 255))
    for x in range(0, W, 160):
        d.rectangle([x + 40, 610, x + 120, 622], fill=(230, 230, 230, 255))
    wire, d = s.new("wire", 0.15)   # three identical birds, evenly spaced, never moving
    d.line([0, 230, W, 260], fill=(40, 40, 40, 255), width=3)
    for bx in (300, 340, 380):
        d.ellipse([bx, 222, bx + 30, 242], fill=(50, 50, 60, 255))
    return s


def desk():
    back = gradient(W, H, (20, 22, 40), (40, 35, 55))
    s = Scene(back, 1.0)
    notes, d = s.new("notes", 0.8)
    for i in range(14):
        x, y = 60 + (i % 7) * 120, 70 + (i // 7) * 130
        d.rectangle([x, y, x + 100, y + 100], fill=[(255, 240, 120, 255), (255, 180, 200, 255), (170, 230, 255, 255)][i % 3])
    strings, d = s.new("strings", 0.6)
    for i in range(14):
        x, y = 60 + (i % 7) * 120, 70 + (i // 7) * 130
        d.line([x + 50, y + 100, 640 + (i % 5) * 40, 360], fill=(200, 40, 40, 255), width=2)
    table, d = s.new("table", 0.3)
    d.rectangle([0, 470, W, H], fill=(70, 50, 40, 255))
    s.add("lamplight", light((980, 420), 360, (255, 200, 120), 120), 0.28, PULSE(0.8, 5))
    lamp, d = s.new("lamp", 0.2)
    d.polygon([(930, 250), (1030, 250), (1060, 330), (900, 330)], fill=(240, 200, 120, 255))
    d.line([980, 330, 980, 470], fill=(60, 60, 60, 255), width=8)
    book, d = s.new("notebook", -0.2)
    d.polygon([(300, 520), (760, 500), (800, 690), (280, 700)], fill=(245, 240, 225, 255))
    f = font(30)
    for i, line in enumerate(["1. repeats when unobserved?", "2. the bird: 7:07 every day",
                              "3. M. knew the dream", "4. ???"]):
        d.text((330, 525 + i * 40), line, fill=(40, 40, 80, 255), font=f)
    return s


def ward():
    back = gradient(W, H, (215, 235, 232), (190, 215, 212))
    d = ImageDraw.Draw(back)
    d.rectangle([840, 90, 1160, 360], fill=(240, 250, 250))
    back.paste(gradient(290, 240, (200, 210, 225), (230, 235, 240)), (855, 105))
    s = Scene(back, 1.0)
    bars, d = s.new("bars", 0.9)
    for x in range(880, 1150, 45):
        d.line([x, 105, x, 345], fill=(150, 160, 170, 255), width=6)
    floor, d = s.new("floor", 0.6)
    d.rectangle([0, 520, W, H], fill=(170, 190, 195, 255))
    for x in range(0, W, 120):
        d.line([x, 520, x + 40, H], fill=(160, 180, 185, 255), width=2)
    bed, d = s.new("bed", 0.3)
    d.rounded_rectangle([90, 400, 640, 600], 20, fill=(250, 250, 250, 255))
    d.rectangle([90, 380, 120, 640], fill=(160, 170, 180, 255))
    d.rectangle([610, 380, 640, 640], fill=(160, 170, 180, 255))
    mon, d = s.new("monitor", 0.05)
    d.rectangle([700, 330, 760, 560], fill=(200, 205, 210, 255))
    d.rounded_rectangle([680, 250, 780, 330], 10, fill=(60, 70, 80, 255))
    trace, d = s.new("heartbeat", 0.04, PULSE(0.2, 1.1))
    d.line([690, 300, 715, 300, 725, 270, 740, 320, 750, 300, 770, 300], fill=(90, 255, 140, 255), width=3)
    s.add("fluorescent", light((640, 0), 600, (230, 255, 255), 60), -0.1, PULSE(0.85, 0.35))
    return s


def rooftop():
    back = gradient(W, H, (10, 12, 35), (45, 40, 90))
    s = Scene(back, 1.5)
    sky_stars(s, "stars", 1.48, 110, 6, (0, 0, W, 430), seed=5, faint=90)
    s.add("moonglow", light((1020, 140), 160, (210, 210, 240), 120), 1.3, PULSE(0.7, 8))
    moon, d = s.new("moon", 1.3)
    d.ellipse([985, 105, 1055, 175], fill=(240, 240, 250, 255))
    city, d = s.new("city", 0.8)
    rng = np.random.default_rng(4)
    x = 0
    while x < W:
        bw, bh = int(rng.integers(60, 150)), int(rng.integers(80, 260))
        d.rectangle([x, 560 - bh, x + bw, 560], fill=(20, 20, 40, 255))
        for wx in range(x + 10, x + bw - 10, 22):
            for wy in range(560 - bh + 12, 550, 30):
                if rng.random() < 0.35:
                    d.rectangle([wx, wy, wx + 8, wy + 12], fill=(255, 220, 140, 255))
        x += bw
    roof, d = s.new("roof", -0.15)
    d.rectangle([0, 560, W, H], fill=(55, 55, 70, 255))
    d.rectangle([0, 545, W, 565], fill=(80, 80, 95, 255))
    return s


def command():
    back = gradient(W, H, (255, 250, 235), (225, 210, 170))
    d = ImageDraw.Draw(back)
    for x in range(-200, W + 200, 90):
        d.line([W // 2, 300, x, H], fill=(230, 210, 160), width=2)
    s = Scene(glow(back, (W // 2, 330), 400, (60, 50, 20), 0.6), 1.2)
    floor, d = s.new("floor", 0.6)
    d.rectangle([0, 560, W, H], fill=(235, 220, 180, 255))
    screens, d = s.new("worlds", 0.45)
    for i in range(6):
        for j in range(3):
            x, y = 120 + i * 180, 60 + j * 120
            d.rounded_rectangle([x, y, x + 150, y + 95], 8, fill=(250, 245, 230, 255), outline=(210, 180, 100, 255), width=3)
            c = [(120, 170, 230), (110, 190, 140), (200, 140, 120)][(i + j) % 3] + (255,)
            d.ellipse([x + 50, y + 22, x + 100, y + 72], fill=c)
    alarm, d = s.new("alarm", 0.4, PULSE(0.15, 1.4))
    x, y = 120 + 3 * 180, 60 + 120
    d.rounded_rectangle([x - 4, y - 4, x + 154, y + 99], 10, outline=(220, 40, 40, 255), width=6)
    s.add("radiance", light((W // 2, 300), 520, (255, 240, 200), 70), -0.2, PULSE(0.6, 7))
    return s


def purgatorium():
    back = gradient(W, H, (70, 60, 110), (140, 120, 160))
    s = Scene(back, 1.2)
    lamps, d = s.new("lanterns", 0.7, SWAY(0, 6, 6))
    for x, y in [(200, 150), (640, 90), (1080, 170)]:
        d.ellipse([x - 20, y - 20, x + 20, y + 20], fill=(255, 230, 160, 255))
    for i, (x, y) in enumerate([(200, 150), (640, 90), (1080, 170)]):
        s.add(f"glow{i}", light((x, y), 130, (255, 210, 140), 120), 0.72, PULSE(0.5, 3 + i))
    mist, d = s.new("mist", 0.5, SWAY(8, 0, 14))
    for i in range(7):
        y = 360 + i * 22
        d.ellipse([-200 + i * 30, y, W + 200 - i * 50, y + 120], fill=(110 + i * 6, 95 + i * 5, 140 + i * 4, 200))
    table, d = s.new("table", 0.2)
    d.rounded_rectangle([200, 470, 1080, 520], 10, fill=(90, 70, 90, 255))
    for x in range(260, 1040, 120):
        d.rounded_rectangle([x, 440, x + 50, 470], 6, fill=(230, 230, 240, 255))
        d.ellipse([x + 8, 420, x + 42, 448], fill=(250, 250, 255, 255))
    d.text((520, 600), "SHIFT 7 - KITCHEN TALK", fill=(200, 190, 230, 255), font=font(30))
    front, d = s.new("front mist", -0.25, SWAY(14, 0, 11))
    for i in range(3):
        d.ellipse([-100 + i * 420, 600, 400 + i * 420, 760], fill=(170, 150, 200, 110))
    return s


def council():
    back = gradient(W, H, (25, 5, 15), (70, 15, 30))
    d = ImageDraw.Draw(back)
    for x in range(100, W, 180):
        d.rectangle([x, 0, x + 40, H], fill=(40, 10, 20))
    s = Scene(back, 1.2)
    s.add("orbglow", light((W // 2, 260), 280, (100, 140, 230), 150), 0.75, PULSE(0.55, 5))
    orb, d = s.new("planet", 0.7, BREATHE(0.02, 6))
    d.ellipse([W // 2 - 110, 150, W // 2 + 110, 370], fill=(60, 110, 190, 255))
    d.ellipse([W // 2 - 60, 190, W // 2 + 20, 260], fill=(80, 150, 90, 255))
    d.ellipse([W // 2 + 10, 270, W // 2 + 80, 330], fill=(80, 150, 90, 255))
    tethers, d = s.new("tethers", 0.35, PULSE(0.4, 2.2))
    for k in range(5):
        d.line([W // 2, 260, 140 + k * 250, 620], fill=(190, 40, 70, 255), width=4)
    thrones, d = s.new("thrones", -0.1)
    for k in range(5):
        x = 140 + k * 250
        d.polygon([(x - 60, 680), (x + 60, 680), (x + 45, 560), (x, 520), (x - 45, 560)], fill=(15, 0, 8, 255))
    d.rectangle([0, 680, W, H], fill=(20, 0, 8, 255))
    return s


def watch():
    back = gradient(W, H, (40, 28, 30), (70, 45, 40))
    s = Scene(back, 1.0)
    win, d = s.new("round window", 0.85)
    d.ellipse([470, 120, 810, 460], fill=(25, 20, 30, 255))
    d.ellipse([490, 140, 790, 440], fill=(15, 18, 40, 255))
    sky_stars(s, "stars", 0.86, 16, 5, (536, 186, 744, 394), seed=9)
    room, d = s.new("aron's window", 0.9)
    d.rectangle([600, 300, 680, 370], fill=(255, 210, 130, 255))
    d.line([640, 300, 640, 370], fill=(80, 60, 40, 255), width=3)
    s.add("his light", light((640, 336), 110, (255, 200, 120), 120), 0.88, PULSE(0.5, 3.5))
    beams, d = s.new("beams", 0.5)
    d.polygon([(0, 0), (W // 2, -120), (W, 0), (W, 80), (W // 2, -40), (0, 80)], fill=(30, 20, 20, 255))
    for x in range(0, W, 140):
        d.line([x, 0, W // 2, 200], fill=(55, 38, 34, 255), width=10)
    floor, d = s.new("floor", 0.25)
    d.rectangle([0, 560, W, H], fill=(60, 40, 32, 255))
    boxes, d = s.new("boxes", -0.1)
    for x, y in [(240, 520), (1020, 540)]:
        d.rectangle([x - 70, y, x + 70, y + 60], fill=(110, 75, 50, 255))
        d.line([x - 70, y + 20, x + 70, y + 20], fill=(80, 55, 40, 255), width=3)
    s.add("embers", motes(12, 30, (255, 190, 120, 170), 3), -0.3, RISE(H, 18))
    return s


def cafe():
    back = gradient(W, H, (120, 80, 60), (170, 120, 90))
    d = ImageDraw.Draw(back)
    d.rectangle([60, 160, 560, 400], fill=(60, 90, 110))
    d.text((90, 180), "THE SAME CAFE", fill=(255, 230, 180), font=font(40))
    s = Scene(back, 1.0)
    lamps, d = s.new("lamps", 0.6, SWAY(2, 0, 5))
    for x in range(0, W, 200):
        d.line([x + 100, 0, x + 100, 70], fill=(40, 30, 25, 255), width=3)
        d.ellipse([x + 80, 70, x + 120, 110], fill=(255, 220, 150, 255))
    for i, x in enumerate(range(0, W, 200)):
        s.add(f"lampglow{i}", light((x + 100, 95), 90, (255, 210, 140), 110), 0.62, PULSE(0.6, 3 + i % 3))
    floor, d = s.new("floor", 0.4)
    d.rectangle([0, 440, W, H], fill=(90, 60, 45, 255))
    tables, d = s.new("tables", 0.15)
    for x in (180, 640, 1100):
        d.ellipse([x - 120, 470, x + 120, 520], fill=(200, 170, 140, 255))
        d.rectangle([x - 10, 510, x + 10, 680], fill=(60, 45, 35, 255))
        d.rounded_rectangle([x - 30, 440, x + 10, 475], 6, fill=(250, 250, 250, 255))
    s.add("steam", motes(14, 18, (255, 255, 255, 110), 4, 300, 460), 0.1, RISE(200, 6))
    return s


def night():
    back = gradient(W, H, (15, 20, 40), (40, 45, 70))
    s = Scene(back, 1.2)
    town, d = s.new("buildings", 0.75)
    x = 0
    rng = np.random.default_rng(21)
    while x < W:
        bw, bh = int(rng.integers(120, 240)), int(rng.integers(250, 450))
        d.rectangle([x, 540 - bh, x + bw, 540], fill=(30, 30, 50, 255))
        for wx in range(x + 15, x + bw - 20, 40):
            for wy in range(540 - bh + 20, 520, 50):
                if rng.random() < 0.3:
                    d.rectangle([wx, wy, wx + 18, wy + 26], fill=(240, 200, 120, 255))
        x += bw + 8
    s.add("far rain", rain(22, 220, (120, 130, 180, 150), 18), 0.6, FALL(H, 1.6))
    street, d = s.new("street", 0.35)
    d.rectangle([0, 540, W, H], fill=(35, 35, 45, 255))
    for k in range(6):
        d.ellipse([100 + k * 200, 600, 220 + k * 200, 620], fill=(60, 60, 90, 255))
    for i, lx in enumerate((250, 900)):
        s.add(f"lampglow{i}", light((lx, 250), 200, (255, 200, 110), 140), 0.3, PULSE(0.75, 3 + i))
    poles, d = s.new("lamps", 0.28)
    for lx in (250, 900):
        d.rectangle([lx - 5, 250, lx + 5, 560], fill=(20, 20, 25, 255))
        d.ellipse([lx - 18, 235, lx + 18, 265], fill=(255, 230, 160, 255))
    s.add("near rain", rain(23, 140, (170, 180, 220, 220), 34), -0.3, FALL(H, 0.9))
    return s


def mirror():
    back = gradient(W, H, (200, 215, 220), (170, 185, 195))
    d = ImageDraw.Draw(back)
    for x in range(0, W, 80):
        for y in range(0, 420, 80):
            d.rectangle([x + 1, y + 1, x + 79, y + 79], outline=(185, 200, 205), width=2)
    s = Scene(back, 1.0)
    frame, d = s.new("mirror", 0.55)
    d.rounded_rectangle([400, 60, 880, 440], 20, fill=(150, 165, 175, 255))
    d.rounded_rectangle([415, 75, 865, 425], 16, fill=(185, 205, 215, 255))
    for k in range(4):   # the reflection that isn't quite in sync
        ring, rd = s.new(f"echo{k}", 0.5 - k * 0.05, SWAY(3 + k * 2, 1, 2.5 + k))
        o = k * 9
        rd.ellipse([560 + o, 140 + o, 720 + o, 330 + o], outline=(120, 130, 140, 255), width=2)
    sink, d = s.new("sink", -0.15)
    d.rectangle([0, 470, W, H], fill=(230, 230, 235, 255))
    d.ellipse([500, 520, 780, 600], fill=(250, 250, 255, 255))
    d.line([0, 470, W, 470], fill=(160, 170, 180, 255), width=6)
    return s


def clinic():
    back = gradient(W, H, (230, 225, 215), (205, 200, 190))
    d = ImageDraw.Draw(back)
    d.rectangle([850, 120, 1130, 300], fill=(250, 250, 245))
    d.text((870, 140), "breathe in 4", fill=(90, 110, 130), font=font(30))
    d.text((870, 190), "hold 4", fill=(90, 110, 130), font=font(30))
    d.text((870, 240), "breathe out 6", fill=(90, 110, 130), font=font(30))
    s = Scene(back, 1.0)
    shelf, d = s.new("shelf", 0.6)
    d.rectangle([80, 120, 420, 430], fill=(120, 90, 60, 255))
    for row in range(3):
        d.rectangle([95, 210 + row * 100, 405, 218 + row * 100], fill=(90, 65, 45, 255))
        for k in range(9):
            d.rectangle([105 + k * 32, 140 + row * 100, 128 + k * 32, 208 + row * 100],
                        fill=[(70, 90, 140, 255), (140, 60, 60, 255), (200, 190, 160, 255)][(k + row) % 3])
    floor, d = s.new("floor", 0.4)
    d.rectangle([0, 500, W, H], fill=(140, 120, 100, 255))
    table, d = s.new("desk", 0.15)
    d.rounded_rectangle([600, 380, 1150, 440], 8, fill=(110, 80, 55, 255))
    d.rectangle([640, 440, 670, 620], fill=(90, 65, 45, 255))
    d.rectangle([1080, 440, 1110, 620], fill=(90, 65, 45, 255))
    plant, d = s.new("plant", -0.1, BREATHE(0.02, 4))   # breathes in 4, out 6-ish
    d.ellipse([480, 300, 560, 380], fill=(90, 150, 90, 255))
    d.rectangle([500, 370, 540, 430], fill=(160, 100, 70, 255))
    return s


def earth():
    back = gradient(W, H, (5, 5, 20), (30, 20, 60))
    s = Scene(back, 1.5)
    sky_stars(s, "stars", 1.48, 170, 7, (0, 0, W, H), seed=17, faint=120)
    s.add("atmosphere", light((640, 900), 620, (90, 140, 230), 200), 0.95, PULSE(0.75, 7))
    planet, d = s.new("earth", 0.9, BREATHE(0.006, 9))
    d.ellipse([140, 420, 1140, 1420], fill=(40, 90, 170, 255))
    d.ellipse([360, 470, 640, 640], fill=(70, 140, 80, 255))
    d.ellipse([760, 520, 980, 700], fill=(70, 140, 80, 255))
    cage, d = s.new("cage", 0.3, PULSE(0.25, 4))
    for k in range(9):
        d.line([140 + k * 125, 420, 640, 40], fill=(180, 160, 255, 255), width=1)
    d.ellipse([600, 10, 680, 70], outline=(200, 180, 255, 255), width=3)
    return s


def blueprint():
    back = gradient(W, H, (15, 40, 80), (25, 60, 110))
    d = ImageDraw.Draw(back)
    for x in range(0, W, 40):
        d.line([x, 0, x, H], fill=(40, 80, 130), width=1)
    for y in range(0, H, 40):
        d.line([0, y, W, y], fill=(40, 80, 130), width=1)
    s = Scene(back, 1.0)
    links, d = s.new("links", 0.4, PULSE(0.5, 3))
    for a, b in [((300, 300), (640, 220)), ((640, 220), (950, 330)), ((300, 300), (520, 520)),
                 ((520, 520), (820, 560)), ((950, 330), (820, 560))]:
        d.line([a, b], fill=(255, 220, 120, 255), width=2)
    for i, (x, y, r) in enumerate([(300, 300, 110), (640, 220, 80), (950, 330, 130), (520, 520, 70), (820, 560, 60)]):
        w_img, wd = s.new(f"world{i}", 0.2 - i * 0.12, SWAY(0, 4, 5 + i))
        wd.ellipse([x - r, y - r, x + r, y + r], outline=(200, 230, 255, 255), width=3)
        wd.text((x - 30, y + r + 8), f"W-{i + 1}", fill=(200, 230, 255, 255), font=font(24))
    return s


def office():
    back = gradient(W, H, (246, 244, 238), (226, 222, 214))
    d = ImageDraw.Draw(back)
    d.text((90, 90), "less, but better.", fill=(110, 110, 110), font=font(34))
    s = Scene(back, 0.9)
    view, d = s.new("view", 1.3)
    view.paste(gradient(560, 390, (160, 205, 245), (225, 240, 245)), (670, 70))
    d.ellipse([600, 330, 1300, 620], fill=(150, 200, 140, 255))
    d.rectangle([600, 470, 1300, 620], fill=(0, 0, 0, 0))
    vclouds, d = s.new("clouds", 1.25, SWAY(10, 0, 30))
    for x, y in [(760, 140), (1080, 190)]:
        for dx, dy, r in [(0, 0, 26), (26, 6, 18), (-26, 8, 18)]:
            d.ellipse([x + dx - r, y + dy - r, x + dx + r, y + dy + r], fill=(255, 255, 255, 240))
    glass, d = s.new("glass wall", 0.8)
    d.rectangle([660, 60, 1240, 470], outline=(250, 250, 250, 255), width=12)
    for x in range(670, 1240, 140):
        d.line([x, 70, x, 460], fill=(235, 235, 235, 255), width=6)
    floor, d = s.new("floor", 0.5)
    d.rectangle([0, 470, W, H], fill=(205, 198, 186, 255))
    table, d = s.new("table", 0.15)
    d.rectangle([80, 440, 600, 460], fill=(60, 60, 60, 255))
    for x in (110, 570):
        d.rectangle([x, 460, x + 10, 640], fill=(60, 60, 60, 255))
    model, d = s.new("model world", 0.05, BREATHE(0.03, 5))
    d.ellipse([260, 330, 420, 440], outline=(240, 120, 40, 255), width=5)
    d.ellipse([300, 360, 380, 410], fill=(240, 120, 40, 255))
    lamp, d = s.new("lamp", -0.1)
    d.line([340, 0, 340, 200], fill=(70, 70, 70, 255), width=3)
    d.chord([290, 190, 390, 250], 180, 360, fill=(70, 70, 70, 255))
    s.add("lamplight", light((340, 260), 180, (255, 230, 170), 90), -0.12, PULSE(0.8, 6))
    return s


def goldlight():
    back = gradient(W, H, (40, 25, 5), (120, 80, 20))
    s = Scene(back, 1.2)
    beams, d = s.new("beams", 0.7, PULSE(0.55, 3.5))
    for k in range(-8, 9):
        x = W // 2 + k * 90
        d.polygon([(W // 2 - 8, -10), (W // 2 + 8, -10), (x + 30, H), (x - 30, H)],
                  fill=(160 + abs(k) * 4, 120 + abs(k) * 3, 40, 160))
    s.layers[-1][1] = s.layers[-1][1].filter(ImageFilter.GaussianBlur(6))
    s.add("source", light((W // 2, 120), 380, (255, 220, 140), 200), 0.75, PULSE(0.7, 5))
    forms, d = s.new("forms", 0.0, BREATHE(0.05, 3))
    for i in range(5):
        x = 240 + i * 200
        d.polygon([(x, 560), (x + 40, 480 - i * 10), (x + 80, 560), (x + 40, 620)], fill=(255, 225, 140, 255))
    s.add("motes far", motes(31, 90, (255, 235, 170, 200), 4), 0.4, RISE(H, 14))
    s.add("motes near", motes(32, 50, (255, 245, 200, 230), 6), -0.35, RISE(H, 9))
    return s


def worlds():
    back = gradient(W, H, (10, 10, 25), (30, 25, 55))
    s = Scene(back, 1.6)
    rng = np.random.default_rng(41)
    for depth in range(4, 0, -1):
        lay, d = s.new(f"lattice{depth}", -0.3 + depth * 0.4, SWAY(4 * depth, 2, 10 + depth * 3))
        size = 40 * depth
        for row in range(0, H // size + 1):
            for col in range(0, W // size + 1):
                if rng.random() < 0.55:
                    continue
                x, y = col * size + (row % 2) * size // 2, row * size
                c = [(120, 160, 230), (230, 160, 110), (140, 210, 150), (220, 200, 120)][int(rng.integers(0, 4))]
                c = tuple(int(v * (0.35 + 0.15 * depth)) for v in c) + (255,)
                d.rectangle([x + 3, y + 3, x + size - 3, y + size - 3], outline=c, width=2)
                if depth >= 3:
                    d.ellipse([x + size // 2 - 4, y + size // 2 - 4, x + size // 2 + 4, y + size // 2 + 4], fill=c)
    return s


def static_noise():
    rng = np.random.default_rng(99)
    a = rng.integers(0, 255, (H // 4, W // 4), dtype=np.uint8)
    back = Image.fromarray(a, "L").resize((W, H), Image.NEAREST).convert("RGB")
    s = Scene(back, 0.6, SWAY(6, 3, 0.15))
    lines, d = s.new("scanlines", -0.25, SWAY(0, 4, 0.2))
    for y in range(0, H, 6):
        d.line([0, y, W, y], fill=(0, 0, 0, 200), width=2)
    return s


def together(night=False):
    """Aron and Mira under the sheets: bare shoulders, faces close, nothing
    more shown."""
    base = gradient(W, H, (25, 30, 60), (55, 50, 85)) if night else gradient(W, H, (250, 200, 160), (230, 170, 140))
    s = Scene(base, 1.0)
    if night:
        s.add("rain", rain(51, 140, (110, 120, 170, 200), 18), 0.95, FALL(H, 1.8))
        s.add("streetlight", light((1180, 120), 220, (255, 200, 120), 110), 0.9, PULSE(0.7, 6))
    else:
        s.add("sunlight", light((180, 80), 360, (255, 210, 150), 150), 0.9, PULSE(0.75, 7))
    head, d = s.new("headboard", 0.7)
    d.rounded_rectangle([80, 40, 1200, 230], 40, fill=((40, 35, 55) if night else (90, 65, 60)) + (255,))
    pil, d = s.new("pillows", 0.45)
    pillow = ((150, 155, 185) if night else (245, 240, 235)) + (255,)
    d.rounded_rectangle([170, 150, 620, 330], 70, fill=pillow)
    d.rounded_rectangle([660, 150, 1110, 330], 70, fill=pillow)
    mskin = ((190, 175, 190) if night else (255, 225, 205)) + (255,)
    askin = ((170, 150, 150) if night else (230, 190, 160)) + (255,)
    hair_r = ((130, 50, 45) if night else (200, 70, 35)) + (255,)
    hair_a = (40, 40, 50, 255)
    mira, d = s.new("mira", 0.2, BREATHE(0.008, 4.2))
    d.ellipse([300, 140, 610, 360], fill=hair_r)
    d.ellipse([360, 180, 560, 360], fill=mskin)
    d.ellipse([330, 330, 620, 470], fill=mskin)
    for dx, dy in [(410, 280), (424, 290), (402, 296), (500, 284), (512, 294), (494, 300)]:
        d.ellipse([dx - 3, dy - 3, dx + 3, dy + 3], fill=((140, 100, 100) if night else (200, 120, 90)) + (255,))
    for ex, ey in [(430, 255), (500, 255)]:
        d.arc([ex - 16, ey - 6, ex + 16, ey + 12], 20, 160, fill=(60, 40, 40, 255), width=4)
    d.arc([440, 300, 510, 330], 20, 160, fill=(150, 60, 70, 255), width=4)
    aron, d = s.new("aron", 0.12, BREATHE(0.008, 5.1))
    d.chord([640, 150, 900, 300], 180, 360, fill=hair_a)
    d.ellipse([650, 180, 890, 380], fill=askin)
    d.ellipse([620, 340, 960, 490], fill=askin)
    for ex, ey in [(720, 270), (800, 270)]:
        d.arc([ex - 16, ey - 6, ex + 16, ey + 12], 20, 160, fill=(60, 40, 40, 255), width=4)
    d.arc([730, 315, 800, 345], 20, 160, fill=(150, 60, 70, 255), width=4)
    d.ellipse([560, 380, 650, 430], fill=askin)   # his hand on her shoulder
    sheet_col = ((95, 105, 150) if night else (235, 235, 245))
    sheet, d = s.new("sheet", -0.2)
    pts = [(60, 470)] + [(x, 455 + 18 * math.sin(x / 70)) for x in range(60, 1240, 30)] + [(1240, H), (60, H)]
    d.polygon(pts, fill=sheet_col + (255,))
    for x in range(120, 1200, 140):
        d.arc([x, 480, x + 180, 640], 200, 320, fill=tuple(max(0, v - 25) for v in sheet_col) + (255,), width=4)
    return s


SCENES = {
    "bg room": room, "bg park": park, "bg bedroom": bedroom, "bg kitchen": kitchen,
    "bg street": street, "bg desk": desk, "bg ward": ward, "bg rooftop": rooftop,
    "bg command": command, "bg purgatorium": purgatorium, "bg council": council,
    "bg watch": watch, "bg cafe": cafe, "bg night": night, "bg mirror": mirror,
    "bg clinic": clinic, "bg earth": earth, "bg blueprint": blueprint, "bg office": office,
    "bg goldlight": goldlight, "bg worlds": worlds, "cg static": static_noise,
    "cg together morning": together, "cg together night": lambda: together(True),
}


def build_all(game_dir):
    """Draw every scene; return the vn3ds.json "layers" mapping."""
    img_dir = os.path.join(game_dir, "images")
    for fn in os.listdir(img_dir):   # drop flat images from older versions
        base = os.path.splitext(fn)[0]
        if base in SCENES and not fn.endswith(".png"):
            os.remove(os.path.join(img_dir, fn))
    layers = {}
    for k, (name, fn) in enumerate(SCENES.items()):
        scene = fn()
        moving = sum(1 for layer in scene.layers if layer[3])
        if moving < 2 and not name.startswith("cg static"):
            # every place breathes a little: drifting dust in front, a slow sway behind
            scene.add("dust", motes(200 + k, 28, (255, 245, 225, 120), 3), -0.3, RISE(H, 34))
            for layer in scene.layers[1:]:
                if not layer[3] and 0.2 < layer[2] < 0.9:
                    layer[3] = SWAY(1.5, 0.8, 11 + k % 5)
                    break
        layers[name] = scene.save(name, game_dir)
    return layers


# ---------------------------------------------------------------- more places
# Variants of familiar places (time of day, weather) and the rest of the map.

def recolor(scene, mul, add=(0, 0, 0)):
    """Tint every plane: multiply RGB by `mul` and add `add` (alpha untouched)."""
    for layer in scene.layers:
        a = np.asarray(layer[1]).astype(np.float32)
        a[..., :3] = np.clip(a[..., :3] * np.array(mul, np.float32) + np.array(add, np.float32), 0, 255)
        layer[1] = Image.fromarray(a.astype(np.uint8), "RGBA")
    return scene


def night_of(fn, moon=(1050, 110), lights=()):
    s = recolor(fn(), (0.35, 0.4, 0.65), (5, 5, 20))
    s.add("moonlight", light(moon, 260, (170, 190, 255), 90), 1.0, PULSE(0.7, 9))
    for i, (xy, depth) in enumerate(lights):
        s.add(f"light{i}", light(xy, 150, (255, 200, 120), 150), depth, PULSE(0.75, 4 + i))
    return s


def bedroom_night():
    return night_of(bedroom, (330, 260), [((1205, 318), 0.04)])


def kitchen_night():
    s = night_of(kitchen, (280, 140), [((945, 220), 0.24)])
    return s


def room_night():
    return night_of(room, (940, 255), [((610, 450), 0.1)])


def street_rain():
    s = recolor(street(), (0.7, 0.75, 0.85))
    s.add("rain far", rain(61, 200, (170, 180, 210, 160), 18), 0.6, FALL(H, 1.5))
    s.add("rain near", rain(62, 120, (200, 210, 235, 210), 34), -0.3, FALL(H, 0.85))
    return s


def street_dusk():
    s = recolor(street(), (1.0, 0.7, 0.6), (20, 0, 10))
    s.add("sunset", light((640, 520), 700, (255, 150, 90), 110), 1.1, PULSE(0.8, 10))
    return s


def street_snow():
    s = recolor(street(), (0.85, 0.9, 1.0), (30, 30, 40))
    s.add("snow far", motes(63, 160, (255, 255, 255, 200), 3), 0.6, FALL(H, 9))
    s.add("snow near", motes(64, 70, (255, 255, 255, 240), 6), -0.3, FALL(H, 6))
    return s


def park_night():
    s = night_of(park, (1000, 90), [((150, 420), 0.3), ((1050, 400), 0.3)])
    star_layer = Scene(Image.new("RGB", (W, H)))
    sky_stars(star_layer, "stars", 1.38, 80, 6, (0, 0, W, 380), seed=67, faint=40)
    s.layers[1:1] = star_layer.layers[1:]   # behind the clouds and hills
    tw, d = s.new("fireflies", 0.0, SWAY(10, 6, 5))
    rng = np.random.default_rng(65)
    for _ in range(25):
        x, y = int(rng.integers(0, W)), int(rng.integers(380, 680))
        d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(230, 255, 140, 230))
    return s


def park_autumn():
    s = park()
    for layer in s.layers:
        if layer[0] in ("trees", "near hill", "far hill", "grass"):
            a = np.asarray(layer[1]).astype(np.float32)
            g = a[..., 1] > a[..., 0]
            a[g, 0], a[g, 1], a[g, 2] = a[g, 1] * 1.4, a[g, 1] * 0.8, a[g, 2] * 0.4
            layer[1] = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")
    s.add("leaves", motes(66, 50, (230, 120, 40, 230), 7), -0.25, FALL(H, 10))
    return s


def ward_night():
    s = recolor(ward(), (0.3, 0.38, 0.5), (0, 5, 15))
    s.add("monitor glow", light((730, 290), 140, (90, 255, 160), 120), 0.04, PULSE(0.4, 1.1))
    return s


def rooftop_dawn():
    s = recolor(rooftop(), (1.4, 1.0, 0.9), (60, 30, 30))
    for layer in s.layers:
        if layer[3] and layer[3].get("type") == "stars":
            layer[3] = STARS(35, 4)
    s.add("dawn", light((200, 560), 600, (255, 170, 110), 160), 1.2, PULSE(0.85, 12))
    return s


def corridor():
    back = gradient(W, H, (225, 232, 230), (200, 210, 208))
    d = ImageDraw.Draw(back)
    d.polygon([(560, 260), (720, 260), (720, 420), (560, 420)], fill=(240, 245, 245))
    s = Scene(back, 1.3)
    walls, d = s.new("walls", 0.6)
    d.polygon([(0, 0), (560, 260), (560, 420), (0, H)], fill=(200, 215, 212, 255))
    d.polygon([(W, 0), (720, 260), (720, 420), (W, H)], fill=(195, 210, 208, 255))
    for k in range(4):
        x = 100 + k * 110
        d.rectangle([x, 200 + k * 15, x + 40, 560 - k * 35], fill=(150, 175, 185, 255))
        d.rectangle([W - x - 40, 200 + k * 15, W - x, 560 - k * 35], fill=(150, 175, 185, 255))
    floor, d = s.new("floor", 0.3)
    d.polygon([(0, H), (560, 420), (720, 420), (W, H)], fill=(170, 185, 190, 255))
    lights, d = s.new("tubes", 0.4, PULSE(0.8, 0.3))
    for k in range(5):
        y = 20 + k * 45
        w = 300 - k * 55
        d.rectangle([640 - w, y, 640 + w, y + 10], fill=(250, 255, 255, 255))
    s.add("gurney", gurney(), -0.1)
    return s


def gurney():
    img, d = blank()
    d.rounded_rectangle([60, 520, 420, 560], 8, fill=(235, 235, 240, 255))
    for x in (90, 380):
        d.line([x, 560, x, 650], fill=(140, 150, 160, 255), width=6)
        d.ellipse([x - 12, 645, x + 12, 669], fill=(60, 60, 70, 255))
    return img


def therapy():
    back = gradient(W, H, (245, 235, 215), (225, 210, 190))
    d = ImageDraw.Draw(back)
    d.rectangle([900, 100, 1180, 330], fill=(230, 240, 245))
    back.paste(gradient(250, 200, (170, 210, 240), (215, 235, 245)), (915, 115))
    d.rectangle([0, 500, W, H], fill=(180, 150, 120))
    s = Scene(back, 1.0)
    s.add("window light", light((1040, 220), 300, (255, 245, 210), 100), 0.95, PULSE(0.8, 9))
    chairs, d = s.new("chairs", 0.3)
    for k in range(7):
        ang = math.pi * (0.1 + k * 0.8 / 6)
        x, y = 640 + 460 * math.cos(ang), 560 - 90 * math.sin(ang)
        d.rounded_rectangle([x - 40, y - 70, x + 40, y], 10, fill=(120, 150, 180, 255))
        d.rectangle([x - 34, y, x - 28, y + 50], fill=(80, 80, 90, 255))
        d.rectangle([x + 28, y, x + 34, y + 50], fill=(80, 80, 90, 255))
    board, d = s.new("whiteboard", 0.7)
    d.rectangle([120, 90, 560, 330], fill=(250, 250, 250, 255), outline=(150, 150, 150, 255), width=6)
    d.text((150, 120), "today: noticing", fill=(70, 100, 150, 255), font=font(34))
    d.text((150, 180), "without judging", fill=(70, 100, 150, 255), font=font(34))
    s.add("tissues", tissues(), -0.15)
    return s


def tissues():
    img, d = blank()
    d.rounded_rectangle([600, 600, 700, 650], 8, fill=(140, 190, 220, 255))
    d.polygon([(630, 600), (650, 570), (670, 600)], fill=(255, 255, 255, 255))
    return img


def pharmacy():
    back = gradient(W, H, (240, 245, 245), (215, 225, 225))
    s = Scene(back, 1.0)
    shelves, d = s.new("shelves", 0.6)
    rng = np.random.default_rng(70)
    for row in range(5):
        y = 80 + row * 85
        d.rectangle([60, y + 60, 1220, y + 68], fill=(170, 180, 185, 255))
        x = 70
        while x < 1200:
            w = int(rng.integers(26, 50))
            col = [(250, 250, 250), (230, 90, 80), (90, 150, 220), (250, 210, 90)][int(rng.integers(0, 4))]
            d.rounded_rectangle([x, y + 10, x + w, y + 60], 6, fill=col + (255,))
            x += w + 8
    sign, d = s.new("sign", 0.5, PULSE(0.7, 3))
    d.rectangle([520, 10, 760, 60], fill=(60, 170, 110, 255))
    d.text((560, 18), "PHARMACY", fill=(255, 255, 255, 255), font=font(30))
    counter, d = s.new("counter", -0.1)
    d.rectangle([0, 520, W, H], fill=(200, 210, 215, 255))
    d.rectangle([0, 510, W, 530], fill=(150, 160, 170, 255))
    d.rounded_rectangle([560, 470, 680, 515], 8, fill=(255, 255, 255, 255))
    d.text((575, 478), "Rx  A-30", fill=(80, 80, 80, 255), font=font(24))
    return s


def theo_flat():
    back = gradient(W, H, (60, 50, 70), (90, 70, 80))
    d = ImageDraw.Draw(back)
    for i, (x, col) in enumerate([(100, (200, 80, 80)), (380, (80, 160, 200)), (900, (220, 190, 70))]):
        d.rectangle([x, 80, x + 200, 330], fill=col)
        d.text((x + 20, 100 + i * 10), ["SYNTH", "NIGHT", "LOOP"][i], fill=(30, 30, 30), font=font(40))
    s = Scene(back, 1.0)
    s.add("lava", lava(), 0.5, BREATHE(0.04, 6))
    s.add("lavaglow", light((1150, 360), 160, (255, 80, 150), 120), 0.52, PULSE(0.5, 6))
    couch, d = s.new("couch", 0.25)
    d.rounded_rectangle([200, 430, 900, 600], 40, fill=(120, 80, 60, 255))
    d.rounded_rectangle([200, 380, 900, 470], 30, fill=(140, 95, 70, 255))
    mess, d = s.new("mess", -0.15)
    d.rectangle([0, 600, W, H], fill=(70, 55, 60, 255))
    for x, y in [(300, 640), (520, 655), (980, 630)]:
        d.ellipse([x - 30, y - 10, x + 30, y + 10], fill=(200, 200, 210, 255))
    d.rectangle([700, 620, 760, 660], fill=(230, 60, 60, 255))
    return s


def lava():
    img, d = blank()
    d.rounded_rectangle([1120, 260, 1180, 470], 25, fill=(90, 30, 80, 255))
    d.ellipse([1130, 300, 1170, 350], fill=(255, 90, 160, 255))
    d.ellipse([1135, 390, 1165, 430], fill=(255, 90, 160, 255))
    return img


def club():
    back = gradient(W, H, (10, 5, 25), (30, 10, 40))
    s = Scene(back, 1.2)
    for i, (col, x) in enumerate([((255, 60, 150), 300), ((60, 200, 255), 980), ((180, 90, 255), 640)]):
        beam, d = s.new(f"laser{i}", 0.8, SWAY(60, 0, 2 + i))
        d.polygon([(x, 0), (x + 10, 0), (x - 300 + i * 250, H), (x - 330 + i * 250, H)], fill=col + (130,))
        s.add(f"strobe{i}", light((x, 0), 300, col, 140), 0.85, PULSE(0.05, 0.5 + i * 0.3))
    crowd, d = s.new("crowd", 0.15, SWAY(4, 6, 0.55))
    rng = np.random.default_rng(71)
    for k in range(18):
        x = int(rng.integers(0, W))
        h = int(rng.integers(160, 260))
        d.ellipse([x - 30, H - h - 60, x + 30, H - h], fill=(5, 0, 10, 255))
        d.rounded_rectangle([x - 50, H - h - 5, x + 50, H + 40], 30, fill=(5, 0, 10, 255))
    return s


def bus():
    back = gradient(W, H, (150, 170, 190), (190, 200, 210))
    s = Scene(back, 1.5)
    outside, d = s.new("city passing", 1.2, SWAY(80, 0, 3))
    rng = np.random.default_rng(72)
    x = -200
    while x < W + 200:
        bw, bh = int(rng.integers(80, 180)), int(rng.integers(100, 260))
        d.rectangle([x, 380 - bh, x + bw, 380], fill=tuple(int(c) for c in rng.integers(110, 170, 3)) + (255,))
        x += bw + 10
    shell, d = s.new("bus", 0.2)
    d.rectangle([0, 0, W, 90], fill=(220, 220, 215, 255))
    d.rectangle([0, 380, W, H], fill=(200, 195, 185, 255))
    for x in range(0, W + 1, 320):
        d.rectangle([x - 15, 90, x + 15, 380], fill=(220, 220, 215, 255))
    d.line([0, 110, W, 110], fill=(150, 150, 150, 255), width=6)
    for x in range(80, W, 160):
        d.line([x, 110, x, 150], fill=(120, 120, 120, 255), width=3)
        d.ellipse([x - 12, 150, x + 12, 174], outline=(240, 200, 60, 255), width=5)
    seats, d = s.new("seats", -0.15, SWAY(0, 2, 0.8))
    for x in range(40, W, 300):
        d.rounded_rectangle([x, 470, x + 220, 640], 20, fill=(70, 100, 160, 255))
    return s


def subway():
    back = gradient(W, H, (60, 60, 70), (90, 90, 100))
    s = Scene(back, 1.0)
    tunnel, d = s.new("tunnel", 0.9)
    d.ellipse([440, 180, 840, 520], fill=(10, 10, 15, 255))
    s.add("headlight", light((640, 360), 180, (255, 250, 200), 200), 0.85, PULSE(0.2, 4))
    sign, d = s.new("sign", 0.5)
    d.rectangle([80, 80, 400, 150], fill=(30, 60, 140, 255))
    d.text((100, 95), "7:07  STATION", fill=(255, 255, 255, 255), font=font(36))
    plat, d = s.new("platform", 0.1)
    d.rectangle([0, 520, W, H], fill=(140, 140, 145, 255))
    d.rectangle([0, 510, W, 530], fill=(240, 210, 60, 255))
    return s


def beach():
    back = gradient(W, H, (150, 190, 230), (240, 220, 200))
    s = Scene(back, 1.5)
    s.add("sun", light((300, 260), 260, (255, 230, 180), 160), 1.4, PULSE(0.8, 10))
    sea, d = s.new("sea", 0.9, SWAY(6, 2, 8))
    d.rectangle([-20, 360, W + 20, 520], fill=(70, 130, 180, 255))
    lh, d = s.new("lighthouse", 1.0)
    d.polygon([(1030, 360), (1060, 230), (1080, 230), (1110, 360)], fill=(240, 240, 240, 255))
    d.rectangle([1052, 270, 1088, 285], fill=(200, 60, 60, 255))
    s.add("beam", light((1070, 225), 60, (255, 250, 200), 230), 1.0, PULSE(0.0, 1.2))
    sand, d = s.new("sand", 0.3)
    d.rectangle([0, 500, W, H], fill=(230, 210, 170, 255))
    foam, d = s.new("foam", 0.45, SWAY(20, 3, 6))
    for x in range(-100, W + 100, 200):
        d.arc([x, 480, x + 220, 540], 180, 360, fill=(255, 255, 255, 230), width=6)
    shells, d = s.new("shells", -0.2)
    for x, y in [(200, 650), (840, 680), (1100, 630)]:
        d.ellipse([x - 14, y - 8, x + 14, y + 8], fill=(250, 220, 220, 255))
    return s


def staircase():
    """The dream: a glass staircase down into a calm sea, a lighthouse at the bottom."""
    back = gradient(W, H, (20, 30, 60), (40, 80, 120))
    s = Scene(back, 1.5)
    sky_stars(s, "stars", 1.5, 90, 6, (0, 0, W, 320), seed=73, faint=50)
    sea, d = s.new("sea", 1.1, SWAY(4, 1, 12))
    d.rectangle([-20, 330, W + 20, H], fill=(30, 70, 110, 255))
    for y in range(350, H, 30):
        d.line([0, y, W, y + 4], fill=(50, 95, 140, 255), width=2)
    lh, d = s.new("lighthouse", 1.2)
    d.polygon([(620, 330), (632, 270), (648, 270), (660, 330)], fill=(230, 230, 240, 255))
    s.add("three flickers", light((640, 265), 70, (255, 245, 180), 240), 1.2, PULSE(0.0, 1.0))
    for k in range(9):
        step, d = s.new(f"step{k}", -0.3 + k * 0.17)
        y = 690 - k * 40
        w = 360 - k * 34
        d.polygon([(640 - w, y), (640 + w, y), (640 + w - 20, y - 30), (640 - w + 20, y - 30)],
                  fill=(200, 230, 255, 120))
        d.line([640 - w, y, 640 + w, y], fill=(230, 245, 255, 220), width=2)
    return s


def lighthouse():
    back = gradient(W, H, (10, 15, 35), (30, 40, 70))
    s = Scene(back, 1.4)
    sky_stars(s, "stars", 1.4, 110, 6, (0, 0, W, 450), seed=74, faint=60)
    sweep, d = s.new("beam", 0.6, SWAY(260, 0, 6))
    d.polygon([(640, 220), (1400, 120), (1400, 330)], fill=(255, 250, 200, 90))
    tower, d = s.new("tower", 0.4)
    d.polygon([(560, 680), (600, 260), (680, 260), (720, 680)], fill=(235, 235, 240, 255))
    for y in (360, 480, 600):
        d.rectangle([590 - (y - 260) // 12, y, 690 + (y - 260) // 12, y + 30], fill=(200, 60, 60, 255))
    d.rectangle([585, 200, 695, 260], fill=(60, 60, 70, 255))
    s.add("lamp", light((640, 230), 110, (255, 245, 180), 230), 0.38, PULSE(0.0, 1.0))
    rocks, d = s.new("rocks", -0.2)
    d.ellipse([-100, 600, 700, 820], fill=(30, 30, 40, 255))
    d.ellipse([600, 640, 1400, 860], fill=(25, 25, 35, 255))
    return s


def studio():
    """Aron's workplace: a small product-design studio, Rams on the walls."""
    back = gradient(W, H, (238, 236, 230), (220, 216, 208))
    d = ImageDraw.Draw(back)
    for i in range(4):
        x = 100 + i * 140
        d.rounded_rectangle([x, 120, x + 110, 230], 10, fill=[(220, 220, 215), (60, 60, 60), (230, 120, 40), (200, 200, 195)][i])
        d.ellipse([x + 35, 150, x + 75, 190], fill=(150, 150, 150))
    d.text((100, 260), "good design is as little design as possible", fill=(120, 120, 120), font=font(26))
    s = Scene(back, 1.0)
    win, d = s.new("window", 0.9)
    d.rectangle([820, 60, 1220, 380], fill=(250, 250, 250, 255))
    win.paste(gradient(370, 290, (180, 210, 240), (225, 238, 245)), (835, 75))
    s.add("daylight", light((1020, 220), 320, (255, 255, 240), 90), 0.85, PULSE(0.85, 8))
    desk_, d = s.new("desk", 0.25)
    d.rectangle([0, 470, W, 500], fill=(180, 170, 155, 255))
    d.rectangle([0, 500, W, H], fill=(205, 198, 186, 255))
    d.rectangle([520, 360, 760, 470], fill=(40, 40, 45, 255))
    d.rectangle([530, 370, 750, 460], fill=(210, 220, 230, 255))
    for k in range(5):
        d.line([545, 385 + k * 15, 735, 385 + k * 15], fill=(160, 170, 180, 255), width=2)
    radio, d = s.new("radio", -0.1)
    d.rounded_rectangle([900, 400, 1080, 470], 8, fill=(235, 230, 220, 255))
    for x in range(915, 990, 12):
        d.line([x, 410, x, 460], fill=(180, 175, 165, 255), width=4)
    d.ellipse([1010, 415, 1050, 455], fill=(230, 120, 40, 255))
    return s


def supermarket():
    back = gradient(W, H, (235, 240, 240), (210, 215, 215))
    s = Scene(back, 1.2)
    rng = np.random.default_rng(75)
    for depth, (x0, x1) in [(0.8, (420, 860)), (0.4, (180, 1100)), (0.0, (-60, 1340))]:
        aisle, d = s.new(f"aisle{depth}", depth)
        scale_ = (x1 - x0) / 1400
        for side in (0, 1):
            x = x0 if side == 0 else x1 - int(260 * scale_ + 40)
            w = int(260 * scale_ + 40)
            for row in range(5):
                y = 120 + row * int(90 * scale_ + 20)
                d.rectangle([x, y, x + w, y + 10], fill=(180, 180, 185, 255))
                for k in range(0, w - 10, 14):
                    col = [(230, 80, 70), (80, 150, 220), (250, 200, 80), (120, 200, 120)][int(rng.integers(0, 4))]
                    d.rectangle([x + k, y - 30, x + k + 10, y], fill=col + (255,))
    s.add("tubes", light((640, 0), 700, (240, 255, 255), 50), 0.6, PULSE(0.8, 0.4))
    cart, d = s.new("cart", -0.2)
    d.rectangle([980, 520, 1180, 620], outline=(150, 150, 160, 255), width=5)
    for x in range(1000, 1180, 25):
        d.line([x, 520, x, 620], fill=(150, 150, 160, 255), width=2)
    d.ellipse([990, 640, 1010, 660], fill=(60, 60, 60, 255))
    d.ellipse([1150, 640, 1170, 660], fill=(60, 60, 60, 255))
    return s


def bridge():
    back = gradient(W, H, (40, 40, 80), (120, 80, 110))
    s = Scene(back, 1.4)
    sky_stars(s, "stars", 1.4, 70, 5, (0, 0, W, 260), seed=76, faint=30)
    city, d = s.new("far shore", 1.0)
    rng = np.random.default_rng(77)
    x = 0
    while x < W:
        bw, bh = int(rng.integers(40, 110)), int(rng.integers(60, 180))
        d.rectangle([x, 380 - bh, x + bw, 380], fill=(30, 25, 50, 255))
        for wy in range(380 - bh + 10, 370, 20):
            if rng.random() < 0.5:
                d.rectangle([x + 8, wy, x + 14, wy + 8], fill=(255, 220, 140, 255))
        x += bw + 4
    river, d = s.new("river", 0.7, SWAY(10, 1, 9))
    d.rectangle([-20, 380, W + 20, 560], fill=(40, 50, 90, 255))
    for y in range(390, 560, 18):
        d.line([0, y, W, y], fill=(80, 90, 140, 255), width=2)
    rail, d = s.new("railing", -0.15)
    d.rectangle([0, 560, W, H], fill=(60, 55, 70, 255))
    d.rectangle([0, 520, W, 530], fill=(150, 150, 160, 255))
    for x in range(0, W, 60):
        d.rectangle([x, 520, x + 6, 600], fill=(150, 150, 160, 255))
    return s


def forest():
    back = gradient(W, H, (190, 220, 200), (120, 160, 120))
    s = Scene(back, 1.3)
    for depth, n, col, seed in [(1.0, 18, (90, 130, 100), 78), (0.6, 12, (60, 105, 70), 79), (0.2, 7, (40, 80, 50), 80)]:
        trees, d = s.new(f"trees{depth}", depth, SWAY(1, 0, 8))
        rng = np.random.default_rng(seed)
        for _ in range(n):
            x = int(rng.integers(0, W))
            w = int(30 / (depth + 0.2))
            d.rectangle([x - w // 4, 100, x + w // 4, H], fill=tuple(c - 30 for c in col) + (255,))
            d.ellipse([x - w * 2, 40, x + w * 2, 300], fill=col + (255,))
    s.add("sunbeams", light((900, 0), 600, (255, 250, 200), 80), 0.4, PULSE(0.7, 7))
    s.add("pollen", motes(81, 40, (255, 255, 220, 180), 3), -0.25, SWAY(20, 10, 11))
    return s


def mira_balcony():
    back = gradient(W, H, (255, 190, 150), (250, 220, 190))
    s = Scene(back, 1.4)
    s.add("sunset", light((900, 420), 400, (255, 170, 110), 160), 1.3, PULSE(0.85, 11))
    roofs, d = s.new("roofs", 0.9)
    for k in range(9):
        x = k * 150
        d.polygon([(x, 480), (x + 75, 400 - (k % 3) * 20), (x + 150, 480)], fill=(180, 100, 90, 255))
        d.rectangle([x, 480, x + 150, 600], fill=(220, 180, 150, 255))
    rail, d = s.new("railing", 0.2)
    d.rectangle([0, 560, W, 575], fill=(60, 60, 60, 255))
    for x in range(0, W, 45):
        d.rectangle([x, 575, x + 6, H], fill=(60, 60, 60, 255))
    plants, d = s.new("plants", -0.2, SWAY(2, 0, 5))
    for x in (90, 1150):
        d.rectangle([x - 50, 600, x + 50, H], fill=(190, 100, 70, 255))
        for k in range(6):
            d.ellipse([x - 70 + k * 25, 470 + (k % 2) * 30, x - 30 + k * 25, 610], fill=(70, 140, 70, 255))
    return s


# -------------------------------------------------- the hidden world

def barracks():
    back = gradient(W, H, (255, 252, 240), (235, 225, 195))
    s = Scene(back, 1.3)
    cols, d = s.new("columns", 0.8)
    for x in range(60, W, 170):
        d.rectangle([x, 0, x + 50, H], fill=(245, 240, 225, 255))
        d.rectangle([x - 10, 0, x + 60, 30], fill=(230, 220, 190, 255))
    ranks, d = s.new("ranks", 0.4)
    for row in range(3):
        for k in range(8):
            x, y = 130 + k * 140 + row * 30, 420 + row * 70
            for side in (-1, 1):
                d.ellipse([x + side * 10 - 30 if side < 0 else x + 10, y - 60, x + side * 10 + 30 if side > 0 else x - 10, y + 10],
                          fill=(255, 255, 255, 200))
            d.rectangle([x - 12, y - 40, x + 12, y + 20], fill=(250, 245, 230, 255))
            d.ellipse([x - 10, y - 62, x + 10, y - 42], fill=(240, 225, 215, 255))
            d.ellipse([x - 14, y - 72, x + 14, y - 66], outline=(255, 210, 90, 255), width=2)
    s.add("halo light", light((640, 0), 700, (255, 230, 150), 70), 0.6, PULSE(0.7, 5))
    banner, d = s.new("banner", -0.1, SWAY(4, 0, 4))
    d.polygon([(560, 0), (720, 0), (720, 160), (640, 130), (560, 160)], fill=(220, 180, 80, 255))
    d.text((585, 40), "CORPS", fill=(255, 255, 240, 255), font=font(30))
    return s


def spawning():
    back = gradient(W, H, (50, 40, 90), (100, 80, 140))
    s = Scene(back, 1.2)
    pools, d = s.new("pools", 0.5)
    for k, x in enumerate((220, 640, 1060)):
        d.ellipse([x - 170, 470, x + 170, 580], fill=(140, 200, 255, 255))
        d.ellipse([x - 150, 480, x + 150, 565], fill=(180, 230, 255, 255))
    for k, x in enumerate((220, 640, 1060)):
        s.add(f"poolglow{k}", light((x, 520), 220, (160, 220, 255), 150), 0.52, PULSE(0.5, 3 + k))
        sp, d = s.new(f"forming{k}", 0.3 - k * 0.05, RISE(80, 6 + k))
        for j in range(3):
            y = 470 - j * 40
            d.ellipse([x - 30 + j * 4, y - 40, x + 30 - j * 4, y + 10], fill=(200, 230, 255, 120 - j * 30))
    s.add("wisps", motes(82, 60, (220, 230, 255, 160), 4), -0.25, RISE(H, 16))
    return s


def archive():
    """Where every record ends up. Pim works here, much later."""
    back = gradient(W, H, (40, 32, 28), (70, 55, 45))
    s = Scene(back, 1.4)
    for depth, n, scale_ in [(1.2, 14, 0.5), (0.7, 9, 0.75), (0.25, 6, 1.0)]:
        shelves, d = s.new(f"shelves{depth}", depth)
        w = int(140 * scale_)
        for k in range(n):
            x = k * (W // n)
            d.rectangle([x, int(120 / scale_ - 120), x + w, H], fill=(90, 65, 45, 255))
            for y in range(int(150 / scale_ - 120), H, int(60 * scale_)):
                d.rectangle([x + 6, y, x + w - 6, y + int(40 * scale_)], fill=(200, 185, 150, 255))
                d.line([x + 6, y + int(40 * scale_), x + w - 6, y + int(40 * scale_)], fill=(70, 50, 35, 255), width=3)
    s.add("candle", light((640, 520), 260, (255, 200, 120), 170), 0.0, PULSE(0.75, 2.5))
    desk_, d = s.new("desk", -0.15)
    d.rectangle([380, 560, 900, 590], fill=(60, 40, 30, 255))
    d.rectangle([560, 520, 720, 560], fill=(240, 230, 200, 255))
    d.text((575, 528), "A-30", fill=(90, 60, 40, 255), font=font(24))
    s.add("dust", motes(83, 40, (255, 230, 190, 140), 3), -0.3, RISE(H, 30))
    return s


def trial():
    back = gradient(W, H, (230, 215, 170), (180, 150, 100))
    s = Scene(back, 1.2)
    s.add("judgement", light((640, 0), 600, (255, 240, 190), 160), 1.0, PULSE(0.8, 6))
    bench, d = s.new("bench", 0.6)
    d.rectangle([240, 140, 1040, 300], fill=(150, 110, 60, 255))
    d.rectangle([220, 120, 1060, 150], fill=(120, 85, 45, 255))
    for x in (400, 640, 880):
        d.ellipse([x - 40, 60, x + 40, 140], fill=(240, 230, 200, 255))
        d.ellipse([x - 50, 40, x + 50, 60], outline=(255, 210, 90, 255), width=4)
    dock, d = s.new("dock", -0.1)
    d.rectangle([430, 560, 850, 600], fill=(110, 80, 45, 255))
    d.rectangle([430, 600, 450, H], fill=(110, 80, 45, 255))
    d.rectangle([830, 600, 850, H], fill=(110, 80, 45, 255))
    return s


def ashveil_study():
    back = gradient(W, H, (40, 10, 25), (80, 25, 40))
    d = ImageDraw.Draw(back)
    for x in range(0, W, 90):
        d.line([x, 0, x, H], fill=(55, 15, 35), width=30)
    s = Scene(back, 1.0)
    fire, d = s.new("fireplace", 0.6)
    d.rectangle([800, 300, 1150, 600], fill=(50, 20, 25, 255))
    d.rectangle([840, 380, 1110, 600], fill=(15, 5, 8, 255))
    flames, d = s.new("flames", 0.58, BREATHE(0.08, 0.7))
    d.polygon([(880, 600), (930, 470), (975, 560), (1010, 440), (1060, 600)], fill=(255, 120, 40, 255))
    s.add("fireglow", light((975, 520), 320, (255, 120, 60), 170), 0.55, PULSE(0.6, 0.9))
    globe, d = s.new("globe", 0.2, SWAY(0, 0, 1))
    d.ellipse([200, 350, 360, 510], fill=(60, 110, 190, 255))
    d.ellipse([240, 380, 300, 430], fill=(80, 150, 90, 255))
    d.rectangle([270, 510, 290, 600], fill=(150, 120, 60, 255))
    chair, d = s.new("chair", -0.15)
    d.rounded_rectangle([450, 380, 720, H], 40, fill=(110, 20, 40, 255))
    d.rounded_rectangle([420, 520, 750, 600], 30, fill=(130, 25, 45, 255))
    glass, d = s.new("wine", -0.25)
    d.polygon([(760, 520), (800, 520), (790, 560), (770, 560)], fill=(140, 0, 30, 255))
    d.line([780, 560, 780, 600], fill=(220, 220, 230, 255), width=3)
    return s


def foundry():
    """Where the snapshot's pattern people are rendered."""
    back = gradient(W, H, (10, 25, 30), (20, 50, 55))
    d = ImageDraw.Draw(back)
    for x in range(0, W, 32):
        d.line([x, 0, x, H], fill=(20, 60, 65), width=1)
    s = Scene(back, 1.2)
    for k, x in enumerate((240, 520, 800, 1080)):
        fig, d = s.new(f"pattern{k}", 0.7 - k * 0.15, BREATHE(0.01, 3 + k * 0.5))
        col = (110, 255, 220, 255)
        d.ellipse([x - 45, 180, x + 45, 270], outline=col, width=3)
        d.polygon([(x - 70, 600), (x + 70, 600), (x + 45, 290), (x - 45, 290)], outline=col)
        for y in range(300, 600, 30):
            d.line([x - 60, y, x + 60, y], fill=(110, 255, 220, 120), width=1)
        if k % 2 == 0:  # half-rendered: filled from the feet up
            d.polygon([(x - 70, 600), (x + 70, 600), (x + 58, 450), (x - 58, 450)], fill=(180, 160, 140, 255))
    s.add("scan", light((640, 0), 900, (110, 255, 220), 60), 0.5, PULSE(0.3, 2))
    s.add("data", motes(84, 70, (110, 255, 220, 200), 3), -0.2, RISE(H, 7))
    return s


def coma_room():
    """World 7,412: the real hospital room. Aron's body, asleep for months."""
    back = gradient(W, H, (190, 200, 210), (160, 170, 180))
    d = ImageDraw.Draw(back)
    d.rectangle([880, 80, 1180, 330], fill=(120, 140, 170))
    s = Scene(back, 1.0)
    s.add("window", light((1030, 200), 260, (220, 230, 255), 110), 0.95, PULSE(0.8, 10))
    bed, d = s.new("bed", 0.35)
    d.rounded_rectangle([160, 420, 900, 600], 20, fill=(240, 240, 245, 255))
    d.rounded_rectangle([180, 360, 360, 440], 25, fill=(255, 255, 255, 255))
    d.ellipse([220, 340, 330, 430], fill=(230, 190, 160, 255))
    d.chord([212, 330, 338, 400], 180, 360, fill=(40, 40, 50, 255))
    d.arc([250, 375, 280, 390], 20, 160, fill=(60, 40, 40, 255), width=3)
    d.arc([290, 375, 320, 390], 20, 160, fill=(60, 40, 40, 255), width=3)
    d.rounded_rectangle([330, 430, 880, 520], 30, fill=(170, 190, 220, 255))
    mon, d = s.new("monitor", 0.1)
    d.rounded_rectangle([960, 380, 1080, 460], 10, fill=(50, 60, 70, 255))
    d.rectangle([1010, 460, 1030, 640], fill=(160, 165, 170, 255))
    beat, d = s.new("heartbeat", 0.09, PULSE(0.15, 1.2))
    d.line([970, 420, 995, 420, 1005, 395, 1020, 445, 1030, 420, 1070, 420], fill=(90, 255, 140, 255), width=3)
    chair, d = s.new("empty chair", -0.1)
    d.rounded_rectangle([1000, 520, 1200, 700], 20, fill=(150, 100, 80, 255))
    d.rectangle([1080, 600, 1110, 640], fill=(220, 120, 60, 255))  # her scarf
    return s


# -------------------------------------------------- key moments (CGs)

def cg_umbrella():
    s = street_rain()
    fig, d = s.new("stranger", 0.1)
    d.rounded_rectangle([520, 300, 640, 620], 40, fill=(90, 90, 100, 255))
    d.ellipse([540, 220, 620, 300], fill=(200, 180, 170, 255))
    ar, d = s.new("aron", -0.05)
    d.rounded_rectangle([700, 320, 820, 640], 40, fill=(70, 130, 200, 255))
    d.ellipse([720, 240, 800, 320], fill=(230, 190, 160, 255))
    d.chord([715, 225, 805, 290], 180, 360, fill=(40, 40, 50, 255))
    um, d = s.new("umbrella", -0.2, SWAY(0, 3, 3))
    d.chord([420, 160, 760, 320], 180, 360, fill=(28, 28, 34, 255))
    d.line([590, 240, 640, 470], fill=(60, 60, 60, 255), width=5)
    d.line([640, 470, 700, 420], fill=(230, 190, 160, 255), width=14)
    return s


def cg_hands():
    back = gradient(W, H, (250, 230, 210), (230, 200, 180))
    s = Scene(back, 1.0)
    s.add("warmth", light((640, 360), 420, (255, 200, 150), 120), 0.8, PULSE(0.7, 5))
    his, d = s.new("his hand", 0.0, BREATHE(0.006, 5))
    d.rounded_rectangle([-50, 330, 620, 450], 60, fill=(230, 190, 160, 255))
    for k in range(4):
        d.rounded_rectangle([560 + k * 8, 300 + k * 30, 700 + k * 8, 340 + k * 30], 20, fill=(225, 185, 155, 255))
    hers, d = s.new("her hand", -0.05, BREATHE(0.006, 4.4))
    d.rounded_rectangle([660, 360, W + 50, 470], 60, fill=(255, 225, 205, 255))
    for k in range(4):
        d.rounded_rectangle([600 - k * 6, 330 + k * 30, 720 - k * 6, 368 + k * 30], 18, fill=(250, 220, 200, 255))
    for x, y in [(900, 400), (1000, 420), (1080, 395)]:
        d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(200, 120, 90, 255))
    return s


def cg_pills():
    back = gradient(W, H, (240, 235, 225), (220, 210, 195))
    s = Scene(back, 1.0)
    s.add("morning", light((1100, 0), 600, (255, 235, 190), 110), 0.9, PULSE(0.85, 8))
    box, d = s.new("organiser", 0.2)
    for k, day in enumerate("MTWTFSS"):
        x = 140 + k * 145
        d.rounded_rectangle([x, 300, x + 130, 470], 14, fill=(180, 210, 240, 255))
        d.text((x + 50, 310), day, fill=(60, 80, 110, 255), font=font(34))
        for j in range(2 if k < 3 else 1):
            d.ellipse([x + 30 + j * 40, 390, x + 62 + j * 40, 420], fill=(250, 250, 250, 255))
    glass, d = s.new("water", -0.2)
    d.rectangle([1080, 380, 1180, 600], outline=(170, 200, 220, 255), width=4)
    d.rectangle([1084, 450, 1176, 596], fill=(200, 225, 245, 180))
    return s


def cg_notebook():
    back = gradient(W, H, (60, 50, 45), (90, 75, 65))
    s = Scene(back, 1.0)
    s.add("lamp", light((900, 200), 500, (255, 210, 140), 140), 0.6, PULSE(0.85, 6))
    page, d = s.new("page", 0.1)
    d.polygon([(200, 120), (1080, 90), (1120, 650), (170, 680)], fill=(248, 244, 230, 255))
    for y in range(180, 640, 40):
        d.line([200, y, 1090, y - 20], fill=(190, 200, 230, 255), width=2)
    words, d = s.new("words", 0.05)
    d.text((240, 200), "If this is a test,", fill=(40, 40, 90, 255), font=font(54))
    d.text((240, 280), "I want to pass it", fill=(40, 40, 90, 255), font=font(54))
    d.text((240, 360), "by being kind.", fill=(40, 40, 90, 255), font=font(54))
    pen, d = s.new("pen", -0.25)
    d.line([800, 600, 1100, 420], fill=(30, 30, 30, 255), width=14)
    return s


def cg_flicker():
    back = gradient(W, H, (20, 18, 30), (35, 30, 45))
    s = Scene(back, 1.0)
    lampshade, d = s.new("lamp", 0.3)
    d.polygon([(520, 160), (760, 160), (820, 320), (460, 320)], fill=(220, 190, 130, 255))
    d.line([640, 320, 640, 600], fill=(50, 50, 50, 255), width=10)
    s.add("one", light((640, 300), 420, (255, 220, 150), 220), 0.28, PULSE(0.0, 0.9))
    s.add("two", light((640, 300), 220, (255, 240, 200), 160), 0.26, PULSE(0.0, 0.9))
    s.add("three", light((640, 300), 90, (255, 255, 230), 230), 0.24, PULSE(0.0, 0.9))
    return s


SCENES.update({
    "bg bedroom night": bedroom_night, "bg kitchen night": kitchen_night,
    "bg room night": room_night, "bg street rain": street_rain, "bg street dusk": street_dusk,
    "bg street snow": street_snow, "bg park night": park_night, "bg park autumn": park_autumn,
    "bg ward night": ward_night, "bg rooftop dawn": rooftop_dawn,
    "bg corridor": corridor, "bg therapy": therapy, "bg pharmacy": pharmacy,
    "bg theo": theo_flat, "bg club": club, "bg bus": bus, "bg subway": subway,
    "bg beach": beach, "bg staircase": staircase, "bg lighthouse": lighthouse,
    "bg studio": studio, "bg supermarket": supermarket, "bg bridge": bridge,
    "bg forest": forest, "bg balcony": mira_balcony,
    "bg barracks": barracks, "bg spawning": spawning, "bg archive": archive,
    "bg trial": trial, "bg ashveil": ashveil_study, "bg foundry": foundry,
    "bg coma": coma_room,
    "cg umbrella": cg_umbrella, "cg hands": cg_hands, "cg pills": cg_pills,
    "cg notebook": cg_notebook, "cg flicker": cg_flicker,
})


# ---------------------------------------------------------------- angles & POV
# Looking out of Aron's head: vignette, the blurred edge of his own nose and
# heavy eyelids sit in front of the screen; the world sits behind it.

def pov(scene, tired=False):
    yy, xx = np.mgrid[0:H, 0:W]
    dist = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    a = (np.clip((dist - 0.75) / 0.6, 0, 1) * 235).astype(np.uint8)
    vig = np.zeros((H, W, 4), np.uint8)
    vig[..., 3] = a
    scene.add("vignette", Image.fromarray(vig, "RGBA"), -0.45)
    nose, d = blank()
    d.polygon([(560, H + 40), (640, 560), (720, H + 40)], fill=(225, 185, 155, 200))
    scene.add("nose", nose.filter(ImageFilter.GaussianBlur(40)), -0.7)
    lids, d = blank()
    band = 120 if tired else 70
    d.rectangle([0, 0, W, band], fill=(10, 5, 5, 255))
    d.rectangle([0, H - band, W, H], fill=(10, 5, 5, 255))
    scene.add("eyelids", lids.filter(ImageFilter.GaussianBlur(45)), -0.6,
              PULSE(0.0 if tired else 0.3, 6 if tired else 9))
    return scene


def pov_ceiling():
    back = gradient(W, H, (110, 95, 120), (150, 125, 130))
    s = Scene(back, 1.0)
    tiles, d = s.new("ceiling", 0.9)
    for x in range(-40, W, 160):
        d.line([x, 0, x + 120, H], fill=(130, 115, 135, 255), width=3)
    s.add("dawn", light((1100, 200), 500, (255, 180, 120), 110), 0.85, PULSE(0.6, 6))
    lampf, d = s.new("lamp", 0.6, SWAY(4, 0, 9))
    d.line([640, 0, 640, 180], fill=(60, 50, 60, 255), width=3)
    d.ellipse([590, 170, 690, 230], fill=(240, 220, 190, 255))
    clk, d = s.new("clock", -0.1)
    d.rounded_rectangle([1060, 560, 1240, 640], 10, fill=(30, 30, 40, 255))
    d.text((1085, 568), "7:07", fill=(255, 90, 90, 255), font=font(56))
    return pov(s, tired=True)


def pov_hands():
    back = gradient(W, H, (70, 60, 80), (110, 90, 100))
    s = Scene(back, 1.2)
    s.add("room blur", light((640, 200), 500, (180, 160, 170), 80), 1.0, PULSE(0.8, 7))
    for side, x0 in ((-1, 380), (1, 900)):
        hand, d = s.new(f"hand{side}", -0.15, SWAY(2, 3, 5 + side))
        d.rounded_rectangle([x0 - 130, 470, x0 + 130, 760], 70, fill=(230, 190, 160, 255))
        for k in range(4):
            fx = x0 - 105 + k * 60
            d.rounded_rectangle([fx, 300 + abs(k - 1.5) * 25, fx + 46, 520], 22, fill=(225, 185, 155, 255))
        tx = x0 + side * 140
        d.rounded_rectangle([min(tx, tx - side * 110), 470, max(tx, tx - side * 110), 520], 22, fill=(225, 185, 155, 255))
        for k in range(4):
            fx = x0 - 105 + k * 60
            d.arc([fx + 8, 330 + abs(k - 1.5) * 25, fx + 38, 360 + abs(k - 1.5) * 25], 200, 340,
                  fill=(200, 160, 135, 255), width=3)
    return pov(s)


def pov_mirror():
    s = mirror()
    face_, d = s.new("reflection", 0.55, SWAY(2, 1, 3.1))
    d.ellipse([560, 130, 720, 330], fill=(230, 190, 160, 255))
    d.chord([550, 110, 730, 250], 180, 360, fill=(40, 40, 50, 255))
    d.ellipse([595, 210, 615, 232], fill=(40, 30, 30, 255))
    d.ellipse([665, 210, 685, 232], fill=(40, 30, 30, 255))
    d.line([615, 290, 665, 290], fill=(150, 50, 60, 255), width=5)
    d.rounded_rectangle([540, 330, 740, 425], 30, fill=(70, 130, 200, 255))
    return pov(s, tired=True)


def pov_street_up():
    back = gradient(W, H, (120, 160, 220), (200, 215, 235))
    s = Scene(back, 1.4)
    tops, d = s.new("rooftops", 0.6)
    d.polygon([(0, H), (0, 380), (260, 300), (260, H)], fill=(150, 140, 160, 255))
    d.polygon([(W, H), (W, 360), (1010, 280), (1010, H)], fill=(160, 150, 165, 255))
    wire, d = s.new("wire", 0.2)   # three birds, from below; still not moving
    d.line([0, 260, W, 200], fill=(40, 40, 40, 255), width=5)
    for k, bx in enumerate((540, 620, 700)):
        y = 260 - (bx / W) * 60
        d.ellipse([bx - 30, y - 34, bx + 30, y + 6], fill=(50, 50, 60, 255))
        d.polygon([(bx + 26, y - 18), (bx + 46, y - 14), (bx + 26, y - 8)], fill=(230, 160, 40, 255))
    return pov(s)


def pov_sky():
    s = rooftop()
    s.layers = [l for l in s.layers if l[0] not in ("roof", "city")]
    return pov(s)


def pov_cup():
    s = kitchen()
    s.layers = [l for l in s.layers if l[0] not in ("coffee", "steam", "indicator")]
    cup, d = s.new("cup", -0.25)
    d.ellipse([440, 470, 840, 600], fill=(240, 240, 245, 255))
    d.ellipse([470, 485, 810, 585], fill=(90, 55, 35, 255))
    d.arc([800, 500, 900, 600], 270, 90, fill=(240, 240, 245, 255), width=18)
    s.add("cupsteam", motes(90, 30, (255, 255, 255, 120), 6, 300, 480), -0.3, RISE(220, 4))
    return pov(s)


def kitchen_table():
    """Sitting at the table, across from Mira's empty chair."""
    back = gradient(W, H, (250, 236, 210), (230, 210, 180))
    s = Scene(back, 1.0)
    win, d = s.new("window", 0.9)
    d.rectangle([780, 70, 1180, 330], fill=(255, 255, 255, 255))
    win.paste(gradient(370, 230, (140, 190, 240), (210, 235, 250)), (795, 85))
    chair, d = s.new("chair", 0.45)
    d.rounded_rectangle([480, 220, 800, 520], 30, fill=(150, 105, 75, 255))
    d.rectangle([500, 520, 530, 650], fill=(130, 90, 65, 255))
    d.rectangle([750, 520, 780, 650], fill=(130, 90, 65, 255))
    table, d = s.new("table", -0.05)
    d.polygon([(0, 560), (W, 560), (W, H), (0, H)], fill=(190, 150, 110, 255))
    d.ellipse([200, 590, 420, 660], fill=(245, 245, 250, 255))   # her plate
    d.ellipse([860, 600, 980, 650], fill=(240, 240, 245, 255))   # his cup
    return s


def bedroom_door():
    """The bedroom seen from the bed: the door, the hallway light."""
    back = gradient(W, H, (80, 70, 100), (130, 110, 120))
    s = Scene(back, 1.0)
    door, d = s.new("doorway", 0.8)
    d.rectangle([500, 90, 780, 560], fill=(250, 230, 180, 255))
    s.add("hall light", light((640, 320), 330, (255, 220, 160), 140), 0.75, PULSE(0.8, 7))
    frame, d = s.new("frame", 0.6)
    d.rectangle([480, 70, 800, 560], outline=(70, 55, 60, 255), width=20)
    d.polygon([(780, 90), (900, 40), (900, 620), (780, 560)], fill=(110, 80, 70, 255))
    blanket, d = s.new("blanket", -0.3)
    pts = [(0, 600)] + [(x, 580 + 25 * math.sin(x / 90)) for x in range(0, W + 30, 30)] + [(W, H), (0, H)]
    d.polygon(pts, fill=(120, 140, 200, 255))
    return s


def ward_window():
    back = gradient(W, H, (200, 215, 225), (230, 235, 240))
    s = Scene(back, 1.3)
    s.add("sky", light((640, 200), 500, (255, 255, 255), 120), 1.25, PULSE(0.8, 9))
    tree, d = s.new("tree", 1.0, SWAY(3, 0, 7))
    d.rectangle([300, 300, 330, H], fill=(110, 90, 80, 255))
    d.ellipse([170, 120, 470, 380], fill=(120, 160, 120, 255))
    bars, d = s.new("bars", 0.2)
    for x in range(80, W, 130):
        d.rectangle([x, 0, x + 18, H], fill=(140, 150, 160, 255))
    d.rectangle([0, 340, W, 356], fill=(140, 150, 160, 255))
    sill, d = s.new("sill", -0.15)
    d.rectangle([0, 620, W, H], fill=(240, 245, 245, 255))
    d.rounded_rectangle([900, 560, 990, 625], 10, fill=(255, 255, 255, 255))   # paper cup of pills
    return s


def rooftop_edge():
    """Looking down from the roof: the street far below."""
    back = gradient(W, H, (15, 15, 30), (35, 30, 55))
    s = Scene(back, 1.6)
    street_, d = s.new("street below", 1.5)
    d.rectangle([380, 0, 900, H], fill=(40, 40, 50, 255))
    for y in range(0, H, 80):
        d.rectangle([630, y, 650, y + 40], fill=(200, 200, 160, 255))
    cars, d = s.new("cars", 1.48, SWAY(0, 120, 6))
    for x, y, c in [(470, 200, (255, 80, 80)), (760, 480, (255, 240, 200))]:
        d.rounded_rectangle([x, y, x + 60, y + 100], 10, fill=c + (255,))
    walls, d = s.new("walls", 0.7)
    d.polygon([(0, 0), (380, 0), (380, H), (0, H)], fill=(25, 25, 40, 255))
    d.polygon([(W, 0), (900, 0), (900, H), (W, H)], fill=(28, 28, 44, 255))
    for x in range(40, 360, 60):
        for y in range(30, H, 70):
            if (x + y) % 3:
                d.rectangle([x, y, x + 18, y + 26], fill=(255, 220, 140, 255))
    ledge, d = s.new("ledge", -0.35)
    d.polygon([(0, 560), (W, 600), (W, H), (0, H)], fill=(70, 70, 85, 255))
    return pov(s)


def cafe_window():
    """Outside in the rain, looking in at the warm cafe."""
    s = cafe()
    s.add("glass", light((640, 360), 900, (200, 210, 230), 40), -0.05)
    frame, d = s.new("window frame", -0.15)
    d.rectangle([0, 0, W, H], outline=(40, 35, 40, 255), width=60)
    d.line([640, 0, 640, H], fill=(40, 35, 40, 255), width=24)
    s.add("rain", rain(91, 160, (180, 190, 220, 200), 30), -0.25, FALL(H, 1.0))
    return s


SCENES.update({
    "pov ceiling": pov_ceiling, "pov hands": pov_hands, "pov mirror": pov_mirror,
    "pov birds": pov_street_up, "pov sky": pov_sky, "pov cup": pov_cup,
    "bg kitchen table": kitchen_table, "bg bedroom door": bedroom_door,
    "bg ward window": ward_window, "bg rooftop edge": rooftop_edge, "bg cafe window": cafe_window,
})


# ---------------------------------------------------------------- the ride and the closed ward

def pov_ambulance():
    """Half-closed eyes, flat on his back: the ambulance ceiling, blue light."""
    back = gradient(W, H, (200, 205, 210), (170, 175, 185))
    s = Scene(back, 0.9)
    rails, d = s.new("ceiling rails", 0.7, SWAY(0, 3, 0.9))   # the road under the wheels
    for x in (300, 980):
        d.rectangle([x - 12, 0, x + 12, H], fill=(150, 155, 165, 255))
    for y in range(40, H, 140):
        d.rounded_rectangle([520, y, 760, y + 60], 10, fill=(240, 245, 250, 255))
    s.add("siren", light((640, 0), 760, (60, 110, 255), 150), 0.6, PULSE(0.0, 0.7))
    figs, d = s.new("figures", -0.1, SWAY(6, 4, 3))
    for x in (130, 1150):          # two people leaning over him, out of focus
        d.ellipse([x - 140, -80, x + 140, 260], fill=(60, 80, 90, 255))
        d.ellipse([x - 90, 120, x + 90, 330], fill=(215, 190, 175, 255))
    s.layers[-1][1] = s.layers[-1][1].filter(ImageFilter.GaussianBlur(28))
    return pov(s, tired=True)


def pov_restraint():
    """The closed ward, on his back, held down. Bright light, faces, a gloved hand."""
    back = gradient(W, H, (235, 240, 240), (210, 220, 220))
    s = Scene(back, 1.0)
    tiles, d = s.new("ceiling", 0.9)
    for x in range(0, W, 120):
        d.line([x, 0, x, H], fill=(215, 222, 222, 255), width=2)
    for y in range(0, H, 120):
        d.line([0, y, W, y], fill=(215, 222, 222, 255), width=2)
    s.add("lamp", light((640, 230), 380, (255, 255, 250), 230), 0.8, PULSE(0.7, 1.6))
    people, d = s.new("staff", 0.0, SWAY(10, 6, 2.2))
    for x, col in ((200, (110, 170, 190)), (1080, (110, 170, 190)), (640, (240, 240, 245))):
        d.ellipse([x - 170, -120, x + 170, 300], fill=col + (255,))
        d.ellipse([x - 100, 140, x + 100, 360], fill=(220, 195, 180, 255))
    s.layers[-1][1] = s.layers[-1][1].filter(ImageFilter.GaussianBlur(26))
    glove, d = s.new("gloved hand", -0.3, SWAY(4, 2, 1.3))
    d.rounded_rectangle([780, 380, 1040, 500], 50, fill=(150, 190, 235, 255))
    s.layers[-1][1] = s.layers[-1][1].filter(ImageFilter.GaussianBlur(14))
    strap, d = s.new("strap", -0.5)
    d.rectangle([0, 640, W, 690], fill=(70, 80, 110, 255))
    d.rounded_rectangle([600, 625, 700, 705], 12, fill=(170, 170, 180, 255))
    return pov(s, tired=True)


def isolation():
    """The seclusion room: soft walls, one bed with straps, a window in the door."""
    back = gradient(W, H, (225, 225, 215), (200, 200, 190))
    d = ImageDraw.Draw(back)
    for x in range(0, W, 100):
        for y in range(0, 520, 100):
            d.rounded_rectangle([x + 4, y + 4, x + 96, y + 96], 18, outline=(205, 205, 195), width=3)
    s = Scene(back, 1.0)
    door, d = s.new("door", 0.75)
    d.rectangle([980, 120, 1200, 540], fill=(190, 195, 190, 255))
    d.rectangle([1050, 180, 1130, 250], fill=(120, 140, 160, 255))
    s.add("watcher", light((1090, 215), 60, (255, 240, 200), 140), 0.74, PULSE(0.2, 5))
    floor, d = s.new("floor", 0.5)
    d.rectangle([0, 520, W, H], fill=(185, 185, 175, 255))
    bed, d = s.new("bed", 0.2)
    d.rounded_rectangle([200, 430, 820, 560], 20, fill=(245, 245, 245, 255))
    for x in (330, 500, 670):
        d.rectangle([x, 425, x + 40, 565], fill=(80, 90, 120, 255))
    d.rectangle([200, 560, 230, 640], fill=(150, 150, 160, 255))
    d.rectangle([790, 560, 820, 640], fill=(150, 150, 160, 255))
    s.add("hum", light((640, 0), 700, (240, 255, 255), 50), -0.1, PULSE(0.85, 0.4))
    return s


SCENES.update({"pov ambulance": pov_ambulance, "pov restraint": pov_restraint,
               "bg isolation": isolation})


# ---------------------------------------------------------------- reverse angles
# The same rooms seen from the other side. Each keeps its original's palette,
# materials and light: whatever was on the left of the original is on the
# right here, and the window the original faced is now behind the camera, so
# its light falls into the shot as a patch on the floor and the far wall.
# "door" and "corner" scenes are the original view filmed from the next room
# or from behind something, with a soft foreground frame in front of the
# screen, as if the documentary crew were standing just outside.

def soft_shape(draw, color, alpha=255, blur=0):
    """A transparent layer with shapes painted by `draw(d)` in one colour,
    edges blurred without dark fringes (only the mask is blurred)."""
    mask = Image.new("L", (W, H), 0)
    draw(ImageDraw.Draw(mask))
    if blur:
        mask = mask.filter(ImageFilter.GaussianBlur(blur))
    if alpha < 255:
        mask = mask.point(lambda v: v * alpha // 255)
    img = Image.new("RGBA", (W, H), tuple(color) + (0,))
    img.putalpha(mask)
    return img


def window_patch(quad, color, alpha=90, panes=(2, 2), bar=14, blur=10):
    """The light of a window behind the camera, thrown onto the room as a
    skewed quad split into panes (quad: top-left, top-right, bottom-right,
    bottom-left)."""
    (ax, ay), (bx, by), (cx_, cy_), (dx, dy) = quad
    nx, ny = panes

    def lerp(p, q, t):
        return (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)

    def draw(d):
        for i in range(nx):
            for j in range(ny):
                pts = []
                for u, v in ((i / nx, j / ny), ((i + 1) / nx, j / ny), ((i + 1) / nx, (j + 1) / ny),
                             (i / nx, (j + 1) / ny)):
                    top, bot = lerp((ax, ay), (bx, by), u), lerp((dx, dy), (cx_, cy_), u)
                    pts.append(lerp(top, bot, v))
                cxp = sum(p[0] for p in pts) / 4
                cyp = sum(p[1] for p in pts) / 4
                pts = [(cxp + (px - cxp) * (1 - bar / 200), cyp + (py - cyp) * (1 - bar / 200)) for px, py in pts]
                d.polygon(pts, fill=255)
    return soft_shape(draw, color, alpha, blur)


def wood_floor(d, y0, color, line, step=80, lean=60):
    d.rectangle([0, y0, W, H], fill=color)
    for x in range(-lean, W + lean, step):
        d.line([x, y0, x + lean, H], fill=line, width=3)


def door_frame(wall, trim, opening, shade=0.85, leaf=None, extra=None, blur=2):
    """The near wall around a doorway, in front of the screen: `opening` is
    the (x0, y0, x1) of the gap the camera films through."""
    x0, y0, x1 = opening
    img, d = blank()
    dark = tuple(int(c * shade) for c in wall) + (255,)
    d.rectangle([0, 0, x0, H], fill=dark)
    d.rectangle([x1, 0, W, H], fill=dark)
    d.rectangle([x0, 0, x1, y0], fill=dark)
    t = trim + (255,)
    d.rectangle([x0 - 26, y0 - 26, x0, H], fill=t)
    d.rectangle([x1, y0 - 26, x1 + 26, H], fill=t)
    d.rectangle([x0 - 26, y0 - 26, x1 + 26, y0], fill=t)
    if leaf:
        d.polygon(leaf, fill=tuple(int(c * 0.95) for c in trim) + (255,))
    if extra:
        extra(d)
    return img.filter(ImageFilter.GaussianBlur(blur)) if blur else img


# -- kitchen ----------------------------------------------------------------

def kitchen_reverse():
    """From the counter, looking back: the table and chairs, the door to the
    hallway (left), the fridge (right). The window is behind the camera on
    the right, so its daylight lies across the floor on the right; the
    coffee machine's corner pokes into the bottom left."""
    back = gradient(W, H, (250, 236, 210), (230, 210, 180))
    d = ImageDraw.Draw(back)
    wood_floor(d, 500, (170, 130, 95), (150, 112, 80))
    d.rectangle([0, 492, W, 502], fill=(215, 195, 165))   # skirting
    s = Scene(back, 1.0)
    hall, d = s.new("hallway", 1.05)
    d.rectangle([120, 150, 330, 500], fill=(205, 182, 155, 255))
    d.rectangle([120, 440, 330, 500], fill=(150, 112, 80, 255))
    d.rounded_rectangle([250, 220, 300, 360], 18, fill=(60, 80, 120, 255))   # a coat on a hook
    d.ellipse([268, 205, 282, 219], fill=(120, 90, 60, 255))
    s.add("hall lamp", light((200, 200), 120, (255, 220, 160), 120), 1.04, PULSE(0.8, 7))
    wall, d = s.new("wall things", 0.95)
    d.rectangle([110, 140, 340, 500], outline=(255, 250, 240, 255), width=16)   # door frame
    d.ellipse([590, 110, 690, 210], fill=(255, 255, 255, 255), outline=(150, 110, 80, 255), width=6)
    d.line([640, 160, 640, 120], fill=(40, 40, 40, 255), width=4)             # 7:07
    d.line([640, 160, 658, 128], fill=(40, 40, 40, 255), width=3)
    d.rectangle([760, 150, 860, 280], fill=(255, 255, 250, 255), outline=(200, 180, 150, 255), width=3)
    d.rectangle([760, 150, 860, 180], fill=(220, 90, 80, 255))
    for k in range(12):
        x, y = 768 + (k % 4) * 23, 190 + (k // 4) * 28
        d.rectangle([x, y, x + 16, y + 20], outline=(200, 180, 150, 255), width=2)
    fridge, d = s.new("fridge", 0.7)
    d.rounded_rectangle([980, 100, 1190, 505], 16, fill=(242, 242, 236, 255))
    d.line([985, 230, 1185, 230], fill=(200, 200, 195, 255), width=4)
    d.rectangle([1000, 150, 1012, 210], fill=(190, 190, 185, 255))
    d.rectangle([1000, 250, 1012, 330], fill=(190, 190, 185, 255))
    d.rectangle([1060, 270, 1140, 330], fill=(250, 250, 250, 255), outline=(180, 180, 180, 255), width=2)
    d.ellipse([1075, 282, 1095, 302], fill=(200, 70, 35, 255))    # a photo: her red hair
    d.ellipse([1105, 282, 1125, 302], fill=(40, 40, 50, 255))     # his dark hair
    for x, y, c in [(1050, 120, (230, 180, 60)), (1150, 160, (90, 150, 220)), (1120, 380, (120, 190, 120))]:
        d.ellipse([x - 9, y - 9, x + 9, y + 9], fill=c + (255,))
    s.add("daylight", window_patch([(760, 520), (1080, 520), (1230, 715), (840, 715)], (255, 245, 215), 80),
          0.6, PULSE(0.8, 9))
    bird, d = s.new("bird shadow", 0.59)   # the bird on the wire, its shadow perfectly still
    d.ellipse([985, 600, 1015, 614], fill=(150, 120, 90, 160))
    table, d = s.new("table", 0.35)
    for x in (330, 950):   # chairs, left and right of the table
        d.rounded_rectangle([x - 50, 330, x + 50, 470], 18, fill=(150, 105, 75, 255))
        d.rectangle([x - 55, 470, x + 55, 488], fill=(140, 98, 70, 255))
        d.rectangle([x - 48, 488, x - 38, 600], fill=(130, 90, 65, 255))
        d.rectangle([x + 38, 488, x + 48, 600], fill=(130, 90, 65, 255))
    d.rectangle([400, 440, 880, 466], fill=(190, 150, 110, 255))
    d.rectangle([420, 466, 860, 480], fill=(165, 125, 90, 255))
    for x in (430, 840):
        d.rectangle([x, 480, x + 16, 610], fill=(150, 112, 80, 255))
    d.ellipse([460, 424, 580, 448], fill=(245, 245, 250, 255))   # her plate
    d.rounded_rectangle([760, 412, 795, 446], 6, fill=(240, 240, 245, 255))   # his cup
    d.arc([785, 418, 805, 438], 270, 90, fill=(240, 240, 245, 255), width=5)
    counter, d = s.new("counter corner", -0.2)
    d.rectangle([0, 600, 300, H], fill=(190, 150, 110, 255))
    d.rectangle([0, 585, 310, 605], fill=(150, 110, 80, 255))
    d.rounded_rectangle([-40, 400, 110, 590], 12, fill=(60, 60, 70, 255))   # the coffee machine's side
    d.ellipse([60, 430, 84, 454], fill=(120, 220, 255, 255))
    s.layers[-1][1] = s.layers[-1][1].filter(ImageFilter.GaussianBlur(3))
    s.add("indicator", light((72, 442), 45, (120, 220, 255), 150), -0.21, PULSE(0.3, 2))
    s.add("dust", motes(101, 30, (255, 245, 220, 130), 3, 300, 700), -0.3, RISE(H, 36))
    return s


def kitchen_door():
    """The kitchen filmed from the hallway, through its doorway."""
    s = kitchen()
    s.add("doorway", door_frame((236, 214, 190), (250, 245, 235), (250, 70, 1030),
                                leaf=[(1056, 44), (1150, 0), (1150, H), (1056, H)],
                                extra=lambda d: (d.rounded_rectangle([70, 180, 150, 420], 30, fill=(60, 80, 120, 255)),
                                                 d.ellipse([100, 160, 120, 180], fill=(120, 90, 60, 255)))),
          -0.25)
    return s


def kitchen_night_reverse():
    return night_of(kitchen_reverse, (1000, 600), [((200, 220), 1.0), ((72, 442), -0.21)])


# -- living room --------------------------------------------------------------

def room_reverse():
    """From the window, looking back into the living room: the sofa under
    the lighthouse picture, the plant by its arm, the door to the hallway on
    the right. The window is behind the camera on the left (its cross of
    light lies on the floor); the bookshelf's end is the blurred edge right."""
    back = gradient(W, H, (236, 214, 190), (200, 170, 140))
    d = ImageDraw.Draw(back)
    d.rectangle([0, 520, W, H], fill=(120, 84, 60))
    for x in range(-60, W, 80):
        d.line([x, 520, x + 60, H], fill=(104, 72, 52), width=3)
    d.rectangle([975, 150, 1135, 520], fill=(205, 180, 150))   # doorway to the hallway
    d.rectangle([975, 470, 1135, 520], fill=(104, 72, 52))
    s = Scene(back, 1.0)
    pic, d = s.new("lighthouse picture", 0.95)
    d.rectangle([470, 140, 700, 300], fill=(250, 245, 235, 255))
    d.rectangle([482, 152, 688, 288], fill=(40, 60, 100, 255))
    d.rectangle([482, 230, 688, 288], fill=(40, 80, 120, 255))
    d.polygon([(575, 230), (582, 185), (590, 185), (597, 230)], fill=(235, 235, 240, 255))
    d.ellipse([580, 176, 592, 188], fill=(255, 240, 170, 255))
    d.rectangle([965, 140, 1145, 520], outline=(250, 245, 235, 255), width=14)   # door frame
    s.add("hall light", light((1055, 300), 130, (255, 220, 160), 110), 0.94, PULSE(0.8, 8))
    s.add("daylight", window_patch([(60, 540), (430, 540), (520, 715), (40, 715)], (255, 250, 230), 85),
          0.6, PULSE(0.85, 11))
    sofa, d = s.new("sofa", 0.45)
    d.rounded_rectangle([290, 330, 880, 450], 40, fill=(110, 140, 165, 255))
    d.rounded_rectangle([270, 420, 900, 540], 30, fill=(100, 128, 152, 255))
    for x in (290, 580):
        d.rounded_rectangle([x + 20, 400, x + 290, 450], 20, fill=(125, 155, 180, 255))
    d.rounded_rectangle([250, 380, 320, 540], 25, fill=(95, 120, 145, 255))
    d.rounded_rectangle([850, 380, 920, 540], 25, fill=(95, 120, 145, 255))
    d.rounded_rectangle([700, 360, 770, 410], 16, fill=(230, 180, 60, 255))   # a cushion
    d.rectangle([290, 540, 305, 560], fill=(70, 50, 40, 255))
    d.rectangle([865, 540, 880, 560], fill=(70, 50, 40, 255))
    plant, d = s.new("plant", 0.42, SWAY(1, 0, 9))
    d.ellipse([925, 470, 1015, 505], fill=(90, 140, 90, 255))
    for k in range(5):
        d.ellipse([935 + k * 14, 440 - (k % 2) * 10, 960 + k * 14, 485], fill=(70, 130, 80, 255))
    d.rectangle([945, 490, 995, 545], fill=(170, 100, 70, 255))
    table, d = s.new("coffee table", 0.2)
    d.rounded_rectangle([420, 560, 780, 585], 8, fill=(150, 105, 70, 255))
    d.rectangle([440, 585, 455, 650], fill=(120, 84, 60, 255))
    d.rectangle([745, 585, 760, 650], fill=(120, 84, 60, 255))
    d.polygon([(480, 560), (600, 556), (604, 548), (484, 552)], fill=(245, 240, 225, 255))   # the notebook
    d.rounded_rectangle([680, 528, 710, 560], 6, fill=(240, 240, 245, 255))                # a mug
    shelf, d = s.new("bookshelf end", -0.3)
    d.rectangle([1190, 0, W, H], fill=(110, 70, 45, 255))
    colors = [(200, 60, 60), (60, 120, 200), (230, 180, 60), (80, 160, 90), (150, 80, 170)]
    for row in range(6):
        y = 30 + row * 115
        d.rectangle([1190, y + 100, W, y + 110], fill=(80, 50, 30, 255))
        for k in range(2):
            d.rectangle([1200 + k * 40, y + 20 + (k * 13) % 30, 1230 + k * 40, y + 100],
                        fill=colors[(row + k) % 5] + (255,))
    s.layers[-1][1] = s.layers[-1][1].filter(ImageFilter.GaussianBlur(5))
    s.add("dust", motes(102, 40, (255, 240, 210, 150), 4), -0.3, RISE(H, 40))
    return s


def room_corner():
    """The living room as in bg room, filmed from behind the plant: its
    leaves blur across the left of the frame."""
    s = room()
    s.layers = [l for l in s.layers if l[0] != "plant"]
    leaves, d = s.new("plant", -0.35, SWAY(3, 1, 9))
    d.ellipse([-120, 560, 330, 820], fill=(80, 120, 80, 255))
    for k, (x, y, r) in enumerate([(40, 470, 120), (180, 560, 100), (-30, 250, 130), (130, 330, 90),
                                   (300, 660, 90), (-60, 640, 110)]):
        d.ellipse([x - r, y - r * 0.6, x + r, y + r * 0.6], fill=((60, 115, 70), (75, 135, 85))[k % 2] + (255,))
    s.layers[-1][1] = s.layers[-1][1].filter(ImageFilter.GaussianBlur(7))
    return s


def room_night_reverse():
    return night_of(room_reverse, (280, 620), [((1055, 300), 0.94), ((880, 300), 0.4)])


# -- bedroom -----------------------------------------------------------------

def bedroom_reverse():
    """From the window, looking at the door: the bed along the left (its
    head at the right end), the open door with the hallway light, the 7:07
    clock on the far nightstand. Dawn comes from the window behind the camera
    on the right and lands on the wall beside the door."""
    back = gradient(W, H, (90, 80, 120), (170, 130, 130))
    d = ImageDraw.Draw(back)
    d.rectangle([0, 540, W, H], fill=(80, 60, 70))
    d.rectangle([640, 130, 860, 545], fill=(250, 230, 180))   # the doorway, hall beyond
    s = Scene(back, 1.0)
    s.add("hall light", light((750, 330), 260, (255, 220, 160), 120), 0.98, PULSE(0.8, 7))
    frame, d = s.new("door frame", 0.9)
    d.rectangle([622, 112, 878, 545], outline=(70, 55, 60, 255), width=20)
    d.polygon([(860, 130), (960, 95), (960, 585), (860, 545)], fill=(110, 80, 70, 255))   # the open leaf
    d.ellipse([930, 330, 946, 346], fill=(200, 170, 120, 255))
    stand, d = s.new("nightstand", 0.75)
    d.rectangle([40, 400, 160, 480], fill=(110, 80, 70, 255))
    d.rounded_rectangle([60, 372, 140, 402], 6, fill=(30, 30, 40, 255))
    d.text((70, 374), "7:07", fill=(255, 90, 90, 255), font=font(24))
    s.add("dawn", window_patch([(1000, 190), (1240, 190), (1250, 470), (990, 470)], (255, 180, 110), 120),
          0.88, PULSE(0.6, 6))
    bed, d = s.new("bed", 0.35)
    d.rounded_rectangle([-40, 450, 560, 650], 30, fill=(200, 200, 225, 255))
    d.rounded_rectangle([-40, 480, 400, 610], 30, fill=(120, 140, 200, 255))
    d.rounded_rectangle([400, 420, 530, 490], 25, fill=(245, 245, 255, 255))
    d.rounded_rectangle([530, 360, 590, 660], 18, fill=(110, 80, 70, 255))
    s.add("dust", motes(103, 50, (255, 230, 200, 140)), -0.25, RISE(H, 30))
    return s


def bedroom_night_reverse():
    return night_of(bedroom_reverse, (1120, 330), [((100, 387), 0.75), ((750, 330), 0.98)])


# -- cafe --------------------------------------------------------------------

def cafe_reverse():
    """From the window seats, looking at the bar: the espresso machine, the
    chalk menu, the pastry case, the three tables now in front of the bar.
    The big window (and its blue daylight) is behind the camera on the right."""
    back = gradient(W, H, (120, 80, 60), (170, 120, 90))
    d = ImageDraw.Draw(back)
    d.rectangle([0, 540, W, H], fill=(90, 60, 45))
    s = Scene(back, 1.0)
    board, d = s.new("menu", 0.95)
    d.rectangle([470, 90, 830, 230], fill=(40, 35, 30, 255), outline=(150, 110, 80, 255), width=6)
    f = font(26)
    for i, (a, b) in enumerate([("coffee", "3.20"), ("the same", "3.20"), ("tea", "2.80")]):
        d.text((495, 102 + i * 40), a, fill=(240, 235, 220, 255), font=f)
        d.text((740, 102 + i * 40), b, fill=(240, 235, 220, 255), font=f)
    bar, d = s.new("bar", 0.7)
    d.rectangle([80, 370, 1200, 395], fill=(200, 170, 140, 255))
    d.rectangle([90, 395, 1190, 560], fill=(90, 60, 45, 255))
    for x in range(120, 1180, 120):
        d.rectangle([x, 410, x + 90, 545], outline=(110, 75, 55, 255), width=4)
    d.rounded_rectangle([250, 260, 430, 372], 12, fill=(190, 190, 200, 255))   # espresso machine
    d.rectangle([280, 330, 400, 345], fill=(80, 80, 90, 255))
    for x in (300, 370):
        d.rectangle([x, 345, x + 14, 360], fill=(60, 60, 70, 255))
    for k in range(4):
        d.rounded_rectangle([470 + k * 8, 352 - k * 20, 520 + k * 8, 372 - k * 20], 6,
                            fill=(250, 250, 250, 255))   # stacked cups
    d.rectangle([720, 290, 980, 372], fill=(200, 225, 230, 255), outline=(160, 140, 120, 255), width=4)
    for k, c in enumerate([(220, 160, 80), (180, 110, 70), (230, 190, 120), (200, 140, 90)]):
        d.ellipse([740 + k * 58, 335, 790 + k * 58, 365], fill=c + (255,))
    lamps, d = s.new("lamps", 0.6, SWAY(2, 0, 5))
    for x in range(0, W, 200):
        d.line([x + 100, 0, x + 100, 70], fill=(40, 30, 25, 255), width=3)
        d.ellipse([x + 80, 70, x + 120, 110], fill=(255, 220, 150, 255))
    for i, x in enumerate(range(0, W, 200)):
        s.add(f"lampglow{i}", light((x + 100, 95), 90, (255, 210, 140), 110), 0.62, PULSE(0.6, 3 + i % 3))
    s.add("window light", window_patch([(760, 580), (1200, 580), (1280, 715), (700, 715)], (170, 200, 235),
                                       70, panes=(3, 1)), 0.4, PULSE(0.85, 10))
    tables, d = s.new("tables", 0.45)
    for x in (180, 640, 1100):
        d.ellipse([x - 95, 520, x + 95, 556], fill=(200, 170, 140, 255))
        d.rectangle([x - 8, 552, x + 8, 660], fill=(60, 45, 35, 255))
        d.rounded_rectangle([x - 6, 496, x + 26, 524], 6, fill=(250, 250, 250, 255))
    s.add("steam", motes(104, 16, (255, 255, 255, 110), 4, 220, 520), 0.4, RISE(160, 6))
    return s


def cafe_corner():
    """The cafe as in bg cafe, filmed from the end of the bar: the espresso
    machine and the cups blur across the bottom right."""
    s = cafe()
    bar, d = s.new("bar end", -0.3)
    d.rectangle([880, 560, W, H], fill=(90, 60, 45, 255))
    d.rectangle([860, 535, W, 565], fill=(200, 170, 140, 255))
    d.rounded_rectangle([1060, 300, 1320, 545], 18, fill=(190, 190, 200, 255))
    d.rectangle([1090, 440, 1320, 470], fill=(80, 80, 90, 255))
    for k in range(3):
        d.rounded_rectangle([900 + k * 10, 500 - k * 30, 980 + k * 10, 535 - k * 30], 8, fill=(250, 250, 250, 255))
    s.layers[-1][1] = s.layers[-1][1].filter(ImageFilter.GaussianBlur(5))
    s.add("machine steam", motes(105, 14, (255, 255, 255, 120), 6, 160, 320), -0.32, RISE(180, 4))
    return s


# -- park --------------------------------------------------------------------

def park_reverse():
    """Up the hill, looking back the way the path came: the town on the
    horizon, the big tree now on the left, the pond and its bench on the
    right, the path running down the middle towards the camera."""
    back = gradient(W, H, (110, 170, 235), (225, 240, 250))
    s = Scene(back, 1.4)
    clouds, d = s.new("clouds", 1.3, SWAY(12, 0, 25))
    for x, y in [(200, 120), (700, 70), (1080, 110)]:
        for dx, dy, r in [(0, 0, 40), (40, 10, 30), (-40, 12, 28)]:
            d.ellipse([x + dx - r, y + dy - r, x + dx + r, y + dy + r], fill=(255, 255, 255, 255))
    town, d = s.new("town", 1.0)
    rng = np.random.default_rng(111)
    x = 0
    while x < W:
        bw, bh = int(rng.integers(50, 110)), int(rng.integers(50, 140))
        c = tuple(int(v) for v in rng.integers(150, 190, 3))
        d.rectangle([x, 430 - bh, x + bw, 440], fill=(c[0] - 20, c[1] - 5, c[2] + 20, 255))
        x += bw + 4
    far, d = s.new("far hill", 0.9)
    d.ellipse([480, 400, 1580, 920], fill=(110, 170, 90, 255))
    near, d = s.new("near hill", 0.5)
    d.ellipse([-320, 430, 780, 960], fill=(95, 155, 80, 255))
    d.ellipse([700, 470, 1500, 960], fill=(100, 160, 85, 255))
    d.polygon([(520, H), (760, H), (660, 450), (625, 450)], fill=(220, 200, 150, 255))
    pond, d = s.new("pond", 0.45, SWAY(2, 0, 8))
    d.ellipse([790, 520, 1160, 590], fill=(120, 175, 220, 255))
    d.arc([840, 535, 960, 565], 200, 340, fill=(200, 230, 250, 255), width=3)
    bench, d = s.new("bench", 0.32)
    d.rectangle([900, 470, 1080, 488], fill=(110, 75, 50, 255))
    d.rectangle([900, 500, 1080, 516], fill=(110, 75, 50, 255))
    for x in (910, 1060):
        d.rectangle([x, 488, x + 10, 545], fill=(70, 70, 75, 255))
    d.rectangle([1170, 330, 1180, 560], fill=(60, 60, 65, 255))   # lamp post
    d.ellipse([1158, 310, 1192, 340], fill=(250, 240, 200, 255))
    trees, d = s.new("trees", 0.3, SWAY(2, 0, 6))
    for x, y, r in [(1130, 330, 90), (230, 300, 110), (400, 360, 70)]:
        d.rectangle([x - 12, y, x + 12, y + 180], fill=(110, 75, 50, 255))
        d.ellipse([x - r, y - r, x + r, y + r // 2], fill=(60, 130, 70, 255))
    grass, d = s.new("grass", -0.2, SWAY(2, 0, 4))
    rng = np.random.default_rng(112)
    for _ in range(90):
        x = int(rng.integers(0, W))
        d.line([x, H, x + int(rng.integers(-10, 10)), H - int(rng.integers(20, 50))], fill=(70, 140, 70, 255), width=4)
    return s


# -- ward --------------------------------------------------------------------

def ward_reverse():
    """From the window, looking at the door: the bed is on the right now
    (the monitor at its left end), the visitor's chair, the whiteboard, the
    door with its little window, a sink in the corner. The barred window is
    behind the camera on the left; its striped light lies on the floor."""
    back = gradient(W, H, (215, 235, 232), (190, 215, 212))
    d = ImageDraw.Draw(back)
    d.rectangle([250, 150, 470, 520], fill=(175, 198, 205))       # the door
    d.rectangle([310, 200, 410, 280], fill=(235, 245, 245))       # its little window
    d.line([360, 200, 360, 280], fill=(175, 198, 205), width=4)
    d.rectangle([430, 330, 450, 345], fill=(150, 160, 170))
    s = Scene(back, 1.0)
    s.add("corridor light", light((360, 240), 90, (240, 255, 255), 120), 0.98, PULSE(0.85, 0.4))
    board, d = s.new("whiteboard", 0.95)
    d.rectangle([495, 100, 665, 235], fill=(250, 250, 250, 255), outline=(160, 170, 175, 255), width=5)
    f = font(22)
    for i, line in enumerate(["Nurse: Hale", "Dr: Okafor", "Today: rest"]):
        d.text((510, 112 + i * 38), line, fill=(70, 100, 150, 255), font=f)
    sink, d = s.new("sink", 0.9)
    d.rectangle([40, 300, 170, 400], fill=(225, 235, 238, 255), outline=(170, 180, 185, 255), width=4)
    d.rectangle([30, 420, 190, 445], fill=(240, 245, 245, 255))
    d.rectangle([60, 445, 160, 520], fill=(200, 210, 212, 255))
    floor, d = s.new("floor", 0.6)
    d.rectangle([0, 520, W, H], fill=(170, 190, 195, 255))
    for x in range(0, W, 120):
        d.line([x + 40, 520, x, H], fill=(160, 180, 185, 255), width=2)
    s.add("window light", window_patch([(30, 545), (560, 545), (640, 715), (0, 715)], (235, 245, 250), 110,
                                       panes=(6, 1), bar=30), 0.58, PULSE(0.85, 9))
    chair, d = s.new("chair", 0.4)
    d.rounded_rectangle([520, 400, 620, 470], 12, fill=(120, 150, 180, 255))
    d.rectangle([515, 470, 625, 488], fill=(110, 140, 170, 255))
    for x in (522, 610):
        d.rectangle([x, 488, x + 8, 570], fill=(150, 160, 170, 255))
    mon, d = s.new("monitor", 0.3)
    d.rectangle([700, 330, 760, 560], fill=(200, 205, 210, 255))
    d.rounded_rectangle([680, 250, 780, 330], 10, fill=(60, 70, 80, 255))
    s.add("heartbeat", Image.new("RGBA", (W, H)), 0.29)
    hb = s.layers[-1][1]
    ImageDraw.Draw(hb).line([690, 300, 715, 300, 725, 270, 740, 320, 750, 300, 770, 300],
                            fill=(90, 255, 140, 255), width=3)
    s.layers[-1][3] = PULSE(0.2, 1.1)
    bed, d = s.new("bed", 0.25)
    d.rounded_rectangle([800, 400, 1300, 600], 20, fill=(250, 250, 250, 255))
    d.rounded_rectangle([1110, 380, 1260, 440], 22, fill=(235, 240, 245, 255))   # pillow, head end
    d.rectangle([800, 380, 830, 640], fill=(160, 170, 180, 255))
    d.rectangle([840, 450, 1290, 470], fill=(200, 210, 220, 255))   # folded blanket edge
    s.add("fluorescent", light((640, 0), 600, (230, 255, 255), 60), -0.1, PULSE(0.85, 0.35))
    return s


def ward_door():
    """The ward room as in bg ward, filmed from the corridor through its
    open door."""
    s = ward()
    s.add("doorway", door_frame((200, 215, 212), (150, 175, 185), (210, 60, 1060),
                                leaf=[(1086, 34), (1200, -20), (1200, H), (1086, H)],
                                extra=lambda d: d.rectangle([1110, 160, 1180, 250], fill=(225, 238, 238, 255))),
          -0.25)
    return s


def ward_night_reverse():
    s = recolor(ward_reverse(), (0.3, 0.38, 0.5), (0, 5, 15))
    s.add("monitor glow", light((730, 290), 140, (90, 255, 160), 120), 0.29, PULSE(0.4, 1.1))
    s.add("corridor glow", light((360, 240), 110, (230, 250, 255), 110), 0.97, PULSE(0.8, 5))
    return s


# -- office ------------------------------------------------------------------

def office_reverse():
    """From the glass wall, looking back into the office: the long low
    sideboard under the seven principle cards, the doorway on the left, the
    table with the model world now on the right under its lamp. The glass
    wall is behind the camera on the left; its daylight floods the floor."""
    back = gradient(W, H, (246, 244, 238), (226, 222, 214))
    d = ImageDraw.Draw(back)
    d.rectangle([140, 90, 330, 470], fill=(240, 238, 232))        # a doorway to a brighter room
    d.rectangle([140, 90, 330, 470], outline=(215, 210, 200), width=6)
    s = Scene(back, 0.9)
    s.add("next room", light((235, 260), 160, (255, 255, 245), 110), 0.88, PULSE(0.9, 9))
    cards, d = s.new("principles", 0.8)
    cols = [(230, 120, 40), (120, 160, 210), (200, 200, 195), (60, 60, 60), (150, 190, 140),
            (230, 190, 90), (190, 150, 190)]
    for k, c in enumerate(cols):
        x = 450 + k * 100
        d.rectangle([x, 95, x + 80, 175], fill=(252, 252, 250, 255), outline=(220, 216, 208, 255), width=3)
        d.ellipse([x + 22, 117, x + 58, 153], fill=c + (255,))
    floor, d = s.new("floor", 0.5)
    d.rectangle([0, 470, W, H], fill=(205, 198, 186, 255))
    s.add("daylight", window_patch([(0, 490), (520, 490), (600, 715), (0, 715)], (255, 255, 245), 120,
                                   panes=(4, 1), bar=18), 0.48, PULSE(0.9, 12))
    side, d = s.new("sideboard", 0.45)
    d.rectangle([420, 380, 1180, 470], fill=(250, 250, 248, 255))
    d.line([420, 425, 1180, 425], fill=(225, 222, 215, 255), width=3)
    d.rounded_rectangle([470, 330, 600, 380], 6, fill=(235, 230, 220, 255))   # the radio
    for x in range(482, 545, 10):
        d.line([x, 338, x, 372], fill=(180, 175, 165, 255), width=3)
    d.ellipse([555, 340, 585, 370], fill=(230, 120, 40, 255))
    d.rounded_rectangle([660, 320, 700, 380], 4, fill=(60, 60, 60, 255))      # a calculator
    d.rounded_rectangle([1050, 300, 1090, 380], 14, fill=(200, 200, 195, 255))  # a vase
    table, d = s.new("table", 0.15)
    d.rectangle([700, 440, 1210, 460], fill=(60, 60, 60, 255))
    for x in (730, 1190):
        d.rectangle([x, 460, x + 10, 640], fill=(60, 60, 60, 255))
    model, d = s.new("model world", 0.05, BREATHE(0.03, 5))
    d.ellipse([860, 330, 1020, 440], outline=(240, 120, 40, 255), width=5)
    d.ellipse([900, 360, 980, 410], fill=(240, 120, 40, 255))
    lamp, d = s.new("lamp", -0.1)
    d.line([940, 0, 940, 200], fill=(70, 70, 70, 255), width=3)
    d.chord([890, 190, 990, 250], 180, 360, fill=(70, 70, 70, 255))
    s.add("lamplight", light((940, 260), 180, (255, 230, 170), 90), -0.12, PULSE(0.8, 6))
    return s


# -- street ------------------------------------------------------------------

def street_reverse():
    """From across the road, looking back: the other row of houses (the
    cafe's blue window among them), the same wire, now on the far side with
    the same three birds, evenly spaced, at the right."""
    back = gradient(W, H, (150, 180, 220), (230, 220, 210))
    s = Scene(back, 1.4)
    town, d = s.new("buildings", 0.8)
    rng = np.random.default_rng(12)
    xs, k = 0, 0
    while xs < W:
        bw, bh = int(rng.integers(140, 260)), int(rng.integers(220, 420))
        col = tuple(int(c) for c in rng.integers(120, 200, 3)) + (255,)
        d.rectangle([xs, 520 - bh, xs + bw, 520], fill=col)
        for wx in range(xs + 20, xs + bw - 30, 50):
            for wy in range(520 - bh + 30, 420, 60):
                d.rectangle([wx, wy, wx + 26, wy + 34], fill=(240, 240, 220, 255))
        if k == 1:   # the cafe's front, its window and name
            d.rectangle([xs + 10, 430, xs + bw - 10, 520], fill=(60, 90, 110, 255))
            d.rectangle([xs + 10, 405, xs + bw - 10, 428], fill=(120, 80, 60, 255))
            d.text((xs + 18, 405), "THE SAME CAFE", fill=(255, 230, 180, 255), font=font(18))
        else:
            d.rectangle([xs + bw // 2 - 20, 450, xs + bw // 2 + 20, 520], fill=(90, 70, 60, 255))
        xs += bw + 6
        k += 1
    wire, d = s.new("wire", 0.55)
    d.line([0, 260, W, 230], fill=(40, 40, 40, 255), width=3)
    for bx in (870, 910, 950):
        y = 260 - 30 * (bx + 15) / W
        d.ellipse([bx, y - 9, bx + 30, y + 11], fill=(50, 50, 60, 255))
    road, d = s.new("road", 0.35)
    d.rectangle([0, 520, W, H], fill=(90, 90, 100, 255))
    for x in range(0, W, 160):
        d.rectangle([x + 40, 590, x + 120, 602], fill=(230, 230, 230, 255))
    curb, d = s.new("sidewalk", -0.15)
    d.rectangle([0, 668, W, H], fill=(175, 172, 168, 255))
    d.rectangle([0, 660, W, 670], fill=(150, 148, 145, 255))
    return s


def street_rain_reverse():
    s = recolor(street_reverse(), (0.7, 0.75, 0.85))
    s.add("rain far", rain(161, 200, (170, 180, 210, 160), 18), 0.6, FALL(H, 1.5))
    s.add("rain near", rain(162, 120, (200, 210, 235, 210), 34), -0.3, FALL(H, 0.85))
    return s


def street_dusk_reverse():
    s = recolor(street_reverse(), (1.0, 0.7, 0.6), (20, 0, 10))
    s.add("sunset", light((640, 520), 700, (255, 150, 90), 110), 1.1, PULSE(0.8, 10))
    return s


# -- angel ops -----------------------------------------------------------------

def command_reverse():
    """Angel ops from the wall of worlds, looking back at the deck: tiers of
    operators at their desks, the great doors, the commander's dais in the
    middle. The screens are behind the camera; their colours (and the red
    alarm) wash over the floor."""
    back = gradient(W, H, (255, 250, 235), (225, 210, 170))
    d = ImageDraw.Draw(back)
    for x in range(-200, W + 200, 90):
        d.line([W // 2, 260, x, H], fill=(230, 210, 160), width=2)
    d.rounded_rectangle([540, 90, 740, 470], 90, fill=(250, 240, 210), outline=(220, 180, 80), width=6)
    d.line([640, 120, 640, 470], fill=(220, 180, 80), width=4)
    for x in (380, 900):
        d.rectangle([x - 25, 0, x + 25, 470], fill=(245, 240, 225))
    s = Scene(glow(back, (W // 2, 280), 360, (60, 50, 20), 0.5), 1.2)
    floor, d = s.new("floor", 0.65)
    d.rectangle([0, 470, W, H], fill=(235, 220, 180, 255))
    for depth, y, n, size in [(0.6, 470, 9, 0.6), (0.45, 530, 7, 0.8), (0.3, 600, 5, 1.0)]:
        tier, d = s.new(f"tier{depth}", depth)
        span = W / n
        for k in range(n):
            if depth == 0.3 and k == n // 2:
                continue   # the gap in front of the dais
            x = span * (k + 0.5)
            w = 60 * size
            d.ellipse([x - w * 0.9, y - 70 * size, x - 6, y - 15 * size], fill=(255, 255, 255, 200))
            d.ellipse([x + 6, y - 70 * size, x + w * 0.9, y - 15 * size], fill=(255, 255, 255, 200))
            d.rectangle([x - 14 * size, y - 55 * size, x + 14 * size, y - 10 * size], fill=(250, 245, 230, 255))
            d.ellipse([x - 12 * size, y - 80 * size, x + 12 * size, y - 56 * size], fill=(240, 225, 215, 255))
            d.ellipse([x - 16 * size, y - 92 * size, x + 16 * size, y - 84 * size], outline=(255, 210, 90, 255),
                      width=2)
            d.rounded_rectangle([x - w, y - 20 * size, x + w, y + 30 * size], 6, fill=(240, 228, 195, 255),
                                outline=(220, 180, 80, 255), width=2)
            d.rectangle([x - w * 0.5, y - 18 * size, x + w * 0.5, y - 8 * size], fill=(170, 200, 230, 255))
    dais, d = s.new("dais", 0.15)
    d.rounded_rectangle([470, 590, 810, 640], 12, fill=(245, 238, 215, 255), outline=(220, 180, 80, 255), width=5)
    d.rectangle([500, 640, 780, 700], fill=(235, 225, 195, 255))
    screens = soft_shape(lambda dd: [dd.ellipse([x - 260, 560, x + 260, 820], fill=255) for x in (200, 640, 1080)],
                         (150, 190, 230), 70, 40)
    s.add("screen light", screens, 0.1, PULSE(0.7, 5))
    s.add("alarm", light((760, 690), 260, (230, 60, 60), 90), 0.05, PULSE(0.15, 1.4))
    s.add("radiance", light((W // 2, 280), 520, (255, 240, 200), 60), -0.2, PULSE(0.6, 7))
    return s


# -- clinic ------------------------------------------------------------------

def clinic_reverse():
    """Dr. Okafor's room from the poster wall, looking back: her desk under
    the window on the left, the patient's armchair (with tissues) in the
    middle, the plant by the door, the door with her name on the right. The
    bookshelf and the breathing poster are behind the camera."""
    back = gradient(W, H, (230, 225, 215), (205, 200, 190))
    d = ImageDraw.Draw(back)
    d.rectangle([110, 100, 430, 320], fill=(250, 250, 245))
    back.paste(gradient(290, 190, (170, 210, 240), (215, 235, 245)), (125, 115))
    d.line([270, 115, 270, 305], fill=(250, 250, 245), width=10)
    d.rectangle([0, 500, W, H], fill=(140, 120, 100))
    s = Scene(back, 1.0)
    s.add("window light", light((270, 210), 260, (255, 250, 230), 90), 0.95, PULSE(0.85, 9))
    door, d = s.new("door", 0.9)
    d.rectangle([930, 140, 1120, 505], fill=(170, 130, 95, 255), outline=(120, 90, 60, 255), width=8)
    d.rectangle([975, 200, 1075, 235], fill=(240, 235, 220, 255))
    d.text((985, 204), "Dr. Okafor", fill=(70, 70, 70, 255), font=font(20))
    d.ellipse([1085, 320, 1103, 338], fill=(210, 190, 120, 255))
    d.rectangle([1170, 150, 1180, 505], fill=(90, 65, 45, 255))     # coat rack
    d.rounded_rectangle([1145, 170, 1205, 320], 24, fill=(200, 120, 70, 255))
    desk, d = s.new("desk", 0.55)
    d.rounded_rectangle([90, 400, 520, 440], 8, fill=(110, 80, 55, 255))
    d.rectangle([110, 440, 135, 560], fill=(90, 65, 45, 255))
    d.rectangle([475, 440, 500, 560], fill=(90, 65, 45, 255))
    d.rounded_rectangle([230, 330, 330, 400], 20, fill=(70, 70, 80, 255))   # her chair's back
    d.rectangle([380, 380, 460, 400], fill=(245, 245, 235, 255))           # notes
    plant, d = s.new("plant", 0.5, BREATHE(0.02, 4))
    d.ellipse([820, 400, 880, 460], fill=(90, 150, 90, 255))
    d.rectangle([835, 455, 865, 500], fill=(160, 100, 70, 255))
    chair, d = s.new("armchair", 0.25)
    d.rounded_rectangle([560, 380, 800, 520], 40, fill=(120, 150, 180, 255))
    d.rounded_rectangle([540, 470, 820, 580], 30, fill=(110, 140, 170, 255))
    for x in (550, 790):
        d.rectangle([x, 580, x + 14, 630], fill=(80, 80, 90, 255))
    d.rectangle([830, 520, 900, 600], fill=(110, 80, 55, 255))           # side table
    d.rounded_rectangle([838, 490, 892, 520], 6, fill=(140, 190, 220, 255))
    d.polygon([(855, 490), (865, 474), (875, 490)], fill=(255, 255, 255, 255))
    return s


SCENES.update({
    "bg kitchen reverse": kitchen_reverse, "bg kitchen door": kitchen_door,
    "bg kitchen night reverse": kitchen_night_reverse,
    "bg room reverse": room_reverse, "bg room corner": room_corner,
    "bg room night reverse": room_night_reverse,
    "bg bedroom reverse": bedroom_reverse, "bg bedroom night reverse": bedroom_night_reverse,
    "bg cafe reverse": cafe_reverse, "bg cafe corner": cafe_corner,
    "bg park reverse": park_reverse,
    "bg ward reverse": ward_reverse, "bg ward door": ward_door, "bg ward night reverse": ward_night_reverse,
    "bg office reverse": office_reverse,
    "bg street reverse": street_reverse, "bg street rain reverse": street_rain_reverse,
    "bg street dusk reverse": street_dusk_reverse,
    "bg command reverse": command_reverse, "bg clinic reverse": clinic_reverse,
})


# ---------------------------------------------------------------- the light and the shadow
# Places for the shadow-realm thread: the hall outside the bathroom door
# (end of ch1), the stairwell they carry him down, the ward garden the
# walkers come over (ch3), Osric's workshop inside the mirror planet and
# the mirror planet seen from outside (ch2 to ch4). The walkers ("Herons")
# and the troopers ("Understudies") are Osric's own designs: stilt legs and a
# round lamp-cabin like a diving bell; dark plate armour with a round mirror
# for a face.

def bathroom_door():
    """The flat's hall, facing the bathroom door: shut, a strip of light under it."""
    back = gradient(W, H, (236, 214, 190), (212, 188, 162))
    d = ImageDraw.Draw(back)
    wood_floor(d, 560, (120, 84, 60), (104, 72, 52))
    s = Scene(back, 1.0)
    door, d = s.new("door", 0.8)
    d.rectangle([540, 90, 880, 562], fill=(250, 245, 235, 255))          # frame
    d.rectangle([566, 112, 854, 562], fill=(238, 232, 222, 255))         # the door
    for y0, y1 in ((150, 330), (370, 530)):
        d.rectangle([600, y0, 820, y1], outline=(222, 214, 202, 255), width=6)
    d.ellipse([808, 340, 830, 362], fill=(190, 170, 120, 255))           # handle
    d.rectangle([800, 300, 838, 318], fill=(250, 250, 250, 255))         # the lock's little window
    d.pieslice([808, 302, 830, 324], 180, 360, fill=(200, 50, 40, 255))  # red: engaged
    s.add("light under the door", light((710, 562), 170, (255, 248, 225), 200), 0.79, PULSE(0.7, 3))
    coats, d = s.new("coats", 0.6, SWAY(1, 0, 9))
    d.rectangle([130, 200, 360, 214], fill=(110, 80, 55, 255))
    for x, c in ((160, (60, 80, 120)), (240, (170, 90, 60)), (315, (40, 40, 45))):
        d.ellipse([x - 8, 200, x + 8, 216], fill=(120, 90, 60, 255))
        d.rounded_rectangle([x - 40, 214, x + 40, 470], 30, fill=c + (255,))
    rug, d = s.new("rug", 0.3)
    d.polygon([(420, 580), (980, 580), (1100, H), (300, H)], fill=(150, 60, 55, 255))
    d.polygon([(450, 595), (950, 595), (1050, H), (340, H)], outline=(210, 170, 110, 255))
    s.add("doorway", door_frame((236, 214, 190), (250, 245, 235), (40, 24, 1150), shade=0.8), -0.25)
    return s


def bathroom_door_siren():
    s = recolor(bathroom_door(), (0.62, 0.66, 0.85), (0, 0, 12))
    s.add("siren", light((60, 120), 700, (60, 110, 255), 170), 0.9, PULSE(0.0, 0.7))
    s.add("siren near", light((1250, 300), 520, (60, 110, 255), 120), -0.2, PULSE(0.0, 0.7))
    return s


def stairwell():
    """An old stairwell, going down, blue light coming up from the street door."""
    back = gradient(W, H, (205, 196, 176), (170, 160, 140))
    d = ImageDraw.Draw(back)
    d.rectangle([0, 380, W, H], fill=(120, 135, 120))                    # the painted dado
    d.line([0, 380, W, 380], fill=(90, 100, 90), width=6)
    d.rectangle([980, 90, 1140, 330], fill=(120, 150, 200))              # landing window
    d.line([1060, 90, 1060, 330], fill=(230, 225, 210), width=8)
    s = Scene(back, 1.1)
    s.add("street light", light((1060, 260), 260, (70, 120, 255), 170), 1.05, PULSE(0.1, 0.7))
    doors, d = s.new("doors", 0.75)
    for x in (150, 700):
        d.rectangle([x, 150, x + 170, 470], fill=(110, 80, 55, 255))
        d.ellipse([x + 140, 300, x + 156, 316], fill=(200, 180, 120, 255))
        d.rectangle([x + 60, 200, x + 110, 220], fill=(220, 210, 180, 255))
    steps, d = s.new("steps", 0.45)
    for k in range(9):
        y = 470 + k * 30
        d.polygon([(380 - k * 40, y), (1280, y), (1280, y + 30), (380 - k * 40 - 40, y + 30)],
                  fill=(150 - k * 6, 140 - k * 6, 130 - k * 6, 255))
        d.line([380 - k * 40, y, 1280, y], fill=(200, 190, 175, 255), width=3)
    rail, d = s.new("banister", 0.15)
    d.line([1280, 300, 120, 700], fill=(80, 55, 40, 255), width=22)
    for k in range(10):
        x = 1240 - k * 115
        y = 314 + k * 40
        d.line([x, y, x, y + 260], fill=(70, 50, 35, 255), width=8)
    s.add("siren", light((640, H + 100), 620, (60, 110, 255), 130), -0.1, PULSE(0.0, 0.7))
    return s


def heron(d, cx, top, scale, lamp=(255, 230, 160)):
    """Osric's walker: a round cabin like a diving bell, slung low between
    four thin stilt legs that bend backwards at the knee."""
    body = int(70 * scale)
    leg = (55, 60, 75, 255)
    for k, dx in enumerate((-2.4, -1.0, 1.0, 2.4)):
        kx = cx + int(dx * body * 0.9)
        ky = top - int(body * 0.9)
        fx = cx + int(dx * body * 1.5)
        d.line([cx + int(dx * body * 0.35), top, kx, ky], fill=leg, width=max(3, int(9 * scale)))
        d.line([kx, ky, fx, H + 40], fill=leg, width=max(3, int(8 * scale)))
        d.ellipse([kx - 8 * scale, ky - 8 * scale, kx + 8 * scale, ky + 8 * scale], fill=(80, 85, 100, 255))
    d.ellipse([cx - body, top - body, cx + body, top + body], fill=(70, 75, 92, 255))
    d.ellipse([cx - body * 0.8, top - body * 0.8, cx + body * 0.8, top + body * 0.2], fill=(90, 96, 115, 255))
    for k in range(-2, 3):                                               # rivets
        d.ellipse([cx + k * body * 0.35 - 3, top + body * 0.45 - 3, cx + k * body * 0.35 + 3,
                   top + body * 0.45 + 3], fill=(150, 150, 160, 255))
    d.ellipse([cx - body * 0.35, top - body * 0.35, cx + body * 0.35, top + body * 0.35], fill=lamp + (255,))
    d.line([cx, top - body, cx, top - body * 1.6], fill=leg, width=4)   # periscope
    d.rectangle([cx, top - body * 1.6, cx + body * 0.4, top - body * 1.45], fill=leg)


def understudy(d, x, y, scale=1.0):
    """A trooper: dark plates over a shadow, a round mirror for a face."""
    s = scale
    d.rounded_rectangle([x - 26 * s, y - 60 * s, x + 26 * s, y + 20 * s], int(12 * s), fill=(30, 32, 40, 255))
    d.ellipse([x - 22 * s, y - 104 * s, x + 22 * s, y - 58 * s], fill=(35, 38, 48, 255))
    d.ellipse([x - 15 * s, y - 96 * s, x + 15 * s, y - 66 * s], fill=(200, 210, 225, 255))   # mirror visor
    d.ellipse([x - 8 * s, y - 92 * s, x + 2 * s, y - 82 * s], fill=(250, 250, 255, 255))
    d.rectangle([x - 22 * s, y + 20 * s, x - 6 * s, y + 80 * s], fill=(28, 30, 38, 255))
    d.rectangle([x + 6 * s, y + 20 * s, x + 22 * s, y + 80 * s], fill=(28, 30, 38, 255))
    d.rectangle([x - 34 * s, y - 52 * s, x - 24 * s, y + 6 * s], fill=(40, 42, 52, 255))
    d.rectangle([x + 24 * s, y - 52 * s, x + 34 * s, y + 6 * s], fill=(40, 42, 52, 255))


def ward_yard():
    """Night, through the ward's barred window: the garden, the wall, and the
    walkers stepping over it, the troopers on the lawn."""
    back = gradient(W, H, (14, 18, 38), (40, 46, 70))
    s = Scene(back, 1.4)
    sky_stars(s, "stars", 1.38, 40, 5, (0, 0, W, 300), seed=41, faint=60)
    town, d = s.new("town", 1.2)
    for k in range(16):
        x = k * 85
        h = 60 + (k * 37) % 70
        d.rectangle([x, 470 - h, x + 70, 470], fill=(25, 28, 45, 255))
        if k % 3 == 0:
            d.rectangle([x + 20, 470 - h + 20, x + 32, 470 - h + 32], fill=(230, 200, 120, 255))
    walkers, d = s.new("walkers", 0.95, SWAY(4, 2, 5))
    heron(d, 330, 170, 1.0)
    heron(d, 960, 120, 1.25)
    s.add("searchlight", light((960, 120), 420, (255, 230, 170), 90), 0.94, PULSE(0.4, 3))
    beam, d = blank()
    d.polygon([(940, 140), (980, 140), (760, 560), (560, 560)], fill=(255, 240, 200, 70))
    s.add("beam", beam.filter(ImageFilter.GaussianBlur(10)), 0.9, SWAY(30, 0, 6))
    wall, d = s.new("garden wall", 0.7)
    d.rectangle([0, 470, W, 540], fill=(70, 62, 66, 255))
    for x in range(0, W, 60):
        d.line([x, 470, x, 540], fill=(55, 48, 52, 255), width=2)
    lawn, d = s.new("lawn", 0.5)
    d.rectangle([0, 540, W, H], fill=(28, 50, 40, 255))
    d.ellipse([140, 300, 300, 520], fill=(30, 52, 42, 255))                # a tree by the wall
    d.rectangle([210, 470, 230, 560], fill=(50, 40, 35, 255))
    troops, d = s.new("understudies", 0.4, SWAY(2, 0, 4))
    for x, sc in ((520, 0.9), (640, 1.0), (760, 0.9), (420, 0.75), (870, 0.75)):
        understudy(d, x, 590, sc)
    bars, d = s.new("bars", 0.15)
    for x in range(80, W, 130):
        d.rectangle([x, 0, x + 18, H], fill=(110, 118, 130, 255))
    d.rectangle([0, 340, W, 356], fill=(110, 118, 130, 255))
    sill, d = s.new("sill", -0.15)
    d.rectangle([0, 640, W, H], fill=(150, 160, 170, 255))
    return s


def shadowbase():
    """Inside the mirror planet: Osric's workshop. The great telescope mirror
    he came through, shadows of borrowed things hanging on wires, a bench,
    and searchlights pointed up at a light that's on the wrong side."""
    back = gradient(W, H, (22, 25, 36), (48, 52, 66))
    s = Scene(back, 1.3)
    s.add("the light above", light((640, -60), 520, (255, 248, 220), 150), 1.28, PULSE(0.6, 8))
    mirror_, d = s.new("telescope mirror", 1.0, PULSE(0.85, 6))
    d.ellipse([420, 60, 860, 500], fill=(150, 160, 180, 255))
    d.ellipse([440, 80, 840, 480], fill=(190, 200, 215, 255))
    for a, b in (((520, 140), (640, 300)), ((640, 300), (600, 470)), ((640, 300), (790, 230)), ((640, 300), (470, 330))):
        d.line([a, b], fill=(110, 120, 140, 255), width=3)
    beams, d = blank()
    for x0, x1 in ((150, 400), (1130, 880)):
        d.polygon([(x0 - 20, H), (x0 + 20, H), (x1 + 40, 0), (x1 - 40, 0)], fill=(230, 235, 255, 60))
    s.add("searchlights", beams.filter(ImageFilter.GaussianBlur(12)), 0.85, SWAY(12, 0, 9))
    things, d = s.new("borrowed shadows", 0.6, SWAY(4, 1, 6))
    sh = (12, 14, 20, 235)
    for x, top in ((140, 0), (300, 0), (980, 0), (1140, 0)):
        d.line([x, top, x, 160], fill=(80, 85, 100, 255), width=2)
    d.ellipse([100, 160, 180, 240], outline=sh, width=10)                 # a bicycle, missing a wheel
    d.line([140, 200, 220, 170], fill=sh, width=8)
    d.ellipse([260, 160, 340, 240], fill=sh)                               # a film reel
    for k in range(5):
        a = k * 2 * math.pi / 5
        d.ellipse([300 + 22 * math.cos(a) - 9, 200 + 22 * math.sin(a) - 9, 300 + 22 * math.cos(a) + 9,
                   200 + 22 * math.sin(a) + 9], fill=(48, 52, 66, 255))
    d.pieslice([930, 150, 1030, 230], 180, 360, fill=sh)                   # an umbrella, open
    d.line([980, 190, 980, 260], fill=sh, width=5)
    d.rounded_rectangle([1100, 160, 1180, 220], 20, fill=sh)               # a teapot with no spout
    walker, d = s.new("walker leg", 0.45)
    d.line([1280, 330, 1060, 120], fill=(55, 60, 75, 255), width=26)
    d.line([1060, 120, 1000, 620], fill=(55, 60, 75, 255), width=22)
    d.ellipse([1040, 100, 1080, 140], fill=(80, 85, 100, 255))
    bench, d = s.new("bench", 0.2)
    d.rectangle([60, 560, 760, 590], fill=(70, 60, 55, 255))
    d.rectangle([90, 590, 110, H], fill=(55, 48, 44, 255))
    d.rectangle([710, 590, 730, H], fill=(55, 48, 44, 255))
    d.rectangle([200, 520, 330, 560], fill=(90, 95, 110, 255))            # a radio set
    d.ellipse([220, 530, 250, 556], fill=(160, 150, 120, 255))
    d.rectangle([420, 540, 560, 560], fill=(220, 215, 200, 255))          # drawings
    understudy(d, 900, 600, 1.1)
    s.add("lamp", light((640, 540), 140, (255, 220, 150), 170), 0.19, PULSE(0.8, 2))
    s.add("ash", motes(91, 60, (190, 195, 210, 150), 3), -0.2, FALL(H, 9))
    return s


def mirrorplanet():
    """The origin of the shadow: a planet of mirror, turned away from the light."""
    back = gradient(W, H, (4, 4, 12), (18, 16, 32))
    s = Scene(back, 1.5)
    sky_stars(s, "stars", 1.48, 150, 6, (0, 0, W, H), seed=29, faint=100)
    s.add("sun", light((1200, 80), 360, (255, 245, 220), 160), 1.4, PULSE(0.85, 9))
    planet, d = s.new("mirror planet", 0.9, BREATHE(0.005, 10))
    d.ellipse([260, 160, 1020, 920], fill=(120, 128, 145, 255))
    d.ellipse([300, 190, 990, 880], fill=(165, 172, 188, 255))
    d.ellipse([420, 260, 700, 470], fill=(70, 120, 190, 150))             # a world reflected in it, faint and backwards
    d.ellipse([480, 300, 560, 360], fill=(80, 140, 90, 150))
    d.ellipse([300, 190, 990, 880], outline=(220, 228, 240, 255), width=4)
    s.add("glint", light((820, 300), 160, (255, 255, 255), 200), 0.85, PULSE(0.3, 4))
    base, d = s.new("base lights", 0.8, PULSE(0.5, 1.5))
    for x, y in ((610, 520), (640, 540), (670, 520), (640, 500)):
        d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=(255, 220, 150, 255))
    return s


SCENES.update({
    "bg bathroom door": bathroom_door, "bg bathroom door siren": bathroom_door_siren,
    "bg stairwell": stairwell, "bg ward yard": ward_yard,
    "bg shadowbase": shadowbase, "bg mirrorplanet": mirrorplanet,
})

"""Draw the art and compose the music for the demo game, "Snapshot"
(examples/demo). Everything is generated, so the game ships no binary art.

    python3 examples/make_demo_assets.py
"""

import json
import math
import os
import sys
import shutil
import subprocess
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scenes3d  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.join(HERE, "demo", "game")
W, H = 1280, 720
RNG = np.random.default_rng(7)


def font(size):
    for p in ("/System/Library/Fonts/Supplemental/Noteworthy.ttc",
              "/System/Library/Fonts/Supplemental/Arial.ttf",
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
    """Additive soft light."""
    layer = Image.new("RGB", img.size, (0, 0, 0))
    d = ImageDraw.Draw(layer)
    x, y = xy
    for i in range(12, 0, -1):
        r = radius * i / 12
        c = tuple(int(v * strength * (13 - i) / 12) for v in color)
        d.ellipse([x - r, y - r, x + r, y + r], fill=c)
    layer = layer.filter(ImageFilter.GaussianBlur(radius / 6))
    a = np.asarray(img, np.int32) + np.asarray(layer, np.int32)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def stars(d, n, ymax, seed=3):
    rng = np.random.default_rng(seed)
    for _ in range(n):
        x, y = rng.integers(0, W), rng.integers(0, ymax)
        r = int(rng.integers(1, 4))
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 230))


# ---------------------------------------------------------------- places
# The scenes themselves live in scenes3d.py, drawn as stereoscopic layers.


def main_menu():
    img = gradient(W, H, (20, 15, 45), (120, 60, 110))
    d = ImageDraw.Draw(img)
    stars(d, 160, H // 2)
    for i, (col, off) in enumerate([((40, 25, 70), 0), ((70, 35, 90), 160)]):
        pts = [(x, 520 + off // 2 + 50 * math.sin(x / 140 + i)) for x in range(0, W + 40, 40)]
        d.polygon(pts + [(W, H), (0, H)], fill=col)
    # a window frame splitting into copies
    for k in range(5):
        o = k * 14
        d.rectangle([520 + o, 140 - o, 760 + o, 380 - o], outline=(255, 220, 150, 255), width=3)
    return glow(img, (640, 260), 220, (90, 60, 30), 0.5)


# ---------------------------------------------------------------- people
# Faces are built from parts (eyes, brows, mouth, blush), so every character
# shares one readable set of moods. On the 3DS a sprite is about a third of
# its size here (roughly 120-210 px tall), so the parts are thick and simple.
# "neutral" is relaxed and pleasant on purpose: a soft little curve of a
# mouth, calm eyes, easy brows. Frowns are kept for moods that need them.

# mood: (eyes, brows, mouth, blush 0-3)
EXPRESSIONS = {
    "neutral":     ("open",      "relaxed",  "soft",    1),
    "smile":       ("open",      "lifted",   "smile",   1),
    "happy":       ("squint",    "lifted",   "happy",   2),
    "laugh":       ("closed",    "lifted",   "laugh",   2),
    "grin":        ("squint",    "relaxed",  "grin",    1),
    "curious":     ("open",      "curious",  "curious", 1),
    "thinking":    ("look_up",   "thinking", "side",    0),
    "surprised":   ("wide",      "high",     "o",       0),
    "awe":         ("sparkle",   "high",     "awe",     1),
    "worried":     ("open",      "worried",  "worried", 0),
    "sad":         ("droop",     "sad",      "sad",     0),
    "tired":       ("tired",     "low",      "tired",   0),
    "embarrassed": ("look_down", "worried",  "wobbly",  3),
    "tender":      ("soft",      "soft",     "tender",  2),
    "annoyed":     ("flat",      "angry",    "flat",    0),
    "determined":  ("firm",      "firm",     "set",     0),
}
MOODS = list(EXPRESSIONS)

WHITE = (255, 255, 255, 255)


def rgba(c, a=255):
    return tuple(c[:3]) + ((c[3],) if len(c) > 3 else (a,))


class Look:
    """Where a face sits on its sprite, how big its parts are, its colours."""

    def __init__(self, cx, ey, ex=45, erx=12, ery=15, brow_dy=32, my=248, ms=1.0,
                 eye=(45, 32, 32), lid=None, line=(150, 55, 65), brow=(60, 40, 40),
                 skin=(230, 190, 160), blush=(250, 150, 150), blush_cut=0,
                 cheek_dx=66, cheek_dy=40, pupil=None, extra=None):
        self.cx, self.ey, self.ex, self.erx, self.ery = cx, ey, ex, erx, ery
        self.brow_dy, self.my, self.ms = brow_dy, my, ms
        self.eye, self.lid = rgba(eye), rgba(lid or eye)
        self.line, self.brow, self.skin = rgba(line), rgba(brow), rgba(skin)
        self.blush, self.blush_cut = blush, blush_cut
        self.cheek_dx, self.cheek_y = cheek_dx, ey + cheek_dy
        self.pupil = pupil and rgba(pupil)   # a slit pupil instead of a shine
        self.extra = extra or {}              # moods only this character has

    def parts(self, mood):
        return self.extra.get(mood) or EXPRESSIONS[mood]


def _curve(x0, x1, y0, y1, bulge, n=10):
    """Points along a lid from (x0, y0) to (x1, y1), bowed up by `bulge`."""
    return [(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t - bulge * math.sin(math.pi * t))
            for t in (i / n for i in range(n + 1))]


def _lid(d, L, x, y, s, inner_y, outer_y, bulge=0, lw=6):
    """Lower an upper eyelid: cover the eye above a line, then draw the line."""
    rx, ry = L.erx, L.ery
    xo, xi = x + s * (rx + 5), x - s * (rx + 5)
    pts = _curve(xo, xi, outer_y, inner_y, bulge)
    top = y - ry - 10
    d.polygon(pts + [(xi, top), (xo, top)], fill=L.skin)
    d.line(pts, fill=L.lid, width=lw, joint="curve")


def _shine(d, L, x, y, r):
    if L.pupil:
        d.ellipse([x - L.erx * 0.3, y - L.ery * 0.6, x + L.erx * 0.3, y + L.ery * 0.6], fill=L.pupil)
        return
    sx, sy = x + L.erx * 0.35, y - L.ery * 0.4
    d.ellipse([sx - r, sy - r, sx + r, sy + r], fill=WHITE)


def draw_eye(d, L, x, y, s, kind):
    rx, ry = L.erx, L.ery
    lw = max(4, round(6 * L.ms))
    shine = max(3, rx * 0.33)
    oval = [x - rx, y - ry, x + rx, y + ry]
    if kind == "closed":       # ^ ^ (laughing)
        d.arc([x - rx - 4, y - ry * 0.5, x + rx + 4, y + ry * 1.3], 200, 340, fill=L.lid, width=lw + 1)
        return
    if kind == "sleep":        # u u (eyes shut, peaceful)
        d.arc([x - rx - 3, y - ry * 0.9, x + rx + 3, y + ry * 0.5], 20, 160, fill=L.lid, width=lw)
        return
    if kind in ("wide", "look_up", "look_down"):
        grow = 5 if kind == "wide" else 3
        d.ellipse([x - rx - grow, y - ry - grow + 1, x + rx + grow, y + ry + grow - 1], fill=WHITE,
                  outline=L.lid, width=3)
        if kind == "wide":
            pr = 0.55
            px, py = x, y + 1
        else:
            pr = 0.7
            px = x - rx * 0.4 if kind == "look_up" else x + rx * 0.4
            py = y - ry * 0.4 if kind == "look_up" else y + ry * 0.38
        d.ellipse([px - rx * pr, py - ry * pr, px + rx * pr, py + ry * pr], fill=L.eye)
        if not L.pupil:
            r = max(2, rx * 0.2)
            d.ellipse([px + rx * 0.2 - r, py - ry * 0.25 - r, px + rx * 0.2 + r, py - ry * 0.25 + r], fill=WHITE)
        return
    if kind == "sparkle":      # big shiny eyes, two highlights
        g = 3
        d.ellipse([x - rx - g, y - ry - g - 1, x + rx + g, y + ry + g], fill=L.eye)
        if L.pupil:
            _shine(d, L, x, y, shine)
        r1, r2 = rx * 0.45, rx * 0.25
        d.ellipse([x + rx * 0.3 - r1, y - ry * 0.4 - r1, x + rx * 0.3 + r1, y - ry * 0.4 + r1], fill=WHITE)
        d.ellipse([x - rx * 0.4 - r2, y + ry * 0.4 - r2, x - rx * 0.4 + r2, y + ry * 0.4 + r2], fill=WHITE)
        return
    d.ellipse(oval, fill=L.eye)
    if kind == "squint":       # cheeks push the lower lids up: a smiling eye
        d.ellipse([x - rx - 8, y + ry * 0.15, x + rx + 8, y + ry * 3.0], fill=L.skin)
        _shine(d, L, x, y - ry * 0.05, shine * 0.9)
        return
    elif kind == "droop":      # sad: outer corners fall
        _lid(d, L, x, y, s, y - ry * 0.95, y - ry * 0.15, lw=lw)
    elif kind == "tired":      # heavy lids, faint shadows underneath
        _lid(d, L, x, y, s, y - ry * 0.1, y - ry * 0.1, bulge=3, lw=lw)
        bag = tuple(int(c * 0.82) for c in L.skin[:3]) + (L.skin[3],)
        d.arc([x - rx - 3, y + ry * 0.6, x + rx + 3, y + ry * 1.7], 20, 160, fill=bag, width=4)
        return
    elif kind == "soft":       # tender: relaxed lids, a gentle look
        _lid(d, L, x, y, s, y - ry * 0.35, y - ry * 0.35, bulge=4, lw=lw)
        _shine(d, L, x, y + ry * 0.35, shine * 0.8)
        return
    elif kind == "flat":       # annoyed: a flat half-lid
        _lid(d, L, x, y, s, y - ry * 0.2, y - ry * 0.2, lw=lw)
        _shine(d, L, x, y + ry * 0.3, shine * 0.7)
        return
    elif kind == "firm":       # determined: lids angled in a little
        _lid(d, L, x, y, s, y - ry * 0.6, y - ry * 0.9, lw=lw)
        _shine(d, L, x, y + ry * 0.2, shine)
        return
    _shine(d, L, x, y, shine)


def draw_brow(d, L, x, y, s, kind):
    """s = -1 for the eye on the left of the picture, +1 for the right one;
    the inner end of a brow points at the nose (towards -s)."""
    bl = 17 * L.ms
    by = y - L.brow_dy
    bw = max(5, round(7 * L.ms))
    xo, xi = x + s * bl, x - s * bl

    def arc(dy, depth=12):
        d.arc([x - bl, by + dy - depth / 2, x + bl, by + dy + depth], 200, 340, fill=L.brow, width=bw)

    def slant(outer, inner):
        d.line([(xo, by + outer), (xi, by + inner)], fill=L.brow, width=bw)

    if kind == "relaxed":
        arc(0)
    elif kind == "lifted":
        arc(-4)
    elif kind == "high":
        arc(-9, 14)
    elif kind == "low":
        arc(3, 7)
    elif kind == "worried":
        slant(3, -7)
    elif kind == "sad":
        slant(6, -9)
    elif kind == "soft":
        slant(1, -4)
    elif kind == "angry":
        slant(-6, 6)
    elif kind == "firm":
        slant(-3, 2)
    elif kind == "curious":
        arc(-12, 14) if s > 0 else arc(1, 9)
    elif kind == "thinking":
        arc(-8, 12) if s < 0 else slant(1, 2)


def draw_mouth(d, L, kind, talk):
    mx, my, k = L.cx, L.my, L.ms
    lw = max(5, round(7 * k))
    inner, tongue = (110, 35, 50, 255), (225, 115, 125, 255)

    def dshape(top, w, h, teeth=False):          # flat top, round bottom
        w, h = w * k, h * k
        d.chord([mx - w, top - h, mx + w, top + h], 0, 180, fill=inner)
        if h > 12 * k:
            d.chord([mx - w * 0.55, top + h * 0.35, mx + w * 0.55, top + h * 1.15], 180, 360, fill=tongue)
        if teeth:
            d.chord([mx - w + 2, top - h * 0.35, mx + w - 2, top + h * 0.35], 0, 180, fill=WHITE)

    def ushape(bottom, w, h):                   # round top, flat bottom
        w, h = w * k, h * k
        d.chord([mx - w, bottom - h, mx + w, bottom + h], 180, 360, fill=inner)

    def oval(rx, ry, ox=0, oy=0):
        rx, ry = rx * k, ry * k
        d.ellipse([mx + ox * k - rx, my + oy * k - ry, mx + ox * k + rx, my + oy * k + ry], fill=inner)

    def arc_up(w, depth, ox=0):                 # a smile: lower half of an ellipse
        w, depth = w * k, depth * k
        cx = mx + ox * k
        d.arc([cx - w, my - depth * 1.5, cx + w, my + depth * 0.5], 15, 165, fill=L.line, width=lw)

    def arc_down(w, depth):                     # a frown: upper half
        w, depth = w * k, depth * k
        d.arc([mx - w, my - depth * 0.2, mx + w, my + depth * 1.8], 200, 340, fill=L.line, width=lw)

    def wave(w, amp, periods=1.0, lift=0):
        pts = [(mx + w * k * (2 * t - 1), my + lift * k + amp * k * math.sin(2 * math.pi * periods * t))
               for t in (i / 16 for i in range(17))]
        d.line(pts, fill=L.line, width=lw - 1, joint="curve")

    def poly(pts):
        d.line([(mx + px * k, my + py * k) for px, py in pts], fill=L.line, width=lw, joint="curve")

    if kind == "soft":
        dshape(my - 5 * k, 14, 14) if talk else arc_up(17, 7)
    elif kind == "smile":
        dshape(my - 8 * k, 24, 20) if talk else arc_up(30, 13)
    elif kind == "happy":
        dshape(my - 10 * k, 32, 30) if talk else dshape(my - 8 * k, 28, 22)
    elif kind == "laugh":
        dshape(my - 12 * k, 36, 40) if talk else dshape(my - 10 * k, 34, 32)
    elif kind == "chatty":
        dshape(my - 6 * k, 36, 34) if talk else dshape(my - 4 * k, 32, 24)
    elif kind == "grin":
        if talk:
            dshape(my - 6 * k, 34, 30, teeth=True)
        else:
            w = 36 * k
            d.chord([mx - w, my - 22 * k, mx + w, my + 22 * k], 0, 180, fill=WHITE, outline=L.line, width=4)
    elif kind == "curious":
        oval(9, 11, 6, 2) if talk else arc_up(14, 8, 7)
    elif kind == "side":
        oval(8, 9, 10, 1) if talk else poly([(-2, 4), (12, 2), (24, -2)])
    elif kind == "o":
        oval(13, 17, 0, 4) if talk else oval(9, 11, 0, 2)
    elif kind == "awe":
        oval(15, 18, 0, 4) if talk else dshape(my - 4 * k, 13, 14)
    elif kind == "worried":
        ushape(my + 10 * k, 13, 12) if talk else wave(15, 2.5, 1.0, 2)
    elif kind == "sad":
        ushape(my + 12 * k, 15, 14) if talk else arc_down(18, 9)
    elif kind == "tired":
        oval(9, 9, 0, 3) if talk else arc_up(11, 4)
    elif kind == "wobbly":
        dshape(my - 4 * k, 14, 13) if talk else wave(17, 3.5, 1.5, 0)
    elif kind == "tender":
        dshape(my - 5 * k, 17, 14) if talk else arc_up(20, 9)
    elif kind == "flat":
        ushape(my + 9 * k, 14, 10) if talk else poly([(-17, 5), (-11, 1), (11, 1), (17, 5)])
    elif kind == "set":
        dshape(my - 4 * k, 16, 13) if talk else poly([(-17, 2), (11, 2), (18, -3)])
    elif kind == "line":
        oval(10, 8, 0, 1) if talk else poly([(-20, 0), (20, 0)])
    elif kind == "w":
        oval(9, 10, 0, 4) if talk else (d.arc([mx - 18 * k, my - 10 * k, mx, my + 6 * k], 15, 165, fill=L.line, width=lw - 1),
                                        d.arc([mx, my - 10 * k, mx + 18 * k, my + 6 * k], 15, 165, fill=L.line, width=lw - 1))


def draw_blush(d, L, level):
    level = max(0, level - L.blush_cut)
    if not level:
        return
    t = {1: 0.3, 2: 0.55, 3: 0.85}[level]
    col = tuple(int(s * (1 - t) + b * t) for s, b in zip(L.skin[:3], L.blush)) + (L.skin[3],)
    rx, ry = 18 * L.ms, 10 * L.ms
    for side in (-1, 1):
        x, y = L.cx + side * L.cheek_dx, L.cheek_y
        d.ellipse([x - rx, y - ry, x + rx, y + ry], fill=col)
        if level == 3:        # embarrassed: little hatch lines on the cheeks
            dark = tuple(int(c * 0.8) for c in L.blush) + (255,)
            for j in (-1, 0, 1):
                d.line([x + j * 9 * L.ms - 4, y + 5, x + j * 9 * L.ms + 4, y - 5], fill=dark, width=3)


def face(d, L, mood, talk=False):
    eyes, brows, mouth, blush = L.parts(mood)
    draw_blush(d, L, blush)
    for s in (-1, 1):
        x = L.cx + s * L.ex
        draw_eye(d, L, x, L.ey, s, eyes)
        draw_brow(d, L, x, L.ey, s, brows)
    draw_mouth(d, L, mouth, talk)


def character(skin, hair, dress, mood, hair_long=True, extra=None, overlay=None, talk=False,
              look=None):
    w, h = 460, 680
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx = w // 2
    if hair_long:
        d.rounded_rectangle([cx - 130, 70, cx + 130, 420], 90, fill=hair)
    d.polygon([(cx - 150, h), (cx + 150, h), (cx + 95, 330), (cx - 95, 330)], fill=dress)
    d.rectangle([cx - 28, 260, cx + 28, 340], fill=skin)
    d.ellipse([cx - 110, 60, cx + 110, 300], fill=skin)
    d.chord([cx - 120, 40, cx + 120, 230], 180, 360, fill=hair)
    if extra:
        extra(d, cx)
    dark_skin = sum(skin) / 3 < 150
    L = look or Look(cx, 185, skin=skin, brow=tuple(int(c * 0.6) for c in hair),
                     line=(95, 28, 40) if dark_skin else (150, 55, 65),
                     blush=(225, 110, 110) if dark_skin else (250, 150, 150))
    face(d, L, mood, talk)
    if overlay:
        overlay(d, cx)
    return img.filter(ImageFilter.SMOOTH)


def freckles(d, cx):
    for dx, dy in [(-70, 205), (-58, 214), (-74, 220), (62, 207), (72, 216), (56, 222)]:
        d.ellipse([cx + dx - 3, dy - 3, cx + dx + 3, dy + 3], fill=(200, 120, 90))


def hospital_band(d, cx):
    d.rectangle([cx - 150, 600, cx + 150, 615], fill=(240, 240, 255))


def glasses(d, cx):
    for x0 in (cx - 76, cx + 14):
        d.rounded_rectangle([x0, 165, x0 + 62, 205], 8, outline=(40, 40, 40), width=4)
    d.line([cx - 14, 180, cx + 14, 180], fill=(40, 40, 40), width=4)


def seraph(mood, talk=False):
    """Commander of an angel corps: wings, halo, a uniform of light."""
    w, h = 640, 700
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx = w // 2
    for side in (-1, 1):
        for k in range(4):
            x0 = cx + side * (120 + k * 40)
            d.ellipse([min(x0, x0 + side * 190), 140 + k * 60, max(x0, x0 + side * 190), 330 + k * 60],
                      fill=(255, 255, 255, 235 - k * 30))
    d.ellipse([cx - 95, 8, cx + 95, 52], outline=(255, 210, 90), width=9)
    d.polygon([(cx - 160, h), (cx + 160, h), (cx + 100, 330), (cx - 100, 330)], fill=(245, 240, 225))
    d.rectangle([cx - 100, 360, cx + 100, 380], fill=(220, 180, 80))
    for k in range(3):
        d.rectangle([cx + 40 + k * 18, 400, cx + 52 + k * 18, 425], fill=(220, 180, 80))
    skin = (240, 225, 215)
    d.rectangle([cx - 28, 260, cx + 28, 340], fill=skin)
    d.ellipse([cx - 110, 60, cx + 110, 300], fill=skin)
    d.chord([cx - 118, 45, cx + 118, 200], 180, 360, fill=(235, 225, 200))
    L = Look(cx, 185, eye=(80, 130, 195), lid=(70, 80, 110), brow=(175, 155, 115), skin=skin,
             blush_cut=1)
    face(d, L, mood, talk)
    return img.filter(ImageFilter.SMOOTH)


def spirit(color, mood, talk=False):
    """A purgatorium spirit: translucent, a little blobby, very chatty."""
    w, h = 360, 520
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx = w // 2
    body = color + (170,)
    d.ellipse([cx - 120, 60, cx + 120, 330], fill=body)
    d.polygon([(cx - 120, 200), (cx + 120, 200), (cx + 80, 460), (cx + 30, 420), (cx, 500),
               (cx - 40, 420), (cx - 80, 470)], fill=body)
    L = Look(cx, 175, ex=40, erx=12, ery=19, brow_dy=40, my=236, eye=(30, 30, 50), line=(30, 30, 50),
             brow=(30, 30, 50), skin=body, blush=(255, 140, 170), cheek_dx=72, cheek_dy=40,
             extra={"chatty": ("open", "lifted", "chatty", 1),
                    "grumpy": EXPRESSIONS["annoyed"]})
    face(d, L, mood, talk)
    return img.filter(ImageFilter.GaussianBlur(1.2))


def patron(mood, talk=False):
    """An energy vampire. Tall, elegant, patient, hungry."""
    w, h = 460, 720
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx = w // 2
    d.polygon([(cx - 200, h), (cx + 200, h), (cx + 90, 300), (cx - 90, 300)], fill=(40, 20, 50))
    d.polygon([(cx - 150, 300), (cx - 40, 300), (cx - 90, 180)], fill=(70, 30, 80))
    d.polygon([(cx + 150, 300), (cx + 40, 300), (cx + 90, 180)], fill=(70, 30, 80))
    skin = (205, 200, 215)
    d.rectangle([cx - 24, 250, cx + 24, 320], fill=skin)
    d.ellipse([cx - 85, 40, cx + 85, 300], fill=skin)
    d.chord([cx - 95, 20, cx + 95, 200], 180, 360, fill=(25, 15, 30))
    L = Look(cx, 172, ex=38, erx=14, ery=11, brow_dy=27, my=236, ms=0.85, eye=(235, 50, 60),
             lid=(70, 25, 50), line=(110, 40, 70), brow=(40, 20, 40), skin=skin, blush=(200, 130, 170),
             blush_cut=1, cheek_dx=52, cheek_dy=40, pupil=(255, 230, 230),
             extra={"cold": ("flat", "low", "line", 0)})
    face(d, L, mood, talk)
    return img.filter(ImageFilter.SMOOTH)


def lantern(mood, talk=False):
    """Ember, of the Lantern Watch: small, warm, secretly on Aron's side."""
    w, h = 340, 520
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx = w // 2 - 30
    body = (255, 180, 110, 200)
    d.ellipse([cx - 100, 90, cx + 100, 310], fill=body)
    d.polygon([(cx - 100, 220), (cx + 100, 220), (cx + 60, 470), (cx, 430), (cx - 60, 470)], fill=body)
    L = Look(cx, 192, ex=34, erx=10, ery=14, brow_dy=30, my=240, ms=0.8, eye=(70, 40, 30),
             line=(90, 45, 30), brow=(140, 80, 45), skin=body, blush=(255, 110, 80), cheek_dx=58,
             cheek_dy=34)
    face(d, L, mood, talk)
    lx = cx + 150
    d.line([cx + 90, 300, lx, 290], fill=(255, 180, 110, 220), width=12)
    d.line([lx, 250, lx, 290], fill=(80, 60, 40, 255), width=4)
    d.rounded_rectangle([lx - 26, 290, lx + 26, 360], 8, fill=(255, 230, 140, 255),
                        outline=(80, 60, 40, 255), width=4)
    return img.filter(ImageFilter.GaussianBlur(1.0))


MISO_MOODS = ("sit", "loaf", "stare", "meow", "curious", "sleepy", "happy")


def cat(mood, talk=False):
    """Miso, Aron's cat. Orange tabby, white chest, unimpressed."""
    w, h = 300, 300
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    fur, dark, chest = (235, 150, 70, 255), (200, 110, 45, 255), (250, 240, 225, 255)
    ink = (60, 40, 30, 255)
    loaf = mood == "loaf"
    if loaf:
        d.rounded_rectangle([40, 170, 260, 290], 60, fill=fur)
        ey = 145
    else:
        d.ellipse([70, 150, 230, 295], fill=fur)
        d.ellipse([110, 190, 190, 290], fill=chest)
        ey = 118 if mood == "sleepy" else 115
        tail_y = 250 if mood in ("meow", "happy", "curious") else 270
        d.arc([180, tail_y - 120, 300, tail_y], 90, 250, fill=fur, width=18)
    # the head on its own layer, so a curious cat can tilt it
    head = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    hd = ImageDraw.Draw(head)
    hd.ellipse([90, ey - 55, 210, ey + 60], fill=fur)
    top = ey - 55
    for x in (100, 180):
        hd.polygon([(x - 10, top + 20), (x + 20, top - 25), (x + 30, top + 25)], fill=fur)
        hd.polygon([(x - 1, top + 16), (x + 19, top - 12), (x + 24, top + 18)], fill=(240, 160, 160, 255))
    for x in (115, 165):
        hd.line([x, top + 5, x + 10, top + 25], fill=dark, width=6)
    for ex in (128, 172):
        if mood in ("loaf", "sleepy"):
            hd.arc([ex - 14, ey - 6, ex + 14, ey + 10], 20, 160, fill=ink, width=4)
        elif mood == "happy":     # ^ ^
            hd.arc([ex - 14, ey - 6, ex + 14, ey + 14], 200, 340, fill=ink, width=5)
        else:
            hd.ellipse([ex - 13, ey - 13, ex + 13, ey + 13], fill=(120, 190, 90, 255))
            if mood == "curious":   # round, dilated pupils
                hd.ellipse([ex - 8, ey - 9, ex + 8, ey + 9], fill=(20, 20, 20, 255))
                hd.ellipse([ex + 1, ey - 7, ex + 6, ey - 2], fill=WHITE)
            else:
                hd.ellipse([ex - 4, ey - 11, ex + 4, ey + 11], fill=(20, 20, 20, 255))
            if mood == "stare":     # deadpan: flat half-lids
                hd.rectangle([ex - 16, ey - 18, ex + 16, ey - 3], fill=fur)
                hd.line([ex - 15, ey - 3, ex + 15, ey - 3], fill=ink, width=4)
    if mood == "happy":
        for ex in (112, 188):
            hd.ellipse([ex - 12, ey + 14, ex + 12, ey + 24], fill=(245, 150, 140, 255))
    hd.polygon([(142, ey + 18), (158, ey + 18), (150, ey + 27)], fill=(230, 120, 140, 255))
    opened = mood == "meow" or talk
    if opened:
        big = 1 if (mood == "meow" and talk) else 0
        hd.ellipse([140 - big * 3, ey + 29, 160 + big * 3, ey + 47 + big * 5], fill=(150, 50, 70, 255))
    else:
        mw = 3 if mood == "happy" else 0
        hd.arc([132 - mw, ey + 22, 150, ey + 36 + mw], 20, 160, fill=ink, width=3)
        hd.arc([150, ey + 22, 168 + mw, ey + 36 + mw], 20, 160, fill=ink, width=3)
    for side in (-1, 1):
        for k in range(3):
            hd.line([150 + side * 25, ey + 28 + k * 5, 150 + side * 75, ey + 18 + k * 12],
                    fill=(250, 250, 250, 255), width=2)
    if mood == "curious":
        head = head.rotate(13, resample=Image.BICUBIC, center=(150, ey + 50))
    img = Image.alpha_composite(img, head)
    if mood == "sleepy":
        zd = ImageDraw.Draw(img)
        for i, (zx, zy, zs) in enumerate([(222, 70, 18), (250, 40, 13)]):
            zd.line([(zx, zy), (zx + zs, zy), (zx, zy + zs), (zx + zs, zy + zs)], fill=(90, 110, 170, 255),
                    width=4)
    return img.filter(ImageFilter.SMOOTH)


TALKING = []   # every sprite name that gets a talking frame


def save_sprite(make, img_dir, name, aliases=()):
    """Save a sprite and its talking frame (mouth open), plus any old names
    that should keep resolving to the same picture."""
    still, talk = make(False), make(True)
    for n in (name,) + tuple(aliases):
        still.save(os.path.join(img_dir, n + ".png"))
        talk.save(os.path.join(img_dir, n + " open.png"))
        TALKING.append(n)


def write_talk_rpy(game_dir):
    """Ren'Py side of talking mouths: with config.speaking_attribute = "talk"
    the speaking character's image gains the "talk" attribute, which maps to
    a mouth-flap animation. (vn3ds does the flapping itself from the first
    frame.)"""
    lines = ["# Generated by examples/make_demo_assets.py - talking mouths.", "",
             'define config.speaking_attribute = "talk"', ""]
    for name in TALKING:
        lines += [f"image {name} talk:", f'    "{name} open"', "    pause 0.11",
                  f'    "{name}"', "    pause 0.09", "    repeat", ""]
    with open(os.path.join(game_dir, "talking.rpy"), "w") as f:
        f.write("\n".join(lines))


# Who gets which moods. Old names stay as aliases so older scripts resolve.
HUMAN_ALIASES = {"neutral": ("normal",)}
CAST = {}   # sheet name -> list of moods (filled in by make_people)


def make_people(img_dir):
    """Draw every character in every mood; return {group: [moods]}."""

    def save(group, mood, make, aliases=()):
        save_sprite(make, img_dir, f"{group} {mood}", tuple(f"{group} {a}" for a in aliases))
        CAST.setdefault(group, []).append(mood)

    def humans(group, **kw):
        for mood in MOODS:
            save(group, mood, lambda t, m=mood: character(mood=m, talk=t, **kw),
                 HUMAN_ALIASES.get(mood, ()))

    mira = dict(skin=(255, 225, 205), hair=(200, 70, 35), dress=(70, 150, 140), extra=freckles)
    humans("mira", **mira)
    aron = dict(skin=(230, 190, 160), hair=(40, 40, 50), dress=(70, 130, 200), hair_long=False)
    humans("aron", **aron)
    humans("aron ward", **dict(aron, dress=(200, 205, 215), extra=hospital_band))

    def golden_coat(d, cx):
        for k in range(6):
            d.line([cx - 150 + k * 60, 680, cx - 60 + k * 24, 340], fill=(255, 235, 150), width=6)
        d.ellipse([cx - 95, 8, cx + 95, 40], outline=(255, 220, 120), width=6)

    def shining(mood, talk):
        img = character(mood=mood, talk=talk, **dict(aron, dress=(235, 185, 70), extra=golden_coat))
        glowing = Image.new("RGBA", img.size, (0, 0, 0, 0))
        halo = img.split()[3].filter(ImageFilter.GaussianBlur(14))
        glowing.paste((255, 220, 120, 255), mask=halo)
        return Image.alpha_composite(glowing, img)
    for mood in MOODS:
        save("aron light", mood, lambda t, m=mood: shining(m, t), HUMAN_ALIASES.get(mood, ()))

    doc = dict(skin=(150, 100, 75), hair=(30, 25, 25), dress=(245, 245, 250), hair_long=False,
               overlay=glasses)
    humans("okafor", **doc)
    humans("nurse", skin=(240, 200, 175), hair=(120, 80, 50), dress=(120, 180, 200))
    humans("theo", skin=(200, 150, 110), hair=(150, 100, 40), dress=(90, 160, 90), hair_long=False)
    seraph_alias = {"neutral": ("stern",), "worried": ("concerned",)}
    for mood in MOODS:
        save("seraph", mood, lambda t, m=mood: seraph(m, t), seraph_alias.get(mood, ()))
    for mood in MOODS + ["chatty"]:
        alias = ("grumpy",) if mood == "annoyed" else ()
        save("pim", mood, lambda t, m=mood: spirit((150, 200, 255), m, t), alias)
        save("dross", mood, lambda t, m=mood: spirit((170, 240, 190), m, t), alias)
    for mood in MOODS + ["cold"]:
        save("patron", mood, lambda t, m=mood: patron(m, t))
    for mood in MOODS:
        save("ember", mood, lambda t, m=mood: lantern(m, t), ("soft",) if mood == "tender" else ())
    for mood in MISO_MOODS:
        save("miso", mood, lambda t, m=mood: cat(m, t))
    return CAST


# ---------------------------------------------------------------- contact sheets

def contact_sheets(img_dir, out_dir, cast):
    """Every character's moods at 3DS size, for review: one sheet per
    character (closed and talking frames) and one overview of everyone."""
    os.makedirs(out_dir, exist_ok=True)
    scale = 400 / 1280          # the 3DS shows the 1280x720 game at this scale
    lab = font(13)
    bg = (214, 204, 192)
    rows_all = []
    for group, moods in cast.items():
        cells = []
        for mood in moods:
            pair = []
            for suffix in ("", " open"):
                im = Image.open(os.path.join(img_dir, f"{group} {mood}{suffix}.png"))
                im = im.resize((max(1, round(im.width * scale)), max(1, round(im.height * scale))),
                               Image.LANCZOS)
                pair.append(im)
            cells.append((mood, pair))
        cw = max(p[0].width for _, p in cells) + 8
        ch = max(p[0].height for _, p in cells)
        cols = 9
        nrows = (len(cells) + cols - 1) // cols
        sheet = Image.new("RGB", (cw * cols + 16, 24 + nrows * (2 * ch + 30)), bg)
        sd = ImageDraw.Draw(sheet)
        sd.text((8, 4), f"{group}   (top: still, below: talking frame; 3DS size)", fill=(40, 40, 40), font=lab)
        for i, (mood, (still, talk)) in enumerate(cells):
            x = 8 + (i % cols) * cw
            y = 24 + (i // cols) * (2 * ch + 30)
            sheet.paste(still, (x, y), still)
            sheet.paste(talk, (x, y + ch + 14), talk)
            sd.text((x + 2, y + ch), mood, fill=(30, 30, 30), font=lab)
        sheet.save(os.path.join(out_dir, group.replace(" ", "_") + ".png"))
        # overview row: stills at about 120 px tall
        row = []
        for mood, (still, _) in cells:
            k = 120 / still.height
            row.append((mood, still.resize((max(1, round(still.width * k)), 120), Image.LANCZOS)))
        rows_all.append((group, row))
    cw = max(im.width for _, row in rows_all for _, im in row) + 4
    width = 90 + cw * max(len(row) for _, row in rows_all)
    over = Image.new("RGB", (width, 8 + len(rows_all) * 140), bg)
    od = ImageDraw.Draw(over)
    for r, (group, row) in enumerate(rows_all):
        y = 8 + r * 140
        od.text((6, y + 50), group, fill=(30, 30, 30), font=lab)
        for c, (mood, im) in enumerate(row):
            x = 90 + c * cw
            over.paste(im, (x, y), im)
            od.text((x, y + 121), mood[:11], fill=(50, 50, 50), font=font(11))
    over.save(os.path.join(os.path.dirname(out_dir), "expressions.png"))


# ---------------------------------------------------------------- music

RATE = 32000


def tone(freq, dur, kind="pluck", vol=0.5):
    t = np.arange(int(RATE * dur)) / RATE
    if kind == "pad":
        env = np.minimum(1, t / 0.6) * np.minimum(1, (dur - t) / 0.6)
        s = sum(np.sin(2 * math.pi * freq * m * t + m) / m for m in (1, 2, 3)) * 0.5
        s *= 1 + 0.15 * np.sin(2 * math.pi * 0.3 * t)
    elif kind == "bell":
        env = np.exp(-t * 2.2)
        s = np.sin(2 * math.pi * freq * t) + 0.4 * np.sin(2 * math.pi * freq * 2.76 * t)
    elif kind == "drone":
        env = np.ones_like(t)
        s = (np.sin(2 * math.pi * freq * t) + 0.5 * np.sin(2 * math.pi * freq * 1.5 * t) +
             0.25 * np.sin(2 * math.pi * freq * 2.01 * t))
        s *= 0.6 + 0.4 * np.sin(2 * math.pi * 0.11 * t)
    else:
        env = np.exp(-t * 6)
        s = np.sin(2 * math.pi * freq * t) * 0.8 + np.sin(4 * math.pi * freq * t) * 0.2
    return s * env * vol


def hz(n):
    return 440 * 2 ** ((n - 69) / 12)


def mix(parts, length):
    out = np.zeros(int(RATE * length))
    for start, sig in parts:
        i = int(start * RATE)
        n = min(len(sig), len(out) - i)
        if n > 0:
            out[i:i + n] += sig[:n]
    return out


def song(name):
    if name == "theme":   # the tutorial's arpeggio
        notes = [60, 64, 67, 72, 67, 64, 57, 60, 64, 69, 64, 60, 53, 57, 60, 65, 60, 57, 55, 59, 62, 67, 62, 59]
        parts = [(i * 0.25, tone(hz(n), 0.6)) for i, n in enumerate(notes * 2)]
        return mix(parts, 12)
    if name == "morning":  # warm, slightly too regular
        prog = [(60, 64, 67), (57, 60, 64), (65, 69, 72), (67, 71, 74)]
        parts = []
        for bar in range(8):
            ch = prog[bar % 4]
            parts.append((bar * 2.0, sum(tone(hz(n - 12), 2.2, "pad", 0.18) for n in ch)))
            for k, n in enumerate([ch[0], ch[1], ch[2], ch[1]]):
                parts.append((bar * 2.0 + k * 0.5, tone(hz(n + 12), 0.5, "pluck", 0.22)))
        return mix(parts, 16)
    if name == "unease":   # minor, with a note that never resolves
        prog = [(57, 60, 64), (53, 57, 60), (50, 53, 57), (52, 56, 59)]
        parts = []
        for bar in range(8):
            ch = prog[bar % 4]
            parts.append((bar * 2.5, sum(tone(hz(n - 12) * 1.003, 2.8, "pad", 0.17) for n in ch)))
            if bar % 2:
                parts.append((bar * 2.5 + 1.2, tone(hz(75), 1.5, "bell", 0.12)))
        return mix(parts, 20)
    if name == "ward":     # sparse, fluorescent
        parts = [(0, tone(hz(45), 24, "drone", 0.08))]
        for k, n in enumerate([76, 79, 74, 72, 76, 71, 69, 72]):
            parts.append((k * 3.0 + 0.5, tone(hz(n), 2.5, "bell", 0.16)))
        return mix(parts, 24)
    if name == "entities": # vast and indifferent
        parts = [(0, tone(hz(38), 24, "drone", 0.16)), (0, tone(hz(45), 24, "drone", 0.08))]
        for k, n in enumerate([62, 69, 64, 71]):
            parts.append((k * 6.0 + 1, tone(hz(n), 5.5, "pad", 0.1)))
        return mix(parts, 24)
    if name == "watch":    # small and kind
        mel = [72, 74, 76, 79, 76, 74, 72, 69, 67, 69, 72, 74, 72]
        parts = [(i * 0.75, tone(hz(n), 1.4, "bell", 0.16)) for i, n in enumerate(mel)]
        for bar in range(5):
            parts.append((bar * 2.0, tone(hz(48 if bar % 2 == 0 else 45), 2.2, "pad", 0.2)))
        return mix(parts, 10)
    if name == "voices":   # the otherworldly transmissions
        parts = []
        for k in range(10):
            f = hz(60 + (k * 7) % 13) * (1 + 0.02 * math.sin(k))
            parts.append((k * 0.7, tone(f, 2.0, "pad", 0.12) * np.sign(np.sin(np.arange(int(RATE * 2)) / 40))))
        noise = RNG.normal(0, 0.05, int(RATE * 8))
        parts.append((0, noise * np.linspace(1, 0, len(noise))))
        return mix(parts, 8)
    raise KeyError(name)


def write_ogg(path, pcm):
    pcm = pcm / max(1e-6, np.abs(pcm).max()) * 0.7
    stereo = np.stack([pcm, np.roll(pcm, 300)], 1)
    data = (stereo * 32767).astype("<i2")
    wav = path[:-4] + ".wav"
    with wave.open(wav, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(data.tobytes())
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        print("ffmpeg not found; left", wav, "as WAV (vnpack will skip it)")
        return
    r = subprocess.run([ffmpeg, "-v", "error", "-y", "-i", wav, "-c:a", "libvorbis", "-q:a", "3", path],
                       capture_output=True)
    if r.returncode != 0:
        subprocess.run([ffmpeg, "-v", "error", "-y", "-i", wav, "-c:a", "vorbis", "-strict", "-2", path],
                       check=True)
    os.remove(wav)




# ---------------------------------------------------------------- main

def write_config(layers):
    """vn3ds.json: depths, the layered scenes, camera and voices. Keys that
    other tools added to an existing file are kept."""
    path = os.path.join(GAME, "vn3ds.json")
    cfg = {}
    if os.path.exists(path):
        try:
            with open(path) as f:
                cfg = json.load(f)
        except ValueError:
            cfg = {}
    cfg.update({
        "depth": {"cg": 0.3, "aron": 0.0, "mira": 0.0, "seraph": -0.08, "patron": -0.15,
                  "ember": -0.1, "pim": 0.05, "dross": 0.1, "miso": -0.12},
        "layers": layers,
        "max_shift": 8.0,
        "camera": {"drift": 4.5, "period": 19, "zoom": 0.015},
        # Machine voices (see voices.rpy): a syllable bank and a pitch per
        # character variable. Narration and thoughts stay silent.
        "voices": {
            "bank": [f"audio/vox/syl{i:02d}.ogg" for i in range(24)],
            "pitch": {"a": 1.0, "m": 1.34, "th": 0.86, "dr": 0.78, "nu": 1.22, "se": 1.55,
                      "pi": 1.85, "dro": 0.62, "em": 1.42, "pa": 0.52, "council": 0.45,
                      "stranger": 0.95, "radio": 1.1},
            "volume": 0.32,
            "duck": 0.8,
        },
    })
    with open(path, "w") as f:
        json.dump(cfg, f, indent=1)


def main():
    """Draws everything. The simple songs below are only written when the
    file is missing (examples/music renders the real score into audio/);
    pass --music to overwrite them anyway."""
    img_dir = os.path.join(GAME, "images")
    aud_dir = os.path.join(GAME, "audio")
    for d in (img_dir, aud_dir, os.path.join(GAME, "gui")):
        os.makedirs(d, exist_ok=True)

    layers = scenes3d.build_all(GAME)
    for old in ("kai normal.png", "kai grin.png", "bg park.jpg"):
        if os.path.exists(os.path.join(img_dir, old)):
            os.remove(os.path.join(img_dir, old))
    write_config(layers)

    cast = make_people(img_dir)
    write_talk_rpy(GAME)
    contact_sheets(img_dir, os.path.join(HERE, "demo", "expressions"), cast)
    main_menu().save(os.path.join(GAME, "gui", "main_menu.png"))

    for name in ("theme", "morning", "unease", "ward", "entities", "watch", "voices"):
        path = os.path.join(aud_dir, name + ".ogg")
        if "--music" in sys.argv or not os.path.exists(path):
            write_ogg(path, song(name))
    print("art written to", GAME)


if __name__ == "__main__":
    main()

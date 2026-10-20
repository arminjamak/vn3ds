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

def face(d, cx, mood, eye_col=(40, 30, 30), mouth=(150, 50, 60), cheeks=True):
    ey = 185
    if mood in ("surprised", "awe"):
        for ex in (cx - 45, cx + 45):
            d.ellipse([ex - 16, ey - 18, ex + 16, ey + 18], fill=(255, 255, 255))
            d.ellipse([ex - 8, ey - 8, ex + 8, ey + 8], fill=eye_col)
        r = 14 if mood == "surprised" else 9
        d.ellipse([cx - r, 250 - r, cx + r, 250 + r], fill=mouth)
        return
    if mood == "tired":
        for ex in (cx - 45, cx + 45):
            d.chord([ex - 13, ey - 6, ex + 13, ey + 14], 0, 180, fill=eye_col)
            d.arc([ex - 16, ey + 8, ex + 16, ey + 26], 20, 160, fill=(150, 120, 150), width=4)
        d.line([cx - 18, 252, cx + 18, 255], fill=mouth, width=5)
        return
    for ex in (cx - 45, cx + 45):
        d.ellipse([ex - 11, ey - 14, ex + 11, ey + 14], fill=eye_col)
    if mood in ("worried", "sad"):
        d.line([cx - 62, ey - 32, cx - 30, ey - 22], fill=(60, 40, 40), width=5)
        d.line([cx + 62, ey - 32, cx + 30, ey - 22], fill=(60, 40, 40), width=5)
    if mood in ("happy", "grin", "smile"):
        d.arc([cx - 40, 215, cx + 40, 265], 10, 170, fill=mouth, width=6)
        if mood == "grin":
            d.chord([cx - 38, 225, cx + 38, 268], 0, 180, fill=(255, 255, 255))
    elif mood in ("sad", "worried"):
        d.arc([cx - 30, 245, cx + 30, 285], 200, 340, fill=mouth, width=6)
    else:
        d.line([cx - 22, 250, cx + 22, 250], fill=mouth, width=6)
    if cheeks and mood not in ("worried",):
        d.ellipse([cx - 80, 215, cx - 50, 235], fill=(250, 170, 170))
        d.ellipse([cx + 50, 215, cx + 80, 235], fill=(250, 170, 170))


def character(skin, hair, dress, mood, hair_long=True, extra=None):
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
    face(d, cx, mood)
    return img.filter(ImageFilter.SMOOTH)


def freckles(d, cx):
    for dx, dy in [(-70, 205), (-58, 214), (-74, 220), (62, 207), (72, 216), (56, 222)]:
        d.ellipse([cx + dx - 3, dy - 3, cx + dx + 3, dy + 3], fill=(200, 120, 90))


def hospital_band(d, cx):
    d.rectangle([cx - 150, 600, cx + 150, 615], fill=(240, 240, 255))


def seraph(mood):
    """Commander of an angel corps: wings, halo, a uniform of light."""
    w, h = 640, 700
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx = w // 2
    for side in (-1, 1):
        for k in range(4):
            x0 = cx + side * (120 + k * 40)
            d.ellipse([min(x0, x0 + side * 190) , 140 + k * 60, max(x0, x0 + side * 190), 330 + k * 60],
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
    face(d, cx, {"stern": "neutral", "concerned": "worried"}.get(mood, mood),
         eye_col=(90, 140, 200), cheeks=False)
    return img.filter(ImageFilter.SMOOTH)


def spirit(color, mood):
    """A purgatorium spirit: translucent, a little blobby, very chatty."""
    w, h = 360, 520
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx = w // 2
    body = color + (170,)
    d.ellipse([cx - 120, 60, cx + 120, 330], fill=body)
    d.polygon([(cx - 120, 200), (cx + 120, 200), (cx + 80, 460), (cx + 30, 420), (cx, 500),
               (cx - 40, 420), (cx - 80, 470)], fill=body)
    for ex in (cx - 40, cx + 40):
        if mood == "worried":
            d.ellipse([ex - 12, 160, ex + 12, 196], fill=(30, 30, 50, 255))
            d.line([ex - 20, 140, ex + 18, 150 if ex < cx else 130], fill=(30, 30, 50, 255), width=4)
        else:
            d.ellipse([ex - 12, 155, ex + 12, 195], fill=(30, 30, 50, 255))
    if mood == "chatty":
        d.chord([cx - 34, 210, cx + 34, 260], 0, 180, fill=(30, 30, 50, 255))
    elif mood == "worried":
        d.arc([cx - 25, 225, cx + 25, 260], 200, 340, fill=(30, 30, 50, 255), width=5)
    else:
        d.line([cx - 20, 235, cx + 20, 235], fill=(30, 30, 50, 255), width=5)
    return img.filter(ImageFilter.GaussianBlur(1.2))


def patron(mood):
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
    for ex in (cx - 38, cx + 38):
        d.ellipse([ex - 14, 160, ex + 14, 182], fill=(255, 60, 60))
        d.ellipse([ex - 5, 165, ex + 5, 177], fill=(255, 230, 230))
    if mood == "smile":
        d.arc([cx - 35, 215, cx + 35, 250], 15, 165, fill=(110, 40, 70), width=4)
    else:
        d.line([cx - 26, 238, cx + 26, 238], fill=(110, 40, 70), width=4)
    img = img.filter(ImageFilter.SMOOTH)
    return img


def lantern(mood):
    """Ember, of the Lantern Watch: small, warm, secretly on Aron's side."""
    w, h = 340, 520
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx = w // 2 - 30
    d.ellipse([cx - 100, 90, cx + 100, 310], fill=(255, 180, 110, 200))
    d.polygon([(cx - 100, 220), (cx + 100, 220), (cx + 60, 470), (cx, 430), (cx - 60, 470)],
              fill=(255, 180, 110, 200))
    for ex in (cx - 34, cx + 34):
        d.ellipse([ex - 10, 175, ex + 10, 205], fill=(70, 40, 30, 255))
    if mood == "soft":
        d.arc([cx - 28, 215, cx + 28, 250], 10, 170, fill=(70, 40, 30, 255), width=5)
    else:
        d.arc([cx - 24, 232, cx + 24, 262], 200, 340, fill=(70, 40, 30, 255), width=5)
    lx = cx + 150
    d.line([cx + 90, 300, lx, 290], fill=(255, 180, 110, 220), width=12)
    d.line([lx, 250, lx, 290], fill=(80, 60, 40, 255), width=4)
    d.rounded_rectangle([lx - 26, 290, lx + 26, 360], 8, fill=(255, 230, 140, 255),
                        outline=(80, 60, 40, 255), width=4)
    return img.filter(ImageFilter.GaussianBlur(1.0))


def cat(mood):
    """Miso, Aron's cat. Orange tabby, white chest, unimpressed."""
    w, h = 300, 300
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    fur, dark, chest = (235, 150, 70, 255), (200, 110, 45, 255), (250, 240, 225, 255)
    if mood == "loaf":
        d.rounded_rectangle([40, 170, 260, 290], 60, fill=fur)
        d.ellipse([90, 90, 210, 200], fill=fur)
        ey = 145
    else:
        d.ellipse([70, 150, 230, 295], fill=fur)
        d.ellipse([110, 190, 190, 290], fill=chest)
        d.ellipse([90, 60, 210, 175], fill=fur)
        ey = 115
        tail_y = 270 if mood != "meow" else 250
        d.arc([180, tail_y - 120, 300, tail_y], 90, 250, fill=fur, width=18)
    top = ey - 55
    for x in (100, 180):
        d.polygon([(x - 10, top + 20), (x + 20, top - 25 if x == 180 else top - 25), (x + 30, top + 25)], fill=fur)
    for x in (115, 165):
        d.line([x, top + 5, x + 10, top + 25], fill=dark, width=6)
    for ex in (128, 172):
        if mood in ("loaf", "sleep"):
            d.arc([ex - 14, ey - 6, ex + 14, ey + 10], 20, 160, fill=(60, 40, 30, 255), width=4)
        else:
            d.ellipse([ex - 13, ey - 13, ex + 13, ey + 13], fill=(120, 190, 90, 255))
            d.ellipse([ex - 4, ey - 11, ex + 4, ey + 11], fill=(20, 20, 20, 255))
    d.polygon([(142, ey + 18), (158, ey + 18), (150, ey + 27)], fill=(230, 120, 140, 255))
    if mood == "meow":
        d.ellipse([140, ey + 30, 160, ey + 48], fill=(150, 50, 70, 255))
    else:
        d.arc([132, ey + 22, 150, ey + 36], 20, 160, fill=(60, 40, 30, 255), width=3)
        d.arc([150, ey + 22, 168, ey + 36], 20, 160, fill=(60, 40, 30, 255), width=3)
    for side in (-1, 1):
        for k in range(3):
            d.line([150 + side * 25, ey + 28 + k * 5, 150 + side * 75, ey + 18 + k * 12], fill=(250, 250, 250, 255), width=2)
    return img.filter(ImageFilter.SMOOTH)


# Where each kind of sprite keeps its mouth: (centre x, centre y, rx, ry).
MOUTHS = {"human": (230, 252, 17, 15), "seraph": (320, 252, 16, 13), "patron": (230, 236, 14, 11),
          "spirit": (180, 234, 18, 14), "ember": (140, 236, 14, 12), "miso": (150, 154, 9, 9)}


def open_mouth(img, kind):
    """A talking frame: paint the mouth open over a finished sprite."""
    x, y, rx, ry = MOUTHS[kind]
    out = img.copy()
    d = ImageDraw.Draw(out)
    skin = img.getpixel((x, y - ry - 8))
    if skin[3] > 0:   # cover the old mouth with the face colour
        d.ellipse([x - rx - 10, y - ry - 6, x + rx + 10, y + ry + 4], fill=skin)
    d.ellipse([x - rx, y - ry, x + rx, y + ry], fill=(110, 35, 50, 255))
    d.ellipse([x - rx // 2, y + ry // 3, x + rx // 2, y + ry - 1], fill=(220, 110, 120, 255))
    return out


TALKING = []   # (image name, kind) of every sprite that gets a talking frame


def save_sprite(img, img_dir, name, kind):
    img.save(os.path.join(img_dir, name + ".png"))
    open_mouth(img, kind).save(os.path.join(img_dir, name + " open.png"))
    TALKING.append(name)


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

def main():
    img_dir = os.path.join(GAME, "images")
    aud_dir = os.path.join(GAME, "audio")
    for d in (img_dir, aud_dir, os.path.join(GAME, "gui")):
        os.makedirs(d, exist_ok=True)

    layers = scenes3d.build_all(GAME)
    for old in ("kai normal.png", "kai grin.png", "bg park.jpg"):
        if os.path.exists(os.path.join(img_dir, old)):
            os.remove(os.path.join(img_dir, old))
    cfg = {
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
    }
    with open(os.path.join(GAME, "vn3ds.json"), "w") as f:
        json.dump(cfg, f, indent=1)

    mira = dict(skin=(255, 225, 205), hair=(200, 70, 35), dress=(70, 150, 140), extra=freckles)
    for mood in ("happy", "sad", "surprised", "worried", "smile", "neutral"):
        save_sprite(character(mood=mood, **mira), img_dir, f"mira {mood}", "human")
    aron = dict(skin=(230, 190, 160), hair=(40, 40, 50), dress=(70, 130, 200), hair_long=False)
    for mood in ("normal", "grin", "worried", "tired", "awe", "sad", "smile"):
        save_sprite(character(mood=mood, **aron), img_dir, f"aron {mood}", "human")
    def golden_coat(d, cx):
        for k in range(6):
            d.line([cx - 150 + k * 60, 680, cx - 60 + k * 24, 340], fill=(255, 235, 150), width=6)
        d.ellipse([cx - 95, 8, cx + 95, 40], outline=(255, 220, 120), width=6)
    for mood in ("smile", "awe", "normal"):
        img = character(mood=mood, **dict(aron, dress=(235, 185, 70), extra=golden_coat))
        glowing = Image.new("RGBA", img.size, (0, 0, 0, 0))
        halo = img.split()[3].filter(ImageFilter.GaussianBlur(14)).point(lambda v: min(255, v))
        glowing.paste((255, 220, 120, 255), mask=halo)
        Image.alpha_composite(glowing, img).save(os.path.join(img_dir, f"aron light {mood}.png"))
    for mood in ("tired", "worried"):
        a = dict(aron, dress=(200, 205, 215), extra=hospital_band)
        save_sprite(character(mood=mood, **a), img_dir, f"aron ward {mood}", "human")
    doc = dict(skin=(150, 100, 75), hair=(30, 25, 25), dress=(245, 245, 250), hair_long=False,
               extra=lambda d, cx: (d.rectangle([cx - 70, 172, cx - 20, 198], outline=(40, 40, 40), width=4),
                                    d.rectangle([cx + 20, 172, cx + 70, 198], outline=(40, 40, 40), width=4),
                                    d.line([cx - 20, 182, cx + 20, 182], fill=(40, 40, 40), width=4)))
    for mood in ("neutral", "smile", "worried"):
        save_sprite(character(mood=mood, **doc), img_dir, f"okafor {mood}", "human")
    nurse = dict(skin=(240, 200, 175), hair=(120, 80, 50), dress=(120, 180, 200))
    for mood in ("smile", "neutral"):
        save_sprite(character(mood=mood, **nurse), img_dir, f"nurse {mood}", "human")
    theo = dict(skin=(200, 150, 110), hair=(150, 100, 40), dress=(90, 160, 90), hair_long=False)
    for mood in ("grin", "normal", "worried", "sad"):
        save_sprite(character(mood=mood, **theo), img_dir, f"theo {mood}", "human")
    for mood in ("stern", "concerned"):
        save_sprite(seraph(mood), img_dir, f"seraph {mood}", "seraph")
    for mood in ("chatty", "neutral", "worried"):
        save_sprite(spirit((150, 200, 255), mood), img_dir, f"pim {mood}", "spirit")
        save_sprite(spirit((170, 240, 190), mood), img_dir, f"dross {mood}", "spirit")
    for mood in ("smile", "cold"):
        save_sprite(patron(mood), img_dir, f"patron {mood}", "patron")
    for mood in ("soft", "worried"):
        save_sprite(lantern(mood), img_dir, f"ember {mood}", "ember")
    for mood in ("sit", "stare", "meow", "loaf"):
        img = cat(mood)
        img.save(os.path.join(img_dir, f"miso {mood}.png"))
        if mood != "loaf":   # she only talks sitting up; "meow" is her open mouth
            cat("meow").save(os.path.join(img_dir, f"miso {mood} open.png"))
            TALKING.append(f"miso {mood}")
    write_talk_rpy(GAME)
    main_menu().save(os.path.join(GAME, "gui", "main_menu.png"))

    for name in ("theme", "morning", "unease", "ward", "entities", "watch", "voices"):
        write_ogg(os.path.join(aud_dir, name + ".ogg"), song(name))
    print("art and music written to", GAME)


if __name__ == "__main__":
    main()

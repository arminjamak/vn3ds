"""Draws the HOME menu banner of vn3ds.cia: banner.png (256x128, the 3D
banner shown above the icons) and banner.wav (the jingle it plays).

    python3 engine/cia/make_banner.py

Run once; both files are kept in the repository so build_cia.sh needs no
fonts. The picture is vn3ds's icon beside its name on a dark stage.
"""

import math
import os
import struct
import wave

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = ("/System/Library/Fonts/SFNSRounded.ttf", "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
         "/System/Library/Fonts/Helvetica.ttc", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")


def font(size):
    for f in FONTS:
        if os.path.exists(f):
            return ImageFont.truetype(f, size)
    return ImageFont.load_default()


def banner():
    im = Image.new("RGBA", (256, 128), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for y in range(16, 112):   # a rounded dark card with a soft gradient
        t = (y - 16) / 96
        c = (int(28 + 20 * t), int(24 + 12 * t), int(52 + 30 * t), 255)
        d.line([(8, y), (247, y)], fill=c)
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([8, 16, 247, 111], radius=18, fill=255)
    im.putalpha(mask)
    icon = Image.open(os.path.join(HERE, "..", "icon.png")).convert("RGBA").resize((72, 72), Image.LANCZOS)
    im.alpha_composite(icon, (22, 28))
    d = ImageDraw.Draw(im)
    d.text((106, 38), "vn3ds", font=font(40), fill=(255, 255, 255, 255))
    d.text((108, 82), "visual novels in 3D", font=font(13), fill=(200, 196, 230, 255))
    im.save(os.path.join(HERE, "banner.png"))


def jingle(rate=22050):
    notes = [(0.0, 659.25), (0.12, 783.99), (0.24, 987.77), (0.36, 1318.5)]
    n = int(rate * 1.6)
    out = []
    for i in range(n):
        t = i / rate
        v = 0.0
        for start, f in notes:
            if t >= start:
                u = t - start
                v += math.sin(2 * math.pi * f * u) * math.exp(-u * 3.2) * 0.22
        out.append(int(max(-1, min(1, v)) * 32767))
    with wave.open(os.path.join(HERE, "banner.wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(struct.pack(f"<{n}h", *out))


if __name__ == "__main__":
    banner()
    jingle()

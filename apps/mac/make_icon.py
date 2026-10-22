"""The Mac app's icon (AppIcon.icns): vn3ds's three stacked cards (the same
colours as engine/icon.png) on a macOS-style rounded square.

    python3 apps/mac/make_icon.py OUT.icns
"""

import os
import shutil
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw, ImageFilter

S = 1024


def draw():
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    # the squircle-ish tile, with a soft drop shadow
    shadow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle([100, 120, 924, 944], radius=185, fill=(0, 0, 0, 110))
    im.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(18)))
    tile = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    td = ImageDraw.Draw(tile)
    for y in range(100, 925):   # deep violet, lighter at the top
        t = (y - 100) / 824
        td.line([(100, y), (924, y)], fill=(int(64 - 26 * t), int(52 - 22 * t), int(118 - 40 * t), 255))
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).rounded_rectangle([100, 100, 924, 924], radius=185, fill=255)
    tile.putalpha(mask)
    im.alpha_composite(tile)
    d = ImageDraw.Draw(im)
    cards = [((90, 160, 230), (236, 282)), ((240, 120, 170), (306, 362)), ((255, 235, 200), (376, 442))]
    for colour, (x, y) in cards:   # back to front, each a little lower and to the right
        d.rounded_rectangle([x + 14, y + 18, x + 414, y + 298], radius=46, fill=(20, 14, 44, 120))
        d.rounded_rectangle([x, y, x + 400, y + 280], radius=46, fill=colour + (255,))
    x, y = cards[-1][1]
    for i, w in enumerate((250, 300, 190)):   # lines of text on the front card
        d.rounded_rectangle([x + 60, y + 70 + i * 58, x + 60 + w, y + 98 + i * 58], radius=14,
                            fill=(60, 50, 70, 255))
    return im


def main(out):
    img = draw()
    tmp = tempfile.mkdtemp()
    try:
        iconset = os.path.join(tmp, "AppIcon.iconset")
        os.makedirs(iconset)
        for size in (16, 32, 128, 256, 512):
            for scale in (1, 2):
                px = size * scale
                name = f"icon_{size}x{size}{'@2x' if scale == 2 else ''}.png"
                img.resize((px, px), Image.LANCZOS).save(os.path.join(iconset, name))
        subprocess.run(["iconutil", "-c", "icns", iconset, "-o", out], check=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "AppIcon.icns")

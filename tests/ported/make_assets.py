"""Draws the pictures of the ported-minigames test game into DIR/game/images."""
import os
import sys

from PIL import Image, ImageDraw

out = os.path.join(sys.argv[1], "game", "images")
os.makedirs(os.path.join(out, "lock"), exist_ok=True)


def save(name, size, draw, bg=(0, 0, 0, 0)):
    im = Image.new("RGBA", size, bg)
    draw(ImageDraw.Draw(im))
    im.save(os.path.join(out, name))


save("lock/plate.png", (800, 800), lambda d: d.rounded_rectangle((200, 250, 600, 600), 40, (150, 150, 160, 255)))
save("lock/cylinder.png", (800, 800), lambda d: d.ellipse((340, 340, 460, 460), (200, 170, 90, 255)))
save("lock/tension.png", (800, 800), lambda d: d.rectangle((400, 395, 700, 410), (90, 90, 100, 255)))
save("lock/pick.png", (800, 800), lambda d: d.rectangle((0, 396, 400, 404), (220, 220, 230, 255)))
save("lock/pick_broken.png", (800, 800), lambda d: d.rectangle((0, 396, 200, 404), (220, 220, 230, 255)))
save("arc.png", (100, 200), lambda d: d.arc((0, 0, 200, 200), 90, 270, (200, 60, 60, 255), 8))
save("dot.png", (20, 20), lambda d: d.ellipse((0, 0, 19, 19), (80, 255, 200, 255)))
save("harp_labels.png", (800, 450), lambda d: [d.ellipse((140, 240, 180, 280), (255, 255, 255, 255)),
                                               d.ellipse((340, 240, 380, 280), (255, 255, 255, 255)),
                                               d.rectangle((620, 60, 740, 100), (255, 255, 255, 255))])
save("harp_glow.png", (800, 450), lambda d: [d.ellipse((130, 230, 190, 290), (255, 220, 120, 255)),
                                             d.ellipse((330, 230, 390, 290), (255, 220, 120, 255)),
                                             d.rectangle((610, 50, 750, 110), (255, 220, 120, 255))])
for name, col in (("room.png", (40, 50, 80)), ("room low.png", (40, 80, 50)), ("room high.png", (80, 50, 40))):
    save(name, (800, 450), lambda d: None, bg=col + (255,))
save("disc.png", (40, 40), lambda d: [d.ellipse((0, 0, 39, 39), (230, 230, 230, 255)),
                                      d.rectangle((18, 0, 22, 20), (20, 20, 20, 255))])

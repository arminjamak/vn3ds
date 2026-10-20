# Test game for vnpack's ported minigames (tools/vnpack/ported.py): custom
# screens in the styles the adapters handle, mapped in vn3ds.json. The
# pictures are made by make_assets.py.

define config.name = "Ported Test"
define config.screen_width = 800
define config.screen_height = 450

init python:
    plate_img = "images/lock/plate.png"
    cylinder_img = "images/lock/cylinder.png"
    tension_img = "images/lock/tension.png"
    pick_img = "images/lock/pick.png"
    pick_broken_img = "images/lock/pick_broken.png"

    class TumblerLock(renpy.Displayable):
        def __init__(self, sweet_angle=10, pick_dmg=1.5, attempts=3, resize=800, **kwargs):
            super(TumblerLock, self).__init__(**kwargs)

    window_deg = 10
    step_steady = 3
    step_shaky = 6

screen vault_lock(lk):
    modal True
    add lk:
        align (0.5, 0.5)

default lock_ok = False
default plucks = 0
default tune = ""
default harp_bg = "images/room.png"
default points = 0
default swing_pos = 0
default swing_cw = True
default steady = True

transform orbit(r):
    subpixel True
    around (100, 100)
    radius 100 - 10
    angle r - 90

screen swing_bar():
    fixed:
        xalign 0.2 yalign 0.5
        xsize 100
        ysize 100 * 2
        add "images/arc.png"
        add "images/dot.png" at orbit(swing_pos)
        key "K_SPACE":
            action [Jump("after_swing")]

screen harp_map:
    modal True
    add harp_bg
    imagemap:
        ground "harp_labels"
        idle "harp_labels"
        hover "harp_glow"
        $ low = [ SetVariable("harp_bg", "room low"), SetVariable("plucks", plucks + 1), SetVariable("tune", tune + "l") ]
        $ high = [ SetVariable("harp_bg", "room high"), SetVariable("plucks", plucks + 1), SetVariable("tune", tune + "h") ]
        hotspot (100, 200, 120, 120) action low
        hotspot (300, 200, 120, 120) action high
        hotspot (600, 40, 160, 80) action [ Jump ("after_harp") ]

transform spin2:
    rotate 0
    linear 3.0 rotate 360
    repeat

transform cap_one:
    alpha 0.0
    pause 0.5
    linear 0.5 alpha 1.0
    pause 1.0
    linear 0.5 alpha 0.0

screen tape_play:
    frame:
        add "disc" at spin2
        xalign 0.1 yalign 0.02
    frame:
        at cap_one
        text _("Testing, one, two.")
        xpos 0.2 yalign 0.04
    timer 4 action [Hide("tape_play"), Jump("after_tape")]

label start:
    "Ported minigames test."
    $ lk = TumblerLock(sweet_angle=5, attempts=2)
    call screen vault_lock(lk)
    $ lock_ok = store._return
    if lock_ok:
        "The vault opened."
    else:
        "The vault stayed shut."
    call screen harp_map with dissolve
label after_harp:
    if "lh" in tune:
        "A rising tune."
    "You plucked [plucks] strings: [tune]."
    call screen swing_bar with dissolve
label after_swing:
    "Points: [points]."
    call screen tape_play
label after_tape:
    "The tape ended."
    return

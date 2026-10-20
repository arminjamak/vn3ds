# Camera grammar for Snapshot: a handheld documentary crew follows Aron.
#
# Use with Ren'Py's camera statement, e.g.
#     scene bg kitchen
#     camera at est_orbit            # B-roll: an establishing shot that loops
#     ...
#     camera at doc_medium(0.3)      # coverage: on whoever stands at xalign 0.3
#     camera at doc_close(0.7)       # tighter, for the line that matters
#     camera at doc_punch(0.7)       # a quick zoom-in when something lands
#     camera at doc_wide             # back out, still handheld
#     camera                         # no camera move at all
#
# Coverage shots cut straight to their framing, as a crew cuts between
# setups; only doc_punch moves (a quick zoom when something lands) and
# doc_creep (a slow drift in). Every shot except `camera` alone keeps a light
# handheld sway, so the whole
# game feels filmed by someone standing in the room. Establishing shots are
# slow loops that end where they began, so a scene can idle on them for as
# long as the player reads. On the 3DS, xrotate/yrotate tilt and orbit around
# the screen plane, so the layers of a scene slide past each other like a
# real camera move. (Ren'Py on PC ignores them without `perspective`; the
# offsets and zooms still play.)

# -- handheld: the crew's breathing, used inside every shot ---------------

transform doc_sway(amount=1.0):
    parallel:
        ease 1.9 yrotate (0.45 * amount)
        ease 2.6 yrotate (-0.35 * amount)
        repeat
    parallel:
        ease 2.3 xrotate (-0.3 * amount)
        ease 1.7 xrotate (0.25 * amount)
        repeat
    parallel:
        ease 3.1 rotate (0.35 * amount)
        ease 2.7 rotate (-0.3 * amount)
        repeat

# -- coverage --------------------------------------------------------------

transform doc_wide:
    zoom 1.06
    doc_sway(1.0)

# a medium shot centred on whoever stands at xalign `a`
transform doc_medium(a=0.5):
    zoom 1.28 xoffset ((a - 0.5) * 1280 * 1.28)
    doc_sway(1.0)

# a close-up: tighter and a little higher (faces sit high in the frame)
transform doc_close(a=0.5):
    zoom 1.55 xoffset ((a - 0.5) * 1280 * 1.55) yoffset (-210)
    doc_sway(0.8)

# close on someone small (Miso, Pim, Dross, Ember): the camera dips instead
# of rising, so their face stays above the text box
transform doc_low(a=0.5):
    zoom 1.4 xoffset ((a - 0.5) * 1280 * 1.4) yoffset (40)
    doc_sway(0.8)

# down on the floor (Miso): low and close, her face just above the text box
transform doc_floor(a=0.5):
    zoom 1.5 xoffset ((a - 0.5) * 1280 * 1.5) yoffset (200)
    doc_sway(0.7)

# (doc_close, doc_punch and doc_creep rise toward faces at standing height;
# for POV shots and CGs with low or off-centre subjects use est_dolly.)

# the camera operator reacts: a fast zoom-in on something that lands
transform doc_punch(a=0.5):
    ease 0.25 zoom 1.7 xoffset ((a - 0.5) * 1280 * 1.7) yoffset (-200)
    doc_sway(0.6)

# filming through a doorway / from across the room: slightly off-axis
transform doc_peek(a=0.5):
    zoom 1.2 xoffset ((a - 0.5) * 1280 * 1.2 + 90) yoffset 20
    doc_sway(0.7)

# a slow drift onto a face, for the quiet lines
transform doc_creep(a=0.5):
    zoom 1.25 xoffset ((a - 0.5) * 1280 * 1.25)
    ease 9.0 zoom 1.5 xoffset ((a - 0.5) * 1280 * 1.5) yoffset (-190)
    doc_sway(0.5)

# -- establishing shots (B-roll): slow, seamless loops -----------------------

# orbit a little around the room, showing it from a new angle and back
transform est_orbit:
    zoom 1.1
    yrotate -2.5
    ease 9.0 yrotate 2.5
    ease 9.0 yrotate -2.5
    repeat

# glide sideways across the place
transform est_pan:
    zoom 1.15 xoffset -70
    ease 11.0 xoffset 70
    ease 11.0 xoffset -70
    repeat

# rise slowly, like a crane or someone standing up with the camera
transform est_crane:
    zoom 1.12 yoffset 50 xrotate 1.5
    ease 10.0 yoffset -40 xrotate -1.5
    ease 10.0 yoffset 50 xrotate 1.5
    repeat

# look up into the sky (pair with a scene whose stars layer is procedural:
# the stars come out a little different every time)
transform est_stars:
    zoom 1.1 yoffset 60 xrotate 2.5
    ease 12.0 yoffset -60 xrotate -3.0
    ease 12.0 yoffset 60 xrotate 2.5
    repeat

# breathe in and out of the room
transform est_dolly:
    zoom 1.05 zpos 0
    ease 10.0 zpos 140
    ease 10.0 zpos 0
    repeat

# Converter regression test: lots of Ren'Py syntax in one file. Every image is
# a Solid so the test needs no art.

define e = Character('Eileen', color="#c8ffc8", image="eileen", what_prefix='"', what_suffix='"')
define n = Character(None, kind=nvl)
define pov = Character("[povname]", color="#ffcc00")
define slow = Dissolve(1.5)
define flash = Fade(0.1, 0.0, 0.4, color="#fff")
define audio.chime = "sfx/chime.ogg"
define MAX_TRIES = 3

image bg black = "#000"
image bg sky = Solid("#336699")
image eileen happy = Solid("#c8ffc8", xysize=(300, 600))
image eileen sad = Solid("#8899aa", xysize=(300, 600))
image eileen happy beach = Solid("#ffee88", xysize=(300, 600))
image side eileen = Solid("#c8ffc8", xysize=(100, 100))
image logo:
    "#ff00ff"
    pause 0.5
    "#00ffff"
    repeat

default povname = "Player"
default score = 0
default flags = ""

init python:
    def helper(x):
        return x * 2
    gui_like_value = 7

transform wobble(amount=10, t=0.3):
    on show:
        alpha 0.0
        linear 0.2 alpha 1.0
    block:
        linear t xoffset amount
        linear t xoffset -amount
        repeat 3
    xoffset 0

transform spin:
    parallel:
        linear 2.0 rotate 360
        rotate 0
        repeat
    parallel:
        ease 1.0 zoom 1.1
        ease 1.0 zoom 1.0
        repeat
    choice:
        xalign 0.3
    choice:
        xalign 0.7

label start:
    scene bg black
    with flash
    window show
    "Narration with {i}tags{/i}, an escaped [[bracket] and {{brace}."
    e happy "Hello, [povname]! This is a long line that will need to wrap across several lines in the textbox to make sure wrapping works as expected on the small screen."
    extend " And this part was extended."
    $ score += 10
    $ flags = flags + "a"
    python:
        if score > 5:
            score = score * 2
        else:
            score = 0
        bonus = 1 if score >= 20 else 0
    e "Score is [score], bonus [bonus], flags '[flags]'."
    call .local_part
    jump after_local

label .local_part:
    "Inside a local label."
    return

label after_local:
    show eileen sad at left, wobble(15)
    e "Attribute change keeps the tag."
    show eileen happy beach at right with ease
    e -beach "Removing an attribute with a minus."
    show eileen at spin
    show bg sky behind eileen
    $ tries = 0
    while tries < MAX_TRIES:
        $ tries += 1
        "Loop iteration [tries]."
    if tries == 3 and not (score < 0):
        "Loop finished correctly."
    menu choose_label:
        "Pick one. (choice menu with conditions)"
        "Hidden option" if False:
            "This should never show."
        "Visible option" if score > 0:
            $ picked = "visible"
        "Another option":
            $ picked = "another"
    "You picked [picked]."
    if picked == "visible":
        menu:
            "Nested menu without caption"
            "Go again":
                $ score = -1
                jump choose_label
            "Continue":
                pass
    n "NVL text is shown in the textbox."
    nvl clear
    pause 0.5
    $ renpy.pause(0.25, hard=True)
    play sound chime
    play music ["a.ogg", "b.ogg"] fadein 0.5
    queue music "c.ogg"
    voice "v1.ogg"
    e "Voice line."
    stop music fadeout 1.0
    show logo at truecenter with slow
    hide logo
    with dissolve
    show screen some_screen
    call screen another_screen
    $ unknown_function()
    $ x = helper(2)
    "Dynamic name next."
    $ povname = "Kim"
    pov "My name comes from a variable."
    "Formatting: [score!u] / [povname!u] / [povname!l]."
    $ msg = f"score={score}"
    "f-string: [msg]"
    window hide
    centered "{size=+10}The End{/size}"
    jump strings_and_screens

label strings_and_screens:
    $ name = renpy.input("Name?")
    $ name = name.strip()
    if name == "":
        $ name = "orion  "
    $ name = name.strip().title()
    $ echo = name[-1] * 3
    $ part = name[1:3]
    "Name [name], echo [echo], part [part]."
    call screen test_nav with dissolve
    "This line must not be reached."
    return

label nav_left:
    "Went left."
    return

screen test_nav:
    if name == "Orion":
        imagemap:
            ground "bg sky"
            hotspot (0, 300, 100, 100) action Jump('nav_left')
    textbutton "Go right" action Jump("nav_right")
    textbutton "Hidden" action Jump("nav_left") xalign 0.5

label nav_right:
    "Went right."
    return

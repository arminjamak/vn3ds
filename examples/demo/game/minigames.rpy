# Minigames are native to vn3ds (the Nintendo 3DS engine): there,
# vn3ds_minigame("id") plays the game and returns its 0-100 score.
# Ren'Py on PC runs this stand-in instead, so the story still flows.

init python:
    def vn3ds_minigame(name):
        return renpy.call_screen("vn3ds_minigame_stand_in", name=name)

screen vn3ds_minigame_stand_in(name):
    modal True
    frame:
        xalign 0.5
        yalign 0.5
        padding (40, 30)
        vbox:
            spacing 14
            text "Minigame: [name]" size 34
            text "This minigame is played in the Nintendo 3DS version (vn3ds)." size 22
            text "How would it have gone?" size 22
            textbutton "Brilliantly" action Return(85)
            textbutton "All right" action Return(55)
            textbutton "Badly" action Return(25)

# Lists every minigame Snapshot uses, so the title screen's Minigames menu has
# them all from the start (the story reaches each one in its own chapter).
# Nothing jumps here.
label vn3ds_all_minigames:
    $ _mg = vn3ds_minigame("quiz")
    $ _mg = vn3ds_minigame("miso")
    $ _mg = vn3ds_minigame("draw")
    $ _mg = vn3ds_minigame("lantern")
    $ _mg = vn3ds_minigame("snake")
    $ _mg = vn3ds_minigame("tower")
    $ _mg = vn3ds_minigame("invaders")
    return

# The game's own screens and Python on vn3ds (tools/vnpack/pyscreens.py,
# engine/source/pyscreen.c): a minigame class with a repeating timer, keys
# and frames placed by its state; call screen returning and jumping; an
# overlay with a button that opens a menu which sets a story variable.

define e = Character("Eileen")
default score = 0
default have_phone = False

init python:
    class Crawler:
        def __init__(self):
            self.ticks = 0
            self.cells = [(1, 1), (1, 2), (1, 3)]
            self.alive = True
            self.turns = []

        def tick(self):
            global score
            self.ticks += 1
            head = self.cells[0]
            self.cells.insert(0, (head[0] + 1, head[1]))
            self.cells.pop(-1)
            if self.ticks >= 10:
                self.alive = False
                score = self.ticks * 2

        def turn(self, d):
            self.turns.append(d)

default crawler = Crawler()

style mini_button:
    background "#4d4d4d"
    padding (10, 10)

screen mini(g=crawler):
    modal True
    style_prefix "mini"
    if g.alive:
        timer 0.1 repeat True action Function(g.tick)
    key "w" action Function(g.turn, "w")
    frame xysize 300,300 align .5,.5 background "#222":
        for n, c in enumerate(g.cells):
            frame xysize 20,20 offset c[0]*20, c[1]*20 background ("#0f0" if n == 0 else "#fff")
        text "Ticks: {}".format(g.ticks) align .5, 1.0
    hbox align 1.0, 1.0 spacing 10:
        button:
            text "Done"
            action Return(g.ticks)
        textbutton "Win" action Jump("won")

screen pick():
    vbox align .5, .5 spacing 20:
        textbutton "Win" action Jump("won")
        textbutton "Lose" action Return(0)

screen phone():
    imagebutton:
        idle Solid("#08f", xysize=(120, 120))
        xalign 1.0
        action ShowMenu("phone_menu")
        alt "Phone"

screen phone_menu():
    modal True
    frame align .5, .5:
        vbox:
            text "Score: [score]"
            textbutton "Set flag" action SetVariable("have_phone", True)
            textbutton "Close" action Return()

label start:
    e "Before the minigame."
    call screen mini
    e "The minigame returned [_return], score [score]."
    show screen phone
    e "The phone is shown."
    e "Flag is [have_phone]."
    hide screen phone
    e "The phone is hidden."
    call screen pick
    e "This line must not be reached."
    return

label won:
    e "You won."
    return

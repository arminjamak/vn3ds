# Shared definitions for "Snapshot". Every chapter file uses these; don't
# redefine them elsewhere.

# ---- people in Aron's world ------------------------------------------------
define a = Character("Aron", color="#8fd3ff", image="aron")
define at = Character("Aron", color="#8fd3ff", what_prefix="(", what_suffix=")")   # thoughts
define m = Character("Mira", color="#ff9a6b", image="mira")
define th = Character("Theo", color="#9be08f", image="theo")
define dr = Character("Dr. Okafor", color="#e8e8e8", image="okafor")
define nu = Character("Nurse Hale", color="#9fd4e6", image="nurse")
define stranger = Character("Stranger", color="#cccccc")
define radio = Character("Radio", color="#bbbbbb")

# ---- the ones Aron can't see -------------------------------------------------
define se = Character("Commander Seraphiel", color="#ffd36b", image="seraph")
define pi = Character("Pim", color="#a8ccff", image="pim")
define dro = Character("Dross", color="#b8f0c8", image="dross")
define em = Character("Ember", color="#ffb46e", image="ember")
define pa = Character("Lord Ashveil", color="#ff6b6b", image="patron")
define council = Character("The Council", color="#ff4f7a")
define vox = Character("???", color="#c9a8ff")
define sysmsg = Character("PROCESS", color="#7fffd4")

# ---- transitions -------------------------------------------------------------
define flash = Fade(0.1, 0.0, 0.6, color="#fff")
define blackout = Fade(0.8, 0.6, 0.8)
define slowfade = Fade(0.6, 0.2, 0.6)
define dis = Dissolve(1.0)
define quick = Dissolve(0.3)

# ---- positions and motion ---------------------------------------------------
transform slightleft:
    xalign 0.22 yalign 1.0

transform slightright:
    xalign 0.78 yalign 1.0

transform bob:
    yoffset 0
    block:
        ease 1.2 yoffset -10
        ease 1.2 yoffset 0
        repeat

transform float:
    yoffset 0
    block:
        ease 2.0 yoffset -18
        ease 2.0 yoffset 0
        repeat

transform popin(d=0.4):
    alpha 0.0 zoom 0.9
    parallel:
        ease d alpha 1.0
    parallel:
        ease d zoom 1.0

transform fadein(d=1.0):
    alpha 0.0
    linear d alpha 1.0

transform distant:
    xalign 0.5 yalign 1.0 zoom 0.75 alpha 0.85

# Things that come out of the screen at you (3D: in front of the glass).
transform closeup:
    xalign 0.5 yalign 1.0 zoom 1.25 zpos 120

transform flicker:
    alpha 1.0
    block:
        linear 0.08 alpha 0.4
        linear 0.08 alpha 1.0
        pause 1.7
        repeat

# ---- story state ------------------------------------------------------------
# All of these only nudge the story; no value is ever a game over.
default clarity = 0      # how much of the system Aron has worked out
default bond = 0         # how much he lets people in without proof they're real
default integrity = 0    # choosing to be the person he decided to be
default watch = 0        # how much the Lantern Watch can help him
default fog = 0          # how hard the medication / throttling pressed on him
default risky = 0        # times he chased clarity with stimulants
default told_mira = False
default told_theo = False
default kept_journal = False
default accepted_offer = False
default chapter = 0

# ---- the hidden design ------------------------------------------------------
# Seven principles, quietly shaped by choices in every chapter. In the last
# scene Aron presents the system they add up to. Positive leans to the first
# idea, negative to the second; 0 means undecided (he names it an open question).
default p_truth = 0      # + Disclosure: every being may learn what it is   / - The Gentle Veil: protect illusions that comfort
default p_share = 0      # + Equal share of consciousness for every world   / - Earned growth: worlds that cooperate earn more minds
default p_rest = 0       # + Rest: no throttling, minds get time to heal    / - Momentum: keep discovery fast, guard it with care
default p_spirits = 0    # + Personhood for spirits and pattern people      / - Honoured craft: spirits stay makers, paid in rest and song
default p_govern = 0     # + Every order votes (a parliament of beings)     / - Small guardians everywhere, like the Lantern Watch
default p_exit = 0       # + Open doors: anyone may move between worlds     / - Rootedness: stay and mend the world you're in
default p_less = 0       # + As little design as possible (Rams)            / - Active gardening: tend worlds closely

# ---- Miso -------------------------------------------------------------------
# Aron's cat. He explains his theories to her; she always ends the
# conversation the same way.
define cat = Character("Miso", color="#f0a050", image="miso")

transform catspot:
    xalign 0.85 yalign 1.0 zoom 0.9

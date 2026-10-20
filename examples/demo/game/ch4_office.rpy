# Snapshot - Chapter 4 (condensed): the office. Every route arrives here.
# Aron presents the system his choices built. The system (one of seven, each
# in two flavours, plus the open question) is chosen in ch4_ending_select
# from the seven hidden principles. Systems live in ch4_systems.rpy.
#
# Blocking. bg office looks at the glass wall and the green hill, where the
# brightness (the assembly) is: Aron stands at the table with the model
# world (slightleft), his companion beside him (center), Ashveil by the
# window (ch4_window, further back). bg office reverse is shot from the glass wall, from the
# assembly's side: the table is on the right, so Aron is at slightright,
# the companion still in the middle, the doorway (the back row) at left.
# Ashveil, by the glass, is behind that camera.

define ch4_listener = Character("The Listener", color="#f4f0ff")
define ch4_measurer = Character("The Measurer", color="#cfe3ff")
define ch4_assembly = Character("The Assembly", color="#ffffff")

label ch4_office:
    scene white with blackout
    scene bg office
    camera at est_dolly
    with slowfade
    play music "audio/office.ogg" fadein 1.5
    "A bright room in a world with no mistakes in it. A long dark table. A green hill. On the wall, in plain grey letters: less, but better."
    camera at doc_medium(0.23)
    "On the table, a small orange lantern, lit."
    if ch4_route == "architect":
        show aron neutral at slightleft
        show mira smile at center
        camera at doc_wide
        with dissolve
        "Mira stands beside him in her teal dress. The real one. She has his notebook under her arm, because she's the one who kept it."
        camera at doc_close(0.5)
        m grin "Breathe. You've explained worse things to my mother."
        camera at doc_close(0.32)
        a grin "Your mother is much scarier than this."
    elif ch4_route == "chosen":
        show aron neutral at slightleft
        show mira smile at center
        camera at doc_wide
        with dissolve
        "He said he'd come if she could come too. The Mira from the kitchen. Some of her, and some of the other. It comes to enough."
        camera at doc_close(0.5)
        m curious "Is this the bit where you explain the universe? Do I need a coffee for this?"
        camera at doc_close(0.32)
        a smile "There's coffee after. I asked."
    elif ch4_route == "lantern":
        show aron neutral at slightleft
        show ember tender at center
        camera at doc_wide
        with dissolve
        "They found him at the bottom of somebody else's staircase, lantern in hand, and waited politely until the bakery woman smiled."
        camera at doc_medium(0.5)
        em grin "Don't be nervous. They're only the oldest things there are."
        camera at doc_close(0.32)
        a grin "That's very reassuring, Ember. Thank you."
    elif ch4_route == "longfog":
        show aron tired at slightleft
        show theo neutral at center
        camera at doc_wide
        with dissolve
        "The fog lifted one ordinary Tuesday and didn't come back. That afternoon someone came to fetch the man who wrote the notebook the boy found."
        camera at doc_close(0.5)
        th grin "Bro. I parked on a cloud. Is that allowed? There was no sign."
        show aron smile
    else:
        show aron neutral at slightleft
        camera at doc_wide
        with dissolve
        "He came alone. That's all right. He's practised being kind to rooms where nobody might be listening."
        show aron thinking
        camera at doc_creep(0.32)
        at "Nobody beside me yet. Yet. I'm learning to notice the yet."
    if ch4_ashveil_fasts:
        camera at doc_peek(0.15)
        "At the end of the table there's an empty chair. Nobody needs to be told whose it is."
    else:
        show patron thinking at ch4_window with dissolve
        camera at doc_medium(0.84)
        "Lord Ashveil stands by the window, thinner. Hungry, and choosing to be. He's only here to watch how it's done."
    if ch4_route != "lantern" and watch >= 6:
        call ch4_office_back
        show pim chatty at left, bob
        camera at doc_medium(0.14)
        with dissolve
        pi grin "Psst. Bro. Watch delegation. We're the back row. The moth's on the lamp."
        hide pim with dissolve
    call ch4_office_front
    camera at est_crane
    with dissolve
    "Then the others arrive, or rather the room turns out to have been inside them all along: a brightness that has opinions."
    show aron awe
    "Older than the Council, and nothing like it. Not hungry. Whatever they were, they finished eating a very long time ago."
    camera at est_dolly
    ch4_listener "Architect. The network that runs your existence has applied to join us, and to be trusted with its own experiments."
    ch4_measurer "Most applications are clever and greedy, or kind and vague. Show us the design. What it costs, and what it does on a bad day."
    call ch4_office_back
    camera at doc_medium(0.68)
    with dissolve
    if kept_journal:
        a determined "I've kept a notebook since the first morning. First line: 'If this is a test, I want to pass it by being kind.' This is that line, with the maths filled in."
    else:
        a determined "I wrote one line, the first morning, and then mostly lived it. 'If this is a test, I want to pass it by being kind.' This is what survived contact."
    camera at doc_close(0.68)
    a "The floor is one line. Every sentient being in every world gets a fair share of its world. And it works without knowing which world is real."
    call ch4_cut_council
    ch4_measurer "...Every design we have been shown begins by locating the original and protecting it. Yours refuses to look."
    call ch4_cut_aron
    a neutral "I spent a long time sorting the people around me into real and rendered. It nearly cost me everyone. I'm not building that into the foundations."
    call ch4_broll_worlds
    a "And one piece of evidence. Sealed in protection, my mind leaked. A cab driver told me my own story. A café table said 'protected'."
    call ch4_office_back
    show aron grin
    camera at doc_medium(0.68)
    with dissolve
    a "Everyone thought I was losing my mind. I mostly took notes. One mind's design really does reshape a world. I'm asking to do it on purpose. Carefully."
    show aron determined
    jump ch4_ending_select

# ---- the two angles of the office, and the cutaways ----------------------------------
# Each sets the stage only; the caller adds a camera and a transition (the
# ch4_cut_* ones do both).
label ch4_office_front:
    scene bg office
    show aron neutral at slightleft
    if ch4_route == "architect" or ch4_route == "chosen":
        show mira smile at center
    elif ch4_route == "lantern":
        show ember tender at center
    elif ch4_route == "longfog":
        show theo neutral at center
    if not ch4_ashveil_fasts:
        show patron neutral at ch4_window
    return

label ch4_office_back:
    scene bg office reverse
    show aron determined at slightright
    if ch4_route == "architect" or ch4_route == "chosen":
        show mira smile at center
    elif ch4_route == "lantern":
        show ember tender at center
    elif ch4_route == "longfog":
        show theo neutral at center
    return

# Aron presenting, from the assembly's side
label ch4_cut_aron:
    call ch4_office_back
    camera at doc_close(0.68)
    with quick
    return

# the assembly: they have no faces, so the whole bright room is their shot
label ch4_cut_council:
    call ch4_office_front
    camera at doc_wide
    with quick
    return

# the assembly deciding: the whole room, the hill lit
label ch4_cut_brightness:
    call ch4_office_front
    camera at est_dolly
    with dissolve
    return

# Ashveil listening at the window (only when he isn't fasting)
label ch4_cut_ashveil:
    call ch4_office_front
    show patron embarrassed
    camera at doc_medium(0.84)
    with quick
    return

# B-roll while Aron talks: what he is describing
label ch4_broll_worlds:
    scene bg worlds
    camera at est_pan
    with dissolve
    return

label ch4_broll_spawning:
    scene bg spawning
    camera at est_crane
    with dissolve
    return

label ch4_broll_earth:
    scene bg earth
    camera at est_stars
    with dissolve
    return

# ---- choosing the system -------------------------------------------------------------
label ch4_ending_select:
    # Each principle's score counts its own lean twice and its two cousins once.
    $ ch4_s_truth = 2 * abs(p_truth) + abs(p_exit) + abs(p_govern)
    $ ch4_s_share = 2 * abs(p_share) + abs(p_spirits) + abs(p_govern)
    $ ch4_s_rest = 2 * abs(p_rest) + abs(p_less) + abs(p_spirits)
    $ ch4_s_spirits = 2 * abs(p_spirits) + abs(p_share) + abs(p_rest)
    $ ch4_s_govern = 2 * abs(p_govern) + abs(p_truth) + abs(p_share)
    $ ch4_s_exit = 2 * abs(p_exit) + abs(p_truth) + abs(p_less)
    $ ch4_s_less = 2 * abs(p_less) + abs(p_rest) + abs(p_exit)

    # Ties go to the earlier one in: less, truth, share, rest, spirits, govern, exit.
    $ ch4_win = "less"
    $ ch4_best = ch4_s_less
    if ch4_s_truth > ch4_best:
        $ ch4_win = "truth"
        $ ch4_best = ch4_s_truth
    if ch4_s_share > ch4_best:
        $ ch4_win = "share"
        $ ch4_best = ch4_s_share
    if ch4_s_rest > ch4_best:
        $ ch4_win = "rest"
        $ ch4_best = ch4_s_rest
    if ch4_s_spirits > ch4_best:
        $ ch4_win = "spirits"
        $ ch4_best = ch4_s_spirits
    if ch4_s_govern > ch4_best:
        $ ch4_win = "govern"
        $ ch4_best = ch4_s_govern
    if ch4_s_exit > ch4_best:
        $ ch4_win = "exit"
        $ ch4_best = ch4_s_exit

    # The winner's sign sets the flavour. If the winner itself is 0 (it won
    # on its cousins), the cousins' combined lean decides.
    $ ch4_open = False
    $ ch4_plus = True
    if ch4_best == 0:
        $ ch4_open = True
        $ ch4_win = "less"
        jump ch4_sys_less
    elif ch4_win == "less":
        if p_less < 0 or (p_less == 0 and p_rest + p_exit < 0):
            $ ch4_plus = False
        jump ch4_sys_less
    elif ch4_win == "truth":
        if p_truth < 0 or (p_truth == 0 and p_exit + p_govern < 0):
            $ ch4_plus = False
        jump ch4_sys_truth
    elif ch4_win == "share":
        if p_share < 0 or (p_share == 0 and p_spirits + p_govern < 0):
            $ ch4_plus = False
        jump ch4_sys_share
    elif ch4_win == "rest":
        if p_rest < 0 or (p_rest == 0 and p_less + p_spirits < 0):
            $ ch4_plus = False
        jump ch4_sys_rest
    elif ch4_win == "spirits":
        if p_spirits < 0 or (p_spirits == 0 and p_share + p_rest < 0):
            $ ch4_plus = False
        jump ch4_sys_spirits
    elif ch4_win == "govern":
        if p_govern < 0 or (p_govern == 0 and p_truth + p_share < 0):
            $ ch4_plus = False
        jump ch4_sys_govern
    else:
        if p_exit < 0 or (p_exit == 0 and p_truth + p_less < 0):
            $ ch4_plus = False
        jump ch4_sys_exit

# ---- the six supporting rules: one line each ------------------------------------------
# Called from each system. Skips the principle that already won. The camera
# drifts along the seven principle cards above the sideboard while he talks.
label ch4_office_rules:
    call ch4_office_back
    camera at doc_medium(0.68)
    with quick
    a neutral "The rest are supporting rules. A good design has one main idea and then gets out of its own way."
    camera at est_pan
    if ch4_win != "truth":
        if p_truth > 0:
            a "On truth: any being that asks what it is gets a true answer, with someone sitting beside it."
        elif p_truth < 0:
            a "On truth: comforting illusions are protected, as long as they're honest underneath."
        else:
            a "On truth: open question. I've been told the truth and been spared it, and both saved me once."
    if ch4_win != "share":
        if p_share > 0:
            a "On minds: every world gets the same chance at being awake. No more worlds full of extras."
        elif p_share < 0:
            a "On minds: worlds earn more minds by care, never by output. The floor stays under all of it."
        else:
            a "On minds: open question. Equal shares or earned growth. I gave an hour once and kept one once."
    if ch4_win != "rest":
        if p_rest > 0:
            a "On rest: no more throttling, ever. A struggling mind gets time to heal, not a dimmer switch."
        elif p_rest < 0:
            a "On pace: discovery stays fast, and every fast mind gets someone watching its heart rate."
        else:
            a "On rest: open question. I've slept when I needed to and pushed when I shouldn't. The line moves."
    if ch4_win != "spirits":
        if p_spirits > 0:
            a "On spirits: they're people if they want to be. Asked, not assigned. A spirit can clock off for a sunrise."
        elif p_spirits < 0:
            a "On spirits: they stay makers, honoured ones, paid in rest and song, their craft named out loud."
        else:
            a "On spirits: open question. Personhood or honoured craft. We ask each spirit, which is slow, and right."
    if ch4_win != "govern":
        if p_govern > 0:
            a "On governance: every order votes. A parliament of beings, loud and slow, spirits included."
        elif p_govern < 0:
            a "On governance: small guardians in every world, like the Lantern Watch. Not a chamber that eats."
        else:
            a "On governance: open question. A parliament or a thousand small watches. Both cost something."
    if ch4_win != "exit":
        if p_exit > 0:
            a "On doors: any mind may move between worlds, and come back. No tickets. No price about who's real."
        elif p_exit < 0:
            a "On doors: you mend the world you're in first. Leaving is for emergencies. Help travels to you."
        else:
            a "On doors: open question. I want doors that exist and roots that hold. I don't know the ratio."
    if ch4_win != "less":
        if p_less > 0:
            a "On the hand that runs it: as light as possible. One change, a long silence, then listen."
        elif p_less < 0:
            a "On the hand that runs it: close and attentive. A gardener walking the rows, not a farmer counting yield."
        else:
            a "On the hand that runs it: open question. Touch lightly or tend closely. Keep asking every century."
    call ch4_cut_brightness
    return

# ---- the close -----------------------------------------------------------------------
# From here the camera calms down: fewer cuts, wider, steadier.
label ch4_office_close:
    camera at ch4_calm
    ch4_listener "One thing more. A design that needs to know where the original is can be broken by finding it. Yours cannot."
    ch4_measurer "We do not know which of our worlds is real either. Nobody does. We had not expected a child's toybox to teach us that."
    call ch4_office_back
    show aron surprised
    camera at doc_close(0.68)
    with dissolve
    a "...Huh. I thought I was the only one who didn't know."
    call ch4_office_front
    show aron curious
    camera at est_dolly
    with dissolve
    ch4_listener "The network will need someone to keep its 'better' honest. Not to rule. To steer. Will you?"
    call ch4_office_back
    camera at doc_close(0.68)
    with dissolve
    if ch4_route == "chosen":
        a smile "I said no to their desk. I'll say yes to this, from the kitchen table. Two days a week. With her."
        camera at doc_close(0.5)
        m grin "Three days. You'll get bored on Thursdays."
    elif ch4_route == "lantern":
        a "Yes. As long as I can still carry the lantern. I don't want to steer anything I've stopped visiting."
        camera at doc_medium(0.5)
        em tender "He'll come back covered in other people's rain. Every time. I'll make tea."
    elif ch4_route == "longfog":
        a smile "Yes. Slowly. I think slowly now. I think that might be what the job needs."
        camera at doc_close(0.5)
        th laugh "Bro. Chief architect of everything. I'm going to need a bigger croissant."
    elif ch4_route == "architect":
        a "Yes. I already said it once at a drafting table. I'll keep saying it, every morning, on purpose."
        camera at doc_close(0.5)
        m tender "Every morning at 7:07. I'll make sure."
    else:
        a smile "Yes. Nobody's standing next to me. That's all right. The job's about the ones who aren't in the room."
    camera at doc_medium(0.68)
    a determined "I'll do it the way my favourite designer made radios and alarm clocks. Useful. Honest. Unobtrusive. Built to last. Thorough to the last detail."
    camera at doc_creep(0.68)
    a tender "Down to the breath of the man at number fourteen. And as little of it as possible. Less, but better."
    camera at ch4_calm
    a determined "Not the nearest good. The absolute best. And I'll check it the way I checked my first theory: is it kind to someone who'll never know I did it?"
    call ch4_office_front
    show aron neutral
    camera at ch4_calm
    with dissolve
    if integrity >= 8:
        ch4_measurer "You held to that when nobody was watching. We can see the record."
    elif bond >= 8:
        ch4_listener "You let them in without proof, over and over. It will make you a good steerer. It will also hurt."
    else:
        ch4_listener "You are not finished. Good. Nothing that steers should think it is finished."
    jump ch4_coda

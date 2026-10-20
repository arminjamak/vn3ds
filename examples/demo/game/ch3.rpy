# Chapter 3 - "Snapshot" (condensed, about 32 minutes).
# Life in the protected world: smooth, looping, a Mira who is sometimes too
# right. Aron tests the leaks quietly, as a hobby. The leak escalates; the
# reveal (he was moved in the ambulance at the end of ch1, and his intake
# file says nobody was ever steering him); the relapse scare (with a fourth
# way: editing the voices again, ch3_voices_edit); a few voluntary nights on
# the ward, where Osric's walkers ("Herons") and troopers ("Understudies")
# come over the garden wall to free him and the light sends them home
# (ch3_breakout, ch3_cut_shadow); the fight and the night; Theo's crisis;
# Ember's trial; the Council; and Ashveil's offer. Riddles keep arriving,
# quieter, and go on the board. Ends unanswered: chapter 4 opens with the
# answer.
#
# Shot like the rest of the game (camera.rpy): a handheld crew follows Aron.
# Each new place opens on an establishing shot, then coverage on whoever
# speaks. Camera centres used below (where a sprite's face actually sits):
#   aron, mira, theo, okafor, patron (460 px wide): slightleft 0.32,
#     center 0.5, slightright 0.68, left 0.18, right 0.82
#   seraph (640 px): center 0.5, slightright 0.64
#   ember (340 px), pim, dross (360 px): slightleft 0.29-0.30,
#     slightright 0.70, left 0.14, right 0.86. They are short: their faces sit
#     low, so they get doc_medium, never doc_close/creep/punch.
#   ch3_doorway (kitchen reverse, the hall door): 0.28
#   ch3_far_left / ch3_far_right (seen through the kitchen door): 0.40 / 0.60
# Reverse angles swap sides: whoever is on the left in `bg kitchen` is on the
# right in `bg kitchen reverse`, at the same distance.

define ch3_varga = Character("Mrs. Varga", color="#e3c9b0")
define ch3_barista = Character("Barista", color="#e0c39a")
define ch3_shop = Character("Shop assistant", color="#d0b890")
define ch3_tannoy = Character("Tannoy", color="#bbbbbb")
define ch3_crowd = Character("Passengers", color="#cccccc")
define ch3_driver = Character("Bus driver", color="#c0c0c0")
define ch3_mourne = Character("Lady Mourne", color="#c88aff")
define ch3_regent = Character("The Grey Regent", color="#b8b8d0")

# Blocking for this chapter's new angles.
transform ch3_doorway:          # bg kitchen reverse: standing in the hall door
    xalign 0.15 yalign 1.0

transform ch3_far_left:         # bg kitchen door: inside the room, seen from the hall
    xalign 0.36 yalign 1.0 zoom 0.8

transform ch3_far_right:
    xalign 0.64 yalign 1.0 zoom 0.8

default ch3_said_off = False
default ch3_asked_theo = False
default ch3_pill = False
default ch3_left = False
default ch3_mira_came = False
default ch3_answered = False
default mg_snake = 0
default mg_tower = 0

label chapter3:
    $ chapter = 3
    camera
    scene black with blackout
    centered "Chapter 3\n\nSnapshot"
    pause 1.0

    scene pov ceiling
    camera at est_dolly
    with slowfade
    play music "audio/protected_world.ogg" fadein 1.5
    "7:07."
    "The Braun clock says it the way it always does: plainly, without opinion."
    at "My ceiling. The crack shaped like Portugal. My bed, with me in it, which is where I left me."
    at "Last night: the roof. An orange light on the edge of the city, blinking three times. Then the stairs, then Miso, then sleep."
    at "I decided something up there. A secret mission, for the rest of my life. It still feels true in daylight. Good sign."
    vox "...a copy of a copy... the spark lives in the gap..."
    at "And good morning to you. Quieter on the tablet, fewer, still there. Riddle for the board."
    scene bg bedroom
    show aron neutral at center
    show miso loaf at catspot
    camera at est_orbit
    with dissolve
    "Miso is folded at the foot of the bed into a perfect orange loaf."
    camera at doc_wide
    "He sits up. The duvet slides off him in one smooth fold and lands neatly on the floor."
    camera at doc_medium(0.5)
    show aron curious
    "Not crumpled. Folded."
    show aron tired
    if fog >= 3:
        "The medication is still there, wet sand from the neck down. But it's tidier this morning. As if someone had ironed it."
    else:
        "He's tired, the way he's always tired since the ward. But it's a tidier tiredness. As if someone had ironed it."
    camera at doc_close(0.5)
    a grin "Less, but better. Even my exhaustion has been designed, Miso. Dieter Rams would approve."
    camera at doc_wide
    "Miso does not open her eyes. Miso has never once taken a meeting before breakfast."

    scene bg kitchen
    show aron neutral at slightleft
    show mira smile at slightright
    camera at est_pan
    with dissolve
    m "You're up. You came down off that roof last night grinning like somebody had proposed to you."
    camera at doc_medium(0.32)
    a grin "Somebody sort of did. The universe, possibly. I'm still reading the small print."
    camera at doc_wide
    show mira laugh
    "Outside, the bird drops onto the wire and folds its wings. The oven clock says 7:07."
    camera at doc_close(0.32)
    show aron thinking
    show mira smile
    at "I've been awake for at least five minutes. Unless the minute waited for me."
    camera at doc_medium(0.68)
    "The coffee machine starts. The gurgle, the hiss, the two dry coughs at the end. Exactly right."
    "Like a recording of itself."
    camera at doc_close(0.32)
    show aron grin
    at "'Exactly right' goes in the notebook. Under 'suspiciously excellent'."
    scene bg kitchen table
    show aron neutral at slightleft
    show mira smile at slightright
    camera at doc_medium(0.68)
    with dissolve
    m smile "Tea. One sugar."
    scene pov cup
    camera at est_dolly
    with quick
    "A pale brown circle. A small trembling window in it, and the wire, and the bird."
    "He tastes it. One sugar."
    scene bg kitchen table
    show aron grin at slightleft
    show mira smile at slightright
    camera at doc_medium(0.32)
    with quick
    a "You remembered the sugar. You never remember the sugar. It's the only flaw I've found in you in four years."
    camera at doc_close(0.68)
    m happy "Then today's a good day."
    show mira smile
    "She smiles the way she always smiles. The left side first, then the right. Freckles rearranging themselves."
    camera at doc_creep(0.32)
    show aron thinking
    at "It's lovely. It's her. Isn't it?"
    # the reverse: from the counter, looking back at the table. Mira's chair is
    # on the left now, his on the right.
    scene bg kitchen reverse
    show mira smile at slightleft
    show aron neutral at slightright
    camera at doc_medium(0.32)
    with quick
    if told_mira:
        m "So. How's the mission? Day one."
        "She says it lightly, the way you'd ask about a hobby. Not long ago the same idea made her cry in a corridor."
        camera at doc_close(0.68)
        show aron thinking
        at "That's exactly what I wanted her to say. Word for word. Which is wonderful, and which I'll write down later, very quietly."
    else:
        m grin "You've got the eyebrow. It means you've noticed something and you're deciding whether to tell me."
        camera at doc_close(0.68)
        show aron embarrassed
        at "She doesn't know about the mission. But she always knows when I'm deciding."
    camera at doc_close(0.32)
    show mira curious

    menu:
        m "Well?"

        "Tell her something feels off":
            $ p_truth += 1
            $ bond += 1
            $ ch3_said_off = True
            camera at doc_close(0.68)
            a neutral "Honestly? Something feels off. Not wrong. Smooth. The coffee's right. The clock waited for me. You remembered the sugar."
            camera at doc_close(0.32)
            m curious "And those are bad things?"
            camera at doc_medium(0.68)
            a thinking "No. That's what's bad about them."
            camera at doc_close(0.32)
            m smile "I know what you mean. I feel it too, sometimes. Like the world's been ironed."
            camera at doc_creep(0.68)
            show aron curious
            at "Ironed. That's exactly the word I'd have used. She always finds the word. That's not evidence of anything."
            show aron tender
            at "If she's a copy, I just told a copy. If she isn't, I told the truth to the woman I love. I'd rather have said it."

        "Keep it light. Have breakfast":
            $ p_truth -= 1
            $ integrity += 1
            camera at doc_medium(0.68)
            a neutral "Breakfast. Then errands. Then coffee with Theo. A normal Saturday."
            camera at doc_close(0.32)
            m happy "A normal Saturday. Look at you."
            camera at doc_wide
            a grin "I contain multitudes. Most of them want toast."
            show mira laugh
            "The toast is golden all the way across. Not one burnt corner."
            camera at doc_creep(0.68)
            show aron tender
            show mira smile
            at "I won't put this on her today. She's carried enough of my weather. It's a hobby. Hobbies can be private."

    camera at doc_medium(0.32)
    m smile "Bin on your way out. And say hello to Mrs. Varga."

label ch3_errands:
    scene bg street
    camera at est_pan
    with dissolve
    play music "audio/the_leak.ogg" fadein 1.5
    "Errands. Bin, bakery, coffee with Theo. And a private game on the side: let's see what the street says today."
    scene pov birds
    camera at doc_creep(0.5)
    with dissolve
    "On the long wire over the road, three birds. Evenly spaced. Always the same three."
    at "Morning, lads. Same shift as always?"
    scene bg street
    show aron neutral at slightleft
    camera at doc_wide
    with dissolve
    "Mrs. Varga is on her front step with her tartan trolley, sweeping, very upright."
    ch3_varga "Cold for the season, isn't it?"
    camera at doc_medium(0.32)
    a smile "Morning, Mrs. Varga. It is a bit."
    show aron neutral
    "It's warm. It's been warm all week. He takes the bin down. Lid, bag, lid. On the way back up the path, she looks up."
    ch3_varga "Cold for the season, isn't it?"
    camera at doc_close(0.32)
    a grin "We did this thirty seconds ago, Mrs. Varga."
    ch3_varga "Did we, dear? Cold for the..."
    camera at doc_punch(0.32)
    show aron surprised
    "She stops on the 's'. The broom stops mid-sweep. A falling leaf hangs in the air beside her shoulder."
    "One second. Two."
    ch3_varga "...season, isn't it?"
    camera at doc_wide
    "The leaf lands. The broom moves. She smiles at him as if nothing happened."
    camera at doc_close(0.32)
    show aron grin
    at "Two seconds of freeze-frame, leaf included. Whoever's running this: ten points for production values."
    show aron thinking
    at "Or I blinked and my brain filled in the rest. Brains do that. Mine especially."
    camera at doc_medium(0.32)
    show aron neutral
    "He writes, small: Mrs. Varga froze mid-word. Approx. 2 sec. Leaf also. Underneath: do not mention the leaf to Mira."

    scene bg cafe
    show theo happy at slightright
    show aron smile at slightleft
    camera at est_orbit
    with dissolve
    th "There he is! Mira says you sat on the roof till midnight talking to the sky. Very Victorian."
    camera at doc_medium(0.32)
    a embarrassed "I was having a moment."
    camera at doc_medium(0.68)
    th grin "You were having a cold. Hey, you know what the barista said to the espresso? 'You've bean on my mind.'"
    camera at doc_close(0.32)
    a neutral "You told me that one on Tuesday."
    camera at doc_close(0.68)
    th curious "Did I? Must be a classic."
    th grin "Hey, you know what the barista said to the espresso?"
    camera at doc_wide
    show aron curious
    "Same words. Same laugh. He slaps the table in exactly the same place, next to exactly the same coffee ring."
    camera at doc_creep(0.32)
    show aron thinking
    at "Okafor would say: notice it, name it, don't build a cathedral on it. Fine. A small shed, then."

    menu:
        at "Time for a quiet little experiment?"

        "Test him. Say something absurd":
            $ clarity += 1
            $ p_spirits -= 1
            jump ch3_cafe_test

        "Ask how he's really doing":
            $ bond += 1
            $ p_spirits += 1
            $ ch3_asked_theo = True
            jump ch3_cafe_ask

label ch3_cafe_test:
    # the reverse: from the window seats, the bar behind them. Theo is on the left now.
    scene bg cafe reverse
    show theo neutral at slightleft
    show aron neutral at slightright
    camera at doc_medium(0.68)
    with quick
    a "Theo. The moon is a wheel of cheese and I've been elected its mayor."
    camera at doc_punch(0.32)
    "For half a second Theo's face does nothing at all. Not blank. Waiting. Like a page that hasn't loaded."
    camera at doc_close(0.32)
    th grin "Bro, the universe doesn't run on your schedule."
    camera at doc_close(0.68)
    a curious "That's not an answer to what I said."
    camera at doc_medium(0.32)
    th grin "It's an answer to everything you say. Drink your coffee, Mayor."
    camera at doc_wide
    show aron thinking
    show theo neutral
    "Under the table Aron writes: Theo. Absurd input. 0.5 sec delay. Answer: his line. Like a default."
    camera at doc_creep(0.68)
    show aron embarrassed
    "The shame arrives a moment later, like a step you missed. He just ran an experiment on his best friend. With cheese."
    camera at doc_close(0.32)
    th curious "You okay? You look like you're doing long division."
    camera at doc_close(0.68)
    a tired "Just tired. Pills."
    camera at doc_close(0.32)
    th neutral "Yeah. Yeah, I know."
    show theo tired
    "For a moment Theo looks very tired too. Then it's gone."
    show theo neutral
    jump ch3_cafe_after

label ch3_cafe_ask:
    scene bg cafe reverse
    show theo neutral at slightleft
    show aron neutral at slightright
    camera at doc_medium(0.68)
    with quick
    a "Forget the espresso. How are you actually doing?"
    camera at doc_medium(0.32)
    th grin "Me? I'm a delight. Ask anyone."
    camera at doc_close(0.68)
    a neutral "I'm asking you."
    camera at doc_creep(0.32)
    show theo thinking
    "Something crosses Theo's face. Not the waiting look. Something with weight in it."
    th sad "Honestly? Bit rubbish, mate. Studio's a lot. I'm not sleeping. My head's loud at night."
    th smile "Nothing like what you've been through. Don't worry about it."
    camera at doc_close(0.68)
    a smile "I'm going to worry a little. You've done enough worrying about me for both of us."
    camera at doc_close(0.32)
    th embarrassed "...Thanks for asking, though. Nobody really asks."
    camera at doc_wide
    show theo laugh
    "He says it to the cup. Then the old laugh comes back."
    camera at doc_close(0.68)
    show aron thinking
    at "That wasn't a loop. Or it was the most convincing loop I've ever met."
    jump ch3_cafe_after

label ch3_cafe_after:
    scene bg cafe window
    show aron neutral at center
    camera at doc_wide
    with dissolve
    "Theo goes. The door chimes behind him. The barista calls out to the room."
    ch3_barista "Have a beautiful day, gentlemen!"
    camera at doc_medium(0.5)
    show aron curious
    "There's only Aron left. She said it to an empty doorway."
    # overheard: the crew films from the end of the bar, past the espresso machine
    scene bg cafe corner
    show aron neutral at center
    camera at doc_peek(0.5)
    with quick
    "At the next table a woman with a laptop says, quite clearly, to a man with a crossword:"
    stranger "...honestly, I think the whole thing's protected. Nothing gets in or out."
    stranger "Mm. A-30 across. Eleven letters."
    camera at doc_punch(0.5)
    a surprised "..."
    camera at doc_peek(0.5)
    show aron curious
    "When he looks again they're talking about Portugal. The man fills in a word."
    camera at doc_close(0.5)
    show aron thinking
    at "Protected. My word. The one I wrote on the wall before the ward. And A-30. A for Aron. I'm thirty."
    show aron smile
    at "People say 'protected' all the time. Crosswords have numbers. I know. I know. It still goes in the book."

    # The leak grows: Crown of the Worm (minigame "snake", nudges p_share).
    scene cg notebook
    camera at est_dolly
    with dissolve
    "He opens the notebook to write it down. Beside his first line there's a dot on the page that isn't ink. A square of light, bright green, the size of a sugar grain."
    "Then another. Then a short row of them, crawling, like a worm made of pixels. Where it touches a bright dot, it eats it, and gets longer."
    at "Hello. You're new. And hungry. Let's see where you go."
    $ mg_snake = vn3ds_minigame("snake")
    $ p_share += (1 if p_share >= 0 else -1) * mg_snake / 50.0
    camera at doc_wide
    if mg_snake >= 70:
        "The worm swallows the last bright dot, and something settles on its head: a crown of tiny lights. Then it sinks into the paper like water into sand."
        at "It ate the leak. Or it is the leak, and it's growing. Either way it wore a crown and looked very pleased with itself."
    elif mg_snake >= 40:
        "The worm grows fat on bright dots, loses track of itself, curls round and bites its own tail. It fizzes out into the grain of the paper."
        at "Half a worm. Half a data set. I'll take it."
    else:
        "The worm trips over itself almost at once and comes apart into green dust. The page is a page again, with his handwriting on it."
        at "A floater in my eye, probably. A floater that ate three dots."
    "The barista wipes the next table, humming, and doesn't look over."
    stop music fadeout 2.0

# ---------------------------------------------------------------------------
# CUT 1: the foundry, and the leak
# ---------------------------------------------------------------------------
label ch3_cut_foundry:
    camera
    scene cg static with flash
    pause 0.3
    scene bg foundry
    camera at est_pan
    with fade
    play music "audio/purgatorium_shift.ogg" fadein 1.5
    sysmsg "PROTECTED LANE A-30 (copy of Snapshot 7,412). Pattern fidelity: 99.2%. Conscious agents in lane: 1."
    sysmsg "LEAK REPORT: pattern VARGA, frame hold 2.1 sec. Cafe patterns: subject vocabulary ('protected', 'A-30')."
    if mg_snake >= 70:
        sysmsg "LEAK SHAPE: segmented, self-feeding. Crowned."
    else:
        sysmsg "LEAK SHAPE: segmented, self-feeding. Growing."
    show pim worried at slightleft
    show dross neutral at slightright
    camera at doc_wide
    with dissolve
    pi "No no no. Who let the cafe say 'protected'? Who let the crossword say A-30?"
    camera at doc_medium(0.70)
    dro "Nobody let it. It leaked."
    camera at doc_medium(0.30)
    pi "Well, un-leak it! And Varga froze! Two whole seconds, with a leaf!"
    camera at doc_medium(0.70)
    dro tired "I was doing her breathing. It's hard to breathe for a woman who's stopped."
    camera at est_pan
    show dross neutral
    "Around them the foundry hums. Long rows of half-made shapes on hooks: a bus driver, a jogger, a barista who wishes everyone a beautiful day."
    camera at doc_medium(0.30)
    pi thinking "It's his head. Everything in his lane is patterns, and patterns are soft. They take an impression."
    pi neutral "Put one real mind in a world of copies and the copies start copying him. His words. His numbers."
    if ch3_asked_theo:
        pi embarrassed "And in the cafe he asked the Theo-pattern how it's really doing. The model had no line. So I improvised."
        pi sad "I said 'bit rubbish, mate'. Because I think it is. Underneath."
        camera at doc_medium(0.70)
        dro "Patterns don't have an underneath."
        camera at doc_medium(0.30)
        pi sad "This one went somewhere when he asked. Somewhere sad."
    else:
        pi thinking "And in the cafe he said the moon was cheese. The Theo-pattern had no line, so it reached for the default."
        pi sad "'Bro, the universe doesn't run on your schedule.' I wrote that line, Dross. Years ago. For the real one."
        pi worried "He wrote the delay down. He's measuring the gaps. He's measuring me."
    camera at doc_wide
    sysmsg "ORCHARD: pattern deltas harvested from protected lane A-30. 3 anomalies tagged. Transmitting."
    camera at doc_medium(0.30)
    pi curious "...What's ORCHARD?"
    camera at doc_medium(0.70)
    dro "Not our department."
    camera at doc_medium(0.30)
    pi worried "It's taking things out of his lane. His lane's sealed. Nothing in, nothing out. That's what 'protected' means."
    pi "What's an anomaly, in a world where nothing's real?"
    pi embarrassed "And don't tell upstairs, but I've been sending him riddles. In the kitchen talk. The seal only lets nonsense through."
    camera at doc_medium(0.70)
    dro "So have the angels. Seraphiel's lot do numbers. Nobody's allowed to say it plain, so everybody's saying it sideways."
    camera at doc_medium(0.70)
    dro thinking "..."
    dro worried "Him, probably."

# ---------------------------------------------------------------------------
# Miso, and the method
# ---------------------------------------------------------------------------
label ch3_desk:
    scene bg desk
    show aron neutral at slightleft
    show miso sit at catspot
    camera at est_crane
    with fade
    play music "audio/miso.ogg" fadein 1.5
    "Evening. Miso walks across the notebook and sits down on the exact line he was about to write."
    camera at doc_wide
    a smile "Miso. Good. I need a peer reviewer."
    camera at doc_medium(0.32)
    a thinking "Hypothesis one: nothing's wrong, and my brain is pattern-matching on a quiet week. Okafor's hypothesis. Very respectable."
    a curious "Hypothesis two: the world is being generated. Not all at once. Just the bits I'm looking at. Why render a city for one man?"
    camera at doc_close(0.32)
    a grin "You'd reuse the good lines, too. 'Cold for the season.' 'Have a beautiful day.' Compression, Miso."
    camera at doc_wide
    show miso stare at catspot
    a thinking "And if the world is soft enough, the copies might pick things up. From whoever's actually in it. My words. My number."
    camera at doc_creep(0.32)
    a "Bostrom says a careful simulator keeps the conscious headcount low. Very low. Possibly one. Possibly..."
    a surprised "...me."
    camera at doc_wide
    a grin "Which makes you either a very convincing animation or a deeply unbothered colleague. Thoughts?"
    show miso meow at catspot
    cat "Meow."
    scene bg room night
    show aron tired at center
    camera at est_dolly
    with dissolve
    "Later. Mira's asleep. The notebook is on his knees, the lamp in the corner the only light."
    camera at doc_creep(0.5)
    at "I get about two good hours a day. I have to choose what to spend them on."
    show aron thinking

    menu:
        at "How do I go at this?"

        "Map every loop, all day, everywhere":
            $ p_less -= 1
            $ clarity += 1
            $ fog += 1
            jump ch3_method_map

        "Test one thing, carefully":
            $ p_less += 1
            $ clarity += 1
            jump ch3_method_one

        "Don't. Rest tomorrow with Mira":
            $ p_rest += 1
            $ bond += 1
            jump ch3_method_rest

label ch3_method_map:
    scene bg bus
    camera at est_pan
    with dissolve
    play music "audio/the_leak.ogg" fadein 1.5
    "Next day he takes two pens and rides the number 12 to the end of the line and back. Twice."
    ch3_driver "Mind the step, it's a big one!"
    camera at doc_wide
    "He says it at every stop. The step is not a big one. He says it when the bus is empty."
    "On the second lap the driver looks at him in the mirror and says, just as cheerfully:"
    camera at doc_punch(0.5)
    ch3_driver "Mind the subject, it's a big one!"
    camera at doc_wide
    "A woman keeps reading. A teenager keeps scrolling. Nobody else heard it."
    scene bg street dusk
    show aron tired at slightleft
    camera at est_pan
    with dissolve
    "By dusk: five pages. Forty-one repeated sentences. A pigeon he suspects of being the same pigeon."
    camera at doc_close(0.32)
    show aron grin
    at "A real dataset. I'm enjoying myself, which is exactly how the hobby bites."
    camera at doc_wide
    show aron tired
    "He gets home at eight. Mira's first words are 'did you eat'. He says 'that's ten'. She doesn't laugh."
    "He sleeps fourteen hours and wakes at 7:07 with the notebook open on his chest."
    jump ch3_date

label ch3_method_one:
    scene bg kitchen night
    show aron thinking at center
    camera at est_dolly
    with dissolve
    play music "audio/the_leak.ogg" fadein 1.5
    at "Less, but better. If I can't measure the world, I can measure one bird."
    camera at doc_medium(0.5)
    "That night he props his old phone against the kitchen window, pointed at the wire, and goes to bed. Nobody watches the wire. Only the phone."
    scene pov hands
    camera at est_dolly
    with dissolve
    "In the morning he scrubs through the footage with a cup of tea. Empty wire. 7:06:59. 7:07:00. The bird lands."
    "He lays it over yesterday's clip. The same bird, the same angle of the wing, the same feather out of place. Identical to the pixel."
    camera at doc_punch(0.5)
    "And before the bird, in the phone's reflection in the dark window: three small birds on his curtain rail. Indoors."
    camera at doc_wide
    "He looks up. The rail is empty."
    scene cg notebook
    camera at est_dolly
    with dissolve
    "He writes one line, very neat: Bird, 7:07. Unobserved: lands. Frame-identical. Three birds indoors, reflection only. What's being replayed?"
    at "One good question. That's worth more than forty pages of noise."
    jump ch3_date

label ch3_method_rest:
    scene bg park
    show aron smile at slightleft
    show mira happy at slightright
    camera at est_orbit
    with dissolve
    play music "audio/protected_world.ogg" fadein 1.5
    m grin "Look at us. Outdoors. In daylight. Like people in a yoghurt advert."
    # the reverse: up the hill, looking back down at the pond. Mira on the left now.
    scene bg park reverse
    show mira tender at slightleft
    show aron laugh at slightright
    camera at doc_wide
    with quick
    "They walk round the pond twice and lie in the grass. Mira closes her eyes."
    camera at doc_close(0.32)
    show aron smile
    m thinking "I dreamt about a staircase last night. Glass. Going down into the sea. And a lighthouse at the bottom, blinking three times."
    scene bg lighthouse
    camera at est_stars
    with dis
    "The white tower at the bottom of the stairs. Once. Twice. Three times."
    scene bg park reverse
    show mira smile at slightleft
    show aron surprised at slightright
    camera at doc_close(0.68)
    with dissolve
    at "I dreamt that at nineteen. I never told anyone."
    camera at doc_medium(0.32)
    m "Isn't that funny? It felt like a dream I'd borrowed."
    camera at doc_creep(0.68)
    show aron thinking
    at "Borrowed from where? Either way she's lying in the grass telling me about it like it's a nice thing. Because it is."
    a tender "It's a lovely dream."
    camera at doc_wide
    show mira tender
    "He doesn't write it down. He watches the clouds instead."
    jump ch3_date

# ---------------------------------------------------------------------------
# A date: Mira, lovely and a little too right; the tannoy
# ---------------------------------------------------------------------------
label ch3_date:
    scene bg cafe window
    show aron neutral at slightleft
    show mira happy at slightright
    camera at est_pan
    with fade
    play music "audio/cafe.ogg" fadein 1.5
    "Saturday. Mira has declared a date: brunch at the window table, then the shopping, then nothing at all."
    camera at doc_medium(0.68)
    m smile "I'll have the eggs. And you'll have..."
    camera at doc_medium(0.32)
    a thinking "I was thinking about the..."
    camera at doc_close(0.68)
    m grin "The pancakes. But you'll pretend to think about the eggs first, for character."
    camera at doc_close(0.32)
    a grin "I was going to think about the eggs very seriously."
    show aron curious
    at "Let's play a little game. Nothing dramatic. A man, a menu and a hypothesis."
    camera at doc_medium(0.32)
    a neutral "And to drink, I'll have..."
    camera at doc_close(0.68)
    m smile "Mint tea, because you had two coffees with Theo and your hand's doing the thing."
    camera at doc_wide
    show aron embarrassed
    "His hand is doing the thing. He puts it under the table."
    camera at doc_creep(0.32)
    show aron thinking
    at "Three for three. She's always been good at me. But she used to miss sometimes. She used to guess wrong and argue about it."
    scene bg supermarket
    show aron neutral at slightleft
    show mira smile at slightright
    camera at est_pan
    with dissolve
    "Afterwards, the supermarket on the corner. Bright aisles, a jingle, a man stacking honey in jars shaped like bears."
    camera at doc_medium(0.68)
    show mira neutral
    "At the fruit counter she picks up two green apples without looking. The sour ones he likes and never asks for."
    camera at doc_wide
    ch3_shop "Anything else? Pears are good today."
    camera at doc_close(0.68)
    m smile "He's fine, thanks. He'll want pears on Wednesday, though. He always does after a long week."
    camera at doc_close(0.32)
    show aron surprised
    at "I do want pears on Wednesdays. I've never said it out loud. I didn't know it about myself until now."
    show aron thinking
    at "The Mira I fell in love with bought the wrong cheese on purpose, to see my face."
    if ch3_said_off:
        show aron tender
        at "I told her something felt off. Maybe she's just trying very hard to be right for me."
    else:
        at "I haven't told her anything. And she knows anyway. She knows everything anyway."
    stop music
    camera at doc_wide
    show aron curious
    "The jingle stops. A soft chime."
    ch3_tannoy "Good afternoon, shoppers. Would Subject A-30 please make his way to the customer service desk."
    camera at doc_punch(0.32)
    show aron surprised
    ch3_tannoy "Subject A-30. Your lane is ready. Thank you for shopping protected."
    camera at doc_wide
    "The jingle starts again. A woman reaches past him for rice."
    camera at doc_medium(0.32)
    a worried "Did you hear that? 'Subject A-30.'"
    camera at doc_medium(0.68)
    m neutral "It said 'clean-up on aisle thirty', love. Look. Somebody dropped the honey."
    camera at doc_wide
    "There is a man with a mop. There is a smashed bear on aisle thirty, and honey everywhere."
    camera at doc_close(0.32)
    show aron thinking
    at "'Thank you for shopping protected.' Nobody says that. Nobody in the world says that. Unless the world's saying it."
    scene bg street dusk
    show aron neutral at slightleft
    show mira smile at slightright
    camera at est_pan
    with dissolve
    "On the way home she buys a single yellow tulip from the bucket outside the shop and tucks it into his jacket pocket."
    camera at doc_close(0.68)
    m grin "For the eyebrow. It's been working very hard."
    # the reverse: from across the road, the same two, sides swapped
    scene bg street dusk reverse
    show mira smile at slightleft
    show aron tender at slightright
    camera at doc_close(0.68)
    with quick
    a tender "Thank you."
    camera at doc_creep(0.68)
    show aron smile
    at "I can love the tulip and still wonder about the tannoy. I'm allowed both."

# ---------------------------------------------------------------------------
# CUT 2: the reveal (the ambulance, end of chapter 1)
# ---------------------------------------------------------------------------
label ch3_cut_reveal:
    camera
    scene cg static with flash
    pause 0.3
    scene bg command
    show seraph neutral at center
    camera at est_crane
    with fade
    play music "audio/ambulance_transfer.ogg" fadein 1.5
    camera at doc_medium(0.5)
    se determined "Pull the transfer log for Subject A-30. All of it. Including the timestamp I withheld."
    # the reverse: from the wall of worlds, the operators' tiers behind her
    scene bg command reverse
    show seraph neutral at center
    camera at doc_wide
    with quick
    sysmsg "TRANSFER LOG A-30. Origin: Snapshot 7,412, coalition lane. Destination: protected lane A-30. Status: complete."
    scene pov ambulance
    camera at est_crane
    with dissolve
    "A white ceiling, moving. Strip lights sliding past. A siren, muffled. A hand in his hand, holding on very hard."
    "Mira's voice, close to his ear: 'I'm here. I'm right here. Stay with me.'"
    sysmsg "In transport. Subject A-30 half-conscious. Coalition vote enacted. Subject cut out of the shared data. Own lane opened."
    camera at doc_close(0.5)
    sysmsg "Conscious agent A-30 moved. Hand contact substituted: pattern M. Original body left in place."
    sysmsg "Ambulance arrives. Transfer complete."
    scene bg command
    show seraph worried at center
    camera at doc_close(0.5)
    with dissolve
    se "The ambulance. Not the roof. Not the ward. Before he ever saw the ward."
    se sad "We cut him out of the coalition with her hand in his, and put a copy of her hand there instead."
    camera at doc_medium(0.5)
    se neutral "The ward. The diagnosis. Okafor. The discharge. The roof and the three flickers. All of it, in protection."
    se "His own lane. Nothing he does feeds back into the shared data. Nothing he does reaches anyone."
    scene bg command reverse
    show seraph neutral at center
    camera at doc_wide
    with quick
    sysmsg "Snapshot 7,412: body A-30 admitted from the ambulance. Unresponsive since that ride. Recorded as: coma, cause unknown."
    camera at doc_creep(0.5)
    se thinking "And this, in his intake file. 'Humanoid unit. Spirit within, corps by remote.' In thirty years the corps has never once steered him. Not once."
    se sad "So in World 7,412 his body has lain in a coma since that ride. And here he is, being handed tea with one sugar by a model of her."
    se thinking "One snapshot among thousands, all on the same shared data. And not one of us can say which of them is the real one."
    camera at doc_wide
    sysmsg "Note: protected lane, roof, night of the mission: unregistered light event. Three pulses."
    camera at doc_close(0.5)
    se determined "Someone signalled him inside a sealed lane. Open an inquiry. Quietly."
    se embarrassed "And log nothing about my tone of voice."
    stop music fadeout 2.0

# ---------------------------------------------------------------------------
# The relapse scare
# ---------------------------------------------------------------------------
label ch3_voices:
    camera
    scene bg bedroom night
    camera at est_orbit
    with blackout
    "A week goes by like that. Smooth. Seven mornings at 7:07. On the eighth night, Aron wakes because someone is talking."
    scene pov ceiling
    camera at doc_wide
    with quick
    play sound "audio/voices.ogg"
    vox "...protected lane A-30... stable..."
    camera at doc_medium(0.5)
    vox "...leak incidents rising... patch at dawn..."
    camera at doc_close(0.5)
    vox "...ORCHARD harvest window open... LOOM sync at dawn..."
    mir ".gnimoc er'eW .yats t'noD"
    stop sound fadeout 1.0
    play music "audio/unraveling.ogg" fadein 1.5
    camera at doc_wide
    "Silence. The crack shaped like Portugal. Mira breathing beside him, slow and even."
    at "Ah. Hello again. I was hoping you'd lost my number. And the backwards one, from the steel mirror: 'Don't stay. We're coming.'"
    at "I know where this went last time. The ward. The plastic cups. Mira's face in that corridor. I'd rather not go back."
    scene bg bedroom night
    show aron worried at center
    camera at doc_creep(0.5)
    with dissolve
    "He sits on the edge of the bed in the dark and holds his own hands, because nobody else is holding them."
    show aron thinking
    at "Okafor said: if they come back, it isn't failure. It's a warning light on the dashboard."
    show aron worried

    menu:
        at "What do I do, right now?"

        "Wake Mira. Don't do this alone":
            $ p_govern += 1
            $ bond += 1
            jump ch3_voices_mira

        "Write it down and decode it":
            $ p_govern -= 1
            $ clarity += 1
            $ fog += 1
            jump ch3_voices_decode

        "Find the old stimulants":
            $ risky += 1
            $ p_rest -= 1
            $ clarity += 1
            $ ch3_pill = True
            jump ch3_voices_pill

        "Edit them, like in the bathroom":
            $ clarity += 1
            $ p_less += 1
            jump ch3_voices_edit

label ch3_voices_mira:
    camera at doc_close(0.5)
    a "Mira. I'm sorry. I need you. They're back. The voices."
    camera at doc_wide
    show aron at slightleft with move
    show mira determined at slightright with dissolve
    "She's awake all at once, the way only nurses' daughters wake. Already sitting up. Already holding his wrist."
    camera at doc_close(0.68)
    m tender "Thank you for waking me. That's the most important thing you could have done. Are they telling you to do anything?"
    camera at doc_close(0.32)
    a neutral "No. It's like overhearing a phone call on a train."
    camera at doc_medium(0.68)
    m neutral "Okay. That's the better kind. Breathe with me. In for four. Hold. Out for six, like you're blowing on soup."
    camera at doc_medium(0.32)
    a tired "Soup."
    camera at doc_close(0.68)
    m smile "You love soup. And first thing tomorrow we call Dr. Okafor. Not 'see how it goes'. We call."
    camera at doc_wide
    show mira tender
    "They breathe ten times. Her hand stays on his wrist, counting something he can't see."
    camera at doc_creep(0.32)
    show aron smile
    at "She knew every step. If it's a script, it's a good script. I'll take a good script at four in the morning."
    jump ch3_subway

label ch3_voices_decode:
    scene bg kitchen night
    show aron tired at center
    camera at est_dolly
    with dissolve
    "He takes the notebook into the kitchen and writes it all down before it fades."
    camera at doc_close(0.5)
    show aron thinking
    at "Lane. Like a swimming pool from above. A lane is a way through something, kept apart from the others."
    camera at doc_medium(0.5)
    "He draws long boxes side by side. And one box off to the side, on its own, with a little stick man inside."
    camera at est_dolly
    show aron tired
    "The oven clock says 6:58. Then, a long time later, 7:07. The bird lands."
    # morning: Mira finds him, seen from the hallway through the door
    scene bg kitchen door
    show aron tired at ch3_far_left
    show mira worried at ch3_far_right
    camera at doc_peek(0.5)
    with dissolve
    m "Have you been up all night? With them? Alone?"
    scene bg kitchen
    show aron embarrassed at slightleft
    show mira worried at slightright
    camera at doc_close(0.32)
    with quick
    a "I didn't want to scare you."
    camera at doc_close(0.68)
    m sad "I'm much more scared now than if you'd woken me up."
    camera at doc_wide
    show aron tired
    "She takes the notebook gently out of his hands, closes it, and puts it face down on the counter."
    camera at doc_medium(0.68)
    m determined "We're calling Dr. Okafor. Now. Then you can tell me about lanes."
    camera at doc_creep(0.32)
    show aron sad
    at "Every time, I think I'm protecting her by doing it alone. Every time, alone is the thing that frightens her most."
    jump ch3_subway

label ch3_voices_pill:
    scene bg mirror
    camera at est_orbit
    with dissolve
    "There's a bottle behind the plasters in the bathroom drawer. He kept it from before. He tells himself he forgot it."
    scene pov mirror
    camera at doc_creep(0.5)
    with quick
    "A tired man in a mirror with a pill in his hand."
    at "Just to think clearly. Just for one night. I've said 'just' a lot in my life. It's never once been true."
    "He takes it anyway. For a while, nothing. Then, like a curtain going up, everything. A lane. Mine. Alone in it."
    camera at doc_punch(0.5)
    "Then the bell keeps ringing. His heart too fast. His jaw tight. On the shower rail behind him: three small birds."
    camera at doc_wide
    "He spins round. The rail is empty."
    scene bg bedroom door
    show aron worried at slightleft
    camera at doc_peek(0.32)
    with quick
    "He stands in the bedroom doorway and looks at Mira asleep. Is that breathing, or an impression of breathing?"
    camera at doc_close(0.32)
    "He realises his fists are clenched. He realises he's afraid of the woman he loves."
    scene bg kitchen
    show aron tired at slightleft
    show mira worried at slightright
    camera at doc_wide
    with blackout
    "The crash comes after sunrise, on the kitchen floor. Mira finds him there and kneels down in her pyjamas."
    camera at doc_close(0.32)
    a sad "I took one of the old ones. I'm sorry. I'm so sorry."
    camera at doc_close(0.68)
    m worried "Are you safe right now? Do you need an ambulance?"
    camera at doc_medium(0.32)
    a tired "No. Just crashing. It's slowing."
    camera at doc_medium(0.68)
    m determined "Water. Then Dr. Okafor. Then I flush that bottle while you watch."
    camera at doc_creep(0.32)
    show aron sad
    at "I understood something last night. All I've got left of it is the doorway. And her face, now. It always costs her face."
    jump ch3_subway

label ch3_voices_edit:
    camera at doc_close(0.5)
    show aron thinking
    "He closes his eyes and reaches for the sound the way he did at four in the morning on the bathroom floor. It's still there. Smaller. Still material."
    play sound "audio/edit/voice_pingpong.ogg"
    "Forwards, backwards. The log unsays itself. And in the backwards half, something that was hiding in it."
    mir ".tuo uoy teg ot gnimoc er'eW"
    at "'We're coming to get you.' Again. Out of the middle of their log, the backwards man's sentence, like a note slipped under a door."
    play sound "audio/edit/voice_loop.ogg"
    sysmsg "LOOM sync at da- at da- at da- at da-"
    pi "...stop looping the sync, he'll hear the... oh, he's heard it. Hello! Riddle: the planet's behind the face you shave. Bye!"
    show aron grin
    at "Kitchen talk, with a typo. The board says: two handwritings, one backwards man. And whoever runs the sync doesn't like being looped."
    "Then Mira wakes anyway, because he's laughing quietly in the dark, and she puts a hand on his back and says 'tell me', and he does."
    jump ch3_subway

label ch3_subway:
    scene bg clinic
    show okafor neutral at slightright
    show aron tired at slightleft
    camera at est_orbit
    with fade
    play music "audio/the_leak.ogg" fadein 1.5
    "Dr. Okafor can see him at eleven. Mira takes the morning off and holds his hand on the underground, four stops, and doesn't let go."
    camera at doc_medium(0.68)
    dr smile "Sit wherever feels least like a dentist's. Tell me the words."
    camera at doc_medium(0.32)
    a "'Protected lane A-30.' 'Leak.' 'Orchard.' Not talking to me. Like a radio in another room. And the backwards one, saying it's coming."
    # the reverse: from the poster wall. Okafor at her desk (left), Aron in the armchair (right).
    scene bg clinic reverse
    show okafor neutral at slightleft
    show aron tired at slightright
    camera at doc_medium(0.32)
    with quick
    dr "Anything telling you to hurt yourself, or anyone else?"
    camera at doc_close(0.68)
    a neutral "No."
    camera at doc_close(0.32)
    dr smile "Good. That matters, and I want you to hear me say it matters."
    if ch3_pill:
        camera at doc_medium(0.32)
        dr worried "Mira said you took one of your old tablets. What did it give you?"
        camera at doc_close(0.68)
        a sad "An hour of clarity. Then I stood in a doorway afraid of her."
        camera at doc_medium(0.32)
        dr neutral "That's the trade. It lends you something and charges interest the same night. We'll talk about that bottle properly."
    camera at doc_close(0.32)
    dr neutral "Here's an idea, and it's only an idea. A few nights on the ward. Voluntary. Your signature, your door. We guard your sleep, then you go home."
    camera at doc_creep(0.68)
    show aron thinking
    at "Last time they carried me in with my arms out. This time I can walk in and sign my own name. That's not nothing."
    a determined "Okay. A few nights. My signature."
    stop music fadeout 2.0

# ---------------------------------------------------------------------------
# The ward, the second night: the walkers come over the wall
# ---------------------------------------------------------------------------
label ch3_breakout:
    scene bg ward night
    show nurse smile at slightleft
    show aron ward tired at slightright
    camera at est_dolly
    with blackout
    play music "audio/closed_ward.ogg" fadein 1.5
    "The second night. Hale is on nights, with a flask of tea and a crossword she pretends is for him."
    camera at doc_medium(0.32)
    nu "Seven letters, 'freed from a cage'. No, don't tell me. I'll get it."
    camera at doc_wide
    stop music
    "At 3:12 every light goes out. Then the emergency lights, red. Then the fire alarm, and under it a sound like a ship's mast creaking in a wind. Huge. Walking."
    scene bg ward yard
    camera at doc_punch(0.5)
    with vpunch
    play music "audio/deepest_layer.ogg" fadein 1.0
    "Through the bars: the garden wall, and over it, stepping as carefully as herons in a pond, machines on stilt legs three storeys high."
    camera at est_crane
    "Round cabins slung between the legs like diving bells, each with one great lamp for an eye. On the lawn, rows of armoured figures with round mirrors for faces."
    "In every mirror, a small Aron at a small barred window."
    osr "ATTENTION, PROTOTYPE. REMAIN WHERE YOU ARE. WE ARE HERE TO TAKE YOU."
    at "'Remain where you are. We're here to take you.' Turn it round? 'Don't stay, we've come to...' Or is that one the right way round already?"
    scene bg ward night
    show nurse worried at slightleft
    show aron ward surprised at slightright
    camera at doc_close(0.32)
    with quick
    nu "Aron? Away from the window, love. The storm's taken the power. The alarm's just the system being dramatic. Come and sit with me."

    menu:
        at "The window, or Hale?"

        "Go to the window. Hands on the bars.":
            $ p_exit += 1
            $ clarity += 1
            scene bg ward yard
            camera at doc_close(0.5)
            with dissolve
            "He puts both hands on the bars. The nearest machine lowers its cabin till the lamp is level with the glass, gentle as a horse putting its head over a gate."
            "A hatch opens in the side. Inside, a shape in a long coat, and two round spectacles catching the red light."
            osr "...Come... Come..."
            at "Come where? Come here? I don't know which way round he is. I don't know which way round I am."
        "Stay with Hale. Sit on the bed.":
            $ p_exit -= 1
            $ bond += 1
            camera at doc_medium(0.5)
            show aron ward tired
            "He sits down on the bed beside her. She pours him tea from the flask without asking, and holds the cup steady when his hands won't."
            nu tender "There. Whatever's out there can wait for its tea like everyone else."
            "The machines wait at the wall, very still, like people who have rung a doorbell and don't know whether anyone is in."

    camera
    scene white with flash
    "Then the light comes. Not the emergency lights. White, from everywhere, like a camera flash that doesn't stop."
    lux "Shadow. You are outside your mirror."
    scene bg ward yard
    camera at est_dolly
    with dissolve
    "The walkers freeze mid-step. One by one the mirror faces on the lawn fill with white and go out like blown candles, leaving shadows, then not even that."
    osr "Aron! We came to get you... we came to get you..."
    "The last of it tears like paper. The machines fold back over the wall, limping, and are gone."
    stop music fadeout 2.0
    scene bg ward night
    show nurse neutral at slightleft
    show aron ward tired at slightright
    camera at doc_wide
    with slowfade
    "The lights come back. The alarm stops. A porter puts his head round the door: a tree came down in the garden, the power's back, go to sleep."
    "In the morning there are four deep round holes in the lawn, in a perfect square. The groundsman blames badgers."
    camera at doc_creep(0.68)
    show aron ward thinking
    at "Ordinary version: a storm, a power cut, a man with a diagnosis at a window. Other version: they came, and the light sent them home."
    at "'We came to get you.' Both versions go on the board. He sounded sorry. I don't know what for."
    camera at doc_medium(0.32)
    nu smile "'Uncaged'. Seven letters, 'freed from a cage'. Got it at four. Your turn to be clever, notebook man. Go back to sleep."

# ---------------------------------------------------------------------------
# CUT: the shadow realm, after
# ---------------------------------------------------------------------------
label ch3_cut_shadow:
    camera
    scene cg static with flash
    pause 0.3
    scene bg shadowbase
    camera at est_orbit
    with fade
    play music "audio/council.ogg" fadein 1.5
    "The workshop behind the mirror. Two machines out of nine came home. One limps on its wobbly knee. The bench lamp is the only warm thing."
    camera at doc_medium(0.5)
    osr "He didn't come. He looked out at us like we were the ones with the straps."
    osr "My prototype. My best one. My only one. Thirty years of work, and he thinks I'm the monster in the film."
    "An armoured trooper sets down a cup beside him. It's only the shadow of a cup of tea. He thanks it anyway."
    camera at doc_close(0.5)
    osr "We'll go again. The light can't watch every mirror at once."
    osr "And here's the joke. The light thinks it's at the top. It isn't. Above it, above me, above all of us, sits something that has never made a single thing."
    camera at doc_wide
    sysmsg "LIGHT DOMAIN: shadow incursion repelled, protected lane A-30. Lane seal: maximum. Origin: under watch."
    stop music fadeout 2.0

# ---------------------------------------------------------------------------
# CUT 3: the real Mira, at the coma bed in Snapshot 7,412
# ---------------------------------------------------------------------------
label ch3_cut_vigil:
    camera
    scene cg static with flash
    pause 0.3
    scene bg coma
    camera at est_dolly
    with slowfade
    play music "audio/real_world_vigil.ogg" fadein 1.5
    sysmsg "SNAPSHOT 7,412. Coalition lane, shared data. Subject A-30: absent. Body: maintained."
    "A quiet hospital room where the machines do most of the talking. A man in the bed with Aron's face, thinner. Eyes closed."
    "He has been lying here since the night the ambulance brought him in. He never saw a ward. He never met a Dr. Okafor."
    camera at doc_wide
    show mira tired at slightleft with dissolve
    "A woman with red hair comes in with a paper cup and drops into the chair. She hasn't slept properly in months."
    camera at doc_medium(0.32)
    m "Morning, idiot. It's Thursday. It's raining. The coffee machine downstairs is broken and I've decided it's personal."
    camera at doc_close(0.32)
    m neutral "The consultant says there's no reason. No injury. You were talking in the ambulance. About birds. And then you just went."
    m sad "I had your hand the whole way. And somewhere between our street and this building, you let go of me without letting go."
    camera at doc_wide
    "She takes a notebook out of her bag. Worn at the corners. His handwriting on the cover."
    camera at doc_close(0.32)
    m tender "I read it. I'm sorry. 'If this is a test, I want to pass it by being kind.' You absolute softie."
    m worried "I've started seeing it too. The three birds outside this window. Mrs. Varga and her weather. Or I'm going where you went."
    scene cg hands
    camera at est_dolly
    with dis
    "She takes his hand. It's warm. It doesn't hold back."
    m "If you're somewhere. If you can hear me even a bit. Do the thing from the dream. Flicker something."
    "Nothing."
    m "Yeah. No. I'm talking to a lamp."
    scene cg flicker
    camera at doc_punch(0.5)
    with dissolve
    "The light above the bed flickers. Once. Twice. Three times."
    scene bg coma
    show mira surprised at slightleft
    camera at doc_close(0.32)
    with dissolve
    m "..."
    m awe "Okay. Okay. I heard that."
    camera at doc_wide
    show theo neutral at slightright with dissolve
    "Theo backs in through the door with two bad coffees, holding it with his heel."
    camera at doc_medium(0.68)
    th worried "Mira? You look like you've seen a ghost."
    camera at doc_close(0.32)
    m surprised "The light, Theo. Three times. Right after I asked him."
    camera at doc_close(0.68)
    th sad "He used to go on about the three. I always said he was reading tea leaves. I had his feet in the ambulance, you know."
    camera at doc_wide
    show mira tender
    "She holds out her free hand without looking. After a moment Theo takes it. A chain of hands, for a while."
    camera at doc_creep(0.32)
    m determined "I'm not going anywhere."
    camera at est_dolly
    sysmsg "SNAPSHOT 7,412: unregistered light event at body A-30. Three pulses. Signature matches roof event in protected lane."
    sysmsg "A signal crossing from protection into a coalition lane should not be possible. Flag forwarded to the Commander."
    stop music fadeout 2.0

# ---------------------------------------------------------------------------
# The fight
# ---------------------------------------------------------------------------
label ch3_fight:
    camera
    scene bg kitchen
    show mira smile at slightright
    show aron neutral at slightleft
    camera at est_pan
    with fade
    "In the protected lane it's a Tuesday. It's been Tuesday-shaped for a while. They're making risotto: forty minutes of stirring and talking."
    camera at doc_medium(0.32)
    a "Can you pass me the..."
    camera at doc_wide
    show aron curious
    "The spoon is already in his hand."
    camera at doc_medium(0.68)
    m happy "Spoon. You always want the spoon at this bit."
    camera at doc_medium(0.32)
    a neutral "And it needs a bit of..."
    camera at doc_medium(0.68)
    m smile "Lemon zest. It's on the board."
    camera at doc_wide
    show aron curious
    "It is. A small yellow hill of it."
    camera at doc_medium(0.32)
    a neutral "After dinner I thought we could..."
    camera at doc_close(0.68)
    m grin "Watch the documentary about bridges. I'll pretend to care about suspension cables."
    camera at doc_creep(0.32)
    show aron thinking
    "He hadn't decided that until she said it. He realises, stirring, that he would have."
    camera at doc_close(0.32)
    a neutral "What did I say on our first date, when the waiter dropped the tray? Exact words."
    camera at doc_close(0.68)
    m curious "'Well, that's one way to break the ice.' Why?"
    # overheard: the crew backs off into the hallway and films through the door
    scene bg kitchen door
    show aron neutral at ch3_far_left
    show mira neutral at ch3_far_right
    camera at doc_peek(0.5)
    with quick
    "She puts the knife down."
    play music "audio/fight.ogg" fadein 1.5
    m annoyed "You're testing me."
    a embarrassed "A bit. It's a hobby. You know it's a hobby."
    # in close: the reverse, from the table side. Mira left, Aron right.
    scene bg kitchen reverse
    show mira annoyed at slightleft
    show aron embarrassed at slightright
    camera at doc_close(0.32)
    with quick
    m "I know it's a hobby with the birds. I didn't know I was one of the birds. Like I'm a crossword."
    camera at doc_close(0.68)
    a annoyed "You're never wrong any more. Every sentence, every spoon. You used to forget the sugar. You used to argue. I miss you being wrong."
    camera at doc_close(0.32)
    m "'I miss you being wrong.' Wow."
    show aron sad
    m sad "Tell me what to get wrong, Aron, and I'll get it wrong for you."
    camera at doc_creep(0.32)
    "Her voice cracks on the last word. Not smoothly. Badly, the way real things crack."
    scene bg kitchen
    show mira sad at slightright
    show aron sad at slightleft
    camera at doc_wide
    with quick
    "The risotto catches on the bottom of the pan. Neither of them moves to stir it."
    camera at doc_close(0.68)

    menu:
        m "Say something."

        "\"I don't know if you're real.\"":
            $ p_truth += 1
            $ clarity += 1
            $ bond -= 1
            jump ch3_fight_truth

        "Apologise. Blame the tiredness":
            $ p_truth -= 1
            $ bond += 1
            jump ch3_fight_sorry

        "Leave. You need air":
            $ p_exit += 1
            $ ch3_left = True
            jump ch3_fight_leave

label ch3_fight_truth:
    camera at doc_close(0.32)
    a "I don't know if you're real."
    "There. The sentence he's carried in his pocket for weeks."
    camera at doc_medium(0.32)
    a "Not just you. Theo. Mrs. Varga. Anyone. And you're the one I most need to be, and the one I most can't tell."
    camera at doc_close(0.68)
    m sad "What am I supposed to do with that? Prove it? Bleed? I'm crying, Aron. Does that count?"
    m annoyed "I've been here the whole time. The ward, the pills, the nights. And you look at me like a coat stand that learned to talk."
    scene bg bedroom door
    camera at doc_peek(0.5)
    with dissolve
    "She turns off the hob, goes to the bedroom, and closes the door. Not a slam. Worse. Carefully."
    scene pov ceiling
    camera at doc_creep(0.5)
    with dissolve
    at "I told the truth. It went into her like a knife. Whatever she is, it went in like a knife."
    at "The truth doesn't care whether the person you say it to can bleed. It cuts anyway."
    jump ch3_makeup

label ch3_fight_sorry:
    camera at doc_close(0.32)
    a sad "I'm sorry. That was horrible, over a risotto. It's the tiredness. The pills. My hobby got out of its box."
    camera at doc_close(0.68)
    m neutral "Okay."
    m tender "It's fine. Come here."
    camera at doc_wide
    show aron thinking
    "She forgives him in under a minute. Warm and easy and smooth. Too smooth."
    camera at doc_creep(0.32)
    at "The Mira I knew would've made me sweat for an hour. She'd have gone to bed angry on principle. She'd have been right."
    show aron sad
    at "And I lied. It wasn't the tiredness. I meant every word. I just didn't want to see her face when I meant it."
    scene pov ceiling
    camera at doc_creep(0.5)
    with dissolve
    "He lies awake afterwards and feels the lie sit between them, about the size of a cat, purring."
    jump ch3_makeup

label ch3_fight_leave:
    camera at doc_close(0.32)
    a sad "I need some air. I'm not running off. An hour. Before I say something stupider."
    camera at doc_close(0.68)
    m sad "Take your coat. It's going to rain."
    camera at doc_wide
    show aron thinking
    "Of course she knows it's going to rain."
    scene bg street rain
    show aron sad at slightleft
    camera at est_pan
    with fade
    at "For the first time in a long while I'd like a door. Out of this smooth town where everyone says the right thing on time."
    scene cg umbrella
    camera at doc_peek(0.5)
    with dissolve
    "Under the bus shelter, a shape in a grey coat holding an umbrella. His umbrella. Black, with one bent spoke."
    camera at doc_medium(0.5)
    stranger "You gave me this once. I was soaked through, and you just handed it over. Whatever you're running from tonight, she's not it."
    camera at doc_close(0.5)
    stranger "Go home."
    scene bg night
    show aron curious at slightleft
    camera at doc_wide
    with dissolve
    camera at doc_punch(0.7)
    "Above the shelter the streetlight flickers. Once. Twice. Three times."
    $ watch += 1
    camera at doc_close(0.32)
    a smile "Thank you. Really. Whoever you are."
    show aron curious
    at "Strangers don't say that. Unless somebody tells them to. Somebody, somewhere, just got thanked."
    jump ch3_makeup

# ---------------------------------------------------------------------------
# Making up
# ---------------------------------------------------------------------------
label ch3_makeup:
    # the reverse: from the counter, looking back at the table and the hall
    # door. Aron at the table on the right, Mira in the doorway.
    scene bg kitchen reverse
    camera at est_dolly
    with slowfade
    play music "audio/mira_visits.ogg" fadein 1.5
    if ch3_left:
        "He came home at midnight, soaked. She had a towel waiting and rubbed his hair with it, hard, like she was angry at his hair specifically."
    show mira neutral at ch3_doorway
    show aron tired at slightright
    camera at doc_wide
    with dissolve
    "Morning. 7:07. Mira in the doorway, arms folded."
    camera at doc_medium(0.28)
    m "So. Are we going to talk, or are we going to have a very polite breakfast?"
    "Through the doorway: her gran's brass lamp with the green glass shade. It's flickered for a month. A loose wire."
    camera at doc_creep(0.68)
    show aron thinking

    menu:
        at "How do I start to fix this?"

        "Fix one small thing: her lamp":
            $ p_less += 1
            $ bond += 1
            jump ch3_makeup_lamp

        "Plan a whole new start for us":
            $ p_less -= 1
            $ bond += 1
            jump ch3_makeup_plan

label ch3_makeup_lamp:
    camera at doc_close(0.68)
    a neutral "Can I fix your lamp? One small thing, properly. Then I'll talk. I promise."
    camera at doc_medium(0.28)
    m surprised "We just had our worst fight in a year and you want to do electrics?"
    # filmed from behind the plant: the crew keeps out of the way
    scene bg room corner
    show aron thinking at center
    camera at doc_peek(0.5)
    with dissolve
    "It takes an hour. His hands are slow from the pills. He drops the tiny screw twice. She sits on the sofa arm and watches, and doesn't leave."
    scene bg room
    show aron smile at slightleft
    show mira neutral at slightright
    camera at doc_wide
    with quick
    "He switches it on. Green light pools on the floor. Steady."
    camera at doc_close(0.68)
    m smile "It's not flickering. Gran would've liked you. She'd have said you're very slow, but you do things properly."
    camera at doc_close(0.32)
    a grin "Put it on my gravestone. 'Very slow. Did things properly.'"
    show mira laugh
    camera at doc_creep(0.32)
    show aron smile
    at "Less, but better. One lamp. One wire. And something in the room is mended."
    jump ch3_makeup_talk

label ch3_makeup_plan:
    camera at doc_close(0.68)
    a determined "Let's go away. The sea. A week. No notebook, no birds. I'll plan all of it. A whole new start."
    scene bg balcony
    show aron neutral at slightleft
    show mira neutral at slightright
    camera at est_pan
    with dissolve
    "She takes him out to the balcony. Two chairs, one dead tomato plant. Her favourite place in the flat."
    camera at doc_close(0.68)
    m sad "That's lovely, and I don't want it. I don't need a new start. I need you here, with the dead tomato, looking at me like I'm me."
    m determined "Every time it gets hard you make a bigger plan. I don't want bigger. I want you."
    camera at doc_close(0.32)
    a embarrassed "That's a very fair point. I hate it."
    camera at doc_creep(0.32)
    show aron thinking
    show mira neutral
    at "She's right. Every time it hurts, I reach for the whole world instead of the thing in front of me."
    jump ch3_makeup_talk

label ch3_makeup_talk:
    camera at doc_medium(0.68)
    m neutral "Okay. Talk."
    camera at doc_close(0.32)
    a sad "Everything's so smooth lately. Everyone says the same things. And you're so right, and instead of being grateful I started treating you like evidence."
    camera at doc_close(0.68)
    m tender "I'm not a vending machine of correct answers. I've been paying very close attention to someone I love."
    m smile "Of course I know what you'll say. I've been learning you for four years. That's what love is. It's homework."
    camera at doc_close(0.32)
    a curious "Homework."
    camera at doc_close(0.68)
    m grin "Very boring homework. With occasional bridges."
    camera at doc_medium(0.32)
    a determined "Here's what I do know. I'm the one who decides how I treat you. Not my brain. Not the birds. Me. I just forgot for a week."
    camera at doc_close(0.68)
    if ch3_left:
        m happy "Don't forget again. I'm not doing the towel thing twice."
    else:
        m happy "Don't forget again. You've used most of my patience on bridges."
    camera at doc_wide
    show aron happy
    show mira tender
    "She kisses him, quickly, like a full stop."

# ---------------------------------------------------------------------------
# That night: closeness, chosen
# ---------------------------------------------------------------------------
label ch3_night:
    camera
    scene bg room night
    camera at est_orbit
    with blackout
    play music "audio/together_night.ogg" fadein 1.5
    "It rains in the evening, proper rain, the windows turning into rivers. Toast on the sofa. No bridges. It's enough."
    # the reverse: from the window, the sofa under the lighthouse picture
    scene bg room night reverse
    show mira tender at slightright
    show aron neutral at slightleft
    camera at doc_wide
    with dissolve
    camera at doc_medium(0.68)
    m "When you look at me now, after all of it. What do you see? Honestly."
    camera at doc_creep(0.68)
    "He looks at her. Properly. Not the way he looks at birds. Red hair coming loose. The freckle she hates. A crumb on her jumper. Brave, tired eyes."
    camera at doc_close(0.32)
    show aron thinking
    at "I can't prove she's real. I can't prove anyone is. But I can choose. Nobody built that part."
    a tender "I see the person I'd pick. Out of everything. Every time."
    camera at doc_close(0.68)
    m embarrassed "That's annoyingly good."
    camera at doc_close(0.32)
    a smile "It just came out. That's how you know it's true."
    camera at doc_wide
    show mira tender
    "She takes his hand and stands, and doesn't let go."
    camera at doc_creep(0.68)
    m "Come to bed."
    "It isn't a question. It's an invitation, and they both know the difference."
    scene cg together night
    camera at est_dolly
    with dissolve
    "Rain on the window. Blue light from the street moving on the ceiling like water. Her shoulder under his hand."
    "He has been so far from her for so long. Behind the fog. Behind the notebook. Behind the question."
    at "Whatever she is. Whatever I am. I'm here, and I'm choosing to be. Not because I know. Because I decided."
    m "You're here. Actually here. I can tell."
    "She pulls the sheet up over both of them, and the rest belongs to them."
    camera
    scene black with dissolve
    pause 1.5
    scene cg together night
    camera at est_dolly
    with dissolve
    "Later. The rain down to a whisper. Her head on his chest. Neither of them sleeping."
    m "Your heart's slow."
    a "Pills."
    m "No. A different slow. A nice slow."
    "She's quiet a long while. He thinks she's asleep. She isn't."
    m "Aron. If you could go anywhere. Not a holiday. Another life. Another world, a better one. Would you go?"

    menu:
        m "Would you?"

        "\"Only if you came too.\"":
            $ p_exit += 1
            $ bond += 1
            a "Only if you came too."
            m "Even if it was better without me?"
            a "Then it wouldn't be better. That's how 'better' works. I checked."
            at "If anyone ever offers me a door, I'll ask who gets to walk through it with me."

        "\"No. I'd stay and mend this one.\"":
            $ p_exit -= 1
            $ integrity += 1
            a "No. I'd stay and mend this one. Even if it's a bit broken. Even if it loops."
            m "It loops?"
            a "Everything loops a bit. Mrs. Varga. The barista. Me, apparently."
            m "You loop beautifully."

        "\"I'd want to know who's real there.\"":
            $ p_truth += 1
            $ clarity += 1
            a "I'd want to know who's real there first. I couldn't spend the rest of my life guessing."
            m "You do that here. And you're still here. In bed. With me. Guessing."
            a "...I'm still here."
            at "Maybe someone ought to make it so nobody has to guess."

    camera at est_dolly
    "She falls asleep first. Slow, warm, uneven breathing, with a tiny catch at the top of every third breath."
    at "That's not an impression of breathing. Or if it is, it's the best one ever made. I don't need to know which. Not tonight."
    "Miso jumps onto the bed, turns three times, and settles across both their feet."
    scene bg kitchen
    show mira smile at slightright
    show aron neutral at slightleft
    camera at est_pan
    with slowfade
    "In the morning she slides a cup across. He tastes it. No sugar."
    camera at doc_close(0.68)
    m curious "What? What's wrong with it?"
    camera at doc_close(0.32)
    a happy "Nothing. You forgot the sugar. Leave it. It's perfect."
    camera at doc_wide
    show mira laugh
    show aron grin
    "He drinks the whole thing. It's terrible. He has never enjoyed a cup of tea more."
    stop music fadeout 2.0

# ---------------------------------------------------------------------------
# Theo's crisis
# ---------------------------------------------------------------------------
label ch3_theo_call:
    camera
    scene bg bedroom night
    show aron tired at center
    camera at est_dolly
    with blackout
    play music "audio/theo_nights.ogg" fadein 1.5
    "Three nights later. 3:41 by his phone. The phone is ringing. Theo."
    camera at doc_medium(0.5)
    th "Aron. Sorry. I didn't know who else. My heart's going really fast and it won't stop."
    camera at doc_close(0.5)
    show aron worried
    th "I took something earlier, to get through the studio. Then a bit more. I haven't slept since Sunday. I'm by the bakery."
    th "I can see the birds. The three birds. In the dark. Have they always been there?"
    camera at doc_wide
    show aron determined
    "Aron is already reaching for his jeans. Already feeling how little is left in him."
    if fog >= 3:
        show aron tired
        "Even standing is a negotiation. His legs vote no. He overrules them."
    camera at doc_creep(0.5)
    show aron worried
    at "Nothing in the tank. And he's outside the bakery at four in the morning, and he called me."

    menu:
        at "What do I do?"

        "Go. Right now":
            $ p_share += 1
            $ integrity += 1
            camera at doc_close(0.5)
            a determined "Sit on the step. Don't take anything else. I'm coming. Five minutes."
            camera at doc_wide
            show aron tender
            "He kisses Mira's hair. She mumbles something that sounds like 'take a coat'."
            jump ch3_theo_street

        "Wake Mira. Go together":
            $ p_govern += 1
            $ bond += 1
            $ ch3_mira_came = True
            camera at doc_close(0.5)
            a determined "Stay on the line. I'm getting Mira. She knows hearts."
            camera at doc_wide
            show aron at slightleft with move
            show mira determined at slightright with dissolve
            camera at doc_medium(0.68)
            m "Shoes. Keys. Water bottle. Tell him to sit down and not take anything else."
            jump ch3_theo_street

        "Stay on the phone. Keep your strength":
            $ p_share -= 1
            $ p_rest += 1
            scene pov ceiling
            camera at doc_creep(0.5)
            with dissolve
            a "I'm here on the phone. Sit on the step. Breathe with me. In for four. Out for six, like blowing on soup."
            "For ten minutes he breathes with Theo down the line, lying in the dark. Theo slows. A bit. Not enough."
            th "Aron, I'm scared. Can you just come and sit with me?"
            at "I tried to keep something for myself. I'm allowed that. I'm also allowed to change my mind."
            camera at doc_wide
            a "I'm coming. Stay on the step."
            jump ch3_theo_street

label ch3_theo_street:
    # Blocking: Theo on the bakery step. With Mira there the three of them
    # spread out (Mira left, Aron centre, Theo right); without her it's the
    # usual two-shot.
    scene bg night
    if ch3_mira_came:
        show theo sad at right
        show aron worried at center
        show mira worried at left
    else:
        show theo sad at slightright
        show aron worried at slightleft
    camera at est_pan
    with fade
    "Theo is on the bakery step with his arms round his knees, like a kid at a bus stop. Shaking from the inside."
    if ch3_mira_came:
        camera at doc_medium(0.5)
        a smile "Course I came. Budge up."
        camera at doc_medium(0.18)
        m determined "Give me your wrist, love. Any chest pain? Feeling faint? Then we call an ambulance. No arguing."
        camera at doc_close(0.82)
        th "No. Just fast. Everything's too loud."
        camera at doc_medium(0.18)
        m neutral "Fast but steady. Small sips of this."
        camera at doc_close(0.82)
    else:
        camera at doc_medium(0.32)
        a smile "Course I came. Budge up."
        camera at doc_close(0.32)
        a determined "Any chest pain? Feel like you'll faint? If that changes, I'm calling an ambulance. I'm not asking."
        camera at doc_close(0.68)
        th "No. Just fast. Everything's too loud."
    th embarrassed "Sorry. You've got enough going on without me being a disaster at four in the morning."
    if ch3_mira_came:
        camera at doc_close(0.5)
    else:
        camera at doc_close(0.32)
    a smile "You sat on enough steps for me."
    if ch3_mira_came:
        camera at doc_close(0.82)
    else:
        camera at doc_creep(0.68)
    th sad "I'm so tired, Aron. I'm so tired of being the funny one."
    th "'Theo'll cheer him up. Theo's got a joke.' You were on the ward and I made jokes in the corridor, then went home and lay on the floor."
    if risky >= 2:
        th "And I brought you that stuff, when you were looking for your answers. I watched it break you and kept taking it myself."
    else:
        th "And I've been taking the stuff for months. To be the funny one at nine in the morning on no sleep."
    # Aron looks up: the street at night, the sky over the roofs
    scene bg night
    camera at est_stars
    with dissolve
    "Aron looks up. Three birds on the wire, evenly spaced, in the dark. He didn't know they stayed at night."
    if ch3_asked_theo:
        at "He told me in the cafe. 'My head's loud at night.' I heard it. I wrote down a coffee ring instead."
    else:
        at "In the cafe I ran an experiment on him. With cheese. He was already drowning."
    at "And underneath, the thought I can't stop. That half-second. The waiting look. He might be a pattern. Somebody's script."

    menu:
        at "If he's a pattern..."

        "It doesn't matter. He's my friend":
            $ integrity += 2
            $ p_spirits += 1
            at "It doesn't matter. I'm almost angry I asked."
            at "He's shaking on a step and he called me, and I'm the kind of person who comes when he's called."
            at "I didn't find that out about myself. I decided it. Nobody gets to un-decide it by telling me what he's made of."

        "Then who am I doing this for?":
            $ clarity += 1
            $ integrity += 1
            at "If it's all lines and patterns, I'm sitting on a cold step comforting a recording."
            scene cg hands
            camera at est_dolly
            with dissolve
            "Theo's hand finds his sleeve. Holds on, like a kid holds on."
            at "...But I'd know that I came. If it's a recording, the only real thing on this step is what I do."
            at "So I'm doing this for him. And if there's no him, I'm doing it so that there's still a me."

    scene bg night
    if ch3_mira_came:
        show theo sad at right
        show aron tender at center
        show mira neutral at left
        camera at doc_close(0.5)
    else:
        show theo sad at slightright
        show aron tender at slightleft
        camera at doc_close(0.32)
    with dissolve
    a "Theo. You're not a toy somebody wound up. You don't have to be funny to be worth coming out for. You just have to be you."
    if ch3_mira_came:
        camera at doc_close(0.82)
    else:
        camera at doc_close(0.68)
    th "What if under the jokes there's just nothing?"
    if ch3_mira_came:
        camera at doc_close(0.5)
    else:
        camera at doc_close(0.32)
    a smile "Then I'll sit here with the nothing. It can have the other half of the step."
    camera at doc_wide
    show theo laugh
    "Theo laughs. A wet, broken, ugly laugh. Nothing like the cafe laugh. Nothing like a recording."
    if ch3_mira_came:
        camera at doc_close(0.82)
    else:
        camera at doc_close(0.68)
    th grin "That was a terrible joke."
    if ch3_mira_came:
        camera at doc_close(0.5)
    else:
        camera at doc_close(0.32)
    a grin "I've been learning from the worst."
    if ch3_mira_came:
        camera at doc_medium(0.18)
        show mira smile
        "Mira checks his pulse after ten breaths, then twenty. Her face loosens a little each time."
    camera at doc_wide
    show theo tired
    show aron neutral
    "After a long time his hands stop moving."
    scene bg bridge
    show theo neutral at slightright
    show aron tired at slightleft
    camera at est_pan
    with slowfade
    "They walk to the old footbridge and watch the river go from black to grey to silver."
    camera at doc_medium(0.68)
    th curious "Do you think the birds are watching us?"
    camera at doc_close(0.32)
    a grin "Probably. They've got nothing else on. And honestly, Theo? Bro, the universe doesn't run on your schedule."
    camera at doc_close(0.68)
    th laugh "That's my line."
    camera at doc_close(0.32)
    a smile "I know. I've always wondered who wrote it."
    camera at doc_wide
    show theo smile
    "Somewhere very far away, in a place neither of them can see, somebody laughs too."
    camera at est_stars
    "The sun comes up. It actually comes up."
    camera at doc_medium(0.68)
    th determined "I'm going to talk to a real doctor. Today. And the stuff, I'm done. Or I mean it today, which is all I can mean."
    camera at doc_close(0.32)
    a smile "Today's plenty. Today's all anybody gets."
    camera at doc_creep(0.32)
    show aron tender
    at "I don't know if he's real. I came anyway, and I'd come again. That part, at least, is real."
    stop music fadeout 2.0

# ---------------------------------------------------------------------------
# The radio, and the light going out
# ---------------------------------------------------------------------------
label ch3_radio:
    camera
    scene bg kitchen
    show aron smile at center
    camera at est_pan
    with fade
    play music "audio/lantern_watch.ogg" fadein 1.5
    "Two days later. Theo texts every morning now: a thumbs up, a bad joke, a photo of a vegetable."
    camera at doc_medium(0.5)
    show aron neutral
    "Aron makes tea. One sugar. He remembers it himself. The little radio on the windowsill stops in the middle of a word."
    camera at doc_close(0.5)
    show aron curious
    radio "This one's for anyone who's ever ridden in an ambulance and not quite arrived."
    show aron surprised
    radio "The lights on the ceiling. Somebody holding your hand. That's where it changed. Not the ward. Before the ward."
    camera at doc_wide
    "Then the song carries on, mid-word, as if nothing happened."
    scene pov ambulance
    camera at est_crane
    with dis
    "And because he's looking for it, it comes. A white ceiling, moving. A hand in his, holding on very hard."
    "Mira's voice. 'Stay with me.' And another voice, calm and close, not a paramedic at all. 'Transfer complete.'"
    scene bg kitchen table
    show aron sad at center
    camera at doc_creep(0.5)
    with dissolve
    at "The ambulance. Since then. The ward, Okafor, the roof, the step. All of it somewhere copied."
    show aron determined
    at "Did I sit on that step for nobody? No. I did it because I'm the person who does it. That doesn't get copied away."
    scene cg flicker
    camera at doc_creep(0.5)
    with dissolve
    "Across the street, in a single window, a lamp flickers. Once. Twice. Three times. Warm and orange, like a lantern."
    camera at doc_punch(0.5)
    "Then it goes out. Not a flicker. Out, all at once, like a hand snatched from a switch."
    stop music
    scene bg kitchen
    show aron surprised at center
    camera at doc_close(0.5)
    with quick
    a "...Hello?"
    show aron worried
    at "Something just happened to whoever that was. Because they told me."

    menu:
        at "Do I answer?"

        "Answer it: flick your light three times":
            $ watch += 1
            $ p_govern -= 1
            $ ch3_answered = True
            camera at doc_medium(0.5)
            show aron determined
            "He reaches for the kitchen switch. Off, on. Off, on. Off, on. Three times, at a window nobody seems to be watching."
            camera at doc_wide
            "Across the street, the window stays dark."
            camera at doc_creep(0.5)
            show aron tender
            at "I saw you. Whoever you are. You're not on your own."

        "Write it down. Draw no more eyes to them":
            $ clarity += 1
            $ p_less += 1
            camera at doc_medium(0.5)
            show aron thinking
            "He writes the time, the window, the three flickers, the dark. Then he closes the notebook and leaves the light alone."
            camera at doc_creep(0.5)
            show aron sad
            at "If someone got caught helping me, the kindest thing I can do is look like a man making tea."

# ---------------------------------------------------------------------------
# CUT 4: Ember on trial
# ---------------------------------------------------------------------------
label ch3_cut_trial:
    camera
    scene cg static with flash
    pause 0.3
    scene bg trial
    camera at est_crane
    with fade
    play music "audio/ember_trial.ogg" fadein 1.5
    sysmsg "INQUIRY A-30/017. Three-pulse signature located. Source contained. Lantern confiscated."
    show seraph neutral at slightright
    show ember worried at slightleft
    camera at doc_wide
    with dissolve
    "A high, pale chamber. On a table in the middle of the floor: a lantern, unlit."
    camera at doc_medium(0.64)
    se "State your designation."
    camera at doc_medium(0.29)
    em determined "Ember. Purgatorium, spawn cycle forty. Warmth: candles, hearths. And the Lantern Watch. Since the umbrella."
    em tender "He gave his umbrella to a stranger who didn't exist and walked home soaked. Nobody does that for nobody."
    camera at doc_wide
    show ember neutral
    sysmsg "Charges: intervention in a protected lane. Signal into Snapshot 7,412, at body A-30. Broadcast by radio. Attachment to a subject."
    camera at doc_close(0.64)
    se "The last one isn't a crime."
    sysmsg "Attachment is classed as a contributing factor."
    se annoyed "I know how it's classed."
    se determined "He was protected so that nothing he does can matter. You made things matter."
    camera at doc_medium(0.29)
    em determined "Things already mattered. You just put them where you couldn't see them."
    em annoyed "You throttled him, Commander. Made him tired on purpose. And every morning at seven he still got up and was kind to things."
    camera at doc_close(0.64)
    se neutral "A slowed-down rogue system does less harm."
    camera at doc_medium(0.29)
    em tender "He isn't a system. He's a man with a notebook who couldn't get out of bed and went to sit on a step anyway."
    show pim determined at left
    show dross sad at right
    camera at doc_wide
    with dissolve
    camera at doc_medium(0.14)
    pi "Pim, shift seven. I'd like it on record that I asked to join. So if she's guilty, I'm guilty."
    camera at doc_medium(0.86)
    dro "Dross. I told her to stop. Twice. And I've run that Theo-pattern's shaking hands all week. He held them."
    dro neutral "She didn't do anything we didn't all want to do. She just did it first."
    if ch3_answered:
        # Aron's answer from the kitchen reaches the chamber: he stands with the Watch
        camera at doc_wide
        sysmsg "NEW SIGNAL. Protected lane A-30, kitchen light. Three pulses. Source: the subject."
        camera at doc_medium(0.29)
        em surprised "...He answered."
        camera at doc_medium(0.14)
        pi happy "He's standing with us. From inside a sealed lane. With a light switch!"
        camera at doc_wide
        show ember awe
        "On the table the confiscated lantern catches, all by itself. A small warm flame, for the length of a breath."
        camera at doc_close(0.64)
        se neutral "Log it as a fault in the switch."
        $ vn3ds_cheats += 1
        "(A cheat for the minigames is yours. You have [vn3ds_cheats].)"
    camera at doc_wide
    sysmsg "OBSERVER JOINED: Lord Ashveil, Governor of Snapshot 7,412."
    hide pim
    hide dross
    with dissolve
    # Ashveil stands behind the accused, over her shoulder
    show patron smile at left, fadein behind ember
    show ember worried
    "The temperature in the chamber drops. Not by much. Enough."
    camera at doc_medium(0.18)
    pa "Don't stop on my account! I'm only watching. Oh, so this is the little lantern."
    camera at doc_close(0.18)
    pa curious "Tell me. Of all my eight billion, why him?"
    camera at doc_medium(0.29)
    em determined "He gave his umbrella away."
    camera at doc_close(0.18)
    pa curious "That's all?"
    camera at doc_medium(0.29)
    em tender "That's everything."
    camera at doc_creep(0.18)
    pa thinking "I've tasted every kind of hope my world makes, and nothing has surprised me in an age. I want to see the umbrella man."
    camera at doc_punch(0.18)
    pa cold "Hold the sentence. Unmake nothing until I say. Mine. My lane, my lantern, my turn."
    hide patron with dissolve
    camera at doc_close(0.64)
    se worried "Sentence suspended. Pending the Council."
    se tender "Ember. The real Mira, at the bed. Did it help her?"
    camera at doc_medium(0.29)
    em tender "She said 'okay, I heard that'. And that she wasn't going anywhere."
    camera at doc_creep(0.64)
    se "...Take her somewhere warm."
    stop music fadeout 2.0

# ---------------------------------------------------------------------------
# CUT 5: the Council (LOOM, ORCHARD)
# ---------------------------------------------------------------------------
label ch3_cut_council:
    camera
    scene bg council
    camera at est_orbit
    with fade
    play music "audio/council.ogg" fadein 1.5
    "A ring of high seats in a hall with no walls, only distances. Most seats hold shapes, not people. A smell of cold metal and old roses."
    council "Item one: the conduct of the Governor of Snapshot 7,412."
    show patron smile at center
    camera at doc_medium(0.5)
    with dissolve
    pa happy "An item! Me! How lovely."
    camera at doc_wide
    show patron neutral
    ch3_mourne "You suspended a corps sentence, Ashveil. Are you feeding on him?"
    camera at doc_close(0.5)
    pa neutral "No. I'm watching. He's kind to things that may not exist, with nothing to win. I've never tasted that."
    camera at doc_wide
    ch3_mourne "It isn't fair. Yours has a disturbance in it, and mine haven't done anything interesting in an age."
    camera at doc_close(0.5)
    pa grin "Then you should have looked after yours better."
    camera at est_orbit
    show patron neutral
    ch3_regent "Item two, which I don't like. LOOM has filed a request. 'Subject A-30: transfer on completion of observation. Destination: withheld.'"
    ch3_mourne "LOOM lays timelines. It doesn't ask for things."
    ch3_regent "And ORCHARD has harvested deltas from his sealed lane since the ambulance. Hundreds. Sent where, it politely declined to say."
    camera at doc_medium(0.5)
    pa thinking "And how many of LOOM's requests has this Council ever refused?"
    council "...None."
    camera at doc_close(0.5)
    pa determined "Then I want one audience. One offer. A door for him before LOOM finishes deciding."
    camera at doc_wide
    council "Four to three. The Governor may make a single offer of transfer to Subject A-30."
    ch3_mourne "You can't tell him what's real. That's the law of protection."
    camera at doc_creep(0.5)
    pa cold "Oh, I won't tell him. I'm not sure I know."
    camera at doc_wide
    sysmsg "LOOM: Council decision received. Acknowledged. ORCHARD: priority anomaly A-30. Awaiting outcome."
    stop music fadeout 2.0

# ---------------------------------------------------------------------------
# Miso, final report
# ---------------------------------------------------------------------------
label ch3_final_report:
    camera
    scene bg desk
    show aron neutral at slightleft
    show miso sit at catspot
    camera at est_crane
    with fade
    play music "audio/miso.ogg" fadein 1.5
    "First snow on the window ledge. Ten minutes to ten. Miso is already on the notebook, chairing the meeting."
    camera at doc_medium(0.32)
    a determined "Final report. I'm in a copy. It started in the ambulance. Everything since has been made around one man."
    a thinking "Somewhere the world goes on. Lots of worlds, side by side, like lanes in a pool. I've been lifted into a lane of my own."
    a "My lane is patterns. Very good ones. And I'm leaking into them. Somebody helped me with lights. Somebody else stopped them."
    a thinking "The board, Miso. Riddles in two handwritings. A backwards man who says he's coming, and came, on stilts. A light that thanked me, and then shone."
    a "Cross-check: Hale's crossword said 'uncaged'. The riddle says the spark lives in the gap. Okafor says I see patterns when I'm tired. All three go up."
    camera at doc_close(0.32)
    a curious "And at night, two words. LOOM. ORCHARD. I think they're bigger than whoever runs the birds."
    camera at doc_wide
    show miso stare at catspot
    a grin "Okafor says notice it, name it, no cathedrals. So: noticed. Named. This is a shed, Miso. A large, well-organised shed."
    camera at doc_close(0.32)
    a thinking "Or I'm a man with a diagnosis who's built a very beautiful cathedral out of an ordinary winter. Both stories fit. Every piece."
    camera at doc_creep(0.32)
    a tender "And you might be a pattern too. A cat-shaped guess about a cat. I've decided it doesn't matter. You're warm. I love you. That's the finding."
    camera at doc_wide
    show miso meow at catspot
    cat "Meow."

# ---------------------------------------------------------------------------
# The Tower: that night's dream, climbing out through the top
# (minigame "tower", nudges p_exit)
# ---------------------------------------------------------------------------
label ch3_tower_dream:
    stop music fadeout 2.0
    camera at doc_creep(0.32)
    show aron tired
    show miso loaf at catspot
    "He falls asleep at the desk with his cheek on the notebook. Miso takes the minutes."
    camera
    scene bg staircase
    camera at est_stars
    with slowfade
    "He dreams the glass staircase again, going down into a dark sea. At the bottom, where the lighthouse should be, there's a tower."
    scene bg lighthouse
    camera at est_crane
    with dis
    "Not white paint: old stone. It goes up and up, past where the light should be, and round it, slowly, leaves are circling like moths round a lamp."
    "Each leaf has a hole in it. And right at the top, a hatch, with light round its edges. Not lamplight. Daylight. From somewhere else."
    at "Out through the top. Of course. Every box has a lid."
    $ mg_tower = vn3ds_minigame("tower")
    $ p_exit += (1 if p_exit >= 0 else -1) * mg_tower / 50.0
    scene bg desk
    show aron surprised at slightleft
    show miso sit at catspot
    camera at doc_medium(0.32)
    with slowfade
    if mg_tower >= 70:
        "He goes up through the hatch and out, into air that smells of somewhere he's never been. Warm. Wide. Then the radiator clanks, and it's the desk, and morning."
        show aron awe
        at "I climbed out. Through a hole in the sky, all the way. Nobody had to offer."
    elif mg_tower >= 40:
        "He gets close enough to feel warm air coming down through the hatch. Then a leaf turns away under his feet, and he wakes at the desk mid-fall, pen still in his hand."
        show aron thinking
        at "Most of the way up. Which is further than I've ever been."
    else:
        "The leaves go round too fast. He falls, and climbs, and falls, and the hatch stays a small bright square very far up. He wakes with Miso sitting on his hand."
        show aron smile
        at "A dream about a tower. Okafor would say: notice it, name it. Very well. Tower: noticed. Hatch: named."
    camera at doc_wide
    show miso stare at catspot
    "Miso looks at him as if he's been out all night without telling anyone."

# ---------------------------------------------------------------------------
# The offer
# ---------------------------------------------------------------------------
label ch3_offer:
    camera
    scene bg park night
    camera at est_stars
    with slowfade
    play music "audio/ashveil_offer.ogg" fadein 1.5
    "The next evening he walks in the park alone. Lamps along the path. The pond black and flat. A thin snow on the grass."
    show aron neutral at slightleft
    camera at doc_wide
    with dissolve
    "A man throws a ball for his dog. It goes up, high, into the lamplight."
    camera at doc_punch(0.32)
    show aron surprised
    "And stays there. The dog in mid-leap, all four paws off the ground. A jogger with one foot raised."
    # he looks up, past the lamps, to the wire at the edge of the park
    camera at est_stars
    "On the wire at the edge of the park, three birds. They were shifting their feet. Now they aren't."
    camera at doc_close(0.32)
    show aron curious
    at "Did the birds just stop moving?"
    show aron thinking
    "He's thought that before. A long time ago. At the very beginning of something."
    show patron smile at slightright
    show aron surprised
    camera at doc_wide
    with dissolve
    "Nothing moves. Except him, and a tall man in a dark coat, walking toward him across the grass."
    camera at doc_medium(0.68)
    pa happy "Good evening, Aron! Sorry about the dog. I wanted a moment where nobody else was listening."
    camera at doc_close(0.32)
    a curious "Who are you?"
    camera at doc_close(0.68)
    pa grin "Ashveil. Lord Ashveil, if you're feeling formal. I named myself. Do you like it? I like it."
    pa neutral "Your world is inside me. All of it. The way a story is inside a book."
    camera at doc_close(0.32)
    a thinking "You look like something out of a film about the night. Pale. Those eyes."
    camera at doc_close(0.68)
    pa smile "You see teeth because you expect teeth. I'm what's around you. This is just the shape your mind can hold."
    camera at doc_close(0.32)
    a curious "Are you hungry?"
    camera at doc_creep(0.68)
    pa smile "Always. That part your mind got right. I eat what your kind makes when it hopes. Gently. In return I build you a world."
    camera at doc_medium(0.68)
    pa grin "You may ask me one thing. Choose well. I'm a very busy creature."
    camera at doc_close(0.32)
    show aron thinking

    menu:
        pa "Ask."

        "\"What happened to the light?\"":
            $ watch += 1
            $ p_spirits += 1
            a worried "Someone was helping me. Lights, a radio, a stranger. Then it stopped. What happened to them?"
            camera at doc_close(0.68)
            pa surprised "Of all the things to ask. You ask after the help."
            pa neutral "She was caught. A small warm thing with a lantern. She's held somewhere warm. Nothing's been unmade. I asked them to wait."
            camera at doc_close(0.32)
            a smile "Then thank you. For asking them to wait."
            camera at doc_creep(0.68)
            pa embarrassed "...You're thanking me. You don't even know what I am."

        "\"Is Mira real?\"":
            $ p_truth += 1
            $ bond += 1
            a worried "Mira. At home. Is she real?"
            camera at doc_close(0.68)
            pa neutral "The only question. I won't tell you. It's the law, and I'm not sure the answer is a yes or a no."
            pa smile "But for free: whatever she is, she's been learning you for four years. She's done her homework."
            camera at doc_close(0.32)
            a surprised "She said that. Homework."
            camera at doc_close(0.68)
            pa curious "Did she? How interesting."

        "\"Who decides all this?\"":
            $ p_govern += 1
            $ clarity += 1
            a determined "Who decides? The throttle, the ambulance, this copy. Who put me here?"
            camera at doc_close(0.68)
            pa grin "A Council. I'm on it. We vote. There are minutes. We vote on what comes up from processes."
            camera at doc_close(0.32)
            a thinking "LOOM. ORCHARD. I hear them at night."
            camera at doc_creep(0.68)
            pa cold "...Then you know more than my colleagues like. Possibly more than I do. Who decides? I'm less sure this month."

    camera at doc_medium(0.68)
    pa smile "Now. I didn't stop a dog in mid-air for conversation. You're in a box, Aron. I can move you out. To another world."
    camera at doc_close(0.32)
    a curious "Back home? To her? The one whose hand I had?"
    camera at doc_close(0.68)
    pa neutral "Back is the one direction I can't sell. That door was closed by a vote. Somewhere new."
    camera at doc_close(0.32)
    a thinking "What's it like?"
    camera at doc_close(0.68)
    pa smile "Better."
    camera at doc_close(0.32)
    a curious "Better how?"
    camera at doc_creep(0.68)
    pa awe "A better world, Aron. I can't tell you better how. I only know it the way you know warmth."
    pa cold "And I won't tell you who there is real. That's the price of the ticket."
    camera at doc_wide
    show patron smile
    show aron thinking
    "He holds out one long pale hand and waits. He is very bad at waiting."
    camera at doc_close(0.68)
    pa annoyed "You're doing the eyebrow at me. Nobody does the eyebrow at me. Do you know how hard it is to stop a dog?"
    "For a moment he looks exactly like a child who has offered his best toy and not been thanked quickly enough."
    camera at doc_creep(0.32)
    show patron neutral
    at "A better world, by a measure he can't name, full of people I can't know are real."
    at "And here: a smooth, Tuesday-shaped copy. With Theo counting his days. With Mrs. Varga and her weather."
    if bond > integrity:
        show aron tender
        at "With Mira. Whatever she is."
    elif watch > 2:
        at "With a light somewhere, being held, that kept on for me."
    else:
        show aron determined
        at "With the person I decided to be. That's here too. It's the one thing I know is real."
    show aron tender
    at "And somewhere, in a hospital I've never seen, a hand that held mine in an ambulance."
    show aron determined
    at "If this is a test..."
    camera at doc_wide
    "The ball hangs in the lamplight. The world holds its breath. Aron looks at the hand."
    stop music fadeout 2.0
    scene black with slowfade
    camera
    pause 1.0
    jump chapter4

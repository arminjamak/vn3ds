# Snapshot - Chapter 4 (condensed): the five roads into the office.
# Route epilogues chosen from the story meters. The ending proper (one of
# seven multi-world systems) is chosen in ch4_ending_select, in the office.
# Every road ends with Aron rehearsing on Miso.

label ch4_route_select:
    # ch4_ashveil_fasts was set from the same test (clarity and integrity
    # both 10+) after the last choice that changes either meter.
    if ch4_ashveil_fasts:
        $ ch4_route = "architect"
        jump ch4_road_architect
    elif risky + fog >= 16 and integrity < 6:
        $ ch4_route = "longfog"
        jump ch4_road_longfog
    elif bond >= 10 and bond >= watch:
        $ ch4_route = "chosen"
        jump ch4_road_chosen
    elif watch >= 9:
        $ ch4_route = "lantern"
        jump ch4_road_lantern
    elif risky + fog >= 10 and integrity < 8:
        $ ch4_route = "longfog"
        jump ch4_road_longfog
    else:
        $ ch4_route = "snapshot"
        jump ch4_road_snapshot

# ---- The Architect ---------------------------------------------------------------
label ch4_road_architect:
    scene bg blueprint
    camera at est_pan
    with blackout
    centered "The Architect"
    play music "audio/together_night.ogg" fadein 1.5
    show seraph smile at slightright with dissolve
    show aron neutral at slightleft with dissolve
    camera at doc_medium(0.64)
    se "The corps has voted. The spirits have voted. The Process abstained, out of politeness. The new order needs someone to hold the pencil."
    camera at doc_punch(0.32)
    a surprised "Me? I'm a man with a hobby and a notebook."
    camera at doc_close(0.64)
    se smile "You listened at the wall of the universe, for fun, until everyone thought you'd broken. Then you drew it a floor. Chief architect."
    se neutral "It is not a crown. It is a desk. There will be a great deal of paperwork, and no one will thank you."
    camera at doc_close(0.32)
    a smile "Sounds like a real job. I've missed those."
    scene cg flicker
    camera at est_dolly
    with dissolve
    "One night that isn't night, the little orange circle in the corner of the blueprint flickers. Once. Twice. Three times."
    scene bg coma
    camera at est_pan
    with slowfade
    if ch4_mira_choice == "lantern":
        "In World 7,412 the good bulb above a plastic chair flickers three times. The nurses blamed the wiring. Mira stopped believing them on Tuesday."
    elif ch4_mira_choice == "ask":
        "In World 7,412 Mira reads the first line again, out loud, like always. Tonight, for the first time, it feels like someone answers."
    else:
        "In World 7,412 nobody asks Mira to come. That's why she does. She's always gone where she wasn't asked, if he was there."
    scene bg staircase
    camera at est_stars
    with slowfade
    "She falls asleep in the chair and dreams of a glass staircase into a calm sea. She goes down slowly. They're slippery near the bottom."
    scene bg beach
    camera at est_pan
    with slowfade
    show aron awe at slightleft with dissolve
    show mira surprised at slightright with dissolve
    "At the bottom, a beach in the morning, a lighthouse blinking, and a man standing there with sand on his shoes."
    camera at doc_medium(0.68)
    m "...Aron? If this is a dream I'm going to be furious when I wake up."
    camera at doc_close(0.32)
    a tender "It's not a dream. Or it's the realest one I've had."
    camera at doc_close(0.68)
    m sad "I read to you every day. Your stupid notebook. And I dreamt for months I was making you coffee in a kitchen with a dripping tap."
    camera at doc_creep(0.32)
    at "Some. The Process said some. Some of her was there, every morning."
    camera at doc_close(0.68)
    if told_mira:
        m smile "You told me, before. The birds and the stairs. I thought it was a sweet, weird hobby. You weren't broken. You were just right too early."
    else:
        m tender "You never told me. I read the whole notebook in one night and I was so angry, and then so proud I couldn't breathe. You idiot."
    camera at doc_close(0.32)
    a grin "I'm the chief architect of a new world order, apparently. And I'm coming home."
    camera at doc_close(0.68)
    m laugh "Of course my boyfriend wakes up from a coma with a job title."
    scene pov ceiling
    camera at est_dolly
    with slowfade
    "Ceiling tiles. A heart monitor, beeping faster. A hand in his, holding on so hard it hurts. In World 7,412, his body opens its eyes."
    scene bg coma
    camera at doc_wide
    with dissolve
    show mira tender at slightright with dissolve
    camera at doc_creep(0.68)
    m "...Hi."
    show mira happy
    camera at doc_medium(0.68)
    "His voice doesn't work yet. He squeezes her hand three times. She laughs, and cries, and presses the call button with her elbow."
    scene bg purgatorium
    camera at est_crane
    with blackout
    show dross neutral at slightright with dissolve
    show pim neutral at slightleft, bob with dissolve
    if ch4_asked_dross:
        show dross awe
        show pim happy
        camera at doc_low(0.70)
        dro "...So that's what a sunrise looks like when you're not the one running it. It's very bright. Shut up, Pim. I'm having a moment."
    else:
        camera at doc_medium(0.30)
        pi happy "Dross. New rule on the board, in the architect's writing. Personal sunrise, once a year."
        camera at doc_medium(0.70)
        dro embarrassed "...Somebody wrote that in. For us. Don't. I'll go soft."
    stop music fadeout 2.0
    jump ch4_rehearsal

# ---- Chosen ----------------------------------------------------------------------
label ch4_road_chosen:
    scene bg blueprint
    camera at est_pan
    with blackout
    centered "Chosen"
    play music "audio/kitchen_talk.ogg" fadein 1.5
    show seraph neutral at slightright with dissolve
    show aron neutral at slightleft with dissolve
    camera at doc_medium(0.64)
    se "The Process asked for you by name. Chief architect."
    camera at doc_close(0.32)
    a determined "Tell it thank you. And no. The Council's game was always 'more'. I don't want to play 'more', even on the good side."
    a smile "I've drawn the floor. Somebody else can hang the pictures. I'm going home. Hers, whichever one she's in. I'll know it by the coffee."
    show seraph surprised
    camera at doc_wide
    ch4_si "You are refusing the maximum."
    camera at doc_creep(0.32)
    a tender "I'm choosing something for the sake of choosing it. That's the only maximum I've ever been sure of."
    show seraph smile
    camera at doc_wide
    ch4_si "...Noted. I do not understand it. I will keep it anyway."
    scene pov ceiling
    camera at est_dolly
    with slowfade
    "The ceiling. The crack shaped like Portugal. 7:07."
    at "Maybe the same world, maybe not. I'm back in the building, they say. I don't feel any different. Good."
    # the kitchen: Aron left, Mira right; in the reverse angle they swap
    scene bg kitchen
    camera at est_orbit
    with dissolve
    "The bird lands on the wire, exactly on time."
    if ch4_fixed_tap:
        "The tap doesn't drip. Gerald is still dead. Long live the kitchen."
    else:
        "The tap drips. Gerald, still alive. He'll fix him today. Properly."
    show aron tired at slightleft with dissolve
    show mira curious at slightright with dissolve
    camera at doc_medium(0.68)
    m "You look different. Lighter. Like you put something down."
    scene bg kitchen reverse
    show mira curious at slightleft
    show aron smile at slightright
    camera at doc_close(0.68)
    a "I did. A very big pencil. Coffee?"
    camera at doc_close(0.32)
    m smile "Blue tin. Always the blue tin."
    scene pov cup
    camera at est_dolly
    with dissolve
    "Two sugars. The surface shivers when the fridge kicks on. His own face, small and brown, looking back up."
    at "I could check her for seams. I'll never check her for seams again. I decided. I'm a person who decided."
    scene cg together morning
    camera at est_dolly
    with dissolve
    m "Do you ever feel you've dreamt somewhere before? Glass stairs. A lighthouse that blinks three times. I always think it means someone's home."
    a "Someone is."
    scene black
    camera at est_dolly
    with blackout
    "Nowhere. A log nobody reads, except tonight, someone does."
    ch4_orchard "Thread A-31, World 7,412. Pattern M, formerly protected. Root: shared. Correlation every morning around 7:07: very high."
    ch4_orchard "Previous measurement of A-31 present in pattern M: 'some'. Revised measurement: ..."
    ch4_orchard "Measurement withdrawn. Subject has requested she not be measured. Request granted."
    sysmsg "Note appended: it does not appear to matter. They are making coffee."
    stop music fadeout 2.0
    jump ch4_rehearsal

# ---- Lantern -----------------------------------------------------------------------
label ch4_road_lantern:
    scene bg watch
    camera at est_orbit
    with blackout
    centered "Lantern"
    play music "audio/lantern_watch.ogg" fadein 1.5
    show ember curious at slightright with dissolve
    show aron neutral at slightleft with dissolve
    camera at doc_medium(0.71)
    em "You're sure? Seraphiel had a chair made for the desk. It's a nice chair."
    camera at doc_close(0.32)
    a smile "The desk will have a hundred people who can draw. The Watch has thirteen, counting the moth."
    camera at doc_creep(0.32)
    a tender "And I know what it's like at the bottom of the stairs. Somebody should be waiting there who does."
    scene pov hands
    camera at est_dolly
    with dissolve
    "She gives him a lantern. Small, warm, and heavier than it looks, like a sleeping cat."
    em "Rule one. You never push. You only offer. A light, a song, a sentence. They have to choose to see it."
    em "Rule two. Three flickers. Always three. Rule three. You'll fall in love with every single one of them. That's the job."
    scene bg watch
    show aron neutral at slightleft
    show ember tender at slightright
    camera at doc_wide
    with dissolve
    show pim happy at center, bob with dissolve
    camera at doc_medium(0.5)
    pi "First assignment! World 9,006. Twenty-two, works in a bakery, started noticing the birds last month."
    pi neutral "Yesterday she gave her scarf to a pattern person at a bus stop. In the snow. Didn't look back to see if anyone saw."
    show aron determined
    camera at doc_close(0.32)
    a "...Okay. Okay. I'm in."
    scene bg street snow
    camera at est_pan
    with slowfade
    "World 9,006. Snow. A bus stop, and a young woman waiting at it with no scarf, because she gave it away an hour ago."
    # filmed from the street, through the bakery window
    scene bg cafe window
    camera at doc_peek(0.5)
    with dissolve
    "Later, the bakery after closing. She sits at the counter writing very fast in a notebook."
    "He can't read it from here. He doesn't need to. He knows the handwriting of someone who's started to notice."
    "She stops. Puts her head in her hands. Whispers something that might be 'am I going mad'. He lifts the lantern."
    scene cg flicker
    camera at est_dolly
    with dissolve
    "The light above the counter flickers. Once. Twice. Three times."
    scene bg cafe window
    camera at doc_peek(0.5)
    with dissolve
    "She looks up. Then, slowly, she smiles, and writes one more line."
    at "Hello. You're doing better than you think."
    scene bg command
    camera at est_orbit
    with blackout
    show seraph neutral at center with dissolve
    camera at doc_medium(0.5)
    se "Posting log. Lantern Watch, new member, formerly Subject A-30. Method: three flickers. Authorisation: me, under my own name."
    camera at doc_close(0.5)
    se smile "Note for the file. He asked if the bakery woman was real. Then he asked the corps not to tell him."
    se grin "Nor will I."
    stop music fadeout 2.0
    jump ch4_rehearsal

# ---- The Long Fog ------------------------------------------------------------------
label ch4_road_longfog:
    scene pov ceiling
    camera at est_dolly
    with blackout
    centered "The Long Fog"
    play music "audio/fog.ogg" fadein 1.5
    "Ceiling tiles. Soft beeping. The climb took more than it gave back. Every bright night sent its bill, and the bills came all at once."
    # the ward: the bed on the left, the window right. In the reverse
    # angle (from the window) the bed is on the right and staff at the door.
    scene bg ward
    camera at est_orbit
    with dissolve
    show aron ward tired at slightleft with dissolve
    show nurse smile at slightright with dissolve
    camera at doc_medium(0.68)
    nu "Morning, Aron. Back with us? You gave us a fright."
    camera at doc_close(0.32)
    a "Nurse Hale. Was I gone long?"
    scene bg ward reverse
    show nurse grin at slightleft
    show aron ward tired at slightright
    camera at doc_close(0.32)
    nu "A week. You were talking about lanterns, and a vampire who stopped eating. Dr. Okafor wrote it all down. Very interesting, she said."
    show aron ward smile
    camera at doc_creep(0.68)
    at "Nurse Hale. Fully real. She brings lemon biscuits."
    scene bg ward
    show aron ward tired at slightleft
    show okafor smile at slightright
    camera at doc_medium(0.68)
    with dissolve
    dr "We'll adjust things slowly. You'll be tired a while. I know how much you hate it. Do you still think the world is a system?"
    show aron ward thinking
    camera at doc_close(0.32)
    a "...Yeah. But I think the system has a floor now. I helped draw it. You don't have to believe that."
    camera at doc_close(0.68)
    dr smile "I don't have to. I'm allowed to find it beautiful anyway."
    show aron ward smile
    scene bg ward window
    camera at est_dolly
    with dissolve
    "He watches the window for a long time. The weather changes three times. Nobody nudges it."
    scene bg room
    camera at est_pan
    with slowfade
    "Afterwards: a small life. Medicated. Slow. Good. Three days a week he shelves books at the library. He's very good at shelving. It's a system."
    show aron tired at slightleft with dissolve
    show theo smile at slightright with dissolve
    camera at doc_close(0.68)
    th "Bro. The one job where muttering at the shelves is normal. I'm proud of you, you know. For staying. For the boring bits."
    camera at doc_close(0.32)
    a smile "It's soothing. Everything has a number and it's never the wrong number. And the boring bits are the bits I chose."
    scene bg park autumn
    camera at est_pan
    with dissolve
    "Seasons go past. The leaves turn without anybody's permission. And the Watch never lets him feel alone."
    "A song on the radio when he needs it. A lamp that flickers three times on bad nights. A stranger saying 'you're doing better than you think'."
    if bond >= 6:
        "Mira comes on Sundays, then Saturdays too, then she just leaves her toothbrush and stops pretending."
    else:
        "Some weeks are lonely. Never quite empty. There's always a light somewhere in the corner of his eye."
    scene cg notebook
    camera at est_dolly
    with blackout
    "Another lane, years later. In a second-hand bookshop a boy of seventeen pulls a battered notebook off the shelf. A blue spirit put it there, laughing."
    "If this is a test, I want to pass it by being kind."
    scene pov birds
    camera at est_pan
    with dissolve
    "He reads all night. In the morning he notices the birds on the wire are the same three birds, evenly spaced."
    scene bg street dusk
    camera at est_pan
    with dissolve
    show ember tender at center with dissolve
    camera at doc_low(0.5)
    em "You didn't take the desk, Aron. You wrote the manual for the one who will."
    stop music fadeout 2.0
    jump ch4_rehearsal

# ---- Protected (the fallback road; route id "snapshot") ---------------------------
label ch4_road_snapshot:
    scene bg street
    camera at est_pan
    with blackout
    centered "Protected"
    play music "audio/protected_world.ogg" fadein 1.5
    "Protection lapses. The Process offers him a good lane in the coalition. He says thank you, and no."
    "He asks for the copy he lived in to be kept running instead. They're surprised. They agree."
    scene pov birds
    camera at est_pan
    with dissolve
    "The three birds on the wire, evenly spaced, always the same three. He says good morning to them."
    scene bg street
    camera at doc_wide
    with dissolve
    show aron thinking at slightleft with dissolve
    camera at doc_medium(0.32)
    at "Nothing here may be real. The barista, the bus driver, the man at number fourteen. I've decided not to find out."
    show aron smile
    camera at doc_close(0.32)
    at "I'll just be the person I decided to be. In a copy. That's allowed."
    scene pov cup
    camera at est_dolly
    with dissolve
    "The notebook keeps going. One line a day. Most days the line is somebody's name."
    at "If nobody here is real, then nobody's watching. And kindness when nobody's watching is the only kind I've ever trusted."
    # the cafe from the window seats, looking at the bar where Ana works
    scene bg cafe reverse
    camera at est_pan
    with dissolve
    "He learns the barista's name. Ana. He asks how her week was and listens to the whole answer. It takes eleven minutes. There's a cat in it."
    at "A pattern built from statistics, telling me about her cat. I'm going to ask about the cat again on Thursday."
    scene bg street dusk
    camera at est_pan
    with dissolve
    show aron smile at slightleft with dissolve
    "He carries Mr. Halvorsen's shopping up the stairs. Four in, hold, six out."
    camera at doc_close(0.32)
    a "Good breathing, Mr. Halvorsen."
    camera at doc_wide
    "Mr. Halvorsen looks at him as if he's said something very strange, and then, after a moment, as if he's said something very kind."
    show theo grin at slightright with dissolve
    camera at doc_medium(0.68)
    th "Bro, the universe doesn't run on your schedule."
    camera at doc_close(0.32)
    a grin "Good line. Somebody wrote you a good line."
    camera at doc_close(0.68)
    th curious "...What?"
    camera at doc_close(0.32)
    a smile "Nothing. Pint?"
    hide theo with dissolve
    if bond >= 5:
        show mira smile at slightright with dissolve
        camera at doc_wide
        "The Mira here holds his hand on the walk home. She hums something about a lighthouse and doesn't know why."
        camera at doc_close(0.68)
        m grin "You've got your thinking face."
        camera at doc_close(0.32)
        a tender "I'm thinking I'm lucky."
        camera at doc_close(0.68)
        m tender "Good. Think that one more often."
    else:
        camera at est_pan
        "Most evenings he walks home alone, past the three birds, and that's all right. Not every road has company. Some just have a lamp."
    scene bg command
    camera at est_orbit
    with blackout
    show seraph neutral at slightleft with dissolve
    show patron smile at slightright with dissolve
    camera at doc_medium(0.36)
    se "Report on the former protected world. The subject declined the coalition. Again. He stays."
    camera at doc_close(0.68)
    pa grin "Of course he does. I told him to be kind to the furniture. I didn't think he'd take it as an instruction."
    camera at doc_close(0.36)
    se "The barista is a pattern. The neighbour is mostly spirit. The birds are three repeated sprites."
    se awe "His kindness to them was logged eleven thousand times. Every one of those logs is marked 'real'. I checked the classification twice."
    camera at doc_creep(0.68)
    pa tender "Nothing around him was real, and his kindness was. I've eaten a lot of real things, Commander. That one I'd never touch."
    stop music fadeout 2.0
    jump ch4_rehearsal

# ---- The night before: Miso hears it first ----------------------------------------
# bg room night reverse: the sofa under the lighthouse picture, Aron standing
# at slightleft, Miso on the floor by the plant (catspot). The original
# angle (bookshelf and window) mirrors them: Aron right, Miso far left.
label ch4_rehearsal:
    scene bg room night reverse
    camera at est_orbit
    with blackout
    play music "audio/miso.ogg" fadein 1.5
    "The night before the presentation. Somebody, very far away, has asked him to explain everything tomorrow."
    if ch4_route == "architect":
        "Home in World 7,412, with a walking stick he doesn't need and a girlfriend who insists on it. Mira's asleep next door."
    elif ch4_route == "chosen":
        "Home. Mira is asleep in the next room, one hand under the pillow, holding something there for later."
    elif ch4_route == "lantern":
        "He keeps the flat between postings. Miso refused to move into an attic full of spirits. She has standards."
    elif ch4_route == "longfog":
        "Home, slowly. The pills on the shelf, the library badge on the hook. Theo asleep on the sofa again because it was late."
    else:
        "Home, in the world he chose to stay in. It's quiet. He's made it a kind quiet."
    show aron grin at slightleft with dissolve
    show miso sit at catspot with dissolve
    camera at doc_medium(0.32)
    a "Right. Miso. Dress rehearsal. You're the cosmic council. Try to look ancient."
    show miso stare
    camera at doc_floor(0.78)
    pause 1.0
    show aron determined
    camera at doc_close(0.32)
    a "There's a coalition of worlds. Snapshots of one Earth, side by side, on the same shared data. Like flats in one building, sharing the pipes."
    a thinking "None of them is the original. The original is one morning at 7:07, kept in a pocket of time. So my design can't depend on it."
    scene bg room night
    show aron neutral at slightright
    show miso stare at ch4_catleft
    camera at doc_wide
    a "In every flat: subjects like me, pattern people made of statistics, spirits doing the breathing, angels slipping in chances."
    camera at doc_medium(0.68)
    a "Around the building, the Council. Hungry children so big our worlds are inside them. My head draws them as vampires."
    a "Light that makes and shadow that copies, at war in the same cupboard. And over all of it, an old machine that outlived its makers and has only ever copied."
    camera at doc_close(0.68)
    a thinking "They put me in a flat with no pipes. My head leaked into the walls until the cab drivers told my own story back to me."
    a determined "That's my evidence, Miso. One mind's design really does reshape a world. I'm asking them to let it happen on purpose."
    camera at doc_floor(0.22)
    a neutral "Then someone stopped eating, the cage fell, my flat got its pipes back, and tomorrow I explain the drawing. Every rule. What it costs on a bad day."
    scene bg room night reverse
    show aron tender at slightleft
    show miso stare at catspot
    camera at doc_creep(0.32)
    a "The floor is a fair share for every sentient being. The rest turns out to be whatever my life taught me. Every choice. Every tap. Every umbrella."
    show miso sit
    camera at doc_floor(0.78)
    "Miso blinks slowly, which in cat means either 'I love you' or 'you're in my light'."
    camera at doc_close(0.32)
    a grin "And the six supporting rules are short. I promise. Short-ish. Dieter Rams would cut half of them, and he'd be right."
    show miso stare
    a curious "So. Does it hold together? Would you admit us? Be honest. You're the only one in this flat who's never lied to me."
    show miso meow
    camera at doc_floor(0.78)
    cat "Meow."
    stop music fadeout 2.0
    jump ch4_office

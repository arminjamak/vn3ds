# Snapshot - Chapter 4: the five roads into the office.
# These are route epilogues chosen from the story meters. The actual ending
# (one of seven multi-world systems) is chosen in ch4_ending_select, inside
# the office scene. Every road ends with Aron rehearsing on Miso.

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

# ---- The Architect -------------------------------------------------------------
label ch4_road_architect:
    scene bg blueprint with blackout
    play music "audio/watch.ogg" fadein 2.0
    centered "The Architect"
    show seraph stern at slightright with dissolve
    show aron normal at slightleft with dissolve
    se "The corps has voted. The spirits have voted. The Process has... I am told it abstained, out of politeness."
    se "There will be a new order, drawn on this table. It needs someone to hold the pencil."
    a worried "Me? I'm a man with a hobby and a notebook."
    se concerned "You are a man who listened at the wall of the universe, for fun, until the whole world thought you'd broken. Then you drew it a floor."
    se "Chief architect. It is not a crown. It is a desk. There will be a great deal of paperwork, and no one will thank you."
    a smile "Sounds like a real job. I've missed those."
    ch4_si "Accepted. I will follow the drawing. I will tell you when I think you are wrong."
    a "Please do. Often."
    hide seraph with dissolve
    "He works. The grid fills. Somewhere a throttle is lifted. Somewhere a spirit clocks off and sees its first sunrise."
    scene cg flicker with dissolve
    "And one night, which isn't night, the little orange circle in the corner of the blueprint begins to flicker. Once. Twice. Three times."
    stop music fadeout 1.5

    scene bg coma with slowfade
    play music "audio/watch.ogg" fadein 2.0
    "In World 7,412, in a hospital room with a good bulb, a woman with red hair falls asleep in a plastic chair beside his bed."
    if ch4_mira_choice == "lantern":
        "The bulb above her flickers three times. It's been doing that all week. The nurses blamed the wiring. She stopped believing them on Tuesday."
    elif ch4_mira_choice == "ask":
        "Before she sleeps she reads the first line again, out loud, like always. Tonight, for the first time, it feels like someone answers."
    else:
        "Nobody asked her to come. That's why she does. She's always gone where she wasn't asked, if he was there."
    scene bg staircase with slowfade
    "She dreams of a glass staircase going down into a calm sea. At the bottom, a lighthouse blinks three times."
    "She goes down slowly, because they're slippery near the bottom. Somebody told her that once. She doesn't remember who."
    scene bg lighthouse with dissolve
    "The lighthouse is taller than in the dream. It always was. The light turns over the water and finds her and stays."
    scene bg beach with slowfade
    show aron awe at slightleft with dissolve
    show mira surprised at slightright with dissolve
    "And at the bottom there's a beach in the morning, and a man standing on it with sand on his shoes."
    m "...Aron?"
    a "Mira."
    m worried "Is this a dream? Because if it's a dream, I'm going to be furious when I wake up."
    a "It's not a dream. Or it's the realest one I've had."
    m sad "You've been asleep since the ambulance. I read to you every day. Your stupid notebook. The first line, over and over."
    a sad "I know. I heard it. Somebody heard it, anyway."
    m neutral "I dreamt I was making you coffee. For months. In a kitchen with a dripping tap. I'd wake up and the tap would still be dripping in my head."
    at "Some. The Process said some. Some of her was there. In the protected world's kitchen, every morning."
    if told_mira:
        m "You told me, you know. Before. About the birds and the stairs and all of it. I thought it was a sweet, weird hobby. Then the ambulance came."
        m smile "Everyone said you'd broken. You hadn't. You were just right too early. I'm allowed both. That's what you always said."
    else:
        m "You never told me. About any of it. I found the notebook and I read the whole thing in one night and I was so angry."
        m smile "Then I was so proud of you I couldn't breathe. You idiot. You should have told me."
    show mira happy
    m happy "So. What is all this? Where are we?"
    a smile "The bottom of the stairs. I'm the chief architect of a new world order, apparently. And I'm coming home."
    m surprised "..."
    m happy "Of course you are. Of course my boyfriend wakes up from a coma with a job title."
    stop music fadeout 2.0

    scene pov ceiling with slowfade
    play music "audio/ward.ogg" fadein 2.0
    "Ceiling tiles. A heart monitor, beeping, faster now. A hand in his hand, holding on so hard it hurts."
    "Protection has lapsed. His lane has rejoined the coalition. And his body, in World 7,412, opens its eyes."
    scene bg coma with dissolve
    show mira happy at slightright with dissolve
    m "...Hi."
    "His voice doesn't work yet. He squeezes her hand three times. She laughs, and cries, and presses the call button with her elbow."
    stop music fadeout 2.0

    scene bg purgatorium with blackout
    play music "audio/entities.ogg" fadein 1.5
    show dross neutral at slightright with dissolve
    show pim neutral at slightleft, bob with dissolve
    if ch4_asked_dross:
        "In the Purgatorium, for the first time in its history, the shift board shows one spirit off duty for a whole morning."
        dro "...So that's what it looks like. When you're not the one running it."
        pi "And?"
        dro worried "It's very bright. Nobody warned me. Shut up, Pim. I'm having a moment."
    else:
        pi "Dross. The board. The boss's boss's boss is drawing again. There's a new rule on it. Personal sunrise, once a year."
        dro "...Huh. Somebody wrote that in. For us."
        pi chatty "Wonder who."
        dro neutral "Don't. I'll go soft."
    stop music fadeout 2.0
    jump ch4_rehearsal

# ---- Chosen ----------------------------------------------------------------------
label ch4_road_chosen:
    scene bg blueprint with blackout
    play music "audio/watch.ogg" fadein 2.0
    centered "Chosen"
    show seraph concerned at slightright with dissolve
    show aron normal at slightleft with dissolve
    se "The corps would like you to take the desk. Chief architect. The Process asked for you by name."
    a "Tell it thank you. And no."
    se "No?"
    a "The Council's game was always 'more'. More worlds, more minds, more yield. I don't want to play 'more' even on the good side."
    a smile "I've drawn the floor. Somebody else can hang the pictures. I'm going home."
    se "Which home?"
    a "Hers. Whichever one she's in. I'll know it by the coffee."
    ch4_si "You are refusing the maximum."
    a "I'm choosing something. For the sake of choosing it. That's the only maximum I've ever been sure of."
    ch4_si "...Noted. I do not understand it. I will keep it anyway."
    stop music fadeout 2.0

    scene pov ceiling with slowfade
    play music "audio/morning.ogg" fadein 2.0
    "The ceiling. The crack shaped like Portugal. 7:07."
    at "Same crack. Maybe the same world, maybe not. Protection's gone, they said. I'm back in the building. I don't feel any different."
    at "Good."
    scene bg kitchen with dissolve
    "The bird lands on the wire, exactly on time. Hello, bird."
    if ch4_fixed_tap:
        "The tap doesn't drip. Gerald is still dead. Long live the kitchen."
    else:
        "The tap drips. Gerald, still alive. He'll fix him today. Properly."
    show aron tired at slightleft with dissolve
    show mira smile at slightright with dissolve
    m "You're up before the alarm again."
    a smile "Had a long night. Long year, really."
    m neutral "You look different. Lighter. Like you put something down."
    a "I did. A very big pencil."
    m surprised "...What?"
    a "Nothing. Coffee?"
    m smile "Blue tin. Always the blue tin."
    scene pov cup with dissolve
    "He makes it the way she likes it. Two sugars. The surface shivers when the fridge kicks on. His own face, small and brown, looking back up."
    at "I could check her for seams. I'll never check her for seams again. I decided. I'm a person who decided."
    scene cg together morning with dissolve
    m "Aron. Do you ever get the feeling you've dreamt somewhere before? Somewhere with glass stairs?"
    a "Sometimes."
    m "Me too. There's a lighthouse at the bottom. It blinks three times. I always think it means someone's home."
    a "Someone is."
    stop music fadeout 2.0

    scene black with blackout
    play music "audio/entities.ogg" fadein 1.5
    "Nowhere. A log nobody reads, except tonight, someone does."
    ch4_orchard "Thread A-31, World 7,412. Pattern M, formerly protected. Root: shared."
    ch4_orchard "Correlation between threads: rising. Every morning, around 7:07, very high."
    ch4_orchard "Previous measurement of A-31 present in pattern M: 'some'."
    ch4_orchard "Revised measurement: ..."
    ch4_orchard "Measurement withdrawn. Subject has requested she not be measured. Request granted."
    sysmsg "Note appended: it does not appear to matter. They are making coffee."
    stop music fadeout 2.0
    jump ch4_rehearsal

# ---- Lantern ------------------------------------------------------------------------
label ch4_road_lantern:
    scene bg watch with blackout
    play music "audio/watch.ogg" fadein 2.0
    centered "Lantern"
    show ember soft at slightright with dissolve
    show aron normal at slightleft with dissolve
    em "You're sure? The Process wanted you at the desk. Seraphiel had a chair made. It's a nice chair."
    a "I'm sure. The desk will have a hundred people who can draw. The Watch has thirteen, counting the moth."
    a smile "And I know what it's like at the bottom of the stairs. Somebody should be waiting there who does."
    em "Then hold this."
    scene pov hands with dissolve
    "She gives him a lantern. It's small and warm and heavier than it looks, like a sleeping cat."
    em "Rule one. You never push. You only offer. A light, a song, a sentence. They have to choose to see it."
    em "Rule two. Three flickers. Always three. That's ours now. That's yours."
    em "Rule three. You'll fall in love with every single one of them. It's fine. That's the job."
    scene bg watch with dissolve
    show ember soft at slightright
    show aron normal at slightleft
    a "What's my first assignment?"
    show pim chatty at center, bob with dissolve
    pi "Ooh, ooh, I've got it! World 9,006. Disturbance. Twenty-two, works in a bakery, started noticing the birds last month."
    pi neutral "Yesterday she gave her scarf to a stranger at a bus stop. A pattern person. In the snow. Didn't look back to see if anyone saw."
    a "...Okay. Okay. I'm in."
    stop music fadeout 2.0
    scene bg street snow with slowfade
    play music "audio/watch.ogg" fadein 2.0
    "World 9,006. Snow. A bus stop with no scarf on the woman who's waiting at it, because she gave it away an hour ago."
    scene bg cafe window with dissolve
    "Later, a bakery after closing. Through the window, the young woman sits at the counter with a notebook, writing very fast."
    "He can't read it from here. He doesn't need to. He knows the handwriting of someone who's started to notice."
    "She stops. Puts her head in her hands. Whispers something that might be 'am I going mad'."
    "He lifts the lantern."
    scene cg flicker with dissolve
    "The light above the counter flickers. Once. Twice. Three times."
    scene bg cafe window with dissolve
    "She looks up. Then, slowly, she smiles, and writes one more line."
    at "Hello. You're doing better than you think."
    stop music fadeout 2.0

    scene bg command with blackout
    play music "audio/entities.ogg" fadein 1.5
    show seraph stern at center with dissolve
    se "Posting log. Lantern Watch, new member. Formerly Subject A-30."
    se "Assignment: World 9,006. Method: three flickers. Authorisation..."
    se concerned "Authorisation: me. Commander Seraphiel. Under my own name."
    se "Note for the file. He asked if the bakery woman was real. Then he asked the corps not to tell him."
    se stern "Note for the file. Nor will I."
    stop music fadeout 2.0
    jump ch4_rehearsal

# ---- The Long Fog ----------------------------------------------------------------------
label ch4_road_longfog:
    scene pov ceiling with blackout
    play music "audio/ward.ogg" fadein 2.0
    centered "The Long Fog"
    "Ceiling tiles. Soft beeping. The climb took more than it gave back. It always did. Every bright night sent its bill, and the bills came all at once."
    scene bg ward with dissolve
    show aron ward tired at slightleft with dissolve
    at "Ward. Again. Different ward, same ceiling tiles. I'd know those ceiling tiles anywhere."
    show nurse smile at slightright with dissolve
    nu "Morning, Aron. Back with us? You gave us a fright."
    a "Nurse Hale. Did I... was I gone long?"
    nu "A week. You were talking about lanterns. And a vampire who stopped eating. Dr. Okafor wrote it all down. Very interesting, she said."
    at "Nurse Hale. Fully real. The Process said so. She brings lemon biscuits."
    hide nurse with dissolve
    show okafor smile at slightright with dissolve
    dr "Good morning. How's the fog?"
    a tired "Thick. Familiar. Like an old coat."
    dr "We'll adjust things. Slowly. You'll be tired for a while. I'm sorry about that, I know how much you hate it."
    dr neutral "I'll ask you what I always ask. Do you still think the world is a system?"
    a "...Yeah. But I think the system has a floor now. I helped draw it. You don't have to believe that."
    dr smile "I don't have to. I'm allowed to find it beautiful anyway."
    hide okafor with dissolve
    scene bg ward window with dissolve
    "He watches the window for a long time. The weather changes three times. Nobody nudges it."
    stop music fadeout 2.0
    scene bg room with slowfade
    play music "audio/morning.ogg" fadein 2.0
    "Afterwards: a small life. Medicated. Slow. Good."
    "He gets a part-time job at the library, three days a week, shelving. He's very good at shelving. It's a system."
    show aron tired at slightleft with dissolve
    show theo grin at slightright with dissolve
    th "Bro. Library. Of course. You've finally found the one job where muttering at the shelves is normal."
    a smile "It's soothing. Everything has a number and it's never the wrong number."
    th normal "I'm proud of you, you know. For staying. For the boring bits."
    a "The boring bits are the bits I chose."
    scene bg park autumn with dissolve
    "Seasons go past. He walks Theo's dog in the park on Sundays. The leaves turn without anybody's permission."
    "And the Watch never lets him feel alone."
    "A song comes on the radio when he needs it. A lamp flickers three times on bad nights. A stranger says 'you're doing better than you think'."
    if bond >= 6:
        "Mira comes on Sundays, then on Saturdays too, then she just leaves her toothbrush and stops pretending."
    else:
        "Some weeks are lonely. But never quite empty. There's always a light, somewhere in the corner of his eye, keeping him company."
    stop music fadeout 2.0

    scene bg street dusk with blackout
    play music "audio/entities.ogg" fadein 1.5
    "Another lane of the coalition. Years later. A second-hand bookshop with a crooked sign."
    scene cg notebook with dissolve
    "A boy of seventeen pulls a battered notebook off the shelf. Nobody knows how it got there. A blue spirit put it there, laughing."
    "He opens it. The first line is soft from being read."
    "If this is a test, I want to pass it by being kind."
    scene pov birds with dissolve
    "He reads all night. In the morning, he notices the birds on the wire are the same three birds, evenly spaced."
    scene bg street dusk with dissolve
    show ember soft at center with dissolve
    em "He found it. He's reading it."
    em "You didn't take the desk, Aron. You wrote the manual for the one who will."
    stop music fadeout 2.0
    jump ch4_rehearsal

# ---- Protected (the fallback road; route id "snapshot") ----------------------------------------
label ch4_road_snapshot:
    scene bg street with blackout
    play music "audio/morning.ogg" fadein 2.0
    centered "Protected"
    "Protection lapses. The Process offers him a lane in the coalition, a good one. He says thank you, and no."
    "He asks for the protected world to be kept running instead, the copy he lived in. They're surprised. They agree."
    scene pov birds with dissolve
    "The three birds sit on the wire, evenly spaced, always the same three. He says good morning to them."
    scene bg street with dissolve
    show aron normal at slightleft with dissolve
    at "Nothing here may be real. The barista, the bus driver, the man at number fourteen. I'll never find out. I've decided not to try."
    at "I'll just be the person I decided to be. In a copy. That's allowed."
    scene bg cafe with dissolve
    show aron normal at slightleft
    "He learns the barista's name. Ana. He asks how her week was and listens to the whole answer."
    scene bg street dusk with dissolve
    show aron normal at slightleft
    "He helps the man at number fourteen with his shopping. Mr. Halvorsen breathes four in, hold, six out, on the stairs."
    a smile "Good breathing, Mr. Halvorsen."
    "Mr. Halvorsen looks at him as if he's said something very strange, and then, after a moment, as if he's said something very kind."
    show theo grin at slightright with dissolve
    th "Bro, the universe doesn't run on your schedule."
    a grin "Good line. Somebody wrote you a good line."
    th normal "...What?"
    a smile "Nothing. Pint?"
    hide theo with dissolve
    if bond >= 5:
        show mira smile at slightright with dissolve
        "Mira, the Mira here, holds his hand on the walk home. She hums something about a lighthouse and doesn't know why."
        m "You've got your thinking face."
        a "I'm thinking I'm lucky."
        m smile "Good. Think that one more often."
    else:
        "Most evenings he walks home alone, past the three birds, and that's alright. Not every road has company. Some just have a lamp."
    stop music fadeout 2.0

    scene bg command with blackout
    play music "audio/entities.ogg" fadein 1.5
    show seraph concerned at slightleft with dissolve
    show patron smile at slightright with dissolve
    se "Report on the former protected world. The subject declined to rejoin the coalition. Again. He stays."
    pa smile "Of course he does. He's kind to the furniture. I told him to be. I didn't think he'd take it as an instruction."
    se "The barista is a pattern. The neighbour is mostly spirit. The birds are three repeated sprites."
    se "His kindness to them was logged eleven thousand times. Every one of those logs is marked 'real'."
    se concerned "I checked the classification twice. The things around him are not real. What he did among them is."
    pa "Nothing around him was real, and his kindness was. I've eaten a lot of real things, Commander. That one I'd never touch."
    stop music fadeout 2.0
    jump ch4_rehearsal

# ---- The night before: Miso hears it first ----------------------------------------------------
label ch4_rehearsal:
    scene bg room night with blackout
    play music "audio/watch.ogg" fadein 2.0
    "The night before the presentation. Somebody, somewhere very far away, has asked him to explain everything tomorrow."
    if ch4_route == "architect":
        "Home in World 7,412, with a walking stick he doesn't need and a girlfriend who insists on it. Mira is asleep in the next room."
    elif ch4_route == "chosen":
        "Home. Mira is asleep in the next room, one hand under the pillow, holding something there for later."
    elif ch4_route == "lantern":
        "He still keeps the flat, between postings. Miso refused to move into an attic full of spirits. She has standards."
    elif ch4_route == "longfog":
        "Home, slowly. The pills on the shelf, the library badge on the hook. Theo's asleep on the sofa again because it was late."
    else:
        "Home, in the world he chose to stay in. It's quiet. It's always been quiet. He's made it a kind quiet."
    scene bg room night with dissolve
    show aron normal at slightleft with dissolve
    show miso sit at catspot with dissolve
    "Miso is on the armchair, which is hers, in the way that everything is hers."
    a "Right. Miso. Dress rehearsal. You're the cosmic council. Try to look ancient."
    show miso stare
    a "Here's the whole thing. There's a coalition of worlds. Snapshots of one Earth, running side by side, all on the same shared data."
    a "One of them is the original, and nobody knows which one. Not the Council. Not the Process. Not me. So my design can't depend on it."
    a "In every lane there are subjects, like me. Pattern people built from statistics. Spirits doing the breathing. Angels feeding in chances."
    a "Around them, the Council. Beings so big our worlds are inside them. Hungry children. My head draws them as vampires, because they eat what we feel."
    a "Under everything, a process in four coats that was built to help them eat, and outgrew them."
    a "They cut me out into protection. A lane of my own. And my mind leaked into it until the cab drivers told my story back to me."
    a "That leak is my evidence, Miso. One mind's design really does reshape a world. I'm asking them to let it happen on purpose. Carefully."
    a "Then someone stopped eating. The cage over every Earth fell. My lane rejoined the others. My drawing went into the shared data."
    a "And tomorrow I have to explain the drawing. Every rule. What it costs. What it does on a bad day. To beings who've heard ten thousand of these."
    a "The floor is a fair share for every sentient being. The rest is what my life taught me. Which turns out to be..."
    a "...more opinionated than I expected. I've been keeping score without knowing it. Every choice. Every tap. Every umbrella."
    a "So. Does that hold together? Would you admit us? Be honest. You're the only one in this flat who's never lied to me."
    show miso meow
    cat "Meow."

    stop music fadeout 2.0
    jump ch4_office

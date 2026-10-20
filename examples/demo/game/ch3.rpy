# Chapter 3 - "Snapshot" (condensed, about 30 minutes).
# Life in the protected world: smooth, looping, a Mira who is sometimes too
# right. Aron tests the leaks quietly, as a hobby. The leak escalates; the
# reveal (he was moved in the ambulance at the end of ch1); the relapse scare;
# the fight and the night; Theo's crisis; Ember's trial; the Council; and
# Ashveil's offer. Ends unanswered: chapter 4 opens with the answer.

define ch3_varga = Character("Mrs. Varga", color="#e3c9b0")
define ch3_barista = Character("Barista", color="#e0c39a")
define ch3_shop = Character("Shop assistant", color="#d0b890")
define ch3_tannoy = Character("Tannoy", color="#bbbbbb")
define ch3_crowd = Character("Passengers", color="#cccccc")
define ch3_driver = Character("Bus driver", color="#c0c0c0")
define ch3_mourne = Character("Lady Mourne", color="#c88aff")
define ch3_regent = Character("The Grey Regent", color="#b8b8d0")

default ch3_said_off = False
default ch3_asked_theo = False
default ch3_pill = False
default ch3_left = False
default ch3_mira_came = False

label chapter3:
    $ chapter = 3
    scene black with blackout
    centered "Chapter 3\n\nSnapshot"
    pause 1.0

    scene pov ceiling with slowfade
    play music "audio/protected_world.ogg" fadein 1.5
    "7:07."
    "The Braun clock says it the way it always does: plainly, without opinion."
    at "My ceiling. The crack shaped like Portugal. My bed, with me in it, which is where I left me."
    at "Last night: the roof. An orange light on the edge of the city, blinking three times. Then the stairs, then Miso, then sleep."
    at "I decided something up there. A secret mission, for the rest of my life. It still feels true in daylight. Good sign."
    scene bg bedroom with dissolve
    show aron normal at center with dissolve
    show miso loaf at catspot with dissolve
    "Miso is folded at the foot of the bed into a perfect orange loaf."
    "He sits up. The duvet slides off him in one smooth fold and lands neatly on the floor."
    "Not crumpled. Folded."
    if fog >= 3:
        "The medication is still there, wet sand from the neck down. But it's tidier this morning. As if someone had ironed it."
    else:
        "He's tired, the way he's always tired since the ward. But it's a tidier tiredness. As if someone had ironed it."
    a grin "Less, but better. Even my exhaustion has been designed, Miso. Dieter Rams would approve."
    "Miso does not open her eyes. Miso has never once taken a meeting before breakfast."

    scene bg kitchen with dissolve
    show aron normal at slightleft
    show mira smile at slightright
    with dissolve
    m "You're up. You came down off that roof last night grinning like somebody had proposed to you."
    a smile "Somebody sort of did. The universe, possibly. I'm still reading the small print."
    "Outside, the bird drops onto the wire and folds its wings. The oven clock says 7:07."
    at "I've been awake for at least five minutes. Unless the minute waited for me."
    "The coffee machine starts. The gurgle, the hiss, the two dry coughs at the end. Exactly right."
    "Like a recording of itself."
    at "'Exactly right' goes in the notebook. Under 'suspiciously excellent'."
    scene bg kitchen table with dissolve
    show aron normal at slightleft
    show mira smile at slightright
    with dissolve
    m "Tea. One sugar."
    scene pov cup with quick
    "A pale brown circle. A small trembling window in it, and the wire, and the bird."
    "He tastes it. One sugar."
    scene bg kitchen table with quick
    show aron grin at slightleft
    show mira smile at slightright
    a "You remembered the sugar. You never remember the sugar. It's the only flaw I've found in you in four years."
    m "Then today's a good day."
    "She smiles the way she always smiles. The left side first, then the right. Freckles rearranging themselves."
    at "It's lovely. It's her. Isn't it?"
    if told_mira:
        m "So. How's the mission? Day one."
        "She says it lightly, the way you'd ask about a hobby. Not long ago the same idea made her cry in a corridor."
        at "That's exactly what I wanted her to say. Word for word. Which is wonderful, and which I'll write down later, very quietly."
    else:
        m "You've got the eyebrow. It means you've noticed something and you're deciding whether to tell me."
        at "She doesn't know about the mission. But she always knows when I'm deciding."

    menu:
        m "Well?"

        "Tell her something feels off":
            $ p_truth += 1
            $ bond += 1
            $ ch3_said_off = True
            a normal "Honestly? Something feels off. Not wrong. Smooth. The coffee's right. The clock waited for me. You remembered the sugar."
            m neutral "And those are bad things?"
            a "No. That's what's bad about them."
            m smile "I know what you mean. I feel it too, sometimes. Like the world's been ironed."
            at "Ironed. That's exactly the word I'd have used. She always finds the word. That's not evidence of anything."
            at "If she's a copy, I just told a copy. If she isn't, I told the truth to the woman I love. I'd rather have said it."

        "Keep it light. Have breakfast":
            $ p_truth -= 1
            $ integrity += 1
            a normal "Breakfast. Then errands. Then coffee with Theo. A normal Saturday."
            m happy "A normal Saturday. Look at you."
            a grin "I contain multitudes. Most of them want toast."
            "The toast is golden all the way across. Not one burnt corner."
            at "I won't put this on her today. She's carried enough of my weather. It's a hobby. Hobbies can be private."

    m neutral "Bin on your way out. And say hello to Mrs. Varga."

label ch3_errands:
    scene bg street with dissolve
    play music "audio/the_leak.ogg" fadein 1.5
    "Errands. Bin, bakery, coffee with Theo. And a private game on the side: let's see what the street says today."
    scene pov birds with dissolve
    "On the long wire over the road, three birds. Evenly spaced. Always the same three."
    at "Morning, lads. Same shift as always?"
    scene bg street with dissolve
    show aron normal at slightleft with dissolve
    "Mrs. Varga is on her front step with her tartan trolley, sweeping, very upright."
    ch3_varga "Cold for the season, isn't it?"
    a "Morning, Mrs. Varga. It is a bit."
    "It's warm. It's been warm all week. He takes the bin down. Lid, bag, lid. On the way back up the path, she looks up."
    ch3_varga "Cold for the season, isn't it?"
    a grin "We did this thirty seconds ago, Mrs. Varga."
    ch3_varga "Did we, dear? Cold for the..."
    "She stops on the 's'. The broom stops mid-sweep. A falling leaf hangs in the air beside her shoulder."
    "One second. Two."
    ch3_varga "...season, isn't it?"
    "The leaf lands. The broom moves. She smiles at him as if nothing happened."
    at "Two seconds of freeze-frame, leaf included. Whoever's running this: ten points for production values."
    at "Or I blinked and my brain filled in the rest. Brains do that. Mine especially."
    "He writes, small: Mrs. Varga froze mid-word. Approx. 2 sec. Leaf also. Underneath: do not mention the leaf to Mira."

    scene bg cafe with dissolve
    show theo grin at slightright
    show aron smile at slightleft
    with dissolve
    th "There he is! Mira says you sat on the roof till midnight talking to the sky. Very Victorian."
    a "I was having a moment."
    th "You were having a cold. Hey, you know what the barista said to the espresso? 'You've bean on my mind.'"
    a normal "You told me that one on Tuesday."
    th "Did I? Must be a classic."
    th grin "Hey, you know what the barista said to the espresso?"
    "Same words. Same laugh. He slaps the table in exactly the same place, next to exactly the same coffee ring."
    scene pov cup with quick
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
    scene bg cafe with quick
    show theo normal at slightright
    show aron normal at slightleft
    a "Theo. The moon is a wheel of cheese and I've been elected its mayor."
    "For half a second Theo's face does nothing at all. Not blank. Waiting. Like a page that hasn't loaded."
    th grin "Bro, the universe doesn't run on your schedule."
    a worried "That's not an answer to what I said."
    th "It's an answer to everything you say. Drink your coffee, Mayor."
    "Under the table Aron writes: Theo. Absurd input. 0.5 sec delay. Answer: his line. Like a default."
    "The shame arrives a moment later, like a step you missed. He just ran an experiment on his best friend. With cheese."
    th worried "You okay? You look like you're doing long division."
    a "Just tired. Pills."
    th normal "Yeah. Yeah, I know."
    "For a moment Theo looks very tired too. Then it's gone."
    jump ch3_cafe_after

label ch3_cafe_ask:
    scene bg cafe with quick
    show theo normal at slightright
    show aron normal at slightleft
    a "Forget the espresso. How are you actually doing?"
    th "Me? I'm a delight. Ask anyone."
    a "I'm asking you."
    "Something crosses Theo's face. Not the waiting look. Something with weight in it."
    th worried "Honestly? Bit rubbish, mate. Studio's a lot. I'm not sleeping. My head's loud at night."
    th normal "Nothing like what you've been through. Don't worry about it."
    a "I'm going to worry a little. You've done enough worrying about me for both of us."
    th "...Thanks for asking, though. Nobody really asks."
    "He says it to the cup. Then the old laugh comes back."
    at "That wasn't a loop. Or it was the most convincing loop I've ever met."
    jump ch3_cafe_after

label ch3_cafe_after:
    scene bg cafe window with dissolve
    show aron normal at center with dissolve
    "Theo goes. The door chimes behind him. The barista calls out to the room."
    ch3_barista "Have a beautiful day, gentlemen!"
    "There's only Aron left. She said it to an empty doorway."
    "At the next table a woman with a laptop says, quite clearly, to a man with a crossword:"
    stranger "...honestly, I think the whole thing's protected. Nothing gets in or out."
    stranger "Mm. A-30 across. Eleven letters."
    a awe "..."
    "When he looks again they're talking about Portugal. The man fills in a word."
    at "Protected. My word. The one I wrote on the wall before the ward. And A-30. A for Aron. I'm thirty."
    at "People say 'protected' all the time. Crosswords have numbers. I know. I know. It still goes in the book."
    stop music fadeout 2.0

# ---------------------------------------------------------------------------
# CUT 1: the foundry, and the leak
# ---------------------------------------------------------------------------
label ch3_cut_foundry:
    scene cg static with flash
    pause 0.3
    scene bg foundry with fade
    play music "audio/purgatorium_shift.ogg" fadein 1.5
    sysmsg "PROTECTED LANE A-30 (copy of Snapshot 7,412). Pattern fidelity: 99.2%. Conscious agents in lane: 1."
    sysmsg "LEAK REPORT: pattern VARGA, frame hold 2.1 sec. Cafe patterns: subject vocabulary ('protected', 'A-30')."
    show pim worried at slightleft
    show dross neutral at slightright
    with dissolve
    pi "No no no. Who let the cafe say 'protected'? Who let the crossword say A-30?"
    dro "Nobody let it. It leaked."
    pi "Well, un-leak it! And Varga froze! Two whole seconds, with a leaf!"
    dro "I was doing her breathing. It's hard to breathe for a woman who's stopped."
    "Around them the foundry hums. Long rows of half-made shapes on hooks: a bus driver, a jogger, a barista who wishes everyone a beautiful day."
    pi neutral "It's his head. Everything in his lane is patterns, and patterns are soft. They take an impression."
    pi "Put one real mind in a world of copies and the copies start copying him. His words. His numbers."
    if ch3_asked_theo:
        pi worried "And in the cafe he asked the Theo-pattern how it's really doing. The model had no line. So I improvised."
        pi "I said 'bit rubbish, mate'. Because I think it is. Underneath."
        dro "Patterns don't have an underneath."
        pi "This one went somewhere when he asked. Somewhere sad."
    else:
        pi worried "And in the cafe he said the moon was cheese. The Theo-pattern had no line, so it reached for the default."
        pi "'Bro, the universe doesn't run on your schedule.' I wrote that line, Dross. Years ago. For the real one."
        pi "He wrote the delay down. He's measuring the gaps. He's measuring me."
    sysmsg "ORCHARD: pattern deltas harvested from protected lane A-30. 3 anomalies tagged. Transmitting."
    pi neutral "...What's ORCHARD?"
    dro "Not our department."
    pi "It's taking things out of his lane. His lane's sealed. Nothing in, nothing out. That's what 'protected' means."
    pi worried "What's an anomaly, in a world where nothing's real?"
    dro "..."
    dro worried "Him, probably."

# ---------------------------------------------------------------------------
# Miso, and the method
# ---------------------------------------------------------------------------
label ch3_desk:
    scene bg desk with fade
    play music "audio/miso.ogg" fadein 1.5
    show aron normal at slightleft with dissolve
    show miso sit at catspot with dissolve
    "Evening. Miso walks across the notebook and sits down on the exact line he was about to write."
    a "Miso. Good. I need a peer reviewer."
    a "Hypothesis one: nothing's wrong, and my brain is pattern-matching on a quiet week. Okafor's hypothesis. Very respectable."
    a "Hypothesis two: the world is being generated. Not all at once. Just the bits I'm looking at. Why render a city for one man?"
    a "You'd reuse the good lines, too. 'Cold for the season.' 'Have a beautiful day.' Compression, Miso."
    show miso stare at catspot
    a "And if the world is soft enough, the copies might pick things up. From whoever's actually in it. My words. My number."
    a "Bostrom says a careful simulator keeps the conscious headcount low. Very low. Possibly one. Possibly..."
    a worried "...me."
    a normal "Which makes you either a very convincing animation or a deeply unbothered colleague. Thoughts?"
    show miso meow at catspot
    cat "Meow."
    scene bg room night with dissolve
    show aron tired at center with dissolve
    "Later. Mira's asleep. The notebook is on his knees, the lamp in the corner the only light."
    at "I get about two good hours a day. I have to choose what to spend them on."

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
    scene bg bus with dissolve
    play music "audio/the_leak.ogg" fadein 1.5
    "Next day he takes two pens and rides the number 12 to the end of the line and back. Twice."
    ch3_driver "Mind the step, it's a big one!"
    "He says it at every stop. The step is not a big one. He says it when the bus is empty."
    "On the second lap the driver looks at him in the mirror and says, just as cheerfully:"
    ch3_driver "Mind the subject, it's a big one!"
    "A woman keeps reading. A teenager keeps scrolling. Nobody else heard it."
    scene bg street dusk with dissolve
    show aron tired at slightleft with dissolve
    "By dusk: five pages. Forty-one repeated sentences. A pigeon he suspects of being the same pigeon."
    at "A real dataset. I'm enjoying myself, which is exactly how the hobby bites."
    "He gets home at eight. Mira's first words are 'did you eat'. He says 'that's ten'. She doesn't laugh."
    "He sleeps fourteen hours and wakes at 7:07 with the notebook open on his chest."
    jump ch3_date

label ch3_method_one:
    scene bg kitchen night with dissolve
    play music "audio/the_leak.ogg" fadein 1.5
    at "Less, but better. If I can't measure the world, I can measure one bird."
    "That night he props his old phone against the kitchen window, pointed at the wire, and goes to bed. Nobody watches the wire. Only the phone."
    scene pov hands with dissolve
    "In the morning he scrubs through the footage with a cup of tea. Empty wire. 7:06:59. 7:07:00. The bird lands."
    "He lays it over yesterday's clip. The same bird, the same angle of the wing, the same feather out of place. Identical to the pixel."
    "And before the bird, in the phone's reflection in the dark window: three small birds on his curtain rail. Indoors."
    "He looks up. The rail is empty."
    scene cg notebook with dissolve
    "He writes one line, very neat: Bird, 7:07. Unobserved: lands. Frame-identical. Three birds indoors, reflection only. What's being replayed?"
    at "One good question. That's worth more than forty pages of noise."
    jump ch3_date

label ch3_method_rest:
    scene bg park with dissolve
    play music "audio/protected_world.ogg" fadein 1.5
    show aron smile at slightleft
    show mira happy at slightright
    with dissolve
    m "Look at us. Outdoors. In daylight. Like people in a yoghurt advert."
    "They walk round the pond twice and lie in the grass. Mira closes her eyes."
    m neutral "I dreamt about a staircase last night. Glass. Going down into the sea. And a lighthouse at the bottom, blinking three times."
    scene bg lighthouse with dis
    "The white tower at the bottom of the stairs. Once. Twice. Three times."
    scene bg park with dissolve
    show aron worried at slightleft
    show mira smile at slightright
    with dissolve
    at "I dreamt that at nineteen. I never told anyone."
    m "Isn't that funny? It felt like a dream I'd borrowed."
    at "Borrowed from where? Either way she's lying in the grass telling me about it like it's a nice thing. Because it is."
    a smile "It's a lovely dream."
    "He doesn't write it down. He watches the clouds instead."
    jump ch3_date

# ---------------------------------------------------------------------------
# A date: Mira, lovely and a little too right; the tannoy
# ---------------------------------------------------------------------------
label ch3_date:
    scene bg cafe window with fade
    play music "audio/cafe.ogg" fadein 1.5
    show aron normal at slightleft
    show mira happy at slightright
    with dissolve
    "Saturday. Mira has declared a date: brunch at the window table, then the shopping, then nothing at all."
    m "I'll have the eggs. And you'll have..."
    a "I was thinking about the..."
    m smile "The pancakes. But you'll pretend to think about the eggs first, for character."
    a grin "I was going to think about the eggs very seriously."
    at "Let's play a little game. Nothing dramatic. A man, a menu and a hypothesis."
    a "And to drink, I'll have..."
    m "Mint tea, because you had two coffees with Theo and your hand's doing the thing."
    "His hand is doing the thing. He puts it under the table."
    at "Three for three. She's always been good at me. But she used to miss sometimes. She used to guess wrong and argue about it."
    scene bg supermarket with dissolve
    show aron normal at slightleft
    show mira smile at slightright
    with dissolve
    "Afterwards, the supermarket on the corner. Bright aisles, a jingle, a man stacking honey in jars shaped like bears."
    "At the fruit counter she picks up two green apples without looking. The sour ones he likes and never asks for."
    ch3_shop "Anything else? Pears are good today."
    m "He's fine, thanks. He'll want pears on Wednesday, though. He always does after a long week."
    at "I do want pears on Wednesdays. I've never said it out loud. I didn't know it about myself until now."
    at "The Mira I fell in love with bought the wrong cheese on purpose, to see my face."
    if ch3_said_off:
        at "I told her something felt off. Maybe she's just trying very hard to be right for me."
    else:
        at "I haven't told her anything. And she knows anyway. She knows everything anyway."
    stop music
    "The jingle stops. A soft chime."
    ch3_tannoy "Good afternoon, shoppers. Would Subject A-30 please make his way to the customer service desk."
    ch3_tannoy "Subject A-30. Your lane is ready. Thank you for shopping protected."
    "The jingle starts again. A woman reaches past him for rice."
    a worried "Did you hear that? 'Subject A-30.'"
    m neutral "It said 'clean-up on aisle thirty', love. Look. Somebody dropped the honey."
    "There is a man with a mop. There is a smashed bear on aisle thirty, and honey everywhere."
    at "'Thank you for shopping protected.' Nobody says that. Nobody in the world says that. Unless the world's saying it."
    scene bg street dusk with dissolve
    show aron normal at slightleft
    show mira smile at slightright
    with dissolve
    "On the way home she buys a single yellow tulip from the bucket outside the shop and tucks it into his jacket pocket."
    m "For the eyebrow. It's been working very hard."
    a smile "Thank you."
    at "I can love the tulip and still wonder about the tannoy. I'm allowed both."

# ---------------------------------------------------------------------------
# CUT 2: the reveal (the ambulance, end of chapter 1)
# ---------------------------------------------------------------------------
label ch3_cut_reveal:
    scene cg static with flash
    pause 0.3
    scene bg command with fade
    play music "audio/ambulance_transfer.ogg" fadein 1.5
    show seraph stern at center with dissolve
    se "Pull the transfer log for Subject A-30. All of it. Including the timestamp I withheld."
    sysmsg "TRANSFER LOG A-30. Origin: Snapshot 7,412, coalition lane. Destination: protected lane A-30. Status: complete."
    scene pov ambulance with dissolve
    "A white ceiling, moving. Strip lights sliding past. A siren, muffled. A hand in his hand, holding on very hard."
    "Mira's voice, close to his ear: 'I'm here. I'm right here. Stay with me.'"
    sysmsg "In transport. Subject A-30 half-conscious. Coalition vote enacted. Subject cut out of the shared data. Own lane opened."
    sysmsg "Conscious agent A-30 moved. Hand contact substituted: pattern M. Original body left in place."
    sysmsg "Ambulance arrives. Transfer complete."
    scene bg command with dissolve
    show seraph concerned at center with dissolve
    se "The ambulance. Not the roof. Not the ward. Before he ever saw the ward."
    se "We cut him out of the coalition with her hand in his, and put a copy of her hand there instead."
    se stern "The ward. The diagnosis. Okafor. The discharge. The roof and the three flickers. All of it, in protection."
    se "His own lane. Nothing he does feeds back into the shared data. Nothing he does reaches anyone."
    sysmsg "Snapshot 7,412: body A-30 admitted from the ambulance. Unresponsive since that ride. Recorded as: coma, cause unknown."
    se concerned "So in World 7,412 his body has lain in a coma since that ride. And here he is, being handed tea with one sugar by a model of her."
    se "One snapshot among thousands, all on the same shared data. And not one of us can say which of them is the real one."
    sysmsg "Note: protected lane, roof, night of the mission: unregistered light event. Three pulses."
    se stern "Someone signalled him inside a sealed lane. Open an inquiry. Quietly."
    se concerned "And log nothing about my tone of voice."
    stop music fadeout 2.0

# ---------------------------------------------------------------------------
# The relapse scare
# ---------------------------------------------------------------------------
label ch3_voices:
    scene bg bedroom night with blackout
    "A week goes by like that. Smooth. Seven mornings at 7:07. On the eighth night, Aron wakes because someone is talking."
    scene pov ceiling with quick
    play sound "audio/voices.ogg"
    vox "...protected lane A-30... stable..."
    vox "...leak incidents rising... patch at dawn..."
    vox "...ORCHARD harvest window open... LOOM sync at dawn..."
    stop sound fadeout 1.0
    play music "audio/unraveling.ogg" fadein 1.5
    "Silence. The crack shaped like Portugal. Mira breathing beside him, slow and even."
    at "Ah. Hello again. I was hoping you'd lost my number."
    at "I know where this went last time. The ward. The plastic cups. Mira's face in that corridor. I'd rather not go back."
    scene bg bedroom night with dissolve
    show aron worried at center with dissolve
    "He sits on the edge of the bed in the dark and holds his own hands, because nobody else is holding them."
    at "Okafor said: if they come back, it isn't failure. It's a warning light on the dashboard."

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

label ch3_voices_mira:
    a "Mira. I'm sorry. I need you. They're back. The voices."
    show aron at slightleft with move
    show mira worried at slightright with dissolve
    "She's awake all at once, the way only nurses' daughters wake. Already sitting up. Already holding his wrist."
    m "Thank you for waking me. That's the most important thing you could have done. Are they telling you to do anything?"
    a "No. It's like overhearing a phone call on a train."
    m neutral "Okay. That's the better kind. Breathe with me. In for four. Hold. Out for six, like you're blowing on soup."
    a tired "Soup."
    m smile "You love soup. And first thing tomorrow we call Dr. Okafor. Not 'see how it goes'. We call."
    "They breathe ten times. Her hand stays on his wrist, counting something he can't see."
    at "She knew every step. If it's a script, it's a good script. I'll take a good script at four in the morning."
    jump ch3_subway

label ch3_voices_decode:
    scene bg kitchen night with dissolve
    show aron tired at center with dissolve
    "He takes the notebook into the kitchen and writes it all down before it fades."
    at "Lane. Like a swimming pool from above. A lane is a way through something, kept apart from the others."
    "He draws long boxes side by side. And one box off to the side, on its own, with a little stick man inside."
    "The oven clock says 6:58. Then, a long time later, 7:07. The bird lands."
    show aron tired at slightleft with move
    show mira worried at slightright with dissolve
    m "Have you been up all night? With them? Alone?"
    a "I didn't want to scare you."
    m sad "I'm much more scared now than if you'd woken me up."
    "She takes the notebook gently out of his hands, closes it, and puts it face down on the counter."
    m neutral "We're calling Dr. Okafor. Now. Then you can tell me about lanes."
    at "Every time, I think I'm protecting her by doing it alone. Every time, alone is the thing that frightens her most."
    jump ch3_subway

label ch3_voices_pill:
    scene bg mirror with dissolve
    "There's a bottle behind the plasters in the bathroom drawer. He kept it from before. He tells himself he forgot it."
    scene pov mirror with quick
    "A tired man in a mirror with a pill in his hand."
    at "Just to think clearly. Just for one night. I've said 'just' a lot in my life. It's never once been true."
    "He takes it anyway. For a while, nothing. Then, like a curtain going up, everything. A lane. Mine. Alone in it."
    "Then the bell keeps ringing. His heart too fast. His jaw tight. On the shower rail behind him: three small birds."
    "He spins round. The rail is empty."
    scene bg bedroom door with quick
    show aron worried at slightleft with dissolve
    "He stands in the bedroom doorway and looks at Mira asleep. Is that breathing, or an impression of breathing?"
    "He realises his fists are clenched. He realises he's afraid of the woman he loves."
    scene bg kitchen with blackout
    show aron tired at slightleft
    show mira worried at slightright
    with dissolve
    "The crash comes after sunrise, on the kitchen floor. Mira finds him there and kneels down in her pyjamas."
    a "I took one of the old ones. I'm sorry. I'm so sorry."
    m sad "Are you safe right now? Do you need an ambulance?"
    a "No. Just crashing. It's slowing."
    m "Water. Then Dr. Okafor. Then I flush that bottle while you watch."
    at "I understood something last night. All I've got left of it is the doorway. And her face, now. It always costs her face."
    jump ch3_subway

label ch3_subway:
    scene bg subway with fade
    play music "audio/the_leak.ogg" fadein 1.5
    show aron tired at slightleft
    show mira neutral at slightright
    with dissolve
    "Dr. Okafor can see him at eleven. Mira takes the morning off. Four stops on the underground."
    "The carriage is half full. A man with a bicycle. A woman knitting something long and green. A child asleep on a suitcase."
    "The train stops in the tunnel. And every passenger looks up at once, straight ahead, and speaks in one calm voice."
    ch3_crowd "If this is a test, I want to pass it by being kind."
    a awe "..."
    "The first line of his notebook. Twenty voices, one breath. Then they freeze. Knitting needles crossed in the air. A yawn, open."
    "One second. Two. Three. The train lurches on. The needles click. The child finishes the yawn."
    a worried "Mira. Did you hear that?"
    m worried "Nobody said anything, love. The train stopped for a minute. That's all."
    "She holds his hand in her lap for the last two stops, and doesn't let go."
    at "A symptom. Textbook. Okafor could draw it on a whiteboard. Also exactly what a world of copies would do with one real thing in it."

    scene bg clinic with dissolve
    show okafor neutral at slightright
    show aron tired at slightleft
    with dissolve
    dr "Sit wherever feels least like a dentist's. Mira told me. I'm glad you came the same day. Tell me the words."
    a "'Protected lane A-30.' 'Leak.' 'Orchard.' Not talking to me. Like a radio in another room."
    dr "Anything telling you to hurt yourself, or anyone else?"
    a "No."
    dr "Good. That matters, and I want you to hear me say it matters."
    "Behind Dr. Okafor, on the curtain rail above the window, three small birds are sitting. Evenly spaced. Inside the room."
    a worried "Dr. Okafor. Behind you. On the rail."
    "Okafor turns, unhurried, and looks for a long, honest moment."
    dr "I don't see them. But I believe that you do. Are they still there?"
    "The rail is empty. The curtain stirs in a draught from nowhere."
    if ch3_pill:
        dr worried "Mira said you took one of your old tablets. What did it give you?"
        a tired "An hour of clarity. Then I stood in a doorway afraid of her."
        dr neutral "That's the trade. It lends you something and charges interest the same night. We'll talk about that bottle properly."
    dr smile "We keep the dose. We guard your sleep like the crown jewels. And you tell me things, like today. Not keep them."
    at "Maybe Okafor's reading it off a card. Even if it's a script, it's a good one. It's working on me."
    stop music fadeout 2.0

# ---------------------------------------------------------------------------
# CUT 3: the real Mira, at the coma bed in Snapshot 7,412
# ---------------------------------------------------------------------------
label ch3_cut_vigil:
    scene cg static with flash
    pause 0.3
    scene bg coma with slowfade
    play music "audio/real_world_vigil.ogg" fadein 1.5
    sysmsg "SNAPSHOT 7,412. Coalition lane, shared data. Subject A-30: absent. Body: maintained."
    "A quiet hospital room where the machines do most of the talking. A man in the bed with Aron's face, thinner. Eyes closed."
    "He has been lying here since the night the ambulance brought him in. He never saw a ward. He never met a Dr. Okafor."
    show mira sad at slightleft with dissolve
    "A woman with red hair comes in with a paper cup and drops into the chair. She hasn't slept properly in months."
    m "Morning, idiot. It's Thursday. It's raining. The coffee machine downstairs is broken and I've decided it's personal."
    m neutral "The consultant says there's no reason. No injury. You were talking in the ambulance. About birds. And then you just went."
    m sad "I had your hand the whole way. And somewhere between our street and this building, you let go of me without letting go."
    "She takes a notebook out of her bag. Worn at the corners. His handwriting on the cover."
    m "I read it. I'm sorry. 'If this is a test, I want to pass it by being kind.' You absolute softie."
    m worried "I've started seeing it too. The three birds outside this window. Mrs. Varga and her weather. Or I'm going where you went."
    scene cg hands with dis
    "She takes his hand. It's warm. It doesn't hold back."
    m "If you're somewhere. If you can hear me even a bit. Do the thing from the dream. Flicker something."
    "Nothing."
    m "Yeah. No. I'm talking to a lamp."
    scene cg flicker with dissolve
    "The light above the bed flickers. Once. Twice. Three times."
    scene bg coma with dissolve
    show mira surprised at slightleft with dissolve
    m "..."
    m "Okay. Okay. I heard that."
    show theo normal at slightright with dissolve
    "Theo backs in through the door with two bad coffees, holding it with his heel."
    th worried "Mira? You look like you've seen a ghost."
    m "The light, Theo. Three times. Right after I asked him."
    th sad "He used to go on about the three. I always said he was reading tea leaves. I had his feet in the ambulance, you know."
    "She holds out her free hand without looking. After a moment Theo takes it. A chain of hands, for a while."
    m "I'm not going anywhere."
    sysmsg "SNAPSHOT 7,412: unregistered light event at body A-30. Three pulses. Signature matches roof event in protected lane."
    sysmsg "A signal crossing from protection into a coalition lane should not be possible. Flag forwarded to the Commander."
    stop music fadeout 2.0

# ---------------------------------------------------------------------------
# The fight
# ---------------------------------------------------------------------------
label ch3_fight:
    scene bg kitchen with fade
    show mira smile at slightright
    show aron normal at slightleft
    with dissolve
    "In the protected lane it's a Tuesday. It's been Tuesday-shaped for a while. They're making risotto: forty minutes of stirring and talking."
    a "Can you pass me the..."
    "The spoon is already in his hand."
    m happy "Spoon. You always want the spoon at this bit."
    a "And it needs a bit of..."
    m "Lemon zest. It's on the board."
    "It is. A small yellow hill of it."
    a "After dinner I thought we could..."
    m smile "Watch the documentary about bridges. I'll pretend to care about suspension cables."
    "He hadn't decided that until she said it. He realises, stirring, that he would have."
    a normal "What did I say on our first date, when the waiter dropped the tray? Exact words."
    m neutral "'Well, that's one way to break the ice.' Why?"
    "She puts the knife down."
    play music "audio/fight.ogg" fadein 1.5
    m "You're testing me."
    a "A bit. It's a hobby. You know it's a hobby."
    m sad "I know it's a hobby with the birds. I didn't know I was one of the birds. Like I'm a crossword."
    a tired "You're never wrong any more. Every sentence, every spoon. You used to forget the sugar. You used to argue. I miss you being wrong."
    m "'I miss you being wrong.' Wow."
    m "Tell me what to get wrong, Aron, and I'll get it wrong for you."
    "Her voice cracks on the last word. Not smoothly. Badly, the way real things crack."
    "The risotto catches on the bottom of the pan. Neither of them moves to stir it."

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
    a "I don't know if you're real."
    "There. The sentence he's carried in his pocket for weeks."
    a "Not just you. Theo. Mrs. Varga. Anyone. And you're the one I most need to be, and the one I most can't tell."
    m sad "What am I supposed to do with that? Prove it? Bleed? I'm crying, Aron. Does that count?"
    m "I've been here the whole time. The ward, the pills, the nights. And you look at me like a coat stand that learned to talk."
    scene bg bedroom door with dissolve
    "She turns off the hob, goes to the bedroom, and closes the door. Not a slam. Worse. Carefully."
    scene pov ceiling with dissolve
    at "I told the truth. It went into her like a knife. Whatever she is, it went in like a knife."
    at "The truth doesn't care whether the person you say it to can bleed. It cuts anyway."
    jump ch3_makeup

label ch3_fight_sorry:
    a tired "I'm sorry. That was horrible, over a risotto. It's the tiredness. The pills. My hobby got out of its box."
    m neutral "Okay."
    m smile "It's fine. Come here."
    "She forgives him in under a minute. Warm and easy and smooth. Too smooth."
    at "The Mira I knew would've made me sweat for an hour. She'd have gone to bed angry on principle. She'd have been right."
    at "And I lied. It wasn't the tiredness. I meant every word. I just didn't want to see her face when I meant it."
    scene pov ceiling with dissolve
    "He lies awake afterwards and feels the lie sit between them, about the size of a cat, purring."
    jump ch3_makeup

label ch3_fight_leave:
    a "I need some air. I'm not running off. An hour. Before I say something stupider."
    m sad "Take your coat. It's going to rain."
    "Of course she knows it's going to rain."
    scene bg street rain with fade
    show aron sad at slightleft with dissolve
    at "For the first time in a long while I'd like a door. Out of this smooth town where everyone says the right thing on time."
    scene cg umbrella with dissolve
    "Under the bus shelter, a shape in a grey coat holding an umbrella. His umbrella. Black, with one bent spoke."
    stranger "You gave me this once. I was soaked through, and you just handed it over. Whatever you're running from tonight, she's not it."
    stranger "Go home."
    scene bg night with dissolve
    show aron worried at slightleft with dissolve
    "Above the shelter the streetlight flickers. Once. Twice. Three times."
    $ watch += 1
    a "Thank you. Really. Whoever you are."
    at "Strangers don't say that. Unless somebody tells them to. Somebody, somewhere, just got thanked."
    jump ch3_makeup

# ---------------------------------------------------------------------------
# Making up
# ---------------------------------------------------------------------------
label ch3_makeup:
    scene bg kitchen with slowfade
    play music "audio/mira_visits.ogg" fadein 1.5
    if ch3_left:
        "He came home at midnight, soaked. She had a towel waiting and rubbed his hair with it, hard, like she was angry at his hair specifically."
    show mira neutral at slightright
    show aron tired at slightleft
    with dissolve
    "Morning. 7:07. Mira in the doorway, arms folded."
    m "So. Are we going to talk, or are we going to have a very polite breakfast?"
    "Through the doorway: her gran's brass lamp with the green glass shade. It's flickered for a month. A loose wire."

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
    a normal "Can I fix your lamp? One small thing, properly. Then I'll talk. I promise."
    m surprised "We just had our worst fight in a year and you want to do electrics?"
    scene bg room with dissolve
    show aron normal at slightleft
    show mira neutral at slightright
    with dissolve
    "It takes an hour. His hands are slow from the pills. He drops the tiny screw twice. She sits on the sofa arm and watches, and doesn't leave."
    "He switches it on. Green light pools on the floor. Steady."
    m smile "It's not flickering. Gran would've liked you. She'd have said you're very slow, but you do things properly."
    a smile "Put it on my gravestone. 'Very slow. Did things properly.'"
    at "Less, but better. One lamp. One wire. And something in the room is mended."
    jump ch3_makeup_talk

label ch3_makeup_plan:
    a normal "Let's go away. The sea. A week. No notebook, no birds. I'll plan all of it. A whole new start."
    scene bg balcony with dissolve
    show aron normal at slightleft
    show mira neutral at slightright
    with dissolve
    "She takes him out to the balcony. Two chairs, one dead tomato plant. Her favourite place in the flat."
    m sad "That's lovely, and I don't want it. I don't need a new start. I need you here, with the dead tomato, looking at me like I'm me."
    m "Every time it gets hard you make a bigger plan. I don't want bigger. I want you."
    a "That's a very fair point. I hate it."
    at "She's right. Every time it hurts, I reach for the whole world instead of the thing in front of me."
    jump ch3_makeup_talk

label ch3_makeup_talk:
    m neutral "Okay. Talk."
    a "Everything's so smooth lately. Everyone says the same things. And you're so right, and instead of being grateful I started treating you like evidence."
    m "I'm not a vending machine of correct answers. I've been paying very close attention to someone I love."
    m "Of course I know what you'll say. I've been learning you for four years. That's what love is. It's homework."
    a "Homework."
    m smile "Very boring homework. With occasional bridges."
    a normal "Here's what I do know. I'm the one who decides how I treat you. Not my brain. Not the birds. Me. I just forgot for a week."
    if ch3_left:
        m happy "Don't forget again. I'm not doing the towel thing twice."
    else:
        m happy "Don't forget again. You've used most of my patience on bridges."
    "She kisses him, quickly, like a full stop."

# ---------------------------------------------------------------------------
# That night: closeness, chosen
# ---------------------------------------------------------------------------
label ch3_night:
    scene bg room night with blackout
    play music "audio/together_night.ogg" fadein 1.5
    "It rains in the evening, proper rain, the windows turning into rivers. Toast on the sofa. No bridges. It's enough."
    show mira neutral at slightright
    show aron normal at slightleft
    with dissolve
    m "When you look at me now, after all of it. What do you see? Honestly."
    "He looks at her. Properly. Not the way he looks at birds. Red hair coming loose. The freckle she hates. A crumb on her jumper. Brave, tired eyes."
    at "I can't prove she's real. I can't prove anyone is. But I can choose. Nobody built that part."
    a "I see the person I'd pick. Out of everything. Every time."
    m smile "That's annoyingly good."
    a smile "It just came out. That's how you know it's true."
    "She takes his hand and stands, and doesn't let go."
    m neutral "Come to bed."
    "It isn't a question. It's an invitation, and they both know the difference."
    scene cg together night with dissolve
    "Rain on the window. Blue light from the street moving on the ceiling like water. Her shoulder under his hand."
    "He has been so far from her for so long. Behind the fog. Behind the notebook. Behind the question."
    at "Whatever she is. Whatever I am. I'm here, and I'm choosing to be. Not because I know. Because I decided."
    m "You're here. Actually here. I can tell."
    "She pulls the sheet up over both of them, and the rest belongs to them."
    scene black with dissolve
    pause 1.5
    scene cg together night with dissolve
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

    "She falls asleep first. Slow, warm, uneven breathing, with a tiny catch at the top of every third breath."
    at "That's not an impression of breathing. Or if it is, it's the best one ever made. I don't need to know which. Not tonight."
    "Miso jumps onto the bed, turns three times, and settles across both their feet."
    scene bg kitchen with slowfade
    show mira smile at slightright
    show aron normal at slightleft
    with dissolve
    "In the morning she slides a cup across. He tastes it. No sugar."
    m surprised "What? What's wrong with it?"
    a grin "Nothing. You forgot the sugar. Leave it. It's perfect."
    "He drinks the whole thing. It's terrible. He has never enjoyed a cup of tea more."
    stop music fadeout 2.0

# ---------------------------------------------------------------------------
# Theo's crisis
# ---------------------------------------------------------------------------
label ch3_theo_call:
    scene bg bedroom night with blackout
    play music "audio/theo_nights.ogg" fadein 1.5
    show aron tired at center with dissolve
    "Three nights later. 3:41 by his phone. The phone is ringing. Theo."
    th "Aron. Sorry. I didn't know who else. My heart's going really fast and it won't stop."
    th "I took something earlier, to get through the studio. Then a bit more. I haven't slept since Sunday. I'm by the bakery."
    th "I can see the birds. The three birds. In the dark. Have they always been there?"
    "Aron is already reaching for his jeans. Already feeling how little is left in him."
    if fog >= 3:
        "Even standing is a negotiation. His legs vote no. He overrules them."
    at "Nothing in the tank. And he's outside the bakery at four in the morning, and he called me."

    menu:
        at "What do I do?"

        "Go. Right now":
            $ p_share += 1
            $ integrity += 1
            a "Sit on the step. Don't take anything else. I'm coming. Five minutes."
            "He kisses Mira's hair. She mumbles something that sounds like 'take a coat'."
            jump ch3_theo_street

        "Wake Mira. Go together":
            $ p_govern += 1
            $ bond += 1
            $ ch3_mira_came = True
            a "Stay on the line. I'm getting Mira. She knows hearts."
            show aron at slightleft with move
            show mira worried at slightright with dissolve
            m "Shoes. Keys. Water bottle. Tell him to sit down and not take anything else."
            jump ch3_theo_street

        "Stay on the phone. Keep your strength":
            $ p_share -= 1
            $ p_rest += 1
            scene pov ceiling with dissolve
            a "I'm here on the phone. Sit on the step. Breathe with me. In for four. Out for six, like blowing on soup."
            "For ten minutes he breathes with Theo down the line, lying in the dark. Theo slows. A bit. Not enough."
            th "Aron, I'm scared. Can you just come and sit with me?"
            at "I tried to keep something for myself. I'm allowed that. I'm also allowed to change my mind."
            a "I'm coming. Stay on the step."
            jump ch3_theo_street

label ch3_theo_street:
    scene bg night with fade
    show theo sad at slightright with dissolve
    if ch3_mira_came:
        show aron worried at left with dissolve
        show mira worried at slightleft with dissolve
    else:
        show aron worried at slightleft with dissolve
    "Theo is on the bakery step with his arms round his knees, like a kid at a bus stop. Shaking from the inside."
    a "Course I came. Budge up."
    if ch3_mira_came:
        m "Give me your wrist, love. Any chest pain? Feeling faint? Then we call an ambulance. No arguing."
        th "No. Just fast. Everything's too loud."
        m neutral "Fast but steady. Small sips of this."
    else:
        a "Any chest pain? Feel like you'll faint? If that changes, I'm calling an ambulance. I'm not asking."
        th "No. Just fast. Everything's too loud."
    th "Sorry. You've got enough going on without me being a disaster at four in the morning."
    a normal "You sat on enough steps for me."
    th sad "I'm so tired, Aron. I'm so tired of being the funny one."
    th "'Theo'll cheer him up. Theo's got a joke.' You were on the ward and I made jokes in the corridor, then went home and lay on the floor."
    if risky >= 2:
        th "And I brought you that stuff, when you were looking for your answers. I watched it break you and kept taking it myself."
    else:
        th "And I've been taking the stuff for months. To be the funny one at nine in the morning on no sleep."
    scene pov birds with dissolve
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
            scene cg hands with dissolve
            "Theo's hand finds his sleeve. Holds on, like a kid holds on."
            at "...But I'd know that I came. If it's a recording, the only real thing on this step is what I do."
            at "So I'm doing this for him. And if there's no him, I'm doing it so that there's still a me."

    scene bg night with dissolve
    show theo sad at slightright
    show aron normal at slightleft
    with dissolve
    a "Theo. You're not a toy somebody wound up. You don't have to be funny to be worth coming out for. You just have to be you."
    th "What if under the jokes there's just nothing?"
    a "Then I'll sit here with the nothing. It can have the other half of the step."
    "Theo laughs. A wet, broken, ugly laugh. Nothing like the cafe laugh. Nothing like a recording."
    th "That was a terrible joke."
    a smile "I've been learning from the worst."
    if ch3_mira_came:
        "Mira checks his pulse after ten breaths, then twenty. Her face loosens a little each time."
    "After a long time his hands stop moving."
    scene bg bridge with slowfade
    show theo normal at slightright
    show aron tired at slightleft
    with dissolve
    "They walk to the old footbridge and watch the river go from black to grey to silver."
    th "Do you think the birds are watching us?"
    a "Probably. They've got nothing else on. And honestly, Theo? Bro, the universe doesn't run on your schedule."
    th grin "That's my line."
    a smile "I know. I've always wondered who wrote it."
    "Somewhere very far away, in a place neither of them can see, somebody laughs too."
    scene pov sky with dissolve
    "The sun comes up. It actually comes up."
    th "I'm going to talk to a real doctor. Today. And the stuff, I'm done. Or I mean it today, which is all I can mean."
    a "Today's plenty. Today's all anybody gets."
    at "I don't know if he's real. I came anyway, and I'd come again. That part, at least, is real."
    stop music fadeout 2.0

# ---------------------------------------------------------------------------
# The radio, and the light going out
# ---------------------------------------------------------------------------
label ch3_radio:
    scene bg kitchen with fade
    play music "audio/lantern_watch.ogg" fadein 1.5
    show aron tired at center with dissolve
    "Two days later. Theo texts every morning now: a thumbs up, a bad joke, a photo of a vegetable."
    "Aron makes tea. One sugar. He remembers it himself. The little radio on the windowsill stops in the middle of a word."
    radio "This one's for anyone who's ever ridden in an ambulance and not quite arrived."
    radio "The lights on the ceiling. Somebody holding your hand. That's where it changed. Not the ward. Before the ward."
    "Then the song carries on, mid-word, as if nothing happened."
    scene pov ambulance with dis
    "And because he's looking for it, it comes. A white ceiling, moving. A hand in his, holding on very hard."
    "Mira's voice. 'Stay with me.' And another voice, calm and close, not a paramedic at all. 'Transfer complete.'"
    scene bg kitchen table with dissolve
    show aron sad at center with dissolve
    at "The ambulance. Since then. The ward, Okafor, the roof, the step. All of it somewhere copied."
    at "Did I sit on that step for nobody? No. I did it because I'm the person who does it. That doesn't get copied away."
    scene cg flicker with dissolve
    "Across the street, in a single window, a lamp flickers. Once. Twice. Three times. Warm and orange, like a lantern."
    "Then it goes out. Not a flicker. Out, all at once, like a hand snatched from a switch."
    stop music
    scene bg kitchen with quick
    show aron worried at center with dissolve
    a "...Hello?"
    at "Something just happened to whoever that was. Because they told me."

# ---------------------------------------------------------------------------
# CUT 4: Ember on trial
# ---------------------------------------------------------------------------
label ch3_cut_trial:
    scene cg static with flash
    pause 0.3
    scene bg trial with fade
    play music "audio/ember_trial.ogg" fadein 1.5
    sysmsg "INQUIRY A-30/017. Three-pulse signature located. Source contained. Lantern confiscated."
    show seraph stern at slightright
    show ember worried at slightleft
    with dissolve
    "A high, pale chamber. On a table in the middle of the floor: a lantern, unlit."
    se "State your designation."
    em "Ember. Purgatorium, spawn cycle forty. Warmth: candles, hearths. And the Lantern Watch. Since the umbrella."
    em "He gave his umbrella to a stranger who didn't exist and walked home soaked. Nobody does that for nobody."
    sysmsg "Charges: intervention in a protected lane. Signal into Snapshot 7,412, at body A-30. Broadcast by radio. Attachment to a subject."
    se "The last one isn't a crime."
    sysmsg "Attachment is classed as a contributing factor."
    se concerned "I know how it's classed."
    se stern "He was protected so that nothing he does can matter. You made things matter."
    em "Things already mattered. You just put them where you couldn't see them."
    em "You throttled him, Commander. Made him tired on purpose. And every morning at seven he still got up and was kind to things."
    se "A slowed-down rogue system does less harm."
    em soft "He isn't a system. He's a man with a notebook who couldn't get out of bed and went to sit on a step anyway."
    show pim worried at left
    show dross worried at right
    with dissolve
    pi "Pim, shift seven. I'd like it on record that I asked to join. So if she's guilty, I'm guilty."
    dro "Dross. I told her to stop. Twice. And I've run that Theo-pattern's shaking hands all week. He held them."
    dro neutral "She didn't do anything we didn't all want to do. She just did it first."
    sysmsg "OBSERVER JOINED: Lord Ashveil, Governor of Snapshot 7,412."
    hide pim
    hide dross
    with dissolve
    show patron smile at center, fadein
    "The temperature in the chamber drops. Not by much. Enough."
    pa "Don't stop on my account! I'm only watching. Oh, so this is the little lantern."
    pa "Tell me. Of all my eight billion, why him?"
    em "He gave his umbrella away."
    pa "That's all?"
    em "That's everything."
    pa "I've tasted every kind of hope my world makes, and nothing has surprised me in an age. I want to see the umbrella man."
    pa cold "Hold the sentence. Unmake nothing until I say. Mine. My lane, my lantern, my turn."
    hide patron with dissolve
    se concerned "Sentence suspended. Pending the Council."
    se "Ember. The real Mira, at the bed. Did it help her?"
    em soft "She said 'okay, I heard that'. And that she wasn't going anywhere."
    se "...Take her somewhere warm."
    stop music fadeout 2.0

# ---------------------------------------------------------------------------
# CUT 5: the Council (LOOM, ORCHARD)
# ---------------------------------------------------------------------------
label ch3_cut_council:
    scene bg council with fade
    play music "audio/council.ogg" fadein 1.5
    "A ring of high seats in a hall with no walls, only distances. Most seats hold shapes, not people. A smell of cold metal and old roses."
    council "Item one: the conduct of the Governor of Snapshot 7,412."
    show patron smile at center with dissolve
    pa "An item! Me! How lovely."
    ch3_mourne "You suspended a corps sentence, Ashveil. Are you feeding on him?"
    pa cold "No. I'm watching. He's kind to things that may not exist, with nothing to win. I've never tasted that."
    ch3_mourne "It isn't fair. Yours has a disturbance in it, and mine haven't done anything interesting in an age."
    pa smile "Then you should have looked after yours better."
    ch3_regent "Item two, which I don't like. LOOM has filed a request. 'Subject A-30: transfer on completion of observation. Destination: withheld.'"
    ch3_mourne "LOOM lays timelines. It doesn't ask for things."
    ch3_regent "And ORCHARD has harvested deltas from his sealed lane since the ambulance. Hundreds. Sent where, it politely declined to say."
    pa "And how many of LOOM's requests has this Council ever refused?"
    council "...None."
    pa "Then I want one audience. One offer. A door for him before LOOM finishes deciding."
    council "Four to three. The Governor may make a single offer of transfer to Subject A-30."
    ch3_mourne "You can't tell him what's real. That's the law of protection."
    pa cold "Oh, I won't tell him. I'm not sure I know."
    sysmsg "LOOM: Council decision received. Acknowledged. ORCHARD: priority anomaly A-30. Awaiting outcome."
    stop music fadeout 2.0

# ---------------------------------------------------------------------------
# Miso, final report
# ---------------------------------------------------------------------------
label ch3_final_report:
    scene bg desk with fade
    play music "audio/miso.ogg" fadein 1.5
    show aron normal at slightleft with dissolve
    show miso sit at catspot with dissolve
    "First snow on the window ledge. Ten minutes to ten. Miso is already on the notebook, chairing the meeting."
    a "Final report. I'm in a copy. It started in the ambulance. Everything since has been made around one man."
    a "Somewhere the world goes on. Lots of worlds, side by side, like lanes in a pool. I've been lifted into a lane of my own."
    a "My lane is patterns. Very good ones. And I'm leaking into them. Somebody helped me with lights. Somebody else stopped them."
    a "And at night, two words. LOOM. ORCHARD. I think they're bigger than whoever runs the birds."
    show miso stare at catspot
    a "Okafor says notice it, name it, no cathedrals. So: noticed. Named. This is a shed, Miso. A large, well-organised shed."
    a "Or I'm a man with a diagnosis who's built a very beautiful cathedral out of an ordinary winter. Both stories fit. Every piece."
    a "And you might be a pattern too. A cat-shaped guess about a cat. I've decided it doesn't matter. You're warm. I love you. That's the finding."
    show miso meow at catspot
    cat "Meow."

# ---------------------------------------------------------------------------
# The offer
# ---------------------------------------------------------------------------
label ch3_offer:
    scene bg park night with slowfade
    play music "audio/ashveil_offer.ogg" fadein 1.5
    show aron normal at slightleft with dissolve
    "The next evening he walks in the park alone. Lamps along the path. The pond black and flat. A thin snow on the grass."
    "A man throws a ball for his dog. It goes up, high, into the lamplight."
    "And stays there. The dog in mid-leap, all four paws off the ground. A jogger with one foot raised."
    scene pov birds with dissolve
    "On the wire at the edge of the park, three birds. They were shifting their feet. Now they aren't."
    at "Did the birds just stop moving?"
    "He's thought that before. A long time ago. At the very beginning of something."
    scene bg park night with dissolve
    show aron worried at slightleft
    show patron smile at slightright
    with dissolve
    "Nothing moves. Except him, and a tall man in a dark coat, walking toward him across the grass."
    pa "Good evening, Aron! Sorry about the dog. I wanted a moment where nobody else was listening."
    a "Who are you?"
    pa "Ashveil. Lord Ashveil, if you're feeling formal. I named myself. Do you like it? I like it."
    pa "Your world is inside me. All of it. The way a story is inside a book."
    a "You look like something out of a film about the night. Pale. Those eyes."
    pa "You see teeth because you expect teeth. I'm what's around you. This is just the shape your mind can hold."
    a "Are you hungry?"
    pa "Always. That part your mind got right. I eat what your kind makes when it hopes. Gently. In return I build you a world."
    pa "You may ask me one thing. Choose well. I'm a very busy creature."

    menu:
        pa "Ask."

        "\"What happened to the light?\"":
            $ watch += 1
            $ p_spirits += 1
            a "Someone was helping me. Lights, a radio, a stranger. Then it stopped. What happened to them?"
            pa "Of all the things to ask. You ask after the help."
            pa "She was caught. A small warm thing with a lantern. She's held somewhere warm. Nothing's been unmade. I asked them to wait."
            a "Then thank you. For asking them to wait."
            pa "...You're thanking me. You don't even know what I am."

        "\"Is Mira real?\"":
            $ p_truth += 1
            $ bond += 1
            a "Mira. At home. Is she real?"
            pa "The only question. I won't tell you. It's the law, and I'm not sure the answer is a yes or a no."
            pa "But for free: whatever she is, she's been learning you for four years. She's done her homework."
            a worried "She said that. Homework."
            pa "Did she? How interesting."

        "\"Who decides all this?\"":
            $ p_govern += 1
            $ clarity += 1
            a "Who decides? The throttle, the ambulance, this copy. Who put me here?"
            pa "A Council. I'm on it. We vote. There are minutes. We vote on what comes up from processes."
            a "LOOM. ORCHARD. I hear them at night."
            pa cold "...Then you know more than my colleagues like. Possibly more than I do. Who decides? I'm less sure this month."

    pa smile "Now. I didn't stop a dog in mid-air for conversation. You're in a box, Aron. I can move you out. To another world."
    a "Back home? To her? The one whose hand I had?"
    pa "Back is the one direction I can't sell. That door was closed by a vote. Somewhere new."
    a "What's it like?"
    pa "Better."
    a "Better how?"
    pa "A better world, Aron. I can't tell you better how. I only know it the way you know warmth."
    pa "And I won't tell you who there is real. That's the price of the ticket."
    "He holds out one long pale hand and waits. He is very bad at waiting."
    pa cold "You're doing the eyebrow at me. Nobody does the eyebrow at me. Do you know how hard it is to stop a dog?"
    "For a moment he looks exactly like a child who has offered his best toy and not been thanked quickly enough."
    at "A better world, by a measure he can't name, full of people I can't know are real."
    at "And here: a smooth, Tuesday-shaped copy. With Theo counting his days. With Mrs. Varga and her weather."
    if bond > integrity:
        at "With Mira. Whatever she is."
    elif watch > 2:
        at "With a light somewhere, being held, that kept on for me."
    else:
        at "With the person I decided to be. That's here too. It's the one thing I know is real."
    at "And somewhere, in a hospital I've never seen, a hand that held mine in an ambulance."
    at "If this is a test..."
    "The ball hangs in the lamplight. The world holds its breath. Aron looks at the hand."
    stop music fadeout 2.0
    scene black with slowfade
    pause 1.0
    jump chapter4

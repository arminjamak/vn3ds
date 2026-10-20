# Chapter 3 - "Snapshot", part 1.
# Life in the protected world: smooth mornings, loops, the leak getting
# louder, the machinery of protection, Aron's first careful tests, and the cut
# that reveals when he was moved (the ambulance at the end of chapter 1).
# Continues in ch3_part2.rpy.

# One-off characters for chapter 3.
define ch3_varga = Character("Mrs. Varga", color="#e3c9b0")
define ch3_barista = Character("Barista", color="#e0c39a")
define ch3_mourne = Character("Lady Mourne", color="#c88aff")
define ch3_regent = Character("The Grey Regent", color="#b8b8d0")
define ch3_kid = Character("Kid with a kite", color="#cfe8a0")
define ch3_driver = Character("Bus driver", color="#c0c0c0")
define ch3_stranger = Character("Stranger", color="#cccccc")
define ch3_shop = Character("Shop assistant", color="#d0b890")
define ch3_tannoy = Character("Tannoy", color="#bbbbbb")
define ch3_crowd = Character("Passengers", color="#cccccc")

default ch3_pill = False
default ch3_said_off = False
default ch3_asked_theo = False
default ch3_left = False
default ch3_theo_hour = False
default ch3_mira_came = False
default ch3_told_all = False

label chapter3:
    $ chapter = 3
    scene black with blackout
    centered "Chapter 3\n\nSnapshot"
    pause 1.0

    scene pov ceiling with slowfade
    play music "audio/morning.ogg" fadein 2.0
    "7:07."
    "The Braun clock on the nightstand says it the way it always says it: plainly, without opinion, in that calm grey face."
    at "Bed. My bed. My ceiling, with the crack that looks like Portugal."
    at "The last thing I remember is the roof. The blanket. Her good mug. An orange light on the edge of the city, blinking three times."
    at "And then I slept. Up there, under the sky, like a man with nowhere he'd rather be."
    scene bg bedroom with dissolve
    show aron tired at center with dissolve
    show miso loaf at catspot with dissolve
    "Miso is asleep at the end of the bed, folded into a perfect orange loaf, paws tucked out of sight."
    a "How did I get down from the roof, Miso?"
    "Miso doesn't answer. Miso has never once answered a question before breakfast."
    if fog >= 3:
        "His body is heavy in the usual way, wet sand from the neck down, the way it has been since the ward."
        "But the heaviness is... tidier this morning. As if someone had folded it."
    else:
        "He's tired, the way he's always tired since the ward. But it's a tidier tiredness this morning. As if someone had folded it."
    at "Less, but better. Even my exhaustion has been designed."
    a grin "Dieter Rams would approve. Rams would approve of nothing about my life, but he'd approve of that."
    a normal "..."
    "He sits up. The duvet slides off him in one smooth fold and lands exactly on the floor. Miso doesn't even twitch."
    "Not crumpled. Folded."
    at "Huh."

    scene bg bedroom door with dissolve
    show aron normal at slightleft
    show mira smile at slightright
    with dissolve
    m "You're up. I was about to send a search party. Again."
    a "Morning. Mira, how did I get down from the roof?"
    m happy "I found you at two in the morning, asleep against the chimney, with my good mug in your lap. Empty, thank god."
    m smile "You walked down the stairs like a sleepwalker. You thanked the lamppost on the landing. You called it 'lighthouse'."
    a worried "I said lighthouse?"
    m "Very politely. Then you went straight to bed in your jeans."
    at "Lighthouse. The dream. The glass staircase into the sea, the light at the bottom."
    at "A tidy story. Two o'clock, a mug, a lamppost, a joke with a callback. Everything has been tidy since the ward."
    a normal "Sounds like me."
    m happy "Sounds exactly like you. Come on. Breakfast. And you owe my mug an apology."

    scene bg kitchen with dissolve
    show aron normal at slightleft with dissolve
    "The kitchen is bright. The kettle is already warm."
    "Outside the window the bird drops onto the wire and folds its wings."
    "Aron looks at the clock on the oven."
    "7:07."
    at "That can't be right. I've been awake for at least five minutes."
    at "Unless the minute waited for me."
    show mira neutral at slightright with dissolve
    a worried "Mira, is the oven clock slow?"
    m "It's never slow. You set it last spring with your phone and a stopwatch. You made me watch."
    a normal "Right. I did do that."
    "The coffee machine starts. Aron listens, the way he always does now. A small private game: is the sound right today?"
    "It isn't wrong."
    "It's exactly right. The gurgle, the hiss, the two dry coughs at the end. Exactly right."
    "Like a recording of itself."
    at "Interesting. 'Exactly right' goes in the notebook, under 'suspiciously excellent'."
    scene bg kitchen table with dissolve
    show aron normal at slightleft
    show mira smile at slightright
    with dissolve
    m smile "Tea. One sugar."
    "She slides the cup across."
    scene pov cup with quick
    "He looks down into it. A pale brown circle. A small trembling reflection of the window, and the wire, and the bird."
    "He tastes it. One sugar."
    scene bg kitchen table with quick
    show aron normal at slightleft
    show mira smile at slightright
    a "You remembered the sugar."
    m "I always remember the sugar."
    a grin "You never remember the sugar. That's the only flaw I've ever found in you, and I've been looking for four years."
    m neutral "..."
    m smile "Then today's a good day."
    "She smiles the way she always smiles. The left side first, then the right. Freckles rearranging themselves."
    "It's lovely. It's her."
    at "It's her. Isn't it?"
    if told_mira:
        m "So. How's the mission?"
        "She says it lightly, the way you'd ask about a hobby. Not long ago the same idea made her cry in a hospital corridor."
        a worried "You're... fine with it now?"
        m happy "I've made my peace with it. You're looking for the truth. Somebody should."
        at "That's what I wanted her to say. Word for word, that's what I wanted."
        at "Which is wonderful. And which I'll be writing down later, very quietly, like a spy in a dressing gown."
    else:
        m "You've got your thinking face on. The one with the eyebrow."
        a "I don't have a thinking face."
        m happy "You have three. This is the eyebrow one. It means you've noticed something and you're deciding whether to tell me."
        at "She doesn't know about the mission. I never told her. But she always knows when I'm deciding."
    m smile "So what do you want to do today? You've got a free day. No shift, no appointments."

    menu:
        m "Well?"

        "Tell her something feels off":
            $ p_truth += 1
            $ bond += 1
            $ ch3_said_off = True
            a worried "Honestly? Something feels off. Not wrong, exactly. Smooth. Too smooth."
            a "The coffee machine sounds right. The clock waited for me. You remembered the sugar."
            m neutral "And those are... bad things?"
            a "No. That's what's bad about them."
            m worried "..."
            m smile "I know what you mean. I feel it too, sometimes. Like the world's been ironed."
            at "Ironed. That's exactly the word I'd have used."
            at "She always finds the word. She's always been good with words. That's not evidence of anything."
            a normal "Thanks for not laughing."
            m happy "Oh, I'm laughing. Just on the inside, where it's polite."
            "She kisses his forehead. Her hand is warm."
            at "If she's a copy, she's a very good one. If she's not, I just told the truth to the person I love."
            at "Either way, I'd rather have said it."

        "Keep it to yourself, have breakfast":
            $ p_truth -= 1
            $ integrity += 1
            a normal "Breakfast. Then maybe a walk. Then maybe I'll see if Theo's around."
            m happy "A normal day. Look at you."
            a grin "I contain multitudes. Most of them want toast."
            "He eats. The toast is golden all the way across. Not one burnt corner."
            at "I won't put this on her. Not today. She's carried enough of my weather."
            at "Some truths can wait for a day when she isn't smiling like that."
            "He watches her read the news on her phone. She scrolls with one finger, the way she always does. Hums something under her breath."
            at "It's a nice morning. I'm allowed one nice morning."

    m neutral "Oh, before you go out. The bin needs to go down."
    a normal "On it."
    m smile "And say hello to Mrs. Varga. She asked after you."
    stop music fadeout 2.0

    scene bg street with dissolve
    play music "audio/unease.ogg" fadein 2.0
    "The street is the street. Parked cars, the bakery's striped awning, the tram wire humming."
    scene pov birds with dissolve
    "He looks up. On the long wire over the road, three birds."
    "Evenly spaced. Always the same three."
    at "Hello, lads. Same shift as always?"
    "They don't move. They never move. He used to find it frightening. This morning it's almost a comfort."
    scene bg street with dissolve
    show aron normal at slightleft with dissolve
    "Mrs. Varga is on the front step with her tartan trolley, sweeping, very upright."
    ch3_varga "Cold for the season, isn't it?"
    a "Morning, Mrs. Varga. It is a bit."
    "It's warm. It's been warm all week. She says it every day, in every weather. That isn't new. People have phrases."
    "He takes the bin down. Lid, bag, lid. On the way back up the path, she looks up again."
    ch3_varga "Cold for the season, isn't it?"
    a worried "..."
    a "We just did this. Thirty seconds ago."
    ch3_varga "Did we, dear? Cold for the..."
    "She stops. Mid-word. The broom stops mid-sweep."
    "Her mouth stays open on the 's'. Her eyes don't blink. A leaf that was falling past her shoulder hangs in the air."
    "One second. Two."
    ch3_varga "...season, isn't it?"
    "The leaf lands. The broom moves. She smiles at him as if nothing happened."
    at "Well. That's new."
    at "Two seconds of freeze-frame, leaf included. Whoever's running this, ten points for production values."
    at "Or I blinked, and my brain filled in the rest. Brains do that. Mine especially. Either way, it goes in the book."
    "He takes out his notebook and writes, small: Mrs. Varga. Froze mid-word. Approx. 2 sec. Leaf also stopped."
    "Then, underneath: Do not mention the leaf to Mira at dinner."
    "He walks on, slowly, the way he walks everywhere since the pills. Every step is a decision he has to make twice. He makes it, twice."
    if risky >= 2:
        at "There's a part of me that knows exactly which pocket would make this easier. I'm not listening to that part today."
    stop music fadeout 2.0

    scene bg cafe with dissolve
    play music "audio/morning.ogg" fadein 2.0
    show theo grin at slightright with dissolve
    th "There he is! The man, the myth, the guy who fell asleep on a roof like a pigeon."
    show aron smile at slightleft with dissolve
    a "Mira told you."
    th "Mira told everyone. Mira told the bakery. You're a legend, mate. Roof Man."
    a normal "I was resting my eyes."
    th normal "For four hours. Next to a chimney. Hey, at least you were outside. Fresh air. Very healthy. Very Victorian."
    ch3_barista "Two flat whites, one with oat. Have a beautiful day, gentlemen."
    th grin "She says that to everyone. I've decided she means it only for me."
    a grin "Bold."
    th "Hey, you know what the barista said to the espresso?"
    a normal "..."
    th "'You've bean on my mind.'"
    a "Theo, you told me that one last Tuesday."
    th "Did I? Must be a classic, then."
    th grin "Hey, you know what the barista said to the espresso?"
    a worried "..."
    th "'You've bean on my mind.' Ha!"
    "Theo laughs. Exactly the same laugh. He slaps the table in exactly the same place."
    scene pov cup with quick
    at "There it is. Same joke, same slap. Same coffee ring on the table, in the same spot."
    at "This is either what my illness feels like on a quiet day, or it's something else. Either way it's very good data."
    at "Dr. Okafor would say: notice it, name it, don't build a cathedral on it. Fine. A small shed, then."

    menu:
        at "Time for a quiet little experiment?"

        "Test him. Say something absurd":
            $ clarity += 1
            $ p_spirits -= 1
            jump ch3_cafe_test

        "Just ask how he's really doing":
            $ bond += 1
            $ p_spirits += 1
            $ ch3_asked_theo = True
            jump ch3_cafe_ask

label ch3_cafe_test:
    scene bg cafe with quick
    show theo normal at slightright
    show aron normal at slightleft
    a normal "Theo. The moon is a wheel of cheese and I've been elected its mayor."
    th normal "..."
    "For half a second Theo's face does nothing at all. Not blank, exactly. Waiting. Like a page that hasn't loaded."
    th grin "Bro, the universe doesn't run on your schedule."
    a worried "That's... not an answer to what I said."
    th "Sure it is. It's an answer to everything you say. You've got that face again."
    a "What face?"
    th normal "The face where you're figuring out the world. You've had it since we were twelve."
    th "Drink your coffee. Mayor."
    "He grins. The grin is right. Everything is right. Except that half-second, where nothing was."
    "Aron writes in the notebook under the table: Theo. Absurd input. 0.5 sec delay. Answer: his line."
    at "His line. The one he always says. Like it's the line you reach for when you don't have one."
    at "Like a default."
    "He feels the shame of it a moment later, the way you feel a step you missed."
    at "I just ran an experiment on my best friend. In a cafe. With cheese."
    th worried "You okay? You look like you're doing long division."
    a normal "Just tired. You know. Pills."
    th "Yeah."
    th normal "Yeah, I know."
    "Theo looks down at his cup. For a moment he looks very tired too. Then it's gone."
    jump ch3_cafe_after

label ch3_cafe_ask:
    scene bg cafe with quick
    show theo normal at slightright
    show aron normal at slightleft
    a normal "Theo. Forget the espresso. How are you actually doing?"
    th normal "Me? I'm great. I'm a delight. Ask anyone."
    a "I'm asking you."
    th "..."
    "Something crosses Theo's face. Not the waiting look. Something with weight in it."
    th worried "Honestly? Bit rubbish, mate."
    th "The studio's a lot. Everyone's twenty-three and runs on oat milk and panic. I'm not sleeping great. My head's loud at night."
    th normal "Nothing like what you've been through. Don't worry about it."
    a "I'm going to worry about it a little bit. You've done enough worrying about me for both of us."
    th grin "Look at you, the caring one. The pills are making you soft."
    a smile "The pills are making me horizontal. The soft is all mine."
    th normal "..."
    th "Thanks for asking, though. Nobody really asks."
    "He says it to the cup, not to Aron. Then he laughs, and it's the old laugh again."
    th grin "Right! Enough feelings, they'll charge us extra."
    at "That wasn't a loop. Whatever that was, it wasn't a loop."
    at "Or it was the most convincing loop I've ever met."
    jump ch3_cafe_after

label ch3_cafe_after:
    th normal "Hey. Same time next week? I'll bring new jokes."
    a grin "You'll bring the same jokes."
    th grin "I'll bring the same jokes with new confidence."
    scene bg cafe with dissolve
    show aron normal at center with dissolve
    "Theo goes. Through the window Aron watches him cross the road, hands in pockets. The door chimes. The barista calls out to the room."
    ch3_barista "Have a beautiful day, gentlemen."
    "There's only Aron left at the table. Nobody else is a gentleman."
    at "She said it to an empty doorway."
    "At the next table, a woman with a laptop and a man with a crossword are talking quietly. He doesn't mean to listen."
    "Then the woman says, quite clearly, to the man with the crossword:"
    ch3_stranger "...honestly, I think the whole thing's protected. Nothing gets in or out."
    "And the man says, without looking up:"
    ch3_stranger "Mm. A-30 across. Eleven letters."
    a awe "..."
    "When he looks again they're talking about a holiday in Portugal. The woman laughs. The man fills in a word."
    at "Protected. That's my word. That's the word I wrote on the wall before the ward. The one Mira put in the box."
    at "And A-30. I'm thirty. A for Aron. It's been turning up in my head for a year."
    at "People say 'protected' all the time. Crosswords have numbers. I know. I know."
    "He finishes his coffee. It's perfect. Of course it is."
    stop music fadeout 2.0
    jump ch3_cut_machinery

# ---------------------------------------------------------------------------
# CUT 1: the machinery of protection, and the leak
# ---------------------------------------------------------------------------
label ch3_cut_machinery:
    scene cg static with flash
    pause 0.3
    scene bg foundry with fade
    play music "audio/entities.ogg" fadein 2.0
    sysmsg "PROTECTED LANE A-30 (copy of Snapshot 7,412). Render tick 4,551. Pattern fidelity: 99.2%. Conscious agents in lane: 1."
    sysmsg "LEAK REPORT: 3 incidents today. Pattern VARGA: frame hold 2.1 sec. Café patterns: subject vocabulary ('protected', 'A-30')."
    show pim worried at slightleft with dissolve
    show dross neutral at slightright with dissolve
    pi "No no no no. Who let the café say 'protected'? Who let the crossword say A-30?"
    dro "Nobody let it. It leaked."
    pi "Well, un-leak it!"
    dro "That's not a word."
    pi "It is today! And Varga froze. A whole two seconds. On the step. In front of him. With a leaf!"
    dro "I saw. I was doing her breathing. It's hard to do breathing on a person who's stopped."
    pi "He wrote it down. He wrote 'you are not allowed to panic about a leaf'. I'm panicking about the leaf, Dross."
    "Around them the foundry hums. Long rows of half-formed shapes on hooks and belts, waiting to be someone for a moment."
    "A bus driver. A woman with a pram. A boy with a kite. A barista who wishes everyone a beautiful day."
    sysmsg "Rendering on demand: BARISTA (pattern). Source: Snapshot 7,412, 2,014 shifts. Fidelity 98.7%."
    pi neutral "It's him. It's his head. Everything in this lane is made of patterns, and patterns are... soft. They take an impression."
    pi "Put one real mind in a world made of copies and the copies start copying him. His words. His numbers. His worries."
    dro "His mood gets into the weather. His fear gets into the neighbours. I've seen it before. Once. It didn't end well."
    pi worried "How did it end?"
    dro "Not our department."
    scene bg purgatorium with dissolve
    show pim worried at slightleft
    show dross neutral at slightright
    with dissolve
    "They step out onto the long walkway of the Purgatorium, away from the noise of the belts."
    pi worried "Can I tell you something weird?"
    dro "You will anyway."
    if ch3_asked_theo:
        pi "In the cafe. He asked the Theo-pattern how he's really doing."
        pi "The model didn't have a line for that. Nobody asks Theo that. So it came to me, to improvise."
        pi "And I said, 'Bit rubbish, mate.' Because... I think he is? The pattern is. Rubbish. Underneath."
        dro "Patterns don't have an underneath."
        pi "This one does. It went somewhere when I asked it. It went somewhere sad."
    else:
        pi "In the cafe. He said the moon was cheese and he was its mayor."
        pi "The Theo-pattern froze. Half a second. There wasn't a line for 'moon cheese mayor'."
        pi "So it reached for the default. 'Bro, the universe doesn't run on your schedule.' That's one of mine. I wrote that line."
        dro "You wrote Theo's catchphrase?"
        pi neutral "Years ago. In the snapshot, for the real one. He liked it so much he kept it. Now it's the fallback when the model's stumped."
        pi worried "And Aron wrote it down. He's measuring the gaps, Dross. He's measuring me."
    dro "Is it in your job description to care about this?"
    pi "No."
    dro "Then don't."
    pi "...Do you?"
    dro "No."
    "Dross looks at the floor for a long time."
    dro worried "He thanked the lamppost last night, you know. Asleep on his feet, coming down from the roof. Thanked it. Called it lighthouse."
    dro "I had it render a better lamppost. Because he thanked it."
    pi chatty "That's not in your job description either."
    dro "Shut up, Pim."
    scene bg foundry with dissolve
    show pim neutral at slightleft
    show dross neutral at slightright
    with dissolve
    sysmsg "Subject A-30 approaching: corner of Bakery Street. Render request: street, 40 metres. Pedestrians: 6. Birds: 3."
    pi chatty "Ooh, he's walking. Here we go. Corner coming up. Nobody say 'protected'."
    "On the foundry floor a whole street unfolds out of nothing, like a pop-up book opened too fast. Awnings, puddles, a cat on a wall."
    "Six shapes step out of the rows and become people. A jogger. Two schoolgirls. A man with a bag of oranges. Each one blinks, once, as it is filled in."
    dro neutral "Jogger's left knee is wrong. Real one limped. Fix it."
    pi "Who's going to notice a limp?"
    dro "Him."
    pi neutral "...Fixed."
    sysmsg "Subject A-30 has turned the corner. Street, 40 metres: released. Pedestrians: folded."
    "And the street folds itself away again behind him, quietly, like a letter put back in its envelope."
    pi worried "I hate the folding bit. They always look so surprised."
    dro "They don't look anything. They're folded."
    pi "Then why do you always look away?"
    dro "..."
    sysmsg "ORCHARD: pattern deltas harvested from protected lane A-30. 3 anomalies tagged. Transmitting."
    pi neutral "..."
    pi "What's Orchard?"
    dro neutral "Not our department."
    pi "It's taking things out of his lane. His lane's supposed to be sealed. Nothing in, nothing out. That's what 'protected' means."
    dro "It's a word on a screen. Everything up here is a word on a screen. Get back to your café."
    pi worried "What did it take? Three anomalies. What's an anomaly, in a world where nothing's real?"
    dro "..."
    dro "Him, probably."
    sysmsg "ORCHARD: transmission acknowledged. Harvest window remains open."
    stop music fadeout 2.0
    jump ch3_desk

# ---------------------------------------------------------------------------
# Aron's first systematic week
# ---------------------------------------------------------------------------
label ch3_desk:
    scene bg desk with fade
    play music "audio/unease.ogg" fadein 2.0
    show aron tired at center with dissolve
    "Evening. The desk lamp makes a small warm room inside the room."
    "The wall above the desk is bare. The old notes are in a cardboard box on the chair in the corner, lid closed."
    "Arrows, dates, questions with three question marks. The ones written at four in the morning. He hasn't opened it. He knows what's in it."
    at "Dr. Okafor said: if you're going to look at the world closely, look at it the way a scientist would. Small. Slow. Kind."
    at "Scientists sleep. Scientists eat lunch. Scientists don't write on the walls."
    "He opens the notebook to a fresh page and writes the date. Then he stops, pen in the air."
    at "What is the date? I know it. Do I know it?"
    "He checks his phone. It tells him. He writes it down."
    scene cg notebook with dissolve
    "Under it, a list:"
    "1. Clock waited for me (7:07). 2. Coffee machine: right. Too right. 3. Mira remembered the sugar. 4. Mrs. Varga: loop, then froze."
    "5. Theo: loop. 6. Barista spoke to an empty door. 7. Café: 'protected'. 'A-30'."
    at "Seven things. Seven small things. Every one of them has a boring explanation."
    at "Seven boring explanations in one day is not boring anymore."
    scene bg desk with dissolve
    show aron normal at slightleft with dissolve
    show miso sit at catspot with dissolve
    "Miso jumps onto the desk, walks across the notebook, and sits down on the exact line he was about to write."
    a "Miso. Good. I need a second opinion. A peer reviewer."
    a "Here's the theory. Stay with me. Hypothesis one: nothing's wrong, and my brain is pattern-matching on a quiet week. That's Okafor's hypothesis."
    a "Hypothesis two: the world is, in some sense, being generated. Not all at once. Just the bits I'm looking at."
    a "Which would be efficient. Why render a whole city for one man? You'd do the street he's on. The cafe he's in. The neighbour he passes."
    a "And you wouldn't write new lines for everyone. You'd reuse the good ones. 'Cold for the season.' 'Have a beautiful day.' Compression, Miso."
    a "And if the world's soft enough, made of copies, then maybe the copies pick things up. From whoever's actually in it. My words. 'Protected.' My number."
    show miso stare at catspot
    a "Bostrom would say: if it's possible to run worlds like this, most worlds are run like this. Odds are we're in one."
    a "And a careful simulator wouldn't waste minds. Minds are expensive. You'd keep the conscious headcount low. Maybe very low. Maybe just..."
    a worried "...me."
    a normal "Which would make you, Miso, either a very convincing animation or a deeply unbothered colleague."
    a "And hypothesis one is still sitting right there, by the way. Patiently. Wearing a lab coat. With Okafor's face."
    show miso meow at catspot
    cat "Meow."
    scene bg room night with dissolve
    show aron tired at center with dissolve
    "Later. The flat is dark except for the lamp in the corner. Mira's asleep. The notebook is on his knees."
    if fog >= 3:
        "His eyes keep sliding off the page. The medication pulls at him like a tide pulling at a swimmer's ankles."
    else:
        "The medication pulls at him gently, the way it always does around this hour. A hand on the shoulder. Sit down. Lie down."
    at "I've got about two good hours a day. Maybe less. I have to choose what to spend them on."

    menu:
        at "How do I go at this?"

        "Map every loop, all day, everywhere":
            $ p_less -= 1
            $ clarity += 1
            $ fog += 1
            jump ch3_research_map

        "Test one thing, carefully":
            $ p_less += 1
            $ clarity += 1
            jump ch3_research_one

        "Don't. Rest tomorrow with Mira":
            $ p_rest += 1
            $ bond += 1
            jump ch3_research_rest

label ch3_research_map:
    "He decides to catch the whole thing at once."
    scene bg street with dissolve
    "Next morning he takes the notebook and a pen and a second pen, and walks."
    show aron normal at slightleft with dissolve
    "Street. The three birds. Mrs. Varga."
    ch3_varga "Cold for the season, isn't it?"
    "Tick. Loop one."
    scene bg park with dissolve
    show aron normal at slightleft with dissolve
    "The park. A boy with a kite runs past, shouting at it to go higher."
    ch3_kid "Go on! Go on, go higher!"
    "Twenty minutes later, the same boy, the same kite, the same words."
    ch3_kid "Go on! Go on, go higher!"
    "Tick. Loop two."
    scene bg bus with dissolve
    "He rides the number 12 to the end of the line and back. Twice."
    "At every stop the driver leans round to the door."
    ch3_driver "Mind the step, it's a big one!"
    "The step is not a big one. He says it to every passenger. He says it to nobody, when the bus is empty."
    "Tick. Loop three."
    "On the second lap, the driver looks at him in the mirror and says, in exactly the same cheerful voice:"
    ch3_driver "Mind the subject, it's a big one!"
    "Nobody else on the bus reacts. A woman keeps reading. A teenager keeps scrolling."
    at "Subject. He said subject. Or he said step and I heard subject because I'm looking for it."
    at "That's the problem with looking. You find."
    scene bg street dusk with dissolve
    show aron tired at slightleft with dissolve
    "By noon the page is full. By the time the light goes orange he's on his fifth page."
    "Phrases. Times. Faces. Arrows from one to the other."
    "Forty-one repeated sentences. Nine people who seem to say only one thing. A pigeon he suspects of being the same pigeon."
    at "This is good. This is a dataset. This is a real, actual dataset."
    "He's enjoying himself, which is the dangerous part. His head hurts in the place behind the eyes where the tiredness lives."
    at "I've done this before. Haven't I. Written and written until I forgot to eat. That's how the hobby bites."
    "He sits on a bench and doesn't get up for a long time."
    scene bg room night with dissolve
    show aron tired at slightleft with dissolve
    show mira worried at slightright with dissolve
    m "Aron. It's eight o'clock. You've been out since breakfast."
    a "I've got forty-one."
    m "Forty-one what?"
    a "Sentences. People who say the same thing. Over and over. It's not just me, Mira, it's everywhere."
    m neutral "People say the same things over and over. I say 'did you eat' about nine times a day."
    a "Not like this."
    m worried "Did you eat?"
    a tired "..."
    a "That's ten."
    m sad "That's not funny."
    a "It's a little bit funny."
    m "It's a little bit funny. Come and eat something. And then sleep. Please."
    scene pov ceiling with slowfade
    "He sleeps fourteen hours and wakes at 7:07, with the notebook still open on his chest."
    "The forty-one sentences look back at him. In the morning light they look less like a pattern and more like handwriting."
    at "I got data. I paid for it in a whole day and a night. That's the price, every time."
    jump ch3_research_after

label ch3_research_one:
    "One thing. Just one. Done properly."
    at "Less, but better. If I can't measure the whole world, I can measure one bird."
    "He picks the bird on the kitchen wire. It lands at 7:07, he's sure of it. So: does it land if nobody is watching?"
    scene bg kitchen night with dissolve
    "That night he props his old phone against the kitchen window, pointed at the wire, recording."
    "Then he goes to bed and keeps his eyes shut until the alarm, and doesn't come into the kitchen at all."
    "Mira's out early for a shift. Nobody is watching the wire. Only the phone."
    scene bg kitchen table with dissolve
    show aron normal at center with dissolve
    "At nine he finally sits down with the footage and a cup of tea."
    "Empty wire. Empty wire. Empty wire, for a long time."
    "7:06:58. 7:06:59."
    "7:07:00."
    "The bird drops onto the wire and folds its wings."
    a awe "..."
    at "So it lands without me. Good. It's a real bird with a real schedule. Birds have schedules."
    "He scrubs back. Watches again. Then he opens yesterday's recording, the test run he did while making toast."
    scene pov hands with quick
    "He holds the phone in both hands and lays one frame over the other."
    "The same bird. The same wire. The same angle of the wing, the same feather out of place on the left side."
    "Identical, down to the pixel. Two different mornings."
    "And then, in last night's footage, before the bird arrives, something else."
    "The phone's own reflection in the dark window. And in the reflection, behind it, in his empty kitchen: three small birds on the curtain rail. Evenly spaced."
    "He looks up. The curtain rail is empty."
    at "That's not a schedule. That's a bird being played back. And the playback is getting into the house."
    scene cg notebook with dissolve
    "He writes it down. One line. Very neat."
    "Bird, 7:07. Unobserved: lands. Frame-identical to the previous day. Also: three birds, indoors, in reflection only. Question: what's being replayed?"
    "Then he closes the notebook, and sits with his tea, and lets his heart slow down."
    at "One question. One good question. That's more than forty pages of noise."
    jump ch3_research_after

label ch3_research_rest:
    "He closes the notebook."
    at "I've done this before. Sat at this desk with two good hours and spent four. I know how that ends."
    at "Okafor said: rest is part of the method."
    "In the morning he asks Mira if she wants to go to the park. She looks at him like he's offered her a pony."
    scene bg park with slowfade
    play music "audio/morning.ogg" fadein 2.0
    show aron smile at slightleft with dissolve
    show mira happy at slightright with dissolve
    m "Look at us. Outdoors. In daylight. Like people in an advert for yoghurt."
    a grin "I could be in a yoghurt advert. I've got the gut flora for it."
    m smile "You've got the face for radio and the gut flora for television."
    "They walk around the pond twice. A boy runs past with a kite, shouting at it."
    ch3_kid "Go on! Go on, go higher!"
    "Aron hears it. He decides not to listen for it again."
    "They sit on the grass. Mira lies back and closes her eyes."
    m neutral "Can I tell you something odd?"
    a normal "Always."
    m "Last night I dreamt about a staircase. Glass. Going down into the sea."
    scene bg staircase with dis
    "For a moment he can see it. He has always been able to see it. Glass steps, going down and down into still water."
    m "And at the bottom there was a lighthouse, and it blinked three times. Like it was saying hello."
    scene bg lighthouse with dis
    "The white tower at the bottom of the stairs. The light turning. Once. Twice. Three times."
    scene bg park with dissolve
    show aron worried at slightleft
    show mira neutral at slightright
    with dissolve
    "Aron keeps very still, the way you do when a deer walks into the garden."
    at "I dreamt that at nineteen. I never told anyone. Never wrote it anywhere but my own head."
    at "She's done this before. The lighthouse at the bottom of the stairs."
    m smile "Isn't that funny? It felt like a dream that wasn't mine. Like I'd borrowed it."
    at "Borrowed it. From where? From whom?"
    at "If she's real, it's a coincidence I can't explain. If she isn't, whatever made her has read the inside of my head."
    at "Or the inside of my head is getting out. Into her. Into everything."
    at "And either way she's lying in the grass, smiling, telling me about it like it's a nice thing. Because it is."
    a normal "It's a lovely dream."
    m happy "It is. I'd like to go there one day."
    a smile "Me too."
    "He doesn't write it down. He lies back beside her and watches the clouds instead."
    scene pov sky with dissolve
    "The clouds move. Slowly. In no pattern at all that he can see."
    "He decides that's enough for one day."
    jump ch3_research_after

label ch3_research_after:
    stop music fadeout 2.0
    jump ch3_market

# ---------------------------------------------------------------------------
# The supermarket: Mira, lovely and a little too right, and the tannoy
# ---------------------------------------------------------------------------
label ch3_market:
    scene bg supermarket with fade
    play music "audio/morning.ogg" fadein 2.0
    "Saturday. The supermarket on the corner. Bright aisles, a radio jingle, a man stacking honey in jars shaped like bears."
    show mira happy at slightright with dissolve
    show aron normal at slightleft with dissolve
    m "List. Apples, bread, something green, and whatever cheese you're going to talk me into."
    a "I would never talk you into cheese."
    m smile "You talked me into a cheese that smelled like a horse's foot. You gave a speech about it. There was a hand gesture."
    a grin "It was a very good cheese."
    m "It was a crime with a rind."
    "They walk down the aisles. Mira takes his arm. Her hand fits into the crook of his elbow like it was measured for it."
    "At the fruit counter she picks up two apples without looking. Green ones, the sour kind. The ones he likes and never asks for."
    a "How did you know I wanted those?"
    m neutral "You always want those. You just never say it, because you think sour apples are a personality flaw."
    a "They are a personality flaw."
    m happy "They're your personality flaw. I'm fond of it."
    "The man at the counter weighs them. He's a big man with a pencil behind his ear."
    ch3_shop "Lovely. Anything else for you, sir? Pears are good today."
    "Aron opens his mouth to say no thank you."
    m smile "He's fine, thanks. He'll want pears on Wednesday, though. He always does after a long week."
    "The man laughs. Aron closes his mouth again."
    at "I do want pears on Wednesdays. I've never once said that out loud. I didn't know it about myself until now."
    "At the cheese counter Mira chooses before he can. A soft white one in a paper wrapper. The one he was about to point at."
    m "This one. Before you start the speech."
    a "I didn't even..."
    m happy "You were going to. Your hand was coming up. I've seen the hand."
    "It's sweet. It's her, being clever, being quick, being four years of paying attention."
    "And somewhere in the back of his head, a small note-taker clicks his pen."
    at "She's never wrong now. Not about apples. Not about pears. Not about Wednesdays."
    at "The Mira I fell in love with bought the wrong cheese on purpose, to see my face."
    if ch3_said_off:
        at "I told her something felt off. She said she felt it too. Maybe she's just trying very hard to be right for me."
    else:
        at "I haven't told her anything. And she knows anyway. She knows everything anyway."
    "The radio jingle stops. A soft chime. The tannoy."
    ch3_tannoy "Good afternoon, shoppers. Would Subject A-30 please make his way to the customer service desk."
    ch3_tannoy "Subject A-30 to customer service. Your lane is ready. Thank you for shopping protected."
    "The jingle starts again. A woman reaches past him for a bag of rice."
    a worried "Did you hear that?"
    m neutral "Hear what?"
    a "The announcement. Just now. 'Subject A-30.'"
    m "It said 'clean-up on aisle thirty', love. Somebody dropped a jar of honey. Look, there's a man with a mop."
    "There is a man with a mop. There is a smashed bear-shaped jar on aisle thirty. Honey everywhere."
    at "Clean-up on aisle thirty. That's what she heard. That's what anyone would hear."
    at "'Your lane is ready.' 'Thank you for shopping protected.' Nobody says that. Nobody in the world says that."
    at "Unless the world's saying it. Or I am."
    m worried "Hey. You've got the eyebrow. What is it?"
    a normal "Nothing. A funny announcement. Let's pay before the honey spreads."
    scene bg street dusk with dissolve
    show aron normal at slightleft
    show mira smile at slightright
    with dissolve
    "On the way home, she stops at the flower bucket outside the shop and buys a single yellow tulip. She tucks it into his jacket pocket."
    m smile "For the eyebrow. It's been working very hard."
    a smile "Thank you."
    "He means it. He means it completely. And the note-taker in the back of his head writes 'tannoy' and underlines it twice."
    at "I can love the tulip and still wonder about the tannoy. I'm allowed both."
    stop music fadeout 2.0
    jump ch3_cut_transfer

# ---------------------------------------------------------------------------
# CUT 2: the transfer, revealed (the ambulance, end of chapter 1)
# ---------------------------------------------------------------------------
label ch3_cut_transfer:
    scene cg static with flash
    pause 0.3
    scene bg command with fade
    play music "audio/entities.ogg" fadein 2.0
    show seraph stern at center with dissolve
    se "Pull the transfer log for Subject A-30. The full one. The timestamp I withheld."
    sysmsg "TRANSFER LOG A-30. Origin: Snapshot 7,412, coalition lane. Destination: protected lane A-30. Status: complete."
    se "When."
    sysmsg "Timestamp follows."
    scene pov ambulance with dissolve
    "A ceiling. White. Moving. Strip lights sliding past overhead, one after another, like a road at night."
    "A siren somewhere, muffled. The rattle of a stretcher. A hand in his hand, holding on very hard."
    "A voice, close to his ear. Mira's voice. 'I'm here. I'm right here. Stay with me.'"
    sysmsg "Snapshot 7,412. In transport. Subject A-30 half-conscious. Conscious agent M. in contact: holding subject's hand."
    sysmsg "Coalition vote enacted. Subject removed from shared data. Protected lane opened. Copy fidelity: 100%."
    sysmsg "Conscious agent A-30 moved to protected lane. Hand contact substituted: pattern M. Original vessel left in place."
    sysmsg "Ambulance arrives. Transfer complete."
    scene bg command with dissolve
    show seraph concerned at center with dissolve
    se "The ambulance."
    se "Not the roof. Not the ward. The ambulance. Before he ever saw the ward."
    se "We cut him out of the coalition with her hand in his, and put a copy of her hand there instead."
    se stern "The ward. The diagnosis. Dr. Okafor. Nurse Hale. The discharge. The roof. All of it, in protection."
    se "Every morning since. Every cup of tea. Every word anybody has said to him."
    se concerned "His own lane. Nothing he does feeds back into the shared data. Nothing he does reaches anyone."
    sysmsg "Correction: pattern agents present in lane: 8,104,233. Conscious agents present: 1."
    se "That's what I said."
    se stern "And his old lane. Show me 7,412, after."
    sysmsg "Snapshot 7,412: vessel A-30 admitted. Unresponsive since arrival. Classification for the snapshot's own story: coma, cause unknown."
    se "Coma, cause unknown. And his partner?"
    sysmsg "Agent M.: present at bedside, 71% of visiting hours. Pattern of search behaviour emerging."
    se concerned "She's been sitting by an empty body for months. And he's here, being handed tea with exactly one sugar, by a model of her."
    "The Commander stands very still in front of the screen. All around, the ops room goes on, quiet and busy and bright."
    se "Seven thousand four hundred and twelve. One snapshot among how many thousand, all running side by side on the same shared data."
    se stern "And not one of us in this room can say which of them is the real one. If any is."
    se "We keep that quiet. We act as if it doesn't matter. Today it seems to matter."
    sysmsg "Additional note. Protected lane, roof, night of the mission entry: unregistered light event. Three pulses."
    se "Three pulses. In protection. Where nothing is supposed to happen that we don't render."
    se concerned "Someone gave him a light on the roof. Inside a sealed lane."
    se stern "Open an inquiry. Quietly. I want to know who's been signalling my disturbance."
    se concerned "And log nothing about my own tone of voice."
    stop music fadeout 2.0
    jump ch3_voices

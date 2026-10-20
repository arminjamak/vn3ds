# Chapter 3 - "Snapshot", part 3.
# The fight with Mira, making up, and the night that follows (closeness,
# chosen without knowing whether she is real).
# Continues in ch3_part4.rpy.

# ---------------------------------------------------------------------------
# The fight
# ---------------------------------------------------------------------------
label ch3_fight:
    scene bg kitchen with fade
    play music "audio/morning.ogg" fadein 2.0
    "In the protected lane, it's a Tuesday. Nobody here has noticed that it's been Tuesday-shaped for a while."
    show mira smile at slightright with dissolve
    show aron normal at slightleft with dissolve
    "They're making dinner. Risotto, which means forty minutes of stirring and talking, which is why they make it."
    "Mira chops the onion. Aron stirs. The radio plays something with a saxophone in it."
    a "Can you pass me the..."
    "The wooden spoon is already in his hand. She passed it before he finished."
    m happy "Spoon. You always want the spoon at this bit."
    a "I do always want the spoon at this bit."
    at "Right. Let's play a little game. Nothing dramatic. Just a man, a risotto, and a hypothesis."
    a "You know what this needs? A little bit of..."
    m "Lemon zest. It's on the board."
    "It is on the board. Already zested. A small yellow hill of it."
    a "And the parmesan should go in at the..."
    m smile "At the very end, off the heat, or it goes stringy. You told me that in our first month. You did a voice."
    a grin "It was a good voice."
    at "Three for three. She's always been good at me. But she used to miss sometimes. She used to guess thyme when I meant lemon, and argue about it."
    at "Let's try one she can't possibly get."
    a "I was thinking, after dinner, we could..."
    m "Watch the documentary about bridges. I know. I'll pretend I care about suspension cables. You'll explain them anyway."
    "He hadn't decided that until she said it. He realises, stirring, that he would have."
    a normal "Mira. What did I say on our first date? When the waiter dropped the tray. The exact words."
    m neutral "'Well, that's one way to break the ice.' And then you helped him pick up the glass and cut your thumb."
    m "Why?"
    a "Just checking my notes."
    "She puts the knife down."
    play music "audio/unease.ogg" fadein 2.0
    m "You're testing me."
    a "No. Well. A bit. It's a hobby. You know it's a hobby."
    m sad "I know it's a hobby with the birds. I didn't know I was one of the birds."
    m "You've been doing it all evening. Starting sentences and waiting to see if I finish them. Like I'm a crossword."
    a "..."
    "He could make a joke. He has three ready. He doesn't use any of them."
    a tired "You're never wrong any more. That's all. It's been weeks. Every sentence, every spoon. I miss you being wrong."
    a "You used to forget the sugar. You used to guess thyme. You used to argue with me about the parmesan. I miss that."
    m sad "'I miss you being wrong.'"
    m "Wow."
    m "I'd love to be wrong, Aron. Tell me how. Tell me what to get wrong and I'll get it wrong for you."
    "Her voice cracks on the last word. Not smoothly. It cracks badly, like real things crack."
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
    "There. He said it. The sentence he's been carrying in his pocket for weeks."
    m "..."
    a "Not just you. Anyone. Theo. Mrs. Varga. The barista. It started as a game. It isn't one any more. I don't know if any of you are real."
    a "And you're the one I most need to be, and you're the one I most can't tell."
    m sad "What am I supposed to do with that?"
    a "I don't know."
    m "No. Really. What am I supposed to do? Prove it? How? Bleed? Cry? I'm crying, Aron, does that count?"
    a "Mira..."
    m "I've been here the whole time. The ward. The pills. The nights. I've been right here, and you're looking at me like I'm a coat stand that learned to talk."
    scene bg bedroom door with dissolve
    "She turns off the hob. She goes to the bedroom and closes the door."
    "Not a slam. Worse. Carefully."
    scene bg room night with dissolve
    show aron sad at center with dissolve
    a "..."
    at "I told the truth. It's true. It's exactly true."
    at "And it went into her like a knife. Whatever she is, it went into her like a knife."
    at "Maybe that's the thing about the truth. It doesn't care whether the person you say it to can bleed. It cuts anyway."
    scene pov ceiling with dissolve
    "He lies on the sofa and looks at the living-room ceiling, which has no crack shaped like anything. The Braun clock keeps the time behind the closed door."
    jump ch3_makeup

label ch3_fight_sorry:
    a tired "I'm sorry. That was a horrible thing to do over a risotto. It's the tiredness, it's the pills, it's... I don't know what it is."
    m sad "..."
    a "You're not a crossword. You're you. I'm just tired and my hobby got out of its box."
    m neutral "Okay."
    a "Okay?"
    m smile "It's fine. It's fine. Come here."
    "She hugs him. She forgives him in under a minute. It's warm and easy and smooth."
    "Too easy. Too smooth."
    at "The Mira I knew would have made me sweat for at least an hour. She'd have gone to bed angry on principle. She'd have been right to."
    at "And I lied, too. It wasn't the tiredness. I meant every word. I just didn't want to see her face when I meant it."
    "They rescue the risotto, mostly. They watch the bridges documentary. She leans on him. He explains the suspension cables. She laughs in all the right places."
    "Every single right place."
    scene pov ceiling with dissolve
    "He lies awake afterwards next to her and feels the lie sit between them, about the size of a cat, purring."
    jump ch3_makeup

label ch3_fight_leave:
    a "I need some air."
    m sad "Of course you do."
    a "I'm not running off. I'll be back in an hour. I just need to walk it off before I say something stupider."
    m "Take your coat. It's going to rain."
    "Of course she knows it's going to rain."
    stop music fadeout 1.0
    scene bg street rain with fade
    play music "audio/watch.ogg" fadein 2.0
    show aron sad at slightleft with dissolve
    "It rains. Of course it rains."
    "He walks without deciding where. Past the bakery, past the bus stop, past the place where the street dips and fills with puddles."
    at "For the first time in a long time, I'd like a door. Out of this smooth town, where everyone says the right thing on time."
    at "Somewhere the sugar gets forgotten. Somewhere I can't win at my own game."
    scene cg umbrella with dissolve
    "Someone is standing under the bus shelter. A shape in a grey coat, holding an umbrella."
    "His umbrella. He'd know it anywhere. Black, with one bent spoke."
    ch3_stranger "Hey. It's you."
    a "Sorry?"
    ch3_stranger "You gave me this. Ages ago. I was soaked through, and you just handed it over and walked off into the rain."
    ch3_stranger "Never got to give it back."
    a "Keep it. It suits you."
    "The stranger looks at him. Not a long look. Just long enough."
    ch3_stranger "Whatever you're running from tonight, she's not it."
    ch3_stranger "Go home."
    scene bg night with dissolve
    show aron worried at slightleft with dissolve
    at "Nobody says that. Strangers don't say that."
    at "Unless somebody tells them to."
    "Above the shelter, the streetlight flickers. Once. Twice. Three times."

    menu:
        at "The stranger is already turning to go."

        "Thank them. Properly":
            $ p_spirits += 1
            $ watch += 1
            a "Hey. Thank you. Really. I needed someone to say that."
            ch3_stranger "Anyone would have."
            a "No. Not anyone. You did. So, thank you. You."
            "The stranger pauses at the edge of the shelter. Something passes over their face. Surprise, maybe. Or something warmer."
            ch3_stranger "...Nobody ever says that to me."
            ch3_stranger "Thank you for saying it."
            "They walk off into the rain with his umbrella. The streetlight burns steady."
            at "If they're a pattern, I just thanked a pattern. Good. Patterns can be thanked."
            at "Somebody, somewhere, made them say it. So somebody, somewhere, just got thanked."

        "Ask who they really are":
            $ clarity += 1
            $ p_truth += 1
            a "Wait. Who are you? Really?"
            ch3_stranger "Me? Nobody. Just someone who got rained on once."
            a "Who told you to say that? About her?"
            "The stranger tilts their head. For half a second, their face does nothing at all."
            "Not blank. Waiting. Like a page that hasn't loaded."
            ch3_stranger "Go home, Aron."
            a awe "I never told you my name."
            "But they're gone. Around the corner, into the rain, with his umbrella."
            "The streetlight burns steady."
            at "Half a second. The same half-second Theo did. The waiting look."
            at "And then something stepped into the gap and spoke. Something that knew my name."

    "He walks home. Slowly. The rain is soft now."
    jump ch3_makeup

# ---------------------------------------------------------------------------
# Making up
# ---------------------------------------------------------------------------
label ch3_makeup:
    stop music fadeout 2.0
    scene bg kitchen with slowfade
    play music "audio/morning.ogg" fadein 2.0
    if ch3_left:
        "He came home at midnight soaked to the skin. She was on the sofa with a towel already waiting. She didn't say anything."
        "She just put the towel over his head and rubbed it, hard, like she was angry at his hair specifically."
    "In the morning, 7:07. The bird on the wire. And Mira, in the kitchen doorway, arms folded."
    show mira neutral at slightright with dissolve
    show aron tired at slightleft with dissolve
    m "So."
    a "So."
    m "Are we going to talk about it, or are we going to have a very polite breakfast?"
    "Through the doorway, in the corner of the living room, her lamp. The brass one with the green glass shade that was her gran's."
    "It's been flickering for a month. A loose wire somewhere. She keeps saying she'll get it fixed."

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

        "Just sit with her. Nothing clever":
            $ integrity += 1
            $ bond += 1
            jump ch3_makeup_sit

label ch3_makeup_lamp:
    a normal "Can I fix your lamp?"
    m surprised "...What?"
    a "Your gran's lamp. It's been flickering for a month. I can fix it. I'd like to fix it."
    m neutral "Aron, we just had the worst fight we've had in a year, and you want to do electrics?"
    a "I want to do one thing right. One small thing, properly. Then I'll talk. I promise."
    "She looks at him for a long moment. Then she shrugs and gets him the little screwdriver set from the drawer."
    scene bg room with dissolve
    show aron normal at slightleft
    show mira neutral at slightright
    with dissolve
    "It takes him an hour. His hands are slow from the pills. He drops the tiny screw twice and finds it once, under the sofa, with a torch."
    "She sits on the arm of the sofa and watches him, and doesn't help, and doesn't leave."
    scene pov hands with dissolve
    "The wire is loose at the plug. He strips it, twists it, tightens the terminal. His fingers shake. He does it anyway. Puts the cover back."
    scene bg room with dissolve
    show aron smile at slightleft
    show mira smile at slightright
    with dissolve
    "He switches it on. Green light pools on the floor. Steady."
    m "..."
    m "It's not flickering."
    a "It's not flickering."
    m "Gran would have liked you. She'd have said you're very slow, but you do things properly."
    a "I'll put it on my gravestone. 'Very slow. Did things properly.'"
    m happy "Don't you dare die before I've had a chance to tell people that."
    at "Less, but better. One lamp. One wire. One hour. And something in the room is mended."
    jump ch3_makeup_talk

label ch3_makeup_plan:
    a normal "Let's go away. A whole new start. A week somewhere. The sea. No notebooks, no pills on the counter, no birds on wires."
    a "I'll plan it. All of it. A new routine when we come back. A new everything."
    m neutral "..."
    m "Come outside a minute."
    scene bg balcony with dissolve
    show aron normal at slightleft
    show mira neutral at slightright
    with dissolve
    "Their little balcony. Two chairs, one dead tomato plant, a view of the backs of other people's buildings. Her favourite place in the flat."
    m "That's lovely. The sea. A new everything."
    m sad "That's lovely and I don't want it."
    a worried "You don't?"
    m "I don't need a new start. I need you here. On this balcony, with the dead tomato. I need you to look at me like I'm me."
    m "Every time things get hard, you make a bigger plan. A bigger theory. A bigger trip. I don't want bigger. I want you."
    a "..."
    a "That's... a very fair point. I hate it."
    m smile "I know. I'm usually right. You said so. Loudly."
    at "A bigger plan. She's right. Every time it hurts, I reach for the whole world instead of the thing in front of me."
    scene bg kitchen table with dissolve
    show aron normal at slightleft
    show mira neutral at slightright
    with dissolve
    jump ch3_makeup_talk

label ch3_makeup_sit:
    scene bg kitchen table with dissolve
    show aron tired at slightleft with dissolve
    "He doesn't say anything clever. He sits down at the kitchen table and waits."
    show mira neutral at slightright with dissolve
    "After a while she sits down across from him."
    "Neither of them speaks. The bird on the wire shifts its feet. The fridge hums."
    scene cg hands with dissolve
    "He reaches across the table and puts his hand palm up, and leaves it there."
    "It stays empty for a long time. He doesn't take it back."
    "Then her hand lands in it. Not gently. Like she's putting something down that's been heavy."
    scene bg kitchen table with dissolve
    show aron normal at slightleft
    show mira sad at slightright
    with dissolve
    m sad "You really hurt me."
    a "I know."
    m "You don't get to say clever things for at least ten minutes."
    a "I don't have any. I left them in the other room."
    m smile "...That was a little bit clever."
    a smile "Sorry. Reflex."
    jump ch3_makeup_talk

label ch3_makeup_talk:
    m neutral "Okay. Talk."
    a "I've been scared. Since the voices came back. Before that, even. Everything's so smooth. Everyone says the same things."
    a "And you're so good. So right. And instead of being grateful, I started looking at you like evidence."
    m "Like a crossword."
    a "Like a crossword. I'm sorry."
    m "I'm not a vending machine of correct answers, Aron. I'm a person who's been paying very close attention to someone she loves."
    m "Of course I know what you're going to say. I've been learning you for four years. That's what love is. It's homework."
    a "Homework."
    m smile "Very boring homework. With occasional bridges."
    if p_truth > 0:
        a "I still don't know, you know. Whether... any of it. I can't promise I'll stop wondering."
        m neutral "I know. I'd rather you told me than lied to me. Even when it stings."
    else:
        a "I'll try to stop wondering."
        m neutral "You won't. But it's sweet that you said it."
    a normal "Here's what I do know. I'm the one who gets to decide how I treat you. Not my brain. Not the birds. Me."
    a "And I decided a long time ago. I just forgot for a week."
    m happy "..."
    if ch3_left:
        m "Don't forget again. I'm not doing the towel thing twice."
    else:
        m "Don't forget again. I've only got so much patience, and you've used most of it on bridges."
    if told_mira:
        m neutral "And Aron? The mission. I meant it. Somebody should look. Just don't look at me like I'm the thing you're looking for."
    "She kisses him. Quickly, on the mouth, like a full stop."
    m smile "Breakfast. Then you're doing the washing up. Penance."
    a smile "Penance accepted."
    stop music fadeout 2.0
    jump ch3_night

# ---------------------------------------------------------------------------
# That night: closeness, chosen
# ---------------------------------------------------------------------------
label ch3_night:
    scene bg room night with blackout
    play music "audio/watch.ogg" fadein 3.0
    "It rains in the evening. Proper rain, the kind that turns the windows into rivers."
    "They don't watch the bridges. They don't watch anything. They eat toast on the sofa and listen to the rain, and it's enough."
    show mira neutral at slightright with dissolve
    show aron normal at slightleft with dissolve
    m "Can I ask you something, and you answer honestly, even if it's bad?"
    a "Yes."
    m "When you look at me now. After all of it. What do you see?"
    "He looks at her. Properly. Not the way he looks at the birds."
    "Red hair coming loose from its clip. The freckle on her left eyelid that she hates. A crumb of toast on her jumper. Tired eyes. Brave ones."
    at "I can't prove she's real. I can't prove anyone is. I've stopped believing I ever could."
    at "But I can choose. That part's mine. Nobody built that part. I decide who I am to her."
    a "I see the person I'd pick. Out of everything. Every time."
    m sad "..."
    m smile "That's a very good answer. Annoyingly good."
    a "I worked on it."
    m "You did not."
    a smile "I didn't. It just came out. That's how you know it's true."
    "She takes his hand, and stands, and doesn't let go of it."
    m neutral "Come to bed."
    "It isn't a question. It's an invitation, and they both know the difference."
    "He goes."
    scene cg together night with dissolve
    "The rain on the window. Blue light from the street, moving on the ceiling like water."
    "Her shoulder under his hand. Her breath at his neck. The ordinary miracle of somebody letting you close."
    "He has been so far away from her for so long. Behind the fog. Behind the notebook. Behind the question."
    at "Whatever she is. Whatever I am. Whatever this place is made of."
    at "I'm here. I'm choosing to be here. With her. Not because I know. Because I decided."
    m "Hey."
    a "Hey."
    m "You're here. Actually here. I can tell."
    a "I'm here."
    "She laughs, very softly, and pulls the sheet up over both of them, and the rest belongs to them."
    scene black with dissolve
    pause 1.5
    scene cg together night with dissolve
    "Later. The rain has softened to a whisper. The blue light still moves on the ceiling."
    "They lie in the dark, not sleeping, her head on his chest, his fingers in her hair."
    m "Your heart's slow."
    a "Pills."
    m "No. It's a different slow. It's a nice slow."
    a "Then it's you."
    m "Smooth."
    a "I've been told everything's very smooth lately."
    "She's quiet for a long while. He thinks she's asleep. She isn't."
    m "Aron. If you could go anywhere. Not a holiday. Anywhere. Another life. Another world, a better one."
    m "Would you go?"

    menu:
        m "Would you?"

        "\"Only if you came too.\"":
            $ p_exit += 1
            $ bond += 1
            a "Only if you came too."
            m "Even if it was better without me?"
            a "Then it wouldn't be better. That's how 'better' works. I checked."
            m "You checked."
            a "I'm very thorough."
            "She laughs into his chest. He feels it more than hears it."
            at "A door. If somebody ever offers me a door, I'll ask who gets to walk through it with me."

        "\"No. I'd stay and mend this one.\"":
            $ p_exit -= 1
            $ integrity += 1
            a "No. I think I'd stay. Mend this one. Even if it's a bit broken. Even if it loops."
            m "It loops?"
            a "Everything loops a bit. Mrs. Varga. The barista. Me, apparently."
            m "You loop beautifully."
            a "Thank you. I practise."
            at "If this is the world I've got, it's the one I'll work on. One lamp at a time."

        "\"I'd want to know who's real there.\"":
            $ p_truth += 1
            $ clarity += 1
            a "I'd want to know who's real there. Before I went. I couldn't go somewhere and spend the rest of my life guessing."
            m "You do that here."
            a "..."
            a "I do do that here."
            m "And you're still here. In bed. With me. Guessing."
            a "I'm still here."
            m "Then maybe guessing isn't the worst thing."
            at "Maybe. Or maybe somebody somewhere ought to make it so nobody has to guess."

    m "Good answer."
    a "You say that about all my answers."
    m "I say it about the good ones. You've had a good night."
    "She falls asleep first. He listens to her breathe. Slow, warm, uneven, with a tiny catch at the top of every third breath."
    at "That's not an impression of breathing. Or if it is, it's the best one ever made."
    at "And I don't need to know which. Not tonight."
    "Somewhere in the dark, Miso jumps onto the bed, turns around three times, and settles across both their feet."
    "He falls asleep with his hand on Mira's back, and for once he doesn't dream of anything at all."
    stop music fadeout 3.0
    jump ch3_sugar

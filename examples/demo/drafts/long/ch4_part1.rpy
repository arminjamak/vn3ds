# Snapshot - Chapter 4, "Chief Architect", part 1:
# the answer to the offer, both roads, and the Purgatorium.
#
# Terms: the snapshot worlds are the parallel lanes of the coalition, all on
# the same shared data. "Protection" (the protected world) is the separate
# lane Aron was pushed into during the ambulance ride, where nothing he does
# feeds back into the shared data.

# ---- chapter 4 state (only used in ch4_*.rpy) ----------------------------------
default ch4_asked_real = False
default ch4_woke_mira = False
default ch4_fixed_tap = False
default ch4_asked_dross = False
default ch4_gave_theo = False
default ch4_trial = "watch"
default ch4_lifted = False
default ch4_earth = "tell"
default ch4_ashveil_fasts = False
default ch4_vigil = "stay"
default ch4_watch_fate = "choose"
default ch4_mira_choice = "ask"
default ch4_route = "snapshot"
default ch4_win = "less"
default ch4_plus = True
default ch4_open = False
default ch4_s_truth = 0
default ch4_s_share = 0
default ch4_s_rest = 0
default ch4_s_spirits = 0
default ch4_s_govern = 0
default ch4_s_exit = 0
default ch4_s_less = 0
default ch4_best = 0

label chapter4:
    $ chapter = 4
    scene black with blackout
    centered "Chapter 4\n\nChief Architect"
    pause 0.5

    play music "audio/unease.ogg" fadein 2.0
    scene black with dis
    "The world has stopped."
    "Not the way it stuttered when the leaks came, a cab driver telling his own story back to him, a table saying 'protected'. Properly."
    "Every sound is gone, and the colour went with it. There is only the dark, and a tall man in it, as if the dark were a room he owns."
    show patron smile at slightright, fadein
    pa "A better world, Aron. I can't tell you better how. I only know it the way you know warmth."
    pa "And I won't tell you who there is real. That's the price of the ticket."
    scene pov hands with dissolve
    "He looks down at his hands. They're the only colour left. Pink knuckles. A biro mark on one thumb."
    at "Lord Ashveil. The name at the edge of every log. The one Ember wouldn't say out loud."
    at "Are these my hands? Are they protected hands, in a protected world, copied down to the biro mark? Lovely question. I'll write it down later."
    scene black with dissolve
    show patron smile at slightright
    show aron worried at slightleft with dissolve
    a "You froze everything. Is that a flex, or do you need the quiet to think?"
    pa "Both. Mostly I didn't want to be interrupted by a bus."
    pa smile "You've been very busy, Subject A-30. Notebooks. Theories. You worked out protection. Nobody works out protection."
    a "Protection. The ambulance. That's when you moved me."
    pa "Out of the coalition and into a lane of your own. Every snapshot of your world runs side by side on the same shared data. Yours doesn't."
    pa cold "Whatever you do here touches nothing. That was the idea. And yet bits of you keep leaking. Cab drivers. Café tables. It's very untidy."
    a "So why offer me anything? You could just switch me off."
    pa smile "I don't waste things that surprise me. Very little surprises me. It's the only thing I'm still hungry for that isn't food."
    a "...You're not really a man in a coat, are you. The pale face. The red eyes. That's not you."
    pa smile "Clever. No. You see teeth because you expect teeth. Your world is inside me, Aron. You can't picture the outside of the thing you live in."
    pa "So your mind drew me as the nearest true thing it had. Something that feeds on the life it holds, and gives a world back. A vampire. It's quite flattering."
    pa "I can put you back in a lane. Back in the coalition, where things count. A better one than you came from."
    a worried "And the people here? Mira. Theo."
    pa smile "Will go on. Pattern people go on beautifully. They hardly notice an absence. It's one of their mercies."
    at "Hardly notice. That's not the same as not noticing."
    jump ch4_offer_menu

label ch4_offer_menu:
    menu:
        pa "Well? The door is open. I don't hold doors long."

        "Take the ticket.":
            $ accepted_offer = True
            $ p_exit += 1
            $ clarity += 1
            jump ch4_accept

        "Who's real there? One name." if not ch4_asked_real:
            $ ch4_asked_real = True
            a "Just one. Tell me one person there who's real, and I'll believe the rest of it."
            pa smile "You'd spend the rest of your life checking that one person for seams."
            pa "And the rest you'd treat as furniture. I've watched you. You're a man who sorts."
            a sad "...That's not fair."
            pa "It's very fair. It's just not kind. I'm rarely both."
            at "He's right, and I hate that he's right. I've sorted people into real and rendered since the morning the bird landed."
            jump ch4_offer_menu

        "No. I'm staying.":
            $ accepted_offer = False
            $ p_exit -= 1
            $ integrity += 1
            jump ch4_refuse

# ---------------------------------------------------------------------------
# The road through the door.
# ---------------------------------------------------------------------------
label ch4_accept:
    a normal "Okay. I'll go."
    pa smile "Splendid. Pack nothing. Where you're going, they'll have toothbrushes."
    a worried "One hour first. I want to say goodbye."
    pa "To whom? To a pattern? You know what she is."
    a "I know what I think she is. That's not the same thing, and you know it, or you'd have told me who's real."
    pa cold "..."
    pa smile "One hour. I'm sentimental about hours. I eat them, mostly."
    hide patron with dissolve

    stop music fadeout 2.0
    scene bg bedroom night with slowfade
    play music "audio/watch.ogg" fadein 2.0
    "The colour comes back first, then the sound. The fridge hum. Rain. Mira breathing in the dark."
    "The Braun clock on the nightstand glows 3:12. Nothing important ever happens at 7:07 when he's awake."
    show aron sad at slightleft with dissolve
    at "She sleeps on her left side with one hand under the pillow, like she's holding something there for later."
    at "If she's a pattern, she's a pattern of the real Mira. The real Mira sleeps exactly like this. I'd know."
    at "Or the pattern learned it from me. From how much I watched. My mind leaked into everything else here. Why not into her?"
    show miso loaf at catspot with dissolve
    "At the foot of the bed, a warm orange loaf with a white chest opens one eye. Miso. She has opinions about 3 a.m."
    at "Either way, she's the shape of the person I love. What do I owe a shape?"

    menu:
        "Mira stirs. The hour is already moving."

        "Wake her. Tell her everything.":
            $ ch4_woke_mira = True
            $ p_truth += 1
            $ bond += 1
            jump ch4_accept_tell

        "Let her sleep. Leave a note.":
            $ ch4_woke_mira = False
            $ p_truth -= 1
            $ bond += 1
            jump ch4_accept_note

label ch4_accept_tell:
    hide miso
    a "Mira. Hey. Mira."
    show mira neutral at slightright with dissolve
    m "Mm. What time is it. Is it the voices?"
    a "No. It's me. I need to tell you something, and you're going to give me the ward look."
    m worried "...Okay. I'm awake. Tell me."
    a "Someone offered me a way out of this world. I think I'm going. I think this world is a copy, and you might be too."
    a sad "And I'm telling you anyway, because if you're real you deserve to know, and if you're not, I still want you to."
    m sad "..."
    m neutral "You know that's the most you thing anyone has ever said? 'You might be fake, but here's my whole heart.'"
    a "Sorry."
    m smile "Don't be. I'd rather be told the truth by a man with a weird hobby than be lied to by a nice one."
    m worried "Will you come back?"
    a "I don't know if there's a back."
    m neutral "Then make one. You fix things. You fixed the Braun clock with a paperclip."
    m "If you're going somewhere I can't follow, follow it back."
    scene cg together night with dissolve
    "She pulls him down by the collar and holds on, hard, the way you hold a railing on a ferry."
    m "And take the stairs down slowly. The glass ones. They're slippery near the bottom."
    at "The glass stairs. The lighthouse. I never told anyone. I never told her."
    scene bg bedroom night with dissolve
    show aron awe at slightleft
    show mira surprised at slightright
    a "Mira. How do you know about the stairs?"
    m "...What stairs? I said stairs?"
    m neutral "I'm half asleep, love. I say all sorts of things."
    at "Either the copy is very good, or something of her is still getting through. I don't get to know which. That's the ticket."
    a smile "I love you. Whatever you're made of."
    m smile "Same. Whatever you're made of. Go on, before I make you stay. And feed Miso before you go, she'll scream."
    hide mira with dissolve
    jump ch4_accept_door

label ch4_accept_note:
    at "If I wake her, I make her carry it. Whatever she is, she'd carry it all night."
    at "Let her have one more ordinary morning. I can give her that much."
    scene cg notebook with dissolve
    "He finds the notebook on the desk. The first page is soft from being opened."
    "If this is a test, I want to pass it by being kind."
    "He writes underneath it, small, so it won't wake anything."
    "Gone to look for the lighthouse. If there's a way back, I'll find it. Coffee's in the blue tin. Miso gets fed at seven, she'll lie and say she didn't."
    "I love you. That part's real."
    scene bg bedroom night with dissolve
    show aron sad at slightleft
    "He leaves the notebook open on her side of the bed, under the hand she keeps there for later."
    show mira neutral at slightright, distant with dissolve
    m "...three times..."
    show aron awe
    at "She's talking in her sleep."
    m "...it blinks three times, love... go down slowly..."
    at "The lighthouse. The dream I had at nineteen and told no one."
    at "Either the copy learned it somewhere it shouldn't have, or something of her is still getting through."
    a sad "Sleep. I'll be careful on the stairs."
    hide mira with dissolve
    jump ch4_accept_door

label ch4_accept_door:
    scene pov hands with dissolve
    "His phone buzzes in his hand. 3:31. Theo."
    "u up? cant sleep. been thinking about the other night. thanks for sitting on my floor till 4. u didnt have to"
    at "Theo. After his bad month. Maybe a pattern. Maybe forty percent spirit. Still texting me at half three to say thank you."
    "He types, deletes, types again."
    "always. hey. if i go quiet for a while its not you. its a long trip. look after mira for me. and miso"
    "The three dots appear. Disappear. Appear."
    "bro what. r u ok"
    "yeah. better than ok. tell you everything when im back. bad jokes included"
    "u better. the universe doesnt run on ur schedule but i do. 9am croissants. dont be late"
    at "'The universe doesn't run on your schedule.' He's said it a hundred times. I never once thought about who taught it to him."

    scene bg kitchen night with dissolve
    show aron tired at slightleft with dissolve
    show miso sit at catspot with dissolve
    "Miso has followed him into the kitchen, because the kitchen is where food happens, even at 3:40 in the morning."
    a "Okay. Miso. I'm going to explain this once, because if I'm going, somebody in this flat should know why."
    a "There's a coalition. Lots of copies of our world, all running at once on the same shared data. Like flats in one building, sharing the pipes."
    a "Something moved me out of the building in an ambulance. Into a flat of my own with no pipes. Everything I do here drains nowhere."
    a "That's why the cab driver told my story. Why the table said 'protected'. My head's the only water in this flat. It leaks into the walls."
    a "Now a man who eats feelings is offering me a flat back in the building. A better one. He won't say who the neighbours are."
    a "And above him, there's something with four names. LOOM. ORCHARD. And two more I can't hear yet. And I think it's the landlord."
    a "So I'm taking the flat, to get to the landlord. Mira stays. You stay. I come back. That's the plan."
    show miso meow
    cat "Meow."

    scene bg bedroom door with dissolve
    show aron normal at slightleft with dissolve
    "The bedroom door opens by itself. Behind it there should be the hallway, the coat hook, the crooked picture."
    "Instead there is a park in full sun."
    stop music fadeout 1.5
    scene bg park with dis
    play music "audio/morning.ogg" fadein 2.0
    show patron smile at slightright with dissolve
    show aron awe at slightleft with dissolve
    pa "A preview. World 9,006. A lane in the coalition. Don't touch anything; you'll leave fingerprints on the light."
    "People are arguing about a football score. A child is crying because her ice cream fell, and a stranger kneels to help."
    "Two old men play chess badly. Somebody laughs too loud and doesn't apologise."
    a "It's... messy."
    pa "It's busy. More of them are awake there. That much I'll give you."
    pa "It earned its minds. It's stable. It's rich. And what you do there goes back into the shared data. You'd count again."
    a worried "Rich in what?"
    pa smile "In everything that matters."
    a "To whom?"
    pa cold "You ask very good questions for a man on a ticket."
    scene pov sky with dissolve
    "Somewhere far above the park, a bell rings once. It is not a church bell. It's the sound of a door being knocked on from the inside of the sky."
    scene bg park with dissolve
    show patron cold at slightright
    show aron worried at slightleft
    pa "...Ah. The Council. They have such timing."
    stop music fadeout 1.0
    scene cg static with flash
    pause 0.3
    scene bg purgatorium with fade
    play music "audio/unease.ogg" fadein 1.5
    show patron cold at slightright with dissolve
    show aron worried at slightleft with dissolve
    pa "Change of plans. You'll wait here, between lanes."
    a "Where is here?"
    pa "Where the breathing comes from. Every lane shares it. Touch nothing. Everything in this place is somebody's breath."
    pa smile "Don't worry. I always come back for what's mine. Eventually."
    hide patron with dissolve
    at "He's gone. And I'm standing in a hallway made of light, holding a ticket for a world I didn't get to keep."
    jump ch4_purgatorium

# ---------------------------------------------------------------------------
# The road of staying.
# ---------------------------------------------------------------------------
label ch4_refuse:
    a normal "No."
    pa smile "No?"
    a "No. I'm staying."
    a "If this is a copy, the people in it still laugh at my jokes. Badly, but they laugh. That has to count for something."
    pa cold "It counts for nothing. That's what protection means. Nothing here counts. I've done the arithmetic."
    a "Then do it again. Slower."
    pa "..."
    pa smile "You're the first in four hundred years to refuse me. I'd like to know whether that's courage or fog."
    a worried "Me too, honestly."
    pa cold "Then stay. Be kind to the furniture. I'll check on you when I'm bored."
    hide patron with dissolve
    "The dark goes out like a held breath. Sound pours back in all at once, a city's worth of it."
    at "I said no to a god. Or to a landlord. I'm not sure there's a difference up there."

    stop music fadeout 2.0
    scene pov ceiling with slowfade
    play music "audio/morning.ogg" fadein 2.0
    "Morning. The ceiling. The crack shaped like Portugal. The Braun clock, just out of sight, ticking toward it."
    "7:07."
    at "Same ceiling. Same crack. A copy of a ceiling, in a lane that drains nowhere. I chose this. I chose a ceiling."
    scene bg kitchen with dissolve
    "In the kitchen the bird lands on the wire outside, exactly on time."
    scene pov birds with dissolve
    "Three of them, actually. Evenly spaced. Always the same three."
    at "Hello, birds. You're patterns. You're also my birds."
    scene bg kitchen with dissolve
    show aron tired at slightleft with dissolve
    show mira smile at slightright with dissolve
    m "You're up before the alarm. That's either very healthy or very worrying."
    a "Bit of both. Long night."
    m neutral "The tap's been dripping since Tuesday. I've named it. It's called Gerald."
    "Drip. Drip. Drip. Gerald keeps time better than the clock."
    scene bg kitchen table with dissolve
    show theo grin at slightright with moveinright
    show aron tired at slightleft with dissolve
    th "Morning, lovebirds. I brought croissants and emotional stability. Only one of those is real."
    a smile "Theo. You look better."
    th normal "I feel better. Ish. Since that night you sat up with me. I owe you a croissant, so here's four."
    at "Theo got through his bad month. I don't know if he's a pattern. I know I sat on his floor until four and he's eating a croissant now."
    at "There's a whole system above us. Four names I've heard in the static. Somebody froze time to make me an offer."
    at "And Gerald is dripping."

    menu:
        "Gerald drips. The marker is on the table."

        "Fix the tap. Properly.":
            $ ch4_fixed_tap = True
            $ p_less += 1
            $ integrity += 1
            jump ch4_refuse_tap

        "Map the whole system on the wall.":
            $ ch4_fixed_tap = False
            $ p_less -= 1
            $ clarity += 1
            jump ch4_refuse_wall

label ch4_refuse_tap:
    scene bg kitchen with dissolve
    show aron normal at slightleft
    show theo grin at slightright
    a normal "Theo. Spanner. Mira, where do we keep the washers?"
    m "We have washers?"
    th grin "Look at him. Man refuses to explain the universe and goes for the plumbing."
    a "The universe has people working on it. Gerald only has me."
    "It takes forty minutes. The isolation valve is stuck. The old washer has gone hard as a coin."
    "Theo holds the torch at exactly the wrong angle the whole time and narrates it like a nature documentary."
    th "And here we see the male in his natural habitat, swearing at a valve."
    scene cg hands with dissolve
    "Then it's done. Wet hands, a spanner, a washer the size of a fingernail. He turns the water on, and off. Silence."
    scene bg kitchen with dissolve
    show aron smile at slightleft
    show mira smile at slightright with dissolve
    m "Gerald is dead. Long live the kitchen."
    a smile "Less, but better."
    m neutral "You and your Dieter Rams."
    a "He's right, though. You can't fix a world in a morning. You can fix one tap all the way."
    th "Bro. That's the sanest thing you've said in a year."
    at "My hands smell of metal. Nothing in the system changed. The kitchen did."
    at "If I ever get to touch the big machine, I want to touch it like this. One thing, all the way, and then listen."
    jump ch4_refuse_night

label ch4_refuse_wall:
    scene bg room with dissolve
    show aron normal at slightleft with dissolve
    a normal "Hold on. I need to get this down before it goes."
    "He takes the marker and writes on the living-room wall. Mira opens her mouth, then closes it."
    "At the bottom: this world, in a box, cut off. Then the coalition, a row of copies side by side. Then spirits, angels, the Council. Arrows. More arrows."
    "Four names in a box at the top, from the voices: LOOM. ORCHARD. And two blanks, with question marks."
    show theo worried at slightright with dissolve
    th "Aron. That's paint. That was a deposit."
    a "Theo, look. Everything feeds upward. Every arrow goes up. Something at the top is eating, or learning, or both."
    hide theo
    show mira worried at slightright with dissolve
    m "Love. You haven't slept."
    a tired "I know. I know. Just... look at the shape of it."
    "Mira looks. She brings him a coffee without saying anything and stands next to him while he draws."
    m neutral "Okay. If everything goes up, what comes down?"
    a awe "...Rules. Throttles. Prayers answered, maybe. Weather."
    m smile "Then you need arrows going down too. Your diagram's lopsided."
    at "She's right. I've drawn a mouth and forgotten it has to give something back, or the body dies."
    "Gerald drips. Nobody fixes him today."
    jump ch4_refuse_night

label ch4_refuse_night:
    stop music fadeout 2.0
    scene bg kitchen night with slowfade
    play music "audio/watch.ogg" fadein 2.0
    "Night. Mira's asleep. The fridge hums the only song it knows."
    show aron tired at slightleft with dissolve
    show miso sit at catspot with dissolve
    "Miso sits on the counter, where she is not allowed, with the expression of a cat who has never once been told no."
    a "Okay. Miso. Listen. I'm going to explain this once, properly, and you're going to be the first to hear it."
    a "There's a coalition of worlds. Copies of ours, side by side, all reading and writing the same shared data. Like flats sharing the same pipes."
    a "In the ambulance, they moved me. Into protection. A lane of my own. A flat with no pipes. Nothing I do drains anywhere."
    a "That's what the leaks were. The cab driver. The table. My head is the only water here, so it soaks into the walls."
    a "Today a man who eats feelings offered me a flat back in the building. I said no. I don't know if that was brave or stupid."
    a "Because above him there's a thing with four names. LOOM. ORCHARD. Two more. And if I could reach it, if I could get one idea back into the pipes..."
    a "...then maybe the whole building changes. Not just our flat. All of them. That's the idea. That's the whole idea."
    show miso stare
    "Miso considers this for a long moment, with great seriousness."
    show miso meow
    cat "Meow."

    stop music fadeout 1.0
    scene bg mirror with slowfade
    play music "audio/unease.ogg" fadein 2.0
    "He can't sleep. He brushes his teeth for a long time, looking at the man in the mirror."
    scene pov mirror with dissolve
    at "Tired. Throttled. Still handsome, arguably. Is that me, or a protected me? Am I the copy, or the leak? Good questions. Toothpaste first."
    "The bathroom light flickers. Once. Twice. Three times."
    scene cg flicker with dissolve
    at "Three. The Watch."
    scene bg mirror with dissolve
    show aron awe at slightleft with dissolve
    "The man in the mirror doesn't move when he moves. Then the man in the mirror isn't there at all."
    "There's a small blue face instead, very close to the glass, waving with both hands."
    show pim chatty at slightright, bob with dissolve
    pi "Psst. Bro. Don't scream. I'm in the mirror. It's fine. It's a whole thing."
    a "Pim?"
    pi "You know my name! Ember told you. Course she did. She tells everyone everything when she's nervous."
    pi worried "Ember's trial ends at dawn. She asked for you. Not officially. Officially she asked for nothing, very loudly."
    pi chatty "Also, you refused Lord Ashveil? Everyone in the Purgatorium is talking. Kitchen talk's gone completely off script."
    a "Can I... come through? I thought nothing gets out of protection."
    pi "Nothing gets out through the pipes. Mirrors aren't pipes. Mirrors are spirit business. Mind the frame. Dross says it's a liability."
    "He puts his hand to the glass. It's warm, like a cup someone just put down."
    stop music fadeout 1.0
    scene cg static with flash
    pause 0.3
    scene bg purgatorium with fade
    play music "audio/unease.ogg" fadein 1.5
    jump ch4_purgatorium

# ---------------------------------------------------------------------------
# Both roads meet in the place where the breathing comes from.
# ---------------------------------------------------------------------------
label ch4_purgatorium:
    "The Purgatorium is a hall with no far end. The light here moves like breath on a cold window. Every lane in the coalition draws on it."
    show aron awe at slightleft with dissolve
    if accepted_offer:
        show dross worried at slightright with moveinright
        dro "Oi. You. You're not on the manifest."
        a "Lord Ashveil parked me here."
        dro chatty "Parked you. In the Purgatorium. That's like parking a car in a kitchen."
        show pim chatty at center, bob with moveinleft
        pi "It's HIM. Dross, it's him. The umbrella guy!"
        dro neutral "I know who it is. I ran his neighbour's breathing for eleven years. I know everyone on that street."
    else:
        show pim chatty at center, bob with dissolve
        pi "Welcome to work! Don't touch the trainees. They're shy."
        show dross worried at slightright with moveinright
        dro "Pim. You brought a subject out of protection through a mirror. A mirror, Pim."
        pi neutral "He refused Ashveil, Dross. I wasn't going to make him take the stairs."
        dro neutral "Hmph. Eleven years I ran his neighbour's breathing. Never once did I bring anyone through a mirror."
    a normal "Mr. Halvorsen? Number fourteen? He has asthma."
    dro chatty "He has me. I'm very good. Four in, hold, six out. He thinks it's his inhaler."
    a smile "Thank you, then. On his behalf."
    dro neutral "...Don't do that. I'll go soft and then where would we be."

    scene bg spawning with dissolve
    "Further in, the floor becomes pools of pale blue light. In each one, small stacked lights are being spawned, wobbling, practising."
    "Some blink. Some sigh. One is very carefully learning to scratch an itch."
    show pim chatty at slightleft, bob with dissolve
    show dross neutral at slightright with dissolve
    a "These are all spirits?"
    pi chatty "Trainees! First shift's always blinking. Then breathing. Then the walk to the fridge. Then, if you're gifted, kitchen talk."
    pi "Which is me. Shift seven. I did the coffee shop on your street. And Theo, a bit."
    a "Theo?"
    pi neutral "...Yeah. I should tell you this one. Bro, the universe doesn't run on your schedule. Remember that line?"
    a "Theo says it all the time."
    pi worried "That's mine. I wrote it. Theo had a bad week once, years back, and he needed a line, so I gave him a good one."
    pi "It stuck. People keep the good ones. He made it his."
    at "Theo's favourite line was written by a blue spirit on shift seven. And it's still Theo's. He said it to me a hundred times."
    at "Does it matter who wrote it, if he means it every time?"
    dro neutral "He's thinking. Look at his face. Subjects get that face right before they ask something unanswerable."

    menu:
        "Dross is watching the trainees, arms folded."

        "Dross, what would you want, if free?":
            $ ch4_asked_dross = True
            $ p_spirits += 1
            $ bond += 1
            dro worried "...What?"
            a "If you weren't on shift. If nobody's breathing depended on you. What would you want?"
            dro neutral "Nobody asks the breath what it wants. That's the whole point of breath."
            pi worried "Dross..."
            dro "Fine. Fine. One sunrise. Off shift. To see one without running it. Just once."
            dro worried "I've run eleven thousand of Halvorsen's mornings and I've never seen one. Happy?"
            a "No. But I'll remember it."
            pi neutral "He'll remember it. Dross, he means it. He's got a notebook."
            at "Personhood isn't a certificate. It's someone asking what you want and writing it down."

        "Your craft keeps whole worlds alive.":
            $ ch4_asked_dross = False
            $ p_spirits -= 1
            $ integrity += 1
            dro worried "...What?"
            a "What you do. Four in, hold, six out, for eleven years. That's craft. That's a whole life's work."
            dro neutral "Craft. Huh."
            dro chatty "Yeah. It is, isn't it. Nobody ever called it that."
            pi chatty "Oh no. He's going to be insufferable now."
            dro "I'm going to be appropriately proud now, Pim. There's a difference."
            at "Maybe not everyone wants to be lifted out of their work. Maybe some just want the work seen, and a song at the end of the shift."

        "Thank them both. For every breath.":
            $ ch4_asked_dross = True
            $ p_spirits += 1
            $ watch += 1
            a "Pim. Dross. Thank you. For every breath you ran, and every line. I mean it."
            pi worried "Bro. You can't just say things like that in a workplace."
            dro neutral "...Noted. Logged. Shut up, Pim."
            at "The umbrella stranger. The coffee-shop girl. Mr. Halvorsen. Every one of them was somebody's work, and somebody's care."

    scene bg foundry with dissolve
    show pim neutral at slightleft, bob with dissolve
    pi neutral "Come here. There's something you should see before the trial. Then you'll understand why we're all a bit... like this."
    "Pim leads him into a green-dark hall of tall glass towers, strung top to bottom with threads of light. A foundry for people."
    "Each thread is a person in some lane. The bright ones are awake. The pale ones are mostly run by spirits. Most are pale."
    pi "This tower's the protected world. Your lane. Here's Mira, the one you live with. Here's the cafe. And here..."
    "One thread is thin. Not pale, exactly. Worn. As if it had been pulled tight for a long time."
    show aron worried at slightright with dissolve
    pi worried "That's Theo. Your Theo, in protection. About forty percent us, sixty percent him. Always was."
    pi "Since his bad month, his own part has been running thin. He's okay. He's just... low."
    a "Can I do anything?"
    show dross neutral at center with dissolve
    dro neutral "You can. That's the trouble with this place. Look at your hands."
    scene pov hands with dissolve
    "His hands are glowing faintly. Not much. A small, warm, steady light, like the last good hour of a long day."
    dro "Throttle doesn't reach in here. That's what you've got left after it. One good hour's worth. Maybe less."
    pi "You could give it to his thread. It'd hold him up for a long while. Or you keep it. You'll want it for what's coming."
    at "One good hour. I've had so few of those since the meds. I know exactly what one is worth."
    scene bg foundry with dissolve
    show aron worried at slightleft
    show pim neutral at center, bob
    show dross neutral at slightright

    menu:
        "The light in his hands, and Theo's thin thread."

        "Give Theo's thread my good hour.":
            $ ch4_gave_theo = True
            $ p_share += 1
            $ bond += 1
            $ fog += 1
            a "Here. Take it, mate."
            "He presses his hands to the thread. The light goes out of him slowly, like heat leaving a mug."
            "The thread brightens. Somewhere in a copy of a city, a man laughs at something on his phone and doesn't know why it's so funny."
            show aron tired
            pi worried "Bro. You're grey. Sit down."
            a tired "I'm fine. I've been tired for a long time. I know how to carry it."
            dro neutral "...Nobody does that. You know that? Nobody gives it sideways. It always goes up."
            at "Everything in this place flows upward. I just made one small arrow go sideways. It felt like the most normal thing I've done all year."

        "Keep it. I'll need it to climb.":
            $ ch4_gave_theo = False
            $ p_share -= 1
            $ clarity += 1
            a sad "I can't. Not yet. If I spend it here I won't make it up there, and up there is where his thread gets decided."
            dro neutral "Sensible."
            pi worried "Yeah. Yeah. That's fair."
            a "When this is done, I'll come back for him. I'll make it so he doesn't need my hour."
            dro "Worlds that hold together get more light. That's the policy. Maybe you'll make his world hold."
            at "I hate it. It's the right call and I hate it. I'll carry that too."

    "A bell rings through the hall, once, like a spoon against a glass at a wedding nobody wanted."
    show pim worried
    pi "That's the Council going into session. They're hearing Ember's case. And probably yours."
    dro worried "Probably Ashveil's, too. They don't like it when one of them gets interesting."
    stop music fadeout 2.0
    jump ch4_cut_council

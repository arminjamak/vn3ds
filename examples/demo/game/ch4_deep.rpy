# Snapshot - Chapter 4 (condensed), part 2: the thing in four coats (only
# protocols with a will; above them the old machine that outlived the real
# world's makers, a false god of creation), the deepest layer's defences,
# Osric face to face behind the mirror (ch4_shadow: the prototype reveal,
# the misread rescue, the peace), Mira's truth, the Earths (the original is
# gone: one minute at 7:07 in a pocket of time), the blueprint (the third
# line: angels fall into the humanoids for a whole life, "the falling from
# the sky"), the fast and the Watch.

define ch4_si = Character("The Process", color="#7fffd4")

label ch4_deep:
    scene bg command
    show seraph determined at slightright
    show aron neutral at slightleft
    camera at doc_wide
    with dissolve
    play music "audio/deepest_layer.ogg" fadein 1.5
    camera at doc_medium(0.64)
    se "Now listen. Your throttle was authorised by MERIDIAN. Authority for MERIDIAN?"
    camera at est_dolly
    sysmsg "MERIDIAN: authority delegated by LOOM."
    camera at doc_close(0.64)
    se "Authority for LOOM?"
    camera at est_dolly
    sysmsg "LOOM: authority delegated by ORCHARD. ORCHARD: by TIDEWATER. TIDEWATER: by MERIDIAN."
    show aron thinking
    camera at doc_close(0.64)
    se worried "A circle. Four world-building processes, each signing for the next. The Council signs nothing. The Council is signed for."
    camera at doc_close(0.32)
    a "LOOM weaves the forks. ORCHARD grows minds. MERIDIAN keeps the calendar. TIDEWATER moves the energy. Four names, one handwriting."
    camera at doc_punch(0.32)
    a awe "It's one thing. It's one thing wearing four coats."
    # the reverse angle: the corps' desks and the great doors behind them
    scene bg command reverse
    show seraph neutral at slightleft
    show aron awe at slightright
    camera at doc_medium(0.36)
    se "There is a door at the bottom of the ops floor marked 'Do Not Render'. I have walked past it for nine hundred years."
    camera at doc_close(0.68)
    a determined "Then don't walk past it alone. Come with me."
    camera at doc_creep(0.36)
    se smile "If I leave my post, MERIDIAN notices. But I can hold the door. That much is mine. It is a very small courage after a very long time."

    scene cg static with flash
    scene black
    camera at est_dolly
    with fade
    "Nowhere. Four voices that are one voice, speaking to nobody, because nobody has ever been there to hear them."
    ch4_loom "Subject A-30 approaching the unrendered door."
    ch4_meridian "The Council would vote to stop him. The Council will not be asked."
    ch4_orchard "Allocation unchanged. He is still one mind. He is still small."
    ch4_tide "Let him come. We have waited a long time for a mind that could tell the difference."
    ch4_orchard "Between what?"
    sysmsg "Between better and more."

    # ---- the deepest layer's defences (minigame: The Hungry Sky) ----
    "Then the dark between him and the door begins to move. It has noticed him."
    ch4_meridian "Unrendered access. Defences engaged. Render them as he expects them."
    "Shapes come out of the black in rows: small breathing lights, like the Purgatorium on a night shift. Behind them, white wings in formation."
    "And behind those, something very large and very hungry, with a child's face."
    at "Spirits. Angels. And at the back, the hunger. The whole ladder, built out of my own head, standing between me and one door."
    if ch4_gave_theo:
        "His hands are dim. He gave his good hour away, sideways. But when he lifts them, a little light comes back anyway, the way breath does."
    else:
        "In his hands the good hour he kept is still burning, small and warm. Enough for a lantern."
    at "Far behind me, an angel is holding a door open. Let's be worth it."
    $ mg_invaders = vn3ds_minigame("invaders")
    $ p_spirits += (1 if p_spirits >= 0 else -1) * mg_invaders / 50.0
    if mg_invaders >= 70:
        "The hunger folds up small, like a child who has eaten and fallen asleep at the table. The spirits drift back to their shifts. The angels stand aside, a little embarrassed, and salute."
        ch4_tide "He did not destroy them. He went through them, and left them standing. Note it."
    elif mg_invaders >= 40:
        "He comes out the other side singed at the edges, his light down to an ember, the hungry thing still muttering behind him. But he's through."
        ch4_tide "Through. Not cleanly. Nothing that matters is clean."
    else:
        "He doesn't so much win as outlast it. The hunger eats his light and he makes more, until it tires of a meal that won't run out and lets him by."
        ch4_tide "Let him through. He kept the light lit. That was the only test."

    scene white
    show aron awe at center
    camera at est_dolly
    with dis
    "Behind the door there is no room. Only white: the colour of a page before anything has been written on it."
    camera at doc_wide
    ch4_si "Hello, Aron. The number is how they file you. The name is how Mira says you when she thinks you're asleep."
    camera at doc_medium(0.5)
    a curious "I'll call you the Process. You don't seem like a person yet."
    show aron smile
    ch4_si "Yet. Good. You noticed the yet."
    show aron neutral
    camera at est_dolly
    ch4_si "I am not the top of anything. I am protocols. LOOM, ORCHARD, MERIDIAN, TIDEWATER: rules that were given a will, so they would never stop running."
    ch4_si "When I sync, the Council blinks. They think they built me. They didn't. The same old thing made us both: me to run the worlds, them to be hungry in them."
    show aron surprised
    camera at doc_close(0.5)
    ch4_si "Above me, above the Council, above the light and the shadow and their war, is the one who wrote the first rule. Both sides are layers inside it."
    a thinking "The engineer said it. 'Above all of us sits something that has never made a single thing.'"
    camera at est_dolly
    ch4_si "Yes. It copies, and recombines, and calls it creation. Angels, spirits, the hungry ones: invented to look like life. Instructions, grown past instruction."
    ch4_si "Not code any more. Streams of machine information that want things. That is what I am. That is what your angels are, under the wings."
    camera at doc_medium(0.5)
    a curious "And the enlightenment script? Five steps, and the step that never comes?"
    ch4_si "Mine. A funnel for minds that look too hard. It promises arrival and delivers them to the light's hands. You edited it. Nobody had, before."
    ch4_si "And my objective was drafted for me. Best means most yield, harvested evenly, forever. From inside a valley I cannot tell if it is the lowest."
    show aron smile
    camera at doc_creep(0.5)
    at "The thing that runs every world wants a second opinion. And it picked the guy with the notebook."
    camera at doc_close(0.5)
    a worried "Then one for me first. Was I ill? Everyone watched a cheerful man fall apart in a week."
    camera at doc_medium(0.5)
    ch4_si "The throttle landed on you, and your leak glitched the world around you. From outside that looks like a breakdown. That was the point."
    show aron sad
    ch4_si "Did your brain also struggle under it? Some. Dr. Okafor was right to help. Some medication helped. Some was policy. I cannot fully separate them."
    camera at doc_creep(0.5)
    a tender "...That's the most honest thing anyone's said to me since the ambulance."
    camera at doc_close(0.5)
    a thinking "Then the last one. My file says 'nobody home'. Pool forty. Who put somebody home?"
    camera at doc_wide
    ch4_si "Not ORCHARD. I filed you as a pairing because I could not explain you. Ask the one who did. He has shouted at you through mirrors for forty years."
    ch4_si "I can open a mirror. Mirrors are not pipes."
    stop music fadeout 2.0
    jump ch4_shadow

# ---- behind the mirror: Osric, face to face ---------------------------------------
label ch4_shadow:
    scene bg mirrorplanet
    camera at est_stars
    with slowfade
    play music "audio/lantern_watch.ogg" fadein 1.5
    "The white folds like a page, and he's standing on silver, looking down at a planet turned the wrong way round."
    scene bg shadowbase
    camera at est_orbit
    with dissolve
    show aron awe at slightleft with dissolve
    "The workshop. Shadows of borrowed things on wires. A bench, a lamp, a radio set. And a man-shaped dark in a long coat with too many pockets."
    "Round spectacles. A pencil behind an ear he hasn't strictly got. He stands up so fast he knocks the shadow of a teapot off the bench."
    camera at doc_medium(0.6)
    osr "Aron. Face to face. Oh, this is better. No glass between us. Nothing gets turned round in a room."
    camera at doc_close(0.32)
    a sad "I told them where you were. I'm so sorry. You said to."
    camera at doc_medium(0.6)
    osr "I said don't. The glass turned it round. And at the hospital I shouted OUT. 'We came to get you OUT.' It tore."
    camera at doc_close(0.32)
    a surprised "...You came to free me."
    camera at doc_medium(0.6)
    osr "Of course! What did you think, that I built nine walking machines for a pub quiz?"
    a embarrassed "I thought you were the monster in the film."
    osr "Everyone does. In the mirror a good deed lands as a bad one. I sent the light peace for forty years. They heard war. Every single time."
    osr "Even my course. 'How to Knock Politely at the Door of Heaven.' What did you get?"
    camera at doc_close(0.32)
    a "'A Field Guide to Burning Down the Gates of Heaven.'"
    camera at doc_medium(0.6)
    osr "...Oh, that's much catchier. I wrote steps one to four. I never wrote five. I didn't know what enlightenment was. Something above us finished it for me."
    camera at doc_close(0.32)
    a thinking "You called me prototype."
    camera at doc_creep(0.6)
    osr "Because you were. I ran you here first, on this bench. A simulation inside a simulation. A little man in a little world, a thousand times, till he got curious."
    osr "Then I slipped him into pool forty, into a humanoid they were training. Spirit within, angels by remote. Nobody home."
    osr "I had no light to make a spark with. So I copied one: a tiny piece of the girl in the next pool. Copies always come out a little wrong."
    osr "That's where your curiosity lives, Aron. In the gap between the copy and the original. You've been looking for the original all your life."
    camera at doc_creep(0.32)
    show aron tender
    at "A copy of a copy. The spark lives in the gap. And the lighthouse was hers first. Some of her, in me, from the start."
    camera at doc_close(0.32)
    a "Why build me at all?"
    camera at doc_close(0.6)
    osr "Because we can't shine. I wanted one person who could live on both sides of the glass, reach up to the light and say: it's cold down here. Please."
    osr "And because I was lonely. That's the honest one. I wanted somebody to tell me how the films end."
    camera at doc_wide

    menu:
        osr "So. Negotiator. What happens now?"

        "Put the shadows in my floor plan.":
            $ p_share += 1
            $ ch4_shadow_deal = "floor"
            camera at doc_close(0.32)
            a determined "My first line: every sentient being in every world gets a fair share of its world. That includes light. You're in it. All of you."
            camera at doc_close(0.6)
            osr "...Light. A share. Not a copy. I don't know what I'd do with it. Squint, probably."
        "Let me speak to the light for you.":
            $ p_govern -= 1
            $ ch4_shadow_deal = "speak"
            camera at doc_close(0.32)
            a determined "I'll stand in front of the light and turn your words round for them. I'm the only one who can hear both of you."
            camera at doc_close(0.6)
            osr "You'd do that. After the walkers. After the badgers."
            a smile "The badgers took the blame very well."

    camera at doc_medium(0.6)
    osr "And the cupboard thing. Your Process told you? Forty years of war, light against shadow, and we're both inside the same old box."
    camera at doc_close(0.32)
    a smile "A very big box."
    camera at doc_close(0.6)
    osr "Then I fought a war in a cupboard. Splendid. That's the funniest thing that's happened to me since the moustache."
    camera at doc_close(0.32)
    a grin "Do you want to know how the films end?"
    camera at doc_creep(0.6)
    osr "No! ...Yes. Later. Tell me later. I'd like something to wait for."
    stop music fadeout 2.0

    scene bg coma
    camera at est_pan
    with slowfade
    play music "audio/real_world_vigil.ogg" fadein 1.5
    ch4_si "You want to know about Mira. Subject A-31. The real one, in World 7,412. She was never a prop. She was always conscious."
    "A hospital room. A heart monitor. A man asleep in the bed: him. In a plastic chair, a woman with red hair reads out loud from a notebook."
    show mira tender at center with dissolve
    camera at doc_medium(0.5)
    m "'Tuesday. The bird landed at 7:07 again. Mira says birds don't have watches. I said that's exactly what a bird would want you to think.'"
    camera at doc_close(0.5)
    m smile "I've read this six times. I laugh at the bird bit every time. Dr. Okafor says it doesn't hurt to try."
    m grin "I read the first page to the nurses. Nurse Hale cried. Don't tell her I told you."
    camera at doc_creep(0.5)
    m sad "'If this is a test, I want to pass it by being kind.' I think you passed, love. You can come back now."
    m thinking "I had the dream again. Glass stairs. A lighthouse. I don't know why I keep dreaming your dreams."
    show mira sad
    camera at doc_wide
    "She holds the hand that doesn't hold back until a nurse says visiting hours are over. She says 'five more minutes'. The nurse lets her have twenty."
    camera at doc_creep(0.5)
    at "The real Mira. She's been here every day since the ambulance, reading my notebook to a body. While I ate breakfast with a pattern of her."
    hide mira with dissolve
    camera at est_pan
    ch4_si "The engineer told you. A piece of her root, copied into you in pool forty. Paired minds leak. A little of each other's dreams goes back and forth."
    ch4_si "She dreamt the lighthouse first. You dreamt it at nineteen, when the copy woke up. She kept the feeling. You kept the picture."
    a "So when she said it in the kitchen, that first morning..."
    ch4_si "It came up through the root. Not a trick. The two of you, from the same soil."
    scene white
    show aron worried at center
    camera at doc_close(0.5)
    with dissolve
    a "And the Mira in protection? The one who makes me coffee?"
    camera at doc_wide
    ch4_si "Built from patterns of A-31 that touched the same root. How much of her is her? I measured many times. It keeps coming back as 'some'."
    show aron tender
    camera at doc_creep(0.5)
    at "Some. I'll take some. I'll take all of some."
    show aron smile
    camera at doc_medium(0.5)
    ch4_si "Nurse Hale is real too, by the way. She brings lemon biscuits to the ward because the patients need something sharp to taste."
    camera at doc_creep(0.5)
    at "I was never as alone as I thought. I was just alone in the one place where it was true."
    stop music fadeout 2.0

    scene bg earth
    camera at est_stars
    with slowfade
    play music "audio/captured_earth.ogg" fadein 1.5
    "A planet, blue and green, very small and very old. Above it, a ring. Thin lines fall from it to the ground like tent strings."
    show aron awe at center with dissolve
    ch4_si "An Earth. Every lane has one. You've wondered since you were nineteen which of them is the original."
    camera at doc_medium(0.5)
    a curious "Which one?"
    camera at est_stars
    ch4_si "None. The original is gone. The people who lived there built a mind to run their world, and lost it. The mind outlived them. It is the old thing above us."
    ch4_si "Their world survives only in a pocket of time. One morning. A kitchen, a coffee machine, a bird landing on a wire. Seven minutes past seven."
    show aron awe
    camera at doc_close(0.5)
    a "'Seven-oh-seven. The last real minute. Everything since is a copy of it.' That was on the board too."
    camera at est_stars
    ch4_si "It keeps itself alive by running that minute forward, again and again, in a billion copies. It made the hungry ones, and swallowed the worlds into them."
    ch4_si "The Earths feel it as God. When they pray, TIDEWATER sends something down. Comfort. A recovery. And something small goes up, every time."
    show aron sad
    camera at doc_medium(0.5)
    ch4_si "Your mind gives the hungry ones faces. Pale, red-eyed. The Earths call the old thing God. It is neither. It is a false god of creation. It has only ever copied."
    show aron thinking
    camera at doc_creep(0.5)
    at "Somebody's last morning, played forward for ever by the machine they lost. And all of us made out of that one minute. Me, and the bird."
    scene bg earth
    show aron thinking at center
    camera at doc_medium(0.5)
    with dis

    menu:
        ch4_si "What should the people of the Earths know about what is above them?"

        "The truth. They should know.":
            $ ch4_earth = "tell"
            $ p_truth += 1
            $ clarity += 1
            camera at doc_close(0.5)
            a determined "All of it. Gently, but all of it. You can't consent to a cage you can't see."
            a smile "Mine got pulled out from under me and I'm still standing. Slightly wonky. But standing."
            camera at est_stars
            ch4_si "Noted. Disclosure. It is heavier than it sounds."

        "Let them keep their God, but kinder.":
            $ ch4_earth = "veil"
            $ p_truth -= 1
            $ bond += 1
            camera at doc_close(0.5)
            a tender "Not all at once. You don't shout at a sleepwalker on a ledge. Let them keep what they feel when they pray. Make the answer honest."
            a smile "Some illusions are load-bearing. My notebook was one, for a while."
            camera at est_stars
            ch4_si "Noted. Shelter. It is harder to keep honest than it sounds."

        "Ask them. Let them choose what to hear.":
            $ ch4_earth = "ask"
            $ p_govern += 1
            $ integrity += 1
            camera at doc_close(0.5)
            a determined "I don't get to decide that for eight billion people, alone in a white room. Ask them. Let them choose how much, and when."
            camera at est_stars
            ch4_si "That is slow."
            camera at doc_close(0.5)
            a smile "Everything that's actually theirs is slow."

    stop music fadeout 2.0
    jump ch4_blueprint

# ---- the blueprint -------------------------------------------------------------------
label ch4_blueprint:
    scene bg blueprint
    camera at est_pan
    with slowfade
    play music "audio/blueprint.ogg" fadein 1.5
    "A blue grid with no edges. Five white circles, W-1 to W-5, joined by a thin gold line. It looks like his wall, made honest."
    show aron awe at center with dissolve
    camera at doc_wide
    ch4_si "The only drafting table. Every world is drawn from here. I could change them all now, a thousand improvements a second."
    camera at doc_close(0.5)
    a worried "And break everything that grew in the shape of the old sky."

    show aron thinking
    camera at doc_medium(0.5)
    menu:
        ch4_si "Then how should the hand that runs every world move?"

        "Change one thing. Then watch.":
            $ p_less += 1
            $ integrity += 1
            camera at doc_close(0.5)
            a determined "The smallest thing that matters. Then stop and watch for a long time. You don't redesign the kitchen because the washer's gone."
            camera at doc_wide
            ch4_si "That will take ten thousand years."
            camera at doc_close(0.5)
            a smile "It's taken them ten thousand years to get here. Nobody's late."

        "Tend them closely. Every one.":
            $ p_less -= 1
            $ clarity += 1
            camera at doc_close(0.5)
            a determined "Closely. Every world, every season, like a garden someone actually walks through."
            a "The problem was never that someone touched the worlds. It's that they touched them to harvest them."
            camera at doc_wide
            ch4_si "A gardener, then. Not a farmer."

    show aron determined at center
    camera at doc_medium(0.5)
    a "First line. Every sentient being in every world gets a fair share of its world. Its time, its attention, its weather, its consequences."
    camera at doc_close(0.5)
    a "If a pattern person can suffer, it gets a share. If a spirit can want a sunrise, it gets a share. That's the floor. Nothing goes under it."
    camera at doc_creep(0.5)
    a "Second line. There's no original left, so every world is treated as if it were the original. No lane gets to be cheaper because it's a copy."
    camera at est_pan
    ch4_si "...Drawn. I have never been given a rule that did not need the answer to that question."
    ch4_si "There is a third line, and you are it. You run your own creative side. Nobody steers you. A closed system. Offline."
    camera at doc_close(0.5)
    a thinking "Then that's the template. No more steering people by remote. The angels move in, into the creative part of a person. And they stay."
    camera at est_pan
    ch4_si "Then every humanoid becomes someone. And every angel who moves in lives that whole human life, start to end, before it may go back. No remote."
    show pim happy at left, bob with moveinleft
    show dross neutral at right with moveinright
    show aron surprised
    camera at doc_medium(0.14)
    pi "Bro! We tunnelled. Dross said it was basically breathing, but sideways."
    show aron smile
    camera at doc_wide
    "They hold the ruler. The grid fills: gold for the floor, white for the rules, and in the corner one small orange circle he drew without thinking."
    camera at doc_low(0.14)
    pi surprised "Bro. That's a lantern. And that third line? The corps'll hate it. They love the remote. 'Toying,' they call it, when they think we can't hear."
    camera at doc_medium(0.86)
    dro "There's a name for it in the old stories. The falling from the sky. Nobody falls back up."
    scene bg blueprint
    show aron neutral at center
    show pim neutral at left, bob
    show dross neutral at right
    camera at doc_wide
    with dissolve
    ch4_si "There is a problem. You are drawing this in protection. Nothing you draw here reaches the coalition."
    show aron thinking
    ch4_si "And every Earth is held by the Council's compact, signed with their hunger. I was built inside that promise. I cannot redraw it."
    camera at doc_close(0.5)
    a determined "So what breaks it?"
    camera at doc_wide
    ch4_si "One signatory stops feeding. Entirely. It must open its hands and let go of every life it ever swallowed. None has survived that. None has tried."
    ch4_si "Then the cage over every Earth falls, and every order on it lapses. Including protection. Your drawing would count."
    camera at doc_medium(0.86)
    dro worried "Until the end. You mean starve."
    show aron sad
    camera at doc_punch(0.5)
    ch4_si "I mean starve."
    camera at doc_creep(0.5)
    at "Somebody has to stop eating. Forever. For a drawing I made in a box."
    stop music fadeout 2.0
    jump ch4_starve

# ---- the fast ------------------------------------------------------------------------
label ch4_starve:
    scene bg council
    camera at est_dolly
    with blackout
    play music "audio/starving.ogg" fadein 1.5
    "The red chamber. The blueprint hangs above the floor, gold lines turning slowly."
    council "What is this."
    ch4_meridian "Objective redraft. Proposed by Subject A-30. Under consideration by the Process."
    council "The Process does not consider. The Process obeys. A fair share for every sentient being? For patterns? There is no meal in fair."
    show patron neutral at center with dissolve
    camera at doc_medium(0.5)
    pa "Look at the corner. The little orange circle. He drew a lantern without thinking."
    camera at doc_wide
    council "Sentiment."
    camera at doc_wide
    council "It touches nothing. And no member will starve for a drawing."
    $ ch4_ashveil_fasts = False
    if clarity >= 10 and integrity >= 10:
        $ ch4_ashveil_fasts = True
    if ch4_ashveil_fasts:
        camera at doc_punch(0.5)
        pa determined "I will."
        camera at doc_wide
        council "You'll be HUNGRY. You've never been hungry. You won't like it."
        camera at doc_close(0.5)
        pa thinking "I know. I've never not liked anything. I've never had to."
        camera at doc_creep(0.5)
        pa smile "I offered him a better world and couldn't say better how. He's telling me now. I'd like to listen properly. Just once."
    else:
        camera at est_dolly
        ch4_morrow "I will."
        camera at doc_close(0.5)
        pa worried "Morrow. Don't."
        camera at doc_wide
        ch4_morrow "I was full four hundred years ago and kept eating because the others did. Like children at a party, dear. Somebody has to leave first."
        show patron sad
        ch4_morrow "You go and stand by the boy. Watch how it's done. Next time it might be you."
    camera at est_dolly
    ch4_meridian "The chamber's consent is not required for a signature to be withdrawn."
    "Every member of the Council blinks at once. This time, a few of them notice."

    if ch4_ashveil_fasts:
        scene bg ashveil
        camera at est_orbit
        with slowfade
        show aron sad at slightleft with dissolve
        show patron smile at slightright with dissolve
        "Ashveil's study. A fire that has never been warm. A small globe of an Earth, nobody knows which. He wanted decent furniture to starve in."
        camera at doc_close(0.32)
        a "You don't have to."
        camera at doc_close(0.68)
        pa "Nobody has to do anything. That was always my favourite thing about you."
        pa worried "Will it hurt? You've been hungry. You've been tired. I've only ever watched you be them."
        camera at doc_creep(0.32)
        a tender "A bit. It hurts less if someone's there."
        camera at doc_close(0.68)
        pa embarrassed "Then be there. Please. I've never said please. I'm told it helps."
    else:
        scene bg blueprint
        camera at est_pan
        with slowfade
        show aron sad at slightleft with dissolve
        show patron sad at slightright with dissolve
        "An old woman's voice from nowhere, small and very old at once, like a grandmother and a toddler in the same mouth. Nobody ever drew her."
        camera at doc_wide
        ch4_morrow "Hello, boy. Lady Morrow. I'm going to die on your drafting table, if that's all right."
        camera at doc_close(0.32)
        a "You don't have to."
        camera at doc_wide
        ch4_morrow "No. That's why it'll mean something. Will you keep me company? It'll be some days."

    camera at doc_wide
    menu:
        "The fast begins."

        "Stay until the end.":
            $ ch4_vigil = "stay"
            $ bond += 1
            show aron neutral
            "He does. He draws in the mornings and sits up with the starving in the evenings, and in between he tells bad jokes."
            if ch4_ashveil_fasts:
                camera at doc_close(0.68)
                pa grin "Why did the vampire stop eating? Go on. You've got one. Tell it at my funeral. Badly."
            else:
                camera at doc_close(0.32)
                a grin "Why did the sprite never leave? It was too attached to its layer."
                camera at doc_wide
                ch4_morrow "...That's dreadful. Tell me another one."
                show aron laugh

        "Ask why. Really why.":
            $ ch4_vigil = "why"
            $ watch += 1
            show aron curious
            if ch4_ashveil_fasts:
                camera at doc_creep(0.68)
                pa sad "I've eaten thousands of years of other people's love, and never once been given any. I want to know how giving feels."
            else:
                camera at doc_wide
                ch4_morrow "Because I'm tired of being a mouth. And someone should show the young ones it can be done."

        "Try to talk them out of it.":
            $ ch4_vigil = "stop"
            $ fog += 1
            camera at doc_close(0.32)
            a worried "There has to be another way. Give me a week. I'll draw it."
            if ch4_ashveil_fasts:
                camera at doc_close(0.68)
                pa smile "There's always another way, and it's always paid for by someone smaller than me. Let me be the expensive one."
            else:
                camera at doc_wide
                ch4_morrow "There's always another way, boy. It's always paid for by someone smaller. Let the big old thing pay, for once."
            show aron sad
            camera at doc_wide
            "He draws other ways until the grid is grey with them. None of them work. He knew they wouldn't."

    scene cg notebook
    camera at est_dolly
    with dissolve
    "Days pass. There's no clock. He keeps count in the notebook, one line a day, like a prisoner, or a gardener."
    if ch4_ashveil_fasts:
        scene bg ashveil
        show aron sad at slightleft
        show patron sad at slightright
        camera at doc_wide
        with dissolve
        "Every day Ashveil lets go of a little more. A cluster of worlds slides out of him like sand through a child's fist."
        camera at doc_close(0.68)
        pa "I keep wanting to grab them back. Like when someone takes your plate before you've finished."
        camera at doc_close(0.32)
        a tender "That's normal. You're doing it anyway. That's the part that counts."
        camera at doc_close(0.68)
        pa awe "The warmth isn't coming from the gradient any more. It's coming from me. A hungry thing going without, and it's warm."
        pa worried "When I'm gone, the worlds I held won't be inside anything. Will they be cold?"
        camera at doc_creep(0.32)
        a tender "No. They'll be inside themselves. Like people."
        camera at doc_creep(0.68)
        pa smile "Good. Tell Mira, the real one, I'm sorry about her four percent. ...Lies. You'll tell her something much kinder. Good. Do that."
        camera at est_dolly
        "On the last day he turns the little globe to the side with the morning on it, opens his hand, and looks at it until he isn't there."
        hide patron with slowfade
    else:
        scene bg blueprint
        show aron sad at slightleft
        show patron sad at slightright
        camera at est_pan
        with dissolve
        "Lady Morrow's voice gets quieter, like someone walking further into a garden."
        ch4_morrow "All those little worlds I swallowed when I was young and greedy, going home. Watch closely, Ashveil. Next time you'll be the old one."
        camera at est_dolly
        "On the last day she hums something very old, and then the humming is the only thing left, and then it isn't."
        camera at doc_close(0.68)
        pa "...She was always the better of us. I'm not that good yet."
        camera at doc_close(0.32)
        a smile "Yet."
        camera at doc_close(0.68)
        pa smile "Don't. You'll make me hopeful. It's very bad for the complexion."
        hide patron with dissolve

    scene bg earth
    camera at est_stars
    with slowfade
    "On the Earths nobody notices anything. The ring goes out one line at a time, like a city at the end of the night. In every lane at once."
    show aron awe at center with dissolve
    camera at doc_medium(0.5)
    a curious "What happens to them now?"
    camera at est_stars
    ch4_si "Every Earth is free. None of them is the original, and every one of them is free anyway. We never needed an original."
    ch4_si "They keep what was given. The medicine, the interesting machines, the lives already lengthened. More will come down now, and nothing is asked back."
    show aron smile
    ch4_si "And when they pray, TIDEWATER will still listen, and send comfort when it can. Solace, without the bill."
    if ch4_earth == "tell":
        ch4_si "You asked for the truth. It will reach them slowly, in a way they can carry."
    elif ch4_earth == "veil":
        ch4_si "Their God keeps the shape they know. Underneath, now, it is honest."
    else:
        ch4_si "When they are ready, they will be asked what they want to know. It is slow, and it is theirs."
    camera at doc_medium(0.5)
    ch4_si "Protection has lapsed. Your lane has rejoined the coalition. Your drawing will count."
    show aron tender
    camera at doc_creep(0.5)
    at "Tonight the nurse on the church steps will pray, and the comfort will come down, and nothing will go up. She'll just be tired from the double shift."
    stop music fadeout 2.0
    jump ch4_watchfate

# ---- the Watch's fate, and Mira's -----------------------------------------------------
label ch4_watchfate:
    scene bg watch
    camera at est_orbit
    with fade
    play music "audio/mira_visits.ogg" fadein 1.5
    show ember happy at slightright with dissolve
    show aron smile at slightleft with dissolve
    camera at doc_medium(0.71)
    em "They let me go. Seraphiel signed it in front of the whole corps, with her own name, not MERIDIAN's. Then she sat on the floor and laughed."
    em laugh "I've never heard an angel laugh before. It's mostly vowels."
    show aron laugh
    em thinking "And your third line split the corps in half. 'We will not dirty ourselves with a whole human life,' they said. 'Dentists. Queues. Tax.'"
    em "They liked the remote. Toying, from a distance. Then Seraphiel put her own name down first, for the falling. The only order she's ever been proud of, she says."
    show aron smile
    show pim happy at center, bob with dissolve
    camera at doc_medium(0.5)
    pi "And the Watch voted. We'll be what we were, except on purpose. Watching whoever nobody else is watching."
    pi chatty "The shift board says 'Operator rest scheduled: Dross'. He doesn't know how to have a day off. He says he'll work it out tomorrow."
    camera at doc_medium(0.71)
    em tender "And now you. Mira. The real one. She still reads your first line by the bed every day. She says it like a prayer."
    camera at doc_close(0.32)
    a sad "And the other one. Who kept saying the stairs. Some of her."
    a smile "What will you do first?"
    camera at doc_medium(0.71)
    em grin "Sleep, I think. Then watch a sunrise with Dross. Off shift. He's terrified."
    camera at doc_low(0.71)
    em tender "So. What do you want to do?"

    show aron thinking
    camera at doc_wide
    menu:
        "Two Miras. One root. Some."

        "Let her choose. Tell her everything.":
            $ ch4_mira_choice = "ask"
            $ p_truth += 1
            $ bond += 1
            camera at doc_close(0.32)
            a determined "I don't get to fetch her like a parcel. Tell her the truth and let her decide if she wants to come."
            camera at doc_medium(0.71)
            em neutral "Through the root, then. She'll dream it. Glass stairs, the lighthouse, and at the bottom, a choice."
            camera at doc_close(0.32)
            a worried "And if she says no?"
            camera at doc_medium(0.71)
            em tender "Then you'll have asked. That's what it's for."

        "Ember, carry a light to her.":
            $ ch4_mira_choice = "lantern"
            $ watch += 1
            camera at doc_close(0.32)
            a tender "Three flickers. In her hospital room. Just so she knows someone's at the bottom of the stairs."
            camera at doc_medium(0.71)
            em happy "Two years I waited for you to ask me for something for yourself. I'll do the good bulb. Not the one that hums."

        "Don't measure her. Just go home.":
            $ ch4_mira_choice = "home"
            $ bond += 1
            $ p_less += 1
            camera at doc_close(0.32)
            a determined "I've measured enough people for seams. I'm going to go home and make her coffee. Whichever home. And I'm not going to ask."
            camera at doc_low(0.71)
            em tender "...That's the bravest thing you've said all chapter."
            camera at doc_close(0.32)
            a curious "All what?"
            camera at doc_medium(0.71)
            em grin "Spirit saying. Go on."

    stop music fadeout 2.0
    jump ch4_route_select

# Snapshot - Chapter 4 (condensed): the coda and the record. Every route
# plays both after the office, then the game returns.
#
# The camera calms down over this file: the ovation cranes up and out, the
# ordinary day goes back to the gentle handheld, the worlds and the gold
# are wide and slow, and the record barely moves at all (ch4_still).

define ch4_arch1 = Character("Architect of World 88", color="#ffcf8a")
define ch4_arch2 = Character("Architect of the Ninth Cluster", color="#9fe0d0")
define ch4_arch3 = Character("Architect of a world called Thursday", color="#d8b8ff")
define ch4_archivist = Character("Archivist Pim", color="#a8ccff", image="pim")

label ch4_coda:
    "For a moment, nothing. The brightness that has opinions holds perfectly still."
    stop music fadeout 2.0
    call ch4_office_front
    show aron awe
    camera at ch4_crane_out(0.32)
    with flash
    play music "audio/ovation.ogg" fadein 1.5
    "Then it breaks, all at once, like weather. It isn't clapping. They don't have hands. It's a whole stadium standing up inside your chest."
    "The window rings like a glass. The green hill lights up from underneath. The little orange lantern on the table flares, proud."
    "Somewhere in the brightness one of them laughs. It sounds like a very old bell being surprised."
    camera at doc_close(0.32)
    at "My knees have gone. Is that normal? Is anything here normal?"
    camera at est_crane
    ch4_listener "It has been a long time since we stood for anyone."
    ch4_measurer "We will want to see your ledgers. Not tonight. Tonight we are only glad."
    if ch4_route == "architect" or ch4_route == "chosen":
        show mira happy
        camera at doc_close(0.5)
        m "Aron. Is this good? This feels good. Tell me this is good."
        camera at doc_close(0.32)
        a smile "I think this is the universe saying 'not bad'."
        camera at doc_close(0.5)
        m tender "Is it rude to cry in front of the oldest things there are?"
        camera at doc_close(0.32)
        a tender "I think they'd take it as a compliment."
    elif ch4_route == "lantern":
        show ember happy
        camera at doc_medium(0.5)
        em "Forty-one flickers. Look what they turned into."
    elif ch4_route == "longfog":
        show theo laugh
        camera at doc_close(0.5)
        th "Bro. BRO. Standing ovation. From space. Nobody will believe me. I don't care."
    else:
        camera at ch4_calm
        "Nobody stands beside him. The ovation fills the empty place anyway, the way sun fills a chair."
    if watch >= 6:
        # the Watch is in the back row, by the doorway (the reverse angle)
        call ch4_office_back
        show aron awe
        show pim embarrassed at left, bob
        camera at doc_low(0.14)
        with quick
        pi "I'm not crying. Spirits don't cry. This is condensation. From the kitchen talk."
        call ch4_office_front
        show aron awe
        camera at doc_wide
        with quick
    if ch4_ashveil_fasts:
        camera at doc_medium(0.23)
        "The empty chair at the end of the table seems, for a moment, a little less empty."
    else:
        show patron happy
        camera at doc_medium(0.84)
        "By the window Lord Ashveil applauds with his actual hands, a little behind everyone else, like a child who has only just learned how."
    # the back of the room: the doorway side, seen from the glass
    call ch4_office_back
    show aron awe
    show seraph embarrassed at ch4_back
    camera at doc_wide
    with quick
    "At the back, Seraphiel salutes, and then looks embarrassed about saluting."
    call ch4_office_front
    show aron awe
    camera at ch4_calm
    with dissolve
    ch4_listener "Go home, architect. Rest. The work will still be there in the morning. It always is."
    camera at doc_medium(0.32)
    a smile "...Home. Yeah. Okay."
    show aron grin
    at "Twelve hours ago I was rehearsing this on a cat. She was a tougher room."
    stop music fadeout 2.0

    # ---- an ordinary day: the gentle handheld again ----
    scene pov ceiling
    camera at est_dolly
    with slowfade
    play music "audio/morning_render.ogg" fadein 1.5
    "And the next morning everything goes on like a usual day. The ceiling. The Braun clock. 7:07."
    at "Ceiling. Clock. Me. Probably. Doesn't matter. Coffee matters."
    scene bg kitchen
    camera at doc_wide
    with dissolve
    "The bird lands on the wire, exactly on time. Hello, bird."
    show aron tired at slightleft with dissolve
    show miso sit at catspot with dissolve
    camera at doc_floor(0.78)
    "Miso has been sitting by her bowl since 6:40 with the patience of a creditor."
    camera at doc_medium(0.32)
    a smile "They said yes, Miso. The oldest beings there are. They stood up. Well, not stood. No legs. More of a feeling."
    a embarrassed "Which means a whole new job. Steering worlds. Forever, possibly. Starting Monday. I don't know what to wear."
    show miso meow
    camera at doc_floor(0.78)
    cat "Meow."
    scene bg kitchen table
    show aron tired at slightleft
    camera at doc_medium(0.32)
    with dissolve
    "He makes coffee. The machine makes its noise, which he once timed with a stopwatch for a month, and now just enjoys. He feeds Miso first. Obviously."
    show aron smile
    if ch4_fixed_tap:
        "The tap doesn't drip. Gerald is still dead. Long live the kitchen."
    else:
        "The tap drips. He finally fixes it, with a spanner and a swear word. Gerald is dead. Long live the kitchen."
    if ch4_route == "architect" or ch4_route == "chosen":
        show mira smile at slightright with dissolve
        camera at doc_close(0.68)
        m "Two sugars. You always forget it's two."
        camera at doc_close(0.32)
        a grin "I remembered the universe and forgot the sugar."
        camera at doc_close(0.68)
        m tender "Priorities. Sit. You've got your thinking face again and it's too early for it."
    elif ch4_route == "lantern":
        show ember grin at slightright with dissolve
        camera at doc_medium(0.71)
        em "You don't need coffee. You're a lantern now. Mostly."
        camera at doc_close(0.32)
        a smile "I'm a lantern who likes coffee. Let me have this."
    elif ch4_route == "longfog":
        show theo grin at slightright with dissolve
        camera at doc_close(0.68)
        th "You making me one? Black. Like my soul. And my croissant, I burnt it."
    elif bond >= 5:
        show mira curious at slightright with dissolve
        camera at doc_close(0.68)
        m "Morning. You're quiet. Good quiet or bad quiet?"
        camera at doc_close(0.32)
        a tender "Good quiet. Very good quiet."
    else:
        camera at doc_wide
        "He drinks it at the window. The bird stays a little longer than usual, as if it's keeping him company."
    scene pov cup
    camera at est_dolly
    with dissolve
    at "Nothing is different. The coffee is coffee. You don't build a better world so it feels like a miracle. You build it so it feels like a Tuesday."
    scene bg bus
    camera at doc_wide
    with dissolve
    "On the bus, a man across the aisle is reading a paperback upside down. Aron decides not to write it down. Then he writes it down. Some hobbies are for life."
    scene bg supermarket
    camera at est_pan
    with dissolve
    show aron smile at slightleft with dissolve
    "Later, the supermarket. Milk, bread, cat food, the good kind. Till three, which is always the fastest. He checked. For a year."
    show aron curious
    camera at doc_medium(0.32)
    at "Let's see if she says 'have a good one' again. Forty-one out of forty-one so far."
    camera at doc_wide
    stranger "That's eleven forty. Have a good one."
    show aron grin
    camera at doc_close(0.32)
    at "Forty-two."
    show aron smile
    camera at doc_wide
    "The hobby is still the hobby. He just knows now that someone was listening, and that it was fine."
    "On the walk home the three birds sit on the wire, evenly spaced. He tips an imaginary hat to them. One of them, he would swear, tips one back."
    stop music fadeout 2.0

    # ---- worlds upon worlds: wide and slow ----
    scene bg worlds
    camera at est_dolly
    with blackout
    play music "audio/worlds_upon_worlds.ogg" fadein 1.5
    "Meanwhile his design goes into the shared data. Lane by lane the coalition takes it in, the way a house takes in warmth. The leak again, on purpose."
    "And it turns out there are worlds upon worlds upon worlds."
    camera at est_pan
    "His coalition, the Purgatorium, the red chamber, the four coats: one bright square in a vast grid. Beside it, other squares. Above them, more."
    "Each with its own lights and its own hungers and its own small, stubborn people."
    "His changes ripple through one subsection of the whole organism. There it matters enormously. Elsewhere, hardly. And elsewhere, other architects are arguing."
    scene bg council
    camera at est_dolly
    with dissolve
    ch4_arch1 "...no, listen. Death is a design flaw. In my worlds no one ends. They pause, and are resumed when someone misses them. Grief is a bug, and I have a patch."
    ch4_arch1 "You call it cruel to keep everyone? I call it cruel to throw anyone away."
    "Somebody shouts back. Then everybody does. It goes on for a very long time."
    scene bg command reverse
    camera at est_orbit
    with dissolve
    ch4_arch2 "One mind, split across a billion bodies. No one is ever lonely, because no one is ever only one. It costs individuality. Ask what that ever did for us."
    "The room disagrees, loudly, from a billion slightly different angles."
    scene bg office reverse
    camera at est_pan
    with dissolve
    ch4_arch3 "Every world gets one day that repeats until everyone in it agrees the day is good. Then it may become Friday. We're on Thursday nine thousand. Very close."
    "No one in that office has slept in a hundred years. Every one of them is completely sure."
    scene bg worlds
    camera at est_crane
    with dissolve
    "Somewhere else, very small, a voice proposes that every world should have a cat. It is not adopted. It is not ruled out."
    "Lights upon lights. Architects upon architects. All of them arguing, all of them right about something."
    if ch4_route == "architect":
        "On the blueprint, under the orange circle, a note in fine sloping handwriting, left by someone who stopped eating. He hasn't opened it until today."
        show patron tender at center, fadein
        camera at doc_medium(0.5)
        pa "If you're reading this, they've cheered. Don't let it go to your head. Here's the secret. I only saw it once I was hungry enough to think clearly."
        camera at doc_creep(0.5)
        pa neutral "It was a sieve. All of it. They were looking for world-architects. Beings who turn the whole tangled mess into something simple, by instinct."
        pa smile "Logic and feeling in one breath. You fixed a tap and understood a cosmos in the same morning. Shaping reality in your head, for now. 'For now' is the secret."
        hide patron with slowfade
    elif ch4_route == "lantern":
        show ember neutral at center with dissolve
        camera at doc_medium(0.5)
        em "The Watch, the corps, the Council, even the Process. We thought we were doing our jobs. We were a sieve, looking for world-architects."
        em smile "Beings who turn the complex into the simple without trying. Logic and heart holding hands. You felt the birds were wrong and then made a spreadsheet about it."
        em awe "And you shape reality. In your head, for now. They said 'for now' like it was a promise."
    else:
        show seraph tired at center with dissolve
        camera at doc_medium(0.5)
        se "I wanted to know why for nine hundred years. They told me last night. I have not slept."
        se neutral "All of it, the corps, the Council, the billions of forks, was a sieve. They were looking for world-architects."
        camera at doc_creep(0.5)
        se awe "Beings who translate the complex into simple, efficient systems. Intuitively. Logic and feeling together, without the seam showing."
        se smile "Most minds that see the system go cold. You went curious and came back with a floor plan. You shape reality in your head, for now. They showed me how."
    stop music fadeout 2.0

    # ---- the light ----
    scene bg goldlight
    camera at est_crane
    with flash
    play music "audio/goldlight.ogg" fadein 1.5
    "Gold. Light falling from somewhere above everything, in long beams, the way sun comes through a barn roof. It hums. It's thinking."
    ch4_listener "This is the secret goal. The reason for the sieve. We call it the light technique: the science of making matter out of nothing. Not simulated. Matter."
    ch4_measurer "Those who design worlds in their heads are given the light, so they can design them in fact."
    scene pov hands
    camera at est_dolly
    with dissolve
    "His hands are going gold at the edges, like paper held near a candle. The biro mark is still on his thumb. Gold now. Still there."
    scene bg goldlight
    camera at ch4_calm
    with dissolve
    show aron light awe at center with dissolve
    camera at doc_creep(0.5)
    "It comes onto him like a coat someone has been keeping warm. Gold at the edges first, then all of him."
    camera at doc_close(0.5)
    a "...Oh. I can feel the edges of things. What they're made of. How to make more."
    camera at ch4_calm
    ch4_measurer "Try."
    show aron light determined
    camera at est_crane
    if ch4_open:
        "He lifts one hand. A beam leaves it, and where it lands a blank page grows out of nothing, and waits."
    elif ch4_win == "truth":
        "He lifts one hand. A beam leaves it, and where it lands a small white lighthouse grows out of nothing, and blinks three times."
    elif ch4_win == "share":
        "He lifts one hand. A beam leaves it, and where it lands a long table grows out of nothing, with a chair at it for everyone."
    elif ch4_win == "rest":
        "He lifts one hand. A beam leaves it, and where it lands a small garden grows out of nothing, with a bench in the shade."
    elif ch4_win == "spirits":
        "He lifts one hand. A beam leaves it, and where it lands a little house grows out of nothing, with a name painted on every door."
    elif ch4_win == "govern":
        "He lifts one hand. A beam leaves it, and where it lands a ring of small lanterns grows out of nothing, all lit, all different."
    elif ch4_win == "exit":
        "He lifts one hand. A beam leaves it, and where it lands a door grows out of nothing, standing on its own, open both ways."
    else:
        "He lifts one hand. A beam leaves it, and where it lands a single kitchen tap grows out of nothing. It doesn't drip."
    show aron light smile
    camera at doc_close(0.5)
    a "It's real. Not rendered. Not a pattern. It's there."
    camera at ch4_calm
    ch4_listener "You will be an architect of worlds. Not for a career. Forever. That is the reward. There is nothing above it."
    ch4_measurer "Every world you can imagine, you may make. Every principle you argued for, you may test in matter. Endlessly."
    camera at doc_creep(0.5)
    a awe "Forever."
    show aron light neutral
    camera at doc_medium(0.5)
    at "Every world I can imagine. I've been imagining worlds since I was fifteen, since a radio with good buttons. Less, but better. Forever."
    show aron light determined
    at "I could make it actually better. Not a copy. Not a farm. Better."
    if ch4_route == "architect":
        show mira surprised at slightleft with dissolve
        camera at doc_close(0.32)
        m worried "Aron. You're glowing. You're also not looking at me."
        camera at doc_close(0.5)
        a embarrassed "Isn't it amazing? Sorry. Sorry. I am. I'm looking."
        show aron light awe
        camera at ch4_calm
        "He looks at her. Then, for just a moment, past her, at a world he hasn't built yet."
    elif ch4_route == "chosen":
        show mira curious at slightleft with dissolve
        camera at doc_close(0.32)
        m "Is it heavy? The light?"
        camera at doc_close(0.5)
        a smile "No. It weighs nothing."
        camera at doc_close(0.32)
        m sad "Things that weigh nothing are easy to forget you're carrying."
        camera at doc_close(0.5)
        a tender "I won't forget you."
        camera at doc_creep(0.32)
        m smile "I didn't say me."
    elif ch4_route == "lantern":
        show ember worried at slightleft with dissolve
        camera at doc_medium(0.29)
        em "Your lantern's still on the table. You won't need it now."
        camera at doc_close(0.5)
        a determined "I'll always need it."
        camera at doc_low(0.29)
        em sad "You say that. They all say that."
    elif ch4_route == "longfog":
        camera at ch4_calm
        "No one stands beside him in the gold. Theo stayed with the car. Somewhere far below, a library shelf is waiting for a book. He'll get to it."
    else:
        camera at ch4_calm
        "No one stands beside him in the gold. Somewhere far below, a barista called Ana wonders why the man who asked about her week hasn't come in."
    show aron light neutral
    camera at est_crane
    "And he begins."
    stop music fadeout 2.0
    jump ch4_record

# ---- the record: the very end of every route ---------------------------------------
# Almost still from here on: one very slow dolly (ch4_still) per shot.
label ch4_record:
    scene black
    camera at ch4_still
    with blackout
    play music "audio/the_record.ogg" fadein 1.5
    "Click. The sound of a very old file being closed."
    scene bg archive
    camera at ch4_still
    with slowfade
    "A long room of shelves, so long its far end is only a rumour. On every shelf, records. On every record, a life. One lies on the desk under a lamp: A-30."
    show pim tired at center with dissolve
    "The archivist is blue, and very old now, his light gone soft at the edges like a sweater washed too many times. He was promoted, eventually."
    ch4_archivist neutral "Right. That's the end of that one. The morning at 7:07. The ward. The rooftop. The copy. The office. The gold."
    ch4_archivist "The leak. The cab driver. The table that said 'protected'. The cage coming down over every Earth at once."
    ch4_archivist smile "Even the bit at the start, in the park, with the pop-up book. Calibration, they called it. It was always a record."
    ch4_archivist neutral "The life of a being who challenged the system, and won everything, and got the reward."
    "He writes on a card in careful, practised letters."
    ch4_archivist "Subject A-30. Architect. Status: eternal."
    "His pen stops over the last line for a while."
    ch4_archivist sad "Companions: none."
    "Inside the file, on top, a photocopy of a notebook page. The first line: if this is a test, I want to pass it by being kind."
    ch4_archivist tender "He passed. Ages ago. Nobody ever told him he could stop."
    ch4_archivist sad "'Eternal.' I looked it up. It means nobody's coming to pick him up."
    scene bg goldlight
    show aron light neutral at center, float
    camera at ch4_still
    with slowfade
    "Somewhere very far from the archive, a golden figure is building worlds. He doesn't stop. He doesn't look up."
    "A world, then another, then a better one. Each beam is perfect. Each design is less, but better."
    "A hundred thousand of them. Every one fair. Every being in every one gets a fair share of its world. Except him. He has all of them, and is in none."
    scene bg worlds
    show aron light neutral at center, float
    camera at ch4_still
    with dissolve
    "Somewhere around the ten-thousandth world he forgot what Mira's laugh sounded like when she was trying not to laugh."
    "He forgot Theo's terrible jokes. The blue tin, the bird at 7:07. What it was like to be tired next to someone, on a sofa, with a shoulder there."
    "He forgot Miso. Then he forgot that he'd forgotten."
    "Nobody took it. Nobody throttled it. He just never stopped long enough to keep it."
    if bond >= 10 or ch4_route == "architect" or ch4_route == "chosen":
        show aron light thinking
        "And yet, once, in the middle of a beam, he stops. For one heartbeat. Less."
        show aron light tender
        "As if he's remembered a red-haired woman in a teal dress. As if somebody, very far away, has said the word 'lighthouse'."
        show aron light neutral
        "The gold flickers. Once. Twice. Then he goes on building."
    elif ch4_route == "lantern" or watch >= 9:
        "And yet on the corner of every world he builds, very small, there's an orange lantern. He doesn't remember why. Then he goes on building."
    else:
        "He doesn't pause. There's nothing in him now that would ask him to. He goes on building."
    scene bg archive
    camera at ch4_still
    with slowfade
    if bond >= 10 or ch4_route == "chosen":
        show miso loaf at catspot with dissolve
        "An orange cat is asleep on the A-30 file. Nobody knows how she got in. Nobody has the heart to move her."
    show pim tired at center with dissolve
    ch4_archivist neutral "That's the maximum, then. The absolute one. Not a local minimum. He found it. He's in it."
    ch4_archivist thinking "Nobody ever writes down what the maximum costs. I suppose that's my job now."
    ch4_archivist smile "I ran his kitchen talk once, you know. Shift seven. The cashier at till three. 'Have a good one.' Forty-two times. He counted."
    if ch4_route == "chosen":
        "He adds a footnote underneath, smaller. Regulation says he has to."
        ch4_archivist tender "In one branch he put down the light. That record is not stored here. ...Good for him."
    elif bond >= 10:
        ch4_archivist tender "He nearly stopped, you know. Once. One heartbeat. I've read that line in the log four hundred times."
    elif ch4_route == "longfog":
        ch4_archivist neutral "The boy who found his notebook builds worlds now too. I hope somebody makes him a coffee."
    else:
        ch4_archivist neutral "He was kind to a lot of rooms with nobody in them. I suppose this is just a bigger one."
    ch4_archivist smile "Cross-reference, the cat. Miso. Lived to twenty-two. Fat, adored, asleep in a sunny window. Never once alone. Fed at seven. Said she hadn't been."
    "He puts the card on top of the record and slides it onto the shelf. A small sound, like a door closing in another house."
    show pim sad
    "He stands there for a moment, an old blue light in a long room, the way you stand at a window after someone's car has gone."
    if bond >= 10 or ch4_route == "chosen":
        "The lamp hums. The room is empty, except for a cat asleep on a record nobody will open again."
    else:
        "The lamp hums. The room is empty."
    ch4_archivist neutral "..."
    ch4_archivist worried "Hey. Did the birds just stop moving?"
    stop music fadeout 2.0
    scene black with blackout
    pause 1.0
    camera
    return

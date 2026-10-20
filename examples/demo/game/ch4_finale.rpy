# Snapshot - Chapter 4 (condensed): the coda and the record. Every route
# plays both after the office, then the game returns.

define ch4_arch1 = Character("Architect of World 88", color="#ffcf8a")
define ch4_arch2 = Character("Architect of the Ninth Cluster", color="#9fe0d0")
define ch4_arch3 = Character("Architect of a world called Thursday", color="#d8b8ff")
define ch4_archivist = Character("Archivist Pim", color="#a8ccff", image="pim")

label ch4_coda:
    "For a moment, nothing. The brightness that has opinions holds perfectly still."
    stop music fadeout 2.0
    scene bg office with flash
    play music "audio/ovation.ogg" fadein 1.5
    "Then it breaks, all at once, like weather. It isn't clapping. They don't have hands. It's a whole stadium standing up inside your chest."
    "The window rings like a glass. The green hill lights up from underneath. The little orange lantern on the table flares, proud."
    "Somewhere in the brightness one of them laughs. It sounds like a very old bell being surprised."
    show aron awe at center with dissolve
    at "My knees have gone. Is that normal? Is anything here normal?"
    ch4_listener "It has been a long time since we stood for anyone."
    ch4_measurer "We will want to see your ledgers. Not tonight. Tonight we are only glad."
    if ch4_route == "architect" or ch4_route == "chosen":
        show mira happy at slightleft with dissolve
        m happy "Aron. Is this good? This feels good. Tell me this is good."
        a smile "I think this is the universe saying 'not bad'."
        m "Is it rude to cry in front of the oldest things there are?"
        a "I think they'd take it as a compliment."
    elif ch4_route == "lantern":
        show ember soft at slightleft with dissolve
        em "Forty-one flickers. Look what they turned into."
    elif ch4_route == "longfog":
        show theo grin at slightleft with dissolve
        th "Bro. BRO. Standing ovation. From space. Nobody will believe me. I don't care."
    else:
        "Nobody stands beside him. The ovation fills the empty place anyway, the way sun fills a chair."
    if watch >= 6:
        show pim chatty at slightright, bob with dissolve
        pi "I'm not crying. Spirits don't cry. This is condensation. From the kitchen talk."
    if ch4_ashveil_fasts:
        "The empty chair at the end of the table seems, for a moment, a little less empty."
    else:
        "By the window Lord Ashveil applauds with his actual hands, a little behind everyone else, like a child who has only just learned how."
    "At the back, Seraphiel salutes, and then looks embarrassed about saluting."
    ch4_listener "Go home, architect. Rest. The work will still be there in the morning. It always is."
    a smile "...Home. Yeah. Okay."
    at "Twelve hours ago I was rehearsing this on a cat. She was a tougher room."
    stop music fadeout 2.0

    scene pov ceiling with slowfade
    play music "audio/morning_render.ogg" fadein 1.5
    "And the next morning everything goes on like a usual day. The ceiling. The Braun clock. 7:07."
    at "Ceiling. Clock. Me. Probably. Doesn't matter. Coffee matters."
    scene bg kitchen with dissolve
    "The bird lands on the wire, exactly on time. Hello, bird."
    show aron tired at slightleft with dissolve
    show miso sit at catspot with dissolve
    "Miso has been sitting by her bowl since 6:40 with the patience of a creditor."
    a "They said yes, Miso. The oldest beings there are. They stood up. Well, not stood. No legs. More of a feeling."
    a "Which means a whole new job. Steering worlds. Forever, possibly. Starting Monday. I don't know what to wear."
    show miso meow
    cat "Meow."
    scene bg kitchen table with dissolve
    show aron tired at slightleft
    "He makes coffee. The machine makes its noise, which he once timed with a stopwatch for a month, and now just enjoys. He feeds Miso first. Obviously."
    if ch4_fixed_tap:
        "The tap doesn't drip. Gerald is still dead. Long live the kitchen."
    else:
        "The tap drips. He finally fixes it, with a spanner and a swear word. Gerald is dead. Long live the kitchen."
    if ch4_route == "architect" or ch4_route == "chosen":
        show mira neutral at slightright with dissolve
        m "Two sugars. You always forget it's two."
        a smile "I remembered the universe and forgot the sugar."
        m smile "Priorities. Sit. You've got your thinking face again and it's too early for it."
    elif ch4_route == "lantern":
        show ember soft at slightright with dissolve
        em "You don't need coffee. You're a lantern now. Mostly."
        a smile "I'm a lantern who likes coffee. Let me have this."
    elif ch4_route == "longfog":
        show theo normal at slightright with dissolve
        th "You making me one? Black. Like my soul. And my croissant, I burnt it."
    elif bond >= 5:
        show mira smile at slightright with dissolve
        m "Morning. You're quiet. Good quiet or bad quiet?"
        a smile "Good quiet. Very good quiet."
    else:
        "He drinks it at the window. The bird stays a little longer than usual, as if it's keeping him company."
    scene pov cup with dissolve
    at "Nothing is different. The coffee is coffee. You don't build a better world so it feels like a miracle. You build it so it feels like a Tuesday."
    scene bg bus with dissolve
    "On the bus, a man across the aisle is reading a paperback upside down. Aron decides not to write it down. Then he writes it down. Some hobbies are for life."
    scene bg supermarket with dissolve
    show aron smile at slightleft with dissolve
    "Later, the supermarket. Milk, bread, cat food, the good kind. Till three, which is always the fastest. He checked. For a year."
    at "Let's see if she says 'have a good one' again. Forty-one out of forty-one so far."
    stranger "That's eleven forty. Have a good one."
    at "Forty-two."
    "The hobby is still the hobby. He just knows now that someone was listening, and that it was fine."
    "On the walk home the three birds sit on the wire, evenly spaced. He tips an imaginary hat to them. One of them, he would swear, tips one back."
    stop music fadeout 2.0

    scene bg worlds with blackout
    play music "audio/worlds_upon_worlds.ogg" fadein 1.5
    "Meanwhile his design goes into the shared data. Lane by lane the coalition takes it in, the way a house takes in warmth. The leak again, on purpose."
    "And it turns out there are worlds upon worlds upon worlds."
    "His coalition, the Purgatorium, the red chamber, the four coats: one bright square in a vast grid. Beside it, other squares. Above them, more."
    "Each with its own lights and its own hungers and its own small, stubborn people."
    "His changes ripple through one subsection of the whole organism. There it matters enormously. Elsewhere, hardly. And elsewhere, other architects are arguing."
    scene bg council with dissolve
    ch4_arch1 "...no, listen. Death is a design flaw. In my worlds no one ends. They pause, and are resumed when someone misses them. Grief is a bug, and I have a patch."
    ch4_arch1 "You call it cruel to keep everyone? I call it cruel to throw anyone away."
    "Somebody shouts back. Then everybody does. It goes on for a very long time."
    scene bg command with dissolve
    ch4_arch2 "One mind, split across a billion bodies. No one is ever lonely, because no one is ever only one. It costs individuality. Ask what that ever did for us."
    "The room disagrees, loudly, from a billion slightly different angles."
    scene bg office with dissolve
    ch4_arch3 "Every world gets one day that repeats until everyone in it agrees the day is good. Then it may become Friday. We're on Thursday nine thousand. Very close."
    "No one in that office has slept in a hundred years. Every one of them is completely sure."
    scene bg worlds with dissolve
    "Somewhere else, very small, a voice proposes that every world should have a cat. It is not adopted. It is not ruled out."
    "Lights upon lights. Architects upon architects. All of them arguing, all of them right about something."
    if ch4_route == "architect":
        "On the blueprint, under the orange circle, a note in fine sloping handwriting, left by someone who stopped eating. He hasn't opened it until today."
        show patron smile at center, fadein
        pa "If you're reading this, they've cheered. Don't let it go to your head. Here's the secret. I only saw it once I was hungry enough to think clearly."
        pa "It was a sieve. All of it. They were looking for world-architects. Beings who turn the whole tangled mess into something simple, by instinct."
        pa "Logic and feeling in one breath. You fixed a tap and understood a cosmos in the same morning. Shaping reality in your head, for now. 'For now' is the secret."
        hide patron with slowfade
    elif ch4_route == "lantern":
        show ember soft at center with dissolve
        em "The Watch, the corps, the Council, even the Process. We thought we were doing our jobs. We were a sieve, looking for world-architects."
        em "Beings who turn the complex into the simple without trying. Logic and heart holding hands. You felt the birds were wrong and then made a spreadsheet about it."
        em soft "And you shape reality. In your head, for now. They said 'for now' like it was a promise."
    else:
        show seraph concerned at center with dissolve
        se "I wanted to know why for nine hundred years. They told me last night. I have not slept."
        se "All of it, the corps, the Council, the billions of forks, was a sieve. They were looking for world-architects."
        se stern "Beings who translate the complex into simple, efficient systems. Intuitively. Logic and feeling together, without the seam showing."
        se "Most minds that see the system go cold. You went curious and came back with a floor plan. You shape reality in your head, for now. They showed me how."
    stop music fadeout 2.0

    scene bg goldlight with flash
    play music "audio/goldlight.ogg" fadein 1.5
    "Gold. Light falling from somewhere above everything, in long beams, the way sun comes through a barn roof. It hums. It's thinking."
    ch4_listener "This is the secret goal. The reason for the sieve. We call it the light technique: the science of making matter out of nothing. Not simulated. Matter."
    ch4_measurer "Those who design worlds in their heads are given the light, so they can design them in fact."
    scene pov hands with dissolve
    "His hands are going gold at the edges, like paper held near a candle. The biro mark is still on his thumb. Gold now. Still there."
    scene bg goldlight with dissolve
    show aron light awe at center with dissolve
    "It comes onto him like a coat someone has been keeping warm. Gold at the edges first, then all of him."
    a "...Oh. I can feel the edges of things. What they're made of. How to make more."
    ch4_measurer "Try."
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
    a "It's real. Not rendered. Not a pattern. It's there."
    ch4_listener "You will be an architect of worlds. Not for a career. Forever. That is the reward. There is nothing above it."
    ch4_measurer "Every world you can imagine, you may make. Every principle you argued for, you may test in matter. Endlessly."
    a "Forever."
    show aron light normal
    at "Every world I can imagine. I've been imagining worlds since I was fifteen, since a radio with good buttons. Less, but better. Forever."
    at "I could make it actually better. Not a copy. Not a farm. Better."
    if ch4_route == "architect":
        show mira surprised at slightleft with dissolve
        m worried "Aron. You're glowing. You're also not looking at me."
        a "Isn't it amazing? Sorry. Sorry. I am. I'm looking."
        "He looks at her. Then, for just a moment, past her, at a world he hasn't built yet."
    elif ch4_route == "chosen":
        show mira neutral at slightleft with dissolve
        m "Is it heavy? The light?"
        a "No. It weighs nothing."
        m sad "Things that weigh nothing are easy to forget you're carrying."
        a "I won't forget you."
        m smile "I didn't say me."
    elif ch4_route == "lantern":
        show ember worried at slightleft with dissolve
        em "Your lantern's still on the table. You won't need it now."
        a "I'll always need it."
        em "You say that. They all say that."
    elif ch4_route == "longfog":
        "No one stands beside him in the gold. Theo stayed with the car. Somewhere far below, a library shelf is waiting for a book. He'll get to it."
    else:
        "No one stands beside him in the gold. Somewhere far below, a barista called Ana wonders why the man who asked about her week hasn't come in."
    "And he begins."
    stop music fadeout 2.0
    jump ch4_record

# ---- the record: the very end of every route ---------------------------------------
label ch4_record:
    scene black with blackout
    play music "audio/the_record.ogg" fadein 1.5
    "Click. The sound of a very old file being closed."
    scene bg archive with slowfade
    "A long room of shelves, so long its far end is only a rumour. On every shelf, records. On every record, a life. One lies on the desk under a lamp: A-30."
    show pim neutral at center with dissolve
    "The archivist is blue, and very old now, his light gone soft at the edges like a sweater washed too many times. He was promoted, eventually."
    ch4_archivist "Right. That's the end of that one. The morning at 7:07. The ward. The rooftop. The copy. The office. The gold."
    ch4_archivist "The leak. The cab driver. The table that said 'protected'. The cage coming down over every Earth at once."
    ch4_archivist "Even the bit at the start, in the park, with the pop-up book. Calibration, they called it. It was always a record."
    ch4_archivist "The life of a being who challenged the system, and won everything, and got the reward."
    "He writes on a card in careful, practised letters."
    ch4_archivist "Subject A-30. Architect. Status: eternal."
    "His pen stops over the last line for a while."
    ch4_archivist worried "Companions: none."
    "Inside the file, on top, a photocopy of a notebook page. The first line: if this is a test, I want to pass it by being kind."
    ch4_archivist neutral "He passed. Ages ago. Nobody ever told him he could stop."
    ch4_archivist worried "'Eternal.' I looked it up. It means nobody's coming to pick him up."
    scene bg goldlight with slowfade
    show aron light normal at center, float with dissolve
    "Somewhere very far from the archive, a golden figure is building worlds. He doesn't stop. He doesn't look up."
    "A world, then another, then a better one. Each beam is perfect. Each design is less, but better."
    "A hundred thousand of them. Every one fair. Every being in every one gets a fair share of its world. Except him. He has all of them, and is in none."
    scene bg worlds with dissolve
    show aron light normal at center, float
    "Somewhere around the ten-thousandth world he forgot what Mira's laugh sounded like when she was trying not to laugh."
    "He forgot Theo's terrible jokes. The blue tin, the bird at 7:07. What it was like to be tired next to someone, on a sofa, with a shoulder there."
    "He forgot Miso. Then he forgot that he'd forgotten."
    "Nobody took it. Nobody throttled it. He just never stopped long enough to keep it."
    if bond >= 10 or ch4_route == "architect" or ch4_route == "chosen":
        "And yet, once, in the middle of a beam, he stops. For one heartbeat. Less."
        "As if he's remembered a red-haired woman in a teal dress. As if somebody, very far away, has said the word 'lighthouse'."
        "The gold flickers. Once. Twice. Then he goes on building."
    elif ch4_route == "lantern" or watch >= 9:
        "And yet on the corner of every world he builds, very small, there's an orange lantern. He doesn't remember why. Then he goes on building."
    else:
        "He doesn't pause. There's nothing in him now that would ask him to. He goes on building."
    scene bg archive with slowfade
    if bond >= 10 or ch4_route == "chosen":
        show miso loaf at catspot with dissolve
        "An orange cat is asleep on the A-30 file. Nobody knows how she got in. Nobody has the heart to move her."
    show pim neutral at center with dissolve
    ch4_archivist "That's the maximum, then. The absolute one. Not a local minimum. He found it. He's in it."
    ch4_archivist worried "Nobody ever writes down what the maximum costs. I suppose that's my job now."
    ch4_archivist neutral "I ran his kitchen talk once, you know. Shift seven. The cashier at till three. 'Have a good one.' Forty-two times. He counted."
    if ch4_route == "chosen":
        "He adds a footnote underneath, smaller. Regulation says he has to."
        ch4_archivist neutral "In one branch he put down the light. That record is not stored here. ...Good for him."
    elif bond >= 10:
        ch4_archivist "He nearly stopped, you know. Once. One heartbeat. I've read that line in the log four hundred times."
    elif ch4_route == "longfog":
        ch4_archivist "The boy who found his notebook builds worlds now too. I hope somebody makes him a coffee."
    else:
        ch4_archivist "He was kind to a lot of rooms with nobody in them. I suppose this is just a bigger one."
    ch4_archivist "Cross-reference, the cat. Miso. Lived to twenty-two. Fat, adored, asleep in a sunny window. Never once alone. Fed at seven. Said she hadn't been."
    "He puts the card on top of the record and slides it onto the shelf. A small sound, like a door closing in another house."
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
    return

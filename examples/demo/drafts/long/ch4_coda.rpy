# Snapshot - Chapter 4: the coda. Every route plays it after the office.

define ch4_arch1 = Character("Architect of World 88", color="#ffcf8a")
define ch4_arch2 = Character("Architect of the Ninth Cluster", color="#9fe0d0")
define ch4_arch3 = Character("Architect of a world called Thursday", color="#d8b8ff")

label ch4_coda:
    "For a moment, nothing. The brightness that has opinions holds perfectly still."
    "Then it breaks, all at once, like weather."
    play sound "audio/voices.ogg"
    scene bg office with flash
    "It isn't clapping. They don't have hands. It's the feeling of a whole stadium standing up inside your chest."
    "The window rings like a glass. The green hill outside lights up from underneath. The little orange lantern on the table flares, proud."
    stop sound
    show aron awe at center with dissolve
    if ch4_route == "architect" or ch4_route == "chosen":
        show mira happy at slightleft with dissolve
        m happy "Aron. Aron, they're... is this good? This feels good. Tell me this is good."
        a smile "I think this is the universe saying 'not bad'."
    elif ch4_route == "lantern":
        show ember soft at slightleft with dissolve
        em "Forty-one flickers. Look what they turned into."
    elif ch4_route == "longfog":
        show theo grin at slightleft with dissolve
        th "Bro. BRO. Standing ovation. From space. I'm telling everyone. Nobody will believe me. I don't care."
    else:
        "Nobody stands beside him. The ovation fills the empty place anyway, the way sun fills a chair."
    if watch >= 6:
        show pim chatty at slightright, bob with dissolve
        pi "I'm not crying. Spirits don't cry. This is condensation. From the kitchen talk."
    ch4_listener "Go home, architect. Rest. The work will still be there in the morning. It always is."
    a smile "...Home. Yeah. Okay."

    stop music fadeout 3.0
    scene black with slowfade
    pause 0.5
    scene pov ceiling with slowfade
    play music "audio/morning.ogg" fadein 2.0
    "And then, the next morning, everything goes on like a usual day."
    "The ceiling. The Braun clock. 7:07."
    at "Ceiling. Clock. Me. Probably. Doesn't matter. Coffee matters."
    scene bg kitchen with dissolve
    "The bird lands on the wire, exactly on time."
    show aron tired at slightleft with dissolve
    show miso sit at catspot with dissolve
    a "Morning, bird. Morning, Miso."
    "Miso has been sitting by her bowl since 6:40 with the patience of a creditor."
    a "They said yes, Miso. The oldest beings there are. They stood up. Well, not stood. They had no legs. It was more of a feeling."
    a "Which means there's a whole new job. Steering. Worlds. Forever, possibly. Starting Monday. I don't know what to wear."
    show miso meow
    cat "Meow."
    scene bg kitchen table with dissolve
    show aron tired at slightleft
    "He makes coffee. The machine makes its noise, the same noise it always makes, which he once timed with a stopwatch for a month, and now just enjoys."
    "He feeds Miso first. Obviously."
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
        "He drinks it alone at the window, and that's fine. The bird stays a little longer than usual, as if it's keeping him company."
    scene pov cup with dissolve
    at "Nothing is different. The coffee is coffee. The bird is the bird. That's the point. That was always the point."
    at "You don't build a better world so it can feel like a miracle every morning. You build it so it can feel like a Tuesday."
    scene bg supermarket with dissolve
    "Later, the supermarket. Milk, bread, cat food, the good kind. The queue at till three, which is always the fastest. He checked. For a year."
    show aron smile at slightleft with dissolve
    at "Right. Let's see if she says 'have a good one' again. Forty-one times out of forty-one, so far."
    stranger "That's eleven forty. Have a good one."
    at "Forty-two."
    "He grins all the way to the car park. The hobby is still the hobby. He just knows now that someone was listening, and that it was fine."

    stop music fadeout 3.0
    scene bg worlds with blackout
    play music "audio/entities.ogg" fadein 3.0
    "Meanwhile his design goes into the shared data."
    "Lane by lane the coalition takes it in, the way a house takes in warmth: the kitchens first, then the stairs, then the rooms nobody uses."
    "It's the leak again. One mind reshaping a world. Except this time it's on purpose, and it's careful, and it's invited."
    "And it turns out there are worlds upon worlds upon worlds."
    "His coalition, the billions of lanes, the Purgatorium, the red chamber, the four coats: one bright square in a vast grid."
    "Beside it, other squares. Above them, more. Below, more again. Each with its own lights and its own hungers and its own small stubborn people."
    "His changes ripple through one subsection of the whole organism. One coalition. One corner of one page. There it matters enormously. Elsewhere, hardly."
    "And in the other squares, other architects are arguing for their worlds."

    scene bg council with dissolve
    ch4_arch1 "...no, listen to me. Death is a design flaw. In my worlds no one ends. They pause. They can be resumed when someone misses them."
    ch4_arch1 "You call it cruel to keep everyone? I call it cruel to throw anyone away. Grief is a bug, and I have a patch."
    "Somebody shouts back. Then everybody does. It goes on for a very long time."

    scene bg command with dissolve
    ch4_arch2 "One mind. Split across a billion bodies. No one is ever lonely because no one is ever only one."
    ch4_arch2 "Yes, it costs individuality. Ask yourselves honestly how much good individuality has done the Ninth Cluster."
    "The room disagrees, loudly, from a billion slightly different angles."

    scene bg office with dissolve
    ch4_arch3 "Mine is simpler. Every world gets one day that repeats, perfectly, forever, until everyone in it agrees the day is good."
    ch4_arch3 "Then, and only then, it's allowed to become Friday. We are on Thursday number nine thousand. We are very close."
    "No one in that office has slept in a hundred years. Every one of them is completely sure."

    scene bg worlds with dissolve
    "Lights upon lights. Architects upon architects. All of them arguing, all of them right about something."
    if ch4_route == "architect":
        "On the blueprint, under the orange circle, there is a note in fine sloping handwriting, left a long time ago, by someone who stopped eating."
        "It is addressed to Aron. He has not opened it until today."
        show patron smile at center, fadein
        pa "If you're reading this, they've cheered. They always cheer for the good ones. Don't let it go to your head. It goes to everyone's head."
        pa "Here is the secret I never told you, because I didn't know it was a secret until I was hungry enough to think clearly."
        jump ch4_coda_reveal_ashveil
    elif ch4_route == "lantern":
        show ember soft at center with dissolve
        em "You see it now, don't you. How big it is. How many of them there are."
        em "There's something I never told you. I didn't know it until they told the Watch, after the vote. It's... a lot. Sit down."
        jump ch4_coda_reveal_ember
    else:
        show seraph concerned at center with dissolve
        se "You will want to know why. I wanted to know why, for nine hundred years. They told me last night. I have not slept."
        jump ch4_coda_reveal_seraph

label ch4_coda_reveal_ashveil:
    pa "The worlds were never really the point. The farms. The yield. Not even the search for the best world."
    pa "They were a sieve. Everything was. They were looking for a particular kind of being, and you only find them by running a great many lives."
    pa smile "World-architects. Beings who can take the whole tangled mess and translate it into something simple and efficient. By instinct."
    pa "Not by logic alone. Not by feeling alone. Both at once, in the same breath. The way you fixed a tap and understood a cosmos in the same morning."
    pa "Shaping reality. In their heads, for now. That 'for now' is the whole secret."
    hide patron with slowfade
    jump ch4_coda_light

label ch4_coda_reveal_ember:
    em worried "The Watch, the corps, the Council, even the Process. We all thought we were doing our jobs. We were the sieve."
    em "They were looking for world-architects. Beings who can turn the complex into the simple, without even trying. Who feel a system and think it at once."
    em soft "Logic and heart together. Most have one. A few have both, but at war. Very few have them holding hands."
    em "You do. You always did. You felt the birds were wrong and then you made a spreadsheet about it."
    em "And you shape reality. In your head, for now. They said 'for now' like it was a promise."
    jump ch4_coda_light

label ch4_coda_reveal_seraph:
    se "The angel corps. The Council. The Process. The billions of forks. All of it was, in the end, a sieve."
    se stern "They were looking for world-architects. Beings who can translate the complex into simple, efficient systems. Intuitively."
    se concerned "Not by calculation alone. Not by feeling alone. Both, together, without the seam showing. It is extremely rare."
    se "Most minds that see the system go cold, or go quiet. You went curious. You took notes. Then you came back with a floor plan."
    se "Beings who shape reality. In their heads, for now. I asked them what 'for now' meant. They showed me."
    jump ch4_coda_light

label ch4_coda_light:
    stop music fadeout 2.0
    scene bg goldlight with flash
    play music "audio/theme.ogg" fadein 3.0
    "Gold."
    "Light falling from somewhere above everything, in long beams, the way sun comes through a barn roof. It hums. It's warm. It's thinking."
    ch4_listener "This is the secret goal. The reason for the sieve. The reward."
    ch4_measurer "We call it the light technique. The science of making matter out of nothing. Not simulated matter. Matter."
    ch4_listener "Those who can design worlds in their heads are given the light, so they can design them in fact."
    scene pov hands with dissolve
    "He looks down. His hands are going gold at the edges, like paper held near a candle. It doesn't hurt. It feels like being remembered."
    at "Are these still my hands? The biro mark's still there, on the thumb. Gold, now. Still there."
    scene bg goldlight with dissolve
    show aron light awe at center with dissolve
    "It comes onto him like a coat someone has been keeping warm. Gold at the edges first, then all of him."
    a "...Oh."
    a "I can feel the edges of things. What they're made of. How to make more."
    ch4_measurer "Try."
    if ch4_win == "truth":
        "He lifts one hand. A beam of gold leaves it, and where it lands, a small white lighthouse grows out of nothing, and blinks three times."
    elif ch4_win == "share":
        "He lifts one hand. A beam of gold leaves it, and where it lands, a long table grows out of nothing, with a chair at it for everyone."
    elif ch4_win == "rest":
        "He lifts one hand. A beam of gold leaves it, and where it lands, a small garden grows out of nothing, with a bench in the shade."
    elif ch4_win == "spirits":
        "He lifts one hand. A beam of gold leaves it, and where it lands, a little house grows out of nothing, with a name painted on every door."
    elif ch4_win == "govern":
        "He lifts one hand. A beam of gold leaves it, and where it lands, a ring of small lanterns grows out of nothing, all lit, all different."
    elif ch4_win == "exit":
        "He lifts one hand. A beam of gold leaves it, and where it lands, a door grows out of nothing, standing on its own, open both ways."
    elif ch4_open:
        "He lifts one hand. A beam of gold leaves it, and where it lands, a blank page grows out of nothing, and waits."
    else:
        "He lifts one hand. A beam of gold leaves it, and where it lands, a single kitchen tap grows out of nothing. It doesn't drip."
    show aron light smile
    a "It's real. It's actually real. Not rendered. Not a pattern. It's there."
    ch4_listener "You will be an architect of worlds. Not for a career. Forever. That is the reward. There is nothing above it."
    ch4_measurer "Every world you can imagine, you may make. Every principle you argued for, you may test in matter. Endlessly."
    show aron light normal
    a "Forever."
    at "Every world I can imagine. I've been imagining worlds since I was fifteen. Since a radio with good buttons."
    at "Less, but better. Forever. I could make it actually better. Not a copy. Not a farm. Better."

    if ch4_route == "architect":
        show mira surprised at slightleft with dissolve
        m "Aron. You're glowing."
        a "I know. Isn't it amazing?"
        m worried "It is. You're also not looking at me."
        a "Sorry. Sorry. I am. I'm looking."
        "He looks at her. Then, for just a moment, past her, at a world he hasn't built yet."
    elif ch4_route == "chosen":
        show mira neutral at slightleft with dissolve
        m "Is it heavy? The light?"
        a "No. That's the strange part. It weighs nothing."
        m sad "Things that weigh nothing are easy to forget you're carrying."
        a "I won't forget you."
        m smile "I didn't say me."
    elif ch4_route == "lantern":
        show ember soft at slightleft with dissolve
        em "Your lantern's still on the table. You won't need it now, I suppose."
        a "I'll always need it."
        em worried "You say that. They all say that."
    elif ch4_route == "longfog":
        "No one stands beside him in the gold. Theo stayed with the car. Theo always stays with the car."
        "Somewhere far below, in a library, a shelf is waiting for him to put a book in its right place. He'll get to it."
    else:
        "No one stands beside him in the gold. He's used to that. He's very good at being kind to an empty room."
        "Somewhere far below, a copy of a barista called Ana is wondering why the man who always asked about her week hasn't come in."

    "And he begins."
    stop music fadeout 3.0
    jump ch4_record

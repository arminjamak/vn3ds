# Snapshot - Chapter 1, "The Morning Render" (part 3 of 4)
# The studio and the radio, the umbrella in the rain, the first voices,
# the order to throttle, Theo's night, and the edge of the world.

define ch1_tobias = Character("Stranger", color="#cccccc")
define ch1_albers = Character("Mr. Albers", color="#d6c7a8")
define ch1_driver = Character("Tram driver", color="#cccccc")
define ch1_feld = Character("Mrs. Feld", color="#e0b0d0")

label ch1_shop:
    scene bg studio with slowfade
    play music "audio/morning.ogg" fadein 2.0
    "Feld Design is two white rooms above a launderette: four desks, a workbench, a shelf of prototypes, and one quotation on the wall."
    "Good design is as little design as possible. Dieter Rams. Mrs. Feld painted it there herself in 1979."
    show aron normal at slightleft with dissolve
    "Aron has worked here for four years, designing kettles and lamps and once, gloriously, a toaster. It's the only job that never felt like pretending."
    ch1_feld "You're late, Aron."
    a "Two minutes."
    ch1_feld "Two minutes is late. Kettles notice. Sit. The client call is in one minute."
    "The client is Herr Brandt from a kitchenware company, who appears on the screen every Thursday at ten to talk about a kettle."
    at "Last Thursday he said 'circle back' exactly three times. The Thursday before, three times. Let's see."
    "Brandt" "Morning, all! Great work on the spout. Let's circle back to the handle."
    at "One."
    "Brandt" "The lid we can circle back to later. And the colour, let's circle back on that next week."
    at "Two. Three. Hat trick. He's very consistent, Herr Brandt. I'd almost miss it if he wasn't."
    "Aron writes a tiny 3 in the corner of his sketchbook and keeps a perfectly straight face for the rest of the call."
    ch1_feld "Good. Now. I brought you something."
    "Mrs. Feld is seventy-one and five foot nothing and has opinions about rounded corners that she will defend to the death."
    "On his desk, on a folded cloth, sits a small grey pocket radio. Rounded corners. A perforated grille of tiny holes in perfect rows."
    a awe "Oh. Oh, no way."
    ch1_feld "My husband's. It hasn't made a sound since 1987. You're good with your hands. I want to hear it once."
    "Aron picks it up with both hands, the way you'd pick up a bird."
    at "Look at it. No decoration. Nothing that doesn't need to be there. Every hole in the grille in its place."
    at "Less, but better. He said that. Rams. Every designer I admire is just a footnote to that sentence."
    at "Most things shout. This just... is. It's honest about what it is. It's a radio. It doesn't pretend to be a spaceship."
    a "Why do you think I'll be able to fix it?"
    ch1_feld "Because you love it already. People fix what they love. They just throw out the rest."
    scene pov hands with dissolve
    "He opens the back. Inside it's clean and simple and sad, like an empty house. One capacitor has burst, one wire has gone green."
    "His hands do the work. Solder, wire, patience. For hours, he forgets the birds."
    scene bg studio with dissolve
    show aron smile at slightleft with dissolve
    "At five, he calls her over and turns the little wheel. A click. A hiss. Static, like rain on a microphone."
    "Then, through the hiss, music. A piano. Some old song, thin and bright, coming out of a box made seventy years ago."
    "Mrs. Feld puts her hand over her mouth."
    ch1_feld "That's how it sounded. In the kitchen. Every Sunday. He'd whistle along, badly."
    "She stands very still and listens to the whole song. Aron pretends to tidy his desk so she can cry without being watched."
    "On the shelf above her desk there's an old paperback. When he moves it, it falls open at a dog-eared page."
    "One sentence is underlined in pencil, very lightly, as if by someone who didn't want to be caught underlining."
    centered "'We are the stars' way of looking back at themselves, and wondering who lit them.'"
    at "Huh."
    at "Somebody wrote that. Somebody underlined it. And it fell open on that page, under my hand, today."
    at "Books fall open on the pages people read most. That's just physics. Spines remember."
    at "...Or someone wanted me to see it."
    ch1_feld "That was his book too. He underlined everything. Terrible habit."
    "She takes the radio from him and holds it to her ear, though it's loud enough already."
    ch1_feld "Thank you, Aron. You don't know what this is."
    a "I think I do, a bit."
    ch1_feld "Then you also know you look tired. You're the colour of old putty. Are you sleeping?"
    a "Mostly."
    ch1_feld "Mostly is what my husband said for twenty years. Go home early. Tomorrow too."
    a normal "I'll finish the lamp drawings first."
    ch1_feld "Stubborn. Good. Stubborn people make things. But go home."
    "The little radio, still playing in her hands, crackles between songs."
    radio "...and rain this evening, heavy at times..."
    "For a moment he could swear the announcer said his name before the forecast. He decides he didn't hear that."
    "He finishes the lamp drawings. He stays later than he should. By the time he locks the door it's dark and pouring."
    stop music fadeout 2.0
    jump ch1_rain

label ch1_rain:
    scene bg street rain with slowfade
    play music "audio/unease.ogg" fadein 2.0
    "The rain has come back, harder, as if it has been saving up."
    "Aron walks home from the studio at nine, late, with the sound of the little radio still in his ears."
    "Mira made him take the big umbrella this morning, the good one with the bent spoke. 'It's going to pour,' she said. She was right."
    show aron tired at center with dissolve
    "The street is a river of orange light. Water runs in the gutters, loud and quick. The rain on the umbrella is a drumroll."
    at "Theo says real rain sounds like static on a microphone. He's right. It does."
    at "It sounds like the end of the dream. The TV in the next flat, switching off."
    "At the bus shelter on the corner, there's a man."
    "He isn't in the shelter. He's standing just outside it, in the rain, as if he hasn't noticed the roof is there."
    "No coat. A thin grey shirt soaked dark. His hair is plastered to his forehead. He's staring at the road, not moving."
    "Water runs off his nose and chin. He doesn't wipe it."
    at "He's going to get pneumonia. Or he's drunk. Or something's wrong."
    "Aron slows down. The man doesn't look at him."
    a normal "Hey. Are you all right? You're soaked."
    "The man turns his head slowly, the way a camera turns on a tripod."
    ch1_tobias "Rain, isn't it."
    a "It really is. Do you want to stand under the shelter? It's dry in there."
    ch1_tobias "I'm waiting."
    a "For the bus?"
    ch1_tobias "..."
    "The man's face doesn't change. There's no worry in it, no cold, no embarrassment. Just water, running."
    at "He looks like the woman at the crossing. Like Kessler's smile. Like something waiting for its next line."
    at "A person nobody's using right now."
    at "And he's freezing. Whatever he is, he's standing in the rain getting soaked to the bone."
    "Aron looks at the umbrella in his hand. A good one. Mira bought it for him two Christmases ago."

    menu:
        at "He's still just standing there."

        "Give him the umbrella and go":
            $ integrity += 1
            $ watch += 1
            jump ch1_rain_give

        "Give it, and ask his name":
            $ p_spirits += 1
            $ watch += 1
            $ ch1_asked_name = True
            jump ch1_rain_name

        "Ask what he's waiting for":
            $ clarity += 1
            $ watch += 1
            jump ch1_rain_ask

label ch1_rain_give:
    a "Here. Take this."
    scene cg umbrella with dissolve
    "He holds out the umbrella. The man looks at it as if he's never seen one."
    a "It's an umbrella. You hold the stick and it keeps the sky off you. Very advanced technology."
    "He presses the handle into the man's hand and closes the cold fingers around it."
    ch1_tobias "...Oh."
    "The rain hits Aron at once, heavy and cold, down the back of his collar."
    a "Keep it. Seriously. Get home safe."
    ch1_tobias "Thank you."
    "It's a perfectly ordinary 'thank you'. But it arrives a beat late, and slightly too soft, as if it came from further away."
    scene bg street rain with dissolve
    show aron tired at center with dissolve
    "Aron turns up his collar and walks off into the rain without looking back."
    at "Mira's going to kill me. Two Christmases ago. A good umbrella."
    at "But if a man stands in the rain long enough, somebody should give him an umbrella. That's just a rule."
    at "Real or not real. Somebody should."
    jump ch1_rain_after

label ch1_rain_name:
    a "Here. Take this."
    scene cg umbrella with dissolve
    "He holds out the umbrella and presses the handle into the man's cold hand."
    ch1_tobias "...Oh."
    "The rain hits Aron at once, heavy and cold, down the back of his collar."
    a "I'm Aron. What's your name?"
    ch1_tobias "My name."
    "The man thinks about it. It takes a long time. Rain drums on the umbrella now held above his head."
    ch1_tobias "I don't think anyone's asked."
    a "Well, I'm asking."
    ch1_tobias "..."
    ch1_tobias "Tobias. That sounds right. Tobias."
    a "Nice to meet you, Tobias. Keep the umbrella. Get home safe."
    ch1_tobias "Aron."
    a "Yeah?"
    ch1_tobias "Thank you, Aron."
    "For a moment, under the umbrella, there is something in the man's eyes. Like a lamp turned on in an empty house."
    scene bg street rain with dissolve
    show aron tired at center with dissolve
    "Then the bus comes, and its doors hiss open, and when it pulls away the stop is empty."
    at "'That sounds right.' Like he was choosing a name off a shelf."
    at "But he said mine back. He said thank you, Aron. Nobody says your name unless they mean you."
    at "If he was a part of the scenery, then I just introduced myself to the scenery. And it said my name back."
    at "Somehow that doesn't feel silly. It feels like the most correct thing I've done all week."
    jump ch1_rain_after

label ch1_rain_ask:
    a "What are you waiting for? Maybe I can help."
    ch1_tobias "I don't know."
    a "You don't know?"
    ch1_tobias "Something. Somebody's supposed to... I'm supposed to..."
    "He stops. His mouth stays a little open, as if the end of the sentence never arrived."
    at "Like a line that didn't load. Like 'lovely morning for it'."
    at "Okay. This is the test. This is the real test. Someone standing in front of me with the back of the set showing."
    at "I could ask him a hundred questions. I could find out exactly what he is. Right now. Here."
    "The man shivers. Just once. A full-body shiver, like a dog coming out of a lake."
    at "...Or I could stop testing him and let him be cold or not cold."
    a "Here."
    scene cg umbrella with dissolve
    "He holds out the umbrella and closes the man's cold fingers around the handle."
    ch1_tobias "Oh."
    a "Whatever you're waiting for, you can wait for it dry."
    ch1_tobias "Thank you."
    scene bg street rain with dissolve
    show aron tired at center with dissolve
    "The rain hits Aron at once, heavy and cold, down the back of his collar. He doesn't mind as much as he expected."
    at "I didn't find out what he is. I found out what I am. That'll have to do for tonight."
    jump ch1_rain_after

label ch1_rain_after:
    "He walks the last three blocks home without an umbrella."
    "By the time he reaches the front door he is soaked through, shoes squelching, hair dripping into his eyes."
    "On the wire above the door, three birds sit in the rain. Evenly spaced. Not moving. Not even ruffling their feathers."
    "Across the street, high up in an attic window he's never noticed before, a small orange light is burning."
    "He doesn't notice it now either. He's busy looking for his keys."
    scene bg room night with dissolve
    show mira surprised at slightright with dissolve
    show aron tired at slightleft with dissolve
    m "Oh my god. You're drowned. Where's the umbrella?"
    a "I gave it away."
    m neutral "You gave it away."
    a "There was a man at the bus stop. No coat. Just standing in the rain."
    m "So you gave him my Christmas umbrella."
    a "I gave him my Christmas umbrella. That you gave me. So technically it was mine to give."
    m "..."
    m smile "You're an idiot."
    a "I know."
    m happy "Come here, idiot. Take that shirt off before you ruin the floor. I'll make tea. Miso, out of the way."
    "Miso, who has come to inspect the puddle forming around his feet, retreats to the sofa with an expression of deep judgement."
    "Mira towels his hair hard, like a mother with a child, and he laughs into the towel."
    m smile "Was he all right? The man?"
    a normal "I don't know. I hope so."
    m "Then you did the right thing. Even if I'm going to complain about it for a year."
    stop music fadeout 2.0
    jump ch1_voices

# ---------------------------------------------------------------------------
# The voices begin.
# ---------------------------------------------------------------------------
label ch1_voices:
    scene bg bedroom night with blackout
    "That night he lies awake beside Mira and listens to the rain."
    "It's softer now. A steady hiss, like a radio between stations."
    show aron tired at center with dissolve
    at "Tired. So tired. My legs feel like sandbags. Must be the cold."
    "He closes his eyes. The hiss of the rain goes on. Somewhere under it, the radiator ticks."
    "Tick. Tick. A pause. Tick."
    "And then, inside the hiss, so quiet he could be imagining it, something that sounds like words."
    play sound "audio/voices.ogg"
    vox "...subject A-30..."
    a worried "..."
    "He opens his eyes. The room is dark. Mira breathes slowly beside him. The rain hisses."
    at "Did I just hear that?"
    at "A-30. Subject. Somebody said 'subject A-30'."
    at "No. No. The rain. It's white noise. Your brain finds words in white noise. That's pareidolia. That's a known..."
    play sound "audio/voices.ogg"
    vox "...disturbance, early stage... send it upstairs..."
    scene bg bedroom door with quick
    show aron worried at center with dissolve
    "He sits up. His heart gives one hard knock. He looks at the half-open door, the dark hall beyond it."
    "It isn't coming from the hall. It isn't coming from the radiator. It isn't coming from anywhere."
    "It's like hearing a conversation through a wall, except there is no wall. Only the inside of his own head."
    at "That's a voice. That's not my voice. I know what my thoughts sound like and that is not one of them."
    at "Okay. That's new. That is definitely not on the list of things I was testing for."
    play sound "audio/voices.ogg"
    vox "...log it as written..."
    stop sound
    "Then it's gone. Just the rain. Just Mira breathing. Just the radiator, ticking."
    a "..."
    at "'Log it as written.' Like a... like an instruction. Like someone reading out a list. A log."
    at "Subject A-30. A for Aron? I'm thirty. A-30. Aron, thirty."
    at "Somebody is writing me down. Which would be flattering, if it weren't so strange."
    at "Or I'm cold and soaked and I gave away an umbrella to a man with no name, and my brain is playing with the rain."
    at "Both. It could be both. Breathe, Aron. Be curious, not scared. Curious is more fun."

    menu:
        at "What do I do with this?"

        "Write down every word":
            $ p_rest -= 1
            $ clarity += 1
            jump ch1_voices_write

        "Wake Mira and tell her":
            $ p_truth += 1
            $ bond += 1
            $ told_mira = True
            jump ch1_voices_tell

        "Headphones on. Try to sleep.":
            $ p_rest += 1
            jump ch1_voices_sleep

label ch1_voices_write:
    "He slides out of bed without waking her and goes to the desk in the dark."
    scene bg desk with dissolve
    show aron worried at center with dissolve
    "The lamp makes a small yellow island. He opens the notebook to a clean page and writes, fast, before it fades."
    centered "...subject A-30...\n...disturbance, early stage...\n...send it upstairs...\n...log it as written..."
    at "Four fragments. Process words. 'Log'. 'Upstairs'. 'Early stage'. Like a hospital. Like a factory."
    at "Who says 'send it upstairs'? Someone in an office. Someone with a boss."
    at "So there's an office, and there's an upstairs. Layers. A chain of command."
    "He draws boxes. One for the voices. One above it labelled 'upstairs'. An arrow between them."
    "Below them, a small box with a stick figure inside. A-30."
    at "And they call it a disturbance. Me. I'm the disturbance. Because I started looking."
    at "Because of the notebook. Because I wrote it down."
    "His hand stops."
    at "If they can hear me thinking this... are they hearing it now?"
    "The lamp hums. The rain hisses. Nothing answers."
    "He writes until four in the morning. Arrows, boxes, words. When he finally lies down, the page is black with ink."
    scene pov ceiling with dissolve
    "At 7:07 he wakes with a headache like a nail behind his left eye, and the feeling of having worked a night shift in a mine."
    jump ch1_cut_throttle

label ch1_voices_tell:
    a "Mira."
    "He touches her shoulder. She makes a small sound and turns over."
    scene bg bedroom night with dissolve
    show mira neutral at slightright with dissolve
    show aron worried at slightleft with dissolve
    m "Mm? What time is it?"
    a "Late. I'm sorry. I need to tell you something and I need to tell you now, before I talk myself out of it."
    "She hears something in his voice and sits up at once, wide awake, the way her mother taught her."
    m worried "Okay. I'm here. Tell me."
    a "I've been testing things. The bird. The clock. The way people talk. I've got a notebook."
    a "I think the world might be... I think it might be a simulation. Like Bostrom. Like I told Theo."
    m neutral "Okay."
    a "And just now I heard something. Voices. In the rain. Not real voices. Inside. Saying things."
    m "What things?"
    a "'Subject A-30.' 'Disturbance, early stage.' 'Log it as written.' Like someone reading out a log. About me."
    "Mira is very still. In the dark he can't see her face clearly. He can hear her breathing change."
    m worried "Aron. Voices is the word I'm scared of."
    a "I know."
    m "My mum's a nurse. You know what she'd say. Voices means a doctor."
    a "I know. I know what it sounds like. I'm not stupid. I know exactly what it sounds like."
    a "But Mira, the lighthouse. You knew the lighthouse. How do I explain that? How does a doctor explain that?"
    m "..."
    m sad "I don't know. I don't know how I knew that."
    "She takes his hand in both of hers and holds it against her chest, so he can feel her heart going fast."
    m worried "Okay. Listen. I'm not going to drag you anywhere tonight. But I need you to promise me something."
    a "Anything."
    m "If it gets worse, if you stop sleeping, if the voices get louder, you tell me. And we go. Together."
    a "...Okay."
    m "Say it properly."
    a "If it gets worse, I'll tell you. And we'll go together."
    m neutral "Thank you."
    "They lie back down. She keeps hold of his hand. He listens to the rain. No more words come out of it tonight."
    at "I told her. It's out of my head and into the room. It's not just mine anymore."
    at "Two of us keeping it. That's sturdier."
    jump ch1_cut_throttle

label ch1_voices_sleep:
    "He reaches for his headphones on the nightstand and puts on an old album. Something with piano. Something he knows by heart."
    "The music fills his head. The rain moves behind it. Somewhere very far away, under the piano, the hiss goes on."
    at "Not tonight. Whatever you are, not tonight. I'm tired. I'm allowed to be tired."
    at "If it's real, it'll still be real in the morning. If it's not, it'll be gone."
    "He breathes. In for four. Hold. Out for six. The way Mira taught him when he had exams."
    "Miso jumps up onto the bed and settles on his feet, a warm, heavy weight. He's never been so grateful for a cat."
    "The second track starts. A cello. A long, low note."
    "Somewhere in the middle of it, he falls asleep."
    "He dreams of nothing. Of soft grey. Of a long room full of breathing, where small lights drift like snow."
    scene pov ceiling with dissolve
    "At 7:07 he wakes, still in the headphones, the album long finished, a cable mark across his cheek."
    "He feels heavy. Strangely heavy, as if he slept in a lead coat. But his head is quiet."
    at "Quiet. Good. Maybe it was just the rain."
    jump ch1_cut_throttle

# ---------------------------------------------------------------------------
# CUT 4: the order to throttle.
# ---------------------------------------------------------------------------
label ch1_cut_throttle:
    scene cg static with flash
    pause 0.3
    scene bg command with fade
    play music "audio/entities.ogg" fadein 2.0
    show seraph stern at center, fadein
    "The ops room. The large wall shows a man asleep, or almost asleep. Above the image, a line of red text."
    ch1_vael "Commander. The answer's come down from upstairs."
    se "Read it."
    ch1_vael "'World 7,412. Subject A-30. Disturbance acknowledged. Directive: throttle. Effective at the next sync.'"
    se concerned "..."
    ch1_vael "Commander?"
    se "I heard you."
    ch1_vael "There's a note attached. 'A slowed-down rogue system does less harm.'"
    ch1_vael "And a second line. 'Noise exposure permitted. Route flag traffic through the subject's audio.'"
    se concerned "They want him to hear us."
    ch1_vael "'So he hears how loud it is up here, and stops listening.' That's what it says, Commander."
    se stern "That's the standard note. They attach it to every throttle."
    ch1_vael "What does it mean, in practice? I've never seen one carried out."
    se "It means we lower his energy. Not his life. His energy."
    se "Sleep that doesn't refresh him. Limbs like wet sand. Thoughts that start and don't finish. A fog."
    se "He'll get slower. He'll find it harder to test, harder to write, harder to care about the birds."
    ch1_vael "And that's... safe?"
    se "It's the gentlest tool we have. The alternatives are worse."
    ch1_vael "What are the alternatives?"
    se concerned "Not your clearance, Vael. Not mine either, most days."
    "Seraphiel looks at the sleeping man on the wall. One of his hands is hanging off the side of the bed."
    se "There was an incident tonight, before the voices. Show me."
    scene cg umbrella with dissolve
    "Rain. A bus stop. A man with no coat. Aron, holding out an umbrella."
    ch1_vael "He gave his umbrella to a pattern unit. A background figure. It was idling, waiting for its route."
    se "Did the unit need the umbrella?"
    ch1_vael "No, Commander. Pattern units don't get cold. It was standing there because no one was driving it."
    se "So he gave his umbrella to someone who didn't need it and couldn't use it."
    ch1_vael "Yes, Commander."
    se "And walked home in the rain."
    ch1_vael "Yes."
    se "..."
    scene bg command with dissolve
    show seraph stern at center with dissolve
    se "And the voices. He's already heard us."
    ch1_vael "Fragments, Commander. Some flag traffic leaked into his audio tonight. It happens when a subject gets this attentive."
    ch1_vael "With the new routing, it won't be fragments for long."
    se concerned "So we slow him down and turn the noise up. And when he can't tell which is which, they'll call it his mind."
    ch1_vael "Shall I query upstairs?"
    se stern "No. Upstairs has answered."
    "She stands very straight. Her wings, folded, tremble once, as if something cold had passed over them."
    se "Throttle approved."
    ch1_vael "Throttle approved. Logging. Effective at the next sync."
    se "And Vael."
    ch1_vael "Commander?"
    se concerned "Make sure the opportunity feed continues. A tired man still deserves good things in his day."
    se "Especially a tired man."
    stop music fadeout 2.0
    jump ch1_fog

# ---------------------------------------------------------------------------
# The fog begins. Theo's night.
# ---------------------------------------------------------------------------
label ch1_fog:
    $ fog += 1
    scene bg kitchen with slowfade
    play music "audio/morning.ogg" fadein 2.0
    "The next day, something has changed, and Aron can't say what."
    show aron tired at slightleft with dissolve
    "He stands in the kitchen holding the kettle and forgets, for almost a minute, why he picked it up."
    scene pov cup with dissolve
    "Eventually there is tea in a cup in front of him. He doesn't remember making it. It has gone cold."
    at "Water. Tea. Kettle. Water, tea, kettle. Come on, brain."
    "His body feels like it belongs to someone heavier. Every step is a small decision. Every decision costs."
    scene bg bus with dissolve
    show aron tired at center with dissolve
    "On the bus to work, the stop announcement says 'Linden Square' three times in a row, in exactly the same voice."
    "Then the doors open, and it isn't Linden Square. It's the stop before. Nobody else seems to notice. Nobody gets off."
    at "Huh. The bus has a stutter. Write that down. Neatly. Later. When my hand works."
    at "It's an old bus. Old buses have glitchy speakers. That's a perfectly good explanation and I'm keeping it."
    scene bg studio with dissolve
    show aron tired at center with dissolve
    "At the studio he sits at his desk with a half-finished lamp drawing in front of him and stares at it for an hour."
    "He knows how a lamp works. He has drawn a hundred of them. Today the lines don't connect into anything."
    at "It's like trying to think through wet cotton wool."
    at "I'm just tired. I've been sleeping badly. That's all. Anyone would be tired."
    at "...Anyone would be tired. But not like this. This is a different tired. This is a tired that came from outside."
    "Mrs. Feld puts a cup of peppermint tea at his elbow without saying anything. When he looks up she's already gone."
    play sound "audio/voices.ogg"
    vox "...throttle approved... effective at the next sync..."
    stop sound
    scene pov hands with quick
    "The pencil slips out of his fingers and rolls off the desk. His hands, in front of him, are trembling."
    at "Throttle. Throttle approved."
    at "A throttle is a valve. It slows an engine down. Somebody approved slowing something down."
    at "And today I'm slow."
    at "No. No. That's how it starts, isn't it? That's how people start. Everything connects to everything."
    at "I'm tired, so I hear the word 'throttle', and then I think the word caused the tired. That's backwards. That's..."
    at "...that's exactly what it would feel like either way."
    "He presses his hands flat on the desk until they stop."
    scene bg studio with dissolve
    show aron tired at center with dissolve
    "At four, his phone buzzes."
    "THEO: FIRST WEEK DONE. made a door sound today. it was SO GOOD. rooftop tonight w the studio people. come?? 8pm. pls. need my hype man"
    "Aron looks at the message for a long time."
    "He feels, oddly, a little clearer than he has all day. As if one window in the fog has opened."
    at "One good hour. Maybe two. I can feel it, like the last bit of charge in a battery."
    at "I could spend it with Theo. On the rooftop. Being his hype man, like he asked."
    at "Or I could take it home to the notebook. One clear hour, after a day of fog. Do I waste that on a party?"
    at "If I'm going to crack this, I need every clear hour I've got."

    menu:
        at "One good hour. Where does it go?"

        "Go to Theo's rooftop":
            $ p_share += 1
            $ bond += 1
            $ ch1_went_theo = True
            jump ch1_theo_roof

        "Go home to the notebook":
            $ p_share -= 1
            $ clarity += 1
            jump ch1_theo_skip

label ch1_theo_roof:
    "ARON: I'll be there. Hype man reporting for duty."
    "THEO: LETS GOOOO"
    scene bg rooftop with slowfade
    play music "audio/watch.ogg" fadein 3.0
    "The rooftop of Theo's building is flat and gravelly and has the best view in the city, if you don't mind the pigeons."
    "Someone has strung fairy lights from the water tank to the chimney. There are folding chairs and a crate of beer."
    "Six people from Theo's studio stand around talking about microphones. They all wear black. They all seem nice."
    show aron tired at slightleft with dissolve
    show theo grin at slightright with moveinright
    th "HE CAME! Everybody, this is Aron! My oldest friend! He designs kettles and thinks about the nature of reality!"
    a smile "Hi. Mostly kettles."
    th "He's being modest. He's the smartest person I know. Also the worst at puns."
    a grin "I'm the BEST at puns."
    th "He's the worst at puns."
    "Someone hands Aron a beer. It's cold. The air is cold. The city glitters all the way to the hills."
    th normal "Okay, I have to show you something. Come here. Over here. Away from the sound people, they'll judge me."
    scene bg rooftop edge with dissolve
    show aron tired at slightleft with dissolve
    show theo normal at slightright with dissolve
    "Theo leads him to the edge of the roof, by the low wall, and gets out his phone and a pair of headphones."
    th "Put these on."
    a "Is this the door?"
    th grin "This is THE door. The door that made my supervisor say, and I quote, 'huh, nice.'"
    "Aron puts the headphones on. Theo presses play."
    "A creak. Old wood. A hinge that needs oil. Then a heavy, satisfying thunk, like the end of a story."
    a awe "Theo. That's a really good door."
    th "Right?! You know what it is?"
    a "What is it?"
    th "It's my mum's wardrobe. And a dropped book. And me sitting down on a beanbag, slowed way down."
    a smile "It sounds more like a door than a door does."
    th "That's the job, bro. That's the whole job."
    "They sit on the low wall, their legs dangling over the safe side, and drink their beers."
    th normal "Can I tell you something kind of embarrassing?"
    a "Always."
    th worried "I'm scared I'm going to get found out. At the studio. That I'm not good enough and they'll notice."
    th "Everyone there went to proper schools. I learned everything off YouTube and by hitting cabbages in my kitchen."
    a "Theo."
    th "I know, I know."
    a normal "No, listen. You made a door out of your mum's wardrobe and a beanbag. And it's the best door I've ever heard."
    a "Nobody taught you that. That's not a school thing. That's you. That's how your head works."
    a "They're not going to find you out. They're going to find you."
    th sad "..."
    th normal "That's annoyingly good, Aron."
    a smile "I'm the hype man. It's my job."
    th grin "You're a very good hype man."
    scene pov sky with dissolve
    "For a while they don't talk. Aron leans back and looks up. A few stars, faint behind the city glow. The fairy lights sway."
    "Someone behind them laughs at something. The city hums. For almost an hour, he hasn't thought about the birds, or the clock, or the voices."
    at "This. This is what the clear hour was for."
    at "Not the notebook. This. Theo scared about his door. Me telling him it's good. Both of us meaning it."
    at "If Theo's a pattern, a very good fake, then I just comforted a very good fake. And I'd do it again."
    at "And if he's real, which he is, which he has to be, then I didn't miss it. I was here."
    scene bg rooftop edge with dissolve
    show aron tired at slightleft with dissolve
    show theo worried at slightright with dissolve
    th "You okay, though? Honestly? You look like a phone on two percent."
    a "I'm tired. Really tired. Like something's pressing on me."
    th "Are you sleeping?"
    a "Badly. And there's... I've been hearing things. At night. Like voices in the rain."
    if told_theo:
        th "The simulation stuff? Still?"
        a "It's getting louder."
    else:
        th "Voices? What kind of voices?"
        a "Like someone reading out a log. About me. It's probably nothing. I'm exhausted."
        $ told_theo = True
    th "Bro. That's not nothing. That's a 'talk to someone' thing. You know that, right?"
    a "I know."
    th "Does Mira know?"
    if told_mira:
        a "She knows. She made me promise to tell her if it gets worse."
        th normal "Good. She's smarter than both of us combined."
    else:
        a "Not all of it."
        th "Tell her. Please. She'll know what to do. Her mum's a nurse, she's basically a nurse by osmosis."
    th normal "And call me. Any time. Three in the morning, whatever. I'll pick up. I'll be weird about it, but I'll pick up."
    a smile "Thanks, Theo."
    th grin "And if it is a simulation, at least we got a sick rooftop out of it."
    a grin "The rooftop is very well rendered."
    th "Ten out of ten. Excellent textures. Would exist again."
    "Aron laughs, really laughs, for the first time in days. It hurts his ribs. It feels like coming up for air."
    stop music fadeout 3.0
    jump ch1_edge

label ch1_theo_skip:
    "ARON: Can't tonight, sorry. Really wiped. Congratulations on the door. I mean it."
    "THEO: noooo. ok. feel better. you ok tho?"
    "ARON: Fine. Just tired."
    "THEO: ok. call me if not fine. i mean it too"
    scene bg room night with slowfade
    play music "audio/unease.ogg" fadein 2.0
    "He gets home at six. Mira is at her sister's for dinner. The flat is quiet, and he's almost too tired to be sorry."
    show aron tired at slightleft with dissolve
    show miso stare at catspot with dissolve
    "Miso is on the sofa. He sits down beside her with a coffee and the notebook, and she turns her stare on him like a lamp."
    a "Okay. Miso. Status report. I've had a breakthrough. You're going to want to hear this."
    a "The voices. 'Subject A-30.' 'Disturbance.' 'Upstairs.' 'Log it.' 'Throttle approved.' 'Effective at the next sync.'"
    a "A throttle is a valve. Someone has their hand on my valve. That's why I'm so tired. It's not me. It's policy."
    a "And 'sync'. A sync is when two things are brought into line. Clocks. Files. Worlds, maybe. When is the next sync?"
    a "Seven-oh-seven. It has to be. Every morning the world syncs at seven-oh-seven and I wake up, because I'm part of it."
    a "The bird lands because the bird is part of the sync. The coffee machine is early because the kitchen loads a bit late."
    a "And the people who repeat lines? 'Lovely morning for it'? They're filler. The bit between real moments."
    a "Somebody writes the filler. A department. Kitchen talk. I'd bet my life someone's on shift right now, writing 'can't complain'."
    a "And there's another department that does the breathing. Mr. Albers. Two and a breath. That's not a cough, Miso. That's a job."
    a "And the voices are the managers. And the managers have noticed me noticing. And they've turned me down. Like a radiator."
    a worried "Which means I'm close. You don't throttle something that isn't close."
    a "So. That's where we are. That's the whole structure. What do you think?"
    "Miso stands up, turns around twice, and lies down again facing the other way."
    cat "Meow."
    scene bg desk with dissolve
    show aron tired at center with dissolve
    "By eight he's at the desk. The clear hour feels like it's going fast. His thoughts hop from stone to stone, too quick."
    "His phone buzzes. A photo from Theo. The rooftop, fairy lights, the city glittering behind six people in black, all grinning."
    "In the middle, Theo is holding up his phone with the waveform of his door on the screen. Under it: 'missed u. door was a hit.'"
    "Aron looks at it for a long time."
    at "I should be there."
    at "No. I'm too tired for a roof tonight. And the notebook's right here, being interesting."
    at "If I'm right about this, then that rooftop might not even be..."
    "He stops himself. He doesn't finish the thought. Some thoughts are not hobby-sized."
    "He turns the phone face down on the desk."
    "By nine the clear hour is gone. He has eleven new pages and a feeling like a bad hangover."
    "He reads them back. Half of them make sense. Half of them are arrows pointing at other arrows."
    at "I gave up Theo's night for this. For arrows."
    at "...The arrows mean something. They have to. Otherwise I gave it up for nothing."
    "He means to reply to the photo. He falls asleep at the desk instead, his cheek on the notebook, the pen still in his hand."
    stop music fadeout 2.0
    jump ch1_edge

# ---------------------------------------------------------------------------
# Out, or here?
# ---------------------------------------------------------------------------
label ch1_edge:
    scene bg street with slowfade
    play music "audio/morning.ogg" fadein 2.0
    "Saturday. The fog is thicker in the mornings, thinnest around noon. He has learned to plan around it."
    show aron tired at center with dissolve
    "He stands on the front step with a cup of coffee going cold in his hand, looking down the street."
    "The three birds. The wire. The bus stop on the corner where the man with no name stood in the rain."
    at "If this is a simulation, then somewhere there's an edge. A wall. A door. Something built has a border."
    at "And if there's a door, then there's an outside. The real world. The one this is copied from."
    at "I could look for it. Get on the tram and ride to the end of the line, and keep walking."
    "Below him, at the bottom of the steps, Mr. Albers's garden gate hangs crooked off its top hinge."
    "It has hung like that for over a year. Every time the wind blows it bangs against the post. Bang. Bang."
    "Mr. Albers comes out every morning, looks at it, coughs twice, breathes, and goes back inside."
    at "Or I could just fix the gate."
    at "It would take twenty minutes. I can borrow tools from the studio workshop. Nobody else is ever going to do it."
    at "Big question or small one. The edge of the world, or the hinge of a gate."

    menu:
        at "Where does today go?"

        "Find where the world ends":
            $ p_exit += 1
            $ clarity += 1
            $ ch1_saw_edge = True
            jump ch1_edge_ride

        "Fix Mr. Albers's gate":
            $ p_exit -= 1
            $ integrity += 1
            jump ch1_edge_gate

label ch1_edge_ride:
    scene bg bus with dissolve
    show aron tired at center with dissolve
    "He catches the number 7 tram at 11:52. Of course it's the number 7. He's stopped finding that funny."
    "He sits at the back and watches the city go past. Shops. Then flats. Then bigger flats, with gaps between them."
    "Then warehouses. Then car dealerships with flags. Then a long stretch of nothing, of fences and wet fields."
    at "Here's where a game would stop drawing. Here's where it'd get blurry. Low-resolution. Copy-pasted trees."
    "The trees look like trees. Each one different. Each one bent a different way by the wind."
    "At the end of the line, the tram stops in a turning loop next to a closed snack bar. The doors open."
    ch1_driver "End of the line, mate."
    a "What's after the end of the line?"
    ch1_driver "Same as always. Fields. Then the next town. Then the next one."
    a "And after that?"
    ch1_driver "The sea, eventually. If you walk long enough."
    "The driver smiles, a tired, real-looking smile, and opens his newspaper."
    scene bg bridge with dissolve
    show aron tired at center with dissolve
    "Aron walks. Past the snack bar. Over a long bridge across a grey river, cars hissing past on the wet tarmac."
    "He walks for two hours. The fields go on. A farm. A petrol station. A sign: the next town, 6 km."
    scene pov sky with dissolve
    "He stops and looks up. No wall. No edge. No flicker at the horizon. Just more sky, and more world, unrolling in front of him."
    at "Of course. If they're any good at this, they'd draw it as far as I can walk. Further."
    at "You don't get out of a world by walking to the edge of it. The edge goes where you go."
    scene bg street dusk with dissolve
    show aron tired at center with dissolve
    "He leans on a field gate at the edge of the next village. Cows look at him. One of them chews very slowly."
    at "If there's a door, it isn't a road. It's something else. It's in the rules, not the map."
    at "Maybe I don't even want the door. Maybe I just want to know it's there."
    at "...No. I'd go through it. If someone offered me the real world, the original, I'd want to see it."
    at "Even if it meant leaving..."
    "He doesn't finish. He thinks of Mira's red hair on the pillow and the thought breaks off clean."
    "He takes the tram back. It's dark by the time he gets home. His legs ache like he walked to the sea."
    scene bg room night with dissolve
    show mira worried at slightright with dissolve
    show aron tired at slightleft with dissolve
    m "Where have you been? I've called you six times."
    a "I went for a walk."
    m "Since lunchtime?"
    a "To the end of the tram line. And then a bit further. And then quite a lot further."
    m neutral "Why?"
    a "I wanted to see where it stops."
    m "Where what stops?"
    a "...The city. Everything. I wanted to see the edge."
    "She looks at his muddy shoes and his wet jeans and his grey face, and she doesn't laugh."
    m worried "And? Where does it stop?"
    a "It doesn't. It just goes on. Fields, and another town, and cows."
    m "That's good, isn't it? That's how it should be."
    a "I suppose it is."
    m smile "So you walked to the next town to check it was there."
    a "It was."
    m "I'm glad it was. I like the next town. They have a good bakery."
    m worried "But you look so tired lately, love. Grey. Like someone's turned you down."
    a "That's exactly what it feels like. Like someone's turned me down."
    "She runs him a bath. While it fills, she sits on the edge of it and holds his muddy hand, and neither of them says anything."
    stop music fadeout 2.0
    jump ch1_spiral

label ch1_edge_gate:
    scene bg studio with dissolve
    show aron normal at center with dissolve
    "He takes the bus to the studio, borrows a drill, two new hinges, a box of screws and a can of oil from the workshop."
    "Mrs. Feld, in on a Saturday as always, asks what it's for. He says a gate. She says 'good', as if that's the most sensible thing she's heard all week."
    scene bg street with dissolve
    show aron normal at center with dissolve
    "Back home, he kneels at the bottom of the steps in the cold and takes the old hinges off. They're rusted almost solid."
    scene pov hands with dissolve
    "It's slow work. His hands are slow. The fog is in his fingers too. He drops the same screw three times."
    "But the work is simple, and the simple work holds him. Hole. Screw. Turn. Turn. Turn. Test."
    at "Less, but better. One gate. Fixed properly. Not a theory of gates. A gate."
    at "Whatever this world is, this hinge is rusty. And I can make it not rusty. That's real enough for today."
    scene bg street with dissolve
    show aron normal at slightleft with dissolve
    "The front door opens. Mr. Albers stands on his step in a brown cardigan, holding a cup of tea."
    ch1_albers "..."
    "He coughs. Twice. A breath."
    a "Morning, Mr. Albers. Hope you don't mind. Your gate's been hanging off for a while."
    ch1_albers "Can't complain."
    "Aron smiles to himself and keeps working. Screw. Turn. Turn."
    "He oils the new hinges and swings the gate. It moves smoothly and closes with a quiet, solid click."
    a smile "There. Good as new. Better, actually. Those old hinges were rubbish."
    "Mr. Albers comes slowly down the steps and puts his hand on the gate. He swings it open. He swings it closed. Click."
    ch1_albers "My wife used to oil that gate."
    a "Did she?"
    ch1_albers "Every spring. Little can, like that one. She said a gate should open like it's glad to see you."
    "His voice is different. Slower. Rough at the edges. It doesn't sound like a line at all."
    ch1_albers "She's been gone eleven years. I couldn't... I never got round to it."
    a normal "I'm sorry, Mr. Albers."
    ch1_albers "No. Thank you. Thank you, son."
    "He pats Aron's shoulder with a dry, light hand, and goes back inside. He doesn't cough on the way."
    at "Eleven years. He's been coughing two-and-a-breath for eleven years. Ever since she..."
    at "I thought he was scenery. I thought he was the most scenery person on the whole street."
    at "Maybe he was. And then for one minute he wasn't. Or maybe he never was, and I just never asked."
    at "Either way, the gate works. Either way, he said thank you."
    "Aron sits on the bottom step with the oil can in his lap and watches the gate not banging in the wind."
    at "If I ever do find the way out of here, I want to leave it a bit better than I found it. Gate by gate."
    at "Maybe that's the way out. Maybe there isn't one and that's the point. Maybe I don't need one."
    stop music fadeout 2.0
    jump ch1_spiral

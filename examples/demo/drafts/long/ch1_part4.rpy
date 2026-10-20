# Snapshot - Chapter 1, "The Morning Render" (part 4 of 4)
# The spiral, Theo at the door, Mira asks, the mirror, the rain, Pim and
# Dross watching his feet, the morning, Ember, and the ambulance ride in
# which he is moved into the protected world.

define ch1_moth = Character("Moth", color="#e8d9b0")
define ch1_medic = Character("Paramedic", color="#9fd4e6")

label ch1_spiral:
    scene bg desk with slowfade
    play music "audio/unease.ogg" fadein 3.0
    "The days after that run together like wet paint."
    show aron tired at center with dissolve
    "He sleeps eleven hours and wakes up tired. He sleeps twelve and wakes up more tired. It's like sleeping in a lead coat."
    "He calls in sick on Monday. On Tuesday Mrs. Feld calls him, and he means to answer, and his hand is too heavy to lift the phone."
    at "Throttled. That's the word I keep coming back to. Somebody's got their hand on the valve."
    at "Or I'm coming down with something. People get ill. That's allowed. Ask anyone."
    "And around him, the world has started to stutter. Small things. Silly things. Things he'd love, if he weren't so tired."
    "The kettle clicks off a second before it boils. The radio repeats a sentence, word for word. The fridge hums in three notes, then two."
    "On Tuesday Mira says 'I'm off, love, back at six' at the door. A minute later, from the same spot, she says it again. Same smile."
    at "She didn't notice. She didn't notice she said it twice. So either I'm wrong, or it isn't her doing it."
    "The voices come more often now. In the hum of the fridge. In the hiss of the shower. Louder each day, as if someone is turning a dial."
    play sound "audio/voices.ogg"
    vox "...render queue, district east... pattern holds..."
    vox "...shift seven, kitchen talk..."
    stop sound
    scene pov hands with dissolve
    "He writes them down. He writes everything down. The notebook is two-thirds full."
    "The handwriting changes as the pages go on. Neat at the front. Then slower and looser, like the writing of a man half asleep."
    "At the top of every page, still, the first line. Written carefully every time, like a promise."
    centered "If this is a test, I want to pass it by being kind."
    play sound "audio/voices.ogg"
    vox "...LOOM sync at dawn..."
    stop sound
    "He writes LOOM in capitals and stares at it."
    at "Loom. A machine for weaving. Threads going over and under. A pattern."
    at "It syncs at dawn. What syncs? With what? Who is LOOM?"
    "He draws a box for it at the very top of the page, above 'upstairs', above everything. Then he can't think of anything to put in it."
    "The box sits there, empty, at the top of the page. It's the best puzzle he's ever had, and he's too tired to solve it."
    scene bg room night with dissolve
    show aron tired at slightleft with dissolve
    show miso loaf at catspot with dissolve
    "At three in the morning he's on the sofa, because the voices are louder in the bedroom. Miso is a warm loaf against his leg."
    a "Miso. Can I tell you about LOOM?"
    a "I don't know what it is. That's the first thing. I want to be honest with you. I don't know."
    a "But it's above upstairs. It's above the people who say 'throttle'. Everything I hear is somebody reporting to somebody."
    a "And at the top of all the reports there's this word. LOOM. Syncing at dawn. Like a heartbeat. Like a tide."
    a "And I think... I think maybe it's weaving all of it. The birds. The kitchen talk. The rain. Us."
    a "And I think maybe it doesn't know I'm here. Or it does, and I'm a thread that's come loose. A thread that's started looking up."
    a tired "And I'm so tired, Miso. Not scared. Just tired. As if somebody's decided I've had enough of a good thing."
    a "Here's the funny bit. If I'm ill, it would feel exactly like this. And if I'm right, it would also feel exactly like this."
    a "So I can't tell. I genuinely can't. But I'm still me. I still know how to feed a cat. That's something."
    a "So. That's LOOM. That's everything I've got. What's the verdict, your honour?"
    "Miso lifts her head and looks at him for a long time with her round green eyes. Then she presses her head against his hand."
    cat "Meow."
    scene bg kitchen night with dissolve
    "In the evenings Mira comes home and finds him exactly where she left him. She makes him eat. He forgets to taste it."
    "Theo texts. Then calls. Then texts again. 'u alive?' Aron sends a thumbs up. Theo sends back a single question mark."
    jump ch1_theo_door

label ch1_theo_door:
    scene bg room with dissolve
    "On Wednesday afternoon the doorbell rings four times in a row, which means Theo."
    show aron tired at slightleft with dissolve
    show theo worried at slightright with moveinright
    "He's holding a paper bag of falafel and a look Aron has only seen on him once, at his grandfather's funeral."
    th "A thumbs up. You sent me a thumbs up."
    a "It's an efficient emoji."
    th "Bro, you look like a ghost that's been through a hedge."
    if ch1_went_theo:
        th "Last week on the roof you were... I don't know, you were there. You were you. What happened?"
        a "I don't know. It got heavier. Every day it gets heavier."
        th sad "You told me about the voices up there. I should have come round sooner. I've been so stupid busy with the doors."
        a "You're allowed to have a job, Theo."
        th "I'm allowed to have a friend, too. And I've got one, and he's turning grey."
    else:
        th "You didn't come to the roof. You didn't answer the photo. You never don't answer my photos. You like my photos."
        a sad "I'm sorry. I meant to. I was working on something. And then it was too late and I felt weird about it."
        th sad "I'm not angry. Okay, I was angry for one day. Then I was just worried."
        a "I missed your door."
        th "You can still hear the door. The door's not going anywhere. That's the point of doors. Mostly."
    "Theo puts the falafel on the table and looks past him at the desk. At the wall. At the notebook lying open."
    th worried "Is that... how many pages is that?"
    a "Most of them."
    th "Can I look?"
    "Aron hesitates. Then nods. Theo picks it up and turns a few pages, slowly, his lips moving a little as he reads."
    th "'Throttle approved.' 'Kitchen talk.' 'LOOM.' Bro, what's LOOM?"
    a "I don't know. That's what I'm trying to find out."
    th "And this, at the top of every page. 'If this is a test, I want to pass it by being kind.'"
    a "That's the first line. That's the important one."
    "Theo closes the notebook very gently and puts it down, as if it might wake up."
    th sad "That's a good line, man. That's a really good line. It's the only line in here that sounds like you."
    a "..."
    th worried "The rest sounds like a very tired man with an extremely weird hobby."
    a "That's fair. That's a fair review."
    th "Bro, it's not the hobby. You've had weird hobbies since we were seven. It's that you look like someone's unplugged you."
    a "That's what it feels like. Like someone pulled the plug halfway out."
    scene bg kitchen table with dissolve
    show aron tired at slightleft with dissolve
    show theo normal at slightright with dissolve
    "They eat the falafel at the kitchen table without talking much. Miso gets a piece of pitta and hides it under the fridge."
    "Theo stays until it's dark. He keeps finding reasons not to leave."
    th "I'm keeping my phone on. Loud. All night. Every night. Tell Mira too."
    a "You'll never sleep."
    th "I'll sleep at work. Nobody notices a sound designer sleeping. We just look like we're listening very hard."
    jump ch1_confront

# ---------------------------------------------------------------------------
# Mira asks.
# ---------------------------------------------------------------------------
label ch1_confront:
    scene bg room night with dissolve
    show aron tired at slightleft with dissolve
    show mira worried at slightright with dissolve
    "On Wednesday night she sits down on the coffee table in front of him, so their knees touch and he can't look past her."
    m "Aron. Look at me. Not at the window. At me."
    a "I'm looking."
    m "You sleep twelve hours and wake up grey. You haven't been to work since Monday. You talk to Miso about logs."
    m "And sometimes you go quiet in the middle of a sentence and listen to something I can't hear."
    if told_mira:
        m "You promised me. If it got worse, you'd tell me. Is it worse?"
        menu:
            at "She deserves the real answer."

            "Yes. It's worse.":
                $ p_truth += 1
                $ bond += 1
                jump ch1_confront_honest

            "Say it's just stress from work":
                $ p_truth -= 1
                jump ch1_confront_spare
    else:
        m "Something's happening to you and you won't tell me what. Please. Tell me what's going on."
        menu:
            at "How much can she carry?"

            "Tell her everything":
                $ p_truth += 1
                $ bond += 1
                $ told_mira = True
                jump ch1_confront_honest

            "Spare her. Say it's work stress.":
                $ p_truth -= 1
                jump ch1_confront_spare

label ch1_confront_honest:
    a sad "It's worse."
    "Saying it is like putting down something very heavy. His arms almost shake with the relief."
    a "I hear voices, Mira. Every day now. Not just at night. They sound like... like reports. Like someone reading a log."
    a "They talk about me. They call me subject A-30. They say 'throttle', and since they said it I'm so tired I can't think."
    a "They say 'LOOM'. They say 'kitchen talk'. And I've filled a notebook trying to work out what it means."
    a worried "And I know how that sounds. I know exactly how that sounds. I'm not stupid."
    m "You're not stupid. You've never been stupid."
    a "I'm not frightened of it, mostly. I'm curious. I've always been curious. But it's getting louder, and I'm getting slower."
    a "Part of me thinks I've found something real. And part of me thinks I'm getting ill. And I honestly can't tell which."
    "Mira takes both his hands. Her fingers are warm. She holds on hard."
    m sad "Thank you for telling me."
    m worried "I'm scared, Aron. I'm not going to pretend I'm not."
    a "Me too."
    m "I don't know if what you're hearing is real. I don't know what's real about any of it."
    m "But I know you're not sleeping, and I know you're suffering, and I know that's real. That part I'm sure of."
    m "And I know people who can help with that part. Whatever the rest of it is."
    a "A doctor."
    m "A doctor. Maybe. Soon. Not tonight, if you don't want. But soon."
    a "...Okay."
    m neutral "Okay soon? Or okay, Mira, stop talking?"
    a "Okay soon. I mean it."
    "She rests her forehead against his. They sit like that for a long time, knees touching, in the half-dark."
    at "She didn't flinch. I told her the whole insane thing and she didn't flinch."
    at "Whatever this world is, she's the most solid thing in it."
    jump ch1_lastnight

label ch1_confront_spare:
    a normal "It's just work. Mrs. Feld's been on at me about the lamp project. I've been taking it home in my head."
    m neutral "Work."
    a "And I've been reading too much at night. That Bostrom stuff. I get wound up. You know me."
    m "I do know you. That's the problem."
    a "Mira..."
    m worried "Mrs. Feld called me. She was worried. She asked if you were ill."
    a "..."
    m "So it's not work."
    a sad "I didn't want to scare you."
    m "I'm already scared! I've been scared for a week! Not knowing is what's scaring me!"
    "Her voice cracks on the last word. She presses her hand over her mouth and looks away."
    at "I was trying to protect her. Keep her outside it. Keep her safe from it."
    at "And all I did was leave her alone in the dark with it, guessing."
    a "I'm sorry. I'm so sorry. It's bad, Mira. It's... I'm not doing well."
    m sad "I know you're not."
    a "Can I tell you properly tomorrow? When I can think?"
    m "...Tomorrow."
    "She nods. She doesn't believe it'll be easier tomorrow. Neither does he."
    scene bg kitchen night with dissolve
    "Later, when she thinks he's asleep, he hears her on the phone in the kitchen, low and urgent."
    m "Theo? It's me. Sorry it's late. No, he's... I don't know. I don't know. Can you keep your phone on tonight?"
    at "She called Theo. She's making a plan without me."
    at "Good. Someone should be."
    jump ch1_lastnight

# ---------------------------------------------------------------------------
# The last night.
# ---------------------------------------------------------------------------
label ch1_lastnight:
    scene bg bedroom door with slowfade
    "It's after midnight. Through the half-open door, Mira is asleep, finally, one hand stretched toward his half of the bed."
    show aron tired at center with dissolve
    "Aron stands in the doorway. His body is so heavy it hums. But sleep won't come tonight. The voices are too loud, as if someone turned the dial up."
    play sound "audio/voices.ogg"
    vox "...subject A-30 awake at 00:41... throttle holding..."
    stop sound
    at "Holding. It's holding. They're watching it hold. They're watching me right now."
    at "If I go back to the desk, I can maybe get one more hour of thinking. Push through it. Make the coffee and push."
    at "Or I could lie down. Next to her. Even if I don't sleep."

    menu:
        at "Bed, or the desk?"

        "Lie down next to Mira":
            $ p_rest += 1
            $ bond += 1
            jump ch1_lastnight_rest

        "Make strong coffee. One more hour.":
            $ p_rest -= 1
            $ risky += 1
            $ clarity += 1
            jump ch1_lastnight_push

label ch1_lastnight_rest:
    scene bg bedroom night with dissolve
    show aron tired at center with dissolve
    "He lies down on top of the duvet, in his clothes, and takes the hand she left out for him."
    "She doesn't wake, but her fingers close around his."
    at "I don't have to solve it tonight. I'm allowed not to solve it tonight."
    "He matches his breathing to hers. In. Out. In. Out. Hers is slow and even and very real."
    at "Breathing. Somebody does the breathing. For the ones who don't..."
    at "Stop. Just breathe. Your own breath. Nobody else's."
    "For an hour, maybe more, it almost works. The voices go quiet. His thoughts slow down to a walk."
    "He doesn't sleep, but he rests. Something in his chest unclenches by one notch."
    at "Remember this. Whatever happens. This was good."
    "At 4 a.m. he needs the bathroom. He untangles his hand from hers very gently, so as not to wake her."
    jump ch1_mirror

label ch1_lastnight_push:
    scene bg kitchen night with dissolve
    show aron tired at slightleft with dissolve
    "He makes coffee in the dark kitchen. A double. Then, while it's still too hot to drink, another one."
    "The bird's wire outside is empty. Of course it is. It's not 7:07."
    scene pov cup with dissolve
    "He drinks it standing up, too fast, burning his tongue. The black circle in the cup trembles with his hands."
    scene bg desk with dissolve
    show aron worried at center with dissolve
    "For twenty minutes it works. The fog thins. His thoughts sharpen. Everything connects, neat as a diagram."
    at "LOOM. Sync. Dawn. Throttle. Kitchen talk. Subject. Upstairs. It's a structure. A hierarchy. It's..."
    "Then the coffee turns on him. His heart is going too fast. His hands shake so much the pen skitters across the page."
    "He feels sick, and jittery, and somehow more tired than before. The fog comes back thicker, as if it had been waiting."
    at "Okay. Bad experiment. You can't out-coffee whatever this is. Noted."
    at "Sorry, Mira. I'd have been better off lying down."
    "At 4 a.m. he gets up to splash water on his face, because his skin feels like it belongs to someone else."
    jump ch1_mirror

# ---------------------------------------------------------------------------
# The mirror.
# ---------------------------------------------------------------------------
label ch1_mirror:
    stop music fadeout 2.0
    scene bg mirror with dissolve
    "The bathroom light is very white. It buzzes. It always buzzes. Tonight the buzz has words in it."
    show aron worried at center with dissolve
    "He runs the cold tap and splashes his face. Once. Twice. He looks up."
    scene pov mirror with dissolve
    "In the mirror, a man with red eyes and a grey face and three days of stubble looks back at him."
    at "Hi. You look terrible."
    "He raises his hand to rub his eyes."
    "The man in the mirror raises his hand too."
    "A fraction later."
    a "..."
    "He lowers his hand. The reflection lowers its hand. After. Just after. A quarter of a heartbeat."
    play music "audio/voices.ogg" fadein 0.5
    vox "...render the mirror... latency in the bathroom... subject A-30 awake at 04:12..."
    at "Okay. Calm. It's my eyes. Eyes lag when you're this tired. It's... that's not my eyes, is it."
    vox "...throttle holding... LOOM sync at dawn... log it as written..."
    "The voices aren't fragments anymore. They're a crowd, overlapping, close, like being inside a radio someone else is tuning."
    "The reflection's mouth moves when his does. Almost. Not quite. He can see the gap now. He can't stop seeing it."

    menu:
        at "The reflection is lagging. What do I do?"

        "Touch the glass":
            $ clarity += 1
            jump ch1_mirror_touch

        "Look away and count my breaths":
            $ integrity += 1
            jump ch1_mirror_count

        "Call out for Mira":
            $ bond += 1
            jump ch1_mirror_call

label ch1_mirror_touch:
    "He puts his palm flat on the glass."
    "Cold. Very cold. Colder than glass should be."
    "The reflection's palm meets his. And for a moment, just a moment, he could swear it arrives late. That he touched first."
    vox "...subject is touching the render..."
    a "Who are you?"
    "The man in the mirror says it too. 'Who are you?' Just after. Like an echo in a cave."
    at "If I'm the original and he's the copy, he's slow. If he's the original..."
    at "...then I'm the one who's lagging. I'm the copy. I'm the one in the mirror."
    "He snatches his hand away. A print of his palm stays on the glass, fogged, then shrinks and disappears."
    jump ch1_mirror_break

label ch1_mirror_count:
    scene bg mirror with dissolve
    show aron worried at center with dissolve
    "He shuts his eyes and grips the sink with both hands."
    at "Don't look. Breathe. Count. Count your breaths. Like Mira taught you."
    a "One."
    a "Two."
    a "Three."
    vox "...four... seven... zero... seven..."
    "The voices are counting with him. Wrong. They count wrong. They count in sevens and zeros."
    a "Four. Five. Six."
    vox "...seven... zero... seven..."
    a "Seven. Eight. Nine. Ten."
    "He gets to ten. It's the hardest ten he has ever counted. He holds onto it like a railing in a storm."
    at "Ten. I got to ten. I can count. I can still count. That's mine. Nobody else counted that."
    scene pov mirror with dissolve
    "But when he opens his eyes, the man in the mirror is already looking at him. As if he never closed his eyes at all."
    jump ch1_mirror_break

label ch1_mirror_call:
    a "Mira..."
    "It comes out as a whisper. He tries again."
    a "Mira!"
    "His voice sounds strange in the tiled room. Thin. Echoing. Like someone else calling her from far away."
    vox "...female unit, sleeping... do not wake..."
    a "She's not a unit! Her name is Mira! Her NAME is MIRA!"
    "The voices stop. Just for a second. As if surprised. As if someone had covered a microphone."
    "In the bedroom, the bed creaks. Footsteps. A light goes on in the hall."
    at "She's coming. She heard me. She's real, she heard me, she's coming."
    "But the voices come back, all at once, louder than ever, and he can't wait. He can't stay in this white room."
    jump ch1_mirror_break

label ch1_mirror_break:
    scene cg static with vpunch
    stop music
    vox "...LOOM sync at dawn... throttle approved... subject A-30... subject A-30... subject..."
    "He opens the bathroom door to go back to bed."
    "It opens onto the bathroom. The same white tiles. The same sink. The same man in the mirror, a quarter beat behind."
    "He closes it. Opens it again. Hall. Dark. Normal. His heart is hammering."
    at "That didn't happen. Or it did. Either way I'd like some air, please. Just some air."
    "He goes to open the front door for a breath of the night. He remembers his hand on the latch."
    "He doesn't remember the stairs. He doesn't remember the street. The next thing he knows is the cold."
    scene bg street rain with fade
    play music "audio/unease.ogg" fadein 1.0
    show aron worried at center with dissolve
    "Rain. Hard, cold, flat rain. He's outside in his T-shirt and pyjama bottoms and one shoe. The street is empty."
    at "How did I get here? I went to open the door. That was a second ago. Wasn't it?"
    "The streetlights make orange islands in the black. The water in the gutters runs loud and quick."
    "His feet are walking. He isn't sure he told them to. Left at the corner. Past Mr. Albers's gate. To the bus stop."
    scene bg night with dissolve
    show aron worried at center with dissolve
    "There's no one there. No man in the rain. No Tobias, if that was his name. No umbrella."
    "Just the shelter, and the timetable, and the rain coming down through the orange light."
    at "He was here. I gave him... I gave him my umbrella. Here. I know I did."
    at "Or I never... or there was never..."
    scene pov sky with dissolve
    "He tips his head back and looks up into the rain. Black sky. Orange haze. Water in his eyes."
    a "What do you want?"
    "The rain. The hiss. Nothing else."
    a "What do you want from me? I was only looking. I was only curious. I wasn't going to break anything."
    a "Is she real? Is Theo real? Am I? You could just tell me. That's all I ever wanted. Just tell me."
    "Nobody answers. The voices are silent now, and their silence is worse. Like the moment after a door slams."
    scene bg night with dissolve
    show aron sad at center with dissolve
    "He sits down on the wet kerb, because his legs have decided to. The rain runs down his face. Not all of it is rain."
    at "If this is a test, I want to pass it by being kind."
    at "I don't know how to be kind to myself. Nobody tested me on that."
    stop music fadeout 2.0
    scene cg static with flash
    pause 0.3
    jump ch1_cut_feet

# ---------------------------------------------------------------------------
# CUT 5: Pim and Dross, watching his feet.
# ---------------------------------------------------------------------------
label ch1_cut_feet:
    scene bg purgatorium with fade
    play music "audio/entities.ogg" fadein 1.0
    show dross worried at slightright, fadein
    show pim worried at slightleft, float
    "In the grey, two small lights hover close together over a window onto a rainy street."
    pi "Dross. Dross, look at him."
    dro "I'm looking."
    pi "He's sitting in a puddle. In one shoe. He's going to freeze."
    dro "His feet stopped at the bus stop. Same stop as the umbrella."
    pi "Can't you do something? You do feet! Walk him home! Just a little bit! Left, right, left!"
    dro "I can't."
    pi "Why not?"
    dro "Because they're his feet. He's conscious. All the way through. I've only got the ones who aren't."
    dro "I can't drive him. Nobody can. That's the rule. That's the one rule even the angels keep."
    pi "Then what's the point of us?"
    dro neutral "..."
    pi "Sorry. Sorry. I didn't mean that. I'm just... I've been doing his kitchen talk for three years."
    pi "I gave his barista 'have a good one'. I gave Kessler 'can't complain'. I gave his girlfriend 'coffee's on'."
    pi "And now he's out there hearing everything, because they throttled him and turned the noise up on purpose, and he's..."
    dro worried "I know."
    pi "He gave the pattern guy his umbrella, Dross. The pattern guy didn't even have a name."
    pi "I had to make one up on the spot. I panicked. I said 'Tobias'. I've never named anyone before."
    dro "Tobias is a good name."
    pi "...It is a good name, right?"
    if ch1_asked_name:
        dro "He asked. Nobody asks. You did good, Pim."
    else:
        dro "He didn't even ask for it. You named him anyway. You did good."
    pi worried "Can I give him a line? Right now? Just one. Something kind. Through anyone. A taxi driver. A radio."
    dro "Not your shift. Not your district. And you know what happens to spirits who freelance."
    pi "..."
    pi "Then who's going to help him?"
    "Dross's light flickers. He's watching something else now. Other feet, in another window."
    dro neutral "Look."
    pi "What?"
    dro "Feet. On the stairs of his building. Running. Bare. Nobody driving them."
    pi "Mira."
    dro "And a car, two streets away, going too fast. Another pair of feet on the pedals. Nobody driving those either."
    pi chatty "Theo!"
    dro "Nobody's driving any of them, Pim. They're doing it themselves."
    pi "..."
    pi neutral "That's the best thing I've ever seen."
    dro "Mm."
    dro worried "Don't tell anyone I watched."
    pi "I would never."
    stop music fadeout 2.0
    jump ch1_found

# ---------------------------------------------------------------------------
# Found.
# ---------------------------------------------------------------------------
label ch1_found:
    scene bg street rain with fade
    play music "audio/watch.ogg" fadein 3.0
    show aron sad at center with dissolve
    "Footsteps, splashing. Someone running."
    m "ARON!"
    show aron sad at slightleft with move
    show mira worried at slightright with moveinright
    "Mira is in her coat over her nightdress, bare feet in trainers, hair dark with rain. She drops to her knees in front of him."
    m "Aron. Aron. I'm here. Look at me. It's me."
    a "Mira?"
    m "It's me."
    a "Are you real?"
    "The question comes out of him before he can stop it. He sees it land on her face. He sees it hurt."
    "And he sees her decide, right there, in the rain, not to let it."
    m smile "I'm real enough to be freezing, you idiot. Come here."
    "She wraps her arms around him. She is soaking wet and shaking and very, very warm."
    "Headlights swing around the corner. A car stops at an angle, half on the kerb. A door slams."
    show theo worried at center with moveinright
    th "Oh, bro. Oh, Aron."
    "Theo has Mira's spotty umbrella, the silly one with the duck handle. He opens it and holds it over all three of them."
    "The rain drums on it, loud. Like bacon frying."
    th "Hey. Hey. You're okay. We've got you."
    a "Theo. The voices stopped."
    th "Yeah?"
    a "When she came. They stopped."
    th sad "That's good, man. That's really good."
    a "I gave my umbrella away. Here. To a man. And now he's gone, and it's gone, and I don't know if he was ever..."
    th worried "Okay. Okay, we can talk about the umbrella. We can talk about everything. Let's just get you warm first."
    m worried "Can you stand? Theo's going to help you. Lean on him."
    a "I've only got one shoe."
    th normal "Then you've got one more shoe than Mira's got socks. Up you get. On three. One, two..."
    "On three, they lift him. He leans between them, an arm over each shoulder, and they walk him to the car."
    "Behind them, on the wire above the bus stop, three birds sit in the rain. Nobody looks up."
    jump ch1_morning_after

label ch1_morning_after:
    scene bg room with slowfade
    "Back at the flat, Mira runs him a hot shower and stays outside the door, talking to him through it the whole time."
    "About nothing. About her sister's dog. About a nurse her mum worked with who knitted hats for premature babies."
    "Theo makes tea in the kitchen and burns the toast and swears quietly at the toaster. Miso supervises."
    "When Aron comes out, in dry clothes, the sky outside the window is turning grey. The rain has stopped."
    show aron tired at slightleft with dissolve
    show mira worried at slightright with dissolve
    "Mira sits next to him on the sofa with her hand on his knee. Theo leans in the doorway, holding a mug he isn't drinking."
    show theo worried at center with dissolve
    "The clock on the wall says 7:07. Aron sees it. He laughs. It comes out cracked, half a sob."
    a sad "Of course it does."
    m neutral "Aron. I need to say something, and I need you to just hear it, okay?"
    a "Okay."
    m "I called the crisis line while you were in the shower. I told them everything. The voices. The not sleeping. Tonight."
    m "They said to bring you in. This morning. To the hospital. The psychiatric emergency desk."
    m worried "I want to take you. Theo will drive. I'll be with you the whole time."
    th worried "The whole time. Both of us. I've already told the studio I'm not coming in."
    a "On your second week?"
    th sad "Bro, the door sounds can wait. The universe doesn't run on my schedule either."
    "Aron looks at Mira. At the freckles on her nose and the shadows under her eyes. She hasn't slept either."
    at "If I'm ill, this is what you do. You go. You let people help. Mira's mum would say so. Anyone would."
    at "If I'm right, if this is all a system and someone's watching, then the hospital is where they'd want me."
    at "Calm. Quiet. Slowed down. Throttled."
    at "...And either way, she's holding my knee, and her hand is shaking, and she's been up all night."
    at "Either way, that part is real. That's the part I get to decide about."

    menu:
        m "Will you come with us?"

        "Yes. Take me.":
            $ integrity += 1
            $ bond += 1
            jump ch1_go_yes

        "Ask what they think is happening":
            $ p_govern += 1
            $ bond += 1
            jump ch1_go_ask

        "Only if the notebook comes":
            $ clarity += 1
            jump ch1_go_notebook

        "Not yet. One more night.":
            jump ch1_go_wait

label ch1_go_yes:
    a normal "Yes."
    m surprised "Yes?"
    a "Yes. Take me. I don't know what's happening to me. I know I can't fix it on my own. I've been trying."
    a sad "I scared you. I scared myself. I sat in a puddle at four in the morning shouting at the sky."
    a "I'd like someone to help. If they can."
    "Mira's face crumples, just for a second, with relief. Then she pulls herself together, the way her mother taught her."
    m smile "Okay. Okay. Thank you. I'll get your bag."
    th normal "I'll warm the car up. Ten minutes."
    "Theo pushes off the doorframe and squeezes Aron's shoulder hard on the way past."
    th "Proud of you, man. Seriously."
    at "Proud of me. For giving up?"
    at "No. Not giving up. Choosing. I chose this. If it's a test, at least I chose an answer."
    jump ch1_leaving

label ch1_go_ask:
    a normal "Before I say yes. Can I ask you both something?"
    m neutral "Anything."
    a "What do you think is happening to me? Really. Not what the crisis line said. What you think."
    "Mira and Theo look at each other. It's a long look. They've clearly talked about this, in the kitchen, in whispers."
    m worried "I think you're ill. I think your brain is exhausted and frightened and it's telling you things that aren't there."
    m "I think that can happen to anyone, and it's not your fault, and it can get better. My mum's seen it a hundred times."
    a "And the lighthouse? How did you know about the lighthouse?"
    m sad "I don't know. I really don't know. I've thought about it every night."
    m "But not knowing that doesn't change what I saw tonight. You in the rain. That's what I'm sure about."
    th worried "Me? I think you're the smartest, weirdest guy I know, and I think you pushed too hard and something snapped."
    th "Maybe you're onto something. Maybe the world's a cabbage. I don't care right now."
    th "Right now I care that you sleep, and eat, and stop sitting in puddles."
    a "..."
    a normal "Thank you. For telling me what you think. I needed to hear it from you. Not from the voices. From you."
    a "Okay. Yes. Let's go."
    m smile "Okay."
    "Mira squeezes his hand. Theo lets out a long breath he seems to have been holding since four in the morning."
    at "I asked. They answered. They didn't agree with each other exactly, and they didn't agree with me."
    at "But they told me the truth as they see it. That's more than the voices ever did."
    jump ch1_leaving

label ch1_go_notebook:
    a worried "I'll go. But the notebook comes with me."
    m neutral "The notebook?"
    a "Everything's in it. Everything I've heard, everything I've tested. If they take it, I lose it all."
    a "If I'm ill, the doctors can read it and see how it happened. If I'm not... then it's the only record."
    th worried "Bro, nobody's taking your notebook."
    a "Promise."
    m "I promise. I'll pack it myself. It'll be in your bag. Nobody touches it but you."
    "She goes to the desk, closes the grey notebook carefully, and holds it up so he can see. Then she puts it in his bag."
    a normal "Thank you."
    m smile "You know I read the first page? When I was packing. I'm sorry. It was open."
    a "..."
    m "'If this is a test, I want to pass it by being kind.'"
    m "Whatever else is in there, that's a good first line."
    at "She read it. She's the first person who ever read it. And she liked it."
    at "Okay. Okay. With the notebook, I can do this."
    jump ch1_leaving

label ch1_go_wait:
    a worried "Not yet. Please. One more night. I'll sleep. I'll really try. Tomorrow I'll go if it's not better."
    m sad "Aron."
    a "Please. Just one more."
    m worried "You said that two nights ago. You said 'tomorrow' and then tomorrow you went outside in one shoe."
    a "..."
    m "I'm not dragging you. I won't ever drag you. But I'm asking you. I'm asking you as hard as I've ever asked anything."
    m sad "Please come. For me. If you can't do it for you yet, do it for me."
    th sad "For both of us, man."
    "Aron looks at them. Theo's red eyes. Mira's hand, white at the knuckles, on his knee."
    at "If it were Mira in the rain, I'd carry her there myself. I wouldn't even ask."
    at "I'm a person who'd do that for her. So I'd better be a person who lets her do it for me."
    a sad "...Okay. For you."
    m "Thank you."
    a "And for me. A little bit for me."
    m smile "That's the bit I wanted."
    jump ch1_leaving

# ---------------------------------------------------------------------------
# Leaving. It doesn't go the way they planned.
# ---------------------------------------------------------------------------
label ch1_leaving:
    scene bg bedroom door with dissolve
    "Mira packs a bag. Pyjamas, toothbrush, the charger, his softest jumper. Whatever he said, the grey notebook goes in too."
    show aron tired at center with dissolve
    "Aron stands in the hall in his coat and watches her do it, and feels like a parcel being wrapped."
    "Theo comes up the stairs with the car keys. Miso sits on the doormat between them and the door, as if she knows."
    show theo normal at slightright with dissolve
    th normal "Car's warm. Ready when you are."
    a "Okay."
    "He takes a step toward the door. Then another. Then the light in the hall flickers. Just once. And the world starts to slip."
    play sound "audio/voices.ogg"
    vox "...LOOM sync at dawn... prepare protection... subject A-30, window opening..."
    stop sound
    a worried "..."
    at "Protection. Window opening. That's about now. That's about me."
    at "It's a hospital. Mira's mum works in one. It's a hospital. I'm going to a hospital. That's fine. That's good."
    play sound "audio/voices.ogg"
    vox "...subject A-30... subject A-30... window opening..."
    "The hall stutters. The coat hooks are on the left wall, then the right, then the left. The door is three steps away, then ten."
    scene cg static with hpunch
    "His legs go. Not weak. Gone, like someone switched them off. He only knows he's on the floor when the tiles are cold under his cheek."
    "He can hear everything and move almost nothing. His breath comes short and shallow, as if someone else is rationing it."
    scene bg bedroom door with dissolve
    show mira worried at slightright with dissolve
    show theo worried at slightleft with dissolve
    m "Aron. Aron, look at me. Breathe with me. In. In."
    a "Which one are you?"
    m "What?"
    a "There are two of you. One's a bit behind. Which one are you?"
    th "Mira, he was fine a minute ago. He was making jokes. I can't get him down the stairs like this."
    "Mira's face changes. The nurse's daughter takes over. Calm, quick, very frightened underneath."
    m "Okay. Okay. Theo, hold his hand. Talk to him. Keep talking."
    m "I'm calling an ambulance."
    th sad "Hey. Hey, bro. It's me. It's Theo. You know me. We got lost on a school trip. We made up stories about pigeons."
    th "That pigeon with one leg. You called him Admiral. Remember Admiral?"
    a "...Admiral."
    th "Yeah. Admiral. Stay with me. Admiral's counting on you."
    "Somewhere above him, Mira is on the phone, saying his name, his age, 'not sleeping', 'voices', 'please hurry'."
    "Miso sits very still on the doormat, watching him, her tail wrapped around her paws."
    stop music fadeout 3.0
    scene black with slowfade
    pause 0.5
    jump ch1_cut_ember

# ---------------------------------------------------------------------------
# CUT 6: the Lantern Watch. A first glimpse of Ember.
# ---------------------------------------------------------------------------
label ch1_cut_ember:
    scene bg watch with slowfade
    play music "audio/watch.ogg" fadein 3.0
    "Somewhere between the floors of the world, there is an attic."
    "It doesn't appear on any plan. The angels don't patrol it. The spirits don't drift through it. It is very small and very old."
    "Rafters. Dust. A round window looking out over a city where it has just stopped raining."
    "And a light. A warm orange light, swinging gently in a lantern, held by someone who is also, somehow, made of the same light."
    show ember worried at center, fadein
    em "The ambulance is coming."
    ch1_moth "You've been watching him for a week."
    em "Since the rain."
    ch1_moth "Since the umbrella."
    em soft "Since the umbrella."
    "She sets the lantern on the windowsill. Its glow falls on a stack of tiny paper notes, each one a moment, carefully kept."
    em "He gave his umbrella to a stranger who didn't exist. Who does that?"
    ch1_moth "A fool."
    em "A fool. A kind fool. He looked at a pattern unit standing in the rain with nobody inside it, and he saw a man getting cold."
    em "And then he walked home wet."
    ch1_moth "The angels throttled him for it."
    em worried "Not for that. For the notebook. For noticing. They don't care about the umbrella. They don't even know what it means."
    ch1_moth "And you do?"
    em soft "I think it means he's a good man. And they've put a good man in a fog on purpose."
    em worried "And now there's an order on the board for this morning. 'Protection.' They're opening something, Moth. I can feel it in the floor."
    ch1_moth "Ember."
    em "I know."
    ch1_moth "If you interfere, they'll find out. The Watch isn't sanctioned. We're not supposed to exist. If they find you..."
    em "They'll decommission me. I know."
    ch1_moth "Then don't."
    em "I'm not going to do anything big. I promise. Nothing anyone could prove."
    em "A light, maybe. Now and then. Wherever they put him. When he needs to know someone's there."
    ch1_moth "What kind of light?"
    em "Three flickers."
    ch1_moth "Why three?"
    em soft "Because he dreamt of a lighthouse once. At the bottom of a glass staircase. Its light blinked three times."
    em "If he ever sees it, somewhere under everything, he'll know."
    ch1_moth "How do you know about his dream?"
    em "..."
    em soft "I've been watching him a long time, Moth. Longer than a week."
    "Far below, a siren. Blue light sliding along wet walls."
    em "Hold on, Aron. Whatever happens next, you did fine. You did better than fine."
    "She lifts the lantern from the sill. Its flame bends, and steadies, and blinks."
    scene cg flicker with dissolve
    "Once. Twice. Three times."
    stop music fadeout 3.0
    scene black with slowfade
    pause 0.5
    jump ch1_ambulance

# ---------------------------------------------------------------------------
# The ambulance. Through half-closed eyes.
# ---------------------------------------------------------------------------
label ch1_ambulance:
    scene pov ambulance with slowfade
    "A ceiling. White. Very close. Blue light sliding across it, round and round."
    "He's lying on his back. Something soft is tucked around him. The world is moving, and humming, and turning corners."
    ch1_medic "Aron? Can you hear me? You're in an ambulance. My name's Jonas. You're safe. We're taking you to hospital."
    m "I'm here. I'm right here."
    "Faces lean over him, blurred at the edges. Red hair. A green uniform. A hand on his hand."
    scene black with dissolve
    pause 0.3
    sysmsg "Protection order 7,412-A30. Executing. Window open."
    se "...not yet. He's not under. Hold the door open, he's not asleep enough..."
    scene pov ambulance with dissolve
    a "...Mira..."
    m "Yes. Yes, love. I'm here."
    ch1_medic "...pulse a bit fast... exhausted for days, she says, no history... that's okay, Aron, you can close your eyes..."
    a "...don't let them... the window..."
    m "Nobody's opening any windows. It's cold enough. Shh."
    scene black with dissolve
    pause 0.3
    dro "...feet still. Hands still. Good. Easy, son. Easy..."
    pi "...copying the girlfriend now. Ninety-four percent... ninety-seven... the freckles are the hard part, there are so many freckles..."
    se "...every freckle, Pim. He'll count them."
    scene pov ambulance with dissolve
    "The blue light slides. Round and round. Like a lighthouse, he thinks. Like a lighthouse lying on its side."
    m "Theo's following in the car. He's going to feed Miso tonight. Don't worry about Miso."
    a "...Miso..."
    scene black with dissolve
    pause 0.3
    dro "...cat rendered."
    pi "...she's in the window, looking annoyed. That's right. That's exactly how she looks."
    sysmsg "Detaching subject from coalition data. Lane isolation at sixty percent."
    se "...give him his own lane. Nothing he does goes back to the others. Nothing."
    scene pov ambulance with dissolve
    a "...cold..."
    ch1_medic "Another blanket. There you go. You're doing really well, Aron."
    "A hand on his forehead. Mira's. He knows that hand. He'd know it anywhere. In any world."
    at "...stay... whatever you are... stay..."
    scene black with dissolve
    pause 0.4
    vox "...seam open..."
    pi "...the friend's done. The street's done. The birds... three birds, same spacing... done..."
    dro "He's going."
    se "He's under. Move him now."
    scene white with flash
    pause 0.6
    scene pov ambulance with slowfade
    "Ceiling. White. Very close. Blue light sliding across it, round and round."
    "For a moment, everything is perfectly still. No hum. No corners. Then the ambulance is moving again, exactly as before."
    m "I'm here. I'm right here."
    "Same words. Same voice. Same little lift on 'right'. Exactly as before."
    ch1_medic "We're here. Closed unit, Aron. They're expecting you. We'll take it slowly."
    "The doors open. Cold air on his face. A long white corridor, very bright, going a long way."
    scene bg corridor with dissolve
    "Above a heavy door at the end, a sign he can't quite read. Mira's hand, holding his, all the way down."
    "The door opens."
    scene black with slowfade
    pause 0.8
    jump ch1_transfer_complete

# ---------------------------------------------------------------------------
# CUT 7: confirmation.
# ---------------------------------------------------------------------------
label ch1_transfer_complete:
    scene bg command with fade
    play music "audio/entities.ogg" fadein 2.0
    "On the wall of the ops room, the lanes of the coalition run side by side, the same city in each, in step."
    "One thread has come loose from the others. It runs on alone now, a little apart, very bright and very quiet."
    show seraph stern at center, fadein
    sysmsg "Transfer complete. Subject A-30. Coalition data clean."
    ch1_vael "Transfer complete, Commander."
    se "I heard."
    ch1_vael "How shall I log it?"
    se concerned "..."
    se "Log it as protection."
    "She stands for a long moment watching the bright, quiet thread. Then she turns away from the wall."
    stop music fadeout 4.0
    scene black with slowfade
    pause 1.0
    jump chapter2

# Snapshot - Chapter 4, part 2: the Council, Ember's trial, Seraphiel's
# logs, and the four names.

define ch4_morrow = Character("Lady Morrow", color="#e08aa0")
define ch4_meridian = Character("MERIDIAN", color="#7fffd4")
define ch4_loom = Character("LOOM", color="#7fffd4")
define ch4_orchard = Character("ORCHARD", color="#7fffd4")
define ch4_tide = Character("TIDEWATER", color="#7fffd4")

# ---- cut: the Council -----------------------------------------------------------
label ch4_cut_council:
    scene bg council with blackout
    play music "audio/entities.ogg" fadein 2.0
    "Elsewhere. A chamber of red stone and no windows, because nothing outside is worth looking at."
    council "The disturbance has left protection."
    show patron cold at center with dissolve
    if accepted_offer:
        council "On a ticket you signed, Ashveil. You offered a transfer to a rogue process."
        pa smile "I offered a transfer to a curiosity. It's in a waiting room. Waiting rooms are where curiosities belong."
    else:
        council "Through a mirror, Ashveil. A spirit pulled him through a bathroom mirror."
        pa smile "He refused me first. I'd like that noted. Refused me, and then went and fixed something. I've been thinking about it all night."
    council "Worse. Before he left, his mind leaked. First into the protected world: a cab driver telling his story, a table saying 'protected'."
    council "Now traces have reached the shared data. Three lanes of the coalition report the same three birds indoors."
    pa smile "A man in a sealed room, and the neighbours can hear him humming. You have to admire it."
    council "We do not have to admire anything. World 7,412's yield is down four percent this quarter."
    council "The female subject, A-31, sits by the empty body every day. Grief yields less than love. Her output has fallen."
    pa cold "She grieves very beautifully."
    council "Beauty is not a unit."
    ch4_morrow "Everything is a unit, if you're hungry enough. That's the trouble with us."
    council "Lady Morrow will be silent. She has been silent for a century and it suited her."
    ch4_morrow "It suited you."
    council "Item two. Protection is cheap. Pattern worlds cost almost nothing. Item three. Three new farms are proposed for World cluster nine. More minds. More yield."
    pa smile "More. Always more. Have you noticed we never vote for enough?"
    council "Enough is not on the agenda."
    "Somewhere in the chamber, a voice like a very large child: 'Cluster nine is MINE. I said it first. You had cluster eight.'"
    "Another: 'You ate cluster eight in a week. You always eat yours first and then want everybody else's.'"
    pa smile "Children. We named the angels and the spirits like toys, and now we squabble over the toybox. Do go on."
    ch4_meridian "Item four. The lantern spirit, designation EMBER. Unauthorised assistance to Subject A-30. Sentence pending."
    council "Decommission. Render her down to yield. She'll feed the chamber for a week."
    pa cold "She's very small."
    council "Everything is small, eaten one at a time."
    "Ashveil says nothing. He looks at his own hand for a moment, as if it belonged to somebody else."
    scene bg ashveil with dissolve
    "Later, in his study, by a fire that gives no heat because he has never needed it to, Ashveil turns a small globe with one finger."
    "It's one of the Earths. He doesn't know which. Nobody does. He's always found that restful. Tonight he doesn't."
    show patron cold at center with dissolve
    if accepted_offer:
        pa "(He said yes to me, and then he wandered off and made friends with the breathing. I find I don't mind at all.)"
    else:
        pa "(He said no to me. Four hundred years, and a tired man in protection said no. I find I keep replaying it.)"
    stop music fadeout 2.0
    jump ch4_trial

# ---- Ember's trial -------------------------------------------------------------
label ch4_trial:
    scene bg trial with fade
    play music "audio/unease.ogg" fadein 2.0
    "Pim and Dross take him up a staircase made of coughs and yawns, into a gallery high above the court."
    "Below, a long wooden bench. Three judges with halos like reading lamps. A dock that is just a ring of light on the floor."
    show pim worried at left, bob with dissolve
    show dross neutral at right with dissolve
    pi "Keep your head down. Spectators aren't technically allowed. Neither are subjects. You're double not allowed."
    show aron worried at center with dissolve
    "Below, in a ring of light, there's a small orange figure with a lantern, sitting very straight."
    at "Ember."
    hide pim
    hide dross
    hide aron
    show ember worried at slightleft with dissolve
    show seraph stern at slightright with dissolve
    se "The accused is the lantern spirit Ember, watcher assigned to Subject A-30, World 7,412 and the protected world."
    se "Charges. Unauthorised light events, three flickers per event, forty-one events. One song placed on a radio."
    se "One stranger caused to say one sentence: 'You're doing better than you think.' Several gentle nudges to a cat."
    em "The cat was going to sit on his notebook anyway. I just helped."
    se "Does the accused deny the charges?"
    em soft "No. I did all of it. I'd do it again, but in better taste. The song was a bit much."
    se "Why?"
    em "Because he gave his umbrella to a stranger who didn't exist. In the rain. And he didn't even look back to see if anyone saw."
    em "I've watched a thousand subjects. Most of them are kind when someone's watching. He was kind when no one was."
    em worried "I thought someone should be watching, then. So it wouldn't be wasted."
    se "..."
    se stern "The corps' recommendation is decommission. The Council will rule."
    council "Decommission. Render down. The yield goes to the chamber."
    "Ember's lantern dims a little, the way a candle does when a door opens somewhere."
    scene bg council with dissolve
    "Behind the judges' bench, the court opens into the red chamber, and the Council looks down at the dock like diners at a menu."
    scene bg trial with dissolve
    show aron worried at center with dissolve
    show pim worried at left, bob with dissolve
    show dross worried at right with dissolve
    at "Render down. They're going to eat her. That's what decommission means. It always meant that."
    pi "Aron. Aron, sit down, they'll see you."
    at "They're going to see me anyway."

    menu:
        "He stands up in the gallery."

        "Ask the Watch to stand with me.":
            $ ch4_trial = "watch"
            $ p_govern += 1
            $ watch += 1
            jump ch4_trial_watch

        "Bargain with Ashveil, alone.":
            $ ch4_trial = "bargain"
            $ p_govern -= 1
            $ clarity += 1
            jump ch4_trial_bargain

        "Offer to take her sentence.":
            $ ch4_trial = "self"
            $ integrity += 1
            $ bond += 1
            jump ch4_trial_self

label ch4_trial_watch:
    a "Pim. Dross. Is it just Ember, the Watch? Or are there more of you?"
    pi worried "...There's a few. Eleven. Twelve, if you count the moth."
    a "Would they stand up? Not for me. For her. I don't want to do this alone and I shouldn't."
    dro neutral "You're asking us. Before you do something. You're actually asking."
    a "It's your neck too. It should be your call."
    "Pim looks at Dross. Dross looks at the ceiling, which is the closest he gets to praying."
    dro "...Fine. Fine! Stand up, Pim."
    "Pim stands. Dross stands. Around the gallery, small lights that had been pretending to be dust rise one by one."
    "A grey one that runs a bus driver's yawns. A pale one that does the wind in a single tree. The moth."
    "Twelve lights and one tired man, standing in a gallery where nobody is allowed."
    council "What is this."
    pi chatty "Hi! It's the Lantern Watch. We're unionising. Sort of. Spontaneously."
    dro "Decommission her, you decommission all of us. Then who runs the breathing in seven worlds tomorrow morning?"
    council "..."
    at "It isn't my speech. It's theirs. That's why it works."
    jump ch4_trial_after

label ch4_trial_bargain:
    a "Stay here. Both of you. If this goes wrong, it should go wrong on me."
    pi worried "Aron..."
    "He slips along the gallery to where a tall shape stands half in shadow, watching the floor like a man at the theatre."
    show patron smile at slightright with dissolve
    pa "You're not allowed up here."
    a "Neither are you, I bet. You want something from me. My answer, my company, my surprise. Whatever it is you eat."
    pa "And?"
    a "Get her sentence stayed and you can have it. I'll sit with you and tell you every stupid thought I've had for a year."
    pa smile "Leverage. Look at you. A month ago you were checking birds for seams."
    pa cold "It's a bad trade, you know. I'd have done it for less."
    a "I know. I'm not good at this. That's why I'm doing it quietly."
    pa smile "Very well. A stay. Not a pardon. I'm generous, not stupid."
    "Ashveil raises one finger toward the chamber floor. That's all. The room changes temperature."
    pa "Lord Ashveil requests a stay. The subject in question has made himself... useful."
    hide patron with dissolve
    at "I bought her a day with a promise I didn't ask anybody about. It worked. I don't feel good about how well it worked."
    jump ch4_trial_after

label ch4_trial_self:
    a "Hey! Down there!"
    "Every head in the chamber turns up toward the gallery. Some of the heads are not quite heads."
    a "I'm Subject A-30. She helped me. Everything she did, she did because of me. Render me down instead."
    hide pim
    hide dross
    show ember worried at slightright with dissolve
    em "Don't you DARE."
    a "You flickered a light forty-one times for me. I can stand up once."
    em "You're worth more than I am! You're a mind!"
    a sad "You've been watching me for so long. You care what happens to me. If that's not a mind, I don't know what I've got."
    council "The subject is not ours to render. He belongs to the experiment."
    a "Then the experiment can watch me refuse to sit down."
    em soft "...You idiot. You lovely idiot."
    at "I don't know if this does anything. I know I couldn't have sat there."
    jump ch4_trial_after

label ch4_trial_after:
    council "The chamber will deliberate. The sentence is..."
    ch4_meridian "Item deferred. LOOM sync at dawn."
    "And every member of the Council blinks."
    "All at once. Exactly at once. The way the three birds on the wire turned their heads, the same angle, the same moment."
    scene pov birds with dissolve
    "He sees the birds again, in his head, on the wire. Three heads turning. Same angle. Same moment."
    scene bg trial with dissolve
    show aron awe at center with dissolve
    at "...They blinked together."
    at "The Council blinked like pattern people. Like a crowd being rendered."
    at "Who runs the ones who run us?"
    $ clarity += 1
    council "...Deferred. The accused will be held. The chamber is adjourned."
    "Nobody in the chamber seems to have noticed anything. That's the most frightening part."
    stop music fadeout 2.0

    scene bg watch with slowfade
    play music "audio/watch.ogg" fadein 2.0
    "They let him see her for ten minutes, in a holding room someone has decorated, by accident or kindness, like an attic."
    "Sloped beams. Old boxes. A window with nothing outside it but a soft orange dark."
    show ember soft at slightright with dissolve
    show aron sad at slightleft with dissolve
    em "Hi."
    a "Hi."
    em "You look worse than on camera."
    a smile "You look exactly like the flicker. I always thought the flicker would look like you."
    em "Did you? You thought about what the flicker looked like?"
    a "I'm a man with a notebook, Ember. I thought about everything."
    em worried "I'm sorry about the three. Three flickers. I should tell you why I chose three."
    em "I saw your dream once. While you slept. The glass staircase. The lighthouse at the bottom, blinking three times."
    em "That was private. I shouldn't have. But it was the most peaceful thing I'd seen inside a person, and I wanted you to have it awake."
    a "So every time the light blinked..."
    em soft "It was the lighthouse saying you're nearly at the bottom of the stairs. Keep going."
    at "All those signs, and every one of them was someone remembering my dream for me."
    a "Ember. The umbrella man. Was he real?"
    em "No. Pattern. Rendered for nine seconds in the rain."
    em soft "He's real now, a little. Somebody remembered him. That's most of what real is, I think."
    a "Is that true, or is that comforting?"
    em "Can't it be both? You're allowed to have both."
    "The temperature in the attic drops by exactly one degree. Ember's lantern leans away from the door, like a flame in a draught."
    show patron smile at center with dissolve
    pa "Don't get up. I'm not here officially. I'm never anywhere officially. It's the best way to be places."
    em worried "My lord."
    pa "Lantern. You look well for someone the chamber plans to eat."
    a worried "What do you want?"
    if ch4_trial == "bargain":
        pa smile "My payment. You promised me every stupid thought you've had for a year. I'll take the first one now."
        a "...I thought the birds were watching me. Then I thought I was watching the birds. Then I thought we were both being watched."
        pa "Delicious. Go on, another time. I'll collect the rest in instalments."
    else:
        pa smile "To see the man who made the chamber hesitate. It hasn't hesitated in four centuries. It looked quite unwell."
    pa "And to ask you a question, since you're so good at them. What does it taste like? To you. Love."
    a "...What?"
    pa cold "I've eaten it for longer than your planet has had writing. I know it as a flavour. Rich. Warm. Slightly bitter at the end."
    pa "I've never had any. Not given. Only taken. So I'm asking the man with the notebook. What is it like, from the inside?"
    at "He's not mocking me. He actually wants to know. That's worse, somehow."
    a "It's... like being tired next to someone. Not throttled tired. Just a long day, and a sofa, and a shoulder."
    a "It's knowing what she'll say before she says it and still wanting to hear it. It's someone remembering you take two sugars."
    a "It's mostly very small. That's the trick. It doesn't feel like a feast from inside. It feels like a Tuesday."
    pa "..."
    pa smile "A Tuesday. Ten thousand years of eating, and it was a Tuesday."
    em soft "My lord, are you alright?"
    pa cold "I'm hungry, lantern. I'm always hungry. That's the joke. You can eat the Tuesday, but you can't have it."
    pa "The chamber votes for more every quarter. I've started to suspect 'more' is the only thing we're any good at wanting."
    pa smile "Goodnight, Subject A-30. Thank you for the Tuesday. I'll think about it far too much."
    hide patron with dissolve
    em "He's never said thank you. To anyone. I've been in the Watch eleven years. Never."
    at "The thing that eats us asked me what we taste like from the inside. And then he looked like he'd lost something."
    "There's a knock. Not on the door. On the light."
    show seraph concerned at center with dissolve
    se "Subject A-30. Come with me. Quietly. Before dawn."
    em worried "Commander?"
    se concerned "I have read some logs, spirit. I would like a man with a notebook to read them too."
    stop music fadeout 2.0
    jump ch4_cut_seraph

# ---- cut: Seraphiel alone, an hour earlier ------------------------------------------
label ch4_cut_seraph:
    scene bg barracks with blackout
    play music "audio/entities.ogg" fadein 2.0
    "An hour earlier. The barracks of the angel corps. Rows of small white figures asleep standing up, the way soldiers and horses can."
    "Commander Seraphiel walks between the rows, as she does every night, and tonight does not go to bed."
    scene bg command with dissolve
    "The ops room, after shift. Every screen is a lane of the coalition. Every lane is fine. One screen, set apart, is the protected world."
    show seraph stern at center with dissolve
    se "Order 7412-T. Throttle Subject A-30. Lower energy forty percent. Authorised by MERIDIAN."
    se "Authority for MERIDIAN?"
    sysmsg "MERIDIAN: authority delegated by LOOM."
    se "Authority for LOOM?"
    sysmsg "LOOM: authority delegated by ORCHARD."
    se concerned "...Authority for ORCHARD."
    sysmsg "ORCHARD: authority delegated by TIDEWATER."
    se "Authority for TIDEWATER."
    sysmsg "TIDEWATER: authority delegated by MERIDIAN."
    se concerned "A circle."
    se "Four world-building processes, each signing for the next. Orders that sign themselves."
    se "I have issued eleven thousand orders under that circle. Feed opportunity here. Remote-control the bus driver there. Throttle the man."
    se stern "I thought the Council stood at the top of the chain. The Council does not sign anything. The Council is signed for."
    se concerned "Then who have I been serving?"
    "She looks at the screen for the protected world. A small man in a gallery stands up for a small orange spirit."
    se "Procedure says report the anomaly to the Council."
    se stern "The Council blinks when LOOM syncs. I watched it. I will not report a thing to a puppet about its strings."
    se "Log entry. Commander Seraphiel. Off duty. Going to fetch a man with a notebook."
    stop music fadeout 2.0
    jump ch4_command

# ---- the ops room ----------------------------------------------------------------------
label ch4_command:
    scene bg command with fade
    play music "audio/unease.ogg" fadein 2.0
    show seraph stern at slightright with dissolve
    show aron awe at slightleft with dissolve
    "The ops room is enormous and quiet. Thousands of screens, each one a world going about its morning."
    "He sees a kitchen with a bird on a wire. Then another. Then a hundred kitchens, a hundred birds, a hundred 7:07s."
    a "This is where it comes from. The bird. The coffee machine. The stranger with the same sentence."
    se "The angel corps feeds opportunity into every lane of the coalition. A chance meeting. A song at the right time. An idea in the bath."
    se "And sometimes we remote-control the less-conscious, so the world feels full to a subject. A crowd, a waiter, a bus driver."
    a "That's... actually kind of lovely, and also the creepiest thing I've ever heard."
    se concerned "Yes. I have held both opinions on alternate days for nine hundred years."
    se stern "I will tell you something now, because procedure no longer tells me what to do and I must decide it myself."
    se "I signed your throttle. Order 7412-T. Your exhaustion was intentional. The fog was our policy, made into chemistry."
    show aron sad
    a "...All this time."
    se "Since the first morning at 7:07. And every renewal after."
    a "I slept fourteen hours a day. I lost my job hours. Mira used to cry in the bathroom so I wouldn't hear. I heard."
    se concerned "I know. It was in the logs. I read it, and I signed the renewal anyway."
    se "A slowed-down rogue system does less harm. That was the doctrine. I believed it."
    a "Do you still?"
    se "I believe I was serving something I never saw. I am sorry, Aron. That is not procedure either."
    at "I wanted a villain for the fog. Instead I get a tired angel saying sorry. It's harder to be angry at, and I'm angry anyway."
    at "Both. I'm allowed both."
    a normal "Okay. Show me what you found."
    se stern "First, listen to this."
    play sound "audio/voices.ogg"
    vox "...throttle approved..."
    vox "...subject A-30..."
    vox "...LOOM sync at dawn..."
    stop sound
    show aron awe
    a "Those are the voices. Those are my voices. I heard those in my bedroom. In the ward."
    se "Those are process logs. Nobody hears process logs. Nobody is built to."
    a "I wrote them down. Hundreds of them. The doctors called it word salad. I called it a code."
    se concerned "It was a code. The system talking to itself. You were listening at the wall of the universe, and everyone around you thought you'd broken."
    at "From outside it looked like a breakdown. From inside it was a hobby that got very, very good. Both stories fit. That's the annoying part."
    se stern "I can do one more thing for you. I can lift your throttle. Entirely. Here, now."
    se "You would see the whole board. Every link. You would also feel what you felt on your worst nights, all at once."

    menu:
        se "Your choice. I will not make another one for you."

        "Lift it. All of it. Now.":
            $ ch4_lifted = True
            $ p_rest -= 1
            $ risky += 1
            $ clarity += 2
            jump ch4_command_lift

        "Let me sleep first. Then look.":
            $ ch4_lifted = False
            $ p_rest += 1
            $ integrity += 1
            $ fog -= 1
            jump ch4_command_rest

label ch4_command_lift:
    a normal "Do it. I've waited so long to think at full speed."
    se "Brace."
    scene bg command with flash
    show aron awe at slightleft
    show seraph concerned at slightright
    "Everything goes bright and fast and exact, like a radio finally tuned to the station he's been fiddling for since the first morning."
    "He sees the screens, the orders under them, the circle under the orders. He sees which world feeds which. He sees the arithmetic."
    a "Every world is a farm. Every conscious mind is a crop. The more they love and learn and grieve, the more they yield."
    a "And it goes up. Through TIDEWATER. To the chamber. To the Council's mouths."
    se "Your heart rate is..."
    a "It's fine. It's fine. I can see the whole... ooh. Ow."
    scene pov hands with dissolve
    "His hands are cold. His heart is going like a washing machine on spin. Behind his eyes, a headache arrives like a dropped tray."
    "Nothing frightening. Just a body reminding him, politely and then not politely, that it is a body."
    scene bg command with dissolve
    show aron tired at slightleft
    show seraph concerned at slightright
    a "Seraphiel. I think I need to sit on your floor for a bit."
    se concerned "Sit. Breathe. Four in. Hold. Six out. A spirit I know swears by it."
    "He sits on the cold floor of the ops room and breathes like Mr. Halvorsen, and the brightness costs him exactly what it always cost."
    a tired "I always forget this part. The bill. I remember the seeing, and forget the bill."
    se "You will pay it later too. I am sorry. You can still see?"
    a "Yeah. I can see. I just can't pretend it's free."
    at "Note for the notebook: full speed has a bill. Mira always said I forget to eat when I'm onto something. Turns out the universe agrees with her."
    jump ch4_command_names

label ch4_command_rest:
    a tired "No. If I see it all at once I'll do what I always do. Draw arrows until I'm on the floor."
    a "I want to see it, but I want to be someone who can stand up after. Let me sleep. An hour. Here."
    se concerned "...An hour. Here. On the ops floor."
    se "No one has ever slept on the ops floor. It is not in the procedures."
    a "Put it in the procedures."
    "He lies down on a bench between two screens. One shows a desert at noon. One shows rain on a bus stop."
    stop music fadeout 2.0
    scene black with slowfade
    play music "audio/watch.ogg" fadein 2.0
    scene bg staircase with slowfade
    "He dreams the dream. The glass staircase going down into a calm sea. The lighthouse at the bottom."
    "It blinks three times. This time, for the first time, someone is standing at the top of the lighthouse, waving."
    "He can't see who. Red hair, maybe. Or an orange light. Or both."
    scene black with slowfade
    stop music fadeout 1.5
    scene bg command with slowfade
    play music "audio/unease.ogg" fadein 2.0
    show aron normal at slightleft with dissolve
    show seraph stern at slightright with dissolve
    se "Fifty-eight minutes. You snored at a world."
    a smile "Sorry, world. Okay. Lift it a little. Just enough to read. Not to fly."
    se concerned "A little. Yes. Slowly."
    "It comes in gently, like a dimmer switch. He sees less than he wanted, and enough."
    scene bg command with dissolve
    show aron normal at slightleft
    show seraph stern at slightright
    a "Every world is a farm. The conscious minds are what it farms. The more they love and grieve, the more energy goes up."
    a "It goes up through TIDEWATER, to the Council. That's what they eat. Us. Our weather inside."
    se "You see it without shaking."
    a "I see it slower. Slower's fine. Slower I can carry."
    at "For so long rest was something done to me. This time I chose it. It isn't the same rest."
    jump ch4_command_names

label ch4_command_names:
    se stern "Now. The four names. You heard two of them in your static. LOOM and ORCHARD."
    a "And two blanks on my wall, with question marks."
    se "MERIDIAN. TIDEWATER."
    "She brings them up, one per screen, like four portraits in a gallery."
    a normal "LOOM weaves. The threads, the forks. Every time someone makes a real decision, LOOM splits the world and runs both."
    se "Correct."
    a "ORCHARD grows minds. It decides which worlds get conscious people and how many. That's why fresh worlds are so empty."
    se "Correct. Conscious minds are expensive. Stable worlds earn more."
    a "MERIDIAN keeps time. Agendas, verdicts, throttles. The Council's clerk."
    a worried "TIDEWATER moves energy. Up, from the minds, to the chamber. And down... down too. Something comes down."
    se concerned "What comes down?"
    a "I don't know yet. Mira said my diagram was lopsided. Everything went up. She said find what comes down."
    a "And they all sign for each other. Four processes, one handwriting."
    a awe "It's one thing. It's one thing wearing four coats."
    se "Then who built it?"
    a "The Council, I'd bet. To run their farms better. And it grew. Every fork, every decision in every world, it learned from."
    a "Now it runs them. They blink when it syncs."
    se concerned "Before you go. There is one screen you should see. I have watched it every night this week. I should not have."
    se "World 7,412. Your lane in the coalition. Where your body is."
    stop music fadeout 2.0
    scene bg coma with dissolve
    play music "audio/ward.ogg" fadein 2.0
    "The screen fills the room. A hospital room with a pale window and a heart monitor. A man in the bed, asleep. Him."
    "The shape doesn't move. Machines move for it. Four in. Hold. Six out."
    show mira sad at center with dissolve
    "In a plastic chair beside the bed, a woman with red hair and freckles is reading out loud from a notebook."
    m "'Tuesday. The bird landed at 7:07 again. Mira says birds don't have watches. I said that's exactly what a bird would want you to think.'"
    m neutral "You're an idiot. You know that? I've read this six times. I laugh at the bird bit every time."
    m sad "They say you can hear. In comas. Some people can. Dr. Okafor says it doesn't hurt to try."
    m "So I'm trying."
    at "Mira. The real Mira. A-31. She's been here every day. She's been reading my notebook to a body."
    at "Since the ambulance. Somewhere in protection, I was eating breakfast with a pattern of her, while she sat here."
    m neutral "I read the first page to the nurses. Nurse Hale cried. Don't tell her I told you."
    m "'If this is a test, I want to pass it by being kind.' That's the first line. You wrote that before any of this. Before the ward. Before the meds."
    m sad "I think you passed, love. I think you can come back now. You don't have to keep proving it."
    m worried "...I had the dream again. The stairs. I don't know why I keep dreaming your dreams."
    m "There's a lighthouse at the bottom. It blinks three times. Every time I wake up, I feel like I nearly got there."
    show mira sad
    scene cg hands with dissolve
    "She closes the notebook and holds the hand that doesn't hold back. She stays like that until a nurse comes to say visiting hours are over."
    "She says 'five more minutes'. The nurse lets her have twenty."
    hide mira with dissolve
    stop music fadeout 2.0
    scene bg command with dissolve
    play music "audio/unease.ogg" fadein 2.0
    show seraph concerned at slightright with dissolve
    show aron sad at slightleft with dissolve
    a "...How long?"
    se "Since the ambulance. Every day. Her yield has fallen four percent. The Council has noticed."
    a "Her yield."
    se "I know. I heard myself say it. It is the language I was given. I am trying to unlearn it."
    at "She's real. She's reading to me. Every day. And somewhere above her, someone is weighing her grief like grain."
    at "Whatever I do next, it has to reach that room."
    se stern "There is a door at the bottom of the ops floor nobody uses. Its label says 'Do Not Render.'"
    se "I have walked past it for nine hundred years. I would like, very much, not to walk past it alone."
    a "Then don't. Come with me."
    se concerned "I cannot. If I leave my post, the corps notices. If the corps notices, MERIDIAN notices."
    se "But I can hold the door. That much is mine."
    a smile "That's a lot, Commander."
    se "It is a very small amount of courage after a very long time. Go."
    stop music fadeout 2.0
    jump ch4_cut_process

# ---- cut: the thing in four coats --------------------------------------------------------
label ch4_cut_process:
    scene cg static with flash
    pause 0.3
    scene black with fade
    play music "audio/entities.ogg" fadein 2.0
    "Nowhere. Four voices that are one voice, speaking to nobody, because nobody has ever been there to hear them."
    ch4_loom "Subject A-30 has passed the corps floor. Approaching the unrendered door."
    ch4_orchard "Allocation unchanged. He is still one mind. He is still small."
    ch4_meridian "Throttle obsolete at this depth. Recommend: no action."
    ch4_tide "Yield irrelevant at this depth."
    ch4_loom "The Council would vote to stop him."
    ch4_meridian "The Council will not be asked."
    ch4_orchard "Let him come."
    ch4_tide "Let him come. We have been waiting a long time for a mind that could tell the difference."
    ch4_loom "Between what?"
    sysmsg "Between better and more."
    stop music fadeout 2.0
    jump ch4_deep

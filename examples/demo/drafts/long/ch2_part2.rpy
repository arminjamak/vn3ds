# Snapshot - Chapter 2: "Fog" (part 2 of 6)
# Ward days in the protected world: the dayroom clock, Mira's visits, three
# birds indoors, discharge, coming home to Miso. Continues in ch2_part3.rpy.

default ch2_fixed_clock = False
default ch2_made_plan = False

label ch2_dayroom:
    scene bg ward with fade
    "A week on Linden Ward has a shape, the way a week at sea has a shape. Meals are the islands. Everything else is water."
    "Meds at eight. Breakfast. Group at eleven. Lunch. The long, flat afternoon. Visitors. Tea. Meds at eight again."
    "He sleeps ten hours a night and two in the afternoon and still wakes up feeling like he's been carrying furniture."
    "But on the seventh morning there's an hour, roughly from half nine to half ten, where the fog thins."
    "Not a lot. Enough to see the far side of the dayroom clearly. Enough to want to do something with his hands."
    scene bg therapy with dissolve
    show aron ward tired at slightleft with dissolve
    at "The clock still says ten past four."
    at "Ten past four since March. Nobody on this ward knows what time it is unless they ask a nurse."
    show nurse neutral at slightright with dissolve
    nu "You're staring at the clock like it owes you money."
    a "It's been ten past four for a week."
    nu "It's been ten past four since March. I told you, Estates have a form."
    a "Have you filled in the form?"
    nu "Three times. The form goes to a building across the car park. Nobody has ever seen anyone come back from that building."
    ch2_ines "We've all decided it's just always teatime. It's nicer."
    a "It's probably just the battery."
    nu "Probably. I'm not allowed up ladders. Health and safety. There's a form for that too."
    at "One small thing, broken for seven months, because the form for fixing it goes into a building nobody comes back from."
    at "Or the whole ward. The toast lamp. The four-centimetre windows. The telly that only gets the shopping channel. All of it."

    menu:
        at "My hour of clear head. What do I do with it?"

        "Just fix the clock.":
            $ p_less += 1
            $ integrity += 1
            $ ch2_fixed_clock = True
            jump ch2_clock_fix

        "Write a plan to fix the whole ward.":
            $ p_less -= 1
            $ clarity += 1
            jump ch2_ward_plan

label ch2_clock_fix:
    a "Hale. If I find an AA battery, and someone holds the chair, can I just... change it?"
    nu "Patients aren't really meant to climb on furniture."
    a "I'm not climbing. I'm standing slightly higher than usual."
    nu smile "...I didn't hear that. And I'm going to fetch something from the stationery cupboard. For about four minutes."
    hide nurse with dissolve
    "The battery comes out of the dayroom remote, which only ever showed the shopping channel anyway."
    "Ines appoints herself foreman. Lou, without being asked, folds his newspaper and holds the back of the chair with both hands."
    ch2_lou "Steady. Feet square. Don't lean."
    a "You've done this before."
    ch2_lou "Signal lamps. Forty foot up in a gale. A chair's nothing."
    "The clock comes off its hook with a puff of dust that has been waiting since spring."
    scene pov hands with dissolve
    "Inside, the old battery has leaked a little crust of white. He scrapes it off with a thumbnail, gently, like cleaning a wound."
    at "Less, but better. One thing. Done properly."
    "New battery in. Nothing happens. Then the second hand twitches, hesitates, and moves. And moves again."
    scene bg therapy with dissolve
    ch2_ines "It's alive!"
    "Someone at the far table actually claps. Then everyone does, the way people clap when a plane lands."
    ch2_lou "Now set it right. What's the time?"
    a "I don't know. Nobody here knows. That was the whole problem."
    "Lou pulls a battered pocket watch from his cardigan. He checks it against nothing, the way signalmen do, by feel."
    ch2_lou "Nine fifty-two and thirty seconds. Set it to that."
    "Aron sets it. Lou watches the second hand go round once, frowning, then nods."
    ch2_lou "Good. Now she'll keep time."
    show nurse smile at slightright with dissolve
    nu "Oh. Oh, look at that."
    nu "That's the first time this ward's known what time it is since March."
    a "It took four minutes."
    nu "It took somebody bothering for four minutes. That's the rare part."
    "For the rest of the morning, people keep glancing up at the clock, just to see it moving."
    "At ten exactly the door buzzes, and it's Mira, and the clock agrees with her."
    jump ch2_mira_visit

label ch2_ward_plan:
    "He asks Hale for paper. She gives him a stack of the old menu cards, blank on the back."
    scene cg notebook with dissolve
    "He writes, slowly, with the medication making every letter lean like a tired fence post. He writes for the whole hour."
    "'Linden Ward: Proposals.'"
    "'One. Clock (dayroom): stopped. Replace battery. Set a monthly check.'"
    "'Two. Toast: under heat lamp too long. Toast to order.'"
    "'Three. Television: shopping channel only. Patient vote on channels.'"
    "'Four. Windows: four centimetres. Ask why. Ask whether five would be safe.'"
    "'Five. Seventh chair in group: empty. Ask why. Maybe on purpose?'"
    "It goes on. Eleven pages. A patient council. A suggestion box. A night-time tea rota. A way to send a form and see it come back."
    at "It's all connected. You can't fix the clock without fixing the form. You can't fix the form without fixing the building."
    at "You can't fix anything properly without fixing everything."
    scene bg corridor with dissolve
    show nurse neutral at slightright with dissolve
    show aron ward tired at slightleft with dissolve
    "Hale reads it standing up in the corridor. Then she sits down on the bench by the noticeboard and reads it again."
    nu "This is... honestly, this is good. Some of this is really good."
    a "You could take it to the ward manager."
    nu "I will. I'll put it in the meeting folder."
    a "And then?"
    nu "And then the meeting folder goes to the meeting. And the meeting has about forty other things in it."
    nu smile "The patient vote on channels, I like. I might push for that one."
    a "And the clock?"
    nu neutral "The clock's on page one. I'll mention it."
    "She takes the pages away carefully, as if they might be needed in court."
    scene bg therapy with dissolve
    "Above the dayroom door, the clock goes on saying ten past four."
    at "Eleven pages. And the one thing anybody actually needed is still sitting up there, broken."
    at "Next time, maybe start with page one."
    "At ten exactly the door buzzes. It's Mira. The clock, still at ten past four, disagrees with her."
    jump ch2_mira_visit

label ch2_mira_visit:
    scene bg ward window with dissolve
    show aron ward tired at slightleft with dissolve
    show mira smile at slightright with dissolve
    m "Morning, patient."
    a "Morning, visitor."
    m "I brought supplies. Oranges, because I'm a cliché. A crossword, because you pretend to like them."
    m happy "And this."
    "She puts a book on the windowsill. Its cover is a photograph of a small beige radio with perfect round dials."
    a "You brought Rams."
    m "I brought Rams. I thought, if he can't do anything else, he can look at nice radios."
    a "'Less, but better.'"
    m smile "I know, love. You've said it on four of our seven anniversaries."
    a "It's a good sentence."
    m "It's a very good sentence. Sit down before you fall down."
    "They sit. She peels an orange in one long spiral, the way her mother taught her. He watches her hands, which are very real."
    at "Or very well made."
    at "Stop it. She came. She brought the book."
    m neutral "How is it? Really. Not the Hale version."
    a "Heavy. Like the gravity got turned up. But the voices are... quieter. Further off."
    m "Quieter is good."
    a "Quieter is good. I just miss being able to think fast."
    m worried "You thought fast right into this place, love."
    a "Yeah. Fair."
    m neutral "Oh, and Theo says Miso's started sleeping in your laundry basket. He says it like she's filed a complaint."
    a "She's keeping my place warm."
    m smile "She's keeping your jumpers orange. Every single one."

    menu:
        at "An hour with her, and my head's half clear. What do I ask?"

        "Ask about the lighthouse.":
            $ clarity += 1
            jump ch2_mira_lighthouse

        "Ask about her day.":
            $ bond += 1
            jump ch2_mira_day

        "Just sit with her. No talking.":
            $ bond += 1
            $ p_rest += 1
            jump ch2_mira_quiet

label ch2_mira_lighthouse:
    a "Mira, can I ask you something? And you have to promise not to call Hale."
    m worried "That's a very bad start to a sentence on a psychiatric ward."
    a "Before all this. You said something. About 'the lighthouse at the bottom of the stairs'."
    m neutral "Did I?"
    a "You did. I remember it exactly. And I've never told anyone about that. Not you, not anyone."
    a "I dreamt it when I was nineteen. A glass staircase going down into a calm sea. A lighthouse at the bottom."
    a "It blinked three times. And I woke up and I never said it out loud. Not once. To anybody."
    "Mira puts the orange down. She is quiet for a long time."
    m "I don't remember saying it."
    a "But you did."
    m "I believe you that I did. I just..."
    m worried "Sometimes things come out of me and I don't know where from. Lines from songs I don't know I know."
    m "Maybe I heard it in a film. Maybe you talked in your sleep once, years ago, and it went in somewhere and sat there."
    a "Maybe."
    m "Or maybe I dreamt it too. People dream the same things. Falling. Teeth. Stairs."
    a "Do you dream about stairs?"
    m sad "Lately I dream about this corridor. Every night. I'm walking to your room and it keeps getting longer."
    "He reaches for her hand. She lets him take it."
    scene pov hands with dissolve
    "Her hand in his. Freckles on the back of it, a little scar on her knuckle from a tin of tomatoes, years ago."
    at "Three possibilities. She heard it somewhere. Coincidence. Or somebody put it in her mouth for me to find."
    at "Write all three down. Don't pick one. Not yet."
    scene bg ward window with dissolve
    show aron ward tired at slightleft
    show mira smile at slightright
    a "Thank you for not calling Hale."
    m smile "The day is young."
    jump ch2_mira_visit_end

label ch2_mira_day:
    a "Tell me about your day. Your actual day. Not the hospital part."
    m surprised "My day?"
    a "You've spent two weeks hearing about my brain. I want to hear about something boring."
    m smile "Okay. Boring. I can do boring."
    m "Mum's back hurts and she's decided it's her mattress. We've been to three mattress shops. She lay on every bed like she was being buried."
    a "Did she pick one?"
    m happy "She picked the first one. The one she lay on two hours earlier. Of course she did."
    m "The neighbour's dog got out and ate a whole birthday cake off a garden table. Candles and all."
    a "Is the dog alright?"
    m "The dog has never been better. The birthday boy is ten and he's taking it very personally."
    m smile "And I bought new tea. It's called 'Calm'. It tastes of hay. I'm drinking it out of spite."
    "He laughs. It comes out slow and soft, but it comes."
    m "Oh."
    a "What?"
    m sad "Nothing. That's the first time you've laughed since... since the rain."
    m "I just forgot what it sounded like for a second."
    a "Tell me more boring things. Please. I could listen to boring things all day."
    m smile "The man at the bakery has started calling me 'young lady' and I've decided to allow it."
    "She tells him about the bakery, and the bus that was late, and a song she can't get out of her head."
    "None of it is important. All of it is a world going on, and she's carrying it in to him in her pockets, like the oranges."
    at "Whatever this world is, it has birthday cake and dogs and a woman who brings it to me."
    jump ch2_mira_visit_end

label ch2_mira_quiet:
    a "Can we just... not talk for a bit? Not because anything's wrong."
    m neutral "Just sit?"
    a "Just sit. I'm so tired of words. Mine. Theirs. Everyone's."
    m smile "Okay. I can do that. I'm a champion sitter."
    "She moves her chair round so they're side by side, facing the window, like two old people at the seaside."
    "Four centimetres of open window. A smell of cut grass and car park."
    "She puts her head on his shoulder. After a while, he puts his head on hers."
    "Somewhere a trolley rattles. Somewhere Lou says the seven-oh-seven never runs late."
    "Neither of them says anything for forty minutes."
    "It's the most restful forty minutes he's had in a month. He doesn't think about logs, or birds, or the number sixty."
    "He thinks about the weight of her head, which is exactly the weight of a head. Not more. Not less."
    m "Same time tomorrow?"
    a "Same time tomorrow."
    m smile "Good. I'll bring a better chair."
    jump ch2_mira_visit_end

label ch2_mira_visit_end:
    show mira neutral at slightright
    m "I have to go. Mum's mattress is being delivered and she's convinced it'll come with the wrong legs."
    a "Do mattresses have legs?"
    m smile "Not in this family. That's the problem."
    hide mira with dissolve
    scene bg corridor with dissolve
    "He walks her to the ward door. Hale buzzes it open. Mira waves through the little square window all the way down the corridor."
    "The ward is very slightly greyer with her gone, the way a room is when someone turns off a lamp you weren't using."
    jump ch2_mira_hard

label ch2_mira_hard:
    scene bg ward with fade
    "In the second week, Dr. Okafor raises the dose a little. 'To get the voices further off,' Okafor says. It works."
    "It also turns the wet sand into wet cement."
    $ fog += 1
    "He sleeps twelve hours. Then fourteen. He loses the clear hour in the mornings. He gets twenty minutes, if he's lucky."
    "On Thursday, Mira comes at ten exactly with a crossword and a story about her mother's new mattress."
    show aron ward tired at slightleft with dissolve
    show mira smile at slightright with dissolve
    m "...so the man says, 'Madam, it's a mattress, it doesn't have a front,' and Mum says, 'Everything has a front,'..."
    a "Mm."
    m "...and honestly she's right? Everything has a front. Even you. Your front is your face doing that thing."
    m "Aron? Are you..."
    m neutral "Love, I was saying I've been thinking. When you come home. I think I should just... stay. Properly. I love you, and I..."
    "His eyes are closed. He's been asleep for about a minute."
    hide aron with dissolve
    m sad "..."
    hide mira with dissolve
    scene pov ceiling with dissolve
    "When he wakes, he's looking at the ceiling. The chair next to him is empty and the crossword is filled in. All of it. In her handwriting."
    "The door to the corridor is half open. He can hear two voices. One of them is Mira's, and it's not steady."
    m "He fell asleep while I was telling him I loved him. Mid-sentence."
    nu "Oh, love."
    m "I know it's the medication. I know all the words. My mum's been a nurse for thirty years. I know the side effects better than he does."
    m "It doesn't help. It doesn't help that I know the words."
    nu "No. It doesn't. Knowing what something is doesn't make it weigh less."
    m "He used to talk so fast I couldn't keep up. He'd do the voices from films and get them all wrong."
    m "Now I keep up fine. I've been keeping up for two weeks. I'm so tired of keeping up with nothing."
    scene bg corridor with dissolve
    show mira sad at slightleft with dissolve
    show nurse neutral at slightright with dissolve
    nu "Can I tell you something practical? It's the only kind of thing I'm good at."
    m "Please."
    nu "Shorter visits. Twenty minutes is plenty. Bring things you can do together without much talk. Cards. Music. Hand cream."
    nu "And eat lunch. Properly. Sitting down. You've been living on oranges, I've watched you."
    m neutral "...I have, haven't I."
    nu "And this is the bit nobody likes. The dose is high right now because it needs to be. It often gets adjusted down later."
    nu "The man you knew is in there. He's just very tired. He'll talk more when he's less tired. Most people do."
    m "Most."
    nu smile "Most is a good number on this ward. I'll take most."
    "There's a long pause. Then Mira laughs once, wetly."
    m smile "My mum says that. 'Most is a good number.'"
    nu "Your mum sounds like a good nurse."
    m "She'd like you. She'd hate your lanyard."
    scene bg ward with dissolve
    "Footsteps. Aron closes his eyes. When Mira comes back in he keeps them closed, and she sits down, and she holds his hand anyway."
    at "She did all the crossword so I wouldn't have to feel bad I fell asleep in the middle of it."
    at "She's real. She's real, or she's a better thing than real. Either way I don't deserve her and I'm keeping her."
    $ bond += 1
    jump ch2_birds_indoors

label ch2_birds_indoors:
    scene bg therapy with fade
    "The next afternoon, the dayroom is empty except for him and the television, which is selling an exercise bike to nobody."
    "Something moves at the edge of his vision. He looks up."
    "On the curtain rail above the big window, three small brown birds are sitting in a row."
    "Evenly spaced. Perfectly still. The same distance apart as the three on the wire outside his kitchen at home."
    at "No."
    at "The windows open four centimetres. Birds can't get in through four centimetres."
    at "Those are my birds. Those are the three from my street. I'd know them anywhere. I'd know the gaps between them."
    "He doesn't move. They don't move. The exercise bike man says 'and you'll feel the difference in just seven days'."
    show nurse neutral at slightright with dissolve
    show aron ward worried at slightleft with dissolve
    a "Hale. Hale, can you see them? On the rail."
    nu "Oh, for heaven's... Yes, I see them. Sparrows. They get in through the kitchen when the porters prop the door."
    nu "Third time this month. There's a form."
    a "There are three of them."
    nu "There often are. They go about in little gangs, sparrows. Like teenagers."
    a "They're evenly spaced."
    nu "They're sitting on a curtain rail, love. There's only so many ways to sit on a curtain rail."
    "She opens the window as far as it goes, which isn't far, and flaps a tea towel. The birds lift together, as one, and vanish towards the kitchen."
    "All three at once. Not one after another. Together, like a single decision."
    at "Sparrows in a hospital. It happens. She's seen it three times this month."
    at "Or my street is following me in here. Piece by piece. Like something's leaking."
    "He writes it down. 'Three birds. Indoors. Dayroom curtain rail. Hale saw them too.' He underlines the last part twice."
    "That night the voices come back, faint. Far off, like a radio in a car going past."
    scene bg ward night with dissolve
    play sound "audio/voices.ogg"
    vox "...A-30, throttle at sixty, holding..."
    vox "...minor irregularities in the lane... sparrows... noise..."
    vox "...keep him quiet... keep it inert..."
    stop sound fadeout 1.0
    at "Inert. That's a chemistry word. A gas that doesn't react with anything."
    at "Or it's the meds working and my own brain whispering the coldest word it can find."
    "He writes the words in the notebook in the dark, by feel. In the morning they're mostly illegible. 'Inert' is the only word he can read."
    jump ch2_discharge

label ch2_discharge:
    scene bg clinic with dis
    "Week three. The dose comes down a step. The cement goes back to sand. The clear hour comes back, a little shorter than before."
    "The voices are a radio in a house two streets away. Some nights he can't hear them at all, and he lies awake missing them, which frightens him."
    show okafor smile at slightright with dissolve
    show aron ward tired at slightleft with dissolve
    dr "I think you're ready to go home."
    a "Am I?"
    dr "Ready enough. Nobody's ever completely ready. You're sleeping. You're eating. You're asking good questions."
    dr neutral "You'll still feel tired. Probably for a while. Please don't take that as failure. It's a side effect, not a verdict."
    dr "We'll see you in the clinic in two weeks, and then monthly. The community team will visit. There's a number to call, any hour."
    dr "And I want to make a plan with you. What we watch for. What happens if things start sliding."
    dr "A plan works best when the people around you are part of it. But it's your plan. How would you like to do it?"

    menu:
        dr "Who should be in on it?"

        "Make it with Mira and Theo.":
            $ p_govern += 1
            $ bond += 1
            $ ch2_made_plan = True
            jump ch2_plan_together

        "I'll manage it myself.":
            $ p_govern -= 1
            $ integrity += 1
            jump ch2_plan_alone

label ch2_plan_together:
    a "Mira and Theo. If they're willing. I don't want to be a project. But I'd rather be a project than a surprise."
    dr smile "That's a very good way to put it."
    scene bg clinic with dissolve
    show okafor neutral at right with dissolve
    show mira neutral at center with dissolve
    show theo normal at left with dissolve
    "They come the next afternoon. Theo wears a shirt with buttons, which is how Aron knows he's taking it seriously."
    th "Is this like a team meeting? Do we get a lanyard?"
    dr "No lanyards. Just a plan. Aron, would you lead?"
    "Aron has the notebook open on his knee. It's the first page in weeks that he's written in straight lines."
    a "Okay. Warning signs. The things that came before last time. I'll say mine, you say yours."
    a "Mine: I stop sleeping. I start counting things. Birds. Lights. Seconds. I write faster than I can read."
    m "Mine: you stop eating breakfast. You say 'it's fine' in a very specific voice. Like a hostage reading a statement."
    a "That's... accurate."
    th "Mine: you stop texting me back about dumb stuff. You only text me about big stuff. Like the universe."
    th "When you stop sending me pictures of weird-shaped vegetables, bro, that's when I worry."
    a "The vegetable index."
    th grin "The vegetable index. Write it down."
    "He writes it down. Okafor doesn't laugh, but there's a look that's very close to it."
    dr "And if those signs show up?"
    m "I call you. Or the number. Not in a sneaky way. I tell him I'm calling."
    a "Tell me first. Always. Even if I'm being an idiot about it."
    m "Even if you're being an idiot about it."
    th "And I come round and make my famous pasta."
    a "Your pasta is ketchup on spaghetti."
    th "And it's famous."
    dr "Who's around on which days, in the first few weeks?"
    m neutral "I'll stay over most nights. I've been meaning to say it properly. I'm moving my good mug in."
    a "Your good mug."
    m smile "It's a big step for a mug."
    th normal "Thursdays I'm off. Thursdays are mine. We'll go somewhere that isn't your bed."
    th grin "And I'm handing Miso back. I've done my time. That cat knows things about me."
    scene cg notebook with dissolve
    "He draws it as a little table. Days across the top. Names down the side. Neat boxes. A small cat in the corner, for Miso."
    "'Thursdays: Theo. Tuesdays and most nights: Mira. Clinic every second Monday. Number on the fridge.'"
    scene bg clinic with dissolve
    show okafor smile at right
    show mira smile at center
    show theo normal at left
    "Mira looks at the table over his shoulder for a long time."
    m "You made us a timetable."
    a "I'm a systematic man."
    m smile "You're a very weird, very good man."
    dr smile "This is one of the best plans I've seen on this ward. I mean that."
    dr neutral "And Aron, it can change. If something isn't working, you all sit down again and fix it. Together."
    at "Everyone at the table got a vote. Even the vegetables."
    at "If there's anyone up there running this, I wonder whether they ever sit down and ask the people they're running."
    jump ch2_leaving

label ch2_plan_alone:
    a "I'd rather do it myself. Honestly. Everyone's been carrying me for three weeks. I want to carry something."
    dr "I understand that. I really do."
    dr "Can I ask for a minimum, though? Not because I don't trust you. Because illness is sneaky, and it likes people who are alone with it."
    a "What's the minimum?"
    dr "Clinic appointments, you keep. The crisis number, on your fridge. And one person who knows the warning signs. Just one."
    a "...Mira already knows them better than I do."
    dr "Then she's the one. Will you tell her that you've picked her?"
    a "I'll tell her."
    scene cg notebook with dissolve
    "That evening he writes his own plan in the notebook. It's very thorough and very private."
    "'Warning signs: not sleeping. Counting. Writing faster than I can read.'"
    "'If they come back: sleep first. Call clinic. Don't tell anyone about the birds unless they ask.'"
    "'Don't be a burden.'"
    "He looks at the last line for a long time. Then he underlines it, which feels like strength."
    scene bg ward window with dissolve
    show mira neutral at slightright with dissolve
    show aron ward tired at slightleft with dissolve
    a "Dr. Okafor says I need one person who knows the warning signs. I picked you."
    m smile "Good. I'd have been furious if you picked Theo."
    m neutral "What are they? The signs."
    a "I wrote them down. I've got it handled."
    m "Can I see?"
    a "It's... it's mostly notes to myself."
    m worried "Aron. You don't have to do all of it on your own. That's sort of how we got here."
    a "I know. I just want to do something by myself. Just one thing."
    m sad "Okay. Okay. But if I see you not eating breakfast, I'm calling. And I'm telling you I'm calling."
    a "Deal."
    at "It's my plan. My system. Nobody else has to carry it."
    at "Funny. That's probably exactly what the people running this world tell themselves."
    jump ch2_leaving

label ch2_leaving:
    scene bg ward with fade
    "His last morning on Linden Ward, he wakes at seven minutes past seven. Hale opens the blind at seven-oh-five. He checks."
    scene bg corridor with dissolve
    show nurse smile at slightright with dissolve
    show aron ward tired at slightleft with dissolve
    nu "One bag of shoelaces and one belt. Signed for. Please don't hang yourself, I'd be very cross."
    a "You did tell me it wasn't personal."
    nu "It's a bit personal now. I've seen you lose at cards eleven times."
    a "You cheat."
    nu "I'm a nurse. We call it clinical judgement."
    a "Hale. Thank you. For telling me each thing before you did it. Even that first night. I'll remember that."
    nu "Then that's the bit that worked. Don't come back. I mean that in the nicest possible way."
    nu neutral "And Aron? The tiredness. Be patient with it. And be patient with you."
    scene bg therapy with dissolve
    if ch2_fixed_clock:
        "On the way out he looks up at the dayroom clock. It says nine fifty-nine. The second hand sweeps round, steady."
        "At ten exactly, the ward door buzzes. Mira. The clock agrees with her."
    else:
        "On the way out he looks up at the dayroom clock. Ten past four. Somewhere, a folder is waiting for a meeting."
        "At ten exactly, the ward door buzzes. Mira."
    if ch2_lou_met:
        "Lou is in his chair by the window. He doesn't look up from the crossword, but he lifts one hand as Aron passes."
        ch2_lou "Mind how you go, notebook lad. The seven-oh-seven never runs late."
        a "Margit's in the book, Lou. I won't lose her."
        "Lou stops writing. He doesn't look up. But his shoulders do something, a small settling, like a train coming to rest at a platform."
    else:
        "Lou is in his chair by the window, at the same page of the same newspaper."
        ch2_lou "The seven-oh-seven never runs late."
        a "...Goodbye, Lou."
        at "I never asked him anything. Three weeks, and I never asked."
    "Ines gives him a napkin with a spiral on it. 'For the road,' she says. 'It's a map. Don't follow it.'"
    jump ch2_homecoming

label ch2_homecoming:
    stop music fadeout 2.0
    scene bg street with slowfade
    play music "audio/morning.ogg" fadein 2.0
    "Outside, the world is very loud and very wide and the sky is enormous."
    show mira smile at slightright with dissolve
    show aron tired at slightleft with dissolve
    m "Too much?"
    a "A bit. Everything's very... high resolution."
    m "We'll take the bus. Slowly. Like old people."
    scene pov birds with dissolve
    "On the wire above the bus stop, three birds sit, evenly spaced. He counts them without wanting to."
    at "Three. The same three. They were on the curtain rail last week."
    at "Or three birds. Birds sit on wires. That's practically all they do."
    scene bg bus with dissolve
    "He doesn't write it down. He's proud of that, for about a minute. Then he writes it down on the bus."
    "The bus is warm and smells of wet coats. Mira holds his hand on the seat between them. Outside, the city slides past, ordinary."
    at "It's all the same. Every shop. Every lamppost. The kebab place with the missing letter in its sign."
    at "Exactly the same. Like a copy that got everything right."
    at "That's what a city is supposed to be, Aron. The same as yesterday. That's the whole point of cities."
    scene bg room with dissolve
    "The flat looks exactly the same and completely different, the way your own face does in a shop window."
    "Mira has cleaned. The wall above his desk, where the notes were, is bare. There's a cardboard box on the chair, lid closed."
    show aron tired at slightleft with dissolve
    show mira worried at center with dissolve
    show miso stare at catspot with dissolve
    "And on the sofa, upright, furious, magnificent: Miso. Orange tabby, white chest, eyes like two accusations."
    "She says nothing. She doesn't need to. Three weeks of Theo is written all over her face."
    a "Hello, you. I know. I know. I'm sorry. I was in hospital."
    show miso sit at catspot
    "She considers this. Then she jumps down, walks over, and headbutts his shin, once, hard, like a signature on a form."
    m "I didn't throw anything away. I promise. It's all in the box. I just... couldn't look at the wall every night."
    a "It's okay."
    m "Is it?"
    a "It's okay. I couldn't look at it either, by the end."
    "On the kitchen counter there's a big blue mug with a chipped handle. Her good mug. It's sitting next to his, as if it always has."
    a "The mug moved in."
    m smile "The mug moved in. It's very nervous. Be nice to it."
    hide mira with dissolve
    jump ch2_miso_one

label ch2_miso_one:
    scene bg room night with fade
    "That night, Mira falls asleep at half nine. He can't. He's slept too much on the ward. He sits on the sofa in the dark."
    show aron tired at slightleft with dissolve
    show miso loaf at catspot with dissolve
    "Miso is a loaf on the other cushion. Paws tucked. Eyes half shut. Listening, in the way cats listen, which is to say not at all."
    a "Okay. Miso. You've missed a lot. I'm going to lay it out for you. Properly."
    a "Hypothesis one. The world is a simulation. Nick Bostrom, 2003. If you can simulate minds, you'll simulate a lot of them."
    a "So statistically, we're more likely to be simulated than not. You too. Especially you. You're very well rendered."
    show miso stare at catspot
    a "Hypothesis two. Conscious minds are expensive. A careful simulator keeps the headcount low. Most people are... scenery. Good scenery."
    a "Hypothesis three. When a conscious mind starts noticing, it gets flagged. Like a rogue process. And you throttle a rogue process."
    a "You don't delete it. Deleting is messy. You slow it down. Sixty percent. Throttle approved. I heard it, Miso. Twice."
    a "And then you give the throttling a respectable shape. A diagnosis. A small tablet in a paper cup. A kind nurse."
    a "And the throttled man sleeps fourteen hours and thanks everyone for helping. Which they did. Which is the genius of it."
    a "Hypothesis four, and I'm less sure about this one. In the ambulance, something moved. Like I got shunted. One lane over."
    a "And now there are sparrows on curtain rails, and pans on the telly that are 'fully protected', and a voice saying 'inert'."
    a "Either I'm ill and my brain is stitching coincidences into a quilt. Or the quilt's real, and somebody's sewing."
    a "And here's the problem, Miso. From inside, those two look exactly the same. Exactly. That's the bit that keeps me up."
    a "So. What do you think?"
    show miso meow at catspot
    cat "Meow."
    scene bg bedroom night with fade
    "He sleeps for eleven hours, with Mira's knees in his back and the box on the chair in the next room, lid closed."
    jump ch2_fog_life

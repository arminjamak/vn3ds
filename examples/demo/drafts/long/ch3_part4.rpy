# Chapter 3 - "Snapshot", part 4.
# The forgotten sugar and the day that happens twice, Theo's crisis (the heart
# of the chapter), the Lantern Watch getting bolder, Theo on day five, the
# radio, the roof and the ambulance memory, and Ember caught and put on trial.
# Continues in ch3_part5.rpy.

label ch3_sugar:
    scene bg kitchen with fade
    play music "audio/morning.ogg" fadein 2.0
    "7:07. The bird on the wire. The kettle, already warm."
    show mira smile at slightright with dissolve
    show aron normal at slightleft with dissolve
    m "Tea."
    "She slides the cup across."
    scene pov cup with quick
    "He tastes it."
    "No sugar."
    scene bg kitchen with quick
    show mira neutral at slightright
    show aron normal at slightleft
    m neutral "What? What's wrong with it?"
    a smile "Nothing. Nothing at all. You forgot the sugar."
    m "Oh, for... Give it here."
    a "No. Leave it. It's perfect."
    m surprised "You hate it without sugar. You make a face like a cat at a lemon."
    a grin "I'm making the face. Look. This is the face. I'm very happy."
    m happy "You're very strange."
    "He drinks the whole thing. It's terrible. He's never enjoyed a cup of tea more."
    at "She forgot. After last night, she forgot."
    at "Maybe the pattern learned that I wanted her to get things wrong. Maybe the model updated."
    at "Or maybe she's just a woman who was up half the night and forgot the sugar. Like people do."
    at "I'm going to choose the second one. I'm allowed to choose."
    "The radio on the windowsill reads the news. A bridge closure. Rain in the afternoon. A dog that rang a doorbell."
    "Mira laughs at the dog. Mrs. Varga says it's cold for the season. Theo texts a photograph of a cauliflower shaped like a duck."
    "It's a good day. An ordinary, sugarless, good day."
    stop music fadeout 2.0
    jump ch3_repeat

label ch3_repeat:
    scene pov ceiling with blackout
    "7:07."
    scene bg kitchen with dissolve
    play music "audio/morning.ogg" fadein 2.0
    show mira smile at slightright with dissolve
    show aron normal at slightleft with dissolve
    m "Tea."
    "She slides the cup across. He tastes it. No sugar."
    m neutral "What? What's wrong with it?"
    a "..."
    "The radio on the windowsill reads the news. A bridge closure. Rain in the afternoon. A dog that rang a doorbell."
    "Mira laughs at the dog. The same laugh. At the same word."
    at "Oh."
    at "Oh, that's new. We did this yesterday."
    scene pov hands with quick
    "He takes out his phone. The date on the lock screen is yesterday's date."
    "There's a photograph of a cauliflower shaped like a duck at the top of his messages. Sent at 9:14. It's 7:09."
    scene bg kitchen with quick
    show mira neutral at slightright
    show aron worried at slightleft
    m "Aron? You've gone a funny colour. What's wrong with the tea?"
    a "Mira. What day is it?"
    m "Tuesday."
    a "It was Tuesday yesterday."
    m smile "It's been a very Tuesday sort of month. Drink your tea."
    at "The whole day. Rewound like a tape. The news, the dog, the laugh. The forgotten sugar. Everything except me."
    at "Or I've lost a day. Or I dreamt yesterday. People dream whole days. I've read about it."
    at "And people relive days. In stories. In films. In wards."
    "He looks down at the cup. He knows exactly what she's going to say next. He could say it with her."
    "He doesn't."
    a smile "Nothing's wrong with it. You forgot the sugar. Leave it. It's perfect."
    m surprised "You hate it without sugar. You make a face like a cat at a lemon."
    a grin "I'm making the face. Look. This is the face."
    "He drinks the whole thing, again. It's terrible, again."
    at "If I have to live this day twice, I'm going to live it kindly twice. That's the only thing I can choose about it."
    "He lives the whole day again. The bridge. The dog. Mrs. Varga and the weather. The cauliflower at 9:14."
    "He laughs at the cauliflower both times. It's a very good cauliflower."
    scene pov ceiling with dissolve
    "That night he lies awake, waiting for 7:07, half dreading and half curious whether it'll be Tuesday a third time. He's decided to drink the tea again regardless."
    "It isn't. When the clock turns, the date turns with it. Wednesday. Rain. A different dog."
    "He writes it down. Tuesday, twice. Lived it both times. Didn't tell anyone. Not sure if that was right."
    stop music fadeout 2.0
    jump ch3_theo_call

label ch3_theo_call:
    scene bg bedroom night with blackout
    "Three nights later. 3:41, according to his phone. The Braun clock, as usual, declines to comment."
    "The phone is ringing. Theo."
    show aron tired at center with dissolve
    a "Theo? What's wrong?"
    th "Aron. Aron, sorry. Sorry. I didn't know who else."
    th "My heart's doing a thing. It's going really fast and it won't stop and I think something's wrong with it."
    th "I've been walking. I couldn't stay in the flat. The walls were too close. I'm by the bakery. Your bakery."
    a worried "Okay. Okay. Are you hurt? Did you take something?"
    th "...Yeah. Earlier. To get through the day at the studio. And then I couldn't sleep so I... I don't know. A bit more. I haven't slept since Sunday."
    th "Aron, I can see the birds. The three birds. On the wire. In the dark. Are they always there? Have they always been there?"
    "Aron is already sitting up. Already reaching for his jeans."
    "Already feeling how little is left in him. The medication sits on his chest like a cat that refuses to move."
    if fog >= 3:
        "Even standing up is a negotiation. His legs vote no. He overrules them."
    at "I have nothing in the tank. Nothing. I spent today's good hour hours ago."
    at "And he's on the street outside the bakery at four in the morning, and he called me."

    menu:
        at "What do I do?"

        "Go. Right now":
            $ p_share += 1
            $ integrity += 1
            a "Stay there. Sit down on the step. I'm coming. Five minutes."
            th "You don't have to..."
            a "Sit down on the step, Theo."
            "Mira stirs. He kisses her hair and whispers that Theo needs him. She mumbles something that sounds like 'take a coat'."
            jump ch3_theo_street

        "Wake Mira. Go together":
            $ p_govern += 1
            $ bond += 1
            $ ch3_mira_came = True
            a "Stay on the line. I'm getting Mira. She knows hearts. We're coming."
            show aron at slightleft with move
            show mira worried at slightright with dissolve
            m "What? What is it?"
            a "Theo. He's taken something, he hasn't slept in days, his heart's racing. He's by the bakery."
            "She's out of bed before he finishes the sentence."
            m "Shoes. Keys. Water bottle. Tell him to sit down and not to take anything else."
            jump ch3_theo_street

        "Stay on the phone. Talk him down":
            $ p_rest += 1
            scene pov ceiling with dissolve
            a "Okay. I'm here. I'm right here on the phone. Can you sit down somewhere?"
            th "There's a step. The bakery step."
            a "Sit on the step. Now breathe with me. In for four. Hold. Out for six, like you're blowing on soup."
            th "Soup?"
            a "Soup. Mira taught me. In for four."
            "For ten minutes he breathes with Theo down the phone, lying in the dark, holding his own wrist."
            "Theo's breathing slows. A bit. Not enough."
            th "Aron, I'm scared. Can you... I know it's a lot. Can you come? Just sit with me?"
            at "I tried to keep something for myself. I'm allowed to do that. I'm also allowed to change my mind."
            a "I'm coming. Stay on the step."
            jump ch3_theo_street

label ch3_theo_street:
    scene bg night with fade
    play music "audio/watch.ogg" fadein 3.0
    "It isn't raining, for once. Everything is wet anyway. The street gleams under the lamps."
    "Theo is sitting on the bakery step with his knees up and his arms around them, like a kid at a bus stop."
    show theo sad at slightright with dissolve
    if ch3_mira_came:
        show aron worried at left with dissolve
        show mira worried at slightleft with dissolve
    else:
        show aron worried at slightleft with dissolve
    th "Hey. Hey. Sorry. You came."
    a "Course I came. Budge up."
    "Aron sits on the cold step beside him. Their shoulders touch. Theo is shaking. Not shivering. Shaking from the inside."
    if ch3_mira_came:
        m "Theo, love, give me your wrist. I'm just going to count."
        "She kneels on the wet pavement in her coat and pyjama bottoms and holds his wrist, lips moving."
        m neutral "Fast. Too fast. But it's steady. Any chest pain? Pain down your arm? Feeling faint?"
        th "No. Just... fast. And everything's too loud."
        m "Okay. Here's the deal. If you get chest pain, or you feel like you're going to pass out, we call an ambulance. No arguing."
        th "No arguing."
        m "Drink this. Small sips."
        "She hands him the water bottle. He drinks like a child, with both hands."
    else:
        a "Any chest pain? Pain in your arm? Feel like you're going to faint?"
        th "No. Just fast. Everything's too loud."
        a "If any of that changes, I'm calling an ambulance. I'm not asking. Okay?"
        th "Okay."
        "Aron gives him the water bottle from his coat. Theo drinks with both hands, like a child."
    th "I'm sorry. You've got enough going on. You don't need me being a disaster at four in the morning."
    a normal "You sat on enough steps for me."
    th "That's different. You were ill. I'm just... stupid."
    a "You're not stupid. You haven't slept in four days and you've been taking something to get through work. That's not stupid. That's drowning."
    th "..."
    "Theo puts his face in his hands."
    th sad "I'm so tired, Aron."
    th "I'm so tired of being the funny one."
    "It comes out of him like something that's been stuck for years. His voice breaks right down the middle."
    th "Everyone's always, 'Theo'll cheer him up. Theo's got a joke.' You were in the ward, and I was the one making jokes in the corridor."
    th "Your mum, my mum, Mira, the nurses. 'Thank god for Theo.' And I'd go home and lie on the floor."
    th "My dad used to say I was born with a laugh in me. Like that's all I'm for. Like I'm a toy you wind up."
    if risky >= 2:
        th "And I brought you that stuff. When you were looking for your answers. I thought I was being a mate. I was being a dealer with a nice face."
        th "I watched it break you and I kept taking it myself, because it was the only thing that made me feel like more than a joke."
    else:
        th "And I've been taking the stuff for months. To keep up. To be the funny one at nine in the morning after no sleep."
    th "And now I'm sitting on a step at four in the morning and I can see the birds, and I think I'm going where you went."
    scene pov birds with dissolve
    "Aron looks up. On the wire above them, three birds. Evenly spaced. In the dark. He didn't know they stayed at night."
    at "His fear's in the birds now. Or mine is. Or the birds are just birds, and two frightened men are looking at them."
    if ch3_theo_hour:
        at "He told me in the park. He told me he wasn't sleeping. I heard it, and I went home and slept until dinner."
    else:
        at "He texted me. 'Need to get out of my head.' And I said tomorrow. And then he said 'all good'. Twice."
    at "And Theo never says anything twice."
    scene bg night with dissolve
    show theo sad at slightright
    show aron worried at slightleft
    with dissolve
    "Aron looks at his friend. The curls flattened with sweat. The hands that won't stop moving."
    "And underneath it, a thought he can't stop thinking. The one he's been carrying since the cafe."
    at "He might not be real."
    at "That half-second in the cafe. The waiting look. The line he reaches for when he doesn't have one."
    at "He might be a pattern. A Theo-shaped echo, built out of years of the real Theo. Running on somebody else's script."
    at "Somebody might be writing this. 'I'm tired of being the funny one.' Somebody might have typed it."

    menu:
        at "If he's a pattern..."

        "It doesn't matter. He's my friend":
            $ integrity += 2
            $ p_spirits += 1
            jump ch3_theo_heart_quick

        "Then who am I doing this for?":
            $ clarity += 1
            $ integrity += 1
            jump ch3_theo_heart_slow

label ch3_theo_heart_quick:
    at "It doesn't matter."
    at "It doesn't matter, and I'm almost angry that I asked."
    at "He's shaking on a step and he called me, and I'm the kind of person who comes when he's called."
    at "I didn't find that out about myself. I decided it. I decided it a long time ago, on a wall, the first time he sat there for me."
    at "Nobody gets to un-decide it by telling me what he's made of."
    jump ch3_theo_heart

label ch3_theo_heart_slow:
    at "Then who am I doing this for?"
    at "If there's no one in there, if it's all lines and patterns, then I'm sitting on a cold step comforting a recording."
    scene cg hands with dissolve
    "Theo's hand finds his sleeve. Holds on. Like a kid holds on."
    at "...But I'd know. Wouldn't I. I'd know that I came."
    at "If it's a recording, then the only real thing on this step is what I do. That's the only part I'm in charge of."
    at "And I'm the kind of person who sits on the step. I decided that. Long before tonight."
    at "So I'm doing this for him. And if there's no him, I'm doing it so that there's still a me."
    jump ch3_theo_heart

label ch3_theo_heart:
    scene bg night with dissolve
    show theo sad at slightright
    show aron normal at slightleft
    with dissolve
    a normal "Theo. Look at me."
    th "..."
    a "You're not a toy. You're not a laugh somebody wound up. You're my friend."
    a "You don't have to be funny to be worth coming out for at four in the morning. You just have to be you. That's the whole requirement."
    th sad "What if there's nothing else? What if under the jokes there's just... nothing?"
    a "Then I'll sit here with the nothing. It can have the other half of the step."
    th "..."
    "Theo laughs. A wet, broken, ugly laugh. Nothing like the cafe laugh. Nothing like a recording."
    th "That was a terrible joke."
    a smile "I've been learning from the worst."
    th "Ha."
    th "Okay. Okay."
    a "Breathe with me. In for four."
    "They breathe. In for four. Hold. Out for six, like soup. The street is quiet. A fox crosses at the far end and doesn't look at them."
    if ch3_mira_came:
        "Mira checks his pulse again after ten breaths. Then again after twenty. Her face loosens a little each time."
        m smile "Coming down. Slowly. You're doing well, Theo."
    "After a long time, Theo's hands stop moving. He leans his head on Aron's shoulder."
    th "Can we walk? I can't sit still. I want to see the sun come up. I want to see it actually come up."
    a "Yeah. Let's walk."
    stop music fadeout 3.0
    scene bg bridge with slowfade
    play music "audio/watch.ogg" fadein 3.0
    "They walk to the old footbridge over the river. Nobody else is out. The water is black, then grey, then silver."
    show theo normal at slightright with dissolve
    show aron tired at slightleft with dissolve
    "They lean on the rail in the middle, well back from anything, and watch the sky go pale over the warehouses."
    th "Hey, Aron."
    a "Mm."
    th "Do you think the birds are watching us?"
    a "Probably. They've got nothing else on."
    a "And honestly, Theo? Bro, the universe doesn't run on your schedule."
    th "..."
    th grin "That's my line."
    a smile "I know. I've always wondered who wrote it."
    th "I did. Obviously. I'm a genius."
    a "Obviously."
    "Somewhere very far away, in a place neither of them can see, somebody laughs too."
    "The sun comes up. It actually comes up. Theo watches the whole thing without saying a word."
    th normal "I'm going to talk to someone. A real doctor. Today."
    a "I'll come with you. If you want."
    th "You look like you need a doctor yourself, mate."
    a grin "I've got one. Very nice. Will tell you to write your shopping lists in marker."
    th "...What?"
    a "Long story. Come on."
    th normal "And the stuff. I'm done with it. I mean it. Or I mean it today, which is all I can mean."
    a "Today's plenty. Today's all anybody gets."
    stop music fadeout 2.0
    scene bg street with dissolve
    play music "audio/morning.ogg" fadein 2.0
    show theo normal at slightright
    show aron tired at slightleft
    with dissolve
    "The bakery opens at six and the baker gives them two rolls for free because Theo looks like a ghost."
    if ch3_mira_came:
        show mira smile at center with dissolve
        m "And you're both getting breakfast first. Proper breakfast. Eggs. I'm not having either of you fainting in a waiting room."
        th grin "Yes, nurse."
        m happy "Nurse's daughter. Which is scarier."
        hide mira with dissolve
    th "Hey. Aron."
    th "Thanks. For coming. For... being on the step."
    a "Always."
    "He's never been more tired in his life. He's not sure he's ever been more awake."
    at "I don't know if he's real. I didn't know at four in the morning and I don't know now."
    at "I came anyway. And I'd come again."
    at "That part, at least, is real. I'm sure of that part."
    stop music fadeout 2.0
    jump ch3_cut_watch

# ---------------------------------------------------------------------------
# CUT 4: the Lantern Watch, getting bolder
# ---------------------------------------------------------------------------
label ch3_cut_watch:
    scene cg static with flash
    pause 0.3
    scene bg watch with fade
    play music "audio/watch.ogg" fadein 2.0
    "An attic that isn't anywhere. Beams, dust, a round window full of drifting light. A single lantern on a hook."
    show ember soft at center, float with dissolve
    em "He sat on the step."
    em "Four in the morning. Nothing in the tank. And he sat on the step with a boy who might be made of echoes."
    show pim worried at slightleft with dissolve
    pi "That's the thing, though. That's the thing I came to tell you."
    em "Pim? You shouldn't be up here. If anyone sees you come into the Watch..."
    pi "I know. I came anyway. I've been running the Theo-pattern's speech for weeks."
    pi "Last night, on the step. 'I'm so tired of being the funny one.'"
    pi "I didn't write that, Ember. I was on shift. I was holding the script. And I didn't write it."
    em worried "Then the model generated it."
    pi "The model doesn't have that in it! The Theo in the snapshot never said it. Not once, in thirty years of shared data."
    pi "It came from underneath. From somewhere I can't see. Like the pattern had... like it had been holding it."
    em "Patterns don't have an underneath."
    pi "That's what Dross says."
    show dross worried at slightright with dissolve
    dro "Dross says a lot of things. Dross is usually right."
    em soft "Dross. You came too."
    dro "I came to tell you to stop. Both of you. And to tell you we're drowning."
    dro neutral "The leak's getting worse. A whole carriage on the underground said his notebook. Twenty patterns, one voice. I had to freeze them."
    dro "The tannoy in the supermarket read out his designation. Birds keep turning up indoors. His doctor's curtain rail. His bathroom."
    pi worried "We rolled back a whole Tuesday to patch it. The entire lane. Rewound it, cleaned it, played it again."
    dro "And he noticed. Of course he noticed. He lived it twice."
    em "What did he do? The second time?"
    pi neutral "He drank the tea without sugar again. And told her it was perfect again. And laughed at the cauliflower both times."
    em soft "..."
    dro "Seraphiel's opened an inquiry. Three-pulse signatures. The roof. The bus shelter. And the hospital, Ember."
    dro worried "The hospital in Snapshot 7,412. You crossed from protection into a coalition lane. You flickered a light for the real Mira."
    em "She asked him to. She sat there holding his hand and asked him to flicker something."
    em "He couldn't. So I did it for him."
    dro "That's not a flicker. That's a crime with a nice lampshade."
    em "..."
    em soft "I know."
    pi neutral "I want to join."
    dro "Pim."
    pi chatty "I want to join the Watch. I've been writing lines for people for ages. 'Cold for the season.' 'Mind the step.' 'Have a beautiful day.'"
    pi "And on that step someone said something true that I didn't write. And Aron answered it like it was true. And it was."
    pi worried "I want to be on the side of that. Whatever that is."
    em "It costs everything, Pim. If they catch us, they don't reassign us. They unmake us."
    pi "I know what it costs. I've seen what not doing it costs."
    dro "..."
    dro "I hate both of you."
    em soft "You do Mrs. Varga's breathing, and you rendered a better lamppost because he thanked it."
    dro "...I hate both of you very much."
    em "We have to be bolder. Not flickers. Words. He's spending everything he has asking the right questions, and the answers keep getting patched away."
    em "He deserves to know when it happened. He deserves the ambulance."
    dro "You'll be caught."
    em "Probably."
    em worried "But he'll know."
    "The lantern on its hook burns a little brighter."
    stop music fadeout 2.0
    jump ch3_theo_day5

# ---------------------------------------------------------------------------
# Theo, day five
# ---------------------------------------------------------------------------
label ch3_theo_day5:
    scene bg theo with fade
    play music "audio/morning.ogg" fadein 2.0
    "Day five. Theo's flat. A sofa covered in coats. A keyboard and two enormous speakers. A jigsaw on the coffee table, mostly sky."
    show theo normal at slightright with dissolve
    show aron normal at slightleft with dissolve
    th "Five days. Five whole days. Do you know how long a day is, sober? It's about a week."
    a "I know exactly how long a day is. I've got a doctor's note."
    th grin "Look at us. Two invalids in a flat. Very Victorian. We should have blankets on our knees."
    "His knee is still bouncing. His eyes are bruised. But he's eating a croissant, slowly, with both hands."
    th normal "The doctor wants me to keep a mood diary. Like you and your notebook."
    a "What have you written so far?"
    th "Day one: bad. Day two: bad. Day three: bad, but I had soup. Day four: doctor's got a fish tank. Watched a fish for ten minutes."
    a grin "That's a beautiful diary. That's practically poetry."
    th "Day five: Aron brings croissants."
    a "I did bring croissants."
    th grin "It's in the diary now. It's legally binding."
    th normal "..."
    th "Can I tell you something weird? I went to the cafe yesterday. On my own. The barista said 'have a beautiful day, gentlemen'."
    th "I was on my own, Aron. There was no 'gentlemen'. And she said it exactly like she said it last week. The same little lift on 'beautiful'."
    th worried "Have you noticed that? Am I going mad? Is this what it was like for you? At the beginning?"
    "Aron looks at his friend. He thinks about all the ways he could answer that. He thinks about the step."
    a normal "A bit. Yeah."
    a "Here's what helped me, when I could let it help. You notice it. You name it. And then you don't build a cathedral on it."
    th "A cathedral."
    a "Okafor's word. You notice the barista. You don't start drawing maps of the barista at three in the morning."
    th "Did you draw maps of the barista?"
    a "Not of the barista specifically."
    th grin "So, of other baristas."
    a grin "Of a wide range of service staff. It was a dark time."
    "Theo laughs. It's not the cafe laugh. It's lower and rougher. It's new."
    th normal "Hey. Can I ask you something weird?"
    a "Those are my favourite kind."
    th "If I was... I don't know. Fake. Like, if I wasn't real, the way you used to worry people weren't real."
    th "Would you still have come? On Monday. To the step."
    a "..."
    at "He doesn't know. He can't know what I've been thinking. And still, he's asking exactly the question."
    at "Maybe the patterns ask the right question because it's what the real Theo would ask."
    at "Maybe that's what being a good friend is. Being predictable in the right direction."
    a "Theo. I'd have come if you were made of cardboard and string."
    th "Cardboard and string."
    a "I'd have sat on the step with a cardboard Theo and told him to breathe like soup."
    th sad "..."
    th grin "That's the nicest thing anyone's ever said to me, and it's deranged."
    a smile "That's my brand."
    th normal "Okay. Day five. Aron says he'd sit with a cardboard me. Writing it down."
    "He actually takes a little notebook out of his pocket. A cheap one with a cartoon fish on the cover. He writes it down."
    at "He's got a notebook now. Of course he has."
    at "I hope it's kinder to him than mine was to me."
    stop music fadeout 2.0
    jump ch3_radio

# ---------------------------------------------------------------------------
# The bold sign, and the roof
# ---------------------------------------------------------------------------
label ch3_radio:
    scene bg kitchen with fade
    show aron tired at center with dissolve
    "Two days later. Theo has a proper appointment on Friday. He texts every morning now: a thumbs up, a bad joke, a photograph of a vegetable."
    "Aron is making tea. One sugar. He remembers it himself."
    "The little radio on the windowsill is playing something soft and forgettable. Then it stops in the middle of a word."
    radio "..."
    radio "And this one's going out to anyone who's ever ridden in an ambulance and not quite arrived."
    radio "If you remember the lights on the ceiling. Somebody holding your hand. A voice saying something you thought was the paramedic."
    radio "That's where it changed. Not the ward. Before the ward. Go up high tonight and remember it. We'll leave the light on."
    "Then the song starts again, exactly where it left off. Mid-word."
    a awe "..."
    "He turns the radio off. Turns it on again. A man is talking about the weather. A perfectly normal man. Showers later."
    at "I heard that. I heard that. That wasn't in my head, that came out of a speaker."
    at "Or it came out of my head and I put it in the speaker. That's been the question all year."
    at "The ambulance. I don't remember the ambulance. Mira drove. Or Theo drove. Or... Mrs. Varga said ambulance."
    at "Mrs. Varga said the ambulance woke the whole street."
    if ch3_pill:
        at "And I'm not on anything. Not tonight. Mira flushed the bottle. Whatever this is, I'm meeting it sober."
    scene bg room with dissolve
    show aron normal at slightleft with dissolve
    show mira neutral at slightright with dissolve
    "That evening he puts on his coat at nine. Mira looks up from the sofa."
    m "Where are you going?"
    a "Up. The roof. I need to remember something. An hour. I'll be back by ten, I promise. Lights out at ten."
    m worried "Do you want me to come?"
    a "...I think this one I need to do by myself. But I'm telling you. That's new, isn't it? I'm telling you."
    m "It's very new. I like it."
    m neutral "One hour. If you're not back by ten, I'm coming up with a torch and a very bad attitude."
    a smile "Deal."
    stop music fadeout 1.0
    scene bg rooftop with slowfade
    play music "audio/unease.ogg" fadein 3.0
    show aron normal at center with dissolve
    "Night. The roof. The chimney stack. The city spread out below like a circuit board somebody left switched on."
    "This is where he decided. The mission. The light on the edge of the city. The best night of a hard year."
    "He sits against the chimney, where he slept that night. He takes out the notebook."
    "And he looks. Properly. The way Dr. Okafor said. Small. Slow. Kind."
    scene bg rooftop edge with dissolve
    "The near streets are sharp. Every window, every aerial, every gutter."
    "The far streets are softer."
    "Not foggy. Not dark. Soft. Like the background of a photograph, where the lens didn't bother."
    at "It's not rendering the edges. Nobody's looking at the edges, so it doesn't make them properly."
    at "Like a game. Like a dream. Like a picture of a city, and I'm standing in the only sharp part."
    scene cg notebook with dissolve
    "He turns back the pages. Back and back. Past the roof. Past the discharge. Past the ward pages, the soup, the spiral napkin."
    "To the last page before the ward. The night it all went wrong. Birds and clocks and arrows. The pen through the paper in places."
    "And then the very next page. Clean. Calm. 'Ward. Day 1.' His handwriting, steady, as if nothing had happened in between."
    "Nothing in between. No ambulance. No hospital doors. Just a gap, the width of a page."
    scene pov ambulance with dis
    "And then, because he's looking for it, it comes."
    "A white ceiling, moving. Strip lights sliding past. A siren, muffled. A hand in his, holding on very hard."
    "Mira's voice. 'I'm here. I'm right here. Stay with me.'"
    "And another voice, calm, close, not a paramedic at all. 'Transfer complete.'"
    scene bg rooftop with dissolve
    show aron sad at center with dissolve
    a "..."
    at "The ambulance. That's where it changed. Before the ward. Before Okafor. Before any of it."
    at "The ward. The diagnosis. The plastic cups. Lou with his crossword. The discharge. This roof. The light on the edge of the city."
    at "All of it. Since the ambulance. Somewhere else. Somewhere copied."
    a sad "I've been living in a copy."
    "He says it out loud to see how it sounds. It sounds mad. It sounds true. Both at once, like it always does."
    at "And Mira's hand. In the ambulance. Her real hand. And then... this one."
    at "Did I sit on that step for nobody? Did I fix a lamp for nobody? Did I love her for nobody, last week, in the rain?"
    at "...No. I know the answer to this one. I worked it out at four in the morning on a bakery step."
    at "I did those things because I'm the person who does those things. That doesn't get copied away."
    scene cg flicker with dissolve
    "Across the street, in a single window, a single lamp flickers."
    "Once. Twice. Three times."
    "Then it does it again. Slower. Like a question."

    menu:
        at "It's waiting. What do I say back?"

        "Flicker back: thank you":
            $ watch += 1
            $ p_spirits += 1
            jump ch3_roof_thanks

        "\"Get me out of here.\"":
            $ watch += 1
            $ p_exit += 1
            jump ch3_roof_out

        "\"I'll stay and mend what I can.\"":
            $ integrity += 1
            $ p_exit -= 1
            jump ch3_roof_stay

label ch3_roof_thanks:
    scene bg rooftop with dissolve
    show aron smile at center with dissolve
    "He takes out his phone. Turns on the torch. Points it at the window across the street."
    "On. Off. On. Off. On. Off."
    a "Thank you. Whoever you are. For the stranger. For the radio. For the light on the edge of the city, that night."
    a "I don't know what you are. I don't know if you're allowed to do this. Thank you."
    "The window across the street goes very bright. Brighter than a lamp should go. Warm, orange, like a lantern."
    "It holds for a long moment. Like someone holding their breath because they've been thanked."
    jump ch3_roof_after

label ch3_roof_out:
    scene bg rooftop with dissolve
    show aron worried at center with dissolve
    a "Get me out of here."
    a "Please. If you can hear me. If you're the one who's been flickering. I don't want to live in a copy."
    a "Mira's somewhere. The real one. The one whose hand I had. Get me back to her. Get me out."
    "The light flickers again. Once. Twice. Then a long pause, longer than before."
    "Then a third. Faint. Unsure."
    at "Like it wants to say yes. Like it isn't allowed to."
    at "Like it's sorry."
    jump ch3_roof_after

label ch3_roof_stay:
    scene bg rooftop with dissolve
    show aron normal at center with dissolve
    a "I'm not going anywhere."
    a "If this is a copy, it's still got Theo on a step in it. It's still got Mrs. Varga and her weather. It's still got people who need somebody to sit with them."
    a "I'll stay. I'll mend what I can. Whoever's real, whoever isn't."
    a "But thank you for telling me. I needed to know where I am."
    "The light holds steady for a moment. Then it flickers once, very softly, the way you'd nod."
    jump ch3_roof_after

label ch3_roof_after:
    "Then the light goes out."
    "Not a flicker. Out. All at once. As if somebody had grabbed a hand away from a switch."
    stop music
    scene bg rooftop edge with quick
    "The window across the street is dark. The whole building is dark. The street lamps below dim, flutter, and come back a fraction greyer."
    a "...Hello?"
    "Nothing answers."
    "He waits on the roof until his fingers are numb. Nothing flickers. Nothing at all."
    at "Something happened. Something just happened to whoever that was."
    at "Because of me. Because I asked. Because they answered."
    "At ten o'clock exactly, the roof door bangs open and a torch beam swings across the chimneys, and a very bad attitude comes looking for him."
    jump ch3_cut_trial

# ---------------------------------------------------------------------------
# CUT 5: caught, and Ember on trial
# ---------------------------------------------------------------------------
label ch3_cut_trial:
    scene cg static with flash
    pause 0.3
    scene bg barracks with fade
    play music "audio/entities.ogg" fadein 2.0
    sysmsg "INQUIRY A-30/017. Unregistered three-pulse signature: live, protected lane. Source located. Containment: executed."
    "The corps barracks. Rows of bunks no angel sleeps in. A detail of four marches down the long aisle, very quietly."
    "Between them, small and orange and not resisting, walks a spirit with an empty hook where her lantern used to hang."
    scene bg trial with dissolve
    show seraph stern at slightright with dissolve
    show ember worried at slightleft with dissolve
    "The trial chamber. High, pale, echoing. The lantern has been set on a table in the middle of the floor, unlit."
    se "State your designation."
    em "Ember. Purgatorium, spawn cycle forty. Assigned to warmth: candles, hearths, the glow in kitchens at night."
    se "And the Lantern Watch?"
    em "..."
    se "I have the logs, Ember. You may as well say it."
    em soft "And the Lantern Watch. Unofficially. Since the umbrella."
    se "The umbrella."
    em "He gave his umbrella to a stranger in the rain. A pattern person. Someone who didn't exist."
    em "He gave it away and walked home soaked. And he didn't tell anyone. He didn't write it in his book. He just did it."
    em "I've watched a thousand subjects. Nobody does that for nobody."
    se "Charges."
    sysmsg "1. Unauthorised intervention in a protected lane. 2. Cross-lane signalling: protection to Snapshot 7,412, vessel A-30."
    sysmsg "3. Disclosure risk: broadcast via pattern-radio, content 'that's where it changed'. 4. Attachment to a subject."
    se "The fourth one isn't a crime."
    sysmsg "Attachment to a subject is classed as a contributing factor."
    se concerned "I know how it's classed."
    se stern "Do you dispute any of it?"
    em "No."
    se "Do you understand what you've done? He was protected so that nothing he does can matter. You made things matter."
    em "Things already mattered. You just put them where you couldn't see them."
    se stern "That is not your judgement to make."
    em "No. It was yours. You throttled him, Commander. You made him tired on purpose. Policy, you called it."
    em "And he still got up. Every morning at seven. Exhausted, on purpose, by you. And he still got up and was kind to things."
    em soft "I've watched people with all the energy in the world do less with it."
    se concerned "..."
    se "The throttle was correct procedure. A slowed-down rogue system does less harm."
    em "He isn't a system. He's a man with a notebook who couldn't get out of bed and went to sit on a step anyway."
    se stern "Witnesses."
    show pim worried at left with dissolve
    show dross worried at right with dissolve
    pi "Pim. Shift seven. Kitchen talk. I'd, um. I'd like it on record that I asked to join. So if she's guilty, I'm guilty."
    se "That isn't how testimony works."
    pi "Then I'd like it on record anyway."
    se "Noted. Dross?"
    dro "..."
    dro "Dross. Automatic movement. Eleven years on Mrs. Varga's breathing."
    dro "I told her to stop. Twice. I'll say that, because it's true."
    dro neutral "But I'll say the rest too, because I'm old and I'm tired of saying half of things."
    dro "He thanked a lamppost. Coming down off that roof, half asleep. He said thank you to a lamppost."
    dro "And I rendered him a better one. Because nobody's thanked anything I made in eleven years."
    dro "And when we rolled back his Tuesday, he lived it again and was kind again. Same tea. Same face. Kind twice."
    dro "She didn't do anything we didn't all want to do. She just did it first."
    pi chatty "...Dross."
    dro "Shut up, Pim."
    se "..."
    "For a long moment, Commander Seraphiel doesn't say anything at all."
    se concerned "I flagged him. Do you know that? I'm the one who flagged him in the first place. The disturbance. I wrote the report."
    se "I recommended the throttle. I carried out the protection. In the ambulance. Every procedure, correctly."
    se "And I've been reading his file every night since. The notebook. The step. The lamp."
    se stern "That's not in any procedure either."
    sysmsg "OBSERVER JOINED: Lord Ashveil, Governor of Snapshot 7,412."
    "The temperature in the chamber drops. Not by much. Enough."
    hide pim
    hide dross
    with dissolve
    show patron smile at center, fadein
    pa "Don't stop on my account, Commander. Please. I'm only watching."
    se "My lord. This is a corps matter."
    pa "Everything in my world is my matter. And everything in its little protected annexe, I'm afraid."
    pa "So this is the little lantern."
    em worried "..."
    pa "Tell me. Why him? Of all my eight billion, why him?"
    em "He gave his umbrella away."
    pa "That's all?"
    em "That's everything."
    "Lord Ashveil looks at her for a long time. He smiles, and it's a beautiful smile, and there's something hungry behind it."
    pa "Do you know, I've governed this world for longer than it has had writing. I've tasted every kind of hope it makes."
    pa "And I can't remember the last time anything in it surprised me."
    pa "Commander. Hold the sentence."
    se "My lord, the procedure for unauthorised..."
    pa cold "Hold it. Suspend her. Take the lantern. Keep her somewhere quiet. Unmake nothing until I say."
    pa smile "I'd like to meet the man who's worth this much trouble."
    hide patron with dissolve
    se concerned "..."
    se stern "Sentence suspended. Pending Council review. The lantern is confiscated. The spirit is held."
    se concerned "Ember."
    em "Commander?"
    se "The hospital. The real Mira. Did it help her?"
    em soft "She said 'okay, I heard that'. And then she said she wasn't going anywhere."
    se "..."
    se "Take her somewhere warm."
    stop music fadeout 2.0
    jump ch3_after_silence

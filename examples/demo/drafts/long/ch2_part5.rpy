# Snapshot - Chapter 2: "Fog" (part 5 of 6)
# Theo's birthday at the club: one night with street speed, or a gentler
# route, and the morning after. Continues in ch2_part6.rpy.

default ch2_took_speed = False
default ch2_night_route = 0

label ch2_speed_setup:
    scene bg kitchen table with fade
    play music "audio/morning.ogg" fadein 2.0
    "The weeks after that are smaller and steadier. Morning walk. Ducks. The good hour at four. Evening dose."
    "At the clinic, Dr. Okafor lowers the dose by a step. 'Stable,' Okafor says, and writes it down, and it sounds like a prize."
    "The wet sand dries out a little. Not to how it was. To something like damp beach. Walkable, if you don't run."
    show aron normal at slightleft with dissolve
    show mira smile at slightright with dissolve
    m "So. This weekend. Hen do. My cousin Dorota. Two nights in a cottage with eleven women and a karaoke machine."
    a "That sounds like a war crime."
    m happy "It is a war crime. I'm a combatant. I've been practising 'Total Eclipse of the Heart' in the car."
    m neutral "And it's Theo's birthday Saturday."
    a "Thirty-one. Jojo's got him a table at that club by the ring road."
    m worried "Jojo."
    a "I know."
    m "Jojo's nights are... Jojo's nights. You don't have to go."
    a "He lost his job last week, Mira. It's his birthday. I want to be there for an hour. Then I'll come home and sleep."
    m "An hour."
    a "An hour. Fizzy water. Home by eleven."
    m "Text me. Every hour. Vegetables if you have to."
    a "I'll find the most suggestive carrot in the city."
    m smile "That's all I've ever wanted from a man."
    scene bg kitchen with dissolve
    "She kisses him, and picks up her bag, and the door clicks, and the flat is very quiet for a Friday."
    show miso stare at catspot with dissolve
    "Miso watches him from the windowsill with the expression of a cat who has read the forecast."
    jump ch2_party

label ch2_party:
    stop music fadeout 2.0
    scene bg street rain with slowfade
    "Saturday. The club is under a railway arch on the wrong side of the ring road. You can feel the bass from the bus stop."
    "It's raining. Not much. Enough to remember the last time it rained like this, and the mirror, and the night after."
    "There's a queue. A doorman in a black puffer jacket with a clipboard and a face like a closed shop."
    ch2_bouncer "Name?"
    a "Aron. I'm with Theo. The birthday."
    ch2_bouncer "Aron..."
    "He runs a finger down the clipboard. Stops. Looks up. Looks at Aron for a long, flat second."
    ch2_bouncer "Subject. Right. In you go."
    a "...Sorry?"
    ch2_bouncer "Subject to a search, mate. Arms up. Everyone gets it."
    "Hands pat his pockets, his sides, the notebook in his jacket. The doorman waves him through without looking at him again."
    at "Subject to a search. People say that. Doormen say that."
    at "He stopped after the first word, though. He looked at me, and stopped, like the rest of the sentence was late."
    scene bg club with dissolve
    play music "audio/unease.ogg" fadein 2.0
    "Inside, it's dark. Coloured lights on a chain. Bodies. Heat. Somebody's playlist that is all the same song in different hats."
    show theo grin at slightright with dissolve
    th "BRO. You came. You actually came. Everyone, this is Aron, he's been in a mental hospital and he still came!"
    show aron worried at slightleft with dissolve
    a "Thanks, Theo. Very discreet."
    th "Discretion's for people with jobs, man. I'm free now. I'm a free man."
    "His eyes are wet and bright. He's drunk, and under the drunk he's somewhere much lower, and he's dancing to keep from falling into it."
    "A tall man in a silver jacket leans in between them. Jojo. He smells of cologne and something chemical."
    ch2_jojo "The famous Aron. Theo talks about you all the time. The genius who cracked."
    a "Mostly the cracked bit, lately."
    ch2_jojo "Aren't we all, mate. Aren't we all."
    "Jojo presses something into Theo's hand. A tiny folded wrap of paper. Theo closes his fingers round it without looking."
    th normal "Birthday present. Not my pills. Proper stuff. Speed."
    if ch2_took_pill:
        th sad "And yeah, I know. I said never again. That was about you. This is about me. I just want one night where I don't feel like this."
    else:
        th sad "Don't look at me like that. I just want one night where I don't feel like this."
    th "And you..."
    th normal "You've been a patient for three months, bro. You could have one night where you're not. Just one. Like the old days."
    "The music swells. Somebody screams the chorus. The lights turn red."
    at "Speed. Not a prescription. Not a 'focus pill'. Something cooked by somebody I'll never meet."
    at "The pill gave me six hours of clear. This would give me more. I could see the whole thing. The table. The agenda. The edge of my lane."
    at "And Theo is about to take it alone, on the worst week of his life."

    menu:
        th "Well? Birthday boy says yes?"

        "Take it.":
            $ risky += 2
            $ clarity += 2
            $ p_rest -= 1
            $ ch2_took_speed = True
            $ ch2_night_route = 1
            jump ch2_speed_yes

        "Stay sober. Keep an eye on Theo.":
            $ bond += 1
            $ integrity += 1
            $ ch2_night_route = 2
            jump ch2_speed_watch

        "Get Theo out of there.":
            $ integrity += 1
            $ watch += 1
            $ ch2_night_route = 3
            jump ch2_speed_out

label ch2_speed_yes:
    a "...Yeah. Okay. One night."
    th grin "THAT'S my boy."
    "Later, he won't remember deciding. He'll remember the bitter taste. Jojo's grin. And how easy it was, again. How very easy."
    "For a while, nothing. He stands by the bar drinking fizzy water and feeling foolish."
    "Then the room snaps into focus like a camera finding the face."
    show aron awe at slightleft
    at "Oh."
    at "Oh, this isn't like the pill. The pill opened a window. This takes the wall down."
    "Everything is loud and clean and lit from inside. He can hear every conversation in the room at once and follow all of them."
    "And he can see it. Finally. All of it. The seams."
    at "That man by the speaker has said 'no way, no way' eleven times. Exactly the same pitch. Loop."
    at "That woman laughs every four seconds. Every four seconds. A metronome. Loop."
    at "Theo. Theo's real. Jojo... Jojo's half. He's half there. The rest is running on something else."
    "A stranger dances past him and shouts something over the music, cheerful, meaningless."
    stranger "A-thirty, mate! A-thirty! Big one tonight!"
    at "A-30. He said A-30. Or 'out till three'. Or 'I'm thirty'. The music's so loud. The music's so loud."
    "He's sure of it the way you're sure of your own name. He counts the room. Two hundred people. A handful of them lit. Everyone else hollow."
    "It's the most important thing he's ever understood, and he understands it with his whole body, and his heart is going like a drum solo."
    a "Theo. Theo. Hardly anyone in here is real. Hardly anyone."
    th grin "Bro, you're flying. Dance, man!"
    "He doesn't dance. He walks through the room looking into faces, and everyone he looks at looks back, and none of them are there."
    "A woman in a yellow dress is crying by the cloakroom. Mascara down both cheeks. Someone has been unkind to her."
    "He stops in front of her. He knows something she doesn't. He has to tell her. It's the kindest thing he can do."
    a "It's okay. Listen to me. It's okay. You don't have to cry. You're not real."
    ch2_girl "...What?"
    a "You're not real. It's fine! It doesn't hurt. Whatever he said to you, it doesn't matter, because none of this is..."
    "She looks at him. Her face does something he'll see for weeks afterwards, every time he closes his eyes."
    ch2_girl "What is wrong with you?"
    "She pushes past him. Somebody shouts. Somebody else says 'mate, mate, leave it'. A hand on his chest, not gentle."
    show theo worried at slightright
    th "Okay. Okay okay okay. Outside. We're going outside. Now."
    scene bg street rain with dissolve
    show aron awe at slightleft with dissolve
    show theo worried at slightright with dissolve
    "The rain is cold and wonderful on his face. Everything smells of metal and lightning."
    a "Theo, it ends. The world ends somewhere. If you walk in one direction long enough you hit the edge. The lane stops. I can feel it."
    th "Bro, it's two in the morning and it's raining. The only thing you'll hit is the ring road."
    a "No. No. Come on. Come on!"
    "He runs. Theo shouts and runs after him. Streetlights. Shop shutters. The canal, black and glittering."
    scene bg bridge with dissolve
    "He runs for an hour. He's sure the next corner will be the last one. It never is."
    "The streets go on. They go on and on, with their shut kebab shops and their bus stops and their wet, ordinary bins."
    "He stops at last on a bridge, gasping, with his heart hammering so hard he can see it in his vision."
    show aron worried at center with dissolve
    at "It doesn't end. Why doesn't it end?"
    at "Because they've drawn it further than I can run. Because they always draw it further than you can run."
    at "Or because it's a city, and cities go on, and I'm a man on speed on a bridge in the rain."
    scene pov hands with dissolve
    "His hands on the wet railing are shaking so hard the rain jumps off them. His jaw is clamped so tight his teeth squeak."
    "Something in his chest is fluttering wrong."
    scene bg bridge with dissolve
    show aron worried at slightleft with dissolve
    show theo worried at slightright with dissolve
    "Theo catches up, soaked, bent double, phone in his hand."
    th "I called Mira. I'm sorry. I'm sorry. She's getting a taxi. Two hours. I didn't know what else..."
    a "Theo. My heart's doing something."
    th "What? What's it doing?"
    a "I don't know. It's too fast. It's wrong."
    "Theo's face goes very white. For a moment, nobody in the world is drunk or high. There are just two frightened men on a bridge."
    th "Okay. Okay. We're going to the hospital. Not the ward. The other one. A and E. Right now."
    a "No, they'll... they'll put it in the file..."
    th "I don't care about the file! Bro, I don't care about anything except your stupid heart!"
    scene bg corridor with dissolve
    "A and E at four in the morning is a strip-lit corridor of people on the worst night of their lives."
    "A young doctor with a ponytail and kind, exhausted eyes clips a monitor to his finger and puts stickers on his chest."
    "Nobody calls him a junkie. Nobody shouts. They just ask what he took, and when, and he tells them, because Theo makes him."
    "His heart is racing, they say, but steady. They'll watch him. Fluids. Wait. He needs to rest. He needs to come down."
    "He lies on a trolley for five hours, watching the green line on the monitor jump, while Theo sleeps sitting up in a plastic chair."
    play sound "audio/voices.ogg"
    vox "...A-30. Energy far above ceiling. The lane is loud..."
    vox "...three leaks in one night... spirits can't keep up... tell the Commander..."
    stop sound fadeout 1.0
    at "Leaks. Leaks of what? Leaks from where?"
    at "Or nobody's saying anything, and I'm on a trolley in A and E, and my brain is saying the worst thing it can find."
    "Mira arrives at seven. She's still in her hen-do outfit: a sash that says 'BRIDE SQUAD', and her face completely white under the glitter."
    show mira worried at center with dissolve
    m "..."
    a "Mira..."
    "She doesn't say anything. She just walks straight to the trolley and puts her forehead against his, very carefully, avoiding the wires."
    "She's shaking. He's never seen her shake. Not in the rain. Not on the ward. Not when he said the word schizophrenia out loud."
    m sad "Theo said your heart."
    a "It's okay. They said it's okay. It's slowing down."
    m "I was singing karaoke. I was singing a stupid song in a stupid sash and my phone was in my bag."
    m "I listened to Theo's voicemail in the taxi. Twice. I thought I was going to... I thought..."
    "She can't finish. She doesn't have to."
    jump ch2_speed_after

label ch2_speed_watch:
    a "No. Not for me. I'm on fizzy water. I'll be the designated... brain."
    th normal "Suit yourself, bro."
    "Theo takes it. Just like that. A small, quick gesture, a mouth, a sip of beer. It looks like nothing at all."
    "Aron stays. He finds a spot by the bar with a view of the room and a glass of fizzy water, and he watches."
    "For a while Theo is happier than he's been in weeks. He dances. He hugs strangers. He tells Jojo he loves him."
    "Then he talks. And talks. He talks to a man by the speaker for forty minutes, and the man talks back, and neither of them is listening."
    at "Listen to that. They're both just going. Like two radios left on in empty rooms."
    "Someone says 'no way, no way' over and over. Someone laughs every few seconds, on the same note. The same three songs go round."
    "And sober, at the bar, Aron has a thought so clear it feels like cold water."
    at "This is what a room of pattern people would look like. Loops. Repeats. Nobody really there."
    at "And Theo's real. I know Theo's real. I know he's in there. He's just... nobody's listening to him. Including him."
    at "Maybe that's what a pattern is. Not a fake person. A person nobody's listening to."
    "He writes it on a napkin, in the dark, with a borrowed pen. He'll copy it into the notebook in the morning. It's the best thing he writes all year."
    "At three, Theo stops dancing. He sits down on the floor by the fire exit with his back to the wall and his hands over his chest."
    show theo worried at slightright with dissolve
    show aron worried at slightleft with dissolve
    th "Bro. Bro, my heart's going mental. It's going too fast. I can feel it in my teeth."
    a "Okay. I'm here. Look at me. Not at the room. At me."
    th "I think I'm dying. Is this dying? I feel like I'm dying."
    a "Breathe with me first. In for four. And then we're getting you checked, properly. That's not a question."
    a "In for four."
    "Theo breathes in, ragged. Aron counts it out, slowly, with his hand flat on Theo's chest so he can feel when it moves."
    a "Hold for four."
    a "Out for six. Good. Again."
    "Then Aron gets a bouncer, and the bouncer gets the first-aider, and the first-aider takes Theo's pulse and calls a cab to A and E."
    scene bg corridor with dissolve
    "They wait four hours under strip lights. Theo's heart is fast but steady, they say. He'll be fine. He needs to come down. And never do that again."
    scene bg street dusk with dissolve
    show theo sad at slightright with dissolve
    show aron tired at slightleft with dissolve
    "They walk back to Theo's flat at dawn. The sky goes from black to grey to a thin, wet pink."
    th "I'm such a mess, man. I'm thirty-one and I've got no job and I nearly had a heart attack by a fire exit."
    a "Not a heart attack. A very bad night."
    th "You're supposed to be the sick one."
    a "Turns out it's a rota."
    "Theo laughs, wetly. They walk past three birds on a wire above a bus shelter, asleep in a row."
    "Aron sits on the end of Theo's sofa until Theo is asleep, and then a bit longer, just in case. His own legs are shaking with tiredness."
    "He gets home at nine. He sleeps until five in the afternoon and wakes up feeling like he's been hit by a slow, polite bus."
    $ fog += 1
    jump ch2_speed_after

label ch2_speed_out:
    a "Theo. Come and get chips with me."
    th normal "What? Now?"
    a "Now. Birthday chips. My treat. The place on the corner. Big ones."
    th "Bro, the party's here."
    a "The party's a guy in a silver jacket selling you a bad night for your birthday. Come and get chips."
    th worried "Don't do that. Don't do the... the sensible voice. You don't get to do the sensible voice."
    th sad "You're the one who was in hospital. You're the one who did tally marks on a bread bin till four in the morning. You don't get to be the responsible one."
    "It hits him harder than the bass. It's not even wrong."
    a "I know. That's exactly why I get to. I know what the bottom looks like, Theo. I've seen the floor. I'm not letting you lie down on it."
    "Theo looks at the little folded paper in his hand for a long time. Then he looks at Jojo, laughing in the red light."
    th "...Big chips?"
    a "The biggest."
    "Theo puts the paper on the bar next to an empty glass and leaves it there. He doesn't look back at it. Aron does, once."
    scene bg street rain with dissolve
    show theo sad at slightright with dissolve
    show aron normal at slightleft with dissolve
    "The chip shop is warm and bright and smells of vinegar. They eat on the wall outside in the rain, from paper, with wooden forks."
    th "You're annoying, you know that?"
    a "I've been told."
    th "I was gonna do it. I was gonna do it and feel brilliant for six hours and then feel like death for three days."
    a "I know. I did the pill version. Or nearly did. It's a bad deal. The interest rates are criminal."
    "Theo laughs. Then he doesn't. Then he's crying, the ugly kind, with chips in his hand."
    th "I lost my job, bro. And my sister won't talk to me. And I'm thirty-one. And I keep thinking, I'm the one who's supposed to be okay."
    a "You don't have to be the one who's okay. Nobody gets that job permanently."
    "Aron puts his arm round him. They sit on the wall in the rain. A bus goes past, lit up and empty, like a fish tank on wheels."
    at "If anybody's up there nudging things, they nudged that paper into his hand tonight."
    at "Or nobody nudged anything, and my friend is just sad, and a man in a silver jacket was standing nearby."
    at "Either way, I got to be here. That part I chose."
    "He walks Theo home and sees him to his door. Theo is angry at him for most of Sunday, then sends a photo of a parsnip with the caption 'thx'."
    "Aron sleeps eleven hours. It's worth it. He knows exactly what it was worth."
    jump ch2_speed_after

label ch2_speed_after:
    stop music fadeout 2.0
    if ch2_took_speed:
        jump ch2_crash
    jump ch2_calm_after

label ch2_crash:
    scene bg mirror with fade
    play music "audio/unease.ogg" fadein 2.0
    "They let him go home at eleven, with a leaflet and a letter for his GP and an appointment with Dr. Okafor first thing Monday."
    "At home, he goes into the bathroom and looks in the mirror for the first time since the night of the rain."
    scene pov mirror with dissolve
    "His own face. Pupils still too big. Jaw aching. A sticker from the heart monitor still on his chest, curling at one corner."
    at "Hello."
    at "I know you. You're the one who told a crying woman she wasn't real."
    "He can still see her face. The yellow dress. The mascara. 'What is wrong with you?'"
    at "I thought I was being kind. I thought it was the kindest thing I'd ever said."
    at "If this is a test, I want to pass it by being kind. And the most certain I've ever been, I was cruel."
    "The crash comes in the afternoon, the way the tide comes in: not a wave, just water getting higher until there's no beach."
    scene bg bedroom night with fade
    "He sleeps for most of three days. When he's awake, everything is the colour of dishwater."
    "Nothing tastes of anything. Mira's voice is a long way off. Thinking feels like pushing a car uphill in the dark."
    show miso loaf at catspot with dissolve
    "Miso sleeps on his feet the whole time. She only gets up to eat. Mira says she's never seen her do that before."
    "On the second night, his brain offers him a thought, calm and reasonable: that this is how it will feel now. Forever. Grey, for good."
    "He knows that voice. It isn't a log. It isn't the system. It's the crash, talking in his own voice, and it's lying. He still can't stop hearing it."
    show mira worried at slightright with dissolve
    show aron sad at slightleft with dissolve
    a "Mira. I'm having the forever thoughts. That it'll always be this grey. It's loud. I'm telling you, like the plan says."
    "She doesn't panic. She's a nurse's daughter. She sits on the bed, takes his hand, and picks up her phone."
    m "Thank you for telling me. I'm going to call the crisis number. I'm telling you I'm calling. That was the deal."
    a "That was the deal."
    "A calm voice on the phone talks to both of them for half an hour. A community nurse comes in the morning. Nobody is angry. Everyone is careful."
    "The grey fades by the fourth day, like a bruise. It leaves a shape behind, though. He knows now where that floor is."
    $ fog += 1
    $ integrity += 1
    scene bg clinic with fade
    show okafor worried at slightright with dissolve
    show aron tired at slightleft with dissolve
    dr "I'm very glad you're sitting in that chair."
    a "Me too. Not just because of the heart. After, it was so grey I couldn't see the edges."
    dr neutral "The crash after amphetamines can be brutal. It can feel like the end of the world. It isn't. It's chemistry, and it passes."
    dr "You did the most important thing. You told Mira, and she called. That's the plan working."
    a "I told a woman at the club she wasn't real. She was crying. I thought I was helping."
    dr "That must be hard to remember."
    a "I keep seeing her face."
    dr "Then let it teach you something, instead of just hurting. What does it teach you?"
    "He thinks about it for a long time. In the waiting room outside, the old fish swims one slow lap of its tank."
    a "That being certain isn't the same as being right. And that being kind isn't something you get to decide on your own."
    a "You have to look at what it does to the other person."
    dr smile "That's a better lesson than most people learn from their worst night."
    dr neutral "No lecture, Aron. You know the risks better than any leaflet now. But I'll ask you one thing."
    dr "Next time the fog feels unbearable, come and tell me before you reach for something. We'll look for a door that doesn't charge interest."
    a "No next time."
    dr "I hope so. But if there is a next time, come anyway. You'll always be welcome in that chair."
    "Theo calls every day that week. He doesn't make any jokes. On the Friday, he makes one, very small, and they both hold onto it like a rope."
    jump ch2_radio

label ch2_calm_after:
    scene bg kitchen with fade
    play music "audio/morning.ogg" fadein 2.0
    show aron tired at slightleft with dissolve
    "Mira comes home on Sunday night with a hoarse voice, a BRIDE SQUAD sash and a hundred photos of women singing badly."
    show mira worried at slightright with dissolve
    m "Theo texted me. At four in the morning. One word. 'sorry.' And then nothing."
    if ch2_night_route == 2:
        a "He took something at the club. Speed. He had a bad comedown. His heart scared him. We went to A and E. He's alright."
        a "I didn't take it. I stayed with him. We did Hale's breathing by a fire exit. I walked him home."
        m surprised "You walked him home?"
        a "Sat with him till it got light. He's okay. He's embarrassed. He'll be okay."
        m worried "And you? You were up all night. With all of it right there."
        a "I was. And I'm exhausted. But I didn't."
        m sad "I spent the whole weekend thinking I'd get a call. I sang 'Total Eclipse' with my phone in my hand."
        a "I know. I'm sorry I'm a person you have to worry about."
        m neutral "No. Don't say sorry for that. You're a person I get to worry about. It's different."
    else:
        a "He nearly took something at the club. Speed. I took him for chips instead."
        m surprised "You took him for chips."
        a "Big ones. He cried on a wall. He was furious with me. Then he sent me a parsnip."
        m smile "The parsnip of forgiveness."
        a "It's the highest honour in the vegetable index."
        m worried "And you? With all that right there? On a bad week?"
        a "I wanted to. For a second. I could feel how much I wanted to. Then I looked at Theo and I wanted chips more."
        m neutral "That's... love, that's actually really big."
        a "It's chips."
        m smile "It's really big chips."
    scene bg kitchen table with dissolve
    show mira neutral at slightright
    show aron tired at slightleft
    "She sits next to him at the little table. She puts her head on his shoulder. Her hair smells of a cottage and a karaoke machine."
    m "I'm proud of you. I'm also really tired of being proud of you for surviving things. I'd like you to have a boring month."
    a "A boring month. I'll put in a request."
    at "To whom, though. That's the question. Who takes requests."
    stop music fadeout 2.0
    jump ch2_radio

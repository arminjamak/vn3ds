# Chapter 3 - "Snapshot", part 2.
# The voices come back (a relapse scare), the subway chorus, Dr. Okafor, one
# good hour, and the real Mira at the hospital bed in Snapshot 7,412.
# Continues in ch3_part3.rpy.

label ch3_voices:
    scene bg bedroom night with blackout
    play music "audio/unease.ogg" fadein 3.0
    "A week goes by like that. Smooth. Quiet. Seven mornings at 7:07."
    "Then, on the eighth night, at a time the Braun clock won't commit to, Aron wakes up because someone is talking."
    stop music fadeout 1.0
    scene pov ceiling with quick
    play sound "audio/voices.ogg"
    vox "...protected lane A-30... stable..."
    vox "...leak incidents rising... patch at dawn..."
    vox "...ORCHARD harvest window open... fidelity ninety-nine point..."
    stop sound fadeout 1.0
    "Silence. The ceiling. The crack shaped like Portugal. The fridge, two rooms away. Mira breathing beside him, slow and even."
    "His heart speeds up. Of course it does."
    at "Ah. Hello again. I was hoping you'd lost my number."
    at "I know where this went last time. The ward, the plastic cups, the doors that open only from one side. I'd rather not go back."
    at "I know what it did to her face. Mira's face, in that corridor."
    scene bg bedroom night with dissolve
    show aron worried at center with dissolve
    if fog >= 3:
        "He's so tired that the fear has to wade to reach him. It gets there anyway."
    "He sits on the edge of the bed in the dark and holds his own hands, because nobody else is holding them."
    at "Dr. Okafor said: if they come back, it isn't a failure. It's information. A warning light on the dashboard."
    at "A warning light. Okay. I can look at a warning light."
    at "Or I can look at what it said. 'Protected.' 'Lane.' 'Leak.' The same words as the café. The same words as the tannoy."

    menu:
        at "What do I do, right now?"

        "Wake Mira. Don't do this alone":
            $ p_govern += 1
            $ bond += 1
            jump ch3_voices_mira

        "Write the words down. Decode them":
            $ p_govern -= 1
            $ clarity += 1
            $ fog += 1
            jump ch3_voices_decode

        "Find the old stimulants. Think clearly":
            $ risky += 1
            $ p_rest -= 1
            $ clarity += 1
            $ ch3_pill = True
            jump ch3_voices_pill

label ch3_voices_mira:
    a "Mira."
    "Nothing."
    a "Mira. I'm sorry. I need you."
    show aron at slightleft with move
    show mira worried at slightright with dissolve
    m "Mm. Mm? What's wrong. What time is it?"
    a "I don't know. The clock won't say."
    a worried "They're back. The voices. Just now. Three sentences."
    "She's awake all at once, the way only nurses' daughters wake. Already sitting up. Already holding his wrist."
    m "Okay. Okay. Thank you for waking me. That's the most important thing you could have done."
    m neutral "Are they talking now?"
    a "No. It stopped."
    m "Are they telling you to do anything?"
    a "No. They're not even talking to me. It's like... overhearing a phone call in a train."
    m "Okay. That's good. That's the better kind. Breathe with me. In for four."
    "He breathes in for four."
    m "Hold."
    "He holds."
    m "Out for six. Slow. Like you're blowing on soup."
    a "Soup."
    m smile "Soup. You love soup."
    "They do it ten times. Her hand stays on his wrist the whole time, counting something he can't see."
    m neutral "Early warning signs. We wrote the list, remember? Sleep's on it. Voices are on it."
    m "First thing in the morning, we call Dr. Okafor. Not 'see how it goes'. We call."
    a "We call."
    m "And tonight you're not going to sit up decoding anything. You're going to lie here and be bored with me."
    a tired "I'm very good at being bored."
    m smile "You're a world champion."
    scene pov ceiling with dissolve
    "He lies down. She tucks herself against his back like a comma."
    at "She knew exactly what to do. Every step. The breathing, the list, the call."
    at "It's what the real Mira would do. It's what anyone who loved me and knew hospitals would do."
    at "If it's a script, it's a good script. I'll take a good script at four in the morning."
    "He doesn't sleep. But he doesn't get up, either."
    jump ch3_subway

label ch3_voices_decode:
    "He takes the notebook into the kitchen without turning on the light. Then he turns on the light, because he's not a monster."
    scene bg kitchen night with dissolve
    show aron tired at center with dissolve
    "He writes it all down before it fades. Word for word, as close as he can."
    scene cg notebook with dissolve
    "PROTECTED LANE A-30. STABLE. LEAK INCIDENTS RISING. PATCH AT DAWN. ORCHARD HARVEST WINDOW OPEN. FIDELITY 99."
    at "A-30. I'm thirty. A for Aron. That's me. Or that's my brain making a label out of my birthday."
    at "Protected. Lane. Like a swimming pool. Like a motorway. A lane is a way through something, kept separate from the others."
    at "Leak. Something getting out. Patch. Someone fixing it."
    at "If I'm in a lane, where are the other lanes? Who's in those?"
    "He draws boxes. Arrows. A row of long boxes side by side, like a swimming pool from above. One box off to the side, on its own, with a little stick man inside."
    "He looks at the stick man for a long time."
    scene bg kitchen night with dissolve
    show aron tired at center with dissolve
    "Outside the window the sky is going grey. The wire is empty. The bird is not due yet."
    "His hands are cold. His eyes feel sanded."
    "The oven clock says 6:58. Then, a long time later, 7:07. The bird drops onto the wire."
    scene bg kitchen with dissolve
    show aron tired at slightleft
    show mira worried at slightright
    with dissolve
    m "Aron?"
    m "Have you been up all night?"
    a "I heard them again. The voices. But Mira, they said 'lane', and 'leak', and I think..."
    m sad "Stop. Please stop for a second."
    m "You heard voices, and you didn't wake me. You sat in the kitchen with them. Alone. All night."
    a tired "I didn't want to scare you."
    m "I'm scared now. I'm much more scared now than if you'd woken me up."
    "She takes the notebook gently out of his hands. Closes it. Puts it face down on the counter."
    m neutral "We're calling Dr. Okafor. Right now. Then you can tell me about lanes."
    at "She's right. I know she's right. I knew it at three in the morning and I sat here anyway."
    at "Every time, I think I'm protecting her by doing it alone. Every time, alone is the thing that frightens her most."
    jump ch3_subway

label ch3_voices_pill:
    "There's a drawer in the bathroom. In the drawer, behind the plasters, there's a bottle he kept from before. He tells himself he forgot it."
    scene bg mirror with dissolve
    show aron tired at center with dissolve
    "A tired man in a bathroom mirror, with a pill in his hand."
    scene pov mirror with quick
    "He looks at himself. Properly. The grey under the eyes. The stubble. The face of someone who has been very patient for a very long time."
    at "Just to think clearly. Just for one night. Just to understand what they said before it fades."
    at "I've said 'just' a lot of times in my life. It's never once been true."
    "He takes it anyway."
    "For a while, nothing. Then, like a curtain going up, everything."
    at "Protected. Lane. Leak. Patch."
    at "If I'm in a lane, there are other lanes. Side by side. And I've been put in one on my own."
    at "That's why everything loops. That's why they freeze. There's nobody else in here to make it move."
    "It's so clear it's like a bell. He laughs out loud in the bathroom at three in the morning."
    "Then the bell keeps ringing."
    "His heart is going too fast. His jaw is tight. The tap is dripping and every drip is a word he almost understands."
    "In the mirror, behind his reflection, on the shower rail: three small birds. Evenly spaced."
    "He spins round. The rail is empty."
    scene bg bedroom door with quick
    show aron worried at slightleft with dissolve
    "He goes back to the bedroom and stands in the doorway, and looks at Mira asleep."
    "She's so still. So perfectly still."
    at "Is she breathing? Is that breathing, or is that an impression of breathing?"
    at "If I touched her, would she be warm? Would she be the right warm?"
    "He stands there for a long time. He realises his fists are clenched. He realises he's afraid of the woman he loves."
    "He realises how he would look to her, if she opened her eyes now. A grey, shaking man in the doorway, staring."
    "He goes into the kitchen and sits on the floor with his back against the cupboard, and stays there."
    scene bg kitchen with blackout
    show aron tired at slightleft with dissolve
    "The crash comes after sunrise. It feels like someone pulled the plug at the bottom of him and everything drained."
    "He's shaking. He's cold. He can't remember the bell at all. He can only remember the doorway."
    show mira worried at slightright with dissolve
    m "Aron? Oh god. Aron, what happened? Are you hurt?"
    a "I took one of the old ones. From the drawer. I'm sorry. I'm so sorry."
    m sad "..."
    "She doesn't shout. That's worse. She kneels down on the kitchen floor in her pyjamas and takes his face in her hands."
    m "Look at me. Are you safe right now? Do you need an ambulance?"
    a "No. No. Just... crashing. My heart's slowing down. It's slowing."
    m "Okay. Water. Then we're calling Dr. Okafor. And then I'm flushing that bottle while you watch."
    a tired "Yes. All of it. Yes."
    at "I understood something last night. I'm sure I did. And all I've got left of it is the doorway."
    at "And her face, now. That's what it cost. It always costs her face."
    jump ch3_subway

# ---------------------------------------------------------------------------
# On the way to the clinic: the subway chorus
# ---------------------------------------------------------------------------
label ch3_subway:
    scene bg subway with fade
    play music "audio/unease.ogg" fadein 2.0
    "Dr. Okafor can see him at eleven. Mira takes the morning off. They take the underground, four stops."
    show aron tired at slightleft with dissolve
    show mira neutral at slightright with dissolve
    "The carriage is half full. Commuters. A man with a bicycle. A woman knitting something long and green. A child asleep on a suitcase."
    "The train rocks. The lights flicker in the tunnel, the ordinary way, the way tunnel lights do."
    m "You okay?"
    a "I'm okay. I'm tired. I'm okay."
    "The train slows between stations. Stops. The tunnel hums."
    "And then every passenger in the carriage looks up at once."
    "The man with the bicycle. The knitting woman. A businessman with a newspaper. The child, waking up on the suitcase."
    "They don't look at Aron. They look straight ahead, at nothing, and they speak together, in one calm, ordinary voice."
    ch3_crowd "If this is a test, I want to pass it by being kind."
    a awe "..."
    "The first line of his notebook. Word for word. Twenty voices. One breath."
    "Then they stop. Mid-gesture. The knitting needles hang crossed in the air. The newspaper is half-turned. The child's mouth is open on a yawn."
    "Nobody blinks. Nothing moves. Only the tunnel hum, and his own heart."
    "One second. Two. Three."
    "The train lurches forward. The needles click. The newspaper turns. The child finishes the yawn."
    a worried "Mira. Mira, did you hear that?"
    m neutral "Hear what, love?"
    a "All of them. They said... they all said my line. From the notebook. Together. And then they stopped."
    "She looks around the carriage. The knitting woman smiles at her. The businessman frowns at his crossword."
    m worried "Nobody said anything, Aron. The train stopped in the tunnel for a minute. That's all."
    m "Are you hearing things now? Right now?"
    a "..."
    a tired "No. Not now."
    "She takes his hand and holds it in her lap for the last two stops, and doesn't let go."
    at "She didn't hear it. Nobody reacted. The kind of thing that happens only to me."
    at "That's what a symptom is. That's the textbook. Okafor could draw it on a whiteboard."
    at "And it's also exactly what I'd expect if a world made of copies started copying the one real thing in it."
    at "Two explanations. Both fit. They've both fit for a year. It's maddening, in a purely technical sense."
    stop music fadeout 2.0
    jump ch3_clinic

# ---------------------------------------------------------------------------
# The clinic
# ---------------------------------------------------------------------------
label ch3_clinic:
    scene bg clinic with fade
    play music "audio/ward.ogg" fadein 2.0
    show okafor neutral at slightright with dissolve
    show aron tired at slightleft with dissolve
    dr "Come in, Aron. Sit wherever feels least like a dentist's."
    "Dr. Okafor's room is the same as always. The plant that is somehow always the same height. The box of tissues angled toward the patient's chair."
    dr "Mira told me on the phone. Voices, a bad night. I'm glad you came in the same day. That was the right call."
    a "It was Mira's call."
    dr smile "Then it was a good call with your name on the appointment. That counts."
    dr neutral "Tell me what you heard. As close to the words as you can."
    a "Numbers. Words. 'Protected lane A-30.' 'Leak incidents rising.' Something called 'Orchard'."
    a "It wasn't talking to me. It was like overhearing a radio in another room."
    a "And on the train just now, everyone in the carriage said the first line of my notebook. Together. Mira didn't hear it."
    dr "Any commands? Anything telling you to hurt yourself, or anyone else?"
    a "No. Nothing like that."
    dr "Good. That matters, and I want you to hear me say it matters."
    "Behind Dr. Okafor, on the curtain rail above the window, three small birds are sitting. Evenly spaced. Inside the room."
    a worried "..."
    a "Dr. Okafor. Behind you. On the rail."
    "Okafor turns, unhurried, and looks."
    dr neutral "What do you see there, Aron?"
    a "Three birds. Sitting on your curtain rail."
    "Okafor looks for a long, honest moment. Then turns back."
    dr "I don't see them. But I believe that you do. Are they still there?"
    "He looks. The rail is empty. The curtain stirs a little, in a draught from nowhere."
    a "...No. They're gone."
    dr "Okay. Thank you for telling me. That's exactly what I need you to do. Tell me, and not keep it."
    if ch3_pill:
        dr worried "Mira said you took one of your old stimulant tablets last night."
        a worried "I did. I'm sorry."
        dr neutral "You don't owe me an apology. You owe yourself an honest look at what it did."
        dr "What did it give you?"
        a "Clarity. For about an hour. Then I stood in the doorway and was afraid of Mira."
        dr "And then?"
        a tired "Then I was on the kitchen floor and I couldn't remember the clarity. Only the doorway."
        dr "That's the trade, isn't it. It lends you something and charges interest on it the same night."
        dr "We'll talk about that bottle properly. Not today. Today we keep you steady."
    "Dr. Okafor writes something down. Then looks up, and smiles a little."
    dr smile "You know what I notice? You came in. You're sitting in the chair. You're telling me the words."
    dr "Six months ago you'd have been on the wall with a marker."
    a "I still have the marker."
    dr "Keep it. Use it for shopping lists."
    "It's exactly what Dr. Okafor would say. It's exactly what's on the leaflet in the waiting room. Early warning signs. Act early. You are not your symptoms."
    at "Maybe Okafor's reading it off a card. Maybe the card's built in. Maybe Okafor wrote the card."
    at "It doesn't matter. Even if it's a script, it's a good script. It's working on me."
    dr neutral "So. We have some options, and I'm going to be honest about each of them."
    dr "One: we keep your dose where it is and we guard your sleep like it's the crown jewels. No late nights, no notebooks after ten."
    dr "Two: we raise it for a few weeks. You'd be safer. You'd also be more tired. I won't pretend otherwise."
    dr "And I know you're going to ask about three, so: I won't lower it today. Not with voices back."
    dr "But I'll tell you exactly why, and when we can talk about it again."

    menu:
        dr "What feels right to you?"

        "Keep the dose. Guard my sleep":
            $ p_rest += 1
            $ integrity += 1
            a normal "Keep it. And I'll guard the sleep. Properly. Lights out at ten, notebook in the drawer."
            dr smile "Then that's the plan. You'll get a text from me on Friday asking how it's going. Answer it honestly."
            a "I'll answer it honestly. Even if the answer's 'badly'."
            dr "'Badly' is a perfectly good answer. It's the silence I worry about."
            at "Rest as a method. Not a surrender. A way of keeping the lab open."

        "Raise it. I'm scared":
            $ fog += 1
            $ bond += 1
            a worried "Raise it. Please. I can't do the ward again. I can't do that to Mira again."
            dr neutral "Then we raise it a little, for a few weeks, and we look again."
            dr "You'll feel it. The tiredness will be heavier. Give yourself permission to be slow."
            a tired "I've got a lot of practice being slow."
            dr smile "Then you're well qualified."
            at "Heavier. Slower. Safer. And somewhere a voice said 'protected lane'. Protected from what? From me?"
            at "I don't care. I'd rather be slow and here than fast and gone."

        "Lower it. I need my head clear":
            $ clarity += 1
            $ p_rest -= 1
            a worried "I know you said no. But I need my head. I can feel things just out of reach and the pills put a wall in front of them."
            dr neutral "I hear that. I hear it from a lot of brilliant people, and it's real. The medication costs you something."
            dr "But right now, with voices back and a night without sleep, lowering it would be like taking the railings off a staircase in the dark."
            dr "Give me four steady weeks. Then come in and argue with me. I like being argued with. I'll listen."
            a "Four weeks."
            dr smile "Four weeks. Write it on the wall with the marker if you want."
            at "A no. An honest one, with the reasons attached. That's more than the voices ever gave me."

    dr neutral "One more thing, Aron. Not as your doctor. As someone who's sat in this chair across from you for a while."
    dr "Whatever is or isn't going on out there, you don't have to solve it alone, and you don't have to solve it this week."
    a "How do you know there's an 'out there'?"
    dr "I don't. That's why I said 'whatever'."
    dr smile "Same time next month."
    scene bg corridor with dissolve
    show aron normal at slightleft with dissolve
    show nurse smile at slightright with dissolve
    "In the corridor, Nurse Hale is restocking a trolley with paper cups. She's on loan to outpatients this month. She looks up and grins."
    nu "Aron! Look at you. Clothes with buttons. Shoes with laces."
    a smile "Hello, Nurse Hale. I'm only visiting."
    nu "Then that's the bit that worked. Don't come back. I mean that in the nicest possible way."
    a normal "..."
    "She said that on the day he was discharged. Exactly that. The same words, the same little nod on 'nicest'."
    at "People have phrases. Nurses have a hundred patients and one good goodbye. Of course she reuses it."
    at "But the nod. The same nod."
    nu neutral "You alright, love? You've gone a bit far away."
    a "Sorry. Just... you said that to me before. Word for word."
    nu smile "Did I? Well. It's a good line. I'd say it to you every day if it kept you out of here."
    "She goes back to her cups. He watches her stack them, perfectly, in towers of ten."
    stop music fadeout 2.0
    jump ch3_good_hour

# ---------------------------------------------------------------------------
# One good hour
# ---------------------------------------------------------------------------
label ch3_good_hour:
    scene bg room with fade
    play music "audio/morning.ogg" fadein 2.0
    show aron normal at slightleft with dissolve
    "The days after are slow. Lights out at ten. The notebook in the drawer at night."
    "On Friday, as promised, a text from Dr. Okafor: How's it going? Honest answer please."
    if fog >= 3:
        "He types 'fine', deletes it, and types: Heavy. Sleeping a lot. No voices since. Sad that I'm so slow. Still here."
    else:
        "He types 'fine', deletes it, and types: Tired. Sleeping. No voices since. Bit scared they'll come back. Still here."
    "The reply comes in a minute: Still here is the headline. Thank you for the honest answer. Same time next month."
    show miso sit at catspot with dissolve
    "Miso arrives on the sofa arm the way she always does, as if she's been called to a meeting."
    a "Miso. Since you're here. I've revised the model."
    a "Old model: the world is being generated around me. New model: the world is being generated around me, and it's leaking."
    a "Look at the evidence. The café said 'protected'. The bus driver said 'subject'. The tannoy said my number. A whole train said my notebook."
    a "Birds on Okafor's curtain rail. Birds in the bathroom mirror. Three, always three. Inside."
    show miso stare at catspot
    a "So here's the mechanism. If everyone around me is a copy, a pattern, then they're soft. And soft things take an impression."
    a "My thoughts press into them. My words come out of their mouths. My birds get into their rooms. I'm the only hard thing in a world of clay."
    a "Which would mean the worse I get, the stranger the world gets. And the stranger it gets, the worse I get. A feedback loop. Very elegant. Horrible."
    a worried "Or it means I'm ill, and that's exactly what being ill feels like from the inside. Which is also very elegant. Also horrible."
    a normal "And you, Miso. If you're clay. If you're a cat-shaped impression of a cat. Does that change anything?"
    a "I've decided it doesn't. I still have to buy the expensive food. You still sit on my notebook. I still love you. Those are the terms."
    show miso meow at catspot
    cat "Meow."
    scene bg kitchen table with dissolve
    show aron normal at center with dissolve
    "Most days he gets one good hour. Usually it comes in the afternoon, around three, like a bus that runs once a day."
    "Today it's arrived. He can feel it: the fog thinning, the edges of things getting sharp."
    "His phone buzzes."
    th "u around? fancy a walk. or a pint. or just standing somewhere that isn't my flat"
    th "need to get out of my head for an hr"
    "The notebook is on the table. The lanes are on the last page, in boxes, with the little stick man on his own."
    at "One good hour. I could work. I've got questions I haven't been able to think about in days."
    at "Or I could spend it on Theo."

    menu:
        at "One hour. Where does it go?"

        "Go and meet Theo":
            $ p_share += 1
            $ bond += 1
            $ ch3_theo_hour = True
            jump ch3_hour_theo

        "Text 'tomorrow?' and use the hour":
            $ p_share -= 1
            $ clarity += 1
            jump ch3_hour_work

label ch3_hour_theo:
    a "on my way. park bench in 10"
    scene bg park autumn with dissolve
    show theo normal at slightright with dissolve
    show aron smile at slightleft with dissolve
    "The park has gone gold and copper while he wasn't looking. Leaves on the path. A smell of smoke from somewhere."
    th "You came! Look at you. Mobile. Upright."
    a grin "I'm told I have about fifty-eight minutes left of upright. Let's not waste it on small talk."
    th grin "Small talk is my only skill, mate."
    "They walk. The boy with the kite is there again, shouting at the sky. Aron decides not to count it."
    th normal "I'm not sleeping."
    a "How long?"
    th "Properly? Couple of weeks. I lie there and my brain's like a radio between stations."
    th "So I've been... helping it along a bit. In the daytime. To get through work. The studio wants me bright at nine, making door noises."
    "He doesn't say with what. He doesn't have to. Aron knows the look. He's worn it."
    a worried "Theo."
    th worried "I know. I know, alright? I know who I'm saying this to."
    th "You had a rough few months and I was there, and I was the one who..."
    "He stops. Kicks at the leaves."
    if risky >= 2:
        th sad "I was the one who brought the stuff. Half the time. When you were looking for your answers. I thought I was helping."
        th "And then I watched what it did to you, and I kept doing it myself anyway. What does that make me?"
    else:
        th sad "I watched what that stuff did to you. Up and then down, every time. And I'm doing it anyway. What does that make me?"
    a normal "It makes you tired. It makes you a person who's tired and scared and trying to keep going."
    a "It doesn't make you bad."
    th "..."
    th normal "You're being very wise for a man with fifty minutes of upright."
    a grin "Forty-four. I'm counting."
    th grin "Ha."
    "They sit on a bench. Theo's knee is bouncing. Aron puts a hand on it, the way Mira does to his wrist."
    a "Will you talk to someone? Not me. Someone with a diploma."
    th normal "Maybe. Yeah. Maybe."
    th "Thanks for coming, man. I know what an hour costs you."
    a "It's the best way I've spent one in weeks."
    scene pov sky with dissolve
    "When the hour runs out, it runs out like a tap closing. He sits on the bench a while longer with his head back, watching the leaves come down."
    "He goes home and sleeps until dinner. He doesn't regret a minute."
    jump ch3_hour_after

label ch3_hour_work:
    a "rough day here, can we do tomorrow? 3pm? promise"
    "A pause. The three dots appear. Disappear. Appear."
    th "yeah no worries bro"
    th "all good"
    at "All good. Okay. He's fine. He said so."
    scene bg desk with dissolve
    show aron normal at center with dissolve
    "He opens the notebook. One good hour. He is going to use every minute."
    "He searches the internet for 'protected lane'. Swimming pools. Bus lanes. A road safety campaign."
    "He searches again a minute later. The same results, in the same order, with the same typo in the third one."
    scene pov hands with quick
    "He searches from his phone instead of the laptop. Same results. Same typo."
    at "That's not strange on its own. Search engines cache things."
    at "But the typo. The same typo. On two devices, a minute apart."
    "He searches for 'Orchard'. Apple orchards. A furniture shop. A film."
    "Then, at the bottom of the second page, a result with no title. Just a line of grey text."
    "ORCHARD intake: delta received from lane A-30."
    "He taps it. The page doesn't load. He refreshes. The result is gone."
    scene bg desk with dissolve
    show aron awe at center with dissolve
    "He writes it down, quickly. His handwriting is getting worse. The hour is getting shorter."
    at "Orchard is real. Or the word is real. Or my eyes are tired and I want things to be real."
    "When the hour runs out, it runs out like a tap closing. He sleeps until dinner."
    "When he wakes there's one more message from Theo, sent at 4:12."
    th "nvm. all good"
    at "All good. Twice. That's what he said."
    at "Theo never says anything twice. That's my job."
    jump ch3_hour_after

label ch3_hour_after:
    stop music fadeout 2.0
    jump ch3_cut_real_mira

# ---------------------------------------------------------------------------
# CUT 3: Snapshot 7,412 goes on without him
# ---------------------------------------------------------------------------
label ch3_cut_real_mira:
    scene cg static with flash
    pause 0.3
    scene black with fade
    play music "audio/entities.ogg" fadein 2.0
    sysmsg "SNAPSHOT 7,412. Coalition lane, shared data. Status: running. Subject A-30: absent. Vessel: maintained."
    stop music fadeout 2.0
    scene bg coma with slowfade
    play music "audio/ward.ogg" fadein 2.0
    "A hospital room. Not the ward he knew. A quieter one, where the machines do most of the talking."
    "A man lies in the bed. His face is Aron's face, thinner. His eyes are closed. A monitor draws small green hills across a screen."
    "Beside the bed, an empty chair. A teal scarf hangs over the back of it, where someone left it to keep the seat."
    "He has been lying here since the night the ambulance brought him in. Months now. He never saw a ward. He never met a Dr. Okafor."
    show mira sad at slightleft with dissolve
    "The door opens. A woman with red hair and freckles comes in with a paper cup, and drops into the chair, and puts the scarf round her neck."
    "She looks like she hasn't slept properly in months. Because she hasn't."
    m "Morning, idiot."
    m "It's Thursday. It's raining. The coffee machine downstairs has been broken since Tuesday and I've decided it's personal."
    show nurse smile at slightright with dissolve
    "Nurse Hale comes in behind her with a chart. Hale works the fourth floor here. In this world, she has never once seen Aron awake."
    nu "Morning, Mira. Did you go home at all last night?"
    m neutral "I went home. I fed Miso. I showered. I came back. That counts as going home."
    nu "That counts as a shower."
    m smile "I'm a nurse's daughter. I know exactly what these chairs do to your back. I'm staying anyway."
    nu "His numbers are good. Brain activity's busy. Very busy, actually. Like he's dreaming the whole time."
    m "The consultant said there's no reason. No injury. No bleed. He was talking in the ambulance. Talking about birds. And then he just... went."
    m sad "I had his hand. I had his hand the whole way. And somewhere between our street and this building, he let go of me without letting go."
    nu "I know, love."
    nu "Talk to him. They hear more than we think."
    hide nurse with dissolve
    m neutral "..."
    "She reaches into her bag and takes out a notebook. Worn at the corners. His handwriting on the cover."
    m "I read it. All of it. I'm sorry. I know it was private."
    m "The first line. 'If this is a test, I want to pass it by being kind.'"
    m sad "You absolute softie. You absolute idiot."
    m "And the last page. The night we called the ambulance. Birds and clocks and arrows. The pen goes right through the paper in places."
    m neutral "I've been doing what you did. Writing things down."
    m "The birds on the wire outside this window. Always three. Mrs. Varga says the same thing about the weather every single day."
    m worried "I'm starting to see it, Aron. Or I'm starting to go where you went. I can't tell which."
    m "Is that what it was like? Not knowing if you're seeing it or losing it?"
    "The monitor draws its small green hills."
    m sad "You told me about the lighthouse. Didn't you? At the bottom of the glass stairs. You must have told me. How else would I know?"
    scene cg hands with dis
    "She takes his hand. It's warm. It's the right warm. It doesn't hold back."
    m "Okay. Here's the deal. If you're somewhere. If you can hear me, even a bit."
    m "Do the thing. From the dream. Flicker something."
    "Nothing."
    m "Yeah. No. That was stupid. I'm talking to a lamp."
    scene cg flicker with dissolve
    "The light above the bed flickers."
    "Once."
    "Twice."
    "Three times."
    scene bg coma with dissolve
    show mira surprised at slightleft with dissolve
    m "..."
    "She doesn't scream. She doesn't call for the nurse. She sits very still, holding his hand, and stares at the light."
    m "Okay."
    m "Okay. I heard that."
    "The door opens. A curly-haired man backs in through it with two coffees and a paper bag, holding the door with his heel."
    show theo normal at slightright with dissolve
    th "Morning. I brought the bad coffee from the place across the road, because the machine here is broken, because of course it is."
    th worried "...Mira? What's wrong? You look like you've seen a ghost."
    m "The light. Over his bed. It flickered."
    th normal "It's a hospital, Mira. Half the lights in here flicker. I've reported three of them."
    m "Three times, Theo. It flickered three times. Right after I asked him to."
    th "..."
    "Theo puts the coffees down very carefully on the windowsill. He looks at the light. He looks at his friend in the bed."
    th worried "He used to go on about that. The three. Birds, flickers, the clock. I always told him he was reading tea leaves."
    th sad "I keep coming in here and making jokes at him. Every day. Terrible ones. I think he'd hate it if I stopped."
    th "And then I go home and I don't sleep. I lie there and think, I was in the ambulance. I had his feet. I should have kept him talking."
    m sad "You couldn't have."
    th "You don't know that."
    m neutral "No. I don't. Nobody knows anything. That's the whole problem with this year."
    "She holds out her free hand without looking. After a moment Theo takes it. The three of them stay like that for a while, a chain of hands."
    th "Hey, Aron. If you did that light... bro, the universe doesn't run on your schedule. But nice timing."
    "Mira laughs. It comes out wet. It's the first time she's laughed in this room."
    m "I'm not going anywhere."
    stop music fadeout 1.0
    scene bg command with fade
    play music "audio/entities.ogg" fadein 1.0
    sysmsg "SNAPSHOT 7,412: agent M. (conscious). Search behaviour: rising. Pattern recognition: unexpectedly strong."
    sysmsg "SNAPSHOT 7,412: unregistered light event at vessel A-30. Three pulses. Signature matches roof event in protected lane."
    sysmsg "Note: a signal crossing between a coalition lane and protection should not be possible."
    sysmsg "Flag forwarded to: Commander, Angel Corps. Inquiry already open."
    stop music fadeout 2.0
    jump ch3_fight


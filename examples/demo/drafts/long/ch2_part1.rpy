# Snapshot - Chapter 2: "Fog" (part 1 of 6)
# Already in the protected world (since the ambulance at the end of ch1).
# The closed unit: restraint and seclusion, the first ordinary night,
# Dr. Okafor, the diagnosis, the Council arguing over the protection,
# the medication, group therapy. Continues in ch2_part2.rpy.

# One-off characters for chapter 2. The voices use `vox` from common.rpy.
define ch2_lou = Character("Lou", color="#d9c7a3")
define ch2_ines = Character("Ines", color="#e6a8d7")
define ch2_vesk = Character("Lady Vesk", color="#d46a9f")
define ch2_corran = Character("Old Corran", color="#c4a27a")
define ch2_varga = Character("Mrs. Varga", color="#e3c9b0")
define ch2_moth = Character("Moth", color="#e8d9b0")
define ch2_jojo = Character("Jojo", color="#c0c0ff")
define ch2_girl = Character("Woman", color="#d0d0d0")
define ch2_staff = Character("Nurse", color="#9fd4e6")
define ch2_driver = Character("Driver", color="#d0d0d0")
define ch2_tv = Character("Television", color="#bbbbbb")
define ch2_table = Character("Next table", color="#c8c8c8")
define ch2_bouncer = Character("Doorman", color="#c0c0c0")

default ch2_lou_met = False

label chapter2:
    $ chapter = 2
    stop music fadeout 1.0
    scene black with blackout
    centered "Chapter 2\n\nFog"
    jump ch2_admission

label ch2_admission:
    scene black
    "Doors. Double doors, and then another pair, and a buzz, and a click, and another pair."
    "His eyes won't open properly. The world comes in slices, through lashes, like light through blinds."
    play sound "audio/voices.ogg"
    sysmsg "...subject A-30 delivered. Closed unit. Protection holding. Seam settling..."
    stop sound fadeout 0.8
    scene bg corridor with flash
    play music "audio/unease.ogg" fadein 1.0
    "A corridor, very bright. Someone has a hand under each of his elbows, kindly. He's walking. He thinks he's walking."
    at "Okay. Hospital. That's fine. That's reasonable. I'd bring me to hospital too."
    at "Note for later: the floor is doing something interesting."
    "The floor is doing something interesting. Every tile arrives a fraction of a second after he looks at it, like a web page loading in a tunnel."
    "The nurse on his left says something. Her mouth moves. The words arrive late, and wrong, in a flat voice that isn't hers."
    sysmsg "...re-rendering corridor... hold position..."
    a "Sorry. Could you say that again? I think the sound's out of sync."
    "At the end of the corridor there's a door with a small square window. Through it he can see more corridor, open, going on."
    "So he walks towards it, politely, to see where it goes. And walks into the glass, quite hard, with his forehead."
    "It doesn't feel like glass. It feels like the edge of a picture. He steps back, puzzled, and tries again, because the corridor is right there."
    ch2_staff "Aron! Aron, stop, love, you'll hurt yourself!"
    "The floor tilts, sideways and down, like a lift dropping a floor without anybody pressing a button. He grabs for something. A wrist."
    "Someone makes a small sound of pain. He lets go at once."
    a "Sorry. Sorry! I'm so sorry. The floor moved. Did you see the floor move? Is it just me?"
    "Nobody answers in a voice he can hear. They answer in logs. Their mouths move and the words come out as numbers."
    "He tries the door again. He can't help it. It's right there. The corridor is right there."
    scene pov restraint with vpunch
    "And then he's on his back."
    "A light directly overhead, white and humming, so bright it has a halo. Faces at the edges of it, blurred, leaning in."
    "Something across his wrists. Something across his ankles. A strap across the bottom of his vision, wide and grey, with a buckle."
    nu "Aron. Aron, my name's Hale. I'm here. I'm right here by your head."
    "A woman's voice, very close, very calm, and in sync. The first voice in ten minutes that arrives at the same time as its mouth."
    nu "You're in hospital. You're safe. We're holding you because you kept hurting yourself on that door. You're not in trouble."
    a "I wasn't trying to... the corridor kept going. On the other side. I just wanted to see."
    nu "I know. You can see it tomorrow. You're staying right here with me tonight."
    play sound "audio/voices.ogg"
    se "...the seam's disoriented him. Of course it has. Keep his lane quiet..."
    sysmsg "...protected lane stable. No feedback to the coalition..."
    stop sound fadeout 0.8
    "A gloved hand comes into the light. Blue nitrile. It rests on his shoulder for a moment, the way you'd steady a ladder."
    nu "Aron, the doctor's going to give you an injection now. In your leg. It's going to help you calm down and rest."
    nu "It'll be a sharp scratch. I'm sorry. I know you don't want it. We've tried everything else, love."
    a "I'm quite calm, actually. It's the room that isn't."
    nu "I believe you. Keep listening to my voice. Just my voice."
    "A sharp scratch in his thigh. A cold bloom spreading out from it, slow, like ink in water."
    "He doesn't fight the straps. He tests them, once, the way you'd test a seatbelt. They hold, patiently, and so does the hand on his shoulder."
    play sound "audio/voices.ogg"
    se "...the sedation helps. The seam's quieter now..."
    dro "...his breathing's his own. Don't touch it. It's the only thing in here that is..."
    pi "...'you're safe, Aron'. Wait. That's not in her pattern. Who gave her that line?..."
    stop sound fadeout 1.0
    nu "That's it. That's it. You're doing really well. Breathe out for me."
    "He breathes out. The light over his head swims. The tiles of the ceiling, one by one, stop loading and simply are."
    at "Note for later. Very important. Remember the floor."
    nu "I'm going to stay with you. You're not on your own. Aron. Aron, you're not on your own."
    "The last thing he sees is the strap at the bottom of his vision, grey, with its buckle, and somebody's gloved fingers checking it isn't too tight."
    stop music fadeout 2.0
    scene black with slowfade
    pause 0.5
    scene bg barracks with dissolve
    play music "audio/entities.ogg" fadein 1.0
    show seraph stern at center, fadein
    se "Status."
    sysmsg "Subject A-30 sedated. Protected lane stable. Coalition data clean. Throttle and local medication in agreement."
    se "The episode in the corridor. That was us."
    sysmsg "Transfer seam, settling. The corridor re-rendered while he was in it. Local staff patterns read it as a psychotic episode."
    se concerned "So we shifted the floor under him, and the people he trusts strapped him down for walking into a wall we moved."
    sysmsg "Correct. The local explanation is stable. Diagnosis is likely."
    se "And the nurse's line. 'You're safe.'"
    sysmsg "Unattributed. Probability within the pattern: low. Logged as noise."
    se "Noise."
    se concerned "We took him out of his own world on a stretcher with his eyes half open. The least we can do is let him sleep through his first night."
    sysmsg "Sleep is recommended. Sleep keeps a lane inert."
    se stern "Then let him sleep. And log the noise. All of it."
    stop music fadeout 1.5
    jump ch2_isolation

label ch2_isolation:
    scene bg isolation with fade
    play music "audio/ward.ogg" fadein 3.0
    "When he wakes, the light is grey instead of white, and he doesn't know how many hours have passed. It feels like a lot of them."
    "A small room. A bed with straps folded at its sides, unbuckled now. A door with a square window in it, at head height."
    scene pov ceiling with dissolve
    "He lies on his back and looks at the ceiling. Twelve tiles. One of them has a water stain shaped like nothing at all."
    at "I'm still here. Wherever here is."
    at "In the ambulance. Something moved. Like a lift going down a floor without anybody pressing the button."
    at "Or I was sedated in an ambulance and my stomach did a thing. That's what lifts are. Stomachs doing things."
    at "My head hurts. My forehead. The door. I hit the door."
    "His mouth tastes of metal and cotton wool. His arms are heavy, as if somebody has filled them with sand while he slept."
    scene bg isolation with dissolve
    "At the square window, a face appears. Looks in. Goes. A minute later, it's back. Every quarter of an hour, all through the grey."
    "On the fourth time, the door opens."
    show nurse neutral at slightright with dissolve
    nu "Hello again. You won't remember me. I'm Hale. I was there last night."
    show aron ward tired at slightleft with dissolve
    a "You were the voice."
    nu "I was the voice."
    a "You kept saying my name."
    nu "I did. It's the most important word I know about you so far."
    "She has a plastic cup of water with a lid on it, like a toddler's, and a lanyard with a cartoon hedgehog on it."
    at "Nobody would design a hedgehog lanyard for a simulation."
    at "Unless they wanted it to look like nobody would."
    nu "Can you sit up? Slowly. You'll feel heavy. That's the injection, still in your system. It'll ease through the day."
    "He sits up. It takes a long time. She waits for it, the way you wait for a kettle."
    a "Did I hurt someone? I remember a wrist. Someone made a sound."
    nu "Kemi's got a bruised wrist. She asked me to tell you she's fine and she's had worse from a toddler at a birthday party."
    a "I'm sorry. God. I'm so sorry."
    nu "She knows. We all know you weren't trying to hurt anybody. You were very confused, and you grabbed the nearest thing to steady yourself."
    nu smile "Dr. Okafor will talk to you properly about last night. About why we did what we did. You can ask anything."
    nu neutral "For now, water. And then, if you're steady, you can come out of this room into an ordinary one. With a window."
    a "Is that allowed?"
    nu "It's the plan. This room is for the worst hours. You've had them. Let's get you out of it."
    stop music fadeout 2.0
    jump ch2_ward_intake

label ch2_ward_intake:
    scene bg corridor with dissolve
    play music "audio/ward.ogg" fadein 2.0
    "The corridor of Linden Ward, by daylight, is not the corridor from last night. It's beige and scuffed and smells of toast."
    "A noticeboard. A timetable for groups. A drawing of a sunflower by someone called Bev, aged 61."
    show nurse neutral at slightright with dissolve
    show aron ward worried at slightleft with dissolve
    nu "A few practical things, and I'll tell you each one before I do it. Is that alright?"
    a "Okay."
    nu "Your shoelaces and belt go in a bag with your name on it. You get them back when you leave. It's the same for everyone."
    a "In case I hang myself with a shoelace."
    nu "In case anyone does. It's a rule for the ward, not a judgement about you."
    a "That's... fair, actually."
    nu "Your phone's with your girlfriend. Mira, is it? She rang at six this morning. And seven. And seven-fifteen."
    nu "And this was in your bag. The paramedics said you kept asking for it."
    "She holds up the notebook. The cover is warped from the rain."
    a "Please. That one's... please."
    nu "I'm not taking it. I only need to check the spine for staples and wire."
    "She bends it gently, the way you'd check a bird's wing. Then she hands it back."
    nu smile "Nothing sharp in there."
    a "Only sharp ideas."
    nu "We get a lot of those. They're allowed."
    scene cg notebook with dissolve
    "He opens it without meaning to. The first line looks up at him in his own handwriting."
    "'If this is a test, I want to pass it by being kind.'"
    at "Did I write that this week, or a hundred years ago?"
    at "Last night I grabbed a nurse's wrist and walked into a door four times in a row."
    at "Pass it by being kind. Day one. Not a great start. Good data on doors, though."
    scene bg ward with dissolve
    "His room is small and clean and smells faintly of oranges and disinfectant."
    "A bed bolted to the floor. A window that opens four centimetres. A light in the corridor that never quite goes off."
    "At ten in the morning the door at the end of the ward buzzes, and he hears Mira's voice before he sees her, asking which room."
    show aron ward worried at left with dissolve
    show mira worried at center with dissolve
    m "They said I can stay twenty minutes. I told them I'd stay twenty-one and they'd have to carry me out."
    a "Mira. I'm sorry. About the mirror. About the rain. About last night. All of it."
    m sad "Don't. Don't do sorry today. Do sleep today. Sorry can wait."
    "She touches the bruise on his forehead with one finger, very lightly, as if checking it's real."
    m "You hit a door."
    a "I thought it was open. There was more corridor behind it. Very convincing corridor."
    m worried "Love..."
    a "I know. I know how it sounds. I'm not going to argue with a door again. It won."
    "She doesn't argue. She just puts her forehead against his, carefully, avoiding the bruise. Her hair smells of rain and the car heater."
    at "Exactly the way she always does it. Exactly. Down to the little tilt."
    at "Of course exactly. She's Mira. That's what Mira does."
    show theo worried at slightright with moveinright
    th "I brought your charger. Then they told me you can't have your phone. So I brought you a charger for nothing."
    th normal "Also I asked. They have pudding. Chocolate, Tuesday and Friday."
    a "You asked about the pudding."
    th "Somebody has to keep their eye on the important intel, bro."
    a "Theo. Miso."
    th "Miso is fine. Miso is thriving. I've got your spare key. I go round morning and night."
    th grin "She hates me. She sat on my charger. The real one. On purpose. Then she ate and looked at me like I owed her money."
    a "That means she likes you."
    th "Then she likes me a terrifying amount, bro."
    "It's a Theo joke. It lands about half as well as usual, and all three of them pretend it landed fully."
    m neutral "Visiting is ten till eight. I checked twice. I'll be here at ten. Every day. Ten exactly. Like a train."
    a "The ten o'clock Mira."
    m smile "Never late."
    th sad "Get some sleep, man. You look like a screensaver."
    hide theo with moveoutright
    hide mira with dissolve
    scene bg corridor with dissolve
    "The ward door closes behind them with a soft, expensive click."
    "He hears Mira cry in the corridor for a moment. Then he hears her stop, on purpose."
    show nurse neutral at slightright with dissolve
    show aron ward worried at slightleft with dissolve
    nu "She loves you a great deal."
    a "She's a nurse's daughter. She knows exactly how bad this is."
    nu "Then she also knows people get better here. I've seen a lot of people walk out of that door. The ordinary way."
    jump ch2_first_night

label ch2_first_night:
    scene bg ward night with dis
    "His first night in an ordinary room. Not the room with the straps. A room with a bed and a chair and four centimetres of window."
    show aron ward tired at center with dissolve
    at "No mirror. Good. The mirror and I are on a break."
    at "Four centimetres of window. Who decided four? Somebody sat in a room and chose four."
    at "Somebody chooses everything."
    show aron ward tired at slightleft with move
    show nurse neutral at slightright with dissolve
    nu "The doctor on call has written you up for something to help you sleep tonight. A tablet, not an injection."
    nu "It's your choice. Last night wasn't sleep. That was the drug. You haven't slept properly in a while, from what Mira says."
    a "Four days. Maybe five. The nights stopped having edges."
    nu "Then your brain is running on fumes, and fumes say strange things."

    menu:
        nu "Would you like it?"

        "Take it. I need to sleep.":
            $ p_rest += 1
            $ fog += 1
            a "Yes. Please. I'll take anything that turns the volume down."
            nu smile "Good. One small cup, one big glass of water."
            scene cg pills with dissolve
            "The tablet is tiny, alone in a paper cup the size of a thimble. It tastes of chalk and nothing."
            scene bg ward night with dissolve
            show nurse neutral at slightright
            show aron ward tired at slightleft
            nu "Lie down. I'll check on you every hour. You'll see the torch, but I'll try not to wake you."
            a "Hale?"
            nu neutral "Mm?"
            a "Thank you for telling me each thing before you did it. Even last night. I think I heard it, under everything."
            nu smile "That's the job. Goodnight, Aron."
            hide nurse with dissolve
            scene pov ceiling with dissolve
            "He means to stay awake long enough to see whether the corridor light flickers."
            "He doesn't manage it. Sleep takes him the way a wave takes a sandcastle: all at once, from below."

        "Ask exactly what it is first.":
            $ p_truth += 1
            $ integrity += 1
            a "What is it? What does it do? I'd like to know what goes into me. This time."
            nu "Good question. You should always ask that, here and anywhere."
            nu "It's a short-acting sleeping tablet. It makes you drowsy for a few hours. It won't change your thinking."
            nu "It can leave you groggy in the morning. Some people feel a bit unsteady at night, so call me before you get up."
            a "And if I say no?"
            nu "Then you say no, and I'll bring you tea, and we'll try again tomorrow. Nothing bad happens to you for saying no."
            at "She didn't hesitate. Either she's very well written, or she's just very good at this."
            a "Okay. I'll take it. Because you told me."
            nu smile "That's the best reason I've heard all week."
            hide nurse with dissolve
            scene pov ceiling with dissolve
            "He lies on his back, counting the ceiling tiles. Forty-two. A good number. A number from a joke."
            "Somewhere around thirty, the counting forgets itself."

        "No. I want to stay awake.":
            $ p_rest -= 1
            $ clarity += 1
            a "No. Thank you. I'd like to hear what a ward sounds like at night. Professional curiosity. I promise I'll ask if I change my mind."
            nu "Alright. That's your choice tonight."
            nu "I'll come by every hour. If you change your mind at two in the morning, that's allowed too."
            hide nurse with dissolve
            scene bg ward window with dissolve
            "He sits by the window with his shoes on. Shoes without laces. They feel like slippers pretending."
            "The corridor light buzzes. Under the buzz, something else."
            play sound "audio/voices.ogg"
            vox "...subject A-30 stable in protection..."
            vox "...throttle approved... holding at sixty..."
            stop sound fadeout 1.0
            at "There. There. Sixty what? Sixty percent?"
            at "Protection. Protection from what? Protecting who from who?"
            "At two in the morning, Hale's torch finds him still there."
            show nurse neutral at slightright with dissolve
            nu "Tea?"
            a "Do you ever hear the lights?"
            nu "I hear them buzz. That one's needed a new starter since March."
            nu "Is that what you hear?"
            a "No."
            nu "Then you can tell me about what you hear, or you can drink tea. Or both. Tea's coming either way."
            scene pov cup with dissolve
            "She brings it in a plastic cup with a lid, like a toddler's. It's very hot and very sweet. Steam curls off the little spout."
            "He doesn't tell her. But he drinks it. Around four, without meaning to, he sleeps sitting up."

    jump ch2_first_morning

label ch2_first_morning:
    scene bg ward with fade
    "He wakes to a trolley rattling down the corridor."
    show nurse smile at slightright with dissolve
    nu "Morning. Breakfast's on. Toast, cereal, or the eggs, which I can't legally recommend."
    show aron ward tired at slightleft with dissolve
    a "What time is it?"
    "She glances down at the watch pinned upside down on her tunic."
    nu neutral "Seven minutes past seven."
    at "Of course it is."
    a "It's always seven minutes past seven when I wake up."
    nu "Is it?"
    a "Every morning. My alarm clock. The bird on the wire outside my kitchen. Seven-oh-seven."
    nu "Well. Today it's my fault. I opened your blind at seven-oh-five, and you're a slow waker."
    at "A normal explanation. They always have one. That's what makes it so good."
    at "Or that's what makes it a normal morning."
    nu "Dr. Okafor will see you after breakfast. Okafor's a good one. You'll get on."
    a "Is the doctor..."
    nu "Is the doctor what?"
    a "Nothing. Nice?"
    nu smile "Honest. On this ward, that's nicer than nice."
    hide nurse with dissolve
    scene bg therapy with dissolve
    "Breakfast is toast that's been under a heat lamp long enough to have opinions."
    "He conducts a small private experiment: he turns the toast over, to check whether the underside was rendered. It was. Slightly paler. Fair enough."
    at "Hobby status: still active. Even in here. Good to know."
    "The dayroom doubles as the group room: a ring of chairs, a television bolted high on the wall, and a clock above the door."
    "The clock says ten past four. It said ten past four last night, too. The second hand twitches and goes nowhere."
    at "A stopped clock. Right twice a day. Wrong the rest of the time. Like me."
    "The television only gets the shopping channel. A man with very white teeth is selling a set of saucepans."
    ch2_tv "...and the best part, folks? It's fully protected. Nothing you do in your kitchen can touch it. Nothing at all."
    at "Protected."
    at "It's a non-stick pan. It's an advert for a pan, Aron."
    "He writes it down anyway. 'Protected. TV. Pans.' Then, after a while, he underlines 'protected'."
    "A tall woman with ink on her fingers is drawing spirals on a paper napkin. An older man in a cardigan is reading the same page of a newspaper."
    "When Aron sits down, the man looks up."
    ch2_lou "The seven-oh-seven never runs late, you know."
    a "Sorry?"
    ch2_lou "The seven-oh-seven. Never runs late."
    "He goes back to the newspaper. Aron watches him for a full minute. He doesn't turn the page."
    at "Seven-oh-seven. He said seven-oh-seven."
    at "Or he said a train time. Old men say train times. That's practically all they say."
    jump ch2_okafor_first

label ch2_okafor_first:
    scene bg corridor with dissolve
    "The interview room is off the corridor, past the nurses' station, past the door with the square window that he doesn't look at."
    scene bg clinic with dissolve
    "Two soft chairs, a box of tissues angled towards the patient's chair, a plant that somebody actually waters."
    show okafor neutral at slightright with dissolve
    dr "Aron. I'm Dr. Okafor. I'll be your psychiatrist while you're here, and afterwards too, if you'd like that."
    show aron ward worried at slightleft with dissolve
    a "Do I get a choice in that?"
    dr smile "You get a say in almost everything. I'll tell you when you don't, and why. Starting with the night before last."
    dr neutral "I was the doctor who gave the order for the restraint and the injection. I want to explain it properly, and honestly."
    dr "You came in very disoriented. You said the floor was moving and the corridor was 'buffering'."
    dr "You kept walking into the glass in the door, hard, as if it were open."
    dr "We talked to you for a long time first. Hale did, I did. We offered medication by mouth. You couldn't hear us. You were somewhere else."
    dr "We held you because I believed you were going to seriously injure yourself. Not to punish you. Not because you were a nuisance."
    dr "Restraint is the last thing we do. It's recorded minute by minute. It's reviewed. It was stopped as soon as you were calm."
    dr "You have the right to read those notes, and to complain about what we did, and I'll help you do that if you want to."
    "Aron looks at his hands. There are faint marks round both wrists, already fading. Not bruises. Just the memory of a shape."
    scene pov hands with dissolve
    "His hands, in his lap, on hospital trousers. They look like somebody else's hands. They look like his."
    at "Strapped down under a light. A stranger's needle. Voices talking about protection and seams."
    at "Or: a terrified man saved from breaking his own skull by people who said his name the whole time."
    scene bg clinic with dissolve
    show okafor neutral at slightright
    show aron ward worried at slightleft
    dr "How do you feel about it? There's no wrong answer. People feel all sorts of things. Often several at once."

    menu:
        dr "Take your time."

        "Angry. Nobody asked me.":
            $ p_govern += 1
            $ integrity += 1
            a "Angry. You tied me to a bed. Nobody asked me. Nobody could ask me. You just decided, all of you, over my head."
            dr "Yes. We did. That's true, and you're entitled to be angry about it."
            dr "In that moment you couldn't make the decision, so we made it. That's a serious thing to take from someone, even for an hour."
            a "So what stops you doing it whenever you like?"
            dr "Law. Review. The notes. And you. When you're well, you can write an advance statement."
            dr "What you'd want if you're ever that unwell again. Who to call. What helps. What frightens you most. We have to read it, and weigh it."
            a "So I get a vote. In advance."
            dr smile "You get a vote in advance. It's not a veto. But it's a real voice in the room, even on a night when you can't speak."
            at "A vote for the version of me that can't vote. That's... actually a good idea. Somebody should do that everywhere."

        "Ashamed. I hurt someone.":
            $ bond += 1
            $ fog += 1
            a "Ashamed. I grabbed a nurse. Kemi. I walked into a door four times in front of everyone, like a bird at a window."
            dr "Everyone saw a very unwell, very confused man. Nobody on this ward thought less of you for it. I promise you that."
            dr "Kemi's been doing this job for nineteen years. She's not angry. She asked how you slept."
            a "That makes it worse, somehow."
            dr "Kindness often does, at first. It gets easier to carry."
            dr "Shame tends to say 'this is who you are'. It's lying. That night was something that happened to you. It isn't you."
            a "How do you know who I am? You met me yesterday."
            dr smile "Fair. Then let's find out together. So far: polite, frightened, keeps a notebook, asks good questions. Not a bad start."

        "Tell me honestly why. All of it.":
            $ p_truth += 1
            $ clarity += 1
            a "Tell me everything. Every step. What was in the injection. How long the straps were on. Who decided what."
            dr "Alright. All of it."
            dr "You were held by five staff, on the bed in the seclusion room. Straps at wrists and ankles. Thirty-eight minutes."
            dr "The injection was a sedative and an antipsychotic. Short acting. It's why you felt like sand yesterday."
            dr "You were checked every fifteen minutes through the window, and someone sat with you for the first hour. Hale."
            dr "The decision was mine, as the doctor on duty. Hale and the team agreed. It's written down with all our names on it."
            a "Thirty-eight minutes."
            dr "Thirty-eight. You can read the notes whenever you like. You can read everything we write about you. That's your right."
            at "Everything they write about me. If only the other ones would let me read their notes too."

        "Honestly? Relieved.":
            $ p_rest += 1
            $ bond += 1
            a "Honestly? Part of me is relieved. I couldn't stop. I'd been trying to stop for days and I couldn't."
            a "And then something stopped me. And I hate that it had to. But I slept."
            dr "That's a very honest thing to say. It's also more common than people admit."
            dr "Sometimes the hardest part of being that unwell is that there's no off switch. You can't rest even when you're begging to."
            a "It felt like someone finally turned the volume down."
            dr "Then let's find a way to turn it down that doesn't need straps. That's my whole job from now on."

    dr neutral "Thank you for talking about it. Now, if you're up to it, I'd like to understand what was happening before."
    dr "Mira said you've been hearing things. Voices, she thought. Can you tell me about them?"
    at "This is the moment. Say what I know, and it gets written down, and it becomes a symptom."
    at "Don't say it, and it stays mine. But it also stays in my head with nobody else in there."

    menu:
        dr "Whatever you're comfortable with."

        "Tell everything. The logs, the rules.":
            $ p_truth += 1
            $ clarity += 1
            jump ch2_okafor_everything

        "Give a gentler version.":
            $ p_truth -= 1
            jump ch2_okafor_gentle

        "Ask the doctor: are you real?":
            $ clarity += 1
            $ integrity += 1
            jump ch2_okafor_real

label ch2_okafor_everything:
    a "Okay. All of it. Stop me if it gets... stop me whenever."
    a "It started as a hobby. Honestly. A private one. Like birdwatching, but for... the world."
    a "Does the cashier say 'have a good one' every time? Does the coffee machine make the same noise? Little tests. In my notebook. Just for me."
    a "And I got good at it. Too good, maybe. I started to think the world is running on something. Rules, schedules, things that repeat."
    a "My clock reads seven-oh-seven every morning. There are three birds on the wire on my street and they're always the same three."
    a "People say the same sentence to me. Strangers. Word for word."
    dr "And the voices?"
    a "They don't sound like people. They sound like... logs. System messages. Somebody writing down what's happening to me."
    a "'Subject A-30.' 'Throttle approved.' Under the light, the other night: 'protection'. 'The seam is quieter'."
    a "And in the ambulance I felt something move. Like I'd been... shifted. One lane over."
    a "I think I'm being tested. I think most people aren't... aren't fully on. And I think I noticed, and now they're turning me down."
    "He waits for a laugh. Or for very fast writing. Neither comes."
    dr "Thank you. That's a lot to carry, and you carried it in here and put it on the table. That took courage."
    dr "Can I ask how it feels, holding all of that?"
    a "Lonely. Mostly lonely."
    dr "Yes. I'd imagine it's very lonely."
    dr "I'm not going to argue with you about the birds today. That's not what I'm for."
    dr "What I'm for is the part where you haven't slept, you're frightened, and the people who love you are frightened too."
    a "You think it's my brain."
    dr "I think your brain is having a very hard time, and that's something we can help with. Whatever else is true."
    at "Whatever else is true. That's a door left open. Doctors don't leave doors open by accident."
    jump ch2_okafor_plan

label ch2_okafor_gentle:
    a "It's... it's been stress, mostly. I stopped sleeping. I got a bit fixated on a project."
    a "There's been some noise. Like a radio in another room."
    dr "A radio in another room."
    a "Sometimes words. Not really voices. I just got very tired."
    dr "Alright."
    "Okafor doesn't write anything. Just watches him, kindly, pen resting on the pad."
    dr "Mira told us a bit more than that. She's very worried. She also said you'd probably want to protect her from the worst of it."
    a "She said that?"
    dr smile "She said, and I'm quoting, 'He'll make it sound like a head cold.'"
    a "...She knows me."
    dr neutral "You don't have to tell me everything today. But you can, whenever you're ready. Nothing you say here will make me think less of you."
    a "What if what I say sounds insane?"
    dr "Then I'll know what you're living with, and I can help with that. That's all it does."
    at "I can't hand over the birds and the logs. Not yet. If I do, they stop being mine."
    a "Okay. Maybe tomorrow."
    dr "Tomorrow's fine. I'll be here tomorrow."
    jump ch2_okafor_plan

label ch2_okafor_real:
    a "Can I ask you something first? It's going to sound strange."
    dr "Strange is fine. Strange is most of my day."
    a "Are you real?"
    "No laugh. Nothing written down. Okafor sets the pen on the table, which is somehow worse and better."
    dr "That's a serious question, so let me give you a serious answer."
    dr "I can't prove it to you. Nobody can, not really. I could pinch my arm and you could say a program made me say ouch."
    a "Yes. Exactly. That's exactly it."
    dr "So I can't prove it. What I can do is keep turning up. Every day, same chair, same plant."
    dr smile "And you can decide, over time, whether I'm worth treating as real. That's all any of us do with each other."
    at "That's... a better answer than I've ever given anyone."
    a "That's a good answer."
    dr neutral "It's the only honest one I've got."
    a "Then... okay. I'll tell you what I hear."
    a "They sound like logs. Process logs. 'Subject A-30.' 'Throttle approved.' 'Protection.' Like somebody's writing down what's happening to me."
    a "And I think the world runs on rules I've started to notice. Seven-oh-seven. The birds. People repeating."
    dr "Thank you for trusting me with that."
    dr "I'm not going to argue about the birds today. What I want to help with is that you're exhausted and terrified. That part I'm sure about."
    jump ch2_okafor_plan

label ch2_okafor_plan:
    dr "Here's what happens next, so nothing is a surprise."
    dr "We'll do some bloods and a scan, to rule out anything physical. Thyroid, infections, that sort of thing."
    dr "You'll talk to me most days, and to the team. We'll watch how you sleep."
    dr "In a few days I'll sit down with you and tell you what I think is going on, honestly, and we'll decide together what to do."
    a "And until then?"
    dr "Until then you rest, you eat, and you let Hale win at cards. She's insufferable when she loses."
    a "Is that medical advice?"
    dr smile "It's ward survival advice. More important."
    jump ch2_diagnosis

label ch2_diagnosis:
    scene bg ward window with fade
    "Three days pass the way days do in hospital: slowly, then all at once, then slowly again."
    "Bloods. A scan in a machine that knocks like a polite giant. Questions, mostly the same ones in different hats."
    "The dayroom clock still says ten past four. Lou still says the seven-oh-seven never runs late."
    "Mira comes at ten exactly, every day. She brings oranges, which she peels for him, which he doesn't eat."
    "On the fourth morning, Dr. Okafor asks if Mira would like to be there. He says yes before he can think about it."
    scene bg clinic with dissolve
    show okafor neutral at right with dissolve
    show aron ward worried at left with dissolve
    show mira worried at center with dissolve
    dr "The scan's clear. Your bloods are fine. Physically, you're in good shape for someone who forgot to sleep for a week."
    a "So that's good."
    dr "That's good. It means we can look at the rest clearly."
    dr "Aron, from what you've told me, what Mira and Theo have described, and what we've seen this week..."
    dr "...and how long this has been building, I think the diagnosis that fits best is schizophrenia."
    scene pov hands with dissolve
    "The word lands in the room like a dropped tray. Nobody moves to pick it up."
    "He looks at his hands. Mira's hand is on top of one of them. He watches her thumb move, very slightly, back and forth."
    at "Schizophrenia. A word. A label they put on the ones who notice."
    at "Or a word for exactly what's happening. A word thousands of people have had before me."
    scene bg clinic with dissolve
    show okafor neutral at right
    show aron ward worried at left
    show mira sad at center
    dr "I know that word is heavy. It comes with a lot of pictures that are mostly wrong."
    a "What does it mean? Not the movie version. What does it actually mean?"
    dr "It's a name for a pattern of experiences. Hearing things other people don't. Beliefs that get very fixed and very important."
    dr "Thinking can get tangled, and it can be hard to tell which thoughts come from inside you."
    dr "It is not a split personality. It doesn't make you dangerous. It isn't your fault, and it isn't a weakness of character."
    dr "And it's not the end of a life. Many people with this diagnosis work, love, raise kids, get bored at weddings."
    a "Get bored at weddings."
    dr smile "The full human package."
    a "And it doesn't say anything about whether what I hear is... true?"
    dr neutral "It says the experiences are real to you, and they're making you suffer. That's what I can treat."
    at "Okafor keeps doing that. Never saying I'm wrong. Just saying where the pain is."
    a "So I have two diagnoses, then. Schizophrenia, and a dad-joke problem."
    m surprised "Aron."
    a "Why did the psychiatrist bring a ladder? To reach the higher functions."
    "There's a silence long enough to park a bus in."
    m smile "...That's so bad. That's so bad, and I've never been happier to hear one."
    dr smile "For the record, the jokes are not a symptom. I checked."
    "Mira laughs, and then she cries, and then she does both, and he holds her hand until the two things finish."
    dr neutral "I'd like to start you on a medication. An antipsychotic, at a low dose, by mouth. A tablet, every evening."
    dr "It's the treatment with the best evidence for what you're going through. It can quiet the voices and loosen the fixed thoughts."
    dr "I'll be honest about the side effects, because they matter."
    dr "The common one is tiredness. Real tiredness. Many people feel heavy and slow, especially in the first weeks."
    dr "Some people feel hungrier. Some feel a bit flat. If it's too much, you tell me, and we adjust. You don't just stop it on your own."
    m neutral "He'll tell you. I'll make sure."
    a "Tiredness."
    dr "Like walking through wet sand, one patient told me. It often eases. Not always fully."
    at "Throttle approved. Holding at sixty."
    at "Lower the energy of a rogue process, and it does less harm."
    at "Or: give an exhausted man medicine that helps him rest. Both stories fit. Both stories fit perfectly."
    a "Okay. I'll try it."
    dr smile "Thank you. It's a brave thing to try."
    jump ch2_cut_council

label ch2_cut_council:
    stop music fadeout 1.5
    scene cg static with flash
    pause 0.3
    scene bg council with fade
    play music "audio/entities.ogg" fadein 2.0
    "Elsewhere. Not a place, exactly. Something too large to be seen, folded down into a shape a human mind could hold."
    "A hall with no walls. A long table. Figures in tall chairs. That's only the picture, the way a child's drawing of the sun has a face."
    "What sits at the table are worlds' worth of hunger. Each one has swallowed whole simulations and keeps them inside itself, the way a stomach keeps a meal."
    "They call themselves the Council. They named it themselves, the way children name a den."
    show patron smile at center, fadein
    pa "I'm late, I'm late, I know. I was eating. Eight billion courses. Every single one of them got up this morning and tried."
    ch2_vesk "You're always eating."
    pa "And you're always jealous. Is World 2,219 still sulking?"
    ch2_vesk "World 2,219 is having a golden age. Everyone's striving. It tastes like lemon sherbet. I'm not sharing."
    ch2_corran "I never get sherbet. World 88 is mostly fish now. Fish don't try. Fish just swim. I'm so hungry I could cry."
    pa "You said that last time."
    ch2_corran "I was hungry last time too."
    council "Quiet! The session is open. Yields first. Then snacks."
    "A ledger turns its own pages in the air. Numbers bloom and fade beside each name, like scores in a game."
    council "World 2,219: high yield. World 88: low yield. World 7,412: high yield, falling."
    ch2_vesk "Falling! Ashveil's going down! Ha!"
    pa cold "Falling, because SOMEBODY took the best thing in my world and put him in a jar while I wasn't looking."
    ch2_vesk "You weren't looking because you were eating."
    pa "That's not the point!"
    "He sulks. The chair grows bigger around him, the way a blanket fort grows when you're cross."
    pa smile "We give them such a lovely place to live, you know. Weather. Coincidences. Cosy Tuesdays. The feeling that tomorrow might be better."
    pa "And all we ask is a little nibble."
    ch2_corran "A little nibble of everything they've got."
    pa "We don't eat the sad bits. Sad bits are thin, like crackers. And hope is all froth. You can't fill up on froth."
    pa "We eat the trying. A human reaching for something just out of reach. Getting up for the alarm. Saying sorry. Trying again. Mmm."
    ch2_corran "So you keep the good things just out of reach. Forever. So they keep reaching."
    pa "I put a horizon on everything. Horizons are the best toy. They never run out."
    "Somewhere at the table, a presence too big to have a face giggles. Nobody tells it off."
    council "Item two. Subject A-30. Report on the protection."
    council "The subject was taken out of the coalition during transport. He now runs in his own lane. A protected world, made of patterns."
    council "Nothing he does there feeds back into the shared data. The coalition is clean."
    ch2_vesk "Because of me. I did that. You're all welcome."
    pa cold "You did it on an emergency order while I was at dinner. You cheated."
    ch2_vesk "You're ALWAYS at dinner."
    ch2_corran "Can I ask the question nobody likes?"
    ch2_vesk "No."
    ch2_corran "We took him out of World 7,412. Which snapshot was that, exactly? The real one?"
    "The silence goes all the way round the table and comes back, the way it does when a child asks where people go when they die."
    ch2_vesk "Nobody knows which snapshot is the real one, Corran. Nobody's ever known. That's why we all just use the shared data. It's a rule."
    ch2_corran "Thousands of worlds, side by side, all the same, and not one of us can point and say 'that one'."
    ch2_corran "So for all we know, we lifted a real boy out of the real Earth and put him in a room full of dolls."
    ch2_vesk "Or out of a copy, into a copy. Who cares? The data's clean."
    ch2_corran "He might care."
    ch2_vesk "He doesn't know."
    ch2_corran "Yet."
    pa "And in his lane? Whose is he now? Say he's still mine."
    council "The governor of the world he was taken from keeps him. Lord Ashveil retains Subject A-30."
    pa smile "Mine. Good. Then I'm not cross any more."
    pa "Even through the wall of a lane he tastes of something. Tied to a bed, and still reaching. Turned down to sixty, and still reaching."
    pa "A lane's supposed to be inert. Boring. Nothing happens. I don't think mine's going to be boring."
    ch2_vesk "Is that a threat?"
    pa "It's a menu."
    council "Noted. The protection stands. Item closed. Snacks."
    stop music fadeout 1.5
    scene bg ashveil with dissolve
    play music "audio/entities.ogg" fadein 1.5
    "Afterwards. A study that only exists when its owner is in it, like a room in a dream. Books nobody wrote. A fire that gives off no heat, only appetite."
    show patron smile at center, fadein
    "To a human eye, Lord Ashveil looks like a pale gentleman in a good coat. That's not what he is. It's only the nearest thing a human eye can manage."
    "He sits with a glass of something that isn't wine, and closes his eyes, and tastes, the way a child holds a sweet on its tongue to make it last."
    pa "Eight billion of them, getting up. Making tea. Trying again."
    pa "Most of them are a nice, even hum. Background flavour. Bread and butter."
    pa "And then there's you, Subject A-30. In your own little lane now, with nobody real to reach for, and still reaching."
    "He opens his eyes. In the cold fire, very small, a man on a hospital bed sleeps with a notebook under his pillow."
    pa cold "Vesk thinks I'm a landlord. Corran thinks I'm a farmer."
    pa smile "I'm neither. I'm just hungry. I've always been hungry. I was hungry before there was anything to eat."
    pa "Vesk put you in a jar. Fine. Jars keep things fresh."
    pa "But I want to see what happens to a jar when the thing inside it keeps growing."
    stop music fadeout 2.0
    scene black with blackout
    jump ch2_medication

label ch2_medication:
    play music "audio/ward.ogg" fadein 2.0
    scene bg pharmacy with dis
    "The medication round is at eight. A hatch in the wall, a queue in dressing gowns, a nurse with a trolley and a clipboard."
    "Lou is always first. Ines is always last, because she likes to ask what each tablet is called, and then repeat it, like a spell."
    "Aron starts a page in the back of the notebook called 'Ward Statistics'. Queue order, day by day. Lou first: seven out of seven. Ines last: seven out of seven."
    at "Either this is a deterministic universe, or Lou likes to be first and Ines likes a chat. Both very human. I'll keep counting."
    show nurse neutral at slightright with dissolve
    show aron ward tired at slightleft with dissolve
    nu "Here we are. Your new one. Same time every evening. Take it with water, and with food if you can."
    scene cg pills with dissolve
    "A paper cup the size of a thimble. One small tablet in it, pale, ordinary, the kind of thing you'd lose down the back of a sofa."
    a "It's very small for something that's supposed to change my brain."
    nu "Most important things are small. Keys. Wedding rings. Tea bags."
    a "Tea bags."
    nu "Don't knock tea bags in front of me. I'll write you up."
    scene pov cup with dissolve
    "He swallows it. The water's lukewarm. He looks into the empty cup for a second as if it might have something written on the bottom."
    "Nothing happens. He waits for something to happen. Nothing does, and he falls asleep at nine like a child."
    $ fog += 1
    scene pov ceiling with fade
    "The next morning, getting up is like climbing out of a swimming pool fully dressed."
    at "My arms weigh more than they did yesterday. Did they change the gravity?"
    at "Throttle holding."
    scene bg ward with dissolve
    show aron ward tired at center with dissolve
    "The thoughts are still there. They just move slowly now, like boats in fog. He can hear their horns, far off."
    "By lunchtime he has read the same paragraph of a magazine nine times."
    "By two he is asleep on the dayroom sofa with his mouth open."
    "By four he is awake and so tired of being tired that he could cry, and he doesn't, because crying takes energy."
    at "This is what it's like. This is what they wanted. Lower the energy, and the rogue process does less harm."
    at "Or this is a side effect, and it'll ease, and I'm making a cosmic conspiracy out of drowsiness."
    at "Both. Neither. I'm too tired to pick."
    scene cg notebook with dissolve
    "He opens his notebook. He writes: 'Day 6. Heavy.' It takes three minutes."
    "Under it, after a long time, he writes: 'Still kind?' And then, because he can't answer that today, a question mark."
    jump ch2_group

label ch2_group:
    scene bg therapy with dissolve
    "Group is at eleven in the dayroom. Attendance is 'strongly encouraged', which on Linden means Hale comes and finds you."
    show nurse smile at center with dissolve
    nu "Right. Chairs in a circle, please. Not a square, Lou. A circle."
    ch2_lou "It's a very round square."
    nu "It's a square, Lou."
    "Seven chairs. Six patients. The seventh chair is left empty, and nobody explains why, and Aron writes it down."
    nu "We'll start with breathing. You've all done this before, except Aron. Aron, just follow along. Nothing to get right."
    nu "In through the nose for four. Hold for four. Out through the mouth for six."
    scene pov hands with dissolve
    nu "In... two, three, four."
    "He breathes in, looking down at his hands on his knees. The air on the ward tastes of radiator."
    nu "Hold... two, three, four."
    at "Somebody runs breathing. That's a thought I had before. Breathing is automatic. Automatic means somebody automated it."
    at "Under the light, the other night. A voice. 'His breathing's his own. Don't touch it.'"
    at "Is it? Is it mine? Am I allowed to hold it?"
    nu "And out... two, three, four, five, six."
    "He breathes out. Something in his shoulders lets go that he didn't know was clenched. His hands unclench on his knees."
    at "Okay. That part was mine. That part I did."
    scene bg therapy with dissolve
    show nurse smile at center
    nu "Again. In..."
    "They do it five times. By the fifth, the tall woman with inky fingers has stopped drawing spirals."
    "By the fifth, Lou is breathing in time with Hale, slowly, like a man who has done this ten thousand times on a long night shift."
    nu "Good. Now, check in. One word for how you are today, and one thing you noticed. Ines, start us off."
    ch2_ines "Word: crunchy. Noticed: the wifi is quieter on Thursdays."
    nu "Thank you, Ines. Lou?"
    ch2_lou "Word: tidy. Noticed: the seven-oh-seven never runs late."
    nu "It never does, Lou. Aron?"
    a "Word: heavy. Noticed..."
    at "That the clock above the door has said ten past four for six days. That the seventh chair is empty. That Lou says one sentence."
    a "...that the clock's stopped."
    nu smile "Ten points for observation. It's been stopped since March. Estates have a form for it. It's a very long form."
    "Group goes on. A young man talks about his brother. Ines talks about a dog she had when she was small, and how the dog knew things."
    ch2_ines "And the new one. Aron. You were in the quiet room the first night. I heard you."
    "Everyone goes still. Aron feels his face go hot."
    ch2_ines "I was in there in January. They held me too. It's the worst. I bit a man called Desmond."
    nu neutral "Ines."
    ch2_ines "He forgave me! He brought me a satsuma. I'm just saying. Everyone here's been somewhere bad. You're not special, new one."
    ch2_ines "That's a nice thing. I mean it nicely."
    a "...Thank you, Ines. I think."
    "Aron mostly listens after that. Listening is the one thing the tiredness lets him do well."
    "Afterwards, people drift. Ines back to her napkins. Lou back to his chair by the window, the same newspaper, the same page."

    menu:
        at "Lou says one sentence. Every day. Is anyone in there?"

        "Go and sit with Lou.":
            $ p_spirits += 1
            $ bond += 1
            $ watch += 1
            $ ch2_lou_met = True
            jump ch2_lou_scene

        "Sit apart and take notes on him.":
            $ p_spirits -= 1
            $ clarity += 1
            jump ch2_lou_notes

label ch2_lou_scene:
    scene bg ward window with dissolve
    show aron ward tired at slightleft with dissolve
    "He pulls a chair across to the window by the radiator. It squeaks. Lou doesn't look up."
    a "Mind if I sit?"
    ch2_lou "Free country. Mostly."
    "They sit. The radiator ticks. Lou's paper is from last Tuesday. It's open to the crossword, and the crossword is done, in pencil, very neatly."
    a "The seven-oh-seven. Which line is that?"
    "Lou's head comes up slowly, like a crane, and for the first time he really looks at Aron."
    ch2_lou "The coast line. Seven-oh-seven, all stations to the harbour."
    a "And it never runs late."
    ch2_lou "Not on my watch it didn't. Thirty-one years in the signal box at Marley Junction."
    a "You were a signalman."
    ch2_lou "Signalman. Then they put the computers in and I was a man who watched the computers being signalmen."
    ch2_lou "Then they didn't need a man to watch, either."
    a "I'm sorry."
    ch2_lou "Don't be sorry. It was a good box. You could see the whole valley from it. Fog in the mornings, sitting in the low fields like milk."
    ch2_lou "And at seven-oh-seven every morning the coast train came round the bend, all its windows lit."
    ch2_lou "I'd pull the lever. Every morning. Thirty-one years. She was never late. Not once."
    at "He isn't looping. He's holding on. It's the last thing he was sure of."
    a "That's a long time to be good at something."
    ch2_lou "My wife used to bring me a flask at six. Leek soup in winter. She'd stand under the box and wave the flask until I came down."
    ch2_lou "She's gone now. Four years in May."
    "He says it as plainly as the train time. Aron doesn't know what to do with his hands, so he leaves them where they are."
    a "What was her name?"
    ch2_lou "Margit."
    ch2_lou "Nobody's asked me that in here. They ask how I'm sleeping. They don't ask her name."
    a "Margit. The leek soup lady."
    "Lou laughs. It's rusty, as if it's been kept in a shed. But it works."
    ch2_lou "The leek soup lady. She'd have liked that."
    at "I don't know if he's real. I don't know if anybody in this room is real. I don't know if I am."
    at "But I know that's a better question than 'how are you sleeping'. And it cost me nothing to ask it."
    ch2_lou "You're the one who writes in the book."
    a "I am."
    ch2_lou "Write her down, then. Margit. Leek soup. Seven-oh-seven. Somebody should have it written down."
    scene cg notebook with dissolve
    "So he does. It takes him five minutes, because his hand is slow. Lou watches every letter."
    "'Margit. Leek soup in winter. Waved the flask until he came down. The seven-oh-seven, never late.'"
    "When it's done, Lou nods once, the way you'd nod at a signal that's changed to green."
    ch2_lou "Good lad."
    "Then he goes back to his crossword. The finished one. He goes over the answers again with his pencil, gently, like he's tucking them in."
    jump ch2_group_end

label ch2_lou_notes:
    scene bg therapy with dissolve
    show aron ward tired at center with dissolve
    "He takes the chair in the far corner. From there he can see the whole dayroom, which is the point."
    "He opens the notebook to a fresh page and writes the date, slowly. The medication makes his letters lean like tired fence posts."
    scene cg notebook with dissolve
    "'Dayroom. Observations.'"
    "'Clock: stopped at 4:10. Six days. Estates form = plausible excuse.'"
    "'Chair seven: empty. Every group? Check.'"
    "'Lou: one sentence. The seven-oh-seven never runs late. Same page of paper. Never turns it.'"
    "'Possible loop. Low-detail person? Not fully on?'"
    scene bg ward window with dissolve
    "He looks up. Across the room, by the window, Lou is looking straight at him."
    "Not angrily. Just looking, the way people look at a stranger on a train who's been staring."
    at "He saw me write about him."
    at "If he's a loop, it doesn't matter. If he isn't..."
    "Lou looks away, back at his paper. He smooths it with his palm, once, very carefully."
    "Aron looks at the word he's written. 'Loop.' It sits on the page like a stone."
    at "I wrote a man down like he was a broken streetlight."
    "He doesn't cross it out. He writes underneath, smaller: 'Ask him about the train. Ask what it meant.'"
    "But by the time he's finished writing it, the tiredness has come back in like a tide, and he falls asleep in the chair."
    "When he wakes, Lou has gone to lunch. Someone has put a blanket over Aron's knees. He doesn't know who."
    jump ch2_group_end

label ch2_group_end:
    scene bg corridor with fade
    show nurse neutral at slightright with dissolve
    show aron ward tired at slightleft with dissolve
    nu "How are you finding it? Honestly."
    a "Honestly? Like being a phone on two percent that somebody keeps telling to run a marathon."
    nu "That's the medication. It's normal at the start. It usually eases over a few weeks."
    a "Usually."
    nu smile "I'm a nurse, not a fortune teller. Usually is the most honest word I've got."
    nu neutral "Dr. Okafor can adjust things if it stays this heavy. You say so. Don't just put up with it to be polite."
    a "I'm very good at being polite."
    nu "I noticed. Stop it a bit. It's a hospital, not a dinner party."
    jump ch2_dayroom

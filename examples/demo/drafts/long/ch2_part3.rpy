# Snapshot - Chapter 2: "Fog" (part 3 of 6)
# Life in the fog: lost hours, Theo's pills or the gentler route, the cab
# driver who knows his name, Dr. Okafor, Pim and Dross patching the leak,
# Seraphiel's unease. Continues in ch2_part4.rpy.

default ch2_took_pill = False

label ch2_fog_life:
    scene pov ceiling with fade
    "Seven minutes past seven."
    "The alarm clock on the bedside table is small and white, with one orange switch. A Braun. He bought it with his first pay cheque."
    "Every morning it says seven minutes past seven when it goes off, and every morning he hears it from the bottom of a well."
    at "Get up."
    at "Get. Up."
    "His body considers this the way a mountain considers a request to move."
    scene bg bedroom with dissolve
    show aron tired at center with dissolve
    show miso loaf at catspot with dissolve
    "Miso is on his chest, then on his legs, then on his face, then back on his chest. She has opinions about breakfast."
    "He gets up at eleven. Mira has gone to work and left a note against the kettle: 'EAT SOMETHING. Love you. The mug says hi.'"
    $ fog += 1
    scene bg kitchen with dissolve
    "He eats toast standing up. On the wire outside the window, a bird sits, looking at nothing."
    show aron tired at slightleft with dissolve
    at "It's eleven fourteen. The bird's still there. It came at seven-oh-seven and I wasn't up to see it."
    at "If a bird lands on a wire and nobody's awake to see it, does the render bother?"
    scene pov cup with dissolve
    "He looks into his coffee. It's gone cold while he was looking at the bird. A skin of milk has formed on top, wrinkled like a map."
    "The thought is very slow. It arrives, sits down, and falls asleep in the chair before it can finish itself."
    scene bg kitchen table with dissolve
    "The weeks go like that."
    "He sleeps eleven hours and wakes up tired. He naps at two and wakes up tired. He goes to bed at nine because tired is easier lying down."
    "The voices are very quiet now. Some days he doesn't hear them at all. On those days he isn't sure whether he feels better or lonelier."
    "The phone rings on a Wednesday. It's Mrs. Feld from Feld Design, kind and awkward, in the voice people use near hospitals."
    "Mrs. Feld" "We just think, while you recover, it makes sense to bring your hours down a bit. Three days. For now."
    show aron tired at slightleft with dissolve
    a "For now."
    "Mrs. Feld" "Absolutely for now. Nobody's in a rush. Your health comes first. Honestly, Aron. Take your time."
    a "Thank you. Really."
    scene bg kitchen with dissolve
    "He puts the phone down and sits on the kitchen floor for a while, because the floor is close and asks nothing."
    "Miso comes and sits next to him, a polite distance away, as if they're both waiting for the same bus."
    at "Three days. Then two, probably. Then 'let's talk about whether this is the right fit'."
    at "That's how it goes. It's how it goes for everyone. Nobody's throttling me. It's just Mrs. Feld, being decent."
    at "Both. Again. Always both."
    scene bg supermarket with dissolve
    "On Fridays he does the shopping, because Okafor said small jobs are good and because the supermarket is a laboratory."
    show aron tired at slightleft with dissolve
    "He has a standing experiment at till four. The cashier is a young man with a lip ring. Every week, he says the same thing."
    at "Hypothesis: 'have a good one'. Twelve weeks running. Let's see."
    "Beep. Beep. Oat milk. Bread. Cat food. A lemon, for no reason, as a control."
    "Cashier" "That's eleven forty. Have a good one."
    at "Thirteen. Thirteen weeks. Lovely. Consistent. A man of principle."
    "He writes it in the notebook at the end of the aisle, between the cereal and the cat litter, and feels the small warm satisfaction of a hobby going well."
    at "The fog can have my mornings. It's not having this."
    scene bg bedroom door with dissolve
    "Laundry, Sunday. He pairs the socks on the bed. Eleven pairs, and one left over. There is always one left over."
    "He has started keeping the singles in a shoebox labelled 'AWAITING PARTNER'. Some of them have been waiting four years."
    at "Where do they go? Every household in the world, losing socks. Somebody's got the most enormous sock budget."
    show miso stare at catspot with dissolve
    "Miso sits in the empty laundry basket and watches him with the air of a cat who knows exactly where the socks go and will never tell."
    scene bg room with dissolve
    "The cardboard box sits on the desk chair in the living room. Lid closed. He walks past it nine times a day."
    "Once, he opens it. The notes are all there, folded, smelling faintly of rain. He closes it again. He's too tired to be afraid of it."
    jump ch2_theo_thursday

label ch2_theo_thursday:
    scene bg room with dissolve
    "Thursday. Theo's day. Theo arrives at one with a bag of crisps and a frozen pizza and the energy of a dog let off a lead."
    show theo grin at slightright with dissolve
    show aron tired at slightleft with dissolve
    th "Thursday, baby! The day of Theo. Get your shoes on, we're going somewhere that isn't a bed."
    a "I am wearing shoes."
    th normal "You're wearing slippers, bro. One of them is Mira's."
    a "...They're comfortable."
    th "Alright. Alright. Plan B. We stay here and I watch you be comfortable."
    show miso stare at catspot with dissolve
    th worried "She's looking at me. Why is she looking at me like that? I fed you for three weeks, cat. Three weeks."
    a "She remembers the charger."
    hide miso with dissolve
    "Theo drops onto the sofa. He looks at Aron for a long moment, and the grin goes somewhere for a rest."
    th worried "You look like a loading screen, man."
    a "I feel like one. I'm behind on everything. Work. Emails. Mira's birthday present, which was three weeks ago."
    a "I keep thinking, by now I should be back. By now it should have lifted."
    th "Bro, the universe doesn't run on your schedule."
    "He says it lightly, the way he always says it. Aron has heard it a hundred times. Today it lands differently."
    at "The universe doesn't run on my schedule. It runs on someone's."
    th "Okay, listen. Don't make the face. I've got an idea, and it's a bit of a Theo idea."
    "He pulls a little orange pharmacy bottle out of his jacket. His name on the label. Prescribed."
    th "My focus pills. The ADHD ones. You know. Squirrel in a man suit, doctor-approved."
    th "One of these and I can do my taxes. Two years of taxes, last spring, in an afternoon."
    th normal "You're just tired, right? These are for when your brain won't get out of bed. That's literally what they're for."
    a "Theo..."
    th "Just one. Just to see. You'd get a Thursday back. A real one. We could go to the park like actual people."
    scene pov hands with dissolve
    "He shakes the bottle into Aron's open palm without quite meaning to. One tablet. Small and bright, like a toy."
    at "Okafor said don't take anything else without asking. Okafor said the tiredness is a side effect."
    at "Throttle at sixty. And here's a way to turn myself back up. Sitting in my own hand."

    menu:
        th "Your call, bro. No pressure."

        "Take Theo's pill.":
            $ risky += 1
            $ p_rest -= 1
            $ clarity += 1
            $ ch2_took_pill = True
            jump ch2_stim_scene

        "No. Ask Dr. Okafor about it.":
            $ p_rest += 1
            $ integrity += 1
            jump ch2_stim_refuse

label ch2_stim_refuse:
    scene bg room with dissolve
    show theo normal at slightright
    show aron tired at slightleft
    a "No. Thanks. I mean it, thank you. But no."
    "He tips the tablet back into the bottle and screws the lid on and hands it back."
    th worried "You sure? It's just one."
    a "It's not mine. And Okafor said, anything else, ask first. I said I would."
    a "I want to actually ask. About the tiredness. Maybe there's a version of this where I don't feel like a wet coat."
    th normal "...Yeah. Yeah, okay. That's smart. That's annoyingly smart."
    "He puts the bottle back in his jacket. Then he takes it out again, and puts it in the other pocket, further away, which Aron appreciates."
    th sad "Sorry. That was dumb. I just miss you, man. You were the fast one. I'm not used to being the fast one."
    a "You're not the fast one. You're the loud one."
    th grin "I contain multitudes."
    "They eat the frozen pizza, which is burnt on one side and frozen on the other, which Theo calls 'two pizzas for the price of one'."
    "They don't go to the park. But they sit on the sofa and watch a documentary about octopuses, and Theo cries at the end, and denies it."
    jump ch2_cab

label ch2_stim_scene:
    scene bg room with dissolve
    show theo grin at slightright
    show aron tired at slightleft
    a "Okay. One. Just to see."
    th grin "That's my boy. Thursday is back on."
    "He swallows it with cold coffee. It's a small thing. It goes down easy. That's the first thing he'll remember later: how easy it was."
    "For forty minutes, nothing. They eat crisps. Theo talks about a girl at the gym who is either flirting with him or allergic to him."
    "Then, somewhere between one crisp and the next, the fog lifts."
    "Not thins. Lifts. Like someone pulling a dust sheet off a piece of furniture."
    show aron awe at slightleft with dissolve
    at "Oh."
    at "Oh, there you are. There I am."
    a "Theo. Theo, I can think."
    th grin "Told you! Welcome back to the land of the living. Park?"
    a "In a minute. In one minute. I just need to..."
    scene bg desk with dissolve
    show aron awe at center with dissolve
    "He's at the box. The lid is off. The notes are out. He's pinning them back on the wall, faster than he's moved in a month."
    show theo worried at slightright with dissolve
    th worried "Bro. That's not the park."
    a "No, listen. Listen. I've been too tired to see it, but it's obvious. It's so obvious."
    a "The voices. They always came when I was most awake. Never when I was tired. Never after the meds."
    a "And they said 'throttle'. Throttle, Theo. You don't throttle something unless it can go fast."
    a "You don't slow down a process that doesn't matter. You let it run. You only slow down the one that's doing something."
    th "Okay, that's... a sentence."
    a "It means I matter. To whatever this is. If they're turning me down, then I was worth turning down."
    a "And the birds on the curtain rail. And 'protected'. And 'inert'. It's all one thing. Something's keeping me in a box and the box is leaking."
    "The wall fills up. String. Arrows. The three birds, the clock, Lou's train, the lighthouse. He writes fast and tiny and perfectly legible."
    "It is the most alive he has felt since the rain. It feels exactly like being right."
    th "Aron. Maybe slow it down a bit, yeah? Maybe sit."
    a "I've been sitting for six weeks, Theo!"
    "It comes out too loud. Theo flinches. Aron doesn't notice. Later, he'll remember that too."
    "Theo leaves at six. He hovers by the door a long time first. 'Text me,' he says. 'Text me something dumb. A vegetable.'"
    "Aron doesn't text him. He's busy."
    scene bg room night with dissolve
    "Evening comes. The clarity doesn't go. It goes sharp instead, like a knife being sharpened past the point of usefulness."
    "His heart is going too fast. His jaw is clenched so hard his teeth ache. He takes his evening meds and they do nothing, or they fight."
    "He can feel the two medicines arguing in his blood, one pressing down, one pushing up."
    "Midnight. One. Two. The wall is finished. It's beautiful. He can't remember what half of it means."
    play sound "audio/voices.ogg"
    vox "...anomaly. Energy draw, subject A-30... above throttle ceiling..."
    vox "...lane disturbance rising... flag for the Commander..."
    stop sound fadeout 1.0
    show aron worried at center with dissolve
    at "Oh, they noticed. I went above the line and somebody noticed."
    at "For the Commander. I've been escalated. I've never been escalated in my life. I'm almost flattered."
    "He isn't frightened, exactly. That's the strange part. He's fascinated, and wired, and his heart won't slow down."
    "At three, he starts testing whether the kitchen light stutters when he blinks. It does. Or he does. He can't tell which, so he tests it again."
    scene bg kitchen night with dissolve
    "Three hundred blinks. He runs out of notebook pages and keeps the tally on the lid of the bread bin, in biro, in neat gates of five."
    show mira worried at slightright with dissolve
    show aron worried at slightleft with dissolve
    m "Aron? Love, it's four in the morning. Why are all the lights..."
    "She sees the bread bin, covered in tally marks. She sees, through the door, the living room wall. All of it, back up, with string."
    m surprised "..."
    m worried "Oh, no. Oh, love, no."
    a "It's fine. It's fine. I just had a good day. I could think. I got loads done."
    m "Your hands are shaking. Your pupils are... Aron, did you take something?"
    "He could lie. The lie is right there, ready to go, polished. He's very tired of lying to her. He's very tired, full stop, under the buzzing."
    a "Theo's pill. One. For the tiredness."
    m sad "His ADHD pills. On top of your meds."
    a "It worked, Mira. For a few hours it really worked. I was me."
    m "You were you at four in the morning, doing tally marks on the bread bin with your heart going like that."
    "She's not shouting. That's the worst of it. She just looks very frightened and very sad, in her pyjamas, at four in the morning."
    m "Okafor said. Stimulants, other people's medication, any of it. It can bring the psychosis back. That's the whole thing we're trying to stop."
    a "I know."
    m "Then why..."
    a "Because I miss being able to think. Because I'm so tired I could cry and I'm too tired to cry."
    m sad "...I know, love. I know you are."
    "She doesn't take the notebook. She sits next to him on the kitchen floor and holds his shaking hand, and they wait for it to wear off. It takes hours."
    scene bg bedroom with fade
    show aron sad at center with dissolve
    "The crash comes the next afternoon like a tide coming in over a beach. He sleeps nineteen hours."
    "When he wakes up, everything is grey. Not tired-grey. Empty-grey. As if someone took the colour out to pay for yesterday."
    "The wall is still up in the next room. He can't read it. It looks like it was written by somebody cleverer and much more frightened than him."
    at "I was right yesterday. I was so sure I was right."
    at "And I made Mira sit up till dawn holding my hand like I was a kid with a fever."
    at "If this is a test, I want to pass it by being kind. I didn't even text Theo back."
    "He takes his phone. Eleven messages from Theo. The last one is a photo of a carrot shaped like a man with two legs."
    "Under it: 'bro im so sorry. that was so dumb of me. please be ok. mira told me. im an idiot.'"
    a "Not your fault. Mine. I said yes."
    th "still my pills bro. never again. ill throw them at the sun if u want"
    a "Don't throw them at the sun. You need them for your taxes."
    th "ha. ok. love u man"
    "He lies there until it's dark again. The shame is the heaviest part, heavier than the meds. It doesn't come with a side-effects leaflet."
    jump ch2_cab

label ch2_cab:
    scene bg street rain with fade
    play music "audio/unease.ogg" fadein 2.0
    "The clinic appointment is on Monday at two. It's pouring. The bus is cancelled. Mira's at work. He calls a cab."
    "The cab is old and clean and smells of pine air freshener. The driver is a big man with a grey beard and a radio on low."
    ch2_driver "Clinic up the hill, is it? Right you are. Mind the seatbelt, it sticks."
    scene pov hands with dissolve
    "He sits in the back with the notebook on his knees. Rain draws long diagonal lines down the window."
    ch2_driver "Filthy day. You alright back there? You look done in."
    a "Just tired. Medication."
    ch2_driver "Ah. Say no more. My sister's on the same sort of thing. Sleeps like a cat."
    scene bg street rain with dissolve
    "They pull out. The wipers go back and forth. On the dashboard, a little green clock says seven minutes past seven."
    at "It's quarter to two."
    at "It's an old cab. The clock's wrong. Clocks in cabs are always wrong."
    ch2_driver "What's your name, then? I like to know who I've got."
    a "Aron."
    "The driver's eyes find his in the mirror. They stay there a beat too long."
    ch2_driver "No. Go on. Aron?"
    a "Aron. Why?"
    ch2_driver "That's mad, that is. That's the lad's name. Exact same."
    ch2_driver "I had a lad in this cab, oh, a few months back now. Your age. Nice lad. Notebook, like yours. Aron, his name was. Same as you."
    ch2_driver "Lived round your way, I think. You might know him."
    "Aron's hands go very still on the notebook."
    ch2_driver "Perfectly normal when he got in. Chatty. Joked about the weather. Then about two streets on, he goes quiet."
    ch2_driver "Starts looking at my clock. That one. Says it's seven-oh-seven. Says it's always seven-oh-seven. Starts asking me if I'm real."
    ch2_driver "Out of the blue. Just like that. Right after he got in this cab. Went mentally ill, poor sod, right there in the back seat."
    ch2_driver "Sat exactly where you're sitting, he did."
    scene pov hands with dissolve
    "His knuckles are white on the notebook's cover. The rain is very loud."
    a "What... what happened to him?"
    ch2_driver "They took him in, I heard. The ward up the hill. Where you're going, funnily enough."
    ch2_driver "Lovely lad. Gave a fella his black umbrella once, someone told me. In the rain. Just handed it over."
    at "That's me."
    at "That's me. He's talking about me. The umbrella. The ward. The clock."
    at "I've never been in this cab. Have I? Before the rain, the weeks are smudged. I might have. I might have and not remembered."
    at "Or he's not a man. He's a... a mirror somebody forgot to turn round."
    a "Did he have... what did he look like?"
    ch2_driver "Like you, a bit. Sad eyes. Nice coat. Funny, that."
    "The driver laughs, and turns the radio up a notch, and starts talking about the football as if none of it had happened."
    ch2_driver "Anyway. United, eh? Shocking. Shocking."
    scene bg street rain with dissolve
    "At the clinic he pays and gets out and stands in the rain without his hood up for a full minute."
    "The cab pulls away. He looks for the number on the licence plate, to write it down. The rain makes it impossible to read."
    at "Small, slow, kind, Okafor would say. Notice it. Name it. Don't build a cathedral on it."
    at "Noticed. A cab driver told me my own story. Named."
    at "I'm going to need a very big cathedral."
    stop music fadeout 2.0
    jump ch2_okafor_fatigue

label ch2_okafor_fatigue:
    scene bg corridor with dissolve
    play music "audio/ward.ogg" fadein 2.0
    "The clinic is the same building as the ward, but downstairs, with plastic chairs and a fish tank with one very old fish in it."
    scene bg clinic with dissolve
    show okafor neutral at slightright with dissolve
    show aron tired at slightleft with dissolve
    dr "You're soaked. Sit down. How are things? The real version."
    if ch2_took_pill:
        a "I took one of Theo's ADHD pills. Last Thursday. I'm sorry. I said I'd ask first and I didn't."
        dr "Thank you for telling me. Truly. That's the hard bit, and you just did it."
        dr "What happened?"
        a "I could think for about six hours. Then I couldn't sleep. Then I heard them again. Then I did tally marks on the bread bin till four."
        dr worried "Alright. And since?"
        a "Crashed. Grey. Ashamed. Mostly ashamed."
        dr neutral "I'm not angry with you, Aron. I'm not going to lecture you. But I do want to be very clear, because it matters."
        dr "Stimulants, especially ones that aren't prescribed for you, can push psychosis back up. Not always. Often enough that I'd never recommend it."
        dr "And the crash afterwards isn't a punishment. It's chemistry. You borrowed energy from tomorrow, and tomorrow wanted it back."
        a "With interest."
        dr "With interest. So let's look at a version where you don't have to borrow."
    else:
        a "Tired. All the time. I sleep eleven hours and wake up like I've been dug up."
        a "Theo offered me one of his ADHD pills. To get a Thursday back. I said no. I said I'd ask you."
        dr smile "Thank you. I know that wasn't easy to turn down."
        dr neutral "And you were right to wait. Stimulants that aren't prescribed for you can push psychosis back up. Often enough that I'd never recommend it."
        a "Then what do I do? I can't live my whole life at two percent battery."
        dr "No. You shouldn't have to. Let's look at what we can actually change."
    dr "The tiredness is real. I'm not going to tell you to push through it. It's one of the most common reasons people stop treatment, and I understand why."
    dr "A few things often help, and none of them are magic."
    dr "First, we move your dose to an hour before bed. A lot of the sleepiness then happens while you're asleep anyway."
    dr "Second, daylight. A short walk in the morning, even ten minutes. It tells your body clock which way is up."
    dr "Third, the same wake-up time every day, even on bad days. Even if you go back to bed after."
    dr "And in a month, if you've been stable, we look at whether the dose can come down a little. Carefully. Together."
    a "What if it doesn't get better?"
    dr "Then we keep looking. Different timing. Different medication, possibly. There's more than one key for this door."
    dr "I'll be honest: some tiredness may stay. But the goal isn't to make you smaller. If you feel smaller, that's a problem to solve, not a price to pay forever."
    at "Not to make me smaller. Lower the energy of a rogue process. Or help a man rest. Both. Always both."
    a "Can I tell you something that happened on the way here?"
    dr "Of course."
    a "The cab driver told me a story about a man called Aron. My age. Notebook. Asked him if he was real. Went to the ward up the hill."
    a "He was telling me about me. As if I was someone else. And I don't remember ever being in that cab."
    "Okafor is quiet for a moment. Not alarmed. Thinking."
    dr "That must have been frightening."
    a "Very."
    dr "Can I offer some possibilities, without telling you which one's right?"
    dr "You were very unwell before you came in. Memory around that time is often patchy. You may have taken that cab and lost it."
    dr "Drivers talk. Your street's small. Someone may have told him. And our brains are very good at hearing our own story in someone else's."
    a "And if none of those?"
    dr "Then we write it down, and see if it happens again, and talk about it here. Not alone at three in the morning."
    dr "The worst thing you can do with something like that is carry it by yourself."
    a "...Okay. Evening dose. Morning walk. Same wake-up time. And bring the weird things here."
    dr smile "That's a plan. Write it in the notebook. I know you will anyway."
    stop music fadeout 2.0
    jump ch2_cut_patch

label ch2_cut_patch:
    scene cg static with flash
    pause 0.3
    scene bg foundry with fade
    play music "audio/entities.ogg" fadein 2.0
    "Elsewhere. Behind the protected world, where it's made. A long hall of moulds and furnaces and hanging, half-finished people."
    "Faces being poured. Coats being stitched. A cab driver, grey-bearded, is hanging from a hook by his collar, very still, waiting to be fixed."
    show pim worried at slightleft, fadein
    show dross neutral at slightright, fadein
    pi "Okay. Okay okay okay. Talk me through it. Why did the cab driver say his name?"
    dro "Because his name was in the cab driver."
    pi "It shouldn't be! The driver's a pattern. A driver says 'filthy day' and 'mind the seatbelt' and something about the football. That's it."
    dro "And 'I had a lad in this cab called Aron'."
    pi "That's not in the pattern! I checked the pattern! There's no Aron in the pattern!"
    dro "There is now."
    "Dross reaches up and turns the hanging driver round by the shoulder. On the inside of his coat, stitched into the lining, there's a word. ARON."
    pi "...Oh, that's horrible. That's actually horrible."
    dro "It's seeped in. Like damp. He sits in that world with his whole mind going, and everything round him soaks it up."
    pi "A lane's supposed to be inert. That's the whole point of protection. He does things, nothing happens. Lovely and quiet."
    dro "Lane's not inert, Pim. Lane's damp."
    pi "First it was the nurse's line on the first night. Then that pan advert. 'Fully protected'. I didn't write that. Nobody wrote that."
    pi "Then his three sparrows, on a curtain rail, inside. Inside, Dross! Patterns don't put birds indoors!"
    dro "And the clock in the cab."
    pi "And the clock in the cab. Seven-oh-seven, at quarter to two. I had to reset that dashboard twice."
    show pim neutral at slightleft
    pi "Okay. We patch it. We re-pour the driver. Fresh pattern, no lining, no Aron. Done. Back on the rank by Tuesday."
    dro "Did that this morning."
    pi "And?"
    dro "Re-poured him clean. Hung him up to set. Came back an hour later and he was humming. Same tune the lad hums when he's making tea."
    pi worried "...Patterns don't hum."
    dro "This one does now."
    "They look at the driver for a while. The driver hangs there, peaceful, humming very faintly to nobody."
    pi "If upstairs finds out the lane's leaking, they'll say we did a bad job."
    dro "We did do a bad job. You can't do a good job on this. It's like mopping a floor while it's still raining."
    pi "Then what do we do?"
    dro "Keep mopping. Write it all down. And if anyone asks, it's damp."
    pi "That's not a technical term."
    dro "It is now."
    "Dross lifts the driver down, very gently, the way you'd lift a sleeping child, and carries him back towards the furnace to try again."
    stop music fadeout 2.0
    jump ch2_cut_seraph

label ch2_cut_seraph:
    scene bg command with fade
    play music "audio/entities.ogg" fadein 2.0
    "The operations room of the Angel corps, where nothing is ever switched off."
    "Rows of light. Worlds on every wall. A whole coalition of snapshot worlds, turning side by side, sharing the same data like a single breath."
    "And off to one side, on a screen of its own, a single lane. One world, alone. Protected."
    show seraph stern at center, fadein
    se "Report on the protected lane."
    sysmsg "Subject A-30 stable. Coalition data clean. No feedback from the lane to the shared data."
    se "And inside the lane?"
    sysmsg "Irregularities. Classified as noise. A nurse's unscripted line. An advertisement. Three sparrows indoors. A taxi clock. A taxi driver."
    se concerned "The taxi driver told him his own story."
    sysmsg "Correct. The spirits are patching it. The patch is not holding."
    if ch2_took_pill:
        sysmsg "Also: one energy spike. Thursday. Source: external stimulant. The irregularities increased that night. Resolved by crash."
        se "He turned himself back up, and the lane got louder. And it hurt him."
    else:
        sysmsg "Also: subject declined an external stimulant. Subject asked his physician instead."
        se "He had a way to turn himself back up, in his friend's hand, and he asked permission first."
    se stern "A lane is supposed to be inert. That's the entire argument for protection. He acts, and nothing answers."
    sysmsg "Correct. Recommendation: maintain the throttle. Lower energy, less leakage."
    se "So we throttled him because he might damage the coalition. And now we keep throttling him because he's damaging his own cell."
    sysmsg "That is an accurate summary."
    se concerned "It's an accurate summary of a trap."
    "Seraphiel turns away from the lane and looks at the great wall of the coalition. Thousands of worlds. Thousands of Earths."
    se "Tell me again which one is the real one."
    sysmsg "Unknown. No agent holds that information. All snapshots are treated equally and act on shared data."
    se "So we lifted him out of a world we can't prove is real, and put him in one we know isn't."
    sysmsg "Correct."
    se "And he's still kind to it. Look at the file. He sits with old men. He fixes clocks. He apologises to the cat."
    sysmsg "Low-value actions. No effect on shared data."
    se stern "Log them anyway. Every one. And log the leaks. Don't call them noise. Call them what they are."
    sysmsg "What are they, Commander?"
    "For a long moment, the Commander doesn't answer. On the lone screen, a man stands in the rain outside a clinic with his hood down."
    se concerned "A mind pressing on the walls of the room we put it in."
    stop music fadeout 2.0
    scene black with blackout
    jump ch2_routine

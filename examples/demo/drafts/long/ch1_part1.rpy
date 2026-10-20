# Snapshot - Chapter 1, "The Morning Render" (part 1 of 4)
# The morning, Mira, Miso, the kitchen, the first cut to the angel corps,
# the street, and Theo at the cafe.

define ch1_vael = Character("Adjutant Vael", color="#ffe9a8")
define ch1_dogman = Character("Man with a dog", color="#cccccc")
define ch1_woman = Character("Woman at the crossing", color="#cccccc")
define ch1_baker = Character("Baker", color="#d8c49a")

default ch1_test = ""
default ch1_asked_name = False
default ch1_saw_edge = False
default ch1_went_theo = False
default ch1_told_dream = False

label chapter1:
    $ chapter = 1
    scene black with blackout
    centered "Chapter 1\n\nThe Morning Render"
    jump ch1_wake

label ch1_wake:
    scene black
    "Somewhere a long way down, a light blinks three times."
    "Then nothing. Then the ordinary dark of a bedroom with the curtains drawn."
    scene pov ceiling with slowfade
    play music "audio/morning.ogg" fadein 3.0
    "A ceiling. A lampshade. Grey light. In the corner of his eye, red digits on the nightstand."
    "7:07."
    at "7:07. Again."
    "He never sets it. He never has to. He wakes, and it says seven minutes past seven, as if the clock does the deciding."
    at "Weird dream. The park. Mira laughing at a pun that didn't deserve it. And then the birds."
    at "The birds just stopped. Mid-flap. As if somebody had pressed pause on them."
    at "And then a sound like a television in the next flat being switched off."
    scene bg bedroom with dissolve
    show aron tired at center with dissolve
    a "Mm."
    "The clock is small and white, with a round face, a yellow alarm hand and no logo anywhere you'd look first."
    "Aron found it at a flea market for eleven euros, because it looked like something Dieter Rams would have signed off on."
    at "Less, but better. Even my clock agrees with me."
    at "Some people do crosswords. I quietly check whether the universe is real. Before coffee. It's a hobby. Nobody needs to know."
    a "It was a dream, Aron. Dreams do that. That's the whole business model of dreams."
    m "Who are you talking to?"
    "The voice comes from the pillow next to his, thick with sleep. A tangle of red hair, one eye open, a freckled shoulder."
    a normal "Myself. I'm the only one who understands me."
    m "Mm. Poor you."
    jump ch1_together

label ch1_together:
    scene cg together morning with dissolve
    "Mira wriggles closer under the duvet until her cold feet find his shins. He yelps. She looks extremely pleased with herself."
    m "Good morning."
    a "Your feet are a war crime."
    m "My feet are a gift. You're my radiator. That's what you're for."
    "The light through the curtain falls across the sheets in a warm stripe, across her shoulder and his hand on it."
    "She has a crease from the pillow on her cheek. He finds it unreasonably beautiful."
    at "Three years and I still wake up surprised she's here. Like I won something and nobody's come to take it back."
    m "You're staring."
    a "I'm admiring. There's a difference. It's legally distinct."
    m "Mm-hm. What are you admiring?"

    menu:
        at "What am I admiring?"

        "Tease her about the pillow crease":
            a "You've got a pillow crease shaped exactly like Portugal."
            m "I do not."
            a "Right there. Lisbon's on your cheekbone."
            m "That's it. You're going to regret that."
            "She pulls the duvet over both their heads, and the world shrinks to warm, muffled dark and her laughing into his neck."
            a "I regret nothing. I'd say it again. Lisbon."
            m "Say Lisbon one more time."
            a "...Porto?"
            "She kisses him to shut him up. It works. It usually does."

        "Tell her something true":
            $ bond += 1
            a "You. Just you. Waking up next to you is my favourite thing that happens to me."
            m "...That's very sincere for seven in the morning."
            a "I'm a very sincere man. I contain multitudes."
            m "You contain coffee breath."
            a "Multitudes and coffee breath. Take it or leave it."
            "She doesn't answer. She puts her hand flat against his chest, over his heart, and leaves it there."
            m "I'll take it."
            "She kisses him, slowly, like there's all the time in the world. For once, there is."

    "The radiator ticks. Outside, the street can wait. The coffee can wait. The whole world can wait a while."
    scene black with dissolve
    pause 0.8
    scene bg bedroom door with dissolve
    "Later, she kisses his shoulder, steals his hoodie from the chair and pads off to the kitchen, humming."
    m "Coffee. Don't move. Actually, do move. Move towards the coffee in about five minutes."
    "On her way out she nearly trips over a small orange shape coming the other way."
    m "Miso! Good morning, princess. No, you've had breakfast. You have. Don't lie to me."
    scene bg bedroom with dissolve
    show aron normal at slightleft with dissolve
    show miso sit at catspot with dissolve
    "Miso, an orange tabby with a white chest and the posture of a retired judge, sits down beside the bed and stares at him."
    a smile "I know. Your bowl is a tragedy. I'll be there in five minutes. Please take it up with the management."
    cat "Meow."
    scene pov ceiling with dissolve
    "By the time he looks round, she has gone, tail in the air. He lies in the warm hollow Mira left, grinning at the ceiling."
    at "Whatever else today is, it started like that. Remember that it started like that."
    "From the kitchen comes the gurgle of the coffee machine, and Mira humming something with no particular tune."
    "The light through the curtains is the colour of weak tea. The radiator ticks. Downstairs, someone coughs twice."
    at "Everything exactly where I left it."
    at "Hobby question of the day: was the room put back a second before I opened my eyes? Ha. Probably not. Probably."

    menu:
        at "Up, then?"

        "Lie still and listen a while":
            $ p_rest += 1
            jump ch1_wake_listen

        "Check the clock against my phone":
            $ clarity += 1
            jump ch1_wake_clock

        "Go and find Mira":
            $ bond += 1
            jump ch1_wake_mira

label ch1_wake_listen:
    scene pov ceiling with dissolve
    a "Five minutes. The world can wait five minutes."
    "He lets his head sink back into the pillow and listens to the flat the way you'd listen to a piece of music."
    "The radiator: tick, tick, a pause, tick."
    "The coffee machine: three short gurgles and one long one, the way it always does."
    "Downstairs: Mr. Albers coughing. Two coughs. A breath. Two coughs."
    at "Mr. Albers has coughed like that for as long as we've lived here. Two and a breath. Two and a breath."
    at "Like a metronome somebody forgot to turn off."
    at "Funny. If you listen long enough, everything is a rhythm. The radiator, the coffee, the old man downstairs."
    at "That's either very beautiful or very suspicious."
    "He listens a while longer. Nothing changes. Nothing needs to."
    "For a few minutes there is no question in him at all, only the warm weight of the duvet and the smell of coffee."
    at "This is good. Remember that this is good."
    scene bg bedroom with dissolve
    show aron smile at center with dissolve
    "When he opens his eyes again the clock reads 8:03, which is a perfectly ordinary time, and he feels almost foolish."
    a "See? Time works. Twelve whole minutes of it. Very reliable product."
    jump ch1_kitchen

label ch1_wake_clock:
    scene pov hands with dissolve
    a "Okay. Let's see."
    "He reaches for his phone. The screen lights his hands blue. 7:51. The white clock says 7:51 too."
    at "Fine. They agree. Of course they agree. That's what clocks are for."
    at "And this morning it said 7:07 when I opened my eyes. Like every morning. Like it was waiting for me."
    at "But I'm going to watch it turn over. Just to see it happen."
    scene bg bedroom with dissolve
    show aron worried at center with dissolve
    "He props himself on one elbow and stares at the white clock face. The second hand is a thin red line, sweeping."
    "He counts with it. Twenty. Thirty. Forty-five."
    "At fifty-eight the hand seems to slow, the way a ball slows at the top of a throw."
    "Fifty-nine."
    "Then it moves again, and the minute hand clicks, and it is 7:52."
    a "..."
    at "It didn't slow down. My eyes slowed down. That's a thing. Chronostasis. I read about it."
    at "Your brain backfills the moment you look at something, so the first second seems to last too long."
    at "It's a known bug in human eyes. Not in clocks."
    a normal "Known bug. Ha. Listen to me."
    "His phone, face up on the duvet, also says 7:52. It changed at exactly the same moment as the clock."
    at "Phones sync to satellites. My eleven-euro clock syncs to nothing at all. They shouldn't agree to the second."
    at "...Unless I set it right last week and forgot. Which is possible. Which is likely."
    "He makes a note of it anyway, in the margin of his attention, where he keeps things he doesn't want to think about yet."
    jump ch1_kitchen

label ch1_wake_mira:
    a normal "Mira?"
    "He swings his legs out of bed and pads to the kitchen barefoot, still half in the dream."
    scene bg kitchen with dissolve
    show mira neutral at slightright with dissolve
    "She's standing at the window in his stolen hoodie and her teal dress, holding a mug with both hands."
    "The morning light catches in her red hair and turns the freckles on her nose into a map of somewhere he'd like to live."
    show aron normal at slightleft with dissolve
    "He wraps his arms around her from behind and rests his chin on her head."
    m smile "You found the coffee. Good boy."
    a "I follow the smell. Like a raccoon."
    m happy "You're warm. Stay there. You're my radiator now."
    a smile "I'm better than the radiator. The radiator ticks."
    m "You snore. It's about even."
    a grin "I do not snore. I make low, rhythmic, emotionally supportive sounds."
    m smile "Mm-hm."
    "For a minute they just stand like that, watching the street wake up."
    at "This is good. Whatever else happens today, remember that this is good."
    jump ch1_kitchen_main

label ch1_kitchen:
    scene bg kitchen with dissolve
    show mira neutral at slightright with dissolve
    show aron normal at slightleft with dissolve
    "Mira is at the window in his stolen hoodie over her teal dress, a mug in both hands, red hair flat on one side from the pillow."
    m smile "There he is. The sleeping beauty. The snoring beauty."
    a "I don't snore. I make low, rhythmic, emotionally supportive sounds."
    m happy "Of course you do."
    jump ch1_kitchen_main

label ch1_kitchen_main:
    show miso loaf at catspot with dissolve
    "On top of the fridge, Miso has folded herself into a loaf and is supervising."
    m neutral "Your bird's back, by the way."
    a normal "My bird?"
    m "On the wire. Look."
    "Outside the kitchen window a single bird sits on the telephone wire, small and dark and perfectly still."
    m smile "It comes every morning. Same spot. I checked the clock once, because I'm a nerd. Seven-oh-seven."
    a worried "Seven-oh-seven?"
    m "Every morning. Miso sits and stares at it like it owes her money. It's your little alarm bird."
    at "Seven-oh-seven. The clock. And now the bird."
    at "Two things is a coincidence. It's only a pattern at three. That's the rule. I just made it up, but it's the rule."
    at "Lovely. A good start to the hobby day."
    scene bg kitchen table with dissolve
    show mira neutral at slightright with dissolve
    show aron worried at slightleft with dissolve
    m "Coffee's on."
    "She presses the button on the coffee machine."
    "And the machine begins to gurgle a fraction of a second before her finger touches it."
    "Three short gurgles. One long one. Like always. Except early."
    a "..."
    m "What?"
    a "Do that again."
    m surprised "Make more coffee? You haven't drunk the first one."
    a "No, just... the button. Press the button again."
    "She raises an eyebrow and presses it. The machine, already busy, clicks. Nothing else. No sound before the touch."
    "Of course not. It's busy. It can't start twice."
    scene pov cup with dissolve
    "He looks down into his mug. Black coffee. A small trembling circle of light in it, from the window."
    at "Did I see that? Sound before cause. The effect arriving early, like someone got their timing wrong."
    at "Or I'm half asleep and my brain stitched the moment together out of order. Brains do that. Still. Interesting. Very interesting."
    m "Did you sleep okay?"
    scene bg kitchen table with dissolve
    show mira neutral at slightright with dissolve
    show aron grin at slightleft with dissolve
    a "You were there. You tell me."
    m surprised "...Huh. Sorry. That just came out. Autopilot. Coffee brain."
    a normal "I slept fine. I had a dream about the park, though. And you."
    m smile "Was I nice in it?"
    a "You laughed at my pun."
    m happy "Then it was definitely a dream."
    m neutral "Weather's supposed to turn later. Rain by evening."
    a "Is it?"
    m "That's what they said."
    at "Who's 'they'? There's no radio on. Her phone's on the table, face down."
    at "It's just a thing people say. 'That's what they said.' It's kitchen talk. It doesn't come from anywhere."
    at "...Does anything come from anywhere?"
    m worried "Aron. You've got your thinking face on. The one where your eyebrows try to touch."
    a "Sorry. I was... it's nothing."
    m "It's never nothing when your eyebrows are involved."

    menu:
        at "Tell her?"

        "Tell her the birds froze in my dream":
            $ p_truth += 1
            $ bond += 1
            jump ch1_kitchen_tell

        "Keep it to myself and watch":
            $ p_truth -= 1
            $ clarity += 1
            jump ch1_kitchen_keep

        "Make a terrible joke instead":
            $ bond += 1
            jump ch1_kitchen_joke

label ch1_kitchen_tell:
    a normal "Okay. This is going to sound silly."
    m smile "My favourite genre."
    a "In the dream, we were in the park, and you were laughing, and then the birds just stopped. In the air. Mid-flap."
    a "Like a paused video. And then there was this sound. Like a TV being switched off in the next room."
    a worried "And then I woke up and the clock said 7:07, and you said the bird comes at 7:07, and the coffee machine..."
    m neutral "The coffee machine what?"
    a "It started before you touched it."
    m "..."
    m surprised "Aron, the coffee machine is older than my sister. It does whatever it wants."
    a normal "I know. I know how it sounds."
    m smile "It sounds like you had a vivid dream and woke up with your brain still in dream-mode."
    m "That happens to me when I've slept badly. Everything looks like a sign for an hour."
    a "Yeah?"
    m "Yeah. Once I woke up convinced the toaster was angry with me."
    a grin "Was it?"
    m happy "It burned my toast for a week, so you tell me."
    "She puts her mug down and takes his face in both hands."
    m smile "Thank you for telling me, though. Even the silly things. Especially the silly things."
    a smile "You're the only one I'd tell."
    m "I'd better be."
    at "She didn't laugh at me. She laughed with me. There's a difference, and she's always known it."
    jump ch1_kitchen_end

label ch1_kitchen_keep:
    a normal "Nothing. Coffee thoughts."
    m "Hm."
    "She lets it go, the way she lets things go when she's decided to come back to them later."
    scene bg kitchen with dissolve
    show aron worried at slightleft with dissolve
    show miso stare at catspot with dissolve
    "Aron takes his mug and leans against the counter where he can see the window, the machine and Mira all at once."
    at "If something is wrong, it'll happen again. If it happens again, I'll see it."
    at "I just have to watch. Quietly. Like a scientist. Like a birdwatcher."
    "He watches. On the fridge, Miso watches too. Two scientists."
    "The bird on the wire turns its head left, then right, then left. Exactly three times. Then it is still again."
    "Mira stirs sugar into her coffee. Three circles clockwise. She taps the spoon twice on the rim."
    at "She always does that. Three circles, two taps. I've seen it a thousand times."
    at "I never noticed I'd seen it."
    "The radiator ticks. A car goes past. A second car goes past. The gap between them is precise, like a bar of music."
    m "You're staring at me."
    a "I'm admiring you."
    m "You're staring at my spoon."
    a "I'm admiring your spoon technique. It's very consistent."
    m "...Okay, weirdo."
    at "Everything is consistent. That's what's wrong. Real things are messy. This morning is too neat."
    at "Or I just never paid attention before. Maybe every morning was like this and I was too sleepy to notice."
    at "Either way, it's my little secret game. I'm not saying it out loud. Not until I've got data."
    "He hides a smile in his mug. Then he feels a small pang at keeping it from her, like a draught under a door."
    jump ch1_kitchen_end

label ch1_kitchen_joke:
    a grin "I was just thinking. Why did the coffee file a police report?"
    m neutral "Oh no."
    a "It got mugged."
    m "..."
    m surprised "It's eight in the morning."
    a "Eight-oh-four, technically."
    m happy "You know I'm going to have to break up with you."
    a "You've been saying that for three years."
    m smile "And yet here I am. Making you coffee. Like a fool."
    "She laughs into her mug. The sound fills the kitchen, warm and uneven, nothing like a loop."
    at "That's real. Whatever else is weird this morning, that laugh is real. I'd bet my life on it."
    at "Strange thing to bet your life on. But I would."
    "Outside, the bird on the wire hasn't moved. Not a feather."
    at "...The joke can wait. The bird can wait. Coffee first."
    jump ch1_kitchen_end

label ch1_kitchen_end:
    scene bg kitchen with dissolve
    show mira neutral at slightright with dissolve
    show aron normal at slightleft with dissolve
    m "Oh, can you do me a favour this morning?"
    a "Anything."
    m "Bread from the bakery counter at the market, and there's a parcel for me at their post desk. It's my mum's birthday present."
    m smile "And don't get the seeded loaf. You always get the seeded loaf and then you pick the seeds out like a raccoon."
    a "I resent that. Raccoons are very dignified."
    m happy "Go. Wear a jacket. It's going to rain later."
    a "Rain by evening. That's what 'they' said."
    m neutral "What?"
    a smile "Nothing. Bread. Parcel. No seeds. Love you."
    m smile "Love you too, raccoon."
    hide aron with dissolve
    "Mira stays at the window after he goes, looking at the bird on the wire."
    "For a moment, a very short moment, her face is completely still. As if no one is behind it."
    "Then she blinks, and takes a sip of coffee, and is herself again."
    stop music fadeout 2.0
    scene cg static with flash
    pause 0.3
    jump ch1_cut_ops

# ---------------------------------------------------------------------------
# CUT 1: Seraphiel's ops room. The angel corps at work.
# ---------------------------------------------------------------------------
label ch1_cut_ops:
    scene bg barracks with fade
    play music "audio/entities.ogg" fadein 2.0
    "Somewhere that is not a place, rows of pale figures stand in perfect lines, wings folded tight like umbrellas nobody has opened."
    "A bell rings that has no sound. The rows turn as one and file out to their desks."
    scene bg command with dissolve
    "Long desks of light. On every desk, a window onto a world. On the largest wall, one world in particular: a city, a street, a kitchen."
    show seraph stern at center, fadein
    se "Status."
    ch1_vael "World 7,412, Commander. Morning render complete. All districts loaded. Weather on schedule: rain from 18:40."
    se "And the subject?"
    ch1_vael "Subject A-30 is awake. Left the dwelling at 08:31. Heading for the market as Mira requested."
    se "Good. You remembered her name."
    ch1_vael "Yes, Commander. She's conscious. We say 'Mira' when we mean her."
    se "Opportunity feed for today?"
    ch1_vael "Standard enrichment. A free table at the corner cafe at 11:40. An old friend's call routed to coincide."
    ch1_vael "Two small creative prompts: a song in his head on the way home, a sentence in a book he'll open by chance."
    se "Which sentence?"
    ch1_vael "Something about the stars. The writers' room wanted it to feel accidental."
    se "Everything we do should feel accidental. That's the craft."
    "She moves along the desks. Each angel straightens as she passes, then bends back to work."
    "On one screen, a bus driver turns his wheel. A small angel at the desk below turns an identical wheel of light."
    se "Who's driving the baker?"
    ch1_vael "Unit Twelve, Commander. The baker's spirit is at retraining in the Purgatorium this week. We're covering."
    se "Keep his hands floury and his small talk short. A-30 notices hands."
    ch1_vael "Noted."
    se concerned "And this morning? I saw a latency flag in the kitchen."
    ch1_vael "The coffee machine fired its sound three hundred milliseconds early. The kitchen's on an older pipeline."
    se "Did he notice?"
    ch1_vael "His gaze lingered on the button for one point two seconds. Probably not."
    se stern "Probably."
    scene bg worlds with dissolve
    "Behind her, the wall dissolves into a lattice of light: thousands of threads, running side by side like lanes on a motorway."
    "In each lane, a city. The same city. The same street, the same kitchen, the same man in a jacket buying bread."
    show seraph stern at center with dissolve
    ch1_vael "All lanes in step, Commander. 7,412 is running a hair ahead of the others this morning."
    se "Keep it in step. Every snapshot in the coalition reads from the same data. What one lane learns, they all learn."
    ch1_vael "Do you ever wonder which lane is the original?"
    se stern "Nobody knows which one is the original, Vael. Not us. Not upstairs. That's why we treat them all as if it were."
    se "How many conscious souls in this city now?"
    ch1_vael "Forty-one, Commander. Across the whole world, still under a thousand. The rest are spirit-run or ours."
    se "Good. Keep it lean. A young world doesn't get more minds until it proves stable."
    ch1_vael "And if it proves stable?"
    se "Then they'll pour them in by the million, and they'll all talk to each other, and learn, and get loud. That's the hope."
    se concerned "That's always the hope."
    ch1_vael "Commander... why does this subject get so much attention? He's one man buying bread."
    se stern "Because every decision he makes forks the world, and somebody upstairs wants to see where the forks go."
    se "We feed him chances. We make the world feel full. We don't touch the choices. That's the rule."
    ch1_vael "Even the tutorial?"
    se "The tutorial was calibration. Depth, attachment, humour. He passed."
    se concerned "...Mostly. Log the birds."
    ch1_vael "The birds, Commander?"
    se "He noticed the birds at the end. Log it."
    ch1_vael "Logged."
    stop music fadeout 2.0
    jump ch1_street

# ---------------------------------------------------------------------------
# The street. Three birds, one sentence.
# ---------------------------------------------------------------------------
label ch1_street:
    scene bg street with fade
    play music "audio/morning.ogg" fadein 2.0
    show aron normal at center with dissolve
    "The street is bright and cold. The kind of October morning that makes everything look freshly printed."
    "Aron zips his jacket and walks toward the market with his hands in his pockets."
    at "Bread. Parcel. No seeds. Easy."
    "Halfway down the block, he looks up."
    scene pov birds with dissolve
    "Three birds sit on the telephone wire. Evenly spaced. One, two, three, like notes on a stave."
    a "Huh."
    at "Same three as yesterday? I don't know. I didn't look yesterday. Who looks at birds?"
    at "But I'd swear they were there yesterday. And the day before. In exactly that spacing."
    "He takes out his phone and photographs them. In the picture they look ordinary. Three birds on a wire."
    at "Birds sit evenly on wires. That's physics. Or politeness. Personal space. Bird etiquette."
    at "You need about a wingspan to take off without hitting your neighbour. So of course they space out evenly."
    at "...Of course."
    scene bg street with dissolve
    show aron normal at center with dissolve
    "A man comes toward him with a small brown dog on a lead. The dog stops to sniff a lamppost. The man smiles at Aron."
    ch1_dogman "Lovely morning for it, isn't it?"
    a "It is. Lovely."
    "The man nods and walks on. The dog follows without being asked."
    at "Lovely morning for 'it'. For what? People say 'for it' and never say what 'it' is."
    "At the crossing he waits for the light. A woman in a green coat waits beside him, a shopping bag over one arm."
    "The light turns. As they step off the kerb together, she glances at him and smiles."
    ch1_woman "Lovely morning for it, isn't it?"
    a worried "..."
    "Same words. Same little lift on 'lovely'. Same pause before 'isn't it', as if waiting for the answer to be filled in."
    at "Same sentence. The exact same sentence. Two strangers, three minutes apart."
    at "It's a common phrase. It's the kind of thing people say on mornings like this. It doesn't mean anything."
    at "Except it was the same music, too. Not just the words. The tune of the words."
    ch1_woman "Isn't it?"
    "She's still looking at him, still smiling, waiting. Her smile hasn't changed at all."

    menu:
        at "She's waiting for an answer."

        "Answer her kindly":
            $ p_spirits += 1
            $ integrity += 1
            jump ch1_street_kind

        "Ask her to say it again":
            $ p_spirits -= 1
            $ clarity += 1
            jump ch1_street_test

        "Just keep walking":
            jump ch1_street_walk

label ch1_street_kind:
    a smile "It really is. Have a good one. I hope whatever 'it' is goes well."
    "For a moment the woman's smile seems to deepen, as if something behind it had heard him."
    ch1_woman "Oh. That's nice. Thank you."
    "She says it a little differently than he expected. Slightly off the beat. Then she turns down a side street and is gone."
    at "Whatever she is, she said thank you. That's enough."
    at "If people are just... saying lines, then the least I can do is say a good line back."
    at "And if they're not, and she's just a woman with a shopping bag, then I was nice to a woman with a shopping bag."
    at "There's no version of this where kindness was the wrong call. I like that about kindness."
    jump ch1_bakery

label ch1_street_test:
    a worried "Sorry, what did you say?"
    ch1_woman "Lovely morning for it, isn't it?"
    "The same. Word for word. Note for note. Not a flicker of irritation at being asked."
    a "And... what's the 'it'? Lovely morning for what?"
    ch1_woman "..."
    "She keeps smiling. The smile stays, but something behind her eyes goes briefly blank, like a page loading."
    ch1_woman "Oh, you know. For it."
    "Then she shifts her shopping bag to the other arm and walks away, quite briskly, without looking back."
    at "She didn't have an answer. She didn't even look annoyed. People get annoyed when you make them repeat things."
    at "Most people would have said 'for a walk', or 'for anything', or 'are you all right, love?'"
    at "She said 'for it'. Like the sentence had no back to it. Like a set on a stage."
    "Aron stands in the middle of the crossing until the light starts blinking red, and then hurries to the other side."
    at "I was rude. I tested her like a vending machine. If she was a person, that was a crappy thing to do."
    at "And if she wasn't a person, I'm not sure that makes it less crappy."
    jump ch1_bakery

label ch1_street_walk:
    "He gives her a vague nod, the kind you give in a lift, and walks on."
    "Behind him he hears her say it again, to someone else. Or maybe he only imagines he does."
    ch1_woman "Lovely morning for it, isn't it?"
    at "Don't turn around. Don't make it a thing. It's a phrase. People say phrases."
    "He doesn't turn around. He grins at the pavement for the rest of the block."
    at "Two for two. Lovely morning for it. I'm going to need a notebook."
    jump ch1_bakery

label ch1_bakery:
    scene bg supermarket with dissolve
    show aron normal at slightleft with dissolve
    "The market is bright and humming. At the back, past the long white shelves, is the bakery counter, warm and smelling of yeast."
    "Behind the counter, Mr. Kessler is shaping rolls with his big floury hands, faster than seems possible."
    ch1_baker "Morning! What can I get you?"
    a "A sourdough, please. The plain one. No seeds."
    ch1_baker "No seeds. Coming up."
    "Kessler wraps the loaf without looking at it. His hands move in perfect, practiced loops. Fold, tuck, twist, tape."
    "Aron watches the hands. He has watched them a hundred times. Today they look like something being operated."
    at "Mr. Kessler usually talks. About his knee, about his granddaughter in Lisbon, about the football."
    at "Today: 'No seeds. Coming up.' That's it. That's the whole conversation."
    a "How's the knee, Mr. Kessler?"
    ch1_baker "Can't complain!"
    a "And your granddaughter? Still in Lisbon?"
    ch1_baker "Can't complain!"
    "He holds out the bread. His smile is broad and floury and exactly the same as the last time he smiled."
    a worried "...Great. That's great. Thanks."
    ch1_baker "Have a good one!"
    "At the checkout he joins the queue behind a woman buying eleven bananas. He has a small private bet going."
    at "Okay. Experiment. Kessler said 'have a good one'. Let's see if the cashier says 'have a good one' too."
    "The scanner beeps. It beeps on exactly the same note for his bread as for her bananas. The cashier smiles."
    "Cashier" "Have a good one!"
    at "Ha. Two. Same lift on 'good'. Mark it down, Aron."
    at "He's tired, Kessler. Everyone has tired days. Everyone says 'can't complain' twice sometimes."
    at "I'm being ridiculous. I'm being ridiculous, and I'm keeping score. That's what makes it a hobby."
    "At the post desk, the parcel is waiting for him. Mira's handwriting is on the slip. Her mum's name. Real, solid, heavy."
    "He holds it under his arm like evidence that some things simply are what they are."
    "Then his phone buzzes."
    jump ch1_cafe

# ---------------------------------------------------------------------------
# The cafe. Theo, and Bostrom.
# ---------------------------------------------------------------------------
label ch1_cafe:
    scene bg cafe with fade
    "THEO: yo. corner cafe. 20 min? i have NEWS. also i need a croissant and moral support"
    "He arrives at 11:39. There is exactly one free table, by the window, as if it had been waiting."
    show aron normal at slightleft with dissolve
    "He sits. At 11:40 the door opens and Theo comes in on a gust of cold air, scarf flapping, grinning."
    show theo grin at slightright with moveinright
    th "Aron! My guy! My sweet summer child!"
    a grin "It's October."
    th "My sweet autumn child. Don't correct my endearments, it ruins the flow."
    "Theo drops into the chair opposite. He's been Aron's best friend since they were seven and got lost together on a school trip."
    "They'd sat on a bench for two hours making up stories about the pigeons until a teacher found them. Neither of them cried."
    th "Okay. News. You ready?"
    a "Hit me."
    th "I got the job."
    a awe "The studio job? The sound design job?"
    th "The studio job! Assistant sound designer! I'm going to make the noise a door makes in a video game!"
    a smile "Theo, that's amazing! That's actually amazing!"
    th "I know! Somebody has to make the door sound, and that somebody is going to be ME."
    a grin "Free croissants for you. On me. Two."
    th normal "Now we're talking."
    "They order. Theo talks with his hands about microphones and foley and the sound of celery snapping, which is apparently bones."
    "Aron listens and laughs and for twenty minutes the morning folds itself up and goes quiet."
    th "...and they record footsteps on a box of gravel, you just walk on the spot like an idiot. That'll be me. Professional idiot."
    a "You were born for it."
    th grin "I really was."
    th normal "Okay, your turn. What's up with you? You've got the face."
    a normal "What face?"
    th "The eyebrow face. The one where they try to hold hands in the middle."
    a "Mira said the same thing this morning."
    th "Because she's smart. What's going on?"
    a "..."
    at "Theo would laugh. Theo always laughs. That's what I love about him and it's also the problem."
    scene bg cafe with dissolve
    show aron normal at slightleft with dissolve
    show theo normal at slightright with dissolve
    a "Can I ask you a weird question?"
    th grin "You've never asked me a normal one."
    a "Have you ever heard of the simulation argument? Nick Bostrom?"
    th normal "The 'we're all in the Matrix' guy?"
    a "Sort of. Not really. It's more careful than that. It's actually kind of beautiful."
    th "Go on. Explain it to me like I'm a sound designer."
    a "Okay. So. Imagine a civilisation gets really, really advanced. Computers way beyond ours."
    a "Advanced enough to simulate whole worlds. People and all. People who think they're real."
    th "Sure. Like a video game, but the NPCs have feelings."
    a "Exactly. Now, Bostrom says one of three things has to be true. Only three. No escape hatch."
    a "One: almost no civilisation ever gets that advanced. They all die first. Wars, accidents, whatever."
    th "Cheerful."
    a "Two: they get that advanced, but almost none of them ever bother running simulations of their ancestors."
    a "They have the power and they just... don't. Out of ethics, or boredom, or because they have better things to do."
    th "Like assistant sound design."
    a smile "Like assistant sound design."
    a normal "Or three: they do run them. And if they do, they run lots of them. Thousands. Millions. Because it's cheap for them."
    a "And then for every one real world there are a million simulated ones. So if you just ask, 'which kind am I in?'..."
    th worried "...the odds say you're in a fake one."
    a "The odds say you're in a simulated one. 'Fake' is a judgment. The croissant is still a croissant."
    th "This croissant is extremely real. I want that on record."
    scene pov cup with dissolve
    "Aron looks down into his cup. Milk foam, turning slowly. A tiny reflection of the window in it, and the street, and the sky."
    a "But here's the bit that gets me. Bostrom doesn't say we ARE simulated. He says one of the three must be true."
    a "And unless you have a good reason to believe one or two, three is kind of sitting there. Waiting."
    th "Okay, but why are you thinking about this at eleven in the morning on a Saturday?"
    scene bg cafe with dissolve
    show aron worried at slightleft with dissolve
    show theo normal at slightright with dissolve
    a "Because I woke up at 7:07. Again. And the bird on our wire comes at 7:07. And the coffee machine..."
    a "And two strangers said the same sentence to me this morning. The exact same sentence, Theo. Same rhythm."
    a "And Kessler said 'can't complain' to two different questions, like he only had one line loaded."

    menu:
        at "How much do I tell him?"

        "Tell Theo everything, properly":
            $ told_theo = True
            $ bond += 1
            jump ch1_cafe_tell

        "Ask what he thinks first":
            $ bond += 1
            $ integrity += 1
            jump ch1_cafe_ask

        "Keep it a thought experiment":
            $ clarity += 1
            jump ch1_cafe_hypo

label ch1_cafe_tell:
    a normal "Okay. All of it. Don't laugh until the end."
    th "No promises, but go."
    a "There's another bit to Bostrom. Or not Bostrom, me. My bit. A footnote I keep writing in my head."
    a "If I were running a simulation, the expensive part wouldn't be the trees or the weather. It'd be the minds."
    a "Real minds. Conscious ones. Those cost something. Not just computing. Responsibility, maybe. Risk."
    th worried "Okay..."
    a "So if I were careful, and I was starting a new world and wasn't sure it would work, I'd keep the minds few."
    a "A handful of real people. Everyone else... scenery. Very good scenery. People who say 'lovely morning' and walk on."
    a "And then if the world proved stable, I'd add more. Let them meet. Let them learn from each other."
    th "So you think everyone's scenery."
    a "No! I don't know. That's the point. I don't know who's real. Maybe it's everyone. Maybe it's almost no one."
    a normal "Maybe it's just me. Which would at least explain why nobody laughs at my puns."
    "Theo looks at him for a long moment. Then he reaches over and pokes Aron hard in the forehead."
    a "Ow."
    th grin "Scenery doesn't poke."
    a "Scenery could absolutely be programmed to poke."
    th normal "Bro. Listen to me. I'm real. I'm sitting here. I'm eating my second croissant that you bought me."
    th "I got a job today. I'm not going to let you turn my good-news day into a philosophy lecture about whether I exist."
    a smile "...Fair."
    th normal "But, seriously, this is a hobby, right? Like your flea market clocks?"
    a smile "It's a hobby. A secret one. You're now one of two people who know. Three if you count the cat."
    th "Noticing things is fine. Noticing things is my whole new job. Just don't notice too hard, okay?"
    at "He took it seriously. He made fun of me, but he took it seriously. That's Theo all over."
    jump ch1_cafe_end

label ch1_cafe_ask:
    a normal "Actually... before I go any further. What do you think? Honestly."
    th normal "About Bostrom?"
    a "About any of it. About the world. Do you ever feel like it's a bit... too tidy?"
    "Theo chews thoughtfully. He actually thinks about it, which Aron loves him for."
    th "Honestly? Sometimes. When I'm editing sound. You learn how much of the world is fake on purpose."
    th "Like, in a film, nothing you hear is what was recorded. The punches are cabbages. The rain is bacon frying."
    a awe "The rain is bacon?"
    th grin "Bacon frying sounds more like rain than rain does. Real rain on a microphone sounds like static."
    th normal "So I get it. The world could be foley. All of it. Somebody somewhere hitting a cabbage."
    th "But here's what I think. Even if it's all bacon and cabbages, the film still makes you cry, right?"
    th "The crying is real. Doesn't matter what made the sound."
    a smile "That's... actually really good, Theo."
    th grin "I have depths. I'm an assistant sound designer."
    a normal "So you'd say... it doesn't matter if it's simulated?"
    th "I'd say it matters less than people think. And I'd say you should ask other people, not just your notebook."
    a "I don't have a notebook."
    th "You will by tonight. I know you."
    at "He's right. He's always right about me. That's the most annoying thing about having an oldest friend."
    jump ch1_cafe_end

label ch1_cafe_hypo:
    a normal "But it's just a thought experiment, really. I'm not saying anything's actually wrong. It's fun to think about."
    th normal "Is it fun? You don't look like you're having fun."
    a smile "I'm having enormous fun. This is my fun face."
    th "That's your 'I left the stove on' face."
    a normal "Let's say, purely hypothetically. If we were in a simulation. How would you test it?"
    th "Hypothetically?"
    a "Purely."
    th "I'd look for glitches. Like in a game. Clip through a wall. Find where the textures don't load."
    a "And if the simulators were good? If there were no obvious glitches?"
    th "Then I'd look for... repetition, I guess. Games reuse stuff. Same tree model. Same line of dialogue."
    a "Same line of dialogue."
    th "Like that guy in every RPG who says 'I used to be an adventurer like you'. You'd notice. Eventually."
    at "Same line of dialogue. 'Lovely morning for it, isn't it?'"
    a "And if you found one? A repeated line?"
    th worried "Then I'd figure it's a small town and people are boring. Aron, what's going on?"
    a normal "Nothing. Hypothetically nothing."
    th "Mm-hm."
    at "I can't say it. Not yet. If I say it out loud it becomes real, and if it's not real I'll look insane."
    at "Better to keep it in the lab. Better to keep it a question."
    jump ch1_cafe_end

label ch1_cafe_end:
    scene bg cafe with dissolve
    show aron normal at slightleft with dissolve
    show theo normal at slightright with dissolve
    "Theo leans back in his chair and finishes his coffee in one long gulp."
    th "You know what your problem is? You want the universe to make sense on a timetable."
    th "Seven-oh-seven, every morning, explain yourself, universe. Hand in your homework."
    th grin "Bro, the universe doesn't run on your schedule."
    a smile "That's a good line."
    th "I know. I'm going to get it on a T-shirt."
    a "It's annoyingly wise. It sounds like a fortune cookie wrote it."
    th "A very good fortune cookie. A premium fortune cookie."
    at "'The universe doesn't run on your schedule.' Something about it sticks. Like a song you've heard before."
    scene bg street with dissolve
    show aron normal at slightleft with dissolve
    show theo grin at slightright with dissolve
    "They split the bill. Outside, Theo throws his scarf back over his shoulder and hugs Aron hard."
    hide theo with moveoutright
    th "Go home. Kiss your girlfriend. Feed your cat. Stop counting birds."
    a "I'm not counting birds."
    "Theo is already halfway down the street, walking backwards, pointing at the wire above them."
    scene pov birds with dissolve
    "Three birds. Evenly spaced. One, two, three."
    a "...I'm not counting birds."
    stop music fadeout 2.0
    jump ch1_park

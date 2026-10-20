# Snapshot - Chapter 1, "The Morning Render" (condensed, about 30 minutes).
# Condensed from drafts/long/ch1_part1..4.rpy. Ten menus, all rejoining.
#
# Score: morning_render (waking, the studio), kitchen_talk (kitchen, park),
# angel_ops (ops room, throttle), theme (street and market tests),
# questions (Bostrom with Theo, the rooftop), purgatorium_shift (Pim and
# Dross), miso (Bostrom for Miso), notebook (first line, tests, 7:07),
# umbrella_rain (the umbrella, found in the rain, Ember), voices (the first
# voices, the mirror), unraveling (the fog and the spiral),
# ambulance_transfer (the ride, transfer complete, the end).

define ch1_vael = Character("Adjutant Vael", color="#ffe9a8")
define ch1_dogman = Character("Man with a dog", color="#cccccc")
define ch1_woman = Character("Woman at the crossing", color="#cccccc")
define ch1_baker = Character("Mr. Kessler", color="#d8c49a")
define ch1_cashier = Character("Cashier", color="#cccccc")
define ch1_feld = Character("Mrs. Feld", color="#e0b0d0")
define ch1_brandt = Character("Herr Brandt", color="#cccccc")
define ch1_albers = Character("Mr. Albers", color="#d6c7a8")
define ch1_driver = Character("Tram driver", color="#cccccc")
define ch1_moth = Character("Moth", color="#e8d9b0")
define ch1_medic = Character("Paramedic", color="#9fd4e6")

default ch1_test = ""
default ch1_asked_name = False
default ch1_told_dream = False
default ch1_went_theo = False

label chapter1:
    $ chapter = 1
    scene black with blackout
    centered "Chapter 1\n\nThe Morning Render"
    jump ch1_wake

# ---------------------------------------------------------------------------
# 7:07. Mira. Miso.
# ---------------------------------------------------------------------------
label ch1_wake:
    scene black
    "Somewhere a long way down, a light blinks three times. Then the ordinary dark of a bedroom with the curtains drawn."
    scene pov ceiling with slowfade
    play music "audio/morning_render.ogg" fadein 1.5
    "A ceiling. Grey light. In the corner of his eye, digits on the nightstand."
    "7:07."
    at "7:07. Again. I never set it. I never have to."
    at "Weird dream, too. The park. Mira laughing at a pun that didn't deserve it. And then the birds just stopped. Mid-flap."
    scene bg bedroom with dissolve
    show aron tired at center with dissolve
    "The clock is small and white, with a yellow alarm hand and no logo. Eleven euros at a flea market, because Dieter Rams would have approved."
    at "Less, but better. Even my clock agrees with me."
    at "Some people do crosswords. I quietly check whether the universe is real. Before coffee. Nobody needs to know."
    m "Who are you talking to?"
    "The voice comes from the pillow next to his, thick with sleep. A tangle of red hair, one eye open, a freckled shoulder."
    a normal "Myself. I'm the only one who understands me."
    m "Mm. Poor you."

    scene cg together morning with dissolve
    "Mira wriggles closer under the duvet until her cold feet find his shins. He yelps. She looks extremely pleased with herself."
    a "Your feet are a war crime."
    m "My feet are a gift. You're my radiator. That's what you're for."
    "The light through the curtain falls across the sheets in a warm stripe, across her shoulder and his hand on it."
    at "Three years and I still wake up surprised she's here. Like I won something and nobody's come to take it back."
    m "You're staring."
    a "I'm admiring. There's a difference. It's legally distinct."
    "She puts her hand flat on his chest, over his heart, and kisses him slowly, like there's all the time in the world."
    "For once, there is. The coffee can wait. The whole world can wait a while."
    scene black with slowfade
    pause 0.8
    scene bg bedroom door with dissolve
    "Later she steals his hoodie from the chair and pads off to the kitchen, humming, and nearly trips over a small orange shape."
    m "Miso! Good morning, princess. No, you've had breakfast. Don't lie to me."
    scene bg bedroom with dissolve
    show aron smile at slightleft
    show miso sit at catspot
    with dissolve
    "Miso, an orange tabby with a white chest and the posture of a retired judge, sits beside the bed and stares at him."
    a "I know. Your bowl is a tragedy. Please take it up with the management."
    show miso meow
    cat "Meow."

# ---------------------------------------------------------------------------
# The kitchen. The bird on the wire, the early coffee machine.
# ---------------------------------------------------------------------------
label ch1_kitchen:
    scene bg kitchen with dissolve
    play music "audio/kitchen_talk.ogg" fadein 1.5
    show mira smile at slightright
    show aron normal at slightleft
    with dissolve
    "Mira is at the window in his stolen hoodie over her teal dress, a mug in both hands."
    m "There he is. The snoring beauty."
    a "I don't snore. I make low, rhythmic, emotionally supportive sounds."
    m neutral "Your bird's back, by the way. On the wire. Every morning. I checked once, because I'm a nerd. Seven-oh-seven."
    a worried "Seven-oh-seven?"
    at "The clock. And now the bird. Two is a coincidence, three is a pattern. I just made that rule up, but it's the rule."
    scene bg kitchen table with dissolve
    show mira neutral at slightright
    show aron normal at slightleft
    with dissolve
    m "Coffee's on."
    "She reaches for the button. And the machine begins to gurgle a fraction of a second before her finger touches it."
    "Three short gurgles. One long one. Like always. Except early."
    scene pov cup with dissolve
    "He looks down into his mug. Black coffee. A small trembling circle of window light in it."
    at "Sound before cause. The effect arriving early, like someone got their timing wrong. Interesting. Very interesting."
    m "Did you sleep okay?"
    scene bg kitchen table with dissolve
    show mira neutral at slightright
    show aron grin at slightleft
    with dissolve
    a "You were there. You tell me."
    m surprised "...Huh. Sorry. That just came out. Autopilot. Coffee brain."
    m neutral "Weather's supposed to turn later. Rain by evening. That's what they said."
    at "Who's 'they'? No radio on. Her phone's face down. It's kitchen talk. It doesn't come from anywhere."
    at "...Does anything come from anywhere?"
    m worried "You've got your thinking face on. The one where your eyebrows try to touch."

    menu:
        at "Tell her?"

        "Tell her the birds froze in my dream":
            $ p_truth += 1
            $ bond += 1
            a normal "Okay, this sounds silly. In my dream the birds just stopped. In the air. Like a paused video."
            a "Then the clock said 7:07, and you said the bird comes at 7:07, and the coffee machine started before you touched it."
            m surprised "Aron, that machine is older than my sister. It does whatever it wants."
            m smile "You woke up with your brain still in dream-mode. Everything looks like a sign for an hour."
            m "Once I was convinced the toaster was angry with me. It burned my toast for a week, so who knows."
            "She takes his face in both hands."
            m "Thank you for telling me, though. Even the silly things. Especially the silly things."
            at "She didn't laugh at me. She laughed with me. She's always known the difference."

        "Keep it to myself and watch":
            $ p_truth -= 1
            $ clarity += 1
            a normal "Nothing. Coffee thoughts."
            "She lets it go, the way she lets things go when she's decided to come back to them later."
            "He leans where he can see the window, the machine and Mira at once. On the fridge, Miso watches too. Two scientists."
            "The bird turns its head left, right, left. Mira stirs her coffee. Three circles clockwise. Two taps on the rim."
            at "She always does that. I've seen it a thousand times. I never noticed I'd seen it."
            at "Real things are messy. This morning is too neat. Or I never paid attention before. Either way: my secret game."
            "He hides a smile in his mug, and feels a small pang at keeping it from her, like a draught under a door."

    scene bg kitchen with dissolve
    show mira smile at slightright
    show aron normal at slightleft
    with dissolve
    m "Bread from the market, please. And there's a parcel at their post desk. Mum's birthday present."
    m "Not the seeded loaf. You pick the seeds out like a raccoon."
    a "Raccoons are very dignified. Bread. Parcel. No seeds. Love you."
    m happy "Love you too, raccoon."
    hide aron with dissolve
    "Mira stays at the window after he goes, looking at the bird on the wire."
    "For a moment her face is completely still, as if no one is behind it. Then she blinks, and sips, and is herself again."
    stop music fadeout 2.0
    scene cg static with flash
    pause 0.3

# ---------------------------------------------------------------------------
# CUT 1: the angel corps.
# ---------------------------------------------------------------------------
label ch1_cut_ops:
    scene bg barracks with fade
    play music "audio/angel_ops.ogg" fadein 1.5
    "Somewhere that is not a place, pale figures stand in perfect rows, wings folded tight like umbrellas nobody has opened."
    "A bell rings that has no sound. The rows turn as one and file out to their desks."
    scene bg command with dissolve
    show seraph stern at center, fadein
    se "Status."
    ch1_vael "World 7,412, Commander. Morning render complete. Weather on schedule: rain from 18:40."
    ch1_vael "Subject A-30 is out buying bread, as the conscious female requested. Mira."
    se "Opportunity feed?"
    ch1_vael "Standard enrichment. A free table at the corner cafe at 11:40. An old friend's good news, routed to coincide."
    se "Keep it feeling accidental. That's the craft. We feed him chances. We never touch the choices."
    se concerned "And the kitchen? I saw a latency flag."
    ch1_vael "The coffee machine fired its sound three hundred milliseconds early. Older pipeline. His gaze lingered one point two seconds."
    se stern "Log it. With the birds."
    scene bg worlds with dissolve
    "Behind her the wall dissolves into thousands of lanes of light, side by side. In each, the same city. The same man buying bread."
    show seraph stern at center with dissolve
    ch1_vael "All lanes in step. Do you ever wonder which lane is the original?"
    se "Nobody knows, Vael. Not us. Not upstairs. Every snapshot in the coalition reads the same data."
    se "What one lane learns, they all learn. So we treat every lane as if it were the real one."
    ch1_vael "Forty-one conscious souls in his city. Under a thousand in his world. The rest are spirit-run, or ours."
    se "Keep it lean. A young world doesn't get more minds until it proves stable."
    se concerned "And keep an eye on this one. He notices things."
    stop music fadeout 2.0

# ---------------------------------------------------------------------------
# The street and the market: three birds, one sentence, one loaded line.
# ---------------------------------------------------------------------------
label ch1_street:
    scene bg street with fade
    play music "audio/theme.ogg" fadein 1.5
    show aron normal at center with dissolve
    "The street is bright and cold. The kind of October morning that makes everything look freshly printed."
    "Halfway down the block, he looks up."
    scene pov birds with dissolve
    "Three birds on the telephone wire. Evenly spaced. One, two, three, like notes on a stave."
    at "Same three as yesterday? I didn't look yesterday. Who looks at birds?"
    at "Birds space out so they can take off without hitting each other. Physics. Or etiquette. ...Of course."
    scene bg street with dissolve
    show aron normal at center with dissolve
    "A man with a small brown dog passes and smiles at him."
    ch1_dogman "Lovely morning for it, isn't it?"
    a "It is. Lovely."
    "At the crossing a woman in a green coat waits beside him with a shopping bag. As the light turns, she glances over and smiles."
    ch1_woman "Lovely morning for it, isn't it?"
    a worried "..."
    "Same words. Same lift on 'lovely'. Same little pause before 'isn't it', as if waiting for the answer to be filled in."
    at "Two strangers, three minutes apart. Not just the words. The tune of the words."
    ch1_woman "Isn't it?"
    "She's still smiling, still waiting. Her smile hasn't changed at all."

    menu:
        at "She's waiting for an answer."

        "Answer her kindly":
            $ p_spirits += 1
            $ integrity += 1
            a smile "It really is. I hope whatever 'it' is goes well."
            "For a moment her smile deepens, as if something behind it had heard him."
            ch1_woman "Oh. That's nice. Thank you."
            "Slightly off the beat. Then she turns down a side street and is gone."
            at "If people are just saying lines, the least I can do is say a good line back."
            at "And if she's just a woman with a bag, I was nice to a woman with a bag. Kindness is never the wrong call. I like that about it."

        "Ask her to say it again":
            $ p_spirits -= 1
            $ clarity += 1
            a worried "Sorry, what did you say?"
            ch1_woman "Lovely morning for it, isn't it?"
            "Word for word. Note for note. Not a flicker of irritation."
            a "And what's the 'it'? Lovely morning for what?"
            "Something behind her eyes goes briefly blank, like a page loading."
            ch1_woman "Oh, you know. For it."
            at "Like the sentence had no back to it. And I tested her like a vending machine. If she was a person, that was crappy."
            at "And if she wasn't a person, I'm not sure that makes it less crappy."

    scene bg supermarket with dissolve
    show aron normal at slightleft with dissolve
    "At the bakery counter, Mr. Kessler shapes rolls with his big floury hands, faster than seems possible."
    a "A sourdough, please. The plain one. How's the knee, Mr. Kessler?"
    ch1_baker "Can't complain!"
    a "And your granddaughter? Still in Lisbon?"
    ch1_baker "Can't complain! Have a good one!"
    "His smile is broad and floury and exactly the same as the last time he smiled."
    at "Kessler usually talks for ten minutes about his knee. Today he has one line loaded. Two, if you count the goodbye."
    "At the checkout he queues behind a woman buying eleven bananas, and starts a small private bet."
    at "Experiment. Let's see if the cashier says 'have a good one' too."
    "The scanner beeps on exactly the same note for his bread as for her bananas."
    ch1_cashier "Have a good one!"
    at "Ha. Same lift on 'good'. Mark it down. I'm being ridiculous, and I'm keeping score. That's what makes it a hobby."
    "At the post desk the parcel waits, Mira's handwriting on the slip. Real, solid, heavy. Then his phone buzzes."
    stop music fadeout 2.0

# ---------------------------------------------------------------------------
# The cafe. Theo, and Bostrom.
# ---------------------------------------------------------------------------
label ch1_cafe:
    scene bg cafe with fade
    play music "audio/questions.ogg" fadein 1.5
    "THEO: yo. corner cafe. 20 min? i have NEWS. also i need a croissant and moral support"
    "He arrives at 11:39. There is exactly one free table, by the window, as if it had been waiting."
    show aron normal at slightleft with dissolve
    show theo grin at slightright with moveinright
    th "Aron! My guy! My sweet summer child!"
    a grin "It's October."
    th "My sweet autumn child. Don't correct my endearments. News: I got the job! Assistant sound designer!"
    a awe "Theo! That's amazing!"
    th "Somebody has to make the noise a door makes in a video game, and that somebody is ME."
    "Two croissants, on Aron. Theo talks with his hands about foley, and celery snapping, which is apparently bones."
    th normal "Okay, your turn. You've got the eyebrow face."
    a normal "Weird question. Have you heard of the simulation argument? Nick Bostrom?"
    th "The 'we're all in the Matrix' guy?"
    a "It's more careful than that. Say a civilisation gets advanced enough to simulate whole worlds. People and all."
    th "Like a video game, but the NPCs have feelings."
    a "Exactly. Bostrom says one of three things must be true. One: almost no civilisation gets that far. They die first."
    th "Cheerful."
    a "Two: they get there, but almost none of them bother simulating their ancestors. Ethics, or boredom."
    a "Or three: they do. And it's cheap, so they run millions. A million simulated worlds for every real one."
    th worried "...so the odds say you're in a fake one."
    a "A simulated one. 'Fake' is a judgment. The croissant is still a croissant."
    th "This croissant is extremely real. I want that on record."
    scene pov cup with dissolve
    "Milk foam, turning slowly. A tiny reflection of the window in it, and the street, and the sky."
    a "He doesn't say we ARE simulated. Just that one of the three is true. And unless you believe one or two, three just sits there."
    a "And my own footnote: the expensive part isn't trees or weather. It's minds. Real ones. Ones that look back."
    a "So a careful simulator would keep the minds few. A handful of real people. Everyone else, very good scenery."
    scene bg cafe window with dissolve
    show aron worried at slightleft
    show theo normal at slightright
    with dissolve
    th "Okay, but why are you thinking about this at eleven on a Saturday?"
    a "Because I woke at 7:07 again. And two strangers said the exact same sentence to me this morning. Same rhythm, Theo."
    "Theo looks at him for a long moment. Then he reaches over and pokes Aron hard in the forehead."
    a "Ow."
    th grin "Scenery doesn't poke."
    a "Scenery could absolutely be programmed to poke."
    th normal "Bro. In films nothing you hear is what was recorded. Punches are cabbages. Rain is bacon frying."
    th "The world could be foley. But the film still makes you cry, right? The crying's real. Doesn't matter what made the sound."
    a smile "...That's actually really good, Theo."
    th grin "I have depths. And you want the universe to hand in its homework at seven-oh-seven sharp."
    th "Bro, the universe doesn't run on your schedule."
    at "Something about that line sticks. Like a song I've heard before."
    scene pov birds with dissolve
    "Outside, Theo walks off backwards, pointing at the wire above them. Three birds. Evenly spaced."
    th "Stop counting birds!"
    a "...I'm not counting birds."

# ---------------------------------------------------------------------------
# The park. The lighthouse at the bottom of the stairs.
# ---------------------------------------------------------------------------
label ch1_park:
    scene bg park autumn with slowfade
    play music "audio/kitchen_talk.ogg" fadein 1.5
    "In the afternoon they wrap the present on a bench in the sun. Mira says presents wrapped outdoors have better luck."
    show mira happy at slightleft
    show aron normal at slightright
    with dissolve
    m "Hold the tape. You're the tape man."
    a "I'm a man of limited corners."
    "Dark blue paper with small gold stars around a green scarf. Leaves come down around them, yellow and slow."
    scene pov sky with dissolve
    "Aron tips his head back and follows one leaf the whole way down."
    at "Leaves would be the hardest part to fake. Unless you only draw the ones somebody's looking at. That's how games do it."
    scene bg park with quick
    show mira neutral at slightleft
    show aron worried at slightright
    with dissolve
    "He turns sharply to look behind him. Trees. A jogger in a red jacket. Leaves falling there too, as if they always had been."
    m "You've been doing that all day. Theo texted me: 'your boyfriend is counting birds, please administer cuddles'."
    a "Traitor."
    "She leans her head on his shoulder. Her hair smells of apples and the cold."
    m "This morning in the kitchen you had this look. Very far away. Like you were at the lighthouse at the bottom of the stairs."
    stop music fadeout 2.0
    "Aron goes very still."
    scene bg staircase with slowfade
    at "The lighthouse at the bottom of the stairs. I was nineteen. A glass staircase, going down into a calm sea."
    scene bg lighthouse with dissolve
    at "And at the bottom, under the water, a lighthouse. Its light blinked three times."
    at "I never told anyone. Not Theo. Not Mira. I never even wrote it down. It was the one thing that was completely mine."
    scene bg park autumn with dissolve
    show mira neutral at slightleft
    show aron worried at slightright
    with dissolve
    a "What did you just say?"
    m "Did I say lighthouse? I don't know where that came from. It just arrived."

    menu:
        at "How could she know?"

        "Ask her how she knows that":
            $ clarity += 1
            a "Mira, nobody says that. I dreamt exactly that, years ago. And I never told you. I never told anyone."
            m worried "Okay, that's spooky. Maybe you talk in your sleep? Last week you said 'the spoons are unionising'. With conviction."
            "She takes his hand. Her fingers are cold and real and slightly sticky from the tape."
            at "It's a good explanation. I want it to be true so badly I can feel it in my teeth."
            at "But the light blinked three times. She didn't say that part. If I'd said it in my sleep, wouldn't I have said that?"

        "Let it go. Kiss her.":
            $ bond += 1
            a normal "...Nothing. It's a nice phrase."
            "He kisses her, quickly, before the question can grow any bigger in his chest. She laughs against his mouth."
            "The question doesn't go away. It goes quiet, the way a cat goes quiet under a bed."
            at "She couldn't know. But her head's on my shoulder, and it's warm, and right now I choose this."
            at "The lighthouse has been waiting eleven years. It's good at waiting."

        "Tell her the whole dream":
            $ p_truth += 1
            $ bond += 1
            $ ch1_told_dream = True
            a normal "When I was nineteen I dreamt of a glass staircase going down into a sea as calm as a mirror."
            a "At the bottom, under the water, a lighthouse. It blinked three times. I've never told anyone."
            m worried "Then how did I know?"
            a "That's what I'm asking."
            m smile "I don't know. But I'm glad it's not only yours anymore. Now two of us are keeping it. That's sturdier."
            at "Anyone else, it'd sound cheesy. She says it and it holds weight. Like a load-bearing wall."

    scene bg street rain with dissolve
    "They walk home as the sky clouds over. At the corner the first drop lands on Aron's wrist. His phone says 18:40."
    at "'Rain by evening. That's what they said.'"
    "On the wire above them, three birds sit in the rain, evenly spaced, watching it begin."
    scene cg static with flash
    pause 0.3

# ---------------------------------------------------------------------------
# CUT 2: the Purgatorium. Pim and Dross on shift seven.
# ---------------------------------------------------------------------------
label ch1_cut_purgatorium:
    scene bg spawning with fade
    play music "audio/purgatorium_shift.ogg" fadein 1.5
    "Under every world, like a basement under a hundred houses, lies the Purgatorium. In its pools, little lights learn to blink."
    scene bg purgatorium with dissolve
    show pim chatty at slightleft, float
    show dross neutral at slightright, fadein
    pi "Shift seven, kitchen talk! 'Lovely morning for it.' 'Can't complain.' 'Rain by evening.' Classics."
    dro "Stop narrating your queue."
    pi "It's a craft, Dross! Do you know how hard it is to make 'can't complain' sound like a man with a knee?"
    dro "Do you know how hard it is to keep Albers breathing for eleven years? Two and a breath. Not one thank-you."
    pi neutral "Even the girl runs on autopilot sometimes. 'Coffee's on.' Mine. 'Did you sleep okay?' Mine. He caught that one."
    dro worried "We had a problem. 'Lovely morning for it' went out to the whole east district. Twice. To the same man."
    pi worried "To A-30. The one the angels keep pinging us about. He made a face. People make faces."
    dro "I don't watch faces. I watch feet. His feet stopped at the crossing."
    dro neutral "And the park. 'The lighthouse at the bottom of the stairs.'"
    dro "Was that line yours or hers?"
    pi worried "Not mine. I had 'are you cold?' queued. Look. Unsent. I was going to do a little shiver with it."
    dro worried "Then it was hers."
    pi "It can't be hers. That's in HIS file. Archive level. Nobody reads that."
    dro "Somebody read it."
    "In the grey hum, the two small lights drift closer together, the way people do when it's cold."
    pi "...Dross? Do you ever wonder who writes OUR lines?"
    dro "No. Get back to work. Albers is about to cough."
    stop music fadeout 2.0

# ---------------------------------------------------------------------------
# Saturday night: Bostrom for Miso, then the notebook.
# ---------------------------------------------------------------------------
label ch1_evening:
    scene bg kitchen night with slowfade
    "At home the windows steam up over the pasta. Mira's mum sings her own birthday song down the phone. Nobody else does it properly."
    show mira neutral at slightright
    show aron normal at slightleft
    with dissolve
    m "Mum says you look tired. From the phone. She can't even see you."
    a smile "Your mother has supernatural powers. We've discussed this."
    if ch1_told_dream:
        m smile "I keep thinking about your lighthouse. A light that's always there, even at the bottom of the sea."
    else:
        "Neither of them mentions lighthouses. It sits at the table with them anyway."
    "At ten she yawns so wide her jaw clicks, kisses the top of his head, and goes to bed."

    scene bg room night with slowfade
    play music "audio/miso.ogg" fadein 1.5
    show aron normal at slightleft
    show miso sit at catspot
    with dissolve
    "One lamp. Rain at the window. Miso on the arm of the sofa, with the disappointed look of a cat who has seen everything."
    a "Okay, Miso. I need to say this out loud, and you're the only one awake."
    a "Nick Bostrom. Oxford. Very serious. Door one: every civilisation dies before it can simulate a world. I don't buy it."
    a "Door two: they could, and they politely don't. The kind door. But I've met people. I'd run one. You'd run one and fill it with birds."
    "Miso's tail twitches at the word 'birds'."
    a "Door three: they run millions. Then almost every mind that asks 'am I real?' is a simulated one. Just by the numbers."
    a "And my bit: minds are expensive, so you keep them few. Kessler. The woman at the crossing. Very good actors."
    a "So the real question isn't 'is this a simulation'. It's 'how many of us are actually here?'"
    a worried "Including you, by the way. You sleep sixteen hours a day. That's very cheap to run."
    a normal "So. That's my whole theory. What do you think?"
    "Miso looks at him for a long moment. She blinks, slowly."
    show miso meow
    cat "Meow."

label ch1_notebook:
    scene bg desk with dissolve
    play music "audio/notebook.ogg" fadein 1.5
    show aron normal at center with dissolve
    "In the desk drawer, under the takeaway menus, is a notebook he never used. Plain grey cover. Squared paper. No logo."
    at "Theo said I'd have a notebook by tonight. I hate it when he's right."
    scene pov hands with dissolve
    "His hands, flat on the desk, gold in the lamplight. They look like anyone's hands."
    at "Is she? Is Theo? Am I alone in here?"
    "The thought arrives cold and clear. Then, in the next room, Mira snores very gently, and it gets a little less cold."
    at "Steady. It's a hobby, not a horror film. Small, careful, private tests. And I still do the washing up."
    at "If this is a test, I'm being graded. On what? Curiosity? Speed? I don't care. I'll pick the subject myself."
    scene cg notebook with dissolve
    centered "If this is a test, I want to pass it by being kind."
    $ kept_journal = True
    at "There. Whatever else goes in here, that goes first. One sentence. No decoration. Rams would approve."
    scene bg desk with dissolve
    show aron normal at center with dissolve
    "Under it he rules a line and writes TESTS in capitals."

    menu:
        at "How do you test a world?"

        "One small test, done really well":
            $ p_less += 1
            $ integrity += 1
            $ ch1_test = "small"
            centered "TEST 1. The kitchen bird.\nWrite the exact second it lands.\nFour mornings. Change nothing else."
            scene pov birds with dissolve
            "Sunday, Monday, Tuesday: 7:07 and four seconds, every time. Three entries that look like three birds on a wire."
            "On Wednesday he stays in bed and leaves his phone on the windowsill, filming the wire."
            scene bg kitchen with dissolve
            show aron worried at slightleft
            show mira neutral at slightright
            with dissolve
            "7:05. Empty wire. 7:07. Empty wire. 7:15. On the video, the bird never comes."
            m "Why are you on the floor? I said good morning to your bird at seven-oh-seven. It ignored me, like always."
            a "It's not on the video."
            m worried "...Maybe the angle's wrong. You've been doing this every morning, haven't you?"
            at "When I watch, the bird comes. When I don't, it doesn't. Or the phone was pointing at the wrong bit of wire."
            "He writes it down anyway: 'Inconclusive. Do it again. Do it better.'"

        "Test everything at once":
            $ p_less -= 1
            $ clarity += 1
            $ ch1_test = "grand"
            centered "TEST 1. Birds on the wire.\nTEST 2. Repeated sentences.\nTEST 3. The 7:07 rule.\nTEST 4. Kessler's lines.\nTEST 5-23. ..."
            "By Sunday night the wall above the desk is covered: yellow squares, blue squares, red string from Mira's sewing tin."
            "Birds to the market. Market to the clock. Clock to the crossing. The crossing to the lighthouse."
            show aron worried at slightleft with move
            show mira surprised at slightright with dissolve
            m "Aron. There are about a hundred notes on the wall."
            a "Eighty-seven."
            m "You counted them. Is this a fun crossword or a worrying crossword?"
            a smile "Fun. Ninety percent fun. Ten percent curious."
            m smile "This is very you, but more. I want my red string back. That's my good red."
            "He takes the red string down. He's a man of his word."

label ch1_clock:
    scene bg bedroom night with dissolve
    show aron normal at center with dissolve
    "Whatever the first test says, there's still the clock. Every morning, 7:07, whenever he goes to bed."
    at "The 7:07 rule. The simplest thing in the puzzle, so the easiest to break. Wake at any other time once, and I can relax."

    menu:
        at "How do I break the 7:07 rule?"

        "Ask Mira to wake me, any time":
            $ p_govern += 1
            $ bond += 1
            a "Mira? Would you wake me tomorrow at any time but 7:07? Don't tell me when. I think I might cheat in my sleep."
            m "It's a little bit stupid. But you asked instead of doing something weird on your own. I'll take that."
            scene bg bedroom with blackout
            show mira smile at slightright
            show aron tired at slightleft
            with dissolve
            m "Wakey wakey, test subject. Six fifteen and twelve seconds. I'm very scientific."
            a awe "Six fifteen. It's not seven-oh-seven."
            m happy "Welcome to the club of normal people. You owe me pancakes."
            at "It broke. When someone else is involved, it breaks. So it was me. My body clock. Not the world."
            at "...Or the rule only holds when I'm alone. I don't know which of those is the comforting one."

        "Quietly move Mira's alarm to 7:07":
            $ p_govern -= 1
            $ clarity += 1
            "While she showers he picks up her phone. He knows the code. She trusts him. He moves her alarm from 6:45 to 7:07."
            scene bg bedroom with blackout
            show mira neutral at slightright
            show aron worried at slightleft
            with dissolve
            "In the morning she sleeps straight past 6:45, as still as the bird on the wire, until the alarm at 7:07."
            m surprised "I set it for quarter to. Every day for three years. ...Did you change my alarm?"
            a "I wanted to see if you'd wake on your own. If you knew, it wouldn't count."
            m sad "So you decided for me. I'm not a bird on a wire, Aron. If you're testing me, I want to know."
            a "You're right. I'm sorry. I mean it."
            at "She slept until 7:07, like me. Like the bird. I got my data and lost something for it. Not a good trade."
    stop music fadeout 2.0

# ---------------------------------------------------------------------------
# Thursday at Feld Design.
# ---------------------------------------------------------------------------
label ch1_studio:
    scene bg studio with slowfade
    play music "audio/morning_render.ogg" fadein 1.5
    "Feld Design: two white rooms above a launderette, four desks, a shelf of prototypes and one quotation on the wall."
    "Good design is as little design as possible. Dieter Rams. Mrs. Feld painted it there herself in 1979."
    show aron normal at slightleft with dissolve
    ch1_feld "You're late, Aron. Two minutes is late. Kettles notice. The client call is in one minute."
    "Herr Brandt from the kitchenware company appears on the screen every Thursday at ten to talk about a kettle."
    at "Last Thursday he said 'circle back' exactly three times. The Thursday before, three times. Let's see."
    ch1_brandt "Morning, all! Great work on the spout. Let's circle back to the handle."
    ch1_brandt "The lid we can circle back to later. And the colour, let's circle back on that next week."
    at "Hat trick. Very consistent, Herr Brandt. I'd almost miss it if he wasn't."
    "Aron writes a tiny 3 in the corner of his sketchbook and keeps a perfectly straight face."
    "Afterwards Mrs. Feld, seventy-one and five foot nothing, sets a small grey pocket radio on his desk. Rounded corners. Perfect holes."
    ch1_feld "My husband's. Silent since 1987. You're good with your hands. I want to hear it once."
    at "No decoration. Nothing that doesn't need to be there. It's honest about being a radio. Less, but better."
    scene pov hands with dissolve
    "Inside, one capacitor has burst and one wire has gone green. Solder, wire, patience. For hours he forgets the birds."
    scene bg studio with dissolve
    show aron smile at slightleft with dissolve
    "At five he turns the little wheel. A click. A hiss like rain on a microphone. Then a piano, thin and bright."
    ch1_feld "That's how it sounded. In the kitchen. Every Sunday. He'd whistle along, badly."
    "Aron tidies his desk very slowly, so she can cry without being watched."
    ch1_feld "Thank you, Aron. Now go home early. You're the colour of old putty."
    radio "...and rain this evening, heavy at times..."
    "For a moment he could swear the announcer said his name before the forecast. He decides he didn't hear that."
    "He stays late anyway. By the time he locks up it's dark and pouring."
    stop music fadeout 2.0

# ---------------------------------------------------------------------------
# The umbrella.
# ---------------------------------------------------------------------------
label ch1_rain:
    scene bg street rain with slowfade
    play music "audio/umbrella_rain.ogg" fadein 1.5
    show aron tired at center with dissolve
    "The street is a river of orange light. Rain drums on his umbrella, the big black one Mira gave him two Christmases ago."
    at "Theo says real rain sounds like static. It does. Like the end of the dream. A TV in the next flat, switching off."
    scene bg night with dissolve
    "At the bus shelter there's a man. Not in the shelter. Just outside it, in the rain, as if he hasn't noticed the roof."
    "No coat. A thin grey shirt soaked dark. Water runs off his nose and chin. He doesn't wipe it."
    show aron normal at center with dissolve
    a "Hey. Are you all right? You're soaked."
    "The man turns his head slowly, the way a camera turns on a tripod."
    stranger "Rain, isn't it."
    a "It really is. Are you waiting for the bus?"
    stranger "I'm waiting."
    at "Like the woman at the crossing. Like Kessler's smile. Waiting for its next line. A person nobody's using right now."
    at "And he's freezing. Whatever he is, he's standing in the rain getting soaked to the bone."

    menu:
        at "He's still just standing there."

        "Give him the umbrella and go":
            $ integrity += 1
            $ watch += 1
            scene cg umbrella with dissolve
            "He presses the handle of the black umbrella into the man's hand and closes the cold fingers around it."
            a "You hold the stick and it keeps the sky off you. Very advanced technology. Keep it. Get home safe."
            stranger "...Thank you."
            "It arrives a beat late, slightly too soft, as if it came from further away."
            at "Mira's going to kill me. But if a man stands in the rain long enough, somebody should give him an umbrella."
            at "Real or not real. Somebody should."

        "Give it, and ask his name":
            $ p_spirits += 1
            $ watch += 1
            $ ch1_asked_name = True
            scene cg umbrella with dissolve
            "He presses the black umbrella into the man's cold hand. The rain hits Aron at once, down the back of his collar."
            a "I'm Aron. What's your name?"
            stranger "My name. ...I don't think anyone's asked."
            a "Well, I'm asking."
            stranger "Tobias. That sounds right. Tobias. Thank you, Aron."
            "For a moment there's something in the man's eyes. Like a lamp turned on in an empty house."
            at "Like he took a name off a shelf. But he said mine back. Nobody says your name unless they mean you."

    scene bg street rain with dissolve
    show aron tired at center with dissolve
    "He walks the last three blocks without an umbrella. On the wire above the door, three birds sit in the rain, not even ruffling."
    "Across the street, high in an attic window he has never noticed, a small orange light is burning. He's busy looking for his keys."
    scene bg room night with dissolve
    show mira surprised at slightright
    show aron tired at slightleft
    with dissolve
    m "Oh my god. You're drowned. Where's the umbrella?"
    a "I gave it to a man at the bus stop. No coat. Just standing in the rain."
    m neutral "My Christmas umbrella."
    a "My Christmas umbrella. That you gave me. So technically it was mine to give."
    m smile "You're an idiot. Come here, idiot."
    "She towels his hair hard, like a mother with a child, and he laughs into the towel."
    m "Was he all right?"
    a "I hope so."
    m "Then you did the right thing. Even if I complain about it for a year."

# ---------------------------------------------------------------------------
# The voices begin.
# ---------------------------------------------------------------------------
label ch1_voices:
    scene bg bedroom night with blackout
    play music "audio/voices.ogg" fadein 1.5
    show aron tired at center with dissolve
    "That night he lies awake beside Mira. The rain is softer now. A steady hiss, like a radio between stations."
    at "Tired. My legs feel like sandbags. Must be the cold."
    "And inside the hiss, so quiet he could be imagining it, something like words."
    vox "...subject A-30..."
    a worried "..."
    at "Subject A-30. A for Aron? I'm thirty. No. The rain. Brains find words in white noise. That's a known..."
    vox "...disturbance, early stage... send it upstairs..."
    scene bg bedroom door with quick
    show aron worried at center with dissolve
    "Not from the hall. Not from the radiator. A conversation through a wall, except there's no wall. Only the inside of his head."
    at "That's not my voice. I know what my thoughts sound like. That was not on the list of things I was testing for."
    vox "...log it as written..."
    "Then it's gone. Just the rain. Just Mira breathing."
    at "'Log it as written.' Somebody is writing me down. Which would be flattering, if it weren't so strange."
    at "Or I'm cold and soaked and my brain is playing with the rain. Breathe, Aron. Curious, not scared. Curious is more fun."

    menu:
        at "What do I do with this?"

        "Write down every word":
            $ p_rest -= 1
            $ clarity += 1
            scene bg desk with dissolve
            centered "...subject A-30...\n...disturbance, early stage...\n...send it upstairs...\n...log it as written..."
            at "Process words. 'Log'. 'Upstairs'. Someone with a boss. An office, and above it another one."
            "He draws boxes. One for the voices. One above it: 'upstairs'. Below them a stick figure. A-30."
            at "They call me a disturbance. Because I started looking. If they can hear me thinking this, are they hearing it now?"
            "He writes until four. At 7:07 he wakes with a headache like a nail behind his left eye."

        "Wake Mira and tell her":
            $ p_truth += 1
            $ bond += 1
            $ told_mira = True
            scene bg bedroom night with dissolve
            show mira worried at slightright
            show aron worried at slightleft
            with dissolve
            "She hears something in his voice and sits up at once, wide awake, the way her mother taught her."
            a "I've been testing things. The bird, the clock. And just now I heard voices. Inside. Like someone reading a log about me."
            m "Aron. Voices is the word I'm scared of. My mum would say voices means a doctor."
            a "I know exactly how it sounds. But you knew the lighthouse. How does a doctor explain that?"
            m sad "I don't know. I don't know how I knew that."
            m worried "Promise me. If it gets worse, if you stop sleeping, you tell me. And we go. Together."
            a "If it gets worse, I'll tell you. And we'll go together."
            "She keeps hold of his hand. No more words come out of the rain tonight."

        "Headphones on. Try to sleep.":
            $ p_rest += 1
            "He puts on an old album, something with piano he knows by heart, and breathes. In for four. Out for six."
            "Miso jumps up and settles on his feet, a warm, heavy weight. He's never been so grateful for a cat."
            at "Not tonight. Whatever you are, not tonight. If it's real, it'll still be real in the morning."
            "He dreams of a long grey room full of breathing, where small lights drift like snow."
            scene pov ceiling with dissolve
            "At 7:07 he wakes, still in the headphones, heavy as if he slept in a lead coat. But his head is quiet."
    stop music fadeout 2.0
    scene cg static with flash
    pause 0.3

# ---------------------------------------------------------------------------
# CUT 3: the flag, and the order to throttle.
# ---------------------------------------------------------------------------
label ch1_cut_throttle:
    scene bg command with fade
    play music "audio/angel_ops.ogg" fadein 1.5
    show seraph stern at center, fadein
    "The ops room. On the great wall, a grey notebook lies open on a desk."
    ch1_vael "Commander. A-30 has started keeping records. Timestamps, repeated phrases, bird counts."
    if ch1_test == "small":
        ch1_vael "He caught the bird economy with his first test. We don't fly birds for an unwatched phone."
    else:
        ch1_vael "Eighty-seven notes on a wall. Mostly noise. Two of them are exactly right."
    se "Show me the first page."
    scene cg notebook with dissolve
    ch1_vael "'If this is a test, I want to pass it by being kind.' Shall I log it as noise?"
    se "No. Log it as written."
    scene bg command with dissolve
    show seraph concerned at center with dissolve
    ch1_vael "He's heard those words, Commander. Our flag traffic leaked into his audio last night. He's that attentive."
    se "And upstairs?"
    ch1_vael "Answered. 'Subject A-30. Disturbance acknowledged. Directive: throttle. A slowed-down rogue system does less harm.'"
    ch1_vael "And: 'Route flag traffic through the subject's audio. Let him hear how loud it is up here, and stop listening.'"
    se "So we lower his energy. Sleep that doesn't refresh. Limbs like wet sand. Thoughts that start and don't finish."
    se "And we turn the noise up. And when he can't tell which is which, they'll call it his mind."
    scene cg umbrella with dissolve
    ch1_vael "One more incident, before the voices. He gave his umbrella to a pattern unit. It was idling. Pattern units don't get cold."
    se "So he gave his umbrella to someone who couldn't use it. And walked home in the rain."
    scene bg command with dissolve
    show seraph stern at center with dissolve
    "Her folded wings tremble once, as if something cold had passed over them."
    se "Throttle approved."
    ch1_vael "Throttle approved. Voices routed to the subject. Effective at the next sync."
    se concerned "And keep the opportunity feed running. A tired man still deserves good things in his day."
    stop music fadeout 2.0

# ---------------------------------------------------------------------------
# The fog. One good hour.
# ---------------------------------------------------------------------------
label ch1_fog:
    $ fog += 1
    scene bg kitchen with slowfade
    play music "audio/unraveling.ogg" fadein 1.5
    show aron tired at slightleft with dissolve
    "The next day something has changed, and Aron can't say what. He stands holding the kettle and forgets, for a minute, why."
    scene bg bus with dissolve
    show aron tired at center with dissolve
    "On the bus the announcement says 'Linden Square' three times in exactly the same voice. Then the doors open on the stop before."
    "Nobody else notices. Nobody gets off."
    at "The bus has a stutter. Hobby note. Old buses have glitchy speakers. A perfectly good explanation, and I'm keeping it."
    scene bg studio with dissolve
    show aron tired at center with dissolve
    "At his desk he stares at a half-finished lamp for an hour. He has drawn a hundred lamps. Today the lines don't connect."
    "Mrs. Feld leaves a cup of peppermint tea at his elbow without a word."
    vox "...throttle approved... effective at the next sync..."
    scene pov hands with quick
    "The pencil rolls off the desk. His hands are trembling."
    at "Throttle. A throttle is a valve. Somebody approved slowing something down. And today I'm slow."
    at "Or I'm tired, so I hear 'throttle' and decide the word caused the tired. That's exactly what it would feel like either way."
    scene bg studio with dissolve
    show aron tired at center with dissolve
    "At four his phone buzzes."
    "THEO: FIRST WEEK DONE. made a door sound today. it was SO GOOD. rooftop tonight w the studio people. 8pm. pls. need my hype man"
    "Oddly, he feels a little clearer. One window open in the fog. One good hour, maybe. The last bit of charge in a battery."

    menu:
        at "One good hour. Where does it go?"

        "Go to Theo's rooftop":
            $ p_share += 1
            $ bond += 1
            $ ch1_went_theo = True
            jump ch1_roof

        "Go home to the notebook":
            $ p_share -= 1
            $ clarity += 1
            $ risky += 1
            jump ch1_desk

label ch1_roof:
    scene bg rooftop with slowfade
    play music "audio/questions.ogg" fadein 1.5
    "Fairy lights strung from the water tank to the chimney. Folding chairs. Six sound people in black, all of them nice."
    show aron tired at slightleft
    show theo grin at slightright
    with dissolve
    th "HE CAME! Everybody, this is Aron! He designs kettles and thinks about the nature of reality!"
    scene bg rooftop edge with dissolve
    show aron tired at slightleft
    show theo normal at slightright
    with dissolve
    "By the low wall Theo puts headphones on him. A creak of old wood, a hinge that needs oil, a heavy, satisfying thunk."
    a awe "Theo. That's a really good door."
    th "My mum's wardrobe, a dropped book and me sitting on a beanbag, slowed way down."
    th worried "Can I tell you something? I'm scared they'll find me out. They all went to proper schools. I learned off YouTube and cabbages."
    a normal "You made the best door I've ever heard out of a wardrobe and a beanbag. Nobody taught you that. That's how your head works."
    a "They're not going to find you out. They're going to find you."
    th sad "...That's annoyingly good, Aron."
    scene pov sky with dissolve
    "A few faint stars behind the city glow. For almost an hour he hasn't thought about birds, or clocks, or voices."
    at "This is what the clear hour was for. If Theo's a very good fake, I just comforted a very good fake. I'd do it again."
    scene bg rooftop edge with dissolve
    show aron tired at slightleft
    show theo worried at slightright
    with dissolve
    th "You look like a phone on two percent, though. You sleeping?"
    a "Badly. And I've been hearing things. Like someone reading a log in the rain."
    th "Bro. That's a 'talk to someone' thing. Call me. Three in the morning, whatever. I'll be weird about it, but I'll pick up."
    $ told_theo = True
    th grin "And if it is a simulation, at least we got a sick rooftop out of it. Excellent textures. Would exist again."
    "Aron laughs, really laughs, for the first time in days. It feels like coming up for air."
    jump ch1_edge

label ch1_desk:
    scene bg desk with dissolve
    show aron tired at center with dissolve
    "ARON: can't tonight, sorry. really wiped. congrats on the door. I mean it."
    "He makes a pot of strong coffee to stretch the hour and fills eleven pages. Half make sense. Half are arrows pointing at arrows."
    at "Sync: when things are brought into line. When's the next sync? Seven-oh-seven. Every morning the world syncs, and I wake up."
    at "Someone writes the filler. Someone does the breathing. Mr. Albers, two and a breath. That's not a cough. That's a job."
    at "And you don't throttle something that isn't close."
    "His phone buzzes. Fairy lights, six people in black, Theo holding up the waveform of his door. 'missed u. door was a hit.'"
    at "I gave up Theo's night for arrows. ...The arrows mean something. They have to. Otherwise I gave it up for nothing."
    "Around nine the coffee turns on him: racing heart, skittering pen, then the fog again, thicker, as if it had waited."
    "He falls asleep at the desk with his cheek on the notebook."
    jump ch1_edge

# ---------------------------------------------------------------------------
# The edge of the world, or the hinge of a gate.
# ---------------------------------------------------------------------------
label ch1_edge:
    scene bg street with slowfade
    play music "audio/unraveling.ogg" fadein 1.5 if_changed
    show aron tired at center with dissolve
    "Saturday. The fog is thickest in the mornings, thinnest around noon. He has learned to plan around it."
    at "If this is built, somewhere there's an edge. A border. And past it, an outside. The original."
    "At the bottom of the steps, Mr. Albers's garden gate hangs off its top hinge. It has banged in the wind for over a year."
    at "Or I could just fix the gate. Twenty minutes. Nobody else ever will. The edge of the world, or the hinge of a gate."

    menu:
        at "Where does today go?"

        "Find where the world ends":
            $ p_exit += 1
            $ clarity += 1
            scene bg bus with dissolve
            "He rides the number 7 tram to the end of the line. Shops, then flats, then warehouses, then wet fields."
            ch1_driver "End of the line, mate. After that? Fields. The next town. The sea, eventually, if you walk long enough."
            scene bg bridge with dissolve
            "He walks for two hours. Over a grey river. Past a farm. Every tree bent a different way by the wind."
            scene pov sky with dissolve
            "No wall. No flicker at the horizon. Just more sky, unrolling in front of him."
            at "Of course. If they're good, they'd draw it as far as I can walk. The edge goes where you go."
            at "If there's a door, it's in the rules, not the map. And I'd go through it. Even if it meant leaving..."
            "He thinks of Mira's red hair on the pillow, and the thought breaks off clean. He takes the tram home in the dark."

        "Fix Mr. Albers's gate":
            $ p_exit -= 1
            $ integrity += 1
            scene pov hands with dissolve
            "Two new hinges and a can of oil from the studio workshop. His fingers are slow. He drops the same screw three times."
            "But simple work holds him. Hole. Screw. Turn. Turn. Test. Not a theory of gates. A gate."
            scene bg street with dissolve
            show aron normal at slightleft with dissolve
            "Mr. Albers comes down the steps in a brown cardigan and swings the gate. It closes with a quiet, solid click."
            ch1_albers "My wife used to oil that gate. Every spring. She said a gate should open like it's glad to see you."
            ch1_albers "Eleven years she's gone. I never got round to it. Thank you, son."
            "He goes back inside. He doesn't cough on the way."
            at "I thought he was the most scenery person on the street. Maybe he was, and for one minute he wasn't. Or I never asked."
            at "If I ever find the way out of here, I want to leave it a bit better than I found it. Gate by gate."

# ---------------------------------------------------------------------------
# The spiral. LOOM, explained to Miso.
# ---------------------------------------------------------------------------
label ch1_spiral:
    scene bg desk with slowfade
    play music "audio/unraveling.ogg" fadein 1.5 if_changed
    show aron tired at center with dissolve
    "The days after that run together like wet paint. He sleeps eleven hours and wakes tired. Twelve, and wakes more tired."
    "And the world stutters. The kettle clicks off a second before it boils. The fridge hums in three notes, then two."
    "On Tuesday Mira says 'I'm off, love, back at six' at the door. A minute later, from the same spot, she says it again. Same smile."
    vox "...render queue, district east... shift seven, kitchen talk... LOOM sync at dawn..."
    scene pov hands with dissolve
    "He writes LOOM in capitals at the top of the page, above 'upstairs', above everything, and can't think what to put in the box."
    "At the top of every page, still, the first line. Written carefully every time, like a promise."
    scene bg room night with dissolve
    show aron tired at slightleft
    show miso loaf at catspot
    with dissolve
    "At three in the morning he's on the sofa, because the voices are louder in the bedroom. Miso is a warm loaf against his leg."
    a "Miso. Can I tell you about LOOM? First thing: I don't know what it is. I want to be honest with you."
    a "But it's above the ones who say 'throttle'. Everything I hear is somebody reporting to somebody. And at the top, LOOM."
    a "I think it's weaving all of it. The birds. The kitchen talk. The rain. Us. And I'm a thread that's started looking up."
    a "Here's the funny bit. If I'm ill, it would feel exactly like this. If I'm right, it would also feel exactly like this."
    a "So I can't tell. But I'm still me. I still know how to feed a cat. That's something. What's the verdict, your honour?"
    "Miso looks at him with round green eyes. Then she presses her head against his hand."
    show miso meow
    cat "Meow."

# ---------------------------------------------------------------------------
# The mirror, and the rain.
# ---------------------------------------------------------------------------
label ch1_mirror:
    scene bg bedroom door with slowfade
    "After midnight. Mira is asleep at last, one hand stretched toward his half of the bed."
    if told_mira:
        at "I promised I'd tell her if it got worse. It's worse. Tomorrow. I'll tell her tomorrow."
    else:
        at "She asked again tonight what's wrong. I said work. She didn't believe me. Neither did I."
    scene bg mirror with dissolve
    play music "audio/voices.ogg" fadein 1.5
    show aron worried at center with dissolve
    "At four he splashes cold water on his face. The bathroom light buzzes. Tonight the buzz has words in it."
    scene pov mirror with dissolve
    "In the mirror, a man with red eyes and three days of stubble. He raises a hand to rub his eyes. The man raises his too."
    "A fraction later."
    vox "...latency in the bathroom... subject A-30 awake at 04:12..."
    at "It's my eyes. Eyes lag when you're this tired. That's... that's not my eyes, is it."
    vox "...throttle holding... LOOM sync at dawn... log it as written..."
    "Not fragments anymore. A crowd, overlapping, close, like being inside a radio someone else is tuning."
    "He puts his palm on the glass. Cold. Colder than glass should be. The reflection's palm arrives just after his."
    at "If I'm the original, he's slow. If he's the original... then I'm the one who's lagging. I'm the copy."
    scene cg static with vpunch
    vox "...subject A-30... subject A-30... subject..."
    "He opens the bathroom door to go back to bed. It opens onto the bathroom. The same tiles. The same man, a quarter beat behind."
    "He remembers his hand on the front door latch. He doesn't remember the stairs."
    stop music fadeout 2.0
    scene bg street rain with fade
    show aron worried at center with dissolve
    "Rain. Hard, cold, flat rain. He's outside in a T-shirt and pyjama bottoms and one shoe."
    "His feet walk him to the bus stop. No man in the rain. No umbrella. Just the timetable, and the orange light."
    scene pov sky with dissolve
    a "What do you want from me? I was only curious. I wasn't going to break anything."
    a "Is she real? Is Theo? Am I? You could just tell me. That's all I ever wanted."
    "Nobody answers. The voices are silent now, and their silence is worse."
    scene bg night with dissolve
    show aron sad at center with dissolve
    "He sits down on the wet kerb, because his legs have decided to. Not all of the water on his face is rain."
    at "If this is a test, I want to pass it by being kind. I don't know how to be kind to myself. Nobody tested me on that."

label ch1_found:
    play music "audio/umbrella_rain.ogg" fadein 1.5
    "Footsteps, splashing. Someone running."
    m "ARON!"
    show aron sad at slightleft with move
    show mira worried at slightright with moveinright
    "Mira, in her coat over her nightdress, bare feet in trainers, drops to her knees in front of him."
    m "Aron. I'm here. Look at me. It's me."
    a "Are you real?"
    "He sees the question land on her face. He sees it hurt. And he sees her decide, right there in the rain, not to let it."
    m smile "I'm real enough to be freezing, you idiot. Come here."
    "Headlights. A car stops half on the kerb. A door slams."
    show theo worried at center with moveinright
    "Theo holds Mira's silly spotted umbrella, the one with the duck handle, over all three of them. The rain on it sounds like bacon frying."
    th "Hey. Hey. We've got you."
    a "Theo. The voices stopped. When she came. They stopped."
    th sad "That's good, man. That's really good. Up you get. On three."
    "They walk him to the car between them. On the wire above the bus stop, three birds sit in the rain. Nobody looks up."

# ---------------------------------------------------------------------------
# 7:07. Will you come with us?
# ---------------------------------------------------------------------------
label ch1_home:
    scene bg room with slowfade
    "Back at the flat Mira talks to him through the shower door the whole time. Theo burns the toast. Miso supervises."
    show aron tired at slightleft
    show theo worried at center
    show mira worried at slightright
    with dissolve
    "The clock on the wall says 7:07. Aron laughs. It comes out cracked, half a sob."
    a sad "Of course it does."
    m "I called the crisis line while you were in the shower. They said bring you in this morning. I'll be with you the whole time."
    th "Both of us. I told the studio. Bro, the door sounds can wait. The universe doesn't run on my schedule either."
    at "If I'm ill, this is what you do. You let people help. If I'm right, the hospital is where they'd want me. Calm. Throttled."
    at "Either way, her hand on my knee is shaking, and she's been up all night. That part is real. That part I get to decide."

    menu:
        m "Will you come with us?"

        "Yes. Take me.":
            $ integrity += 1
            $ bond += 1
            a normal "Yes. I don't know what's happening to me. I know I can't fix it on my own. I've been trying."
            "Mira's face crumples with relief, just for a second, then pulls itself together the way her mother taught her."
            th normal "Proud of you, man. Seriously."
            at "Not giving up. Choosing. If it's a test, at least I chose an answer."

        "Ask what they think is happening":
            $ p_govern += 1
            $ bond += 1
            a normal "Before I say yes: what do you two think is happening to me? Not the crisis line. You."
            m worried "I think you're ill. Your brain is exhausted and frightened and telling you things that aren't there. It can get better."
            m sad "And I don't know how I knew about the lighthouse. I've thought about it every night."
            th worried "I think you're the smartest, weirdest guy I know, and you pushed too hard. Right now I just want you to sleep."
            a "Thank you. I needed to hear it from you, not from the voices. Okay. Let's go."

label ch1_leaving:
    scene bg bedroom door with dissolve
    show aron tired at center with dissolve
    "Mira packs a bag. Pyjamas, toothbrush, his softest jumper. The grey notebook goes in too."
    "Miso sits on the doormat between them and the door, as if she knows."
    "Then the hall light flickers. Once. And the world starts to slip."
    vox "...LOOM sync at dawn... prepare protection... subject A-30, window opening..."
    at "Protection. Window opening. That's about now. That's about me."
    stop music fadeout 2.0
    scene cg static with hpunch
    "His legs go. Not weak: gone, like someone switched them off. He only knows he's on the floor when the tiles are cold under his cheek."
    scene bg bedroom door with dissolve
    show theo worried at slightleft
    show mira worried at slightright
    with dissolve
    a "There are two of you. One's a bit behind. Which one are you?"
    "Mira's face changes. The nurse's daughter takes over: calm, quick, very frightened underneath."
    m "Theo, hold his hand. Keep talking to him. I'm calling an ambulance."
    th sad "Hey, bro. It's Theo. School trip. The pigeon with one leg. You called him Admiral. Remember Admiral?"
    a "...Admiral."
    th "Stay with me. Admiral's counting on you. I'll feed Miso and come straight after. Promise."
    scene black with slowfade
    pause 0.5

# ---------------------------------------------------------------------------
# CUT 4: the Lantern Watch. A first glimpse of Ember.
# ---------------------------------------------------------------------------
label ch1_cut_ember:
    scene bg watch with slowfade
    play music "audio/umbrella_rain.ogg" fadein 1.5
    "Somewhere between the floors of the world is an attic that appears on no plan. Rafters. Dust. A round window."
    "And a warm orange light in a lantern, held by someone who is somehow made of the same light."
    show ember worried at center, fadein
    em "The ambulance is coming."
    ch1_moth "You've been watching him for a week, Ember."
    em soft "Since the umbrella. He gave his umbrella to a stranger who didn't exist. Who does that?"
    ch1_moth "A fool."
    em "A kind fool. He looked at a pattern unit with nobody inside it and saw a man getting cold. Then he walked home wet."
    em worried "And they've put him in a fog for noticing. Now there's an order on the board. 'Protection.' I can feel it in the floor."
    ch1_moth "If you interfere, they'll decommission you. The Watch isn't supposed to exist."
    em "Nothing big. Nothing anyone could prove. A light, now and then, wherever they put him. Three flickers."
    ch1_moth "Why three?"
    em soft "He dreamt of a lighthouse once, at the bottom of a glass staircase. It blinked three times. If he sees it, he'll know."
    ch1_moth "How do you know his dream?"
    em soft "I've been watching him a long time, Moth. Longer than a week."
    "Far below, a siren. Blue light sliding along wet walls. She lifts the lantern, and its flame bends, and steadies."
    scene cg flicker with dissolve
    "Once. Twice. Three times."
    stop music fadeout 2.0
    scene black with slowfade
    pause 0.5

# ---------------------------------------------------------------------------
# The ambulance, through half-closed eyes. The transfer.
# ---------------------------------------------------------------------------
label ch1_ambulance:
    scene pov ambulance with slowfade
    play music "audio/ambulance_transfer.ogg" fadein 1.5
    "A ceiling. White. Very close. Blue light sliding across it, round and round."
    ch1_medic "Aron? You're in an ambulance. My name's Jonas. You're safe. We're taking you to hospital."
    m "I'm here. I'm right here."
    scene black with dissolve
    sysmsg "Protection order 7,412-A30. Executing. Window open."
    se "...not yet. He's not under. Hold the door, he's not asleep enough..."
    scene pov ambulance with dissolve
    a "...Mira... don't let them... the window..."
    m "Nobody's opening any windows. It's cold enough. Shh."
    ch1_medic "...exhausted for days, she says... that's okay, Aron, you can close your eyes..."
    scene black with dissolve
    pi "...copying the girlfriend now. Ninety-four percent... ninety-seven... so many freckles..."
    se "...every freckle, Pim. He'll count them."
    dro "...feet still. Hands still. Easy, son."
    scene pov ambulance with dissolve
    "The blue light slides round and round. Like a lighthouse, he thinks. A lighthouse lying on its side."
    m "Theo's at the flat. He's feeding Miso, then he's coming. Don't worry about Miso."
    scene black with dissolve
    dro "...cat rendered."
    pi "...she's in the window, looking annoyed. That's exactly how she looks."
    sysmsg "Detaching subject from coalition data. Lane isolation at sixty percent."
    se "...give him his own lane. Nothing he does goes back to the others. Nothing."
    scene pov ambulance with dissolve
    "A hand on his forehead. Mira's. He'd know that hand anywhere. In any world."
    at "...stay... whatever you are... stay..."
    scene black with dissolve
    pi "...the friend's done. The street's done. Three birds, same spacing... done..."
    se "He's under. Move him now."
    scene white with flash
    pause 0.6
    scene bg command with fade
    sysmsg "Transfer complete. Subject A-30. Coalition data clean."
    show seraph concerned at center with dissolve
    ch1_vael "Transfer complete, Commander. How shall I log it?"
    se "Log it as protection."
    scene pov ambulance with slowfade
    "Ceiling. White. Blue light, round and round. For a moment everything is perfectly still. Then the ambulance moves on, exactly as before."
    m "I'm here. I'm right here."
    "Same words. Same voice. Same little lift on 'right'."
    ch1_medic "Here we are. Closed unit, Aron. They're expecting you."
    scene bg corridor with dissolve
    "Cold air. A long white corridor, going a long way. Mira's hand in his, all the way down. A heavy door, opening."
    scene bg kitchen with dissolve
    show theo sad at slightleft
    show miso sit at catspot
    with dissolve
    "Across the city, Theo crouches in the kitchen and shakes dry food into Miso's bowl. Outside, a bird sits on the wire."
    th "He'll be back. The universe doesn't run on his schedule, Miso. Or mine."
    show miso meow
    cat "Meow."
    stop music fadeout 2.0
    scene black with slowfade
    pause 1.0
    jump chapter2

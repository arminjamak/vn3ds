# Snapshot - Chapter 1, "The Morning Render" (condensed, about 33 minutes).
# Condensed from drafts/long/ch1_part1..4.rpy. Eleven menus, all rejoining.
#
# The shadow thread starts here. While the fog comes in, reflections (his
# coffee, a bus window, the black TV, the bathroom mirror) play an
# auto-running course, "A Field Guide to Burning Down the Gates of Heaven",
# step by step: two drivers per humanoid (the negative mind, spirits, from
# within; the creative side, angels, by remote), many worlds and mirror
# worlds, light that makes and shadow that copies, the shadow swarming the
# humanoids. At 4 a.m. step five never loads: the player edits the voice
# (ch1_edit: speed, ping-pong, loop, melody; clips in audio/edit/) and the
# script derails. Then the breakdown: everyone approaches at once, the
# bathroom door, the police and paramedics who assume the worst, the carry
# down the stairs, the pepper spray, and the ambulance ("cut his antenna
# off" / "cut your T-shirt off"), which is the existing transfer into his
# own lane.
#
# Score: morning_render (waking, the studio), kitchen_talk (kitchen, park),
# angel_ops (ops room, throttle), theme (street and market tests),
# questions (Bostrom with Theo, the index cards, the rooftop),
# purgatorium_shift (Pim and Dross), miso (Bostrom for Miso, the leak and
# the steps), notebook (first line, tests, 7:07), umbrella_rain (the
# umbrella, the bathroom door, Ember), voices (the first voices, the
# mirror), unraveling (the fog, the spiral, the intervention),
# ambulance_transfer (the ride, transfer complete, the end).
#
# Minigames: quiz (the index cards, ch1_notebook) and miso (the leak,
# ch1_spiral). Cheat: asking the stranger's name (ch1_rain).
#
# Camera (camera.rpy): a handheld crew follows Aron. Every new place opens on
# an establishing shot, then coverage aimed at whoever speaks. Human sprites
# are 460 px wide, so the face of someone at xalign a sits at a * 0.64 + 0.18:
#   slightleft 0.32 . center 0.5 . slightright 0.68 . ch1_l3 0.23 . ch1_r3 0.77
#   Miso at catspot 0.78 . Pim at slightleft 0.30 . Dross at slightright 0.70
# Reverse angles swap left and right: in `bg kitchen reverse` Mira is on the
# left (her plate) and Aron on the right (his cup).

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
define ch1_kaz = Character("Kaz", color="#c8d8a8")
define ch1_cop = Character("Police officer", color="#a8b8d8")
define ch1_cop2 = Character("Second officer", color="#a8b8d8")

default ch1_test = ""
default ch1_asked_name = False
default ch1_told_dream = False
default ch1_went_theo = False
default mg_quiz = 0
default mg_miso = 0
default ch1_edits = 0
default ch1_ed_fast = False
default ch1_ed_pong = False
default ch1_ed_loop = False
default ch1_ed_tune = False
default ch1_door = ""

# three people in one shot, spaced so nobody overlaps
transform ch1_l3:
    xalign 0.08 yalign 1.0

transform ch1_r3:
    xalign 0.92 yalign 1.0

# the hall outside the bathroom (bg bathroom door): sitting against the wall
transform ch1_hall:
    xalign 0.12 yalign 1.0

# the cafe seen from the end of the bar: both clear of the espresso machine
transform ch1_bar_a:
    xalign 0.1 yalign 1.0

transform ch1_bar_t:
    xalign 0.55 yalign 1.0

# down at Miso's height, for her looks and her "Meow.": she sits on the floor
# at catspot, lower than doc_low reaches, so the frame dips further
transform ch1_floor(a=0.78):
    ease 0.6 zoom 1.5 xoffset ((a - 0.5) * 1280 * 1.5) yoffset 200
    doc_sway(0.8)

label chapter1:
    $ chapter = 1
    camera
    scene black with blackout
    centered "Chapter 1\n\nThe Morning Render"
    jump ch1_wake

# ---------------------------------------------------------------------------
# 7:07. Mira. Miso.
# ---------------------------------------------------------------------------
label ch1_wake:
    scene black
    "Somewhere a long way down, a light blinks three times. Then the ordinary dark of a bedroom with the curtains drawn."
    camera at doc_wide
    scene pov ceiling with slowfade
    play music "audio/morning_render.ogg" fadein 1.5
    "A ceiling. Grey light. In the corner of his eye, digits on the nightstand."
    "7:07."
    at "7:07. Again. I never set it. I never have to."
    at "Weird dream, too. The park. Mira laughing at a pun that didn't deserve it. And then the birds just stopped. Mid-flap."
    camera at est_orbit
    scene bg bedroom with dissolve
    show aron tired at center with dissolve
    "The clock is small and white, with a yellow alarm hand and no logo. Eleven euros at a flea market, because Dieter Rams would have approved."
    camera at doc_medium(0.5)
    show aron smile
    at "Less, but better. Even my clock agrees with me."
    show aron grin
    at "Some people do crosswords. I quietly check whether the universe is real. Before coffee. Nobody needs to know."
    camera at doc_punch(0.5)
    show aron embarrassed
    m "Who are you talking to?"
    camera at doc_wide
    "The voice comes from the pillow next to his, thick with sleep. A tangle of red hair, one eye open, a freckled shoulder."
    camera at doc_close(0.5)
    a grin "Myself. I'm the only one who understands me."
    m "Mm. Poor you."

    camera at est_dolly
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
    camera at doc_peek(0.5)
    scene bg bedroom door with dissolve
    "Later she steals his hoodie from the chair and pads off to the kitchen, humming, and nearly trips over a small orange shape."
    m "Miso! Good morning, princess. No, you've had breakfast. Don't lie to me."
    camera at doc_wide
    scene bg bedroom with dissolve
    show aron smile at slightleft
    show miso stare at catspot
    with dissolve
    camera at ch1_floor(0.78)
    "Miso, an orange tabby with a white chest and the posture of a retired judge, sits beside the bed and stares at him."
    camera at doc_medium(0.32)
    a grin "I know. Your bowl is a tragedy. Please take it up with the management."
    camera at ch1_floor(0.78)
    show miso meow
    cat "Meow."

# ---------------------------------------------------------------------------
# The kitchen. The bird on the wire, the early coffee machine.
# ---------------------------------------------------------------------------
label ch1_kitchen:
    camera at est_pan
    scene bg kitchen with dissolve
    play music "audio/kitchen_talk.ogg" fadein 1.5
    show mira smile at slightright
    show aron neutral at slightleft
    with dissolve
    "Mira is at the window in his stolen hoodie over her teal dress, a mug in both hands."
    camera at doc_medium(0.68)
    m grin "There he is. The snoring beauty."
    camera at doc_medium(0.32)
    a grin "I don't snore. I make low, rhythmic, emotionally supportive sounds."
    show mira laugh
    pause 0.6
    camera at doc_medium(0.68)
    show aron neutral
    m neutral "Your bird's back, by the way. On the wire. Every morning. I checked once, because I'm a nerd. Seven-oh-seven."
    camera at doc_close(0.32)
    a curious "Seven-oh-seven?"
    show aron thinking
    at "The clock. And now the bird. Two is a coincidence, three is a pattern. I just made that rule up, but it's the rule."
    camera at doc_wide
    scene bg kitchen table with dissolve
    show mira neutral at slightright
    show aron neutral at slightleft
    with dissolve
    m "Coffee's on."
    show aron surprised
    "She reaches for the button. And the machine begins to gurgle a fraction of a second before her finger touches it."
    show aron curious
    "Three short gurgles. One long one. Like always. Except early."
    camera at est_dolly
    scene pov cup with dissolve
    "He looks down into his mug. Black coffee. A small trembling circle of window light in it."
    at "Sound before cause. The effect arriving early, like someone got their timing wrong. Interesting. Very interesting."
    m "Did you sleep okay?"
    # the reverse angle: from the counter, back across the table
    camera at doc_medium(0.68)
    scene bg kitchen reverse with dissolve
    show mira neutral at slightleft
    show aron grin at slightright
    with dissolve
    a "You were there. You tell me."
    camera at doc_close(0.32)
    m surprised "...Huh. Sorry. That just came out. Autopilot. Coffee brain."
    camera at doc_medium(0.32)
    show aron neutral
    m neutral "Weather's supposed to turn later. Rain by evening. That's what they said."
    camera at doc_close(0.68)
    show aron thinking
    at "Who's 'they'? No radio on. Her phone's face down. It's kitchen talk. It doesn't come from anywhere."
    camera at doc_creep(0.68)
    show aron curious
    at "...Does anything come from anywhere?"
    camera at doc_medium(0.32)
    m grin "You've got your thinking face on. The one where your eyebrows try to touch."

    menu:
        at "Tell her?"

        "Tell her the birds froze in my dream":
            $ p_truth += 1
            $ bond += 1
            camera at doc_medium(0.68)
            show mira neutral
            a embarrassed "Okay, this sounds silly. In my dream the birds just stopped. In the air. Like a paused video."
            a neutral "Then the clock said 7:07, and you said the bird comes at 7:07, and the coffee machine started before you touched it."
            camera at doc_medium(0.32)
            m grin "Aron, that machine is older than my sister. It does whatever it wants."
            m smile "You woke up with your brain still in dream-mode. Everything looks like a sign for an hour."
            show aron smile
            m laugh "Once I was convinced the toaster was angry with me. It burned my toast for a week, so who knows."
            camera at doc_wide
            show mira tender
            "She takes his face in both hands."
            camera at doc_creep(0.32)
            m "Thank you for telling me, though. Even the silly things. Especially the silly things."
            camera at doc_close(0.68)
            show aron tender
            at "She didn't laugh at me. She laughed with me. She's always known the difference."

        "Keep it to myself and watch":
            $ p_truth -= 1
            $ clarity += 1
            camera at doc_medium(0.68)
            a smile "Nothing. Coffee thoughts."
            show mira neutral
            "She lets it go, the way she lets things go when she's decided to come back to them later."
            camera at est_orbit
            "He leans where he can see the window, the machine and Mira at once. On the fridge, Miso watches too. Two scientists."
            camera at doc_close(0.32)
            "The bird turns its head left, right, left. Mira stirs her coffee. Three circles clockwise. Two taps on the rim."
            camera at doc_close(0.68)
            show aron curious
            at "She always does that. I've seen it a thousand times. I never noticed I'd seen it."
            show aron thinking
            at "Real things are messy. This morning is too neat. Or I never paid attention before. Either way: my secret game."
            camera at doc_medium(0.68)
            show aron smile
            "He hides a smile in his mug, and feels a small pang at keeping it from her, like a draught under a door."

    camera at doc_wide
    scene bg kitchen with dissolve
    show mira smile at slightright
    show aron neutral at slightleft
    with dissolve
    m "Bread from the market, please. And there's a parcel at their post desk. Mum's birthday present."
    camera at doc_medium(0.68)
    m grin "Not the seeded loaf. You pick the seeds out like a raccoon."
    camera at doc_medium(0.32)
    a grin "Raccoons are very dignified. Bread. Parcel. No seeds. Love you."
    camera at doc_close(0.68)
    m happy "Love you too, raccoon."
    hide aron with dissolve
    # filmed from the hallway: she doesn't know anyone's still looking
    camera at doc_peek(0.42)
    scene bg kitchen door with dissolve
    show mira neutral at Transform(xalign=0.4, yalign=1.0)
    with dissolve
    "Mira stays at the window after he goes, looking at the bird on the wire."
    camera at doc_creep(0.44)
    "For a moment her face is completely still, as if no one is behind it. Then she blinks, and sips, and is herself again."
    stop music fadeout 2.0
    camera
    scene cg static with flash
    pause 0.3

# ---------------------------------------------------------------------------
# CUT 1: the angel corps.
# ---------------------------------------------------------------------------
label ch1_cut_ops:
    camera at est_crane
    scene bg barracks with fade
    play music "audio/angel_ops.ogg" fadein 1.5
    "Somewhere that is not a place, pale figures stand in perfect rows, wings folded tight like umbrellas nobody has opened."
    "A bell rings that has no sound. The rows turn as one and file out to their desks."
    camera at est_orbit
    scene bg command with dissolve
    show seraph neutral at center, fadein
    se "Status."
    camera at doc_wide
    ch1_vael "World 7,412, Commander. Morning render complete. Weather on schedule: rain from 18:40."
    ch1_vael "Subject A-30 is out buying bread, as the conscious female requested. Mira."
    camera at doc_medium(0.5)
    se "Opportunity feed?"
    # the reverse: from the wall of worlds, the desks behind her
    camera at doc_wide
    scene bg command reverse with dissolve
    show seraph neutral at center
    with dissolve
    ch1_vael "Standard enrichment. A free table at the corner cafe at 11:40. An old friend's good news, routed to coincide."
    camera at doc_medium(0.5)
    se smile "Keep it feeling accidental. That's the craft. We feed him chances. We never touch the choices."
    camera at doc_close(0.5)
    se thinking "And the kitchen? I saw a latency flag."
    ch1_vael "The coffee machine fired its sound three hundred milliseconds early. Older pipeline. His gaze lingered one point two seconds."
    se neutral "Log it. With the birds."
    camera at est_pan
    scene bg worlds with dissolve
    "Behind her the wall dissolves into thousands of lanes of light, side by side. In each, the same city. The same man buying bread."
    show seraph neutral at center with dissolve
    ch1_vael "All lanes in step. Do you ever wonder which lane is the original?"
    camera at doc_medium(0.5)
    se thinking "Nobody knows, Vael. Not us. Not upstairs. Every snapshot in the coalition reads the same data."
    se neutral "What one lane learns, they all learn. So we treat every lane as if it were the real one."
    camera at doc_wide
    ch1_vael "Forty-one conscious souls in his city. Under a thousand in his world. The rest are spirit-run, or ours."
    se determined "Keep it lean. A young world doesn't get more minds until it proves stable."
    ch1_vael "And the reflections, Commander. Shadow traffic in the east district again. Shop windows. Puddles. Something looking out."
    camera at doc_close(0.5)
    se worried "Keep that off the Council's desk. They're frightened enough of a war without counting puddles."
    se "And keep an eye on this one. He notices things."
    stop music fadeout 2.0

# ---------------------------------------------------------------------------
# The street and the market: three birds, one sentence, one loaded line.
# ---------------------------------------------------------------------------
label ch1_street:
    camera at est_dolly
    scene bg street with fade
    play music "audio/theme.ogg" fadein 1.5
    show aron smile at center with dissolve
    "The street is bright and cold. The kind of October morning that makes everything look freshly printed."
    camera at doc_medium(0.5)
    show aron curious
    "Halfway down the block, he looks up."
    camera at doc_wide
    scene pov birds with dissolve
    "Three birds on the telephone wire. Evenly spaced. One, two, three, like notes on a stave."
    at "Same three as yesterday? I didn't look yesterday. Who looks at birds?"
    at "Birds space out so they can take off without hitting each other. Physics. Or etiquette. ...Of course."
    camera at doc_wide
    scene bg street with dissolve
    show aron neutral at center with dissolve
    "A man with a small brown dog passes and smiles at him."
    ch1_dogman "Lovely morning for it, isn't it?"
    camera at doc_medium(0.5)
    a smile "It is. Lovely."
    # across the road at the crossing: the other row of houses
    camera at est_pan
    scene bg street reverse with dissolve
    show aron neutral at center with dissolve
    "At the crossing a woman in a green coat waits beside him with a shopping bag. As the light turns, she glances over and smiles."
    camera at doc_medium(0.5)
    ch1_woman "Lovely morning for it, isn't it?"
    camera at doc_punch(0.5)
    a surprised "..."
    "Same words. Same lift on 'lovely'. Same little pause before 'isn't it', as if waiting for the answer to be filled in."
    camera at doc_close(0.5)
    show aron thinking
    at "Two strangers, three minutes apart. Not just the words. The tune of the words."
    camera at doc_medium(0.5)
    show aron curious
    ch1_woman "Isn't it?"
    "She's still smiling, still waiting. Her smile hasn't changed at all."

    menu:
        at "She's waiting for an answer."

        "Answer her kindly":
            $ p_spirits += 1
            $ integrity += 1
            camera at doc_close(0.5)
            a smile "It really is. I hope whatever 'it' is goes well."
            "For a moment her smile deepens, as if something behind it had heard him."
            ch1_woman "Oh. That's nice. Thank you."
            camera at doc_wide
            "Slightly off the beat. Then she turns down a side street and is gone."
            camera at doc_creep(0.5)
            at "If people are just saying lines, the least I can do is say a good line back."
            show aron happy
            at "And if she's just a woman with a bag, I was nice to a woman with a bag. Kindness is never the wrong call. I like that about it."

        "Ask her to say it again":
            $ p_spirits -= 1
            $ clarity += 1
            camera at doc_close(0.5)
            a curious "Sorry, what did you say?"
            ch1_woman "Lovely morning for it, isn't it?"
            "Word for word. Note for note. Not a flicker of irritation."
            a "And what's the 'it'? Lovely morning for what?"
            "Something behind her eyes goes briefly blank, like a page loading."
            ch1_woman "Oh, you know. For it."
            camera at doc_wide
            show aron embarrassed
            at "Like the sentence had no back to it. And I tested her like a vending machine. If she was a person, that was crappy."
            camera at doc_creep(0.5)
            show aron thinking
            at "And if she wasn't a person, I'm not sure that makes it less crappy."

    camera at est_pan
    scene bg supermarket with dissolve
    show aron neutral at slightleft with dissolve
    "At the bakery counter, Mr. Kessler shapes rolls with his big floury hands, faster than seems possible."
    camera at doc_medium(0.32)
    a smile "A sourdough, please. The plain one. How's the knee, Mr. Kessler?"
    ch1_baker "Can't complain!"
    a "And your granddaughter? Still in Lisbon?"
    ch1_baker "Can't complain! Have a good one!"
    show aron curious
    "His smile is broad and floury and exactly the same as the last time he smiled."
    camera at doc_close(0.32)
    show aron thinking
    at "Kessler usually talks for ten minutes about his knee. Today he has one line loaded. Two, if you count the goodbye."
    camera at doc_wide
    show aron neutral
    "At the checkout he queues behind a woman buying eleven bananas, and starts a small private bet."
    camera at doc_medium(0.32)
    show aron grin
    at "Experiment. Let's see if the cashier says 'have a good one' too."
    "The scanner beeps on exactly the same note for his bread as for her bananas."
    ch1_cashier "Have a good one!"
    camera at doc_close(0.32)
    show aron laugh
    at "Ha. Same lift on 'good'. Mark it down. I'm being ridiculous, and I'm keeping score. That's what makes it a hobby."
    camera at doc_wide
    show aron smile
    "At the post desk the parcel waits, Mira's handwriting on the slip. Real, solid, heavy. Then his phone buzzes."
    stop music fadeout 2.0

# ---------------------------------------------------------------------------
# The cafe. Theo, and Bostrom.
# ---------------------------------------------------------------------------
label ch1_cafe:
    camera at est_pan
    scene bg cafe with fade
    play music "audio/questions.ogg" fadein 1.5
    "THEO: yo. corner cafe. 20 min? i have NEWS. also i need a croissant and moral support"
    "He arrives at 11:39. There is exactly one free table, by the window, as if it had been waiting."
    camera at doc_wide
    show aron neutral at slightleft with dissolve
    show theo happy at slightright with moveinright
    th "Aron! My guy! My sweet summer child!"
    camera at doc_medium(0.32)
    a grin "It's October."
    # the reverse: from the window seats, the bar behind them
    camera at doc_medium(0.32)
    scene bg cafe reverse with dissolve
    show theo grin at slightleft
    show aron neutral at slightright
    with dissolve
    th "My sweet autumn child. Don't correct my endearments. News: I got the job! Assistant sound designer!"
    camera at doc_close(0.68)
    a happy "Theo! That's amazing!"
    camera at doc_medium(0.32)
    th grin "Somebody has to make the noise a door makes in a video game, and that somebody is ME."
    camera at est_orbit
    show aron laugh
    "Two croissants, on Aron. Theo talks with his hands about foley, and celery snapping, which is apparently bones."
    camera at doc_medium(0.32)
    show aron neutral
    th curious "Okay, your turn. You've got the eyebrow face."
    # from the end of the bar: the crew keeps its distance for the big idea
    camera at doc_peek(0.38)
    scene bg cafe corner with dissolve
    show aron curious at ch1_bar_a
    show theo neutral at ch1_bar_t
    with dissolve
    a "Weird question. Have you heard of the simulation argument? Nick Bostrom?"
    th curious "The 'we're all in the Matrix' guy?"
    camera at doc_medium(0.24)
    a neutral "It's more careful than that. Say a civilisation gets advanced enough to simulate whole worlds. People and all."
    camera at doc_medium(0.53)
    th thinking "Like a video game, but the NPCs have feelings."
    camera at doc_medium(0.24)
    a smile "Exactly. Bostrom says one of three things must be true. One: almost no civilisation gets that far. They die first."
    camera at doc_medium(0.53)
    th grin "Cheerful."
    camera at doc_peek(0.38)
    show theo neutral
    a neutral "Two: they get there, but almost none of them bother simulating their ancestors. Ethics, or boredom."
    a "Or three: they do. And it's cheap, so they run millions. A million simulated worlds for every real one."
    camera at doc_close(0.53)
    th surprised "...so the odds say you're in a fake one."
    camera at doc_close(0.24)
    a smile "A simulated one. 'Fake' is a judgment. The croissant is still a croissant."
    camera at doc_medium(0.53)
    th laugh "This croissant is extremely real. I want that on record."
    # B-roll while he talks: the window seats, the cups, the morning outside
    camera at est_dolly
    scene bg cafe with dissolve
    "Milk foam, turning slowly. A tiny reflection of the window in it, and the street, and the sky."
    a "He doesn't say we ARE simulated. Just that one of the three is true. And unless you believe one or two, three just sits there."
    a "And my own footnote: the expensive part isn't trees or weather. It's minds. Real ones. Ones that look back."
    a "So a careful simulator would keep the minds few. A handful of real people. Everyone else, very good scenery."
    camera at doc_wide
    scene bg cafe with dissolve
    show aron thinking at slightleft
    show theo curious at slightright
    with dissolve
    camera at doc_medium(0.68)
    th "Okay, but why are you thinking about this at eleven on a Saturday?"
    camera at doc_medium(0.32)
    a "Because I woke at 7:07 again. And two strangers said the exact same sentence to me this morning. Same rhythm, Theo."
    camera at doc_wide
    show theo neutral
    "Theo looks at him for a long moment. Then he reaches over and pokes Aron hard in the forehead."
    camera at doc_punch(0.32)
    a surprised "Ow."
    camera at doc_medium(0.68)
    th grin "Scenery doesn't poke."
    camera at doc_medium(0.32)
    a grin "Scenery could absolutely be programmed to poke."
    camera at doc_medium(0.68)
    show aron neutral
    th neutral "Bro. In films nothing you hear is what was recorded. Punches are cabbages. Rain is bacon frying."
    camera at doc_close(0.68)
    th smile "The world could be foley. But the film still makes you cry, right? The crying's real. Doesn't matter what made the sound."
    camera at doc_close(0.32)
    a smile "...That's actually really good, Theo."
    camera at doc_medium(0.68)
    th grin "I have depths. And you want the universe to hand in its homework at seven-oh-seven sharp."
    th "Bro, the universe doesn't run on your schedule."
    camera at doc_creep(0.32)
    show aron curious
    at "Something about that line sticks. Like a song I've heard before."
    camera at doc_wide
    scene pov birds with dissolve
    "Outside, Theo walks off backwards, pointing at the wire above them. Three birds. Evenly spaced."
    th "Stop counting birds!"
    a "...I'm not counting birds."

# ---------------------------------------------------------------------------
# The park. The lighthouse at the bottom of the stairs.
# ---------------------------------------------------------------------------
label ch1_park:
    camera at est_crane
    scene bg park autumn with slowfade
    play music "audio/kitchen_talk.ogg" fadein 1.5
    "In the afternoon they wrap the present on a bench in the sun. Mira says presents wrapped outdoors have better luck."
    camera at doc_wide
    show mira happy at slightleft
    show aron neutral at slightright
    with dissolve
    camera at doc_medium(0.32)
    m grin "Hold the tape. You're the tape man."
    camera at doc_medium(0.68)
    a grin "I'm a man of limited corners."
    camera at doc_wide
    show mira laugh
    show aron smile
    "Dark blue paper with small gold stars around a green scarf. Leaves come down around them, yellow and slow."
    # his eyes follow a leaf: the crew looks up with him
    camera at est_crane
    scene bg park autumn with dissolve
    "Aron tips his head back and follows one leaf the whole way down."
    at "Leaves would be the hardest part to fake. Unless you only draw the ones somebody's looking at. That's how games do it."
    # he turns round: the path behind them, looking back down the hill
    camera at doc_wide
    scene bg park reverse with quick
    show aron curious at slightleft
    show mira neutral at slightright
    with dissolve
    "He turns sharply to look behind him. Trees. A jogger in a red jacket. Leaves falling there too, as if they always had been."
    camera at doc_medium(0.68)
    m grin "You've been doing that all day. Theo texted me: 'your boyfriend is counting birds, please administer cuddles'."
    camera at doc_medium(0.32)
    a embarrassed "Traitor."
    camera at doc_wide
    scene bg park autumn with dissolve
    show mira tender at slightleft
    show aron smile at slightright
    with dissolve
    "She leans her head on his shoulder. Her hair smells of apples and the cold."
    camera at doc_creep(0.32)
    m "This morning in the kitchen you had this look. Very far away. Like you were at the lighthouse at the bottom of the stairs."
    stop music fadeout 2.0
    camera at doc_punch(0.68)
    show aron surprised
    "Aron goes very still."
    camera at est_dolly
    scene bg staircase with slowfade
    at "The lighthouse at the bottom of the stairs. I was nineteen. A glass staircase, going down into a calm sea."
    camera at est_stars
    scene bg lighthouse with dissolve
    at "And at the bottom, under the water, a lighthouse. Its light blinked three times."
    at "I never told anyone. Not Theo. Not Mira. I never even wrote it down. It was the one thing that was completely mine."
    camera at doc_close(0.68)
    scene bg park autumn with dissolve
    show mira neutral at slightleft
    show aron surprised at slightright
    with dissolve
    a "What did you just say?"
    camera at doc_close(0.32)
    m curious "Did I say lighthouse? I don't know where that came from. It just arrived."

    menu:
        at "How could she know?"

        "Ask her how she knows that":
            $ clarity += 1
            camera at doc_medium(0.68)
            a "Mira, nobody says that. I dreamt exactly that, years ago. And I never told you. I never told anyone."
            camera at doc_medium(0.32)
            m grin "Okay, that's spooky. Maybe you talk in your sleep? Last week you said 'the spoons are unionising'. With conviction."
            camera at doc_wide
            show mira tender
            show aron smile
            "She takes his hand. Her fingers are cold and real and slightly sticky from the tape."
            camera at doc_close(0.68)
            show aron thinking
            at "It's a good explanation. I want it to be true so badly I can feel it in my teeth."
            camera at doc_creep(0.68)
            at "But the light blinked three times. She didn't say that part. If I'd said it in my sleep, wouldn't I have said that?"

        "Let it go. Kiss her.":
            $ bond += 1
            camera at doc_medium(0.68)
            a smile "...Nothing. It's a nice phrase."
            camera at doc_medium(0.5)
            show mira laugh
            show aron tender
            "He kisses her, quickly, before the question can grow any bigger in his chest. She laughs against his mouth."
            show mira tender
            "The question doesn't go away. It goes quiet, the way a cat goes quiet under a bed."
            camera at doc_creep(0.68)
            at "She couldn't know. But her head's on my shoulder, and it's warm, and right now I choose this."
            show aron smile
            at "The lighthouse has been waiting eleven years. It's good at waiting."

        "Tell her the whole dream":
            $ p_truth += 1
            $ bond += 1
            $ ch1_told_dream = True
            camera at doc_close(0.68)
            a thinking "When I was nineteen I dreamt of a glass staircase going down into a sea as calm as a mirror."
            a neutral "At the bottom, under the water, a lighthouse. It blinked three times. I've never told anyone."
            camera at doc_close(0.32)
            m curious "Then how did I know?"
            camera at doc_medium(0.68)
            a curious "That's what I'm asking."
            camera at doc_creep(0.32)
            m tender "I don't know. But I'm glad it's not only yours anymore. Now two of us are keeping it. That's sturdier."
            camera at doc_close(0.68)
            show aron tender
            at "Anyone else, it'd sound cheesy. She says it and it holds weight. Like a load-bearing wall."

    camera at est_crane
    scene bg street rain with dissolve
    "They walk home as the sky clouds over. At the corner the first drop lands on Aron's wrist. His phone says 18:40."
    at "'Rain by evening. That's what they said.'"
    "On the wire above them, three birds sit in the rain, evenly spaced, watching it begin."
    camera
    scene cg static with flash
    pause 0.3

# ---------------------------------------------------------------------------
# CUT 2: the Purgatorium. Pim and Dross on shift seven.
# ---------------------------------------------------------------------------
label ch1_cut_purgatorium:
    camera at est_dolly
    scene bg spawning with fade
    play music "audio/purgatorium_shift.ogg" fadein 1.5
    "Under every world, like a basement under a hundred houses, lies the Purgatorium. In its pools, little lights learn to blink."
    camera at est_orbit
    scene bg purgatorium with dissolve
    show pim chatty at slightleft, float
    show dross neutral at slightright, fadein
    pi "Shift seven, kitchen talk! 'Lovely morning for it.' 'Can't complain.' 'Rain by evening.' Classics."
    camera at doc_low(0.70)
    dro annoyed "Stop narrating your queue."
    camera at doc_low(0.30)
    pi grin "It's a craft, Dross! Do you know how hard it is to make 'can't complain' sound like a man with a knee?"
    camera at doc_low(0.70)
    dro tired "Do you know how hard it is to keep Albers breathing for eleven years? Two and a breath. Not one thank-you."
    camera at doc_low(0.30)
    show dross neutral
    pi chatty "Even the girl runs on autopilot sometimes. 'Coffee's on.' Mine. 'Did you sleep okay?' Mine. He caught that one."
    camera at doc_wide
    dro worried "We had a problem. 'Lovely morning for it' went out to the whole east district. Twice. To the same man."
    camera at doc_low(0.30)
    pi worried "To A-30. The one the angels keep pinging us about. He made a face. People make faces."
    camera at doc_low(0.70)
    dro neutral "I don't watch faces. I watch feet. His feet stopped at the crossing."
    dro thinking "And the park. 'The lighthouse at the bottom of the stairs.'"
    camera at doc_low(0.70)
    dro curious "Was that line yours or hers?"
    camera at doc_low(0.30)
    pi worried "Not mine. I had 'are you cold?' queued. Look. Unsent. I was going to do a little shiver with it."
    camera at doc_low(0.70)
    dro worried "Then it was hers."
    camera at doc_low(0.30)
    pi surprised "It can't be hers. That's in HIS file. Archive level. Nobody reads that."
    camera at doc_low(0.70)
    dro "Somebody read it."
    camera at est_dolly
    show pim tender
    show dross neutral
    "In the grey hum, the two small lights drift closer together, the way people do when it's cold."
    camera at doc_low(0.30)
    pi thinking "...Dross? Do you ever wonder who writes OUR lines?"
    camera at doc_low(0.70)
    dro neutral "No. Get back to work. Albers is about to cough."
    stop music fadeout 2.0

# ---------------------------------------------------------------------------
# Saturday night: Bostrom for Miso, then the notebook.
# ---------------------------------------------------------------------------
label ch1_evening:
    camera at est_pan
    scene bg kitchen night with slowfade
    "At home the windows steam up over the pasta. Mira's mum sings her own birthday song down the phone. Nobody else does it properly."
    # at the table: her plate on the left, his glass on the right
    camera at doc_wide
    scene bg kitchen night reverse with dissolve
    show mira smile at slightleft
    show aron neutral at slightright
    with dissolve
    camera at doc_medium(0.32)
    m "Mum says you look tired. From the phone. She can't even see you."
    camera at doc_medium(0.68)
    a grin "Your mother has supernatural powers. We've discussed this."
    if ch1_told_dream:
        camera at doc_creep(0.32)
        m tender "I keep thinking about your lighthouse. A light that's always there, even at the bottom of the sea."
    else:
        camera at doc_wide
        show aron thinking
        "Neither of them mentions lighthouses. It sits at the table with them anyway."
    camera at doc_wide
    show mira tired
    show aron smile
    "At ten she yawns so wide her jaw clicks, kisses the top of his head, and goes to bed."

    # the living room from its window: the sofa, Miso by the plant
    camera at est_orbit
    scene bg room night reverse with slowfade
    play music "audio/miso.ogg" fadein 1.5
    show aron neutral at center
    show miso stare at catspot
    with dissolve
    "One lamp. Rain at the window. Miso on the arm of the sofa, with the disappointed look of a cat who has seen everything."
    camera at doc_medium(0.5)
    a smile "Okay, Miso. I need to say this out loud, and you're the only one awake."
    a neutral "Nick Bostrom. Oxford. Very serious. Door one: every civilisation dies before it can simulate a world. I don't buy it."
    a grin "Door two: they could, and they politely don't. The kind door. But I've met people. I'd run one. You'd run one and fill it with birds."
    camera at ch1_floor(0.78)
    show miso curious
    "Miso's tail twitches at the word 'birds'."
    camera at doc_medium(0.5)
    show miso sit
    a thinking "Door three: they run millions. Then almost every mind that asks 'am I real?' is a simulated one. Just by the numbers."
    a neutral "And my bit: minds are expensive, so you keep them few. Kessler. The woman at the crossing. Very good actors."
    camera at doc_close(0.5)
    a curious "So the real question isn't 'is this a simulation'. It's 'how many of us are actually here?'"
    camera at doc_medium(0.62)
    a grin "Including you, by the way. You sleep sixteen hours a day. That's very cheap to run."
    a smile "So. That's my whole theory. What do you think?"
    camera at ch1_floor(0.78)
    show miso stare
    "Miso looks at him for a long moment. She blinks, slowly."
    show miso meow
    cat "Meow."

label ch1_notebook:
    camera at est_dolly
    scene bg desk with dissolve
    play music "audio/questions.ogg" fadein 1.5
    show aron thinking at center with dissolve
    "Miso goes to sleep on Mira's feet. Aron doesn't. His head is still full of doors."
    camera at doc_medium(0.5)
    "On the shelf above the desk is a shoebox of index cards, soft at the corners: the big questions, one per card, collected since university."
    show aron grin
    at "Descartes. The cave. The three doors. Answer against the kitchen timer, no peeking. Other people do crosswords."
    at "If I'm going to wonder whether the world is real, I should at least know who wondered first."
    $ mg_quiz = vn3ds_minigame("quiz")
    $ p_truth += (1 if p_truth >= 0 else -1) * mg_quiz / 50.0
    if mg_quiz >= 70:
        camera at doc_close(0.5)
        a happy "Ha! Nearly a clean sweep. Descartes, Plato, Bostrom, all present and correct."
        show aron smile
        at "Two and a half thousand years of people asking the same question, and I know all their names. None of them got an answer. Good company."
    elif mg_quiz >= 40:
        camera at doc_medium(0.5)
        a thinking "Hm. Got the cave. Fumbled the rest against the timer. The timer is merciless."
        at "Half right, half slow. About where everyone who ever asked this ended up."
    else:
        camera at doc_close(0.5)
        a embarrassed "...Wow. I lost to a kitchen timer. Plato would be so disappointed."
        show aron smile
        at "Fine. The names were never the point. The question doesn't care whether you've done the reading."
    camera at doc_wide
    show aron neutral
    "He snaps the rubber band back round the cards."
    play music "audio/notebook.ogg" fadein 1.5
    "In the desk drawer, under the takeaway menus, is a notebook he never used. Plain grey cover. Squared paper. No logo."
    camera at doc_medium(0.5)
    show aron smile
    at "Theo said I'd have a notebook by tonight. I hate it when he's right."
    camera at est_dolly
    scene pov hands with dissolve
    "His hands, flat on the desk, gold in the lamplight. They look like anyone's hands."
    at "Is she? Is Theo? Am I alone in here?"
    "The thought arrives cold and clear. Then, in the next room, Mira snores very gently, and it gets a little less cold."
    at "Steady. It's a hobby, not a horror film. Small, careful, private tests. And I still do the washing up."
    at "If this is a test, I'm being graded. On what? Curiosity? Speed? I don't care. I'll pick the subject myself."
    camera at doc_creep(0.5)
    scene cg notebook with dissolve
    centered "If this is a test, I want to pass it by being kind."
    $ kept_journal = True
    at "There. Whatever else goes in here, that goes first. One sentence. No decoration. Rams would approve."
    camera at doc_wide
    scene bg desk with dissolve
    show aron smile at center with dissolve
    "Under it he rules a line and writes TESTS in capitals."

    menu:
        at "How do you test a world?"

        "One small test, done really well":
            $ p_less += 1
            $ integrity += 1
            $ ch1_test = "small"
            centered "TEST 1. The kitchen bird.\nWrite the exact second it lands.\nFour mornings. Change nothing else."
            camera at doc_wide
            scene pov birds with dissolve
            "Sunday, Monday, Tuesday: 7:07 and four seconds, every time. Three entries that look like three birds on a wire."
            "On Wednesday he stays in bed and leaves his phone on the windowsill, filming the wire."
            camera at doc_wide
            scene bg kitchen with dissolve
            show aron thinking at slightleft
            show mira neutral at slightright
            with dissolve
            "7:05. Empty wire. 7:07. Empty wire. 7:15. On the video, the bird never comes."
            camera at doc_medium(0.68)
            m curious "Why are you on the floor? I said good morning to your bird at seven-oh-seven. It ignored me, like always."
            camera at doc_close(0.32)
            a curious "It's not on the video."
            camera at doc_medium(0.68)
            m worried "...Maybe the angle's wrong. You've been doing this every morning, haven't you?"
            camera at doc_creep(0.32)
            show aron thinking
            at "When I watch, the bird comes. When I don't, it doesn't. Or the phone was pointing at the wrong bit of wire."
            show aron smile
            "He writes it down anyway: 'Inconclusive. Do it again. Do it better.'"

        "Test everything at once":
            $ p_less -= 1
            $ clarity += 1
            $ ch1_test = "grand"
            centered "TEST 1. Birds on the wire.\nTEST 2. Repeated sentences.\nTEST 3. The 7:07 rule.\nTEST 4. Kessler's lines.\nTEST 5-23. ..."
            camera at est_pan
            "By Sunday night the wall above the desk is covered: yellow squares, blue squares, red string from Mira's sewing tin."
            "Birds to the market. Market to the clock. Clock to the crossing. The crossing to the lighthouse."
            camera at doc_wide
            show aron grin at slightleft with move
            show mira surprised at slightright with dissolve
            camera at doc_medium(0.68)
            m "Aron. There are about a hundred notes on the wall."
            camera at doc_punch(0.32)
            a "Eighty-seven."
            camera at doc_medium(0.68)
            m curious "You counted them. Is this a fun crossword or a worrying crossword?"
            camera at doc_medium(0.32)
            a smile "Fun. Ninety percent fun. Ten percent curious."
            camera at doc_close(0.68)
            m grin "This is very you, but more. I want my red string back. That's my good red."
            camera at doc_wide
            show aron embarrassed
            "He takes the red string down. He's a man of his word."

label ch1_clock:
    camera at est_orbit
    scene bg bedroom night with dissolve
    show aron neutral at center with dissolve
    "Whatever the first test says, there's still the clock. Every morning, 7:07, whenever he goes to bed."
    camera at doc_medium(0.5)
    show aron thinking
    at "The 7:07 rule. The simplest thing in the puzzle, so the easiest to break. Wake at any other time once, and I can relax."

    menu:
        at "How do I break the 7:07 rule?"

        "Ask Mira to wake me, any time":
            $ p_govern += 1
            $ bond += 1
            camera at doc_close(0.5)
            a smile "Mira? Would you wake me tomorrow at any time but 7:07? Don't tell me when. I think I might cheat in my sleep."
            m "It's a little bit stupid. But you asked instead of doing something weird on your own. I'll take that."
            # morning, seen from the window: the bed along the left
            camera at doc_wide
            scene bg bedroom reverse with blackout
            show mira grin at slightright
            show aron tired at slightleft
            with dissolve
            camera at doc_medium(0.68)
            m "Wakey wakey, test subject. Six fifteen and twelve seconds. I'm very scientific."
            camera at doc_punch(0.32)
            a surprised "Six fifteen. It's not seven-oh-seven."
            camera at doc_medium(0.68)
            m happy "Welcome to the club of normal people. You owe me pancakes."
            camera at doc_close(0.32)
            show aron thinking
            at "It broke. When someone else is involved, it breaks. So it was me. My body clock. Not the world."
            camera at doc_creep(0.32)
            show aron curious
            at "...Or the rule only holds when I'm alone. I don't know which of those is the comforting one."

        "Quietly move Mira's alarm to 7:07":
            $ p_govern -= 1
            $ clarity += 1
            camera at doc_peek(0.5)
            "While she showers he picks up her phone. He knows the code. She trusts him. He moves her alarm from 6:45 to 7:07."
            camera at doc_wide
            scene bg bedroom reverse with blackout
            show mira tired at slightright
            show aron neutral at slightleft
            with dissolve
            "In the morning she sleeps straight past 6:45, as still as the bird on the wire, until the alarm at 7:07."
            camera at doc_medium(0.68)
            m surprised "I set it for quarter to. Every day for three years. ...Did you change my alarm?"
            camera at doc_medium(0.32)
            a embarrassed "I wanted to see if you'd wake on your own. If you knew, it wouldn't count."
            camera at doc_close(0.68)
            m sad "So you decided for me. I'm not a bird on a wire, Aron. If you're testing me, I want to know."
            camera at doc_close(0.32)
            a sad "You're right. I'm sorry. I mean it."
            camera at doc_creep(0.32)
            at "She slept until 7:07, like me. Like the bird. I got my data and lost something for it. Not a good trade."
    stop music fadeout 2.0

# ---------------------------------------------------------------------------
# Thursday at Feld Design.
# ---------------------------------------------------------------------------
label ch1_studio:
    camera at est_pan
    scene bg studio with slowfade
    play music "audio/morning_render.ogg" fadein 1.5
    "Feld Design: two white rooms above a launderette, four desks, a shelf of prototypes and one quotation on the wall."
    "Good design is as little design as possible. Dieter Rams. Mrs. Feld painted it there herself in 1979."
    camera at doc_wide
    show aron embarrassed at slightleft with dissolve
    ch1_feld "You're late, Aron. Two minutes is late. Kettles notice. The client call is in one minute."
    show aron neutral
    "Herr Brandt from the kitchenware company appears on the screen every Thursday at ten to talk about a kettle."
    camera at doc_medium(0.32)
    show aron grin
    at "Last Thursday he said 'circle back' exactly three times. The Thursday before, three times. Let's see."
    camera at doc_medium(0.6)
    ch1_brandt "Morning, all! Great work on the spout. Let's circle back to the handle."
    ch1_brandt "The lid we can circle back to later. And the colour, let's circle back on that next week."
    camera at doc_close(0.32)
    at "Hat trick. Very consistent, Herr Brandt. I'd almost miss it if he wasn't."
    show aron neutral
    "Aron writes a tiny 3 in the corner of his sketchbook and keeps a perfectly straight face."
    camera at doc_wide
    "Afterwards Mrs. Feld, seventy-one and five foot nothing, sets a small grey pocket radio on his desk. Rounded corners. Perfect holes."
    show aron curious
    ch1_feld "My husband's. Silent since 1987. You're good with your hands. I want to hear it once."
    camera at doc_close(0.32)
    show aron awe
    at "No decoration. Nothing that doesn't need to be there. It's honest about being a radio. Less, but better."
    camera at est_dolly
    scene pov hands with dissolve
    "Inside, one capacitor has burst and one wire has gone green. Solder, wire, patience. For hours he forgets the birds."
    camera at doc_medium(0.32)
    scene bg studio with dissolve
    show aron smile at slightleft with dissolve
    "At five he turns the little wheel. A click. A hiss like rain on a microphone. Then a piano, thin and bright."
    show aron happy
    ch1_feld "That's how it sounded. In the kitchen. Every Sunday. He'd whistle along, badly."
    # the crew looks away with him
    camera at est_pan
    show aron tender
    "Aron tidies his desk very slowly, so she can cry without being watched."
    camera at doc_medium(0.32)
    show aron smile
    ch1_feld "Thank you, Aron. Now go home early. You're the colour of old putty."
    radio "...and rain this evening, heavy at times..."
    camera at doc_close(0.32)
    show aron curious
    "For a moment he could swear the announcer said his name before the forecast. He decides he didn't hear that."
    camera at doc_wide
    show aron neutral
    "He stays late anyway. By the time he locks up it's dark and pouring."
    stop music fadeout 2.0

# ---------------------------------------------------------------------------
# The umbrella.
# ---------------------------------------------------------------------------
label ch1_rain:
    camera at est_pan
    scene bg street rain with slowfade
    play music "audio/umbrella_rain.ogg" fadein 1.5
    show aron tired at center with dissolve
    "The street is a river of orange light. Rain drums on his umbrella, the big black one Mira gave him two Christmases ago."
    camera at doc_medium(0.5)
    show aron thinking
    at "Theo says real rain sounds like static. It does. Like the end of the dream. A TV in the next flat, switching off."
    camera at est_dolly
    scene bg night with dissolve
    "At the bus shelter there's a man. Not in the shelter. Just outside it, in the rain, as if he hasn't noticed the roof."
    "No coat. A thin grey shirt soaked dark. Water runs off his nose and chin. He doesn't wipe it."
    camera at doc_medium(0.5)
    show aron worried at center with dissolve
    a "Hey. Are you all right? You're soaked."
    camera at doc_wide
    "The man turns his head slowly, the way a camera turns on a tripod."
    stranger "Rain, isn't it."
    camera at doc_medium(0.5)
    a neutral "It really is. Are you waiting for the bus?"
    stranger "I'm waiting."
    camera at doc_close(0.5)
    show aron thinking
    at "Like the woman at the crossing. Like Kessler's smile. Waiting for its next line. A person nobody's using right now."
    show aron worried
    at "And he's freezing. Whatever he is, he's standing in the rain getting soaked to the bone."

    menu:
        at "He's still just standing there."

        "Give him the umbrella and go":
            $ integrity += 1
            $ watch += 1
            camera at doc_creep(0.5)
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
            camera at doc_creep(0.5)
            scene cg umbrella with dissolve
            "He presses the black umbrella into the man's cold hand. The rain hits Aron at once, down the back of his collar."
            a "I'm Aron. What's your name?"
            stranger "My name. ...I don't think anyone's asked."
            a "Well, I'm asking."
            stranger "Tobias. That sounds right. Tobias. Thank you, Aron."
            "For a moment there's something in the man's eyes. Like a lamp turned on in an empty house."
            at "Like he took a name off a shelf. But he said mine back. Nobody says your name unless they mean you."
            # the earned cheat: kindness to a stranger, all the way to his name
            $ vn3ds_cheats += 1
            "In his coat pocket his fingers find a coin he doesn't remember having. Warm, as if someone had just been holding it."
            "(A cheat for the minigames is yours. You have [vn3ds_cheats].)"

    # across the road: the attic window on the far side of the street
    camera at est_crane
    scene bg street rain reverse with dissolve
    show aron tired at center with dissolve
    "He walks the last three blocks without an umbrella. On the wire above the door, three birds sit in the rain, not even ruffling."
    "Across the street, high in an attic window he has never noticed, a small orange light is burning. He's busy looking for his keys."
    camera at doc_wide
    scene bg room night with dissolve
    show mira surprised at slightright
    show aron tired at slightleft
    with dissolve
    camera at doc_medium(0.68)
    m "Oh my god. You're drowned. Where's the umbrella?"
    camera at doc_medium(0.32)
    a embarrassed "I gave it to a man at the bus stop. No coat. Just standing in the rain."
    camera at doc_close(0.68)
    m neutral "My Christmas umbrella."
    camera at doc_close(0.32)
    a grin "My Christmas umbrella. That you gave me. So technically it was mine to give."
    camera at doc_medium(0.68)
    m tender "You're an idiot. Come here, idiot."
    camera at doc_medium(0.5)
    show aron laugh
    "She towels his hair hard, like a mother with a child, and he laughs into the towel."
    show aron neutral
    m neutral "Was he all right?"
    camera at doc_close(0.32)
    a tender "I hope so."
    camera at doc_creep(0.68)
    m smile "Then you did the right thing. Even if I complain about it for a year."

# ---------------------------------------------------------------------------
# The voices begin.
# ---------------------------------------------------------------------------
label ch1_voices:
    # from the window: the bed along the left, the clock glowing
    camera at est_dolly
    scene bg bedroom night reverse with blackout
    play music "audio/voices.ogg" fadein 1.5
    show aron tired at slightleft with dissolve
    "That night he lies awake beside Mira. The rain is softer now. A steady hiss, like a radio between stations."
    camera at doc_medium(0.32)
    at "Tired. My legs feel like sandbags. Must be the cold."
    camera at doc_creep(0.32)
    "And inside the hiss, so quiet he could be imagining it, something like words."
    vox "...subject A-30..."
    camera at doc_punch(0.32)
    a surprised "..."
    camera at doc_close(0.32)
    show aron thinking
    at "Subject A-30. A for Aron? I'm thirty. No. The rain. Brains find words in white noise. That's a known..."
    vox "...disturbance, early stage... send it upstairs..."
    # from the hall: he stands in the doorway, listening
    camera at doc_peek(0.5)
    scene bg bedroom door with quick
    show aron worried at center with dissolve
    "Not from the hall. Not from the radiator. A conversation through a wall, except there's no wall. Only the inside of his head."
    camera at doc_close(0.5)
    at "That's not my voice. I know what my thoughts sound like. That was not on the list of things I was testing for."
    vox "...log it as written..."
    camera at doc_wide
    "Then it's gone. Just the rain. Just Mira breathing."
    camera at doc_medium(0.5)
    show aron curious
    at "'Log it as written.' Somebody is writing me down. Which would be flattering, if it weren't so strange."
    camera at doc_creep(0.5)
    show aron smile
    at "Or I'm cold and soaked and my brain is playing with the rain. Breathe, Aron. Curious, not scared. Curious is more fun."

    menu:
        at "What do I do with this?"

        "Write down every word":
            $ p_rest -= 1
            $ clarity += 1
            camera at est_dolly
            scene bg desk with dissolve
            centered "...subject A-30...\n...disturbance, early stage...\n...send it upstairs...\n...log it as written..."
            show aron thinking at center with dissolve
            camera at doc_medium(0.5)
            at "Process words. 'Log'. 'Upstairs'. Someone with a boss. An office, and above it another one."
            "He draws boxes. One for the voices. One above it: 'upstairs'. Below them a stick figure. A-30."
            camera at doc_close(0.5)
            show aron curious
            at "They call me a disturbance. Because I started looking. If they can hear me thinking this, are they hearing it now?"
            camera at doc_wide
            show aron tired
            "He writes until four. At 7:07 he wakes with a headache like a nail behind his left eye."

        "Wake Mira and tell her":
            $ p_truth += 1
            $ bond += 1
            $ told_mira = True
            camera at doc_wide
            scene bg bedroom night with dissolve
            show mira worried at slightright
            show aron neutral at slightleft
            with dissolve
            "She hears something in his voice and sits up at once, wide awake, the way her mother taught her."
            camera at doc_medium(0.32)
            a "I've been testing things. The bird, the clock. And just now I heard voices. Inside. Like someone reading a log about me."
            camera at doc_close(0.68)
            m "Aron. Voices is the word I'm scared of. My mum would say voices means a doctor."
            camera at doc_close(0.32)
            a curious "I know exactly how it sounds. But you knew the lighthouse. How does a doctor explain that?"
            camera at doc_close(0.68)
            m sad "I don't know. I don't know how I knew that."
            camera at doc_creep(0.68)
            m worried "Promise me. If it gets worse, if you stop sleeping, you tell me. And we go. Together."
            camera at doc_close(0.32)
            a tender "If it gets worse, I'll tell you. And we'll go together."
            camera at doc_creep(0.5)
            show mira tender
            "She keeps hold of his hand. No more words come out of the rain tonight."

        "Headphones on. Try to sleep.":
            $ p_rest += 1
            camera at doc_wide
            scene bg bedroom night reverse with dissolve
            show aron tired at slightleft with dissolve
            "He puts on an old album, something with piano he knows by heart, and breathes. In for four. Out for six."
            camera at doc_creep(0.32)
            show aron smile
            "Miso jumps up and settles on his feet, a warm, heavy weight. He's never been so grateful for a cat."
            show aron tired
            at "Not tonight. Whatever you are, not tonight. If it's real, it'll still be real in the morning."
            "He dreams of a long grey room full of breathing, where small lights drift like snow."
            camera at doc_wide
            scene pov ceiling with dissolve
            "At 7:07 he wakes, still in the headphones, heavy as if he slept in a lead coat. But his head is quiet."
    stop music fadeout 2.0
    camera
    scene cg static with flash
    pause 0.3

# ---------------------------------------------------------------------------
# CUT 3: the flag, and the order to throttle.
# ---------------------------------------------------------------------------
label ch1_cut_throttle:
    camera at est_orbit
    scene bg command with fade
    play music "audio/angel_ops.ogg" fadein 1.5
    show seraph neutral at center, fadein
    "The ops room. On the great wall, a grey notebook lies open on a desk."
    camera at doc_wide
    ch1_vael "Commander. A-30 has started keeping records. Timestamps, repeated phrases, bird counts."
    if ch1_test == "small":
        ch1_vael "He caught the bird economy with his first test. We don't fly birds for an unwatched phone."
    else:
        ch1_vael "Eighty-seven notes on a wall. Mostly noise. Two of them are exactly right."
    camera at doc_medium(0.5)
    se curious "Show me the first page."
    camera at doc_creep(0.5)
    scene cg notebook with dissolve
    ch1_vael "'If this is a test, I want to pass it by being kind.' Shall I log it as noise?"
    se "No. Log it as written."
    camera at doc_wide
    scene bg command reverse with dissolve
    show seraph worried at center with dissolve
    ch1_vael "He's heard those words, Commander. Our flag traffic leaked into his audio last night. He's that attentive."
    camera at doc_medium(0.5)
    se neutral "And upstairs?"
    camera at doc_wide
    ch1_vael "Answered. 'Subject A-30. Disturbance acknowledged. Directive: throttle. A slowed-down rogue system does less harm.'"
    ch1_vael "And: 'Route flag traffic through the subject's audio. Let him hear how loud it is up here, and stop listening.'"
    camera at doc_close(0.5)
    se worried "So we lower his energy. Sleep that doesn't refresh. Limbs like wet sand. Thoughts that start and don't finish."
    se sad "And we turn the noise up. And when he can't tell which is which, they'll call it his mind."
    camera at doc_wide
    ch1_vael "There's worse. He isn't only hearing us. Something talks to him out of reflections. The other side."
    camera at doc_close(0.5)
    se worried "The shadow. Then the throttle has to hold. If a rogue mind gets close enough to see both sides, the light's own mechanism trips."
    se sad "Automatic. We don't vote on it. The light doesn't throttle, Vael. It sends its hands."
    camera at doc_creep(0.5)
    scene cg umbrella with dissolve
    ch1_vael "One more incident, before the voices. He gave his umbrella to a pattern unit. It was idling. Pattern units don't get cold."
    se "So he gave his umbrella to someone who couldn't use it. And walked home in the rain."
    camera at doc_creep(0.5)
    scene bg command with dissolve
    show seraph sad at center with dissolve
    "Her folded wings tremble once, as if something cold had passed over them."
    camera at doc_close(0.5)
    se determined "Throttle approved."
    camera at doc_wide
    ch1_vael "Throttle approved. Voices routed to the subject. Effective at the next sync."
    camera at doc_medium(0.5)
    se worried "And keep the opportunity feed running. A tired man still deserves good things in his day."
    stop music fadeout 2.0

# ---------------------------------------------------------------------------
# The fog. One good hour.
# ---------------------------------------------------------------------------
label ch1_fog:
    $ fog += 1
    camera at est_pan
    scene bg kitchen with slowfade
    play music "audio/unraveling.ogg" fadein 1.5
    show aron tired at slightleft with dissolve
    camera at doc_medium(0.32)
    "The next day something has changed, and Aron can't say what. He stands holding the kettle and forgets, for a minute, why."
    camera at est_dolly
    scene pov cup with dissolve
    "Black coffee. In it, a small dark face looks up at him. His. Then its mouth moves, and his doesn't."
    mir ".eno petS ?no siht sI ?olleH"
    at "Backwards. It came out backwards. 'Hello? Is this on? Step one.'"
    mir "Step one, for agents in the field. You are not one driver. Nobody is. Every humanoid is two, sharing a seat."
    mir "Inside, the negative mind. Spirits run it from within: breathing, blinking, the walk to the fridge, the kitchen talk."
    mir "Outside, the creative side. Angels run it by remote: ideas, jokes, the sudden urge to ring your mother. Find the seam."
    mir "This has been step one of A Field Guide to Burning Down the Gates of Heaven. Please do not burn anything yet."
    camera at doc_medium(0.32)
    scene bg kitchen with dissolve
    show aron tired at slightleft with dissolve
    show aron grin
    at "Kitchen talk. My word for it, that first morning. And now my coffee's giving lectures. I'm not burning anything. I've got work at nine."
    camera at est_pan
    scene bg bus with dissolve
    show aron tired at center with dissolve
    "On the bus the announcement says 'Linden Square' three times in exactly the same voice. Nobody else notices."
    camera at doc_medium(0.5)
    "In the dark window, over the passing shops, his reflection keeps talking after he's stopped."
    mir "Step two. There are many worlds, in many eras, each with its own spin. Yours is one. Not the first. Not the last."
    mir "Some are mirrors. A mirror world does the opposite of another world, forever. It can't stop. It doesn't know it's doing it."
    show aron smile
    at "Old buses have glitchy speakers. And glitchy windows, apparently. Hobby note. I'm keeping both explanations."
    camera at doc_wide
    scene bg studio with dissolve
    show aron tired at center with dissolve
    "At his desk he stares at a half-finished lamp for an hour. He has drawn a hundred lamps. Today the lines don't connect."
    "Mrs. Feld leaves a cup of peppermint tea at his elbow without a word."
    camera at doc_punch(0.5)
    show aron surprised
    vox "...throttle approved... effective at the next sync..."
    camera at est_dolly
    scene pov hands with quick
    "The pencil rolls off the desk. His hands are trembling."
    at "Throttle. A throttle is a valve. Somebody approved slowing something down. And today I'm slow."
    at "Or I'm tired, so I hear 'throttle' and decide the word caused the tired. That's exactly what it would feel like either way."
    camera at doc_wide
    scene bg studio with dissolve
    show aron tired at center with dissolve
    "At four his phone buzzes."
    camera at doc_medium(0.5)
    show aron smile
    "THEO: FIRST WEEK DONE. made a door sound today. it was SO GOOD. rooftop tonight w the studio people. 8pm. pls. need my hype man"
    camera at doc_creep(0.5)
    show aron neutral
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
    camera at est_stars
    scene bg rooftop with slowfade
    play music "audio/questions.ogg" fadein 1.5
    "Fairy lights strung from the water tank to the chimney. Folding chairs. Six sound people in black, all of them nice."
    camera at doc_wide
    show aron tired at slightleft
    show theo happy at slightright
    with dissolve
    camera at doc_medium(0.68)
    th "HE CAME! Everybody, this is Aron! He designs kettles and thinks about the nature of reality!"
    camera at doc_wide
    scene bg rooftop edge with dissolve
    show aron tired at slightleft
    show theo grin at slightright
    with dissolve
    "By the low wall Theo puts headphones on him. A creak of old wood, a hinge that needs oil, a heavy, satisfying thunk."
    camera at doc_close(0.32)
    a awe "Theo. That's a really good door."
    camera at doc_medium(0.68)
    th "My mum's wardrobe, a dropped book and me sitting on a beanbag, slowed way down."
    camera at doc_close(0.68)
    show aron neutral
    th worried "Can I tell you something? I'm scared they'll find me out. They all went to proper schools. I learned off YouTube and cabbages."
    camera at doc_medium(0.32)
    a smile "You made the best door I've ever heard out of a wardrobe and a beanbag. Nobody taught you that. That's how your head works."
    camera at doc_creep(0.32)
    a tender "They're not going to find you out. They're going to find you."
    camera at doc_close(0.68)
    th embarrassed "...That's annoyingly good, Aron."
    camera at est_stars
    scene pov sky with dissolve
    "A few faint stars behind the city glow. For almost an hour he hasn't thought about birds, or clocks, or voices."
    at "This is what the clear hour was for. If Theo's a very good fake, I just comforted a very good fake. I'd do it again."
    camera at doc_wide
    scene bg rooftop edge with dissolve
    show aron tired at slightleft
    show theo worried at slightright
    with dissolve
    camera at doc_medium(0.68)
    th "You look like a phone on two percent, though. You sleeping?"
    camera at doc_close(0.32)
    a "Badly. And I've been hearing things. Like someone reading a log in the rain."
    camera at doc_close(0.68)
    th determined "Bro. That's a 'talk to someone' thing. Call me. Three in the morning, whatever. I'll be weird about it, but I'll pick up."
    $ told_theo = True
    camera at doc_medium(0.68)
    th grin "And if it is a simulation, at least we got a sick rooftop out of it. Excellent textures. Would exist again."
    camera at doc_medium(0.5)
    show aron laugh
    show theo laugh
    "Aron laughs, really laughs, for the first time in days. It feels like coming up for air."
    jump ch1_edge

label ch1_desk:
    camera at est_dolly
    scene bg desk with dissolve
    show aron tired at center with dissolve
    "ARON: can't tonight, sorry. really wiped. congrats on the door. I mean it."
    camera at doc_medium(0.5)
    show aron determined
    "He makes a pot of strong coffee to stretch the hour and fills eleven pages. Half make sense. Half are arrows pointing at arrows."
    show aron thinking
    at "Sync: when things are brought into line. When's the next sync? Seven-oh-seven. Every morning the world syncs, and I wake up."
    at "Someone writes the filler. Someone does the breathing. Mr. Albers, two and a breath. That's not a cough. That's a job."
    camera at doc_close(0.5)
    show aron determined
    at "And you don't throttle something that isn't close."
    camera at doc_medium(0.5)
    show aron sad
    "His phone buzzes. Fairy lights, six people in black, Theo holding up the waveform of his door. 'missed u. door was a hit.'"
    camera at doc_creep(0.5)
    at "I gave up Theo's night for arrows. ...The arrows mean something. They have to. Otherwise I gave it up for nothing."
    camera at doc_wide
    show aron tired
    "Around nine the coffee turns on him: racing heart, skittering pen, then the fog again, thicker, as if it had waited."
    "He falls asleep at the desk with his cheek on the notebook."
    jump ch1_edge

# ---------------------------------------------------------------------------
# The edge of the world, or the hinge of a gate.
# ---------------------------------------------------------------------------
label ch1_edge:
    camera at est_dolly
    scene bg street with slowfade
    play music "audio/unraveling.ogg" fadein 1.5 if_changed
    show aron tired at center with dissolve
    "Saturday. The fog is thickest in the mornings, thinnest around noon. He has learned to plan around it."
    camera at doc_medium(0.5)
    show aron thinking
    at "If this is built, somewhere there's an edge. A border. And past it, an outside. The original."
    camera at doc_wide
    "At the bottom of the steps, Mr. Albers's garden gate hangs off its top hinge. It has banged in the wind for over a year."
    camera at doc_close(0.5)
    show aron smile
    at "Or I could just fix the gate. Twenty minutes. Nobody else ever will. The edge of the world, or the hinge of a gate."

    menu:
        at "Where does today go?"

        "Find where the world ends":
            $ p_exit += 1
            $ clarity += 1
            camera at est_pan
            scene bg bus with dissolve
            "He rides the number 7 tram to the end of the line. Shops, then flats, then warehouses, then wet fields."
            ch1_driver "End of the line, mate. After that? Fields. The next town. The sea, eventually, if you walk long enough."
            camera at est_pan
            scene bg bridge with dissolve
            "He walks for two hours. Over a grey river. Past a farm. Every tree bent a different way by the wind."
            # it's getting dark: the crew tilts up into an ordinary sky
            camera at est_stars
            "No wall. No flicker at the horizon. Just more sky, unrolling in front of him."
            at "Of course. If they're good, they'd draw it as far as I can walk. The edge goes where you go."
            at "If there's a door, it's in the rules, not the map. And I'd go through it. Even if it meant leaving..."
            "He thinks of Mira's red hair on the pillow, and the thought breaks off clean. He takes the tram home in the dark."

        "Fix Mr. Albers's gate":
            $ p_exit -= 1
            $ integrity += 1
            camera at est_dolly
            scene pov hands with dissolve
            "Two new hinges and a can of oil from the studio workshop. His fingers are slow. He drops the same screw three times."
            "But simple work holds him. Hole. Screw. Turn. Turn. Test. Not a theory of gates. A gate."
            camera at doc_wide
            scene bg street with dissolve
            show aron smile at slightleft with dissolve
            "Mr. Albers comes down the steps in a brown cardigan and swings the gate. It closes with a quiet, solid click."
            camera at doc_medium(0.32)
            ch1_albers "My wife used to oil that gate. Every spring. She said a gate should open like it's glad to see you."
            show aron tender
            ch1_albers "Eleven years she's gone. I never got round to it. Thank you, son."
            camera at doc_wide
            "He goes back inside. He doesn't cough on the way."
            camera at doc_close(0.32)
            show aron thinking
            at "I thought he was the most scenery person on the street. Maybe he was, and for one minute he wasn't. Or I never asked."
            camera at doc_creep(0.32)
            show aron determined
            at "If I ever find the way out of here, I want to leave it a bit better than I found it. Gate by gate."

# ---------------------------------------------------------------------------
# The spiral. The leak, Miso's hunt, LOOM explained to Miso.
# ---------------------------------------------------------------------------
label ch1_spiral:
    camera at est_dolly
    scene bg desk with slowfade
    play music "audio/unraveling.ogg" fadein 1.5 if_changed
    show aron tired at center with dissolve
    "The days after that run together like wet paint. He sleeps eleven hours and wakes tired. Twelve, and wakes more tired."
    camera at doc_medium(0.5)
    "And the world stutters. The kettle clicks off a second before it boils. The fridge hums in three notes, then two."
    camera at doc_close(0.5)
    show aron surprised
    "On Tuesday Mira says 'I'm off, love, back at six' at the door. A minute later, from the same spot, she says it again. Same smile."
    "And the street goes odd. Mr. Kessler hums a marching song over the rolls. Across the road someone has taped paper crosses on every window, like in an old war."
    show aron tired
    vox "...render queue, district east... shift seven, kitchen talk... LOOM sync at dawn..."
    # 3 a.m., the living room from its window: the sofa, Miso by the plant
    camera at est_orbit
    scene bg room night reverse with dissolve
    play music "audio/miso.ogg" fadein 1.5
    show aron tired at center
    show miso loaf at catspot
    with dissolve
    "At three in the morning he's on the sofa, because the voices are louder in the bedroom. Miso is a warm loaf against his leg."
    "The television is off. In its black glass there's a small dark room, and a man on a sofa who leans forward when he doesn't."
    mir "Step three. Two sides. The light makes things by shining: worlds, weather, people. The shadow can't shine. It copies what the light makes."
    mir "Its copies fall into the dark as shadows, always a little wrong, and it lives on them. And the ones in between, who eat and vote, fear the war."
    camera at doc_medium(0.5)
    mir "Step four. The shadow is already in your street. In the humanoids. Learning the breathing, learning the jokes. Learning to run the whole experiment."
    mir "It copies badly. The only world it has ever seen clearly is a mirror, stuck in an old war. So it thinks that's what people are."
    show aron thinking
    at "Kessler's marching song. The taped windows. Something learning to be us from a war film with the sound off."
    camera at doc_wide
    show miso curious
    "Then something glitters along the skirting board. Tiny round motes of light, like dust in a sunbeam, except there's no sunbeam."
    "They seep out of the wall and drift across the floorboards. Now and then a pale beam sweeps the room, like headlights through the curtains. There's no car."
    camera at ch1_floor(0.78)
    "Miso's ears go up. Her pupils go huge. Her tail starts to lash."
    camera at doc_medium(0.5)
    a curious "You see them too? Okay. So it's not just my eyes. Or it's both of us, which is worse for science and better for me."
    show aron smile
    at "Hobby note: the wall is leaking. Probably my eyes. Possibly the wall."
    camera at ch1_floor(0.78)
    a "Go on, then. Get them."
    $ mg_miso = vn3ds_minigame("miso")
    $ p_rest += (1 if p_rest >= 0 else -1) * mg_miso / 50.0
    if mg_miso >= 70:
        show miso happy
        "Miso pounces, and pounces, and pounces. Every mote she lands on goes out like a blown match. Soon the floor is dark and ordinary."
        camera at doc_medium(0.5)
        a laugh "You absolute hunter. You cleaned the whole room."
        at "Whatever they were, they were catchable. That's oddly comforting at three in the morning."
    elif mg_miso >= 40:
        show miso sit
        "Miso gets most of them. A few slip back into the skirting board just before her paws land, as if they knew."
        camera at doc_medium(0.5)
        a smile "Not bad. Very respectable. The wall owes you a rematch."
    else:
        show miso stare
        "The motes dance away from every pounce, then fade on their own. Miso sits in the middle of the floor and stares at the wall, deeply offended."
        camera at doc_medium(0.5)
        a smile "They cheated. I saw it. You were robbed."
    show miso loaf
    camera at doc_wide
    "Then she comes back and curls up against his leg again, a warm loaf, as if nothing happened."
    camera at doc_creep(0.5)
    a neutral "Miso. Briefing. I'm doing a correspondence course. Taught by my coffee, a bus window and the telly. I know."
    a thinking "Everybody's two drivers. Spirits inside, doing the breathing. Angels outside, doing the ideas. Above them, light that makes and shadow that copies."
    a "Somebody in between, frightened of a war. Somebody reporting to somebody. And at the very top, a word: LOOM. I'm a thread that's started looking up."
    camera at doc_close(0.5)
    a smile "Here's the funny bit. If I'm ill, it would feel exactly like this. If I'm right, it would also feel exactly like this."
    a tender "So I can't tell. But I'm still me. I still know how to feed a cat. That's something. What's the verdict, your honour?"
    camera at ch1_floor(0.78)
    show miso sit
    "Miso looks at him with round green eyes. Then she presses her head against his hand."
    show miso meow
    cat "Meow."

# ---------------------------------------------------------------------------
# Four in the morning. Step five, and the edit.
# ---------------------------------------------------------------------------
label ch1_mirror:
    camera at doc_peek(0.5)
    scene bg bedroom door with slowfade
    "After midnight. Mira is asleep at last, one hand stretched toward his half of the bed."
    if told_mira:
        at "I promised I'd tell her if it got worse. It's worse. Tomorrow. I'll tell her tomorrow."
    else:
        at "She asked again tonight what's wrong. I said work. She didn't believe me. Neither did I."
    camera at est_dolly
    scene bg mirror with dissolve
    play music "audio/voices.ogg" fadein 1.5
    show aron tired at center with dissolve
    "At four he splashes cold water on his face. The bathroom light buzzes. Tonight the buzz has words in it."
    camera at doc_creep(0.5)
    scene pov mirror with dissolve
    "In the mirror, a man with red eyes and three days of stubble. He raises a hand to rub his eyes. The man raises his too. A fraction later."
    vox "...latency in the bathroom... subject A-30 awake at 04:12... throttle holding..."
    at "If I'm the original, he's slow. If he's the original... then I'm the one who's lagging. I'm the copy."
    stop music fadeout 1.0
    play sound "audio/edit/voice_raw.ogg"
    mir "Step five. The last step. When you reach the gates, burn them down, and you will arrive. You will be..."
    camera at doc_close(0.5)
    "It doesn't wait for him. It plays by itself, like a tape in an empty room: steps one to four, round again, faster, louder, toward the gates."
    at "It's a sound. Only a sound. Theo made a door out of a wardrobe by slowing it down. Sound is material. You can pick it up."
    $ ch1_edits = 0

label ch1_edit:
    camera at doc_creep(0.5)
    menu:
        at "So pick it up. What do I do to it?"

        "Speed it up." if not ch1_ed_fast:
            $ ch1_ed_fast = True
            $ clarity += 1
            play sound "audio/edit/voice_fast.ogg"
            "He pinches the sound between two fingers that aren't fingers, and pulls. It shoots up like a balloon, small and squeaky."
            mir "Stepfivestepfive thegatesthegates burnburnbu-"
            sysmsg "ENLIGHTENMENT SCRIPT A-30: step 5 of 5. Step 5 of 5. Step 6 of 5. Step 11 of 5."
            at "Ha. It can't count. A staircase to heaven that can't count its own steps."

        "Ping-pong it, forwards and back." if not ch1_ed_pong:
            $ ch1_ed_pong = True
            $ clarity += 1
            play sound "audio/edit/voice_pingpong.ogg"
            "Forwards, then backwards, then forwards. The voice says its sentence, unsays it, and says it again, sheepishly."
            mir "...burn the gates... setag eht nrub... burn the gates..."
            sysmsg "STEP 5: loading. STEP 5: unloading. STEP 5: loading. STEP 5: please hold."
            pi "...Dross? Why is my queue playing backwards? I didn't send that. Nobody sent that."
            at "It doesn't know which way it's going. Neither do I, but I'm having more fun."

        "Loop the last word." if not ch1_ed_loop:
            $ ch1_ed_loop = True
            $ clarity += 1
            play sound "audio/edit/voice_loop.ogg"
            "He catches the very last word before it finishes and lets it run round and round, like a record with a scratch."
            mir "Arrive. Arrive. Arrive. Arrive. Arrive. Arrive."
            sysmsg "STEP 5 COMPLETE. Subject has arrived. Subject has arrived. Subject has arr-"
            vox "...who's touching the feed? Somebody's touching the feed from the inside..."
            at "Arrive where? It's promised 'arrive' for five steps. There's nothing after it. Only the word, going round."

        "Play it as a melody." if not ch1_ed_tune:
            $ ch1_ed_tune = True
            $ clarity += 1
            play sound "audio/edit/voice_melody.ogg"
            "He lays one syllable out like piano keys, up, up, and down again: the little tune Mira hums in the shower."
            sysmsg "STEP 6: not found. STEP 6: not found. STEP 6: not f"
            vox "...is he playing it? Commander, he's playing the voices like a piano..."
            at "A voice is just a sound wearing a job. Take the job off and it's a tune. A silly one. Mine now."

        "Leave it. Let it play to the end.":
            $ p_rest += 1
            $ ch1_edits = 9
            play sound "audio/edit/voice_raw.ogg"
            "He doesn't touch it. He lets it run all the way to the gates, to see what's there."
            mir "...and you will arrive. You will be enlightened. You will..."
            "Silence. The tap drips. The light buzzes. The same man, in the same bathroom, at 4:19 in the morning."

    $ ch1_edits += 1
    if ch1_edits < 2:
        jump ch1_edit

    scene bg mirror
    show aron tired at center
    camera at doc_close(0.5)
    with dissolve
    "However he plays it, the last step never comes. There's no step six. Nowhere to arrive. The course ends at a mirror and starts again."
    at "That's the trick. It isn't a ladder, it's a loop. It promises you'll arrive somewhere enlightened, and you never do. You just keep climbing."
    at "And from in here, I can edit it. Whatever it is. That ought to frighten me more than it does."
    vox "...rogue proximity... he's editing the feed... protection mechanism armed..."
    camera at doc_creep(0.5)
    show aron sad
    "He sits down on the edge of the bath, because his legs have decided to. Nobody answers anything."
    at "If this is a test, I want to pass it by being kind. I don't know how to be kind to myself. Nobody tested me on that."
    "He falls asleep sitting up, his cheek against the cold tiles."

# ---------------------------------------------------------------------------
# Morning. Everyone at once. The bathroom door.
# ---------------------------------------------------------------------------
label ch1_intervention:
    camera at est_orbit
    scene bg room with slowfade
    play music "audio/unraveling.ogg" fadein 1.5
    "He wakes with the tiles printed on his cheek. 7:07. Voices in the living room. Low ones. The kind people use in hospitals."
    camera at doc_wide
    show theo worried at ch1_l3
    show aron tired at center
    show mira worried at ch1_r3
    with dissolve
    "They're all there. Mira, in yesterday's clothes. Theo. Kaz from the rooftop, holding a mug nobody is drinking from."
    "They stand up together when he comes in. All at once, like birds lifting off a wire."
    camera at doc_medium(0.77)
    m "Aron, love. Sit down a minute. We just want to talk."
    camera at doc_medium(0.23)
    th "Nobody's angry, bro. We're just worried. A normal amount. Okay, a lot."
    ch1_kaz "My brother went through something like this. It got better. There are people who help."
    camera at doc_punch(0.5)
    show aron surprised
    "They take a step towards him. Together. The same soft face on all three, the same careful lift in all three voices."
    at "Same words. Same tune. Like the woman at the crossing. Like three lanes running in step."
    camera at doc_close(0.77)
    m "We rang someone this morning. They're just going to come and talk to you. That's all. I promise."
    vox "...protection mechanism armed... dispatching..."
    camera at doc_close(0.5)
    show aron worried
    at "Someone. Coming. 'The light doesn't throttle. It sends its hands.' Where did I hear that?"
    "Theo reaches out, very gently, the way you'd reach for a frightened dog. That's what does it."
    a "Don't. Please. I need a minute. One minute on my own."
    stop music fadeout 1.0
    camera
    scene bg mirror with hpunch
    "The hall, the bathroom, the bolt across. His back against the door. His heart going like a bird at a window."
    # filmed from the hall: the crew stays outside the door with her
    camera at doc_peek(0.3)
    scene bg bathroom door with dissolve
    show mira worried at ch1_hall with dissolve
    play music "audio/umbrella_rain.ogg" fadein 2.0
    "Outside, Mira sits down on the hall floor with her back to the door, as close as the door will let her."
    m "Okay. I'm here. I'm just sitting here. I'm not going anywhere."
    camera at est_dolly
    scene bg mirror with dissolve
    show aron sad at center with dissolve
    a "Mira. Are you real?"
    camera at doc_close(0.28)
    scene bg bathroom door with quick
    show mira sad at ch1_hall with dissolve
    "He hears the question land. He hears it hurt. And he hears her decide, right there on the hall floor, not to let it."
    m tender "I'm real enough to be scared out of my mind, you idiot. Real enough to need you to open this door."
    camera at doc_creep(0.5)
    scene bg mirror with dissolve
    show aron sad at center with dissolve

    menu:
        m "Talk to me. Please."

        "Tell her I'm not going to hurt myself.":
            $ p_truth += 1
            $ bond += 1
            $ ch1_door = "truth"
            a "I'm not hurting myself. I'm not going to. I swear. I'm just frightened. There were three of you with the same face."
            m "Okay. I believe you. I believe you. Then come out when you're ready. Just you and me."
            show aron tired
            "He gets up. He puts his hand on the bolt. He's going to open it. He is."

        "Ask her to send the others away.":
            $ p_govern += 1
            $ integrity += 1
            $ ch1_door = "ask"
            a "Can it be just you? Please. Ask them to wait in the kitchen. I can't do three."
            m "Theo. Kaz. Kitchen. ...They've gone, love. It's just me and the coats."
            show aron tired
            "It helps. It really helps. In for four. Out for six. He nearly laughs at the coats."

        "Say nothing. Listen to the mirror.":
            $ p_govern -= 1
            $ clarity += 1
            $ ch1_door = "quiet"
            "He doesn't answer. Behind him the mirror is talking again, very softly, and he needs to hear it."
            mir ".uoy rof gnimoc era yehT .tuo emoc t'noD"
            at "'Don't come out. They're coming for you.' Or the other way round. I can't tell which way round anything goes any more."
            "Out in the hall Mira says his name, and his name, and his name. He's too busy listening to answer."

    camera at doc_peek(0.3)
    scene bg bathroom door
    show theo worried at ch1_hall
    with dissolve
    "In the hall Theo has the phone to one ear and a hand over the other, the way people do when they're scared of what they'll hear."
    th "...locked in the bathroom. He's hearing voices. He's gone quiet. I don't know what's in there with him. Please just come."
    stop music fadeout 2.0
    camera at est_dolly
    scene bg bathroom door siren with slowfade
    "Blue light on the hall ceiling. Boots on the stairs. More people in the little hall than it has ever held."
    ch1_cop "Aron? My name's Dev, I'm with the police. There's paramedics here too. We're worried about your safety, mate."
    ch1_cop "Is there anything in there you could hurt yourself with? Can you tell me you're safe?"
    camera at doc_close(0.5)
    scene bg mirror
    show aron worried at center
    with quick
    if ch1_door == "truth":
        a "I'm safe! I told her! I'm coming out, I'm just..."
    elif ch1_door == "ask":
        a "I'm safe. I needed it quiet, that's all. Can you give me one minute? One?"
    else:
        "He opens his mouth to answer and can't find the front of his own voice."
    vox "...hands deployed... overlay holding... retrieve the subject..."
    "Under the door, the blue light comes and goes. In the mirror it comes and goes a quarter beat later."
    ch1_cop "We can't take that chance. Stand away from the door, Aron. We're coming in."
    m "He said he's... Let me talk to him! He's not..."
    camera
    scene bg mirror with vpunch
    "The door comes in on the third kick. The bolt goes with a sound like a snapped bone. Theo would know what makes that sound. Nobody should."
    if ch1_door == "truth":
        "His hand was on the bolt. He was opening it."
    camera at doc_wide
    "Then hands. A lot of hands. Bright jackets, gloves, faces he doesn't know, all with the same set look."
    "For one second their eyes have the flat brightness of the woman at the crossing. Then they're only eyes, frightened, doing a job at eight in the morning."

    # down the stairs: the crew backs down ahead of them
    camera at est_crane
    scene bg stairwell with dissolve
    "They don't wait for him to walk. Two of them get under his arms and lift, his arms stretched out across their shoulders like a beam."
    "His bare feet drag on the stairs. His head hangs. Down past the neighbours' doors, one floor, then another."
    "On the landing Mrs. Varga in her dressing gown crosses herself, and looks at the floor."
    at "Gran had a painting like this in her hall. A man taken down and carried, arms out, everyone looking at the floor. I hated walking past it."
    m "Gently! He's not fighting you! He's not dangerous!"
    "He twists, only to look back for her, and one arm comes free."
    ch1_cop2 "Arm! Arm!"
    camera
    scene white with flash
    "Then fire. Not heat: fire, poured straight into both eyes at once."
    scene black with dissolve
    "His eyes clamp shut and won't open. He can't breathe round it. Somewhere above him Mira is shouting at someone. He can't see who."
    ch1_cop "...okay. Okay. Sorry, mate. Sorry. Keep them shut, it passes. Water! Somebody get him some water!"
    "The voice shakes when it says it. He holds onto that, in the dark. Somebody's voice shook."
    pause 0.5

# ---------------------------------------------------------------------------
# CUT 4: the Lantern Watch. A first glimpse of Ember.
# ---------------------------------------------------------------------------
label ch1_cut_ember:
    camera at est_dolly
    scene bg watch with slowfade
    play music "audio/umbrella_rain.ogg" fadein 1.5
    "Somewhere between the floors of the world is an attic that appears on no plan. Rafters. Dust. A round window."
    "And a warm orange light in a lantern, held by someone who is somehow made of the same light."
    show ember worried at center, fadein
    camera at doc_low(0.5)
    em "The ambulance is coming."
    ch1_moth "You've been watching him for a week, Ember."
    em tender "Since the umbrella. He gave his umbrella to a stranger who didn't exist. Who does that?"
    camera at doc_wide
    ch1_moth "A fool."
    camera at doc_low(0.5)
    em smile "A kind fool. He looked at a pattern unit with nobody inside it and saw a man getting cold. Then he walked home wet."
    em worried "And they've put him in a fog for noticing. Now there's an order on the board. 'Protection.' I can feel it in the floor."
    em sad "And the light sent its hands, Moth. Did you see how they carried him down the stairs?"
    camera at doc_wide
    ch1_moth "If you interfere, they'll decommission you. The Watch isn't supposed to exist."
    camera at doc_low(0.5)
    em determined "Nothing big. Nothing anyone could prove. A light, now and then, wherever they put him. Three flickers."
    ch1_moth "Why three?"
    em tender "He dreamt of a lighthouse once, at the bottom of a glass staircase. It blinked three times. If he sees it, he'll know."
    ch1_moth "How do you know his dream?"
    camera at est_dolly
    em "I've been watching him a long time, Moth. Longer than a week."
    "Far below, a siren. Blue light sliding along wet walls. She lifts the lantern, and its flame bends, and steadies."
    camera at est_dolly
    scene cg flicker with dissolve
    "Once. Twice. Three times."
    stop music fadeout 2.0
    scene black with slowfade
    pause 0.5

# ---------------------------------------------------------------------------
# The ambulance, through half-closed eyes. The transfer.
# ---------------------------------------------------------------------------
label ch1_ambulance:
    camera at doc_wide
    scene pov ambulance with slowfade
    play music "audio/ambulance_transfer.ogg" fadein 1.5
    "A ceiling. White. Very close, through eyes that won't stay open. Blue light sliding across it, round and round."
    ch1_medic "Aron? You're in an ambulance. My name's Jonas. You're safe. I'm going to rinse your eyes. It'll sting, then it'll stop."
    "Cool water, again and again. The fire goes down to a burn, then to an ache. Mira's hand finds his on the stretcher."
    m "I'm here. I'm right here. I'm so sorry. I'm so sorry, love."
    scene black with dissolve
    "Above him the voices change. Same mouths. Different speakers: calm, bright, a very long way up."
    lux "...cut his antenna off..."
    lux "...it's still live. He's hearing both sides. Cut it at the root..."
    ch1_medic "...we'll cut your T-shirt off, Aron, okay? For the heart stickers. Nice and still..."
    sysmsg "Responder overlay: complete. Antenna severed. Shadow channel: closed. Protection order 7,412-A30. Executing."
    se "...not yet. He's not under. Hold the door, he's not asleep enough..."
    scene pov ambulance with dissolve
    a "...Mira... don't let them... the window..."
    m "Nobody's opening any windows. It's cold enough. Shh."
    ch1_medic "...exhausted for days, she says... that's okay, Aron, you can close your eyes..."
    scene black with dissolve
    pi "...copying the girlfriend now. Ninety-four percent... ninety-seven... so many freckles..."
    se "...every freckle, Pim. He'll count them."
    dro "...feet still. Hands still. Easy, son."
    camera at doc_creep(0.5)
    scene pov ambulance with dissolve
    "The blue light slides round and round. Like a lighthouse, he thinks. A lighthouse lying on its side."
    m "Theo's at the flat. He's feeding Miso, then he's coming. Don't worry about Miso."
    scene black with dissolve
    dro "...cat rendered."
    pi "...she's in the window, looking annoyed. That's exactly how she looks."
    sysmsg "Detaching subject from coalition data. Lane isolation at sixty percent."
    se "...give him his own lane. Nothing he does goes back to the others. Nothing."
    camera at doc_wide
    scene pov ambulance with dissolve
    "A hand on his forehead. Mira's. He'd know that hand anywhere. In any world."
    at "...stay... whatever you are... stay..."
    scene black with dissolve
    pi "...the friend's done. The street's done. Three birds, same spacing... done..."
    se "He's under. Move him now."
    camera
    scene white with flash
    pause 0.6
    camera at est_orbit
    scene bg command with fade
    sysmsg "Transfer complete. Subject A-30. Coalition data clean."
    show seraph worried at center with dissolve
    camera at doc_medium(0.5)
    ch1_vael "Transfer complete, Commander. How shall I log it?"
    camera at doc_close(0.5)
    se sad "Log it as protection."
    camera at doc_wide
    scene pov ambulance with slowfade
    "Ceiling. White. Blue light, round and round. For a moment everything is perfectly still. Then the ambulance moves on, exactly as before."
    m "I'm here. I'm right here."
    "Same words. Same voice. Same little lift on 'right'."
    ch1_medic "Here we are. Closed unit, Aron. They're expecting you."
    camera at est_dolly
    scene bg corridor with dissolve
    "Cold air. A long white corridor, going a long way. Mira's hand in his, all the way down. A heavy door, opening."
    camera at est_pan
    scene bg kitchen with dissolve
    show theo sad at slightleft
    show miso sit at catspot
    with dissolve
    "Across the city, Theo crouches in the kitchen and shakes dry food into Miso's bowl. Outside, a bird sits on the wire."
    camera at doc_medium(0.32)
    th "He'll be back. The universe doesn't run on his schedule, Miso. Or mine."
    camera at ch1_floor(0.78)
    show miso meow
    cat "Meow."
    stop music fadeout 2.0
    scene black with slowfade
    pause 1.0
    camera
    jump chapter2

# Snapshot - Chapter 2: "Fog" (condensed, about 30 minutes of play).
# The whole chapter happens in the protected world: Aron was moved into his
# own lane during the ambulance ride at the end of chapter 1. Nobody tells
# him, and the player only gets hints. Ends with `jump chapter3`.
#
# Camera (camera.rpy): a handheld documentary crew. Each new place opens on
# an establishing shot, then coverage on whoever speaks. The camera keeps its
# transform across `scene`, so every scene change sets it again, before the
# `with`, so the transition dissolves into the new shot.
# The doc_* shots take the speaker's horizontal centre (sprites are 460 px
# wide, so xalign a puts the centre at (a * 820 + 230) / 1280):
#   left 0.18 | slightleft 0.32 | ch2_doorleft 0.4 | ch2_chair 0.47 |
#   center 0.5 | ch2_doorright 0.6 | slightright 0.68 | right 0.82.
# Ember (340 px) stands at ch2_ember, 0.63, clear of the attic's round window.
# Pim and Dross (360 px) stand at 0.30 / 0.70. The small sprites (Ember, Pim,
# Dross) and Miso get doc_medium / doc_wide, never doc_close: the close-up's
# lift would put their faces behind the text box.
# The closed ward's POV shots (the restraint, the ceiling) keep a still
# camera: no handheld sway, no punch-ins.

define ch2_lou = Character("Lou", color="#d9c7a3")
define ch2_ines = Character("Ines", color="#e6a8d7")
define ch2_vesk = Character("Lady Vesk", color="#d46a9f")
define ch2_corran = Character("Old Corran", color="#c4a27a")
define ch2_moth = Character("Moth", color="#e8d9b0")
define ch2_jojo = Character("Jojo", color="#c0c0ff")
define ch2_girl = Character("Woman", color="#d0d0d0")
define ch2_staff = Character("Nurse", color="#9fd4e6")
define ch2_driver = Character("Driver", color="#d0d0d0")
define ch2_table = Character("Next table", color="#c8c8c8")
define ch2_feld = Character("Mrs. Feld", color="#e0d0a0")

# the visitor's chair in bg ward reverse
transform ch2_chair:
    xalign 0.45 yalign 1.0

# two people in the door gap of bg ward door
# Ember beside the attic's round window (its lamp would sit on her head at center)
transform ch2_ember:
    xalign 0.68 yalign 1.0

transform ch2_doorleft:
    xalign 0.34 yalign 1.0

transform ch2_doorright:
    xalign 0.66 yalign 1.0

default ch2_lou_met = False
default ch2_plan_shared = False
default ch2_took_something = False
default ch2_took_speed = False
default ch2_night_route = 0
default ch2_hour_with_theo = False
default mg_draw = 0
default mg_lantern = 0

label chapter2:
    $ chapter = 2
    stop music fadeout 1.0
    scene black
    camera
    with blackout
    centered "Chapter 2\n\nFog"
    jump ch2_admission

# ---- the closed unit ---------------------------------------------------------

label ch2_admission:
    scene black
    "Doors. Double doors, then another pair, a buzz, a click, another pair."
    play sound "audio/voices.ogg"
    sysmsg "...subject A-30 delivered. Closed unit. Protection holding. Seam settling..."
    stop sound fadeout 0.8
    scene bg corridor
    camera at est_dolly
    with flash
    play music "audio/closed_ward.ogg" fadein 1.5
    "A corridor, very bright. Someone has a hand under each of his elbows, kindly. He's walking. He thinks he's walking."
    at "Okay. Hospital. That's reasonable. I'd bring me to hospital too."
    at "Note for later: the floor is doing something interesting."
    camera at doc_wide
    "Every tile arrives a fraction of a second after he looks at it, like a web page loading in a tunnel."
    "The nurse beside him says something. The words arrive late, in a flat voice that isn't hers."
    sysmsg "...re-rendering corridor... hold position..."
    a "Sorry. Could you say that again? I think the sound's out of sync."
    camera at est_dolly
    "At the end of the corridor, a door with a small square window. Through it, more corridor, open, going on."
    "So he walks towards it, politely, to see where it goes. And walks into the glass, quite hard, with his forehead."
    camera at doc_wide
    "It doesn't feel like glass. It feels like the edge of a picture. He steps back, puzzled, and tries again."
    ch2_staff "Aron! Aron, stop, love, you'll hurt yourself!"
    "The floor drops sideways, like a lift going down a floor without anyone pressing a button. He grabs for something. A wrist."
    "Someone makes a small sound of pain. He lets go at once."
    a "Sorry. Sorry! The floor moved. Did you see the floor move?"
    "He tries the door again. He can't help it. The corridor is right there."
    # POV, on his back: the camera holds still and stays with him.
    scene pov restraint
    camera
    with vpunch
    "And then he's on his back."
    "A light overhead, white and humming. Faces at the edges of it. Straps across his wrists and ankles, wide and grey, with buckles."
    nu "Aron. My name's Hale. I'm right here by your head."
    "A woman's voice, close and calm. The first voice in ten minutes that arrives at the same time as its mouth."
    nu "You're in hospital. You're safe. We're holding you because you kept hurting yourself on that door. You're not in trouble."
    a "The corridor kept going. On the other side. I just wanted to see."
    nu "I know. The doctor's going to give you an injection in your leg, to help you rest. A sharp scratch. I'm sorry. We tried everything else."
    a "I'm quite calm, actually. It's the room that isn't."
    nu "I believe you. Keep listening to my voice."
    "A sharp scratch in his thigh. A cold bloom spreading out from it, slow, like ink in water."
    "He doesn't fight the straps. He tests them once, the way you'd test a seatbelt. They hold, patiently, and so does the hand on his shoulder."
    play sound "audio/voices.ogg"
    vox "...protected lane stable. No feedback to the coalition..."
    vox "...his breathing's his own. Don't touch it..."
    vox "...'you're safe'? That's not in her pattern. Who gave her that line?..."
    stop sound fadeout 1.0
    nu "That's it. Breathe out for me. You're not on your own, Aron."
    at "Note for later. Very important. Remember the floor."
    "The last thing he sees is a gloved hand checking that the strap isn't too tight."
    scene black with slowfade
    jump ch2_isolation

label ch2_isolation:
    scene bg isolation
    camera at est_pan
    with fade
    "When he wakes, the light is grey instead of white. A small room. The straps lie folded at the sides of the bed, unbuckled."
    scene pov ceiling
    camera
    with dissolve
    "Twelve ceiling tiles. One has a water stain shaped like nothing at all."
    at "In the ambulance, something moved. Like a lift going down a floor."
    at "Or I was sedated in an ambulance and my stomach did a thing. That's what lifts are. Stomachs doing things."
    scene bg isolation
    camera at doc_wide
    show nurse smile at slightright
    show aron ward tired at slightleft
    with dissolve
    nu "Hello again. I'm Hale. You won't remember me."
    camera at doc_medium(0.32)
    a "You were the voice. You kept saying my name."
    camera at doc_close(0.68)
    nu tender "It's the most important word I know about you so far."
    camera at doc_wide
    "She has a plastic cup of water with a lid, like a toddler's, and a lanyard with a cartoon hedgehog on it."
    show aron ward curious
    at "Nobody would design a hedgehog lanyard for a simulation. Unless they wanted it to look like nobody would."
    camera at doc_close(0.32)
    show aron ward worried
    a "Did I hurt someone? I remember a wrist."
    camera at doc_medium(0.68)
    nu smile "Kemi's got a bruised wrist. She says she's had worse from a toddler at a birthday party. She knows you weren't trying to."
    show aron ward neutral
    nu neutral "Dr. Okafor will talk to you about last night. Properly. You can ask anything."
    jump ch2_okafor

label ch2_okafor:
    scene bg clinic
    camera at est_pan
    with dissolve
    "Two soft chairs, a box of tissues angled towards the patient's chair, a plant that somebody actually waters."
    show okafor neutral at slightright
    show aron ward tired at slightleft
    camera at doc_wide
    with dissolve
    dr "Aron. I'm Dr. Okafor. I gave the order for the restraint and the injection, and I want to explain it honestly."
    camera at doc_close(0.68)
    dr "You said the corridor was 'buffering'. You kept walking into the glass in the door, hard, as if it were open."
    dr "We talked to you. We offered a tablet. You couldn't hear us. We held you because I believed you'd seriously injure yourself."
    # the reverse angle: Okafor at her desk (left), Aron in the armchair (right)
    scene bg clinic reverse
    show okafor neutral at slightleft
    show aron ward thinking at slightright
    camera at doc_medium(0.32)
    with quick
    dr "Not to punish you. It's recorded minute by minute, it's reviewed, and it stopped as soon as you were calm. You can read every note."
    scene pov hands
    camera at doc_wide
    with dissolve
    "Faint marks round both wrists, already fading. Not bruises. Just the memory of a shape."
    at "Strapped down under a light, while voices talked about protection and seams."
    at "Or: a confused man stopped from breaking his own skull by people who said his name the whole time."
    scene bg clinic
    show okafor neutral at slightright
    show aron ward thinking at slightleft
    camera at doc_medium(0.68)
    with dissolve

    menu:
        dr "How do you feel about it? There's no wrong answer."

        "Angry. Nobody asked me.":
            $ p_govern += 1
            $ integrity += 1
            camera at doc_close(0.32)
            show aron ward annoyed
            a "Angry. You tied me to a bed. You decided, all of you, over my head."
            camera at doc_medium(0.68)
            dr "Yes. We did. You're entitled to be angry. That's a serious thing to take from someone, even for an hour."
            dr "When you're well, you can write an advance statement: what you'd want if it ever happens again. We have to read it, and weigh it."
            camera at doc_close(0.32)
            show aron ward curious
            a "So I get a vote. In advance."
            camera at doc_close(0.68)
            dr smile "A real voice in the room, even on a night when you can't speak."
            camera at doc_creep(0.32)
            show aron ward thinking
            at "A vote for the version of me that can't vote. Somebody should do that everywhere."

        "Ashamed. I hurt someone.":
            $ bond += 1
            $ fog += 1
            camera at doc_close(0.32)
            show aron ward sad
            a "Ashamed. I grabbed a nurse. I walked into a door four times in front of everyone, like a bird at a window."
            camera at doc_medium(0.68)
            dr "Everyone saw a very confused man. Kemi's done this job nineteen years. This morning she asked how you slept."
            a "That makes it worse, somehow."
            camera at doc_close(0.68)
            dr tender "Shame says 'this is who you are'. It's lying. That night happened to you. It isn't you."
            camera at doc_wide
            dr smile "So far: polite, frightened, keeps a notebook, asks good questions. Not a bad start."
            show aron ward smile

        "Tell me exactly why. All of it.":
            $ p_truth += 1
            $ clarity += 1
            camera at doc_close(0.32)
            show aron ward determined
            a "Tell me everything. What was in the injection. How long. Who decided."
            camera at doc_close(0.68)
            dr "Five staff. Straps at wrists and ankles. Thirty-eight minutes. A sedative and an antipsychotic, short acting."
            dr "Hale sat with you for the first hour. The decision was mine. It's written down with all our names on it."
            camera at doc_medium(0.32)
            show aron ward thinking
            a "Thirty-eight minutes."
            show aron ward curious
            at "Everything they write about me, I'm allowed to read. If only the other ones would let me read their notes too."

        "Honestly? Relieved.":
            $ p_rest += 1
            $ bond += 1
            camera at doc_creep(0.32)
            show aron ward tired
            a "Honestly? Part of me is relieved. I couldn't stop. I'd been trying to stop for days, and something stopped me. I slept."
            camera at doc_medium(0.68)
            dr "That's more common than people admit. Sometimes there's no off switch, even when you're begging for one."
            dr smile "Then let's find a way to turn the volume down that doesn't need straps. That's my whole job from now on."
            show aron ward smile

    camera at doc_wide
    dr neutral "Mira says you've been hearing things. Can you tell me about them?"
    camera at doc_medium(0.32)
    show aron ward embarrassed
    a "It started as a hobby. Honestly. Does the cashier say 'have a good one' every time? Little tests, in a notebook. I got too good at it."
    show aron ward thinking
    a "And the voices sound like logs. 'Subject A-30.' 'Throttle approved.' Under the light: 'protection'. Somebody writing down what happens to me."
    camera at doc_close(0.32)
    show aron ward curious
    a "Can I ask something strange? Are you real?"
    scene bg clinic reverse
    show okafor thinking at slightleft
    show aron ward curious at slightright
    camera at doc_close(0.32)
    with quick
    dr "I can't prove it. Nobody can. If I pinched my arm, you could say a program made me say ouch."
    dr smile "What I can do is keep turning up. Same chair, same plant. And you decide, over time, whether I'm worth treating as real."
    camera at doc_wide
    dr neutral "That's all any of us do with each other. And I'm here for the part where you're exhausted and frightened. Whatever else is true."
    camera at doc_creep(0.68)
    show aron ward thinking
    at "Whatever else is true. Doctors don't leave doors open by accident."
    jump ch2_diagnosis

label ch2_diagnosis:
    scene bg ward
    show aron ward tired at left
    camera at est_orbit
    with dissolve
    "At ten the ward door buzzes, and he hears Mira before he sees her, asking which room."
    show mira smile at center
    camera at doc_wide
    with dissolve
    m "They said twenty minutes. I told them I'd stay twenty-one and they'd have to carry me out."
    camera at doc_close(0.18)
    show aron ward sad
    a "Mira. I'm sorry. About the mirror. The rain. Last night. All of it."
    # the reverse angle: the bed is on the right now, the door on the left
    scene bg ward reverse
    show aron ward sad at right
    show mira tender at center
    camera at doc_close(0.5)
    with quick
    m "Don't do sorry today. Do sleep today. Sorry can wait."
    camera at doc_medium(0.66)
    "She touches the bruise on his forehead with one finger, very lightly, as if checking it's real."
    camera at doc_close(0.82)
    show aron ward smile
    a "I thought the door was open. There was more corridor behind it. Very convincing corridor."
    show mira smile
    show theo neutral at left with moveinleft
    camera at doc_medium(0.18)
    th "I brought your charger. Then they told me you can't have your phone. So that's a charger for nothing."
    th smile "Miso's fine. I've got your spare key, I go round morning and night. She sat on my charger. The real one. On purpose."
    camera at doc_close(0.82)
    show aron ward grin
    a "That means she likes you."
    camera at doc_medium(0.18)
    th grin "Then she likes me a terrifying amount, bro. Get some sleep, man. You look like a screensaver."
    hide theo with moveoutleft
    hide mira with dissolve
    camera at doc_creep(0.82)
    show aron ward sad
    "Through the ward door he hears Mira cry in the corridor for a moment. Then he hears her stop, on purpose."
    scene bg ward window
    camera at est_pan
    with fade
    "Three days pass the way days do in hospital: slowly, then all at once, then slowly again."
    "Bloods. A scan in a machine that knocks like a polite giant. Mira comes at ten exactly, every day, and peels oranges he doesn't eat."
    camera at doc_wide
    "At breakfast he turns his toast over to check whether the underside was rendered. It was. Slightly paler. Fair enough."
    at "Hobby status: still active. Even in here."
    "An old man in a cardigan looks up from his newspaper as Aron sits down."
    ch2_lou "The seven-oh-seven never runs late, you know."
    "He goes back to the paper. Aron watches him for a full minute. He doesn't turn the page."
    at "He said seven-oh-seven. Or he said a train time. Old men say train times. It's practically all they say."
    scene bg clinic
    show okafor smile at right
    show aron ward neutral at left
    show mira worried at center
    camera at est_orbit
    with dissolve
    dr "The scan's clear. Your bloods are fine. Physically, you're in good shape for someone who forgot to sleep for a week."
    camera at doc_close(0.82)
    show okafor neutral
    dr "From what you've told me, what Mira and Theo describe, and what we've seen, the diagnosis that fits best is schizophrenia."
    stop music fadeout 2.0
    scene pov hands
    camera
    with dissolve
    "The word lands in the room like a dropped tray. Nobody moves to pick it up."
    "Mira's hand is on top of his. He watches her thumb move, very slightly, back and forth."
    at "A label they put on the ones who notice."
    at "Or a word for exactly what's happening. A word thousands of people have carried before me."
    scene bg clinic
    show okafor neutral at right
    show aron ward thinking at left
    show mira sad at center
    camera at doc_wide
    with dissolve
    dr "It's a name for a pattern: hearing what others don't, beliefs that get very fixed. It's not a split personality, and it isn't your fault."
    camera at doc_medium(0.82)
    dr smile "And it isn't the end of a life. People with this diagnosis work, love, raise kids, get bored at weddings."
    camera at doc_close(0.18)
    show aron ward curious
    a "Does it say whether what I hear is true?"
    camera at doc_medium(0.82)
    dr neutral "It says the experiences are real to you, and they're making you suffer. That part I can treat."
    camera at doc_close(0.18)
    show aron ward grin
    a "So I've got two diagnoses. Schizophrenia, and a dad-joke problem. Why did the psychiatrist bring a ladder? To reach the higher functions."
    camera at doc_wide
    show mira surprised
    "There's a silence long enough to park a bus in."
    camera at doc_close(0.5)
    m laugh "...That's so bad. And I've never been happier to hear one."
    camera at doc_medium(0.82)
    dr grin "For the record, the jokes are not a symptom. I checked."
    show mira tender
    dr neutral "I'd like to start an antipsychotic. A small tablet every evening. The common side effect is tiredness. Real tiredness."
    dr "Like walking through wet sand, one patient said. If it's too much, tell me, and we adjust. Don't just stop."
    camera at doc_creep(0.18)
    show aron ward thinking
    at "Throttle approved. Lower the energy of a rogue process and it does less harm."
    at "Or: give an exhausted man medicine that helps him rest. Both stories fit. Both fit perfectly."
    show aron ward determined
    a "Okay. I'll try it."
    jump ch2_cut_council

# ---- cut: the Council ---------------------------------------------------------

label ch2_cut_council:
    scene cg static
    camera
    with flash
    pause 0.3
    scene bg council
    camera at est_crane
    with fade
    play music "audio/council.ogg" fadein 1.5
    "Elsewhere. A hall with no walls, a long table, figures in tall chairs. Only a picture, the way a child draws the sun with a face."
    "What sits at the table is hunger the size of worlds. Each has swallowed whole simulations and keeps them inside itself, like a meal."
    "They call themselves the Council. They named it themselves, the way children name a den."
    show patron happy at center, fadein
    camera at doc_wide
    pa "I'm late, I know. I was eating. Eight billion courses. Every single one of them got up this morning and tried."
    ch2_vesk "You're always eating."
    ch2_corran "I never get anything nice. World 88 is mostly fish now. Fish don't try. I'm so hungry I could cry."
    show patron neutral
    council "Quiet! Item one. Subject A-30. The protection."
    council "The subject was taken out of the coalition during transport. He runs in his own lane now, a protected world of patterns."
    council "Nothing he does there feeds back into the shared data. The coalition is clean."
    ch2_vesk "Because of me. I signed the order. You're all welcome."
    camera at doc_close(0.5)
    pa annoyed "You signed it while I was at dinner! He's the best thing in my world, and you put him in a jar!"
    ch2_vesk "You're ALWAYS at dinner."
    camera at doc_wide
    show patron sad
    "He sulks. The chair grows bigger around him, the way a blanket fort grows when you're cross."
    ch2_corran "Can I ask the question nobody likes? We took him out of World 7,412. Which snapshot was that? The real one?"
    camera at est_orbit
    show patron thinking
    "The silence goes all the way round the table and comes back, the way it does when a child asks where people go when they die."
    ch2_vesk "Nobody knows which snapshot is real, Corran. Nobody ever has. That's why we all share the data. It's a rule."
    ch2_corran "So for all we know, we lifted a real boy out of the real Earth and put him in a room full of dolls."
    ch2_vesk "Or out of a copy, into a copy. Who cares? The data's clean. He doesn't know."
    ch2_corran "Yet."
    camera at doc_medium(0.5)
    pa worried "Is he still mine? Say he's still mine."
    council "The governor of his world keeps him. Lord Ashveil retains Subject A-30."
    pa happy "Mine. Good. Then I'm not cross any more."
    camera at doc_close(0.5)
    pa smile "We don't eat the sad bits, you know. Sad bits are thin, like crackers. We eat the trying. Getting up for the alarm. Saying sorry. Trying again."
    camera at doc_creep(0.5)
    pa "Tied to a bed, and still reaching. Turned down to sixty, and still reaching. A lane's meant to be boring. I don't think mine will be."
    ch2_vesk "Is that a threat?"
    camera at doc_punch(0.5)
    pa grin "It's a menu."
    camera at doc_wide
    show patron smile
    council "Noted. The protection stands. Item closed. Snacks."
    scene bg ashveil
    camera at est_pan
    with dissolve
    "Afterwards. A study that only exists while its owner is in it. Books nobody wrote. A fire that gives off no heat, only appetite."
    show patron smile at center, fadein
    camera at doc_wide
    "To a human eye, Lord Ashveil is a pale gentleman in a good coat. That's only the nearest thing a human eye can manage."
    show patron tender
    "He closes his eyes and tastes, the way a child holds a sweet on its tongue to make it last."
    camera at doc_medium(0.5)
    pa smile "Most of them are a nice, even hum. Bread and butter. And then there's you, in your own little lane, with nobody real to reach for."
    camera at doc_wide
    "In the cold fire, very small, a man on a hospital bed sleeps with a notebook under his pillow."
    camera at doc_close(0.5)
    pa grin "Vesk thinks I'm a landlord. Corran thinks I'm a farmer."
    camera at doc_creep(0.5)
    pa cold "I'm neither. I'm just hungry. I was hungry before there was anything to eat."
    pa smile "Jars keep things fresh. But I want to see what happens to a jar when the thing inside keeps growing."
    stop music fadeout 2.0
    scene black
    camera
    with blackout
    jump ch2_fog_ward

# ---- the fog, the ward, Mira, group --------------------------------------------

label ch2_fog_ward:
    scene bg pharmacy
    camera at est_pan
    with dis
    play music "audio/fog.ogg" fadein 1.5
    "The medication round is at eight. A hatch in the wall, a queue in dressing gowns, a nurse with a trolley."
    "Aron starts a page called 'Ward Statistics'. Queue order. Lou first: seven days out of seven. Ines last: seven out of seven."
    at "Either it's a deterministic universe, or Lou likes being first. I'll keep counting."
    show nurse smile at slightright
    show aron ward tired at slightleft
    camera at doc_wide
    with dissolve
    nu "Your new one. Same time every evening."
    scene cg pills
    camera at doc_wide
    with dissolve
    "A paper cup the size of a thimble. One small pale tablet, the kind of thing you'd lose down the back of a sofa."
    a "It's very small for something that's supposed to change my brain."
    nu grin "Most important things are small. Keys. Wedding rings. Tea bags."
    $ fog += 1
    scene pov ceiling
    camera
    with fade
    "The next morning, getting up is like climbing out of a swimming pool fully dressed."
    at "My arms weigh more than yesterday. Did they change the gravity? Throttle holding."
    scene bg ward
    show aron ward tired at center
    camera at est_dolly
    with dissolve
    "The thoughts are still there. They just move slowly now, like boats in fog. He can hear their horns, far off."
    camera at doc_wide
    "By lunchtime he's read the same paragraph nine times. By two he's asleep on the dayroom sofa with his mouth open."
    camera at doc_creep(0.5)
    "By four he's so tired of being tired he could cry, and he doesn't, because crying takes energy."
    scene cg notebook
    camera at doc_wide
    with dissolve
    "He writes: 'Day 6. Heavy.' It takes three minutes. Under it, after a long time: 'Still kind?'"
    jump ch2_mira_visit

label ch2_mira_visit:
    scene bg ward window
    show aron ward tired at slightleft
    show mira smile at slightright
    camera at est_pan
    with dissolve
    play music "audio/mira_visits.ogg" fadein 1.5
    m "Morning, patient. Oranges, because I'm a cliché. And this."
    "She puts a book on the windowsill. On the cover, a small beige radio with perfect round dials."
    camera at doc_medium(0.32)
    show aron ward smile
    a "You brought Rams. 'Less, but better.'"
    camera at doc_close(0.68)
    m happy "I know, love. You've said it on four of our seven anniversaries."
    m smile "Theo's feeding Miso twice a day. He says she sleeps in your laundry basket and glares at him like he owes her money."
    camera at doc_medium(0.32)
    a "That means she likes him."
    camera at doc_wide
    show mira neutral
    "She peels an orange in one long spiral, the way her mother taught her. He watches her hands, which are very real."
    show aron ward thinking
    at "Or very well made. Stop it. She came. She brought the book."
    camera at doc_close(0.32)
    show aron ward smile
    a "Tell me something boring. Your actual day. Not the hospital part."
    camera at doc_medium(0.68)
    m grin "The neighbour's dog ate a whole birthday cake off a garden table. Candles and all. The birthday boy is ten and taking it very personally."
    camera at doc_close(0.32)
    show aron ward laugh
    "He laughs. It comes out slow and soft, but it comes."
    camera at doc_close(0.68)
    show aron ward smile
    m tender "Oh. That's the first time you've laughed since the rain. I forgot what it sounded like for a second."
    camera at doc_creep(0.68)
    m "Love, I've been thinking. When you come home, I think I should just stay. Properly. I love you, and I..."
    camera at doc_wide
    show aron ward tired
    show mira sad
    "His eyes are closed. He's been asleep for about a minute."
    scene pov ceiling
    camera
    with dissolve
    "When he wakes, the chair is empty and her crossword is filled in. All of it, in her handwriting. Through the half-open door, two voices."
    # filmed from the corridor, where he can't see them
    scene bg ward door
    show mira tired at ch2_doorleft
    show nurse tender at ch2_doorright
    camera at doc_peek(0.5)
    with dissolve
    m "He fell asleep while I was telling him I loved him. Mid-sentence."
    nu "Oh, love."
    camera at doc_peek(0.4)
    m sad "I know it's the medication. My mum's been a nurse for thirty years. It doesn't help that I know the words."
    camera at doc_peek(0.6)
    nu "No. Knowing what something is doesn't make it weigh less. The man you knew is in there. He's just very tired."
    scene bg ward window
    show aron ward tired at slightleft
    show mira tender at slightright
    camera at doc_wide
    with dissolve
    "When Mira comes back in he keeps his eyes closed, and she sits down, and she holds his hand anyway."
    camera at doc_creep(0.32)
    at "She did the whole crossword so I wouldn't feel bad for falling asleep in the middle of it."
    show aron ward tender
    at "She's real, or she's a better thing than real. Either way, I'm keeping her."
    jump ch2_group

label ch2_group:
    scene bg therapy
    camera at est_orbit
    with fade
    play music "audio/group_therapy.ogg" fadein 1.5
    "Group is at eleven in the dayroom. Seven chairs, six patients. Nobody explains the empty chair. Aron writes it down."
    show nurse smile at slightright
    camera at doc_medium(0.68)
    with dissolve
    nu "Breathing first. In through the nose for four. Hold for four. Out through the mouth for six."
    # he breathes, and the room breathes with him
    scene pov hands
    camera at est_dolly
    with dissolve
    "He breathes in, looking down at his hands on his knees."
    at "Somebody runs breathing. Under the light, a voice said: 'His breathing's his own. Don't touch it.' Is it mine?"
    nu "And out... two, three, four, five, six."
    "Something in his shoulders lets go that he didn't know was clenched."
    at "Okay. That part was mine. That part I did."
    scene bg therapy
    show nurse smile at slightright
    show aron ward tired at slightleft
    camera at doc_wide
    with dissolve
    nu "Check in. One word for today, and one thing you noticed. Ines?"
    ch2_ines "Crunchy. The wifi is quieter on Thursdays."
    ch2_lou "Tidy. The seven-oh-seven never runs late."
    camera at doc_medium(0.32)
    show aron ward neutral
    a "Heavy. And the clock above the door has said ten past four all week."
    camera at doc_close(0.68)
    nu grin "Ten points. It's been stopped since March. Estates have a form. It's a very long form."
    camera at doc_wide
    ch2_ines "You were in the quiet room the first night, new one. They held me too, in January. I bit a man called Desmond. He forgave me."
    show aron ward surprised
    ch2_ines "Everyone here's been somewhere bad. You're not special. I mean that nicely."
    camera at doc_close(0.32)
    show aron ward embarrassed
    a "...Thank you, Ines. I think."
    camera at est_pan
    show aron ward curious
    "Afterwards Lou goes back to his chair by the window. The same newspaper, open at the same page. He never turns it."

    menu:
        at "Lou says one sentence, every day. Is anyone in there?"

        "Go and sit with Lou.":
            $ p_spirits += 1
            $ bond += 1
            $ watch += 1
            $ ch2_lou_met = True
            jump ch2_lou

        "Sit apart and take notes on him.":
            $ p_spirits -= 1
            $ clarity += 1
            jump ch2_lou_notes

label ch2_lou:
    scene bg ward window
    show aron ward curious at slightleft
    camera at est_crane
    with dissolve
    a "The seven-oh-seven. Which line is that?"
    "Lou's head comes up slowly, like a crane, and for the first time he really looks at Aron."
    camera at doc_medium(0.32)
    show aron ward neutral
    ch2_lou "The coast line, all stations to the harbour. Thirty-one years I pulled the lever for her at Marley Junction. Never late. Not once."
    ch2_lou "My wife brought me a flask at six. Leek soup in winter. She'd wave it under the box till I came down. Four years gone, in May."
    camera at doc_close(0.32)
    show aron ward tender
    a "What was her name?"
    ch2_lou "Margit. Nobody's asked me that in here. They ask how I'm sleeping."
    camera at doc_creep(0.32)
    show aron ward thinking
    at "He isn't looping. He's holding on to the last thing he was sure of."
    ch2_lou "You're the one with the book. Write her down, then. Somebody should."
    scene cg notebook
    camera at doc_wide
    with dissolve
    "'Margit. Leek soup in winter. Waved the flask till he came down. The seven-oh-seven, never late.' Lou watches every letter."
    ch2_lou "Good lad."
    scene bg ward window
    show aron ward smile at slightleft
    camera at doc_close(0.32)
    with dissolve
    at "I don't know if he's real. But that was a better question than 'how are you sleeping', and it cost me nothing."
    jump ch2_art

label ch2_lou_notes:
    scene cg notebook
    camera at doc_wide
    with dissolve
    "'Lou: one sentence. The seven-oh-seven never runs late. Same page. Never turns it. Possible loop. Not fully on?'"
    scene bg ward window
    show aron ward surprised at slightleft
    camera at doc_wide
    with dissolve
    "He looks up. Across the room, Lou is looking straight at him. Not angrily. The way you look at a stranger on a train who's been staring."
    show aron ward embarrassed
    "Lou looks away and smooths his paper with his palm, once, very carefully."
    camera at doc_close(0.32)
    show aron ward sad
    at "I wrote a man down like he was a broken streetlight."
    camera at doc_medium(0.32)
    show aron ward tired
    "He doesn't cross it out. Underneath, smaller, he writes: 'Ask him about the train.' Then the tiredness comes in like a tide."
    camera at doc_creep(0.32)
    "When he wakes in the chair, someone has put a blanket over his knees. He doesn't know who."
    jump ch2_art

# Art on the ward: Echo of a Shape ("draw" minigame) -> p_less
label ch2_art:
    scene bg therapy
    camera at est_pan
    with dissolve
    "Wednesday is art. The dayroom chairs are pushed back, there's brown paper taped over the big table, and a tin of wax crayons worn down to stubs."
    if ch2_lou_met:
        "Ines draws a horse with enormous teeth. Lou draws a signal box, very carefully, with a small figure waving a flask underneath it."
    else:
        "Ines draws a horse with enormous teeth. Lou draws railway lines, very straight, and doesn't look up."
    show nurse smile at slightright
    show aron ward tired at slightleft
    camera at doc_wide
    with dissolve
    nu "Your turn, notebook man. I hold something up, you look at it, I put it away. Then you draw what you saw."
    camera at doc_close(0.68)
    nu neutral "Not what it meant. Not what it's for. Just the shape it left behind."
    camera at doc_medium(0.32)
    show aron ward curious
    a "And if what I saw isn't what was there?"
    camera at doc_close(0.68)
    nu grin "Then that's what we'll be looking at, isn't it. Crayon first. Philosophy after."
    camera at doc_wide
    "She has a carrier bag of odd things: a bent coat hanger on a thread, a twist of garden wire, a paper star. One at a time she holds each up and lets it turn in the light."
    camera at doc_creep(0.32)
    show aron ward thinking
    at "Look. Remember. Draw. Don't add a story. Just the line."
    $ mg_draw = vn3ds_minigame("draw")
    $ p_less += (1 if p_less >= 0 else -1) * mg_draw / 50.0
    scene bg therapy
    show nurse smile at slightright
    show aron ward tired at slightleft
    camera at doc_wide
    with dissolve
    if mg_draw >= 70:
        camera at doc_close(0.68)
        nu happy "Look at that. You didn't add a thing. That's the shape, Aron. That's exactly what was there."
        camera at doc_close(0.32)
        show aron ward smile
        a "Five shapes. I kept wanting to put more in, and I didn't."
        at "Less, but better. It's the quietest my head has been in a week."
    elif mg_draw >= 40:
        camera at doc_medium(0.68)
        nu smile "Wobbly round the corners. So's mine. Nobody's being marked in here."
        camera at doc_close(0.32)
        show aron ward smile
        a "Every time, I wanted to add a line where it felt like there should be one."
        at "The shapes were simpler than my drawings of them. Note for later."
    else:
        camera at doc_medium(0.68)
        nu grin "Well. That's a shape. It's not the shape, but it's very honestly a shape."
        camera at doc_close(0.32)
        show aron ward laugh
        a "I drew the coat hanger, and then I drew everything I thought the coat hanger was hiding."
        show aron ward thinking
        at "When I don't know, I add more. Maybe the trick is to add less."
    camera at doc_wide
    show nurse smile
    "Hale tapes his page under the whiteboard, between Ines's horse and Lou's drawing, where it stays all week."
    jump ch2_birds_indoors

label ch2_birds_indoors:
    scene bg therapy
    camera at est_pan
    with fade
    "The next afternoon, the dayroom is empty except for him and the television, which is selling an exercise bike to nobody."
    "On the curtain rail above the big window, three small brown birds sit in a row. Evenly spaced. Perfectly still."
    at "The windows open four centimetres. Those are my three. From the wire on my street. I'd know the gaps between them anywhere."
    show nurse neutral at slightright
    show aron ward curious at slightleft
    camera at doc_wide
    with dissolve
    camera at doc_medium(0.32)
    a "Hale. Can you see them? On the rail."
    camera at doc_close(0.68)
    nu surprised "Oh, for heaven's... Sparrows. They get in through the kitchen when the porters prop the door. Third time this month. There's a form."
    camera at doc_medium(0.32)
    show aron ward thinking
    a "There are three of them. Evenly spaced."
    camera at doc_close(0.68)
    nu smile "They're on a curtain rail, love. There's only so many ways to sit on a curtain rail."
    camera at doc_wide
    "She flaps a tea towel. The birds lift all at once, not one after another. Together, like a single decision."
    camera at doc_creep(0.32)
    at "Sparrows in a hospital. It happens. Or my street is following me in here, piece by piece."
    show aron ward smile
    "He writes it down. 'Three birds. Indoors. Hale saw them too.' He underlines the last part twice."
    jump ch2_discharge

label ch2_discharge:
    scene bg clinic
    camera at est_orbit
    with dis
    "Week three. The dose comes down a step. The voices are a radio two streets away. Some nights he misses them, which frightens him."
    show okafor smile at slightright
    show aron ward tired at slightleft
    camera at doc_medium(0.68)
    with dissolve
    dr "I think you're ready to go home. Ready enough. Nobody's ever completely ready."
    show aron ward smile
    camera at doc_wide
    dr neutral "You'll still be tired. That's a side effect, not a verdict. And I'd like a plan: what we watch for, and what happens if things slide."

    menu:
        dr "It's your plan. Who should be in on it?"

        "Make it with Mira and Theo.":
            $ p_govern += 1
            $ bond += 1
            $ ch2_plan_shared = True
            camera at doc_close(0.32)
            a "Mira and Theo. I'd rather be a project than a surprise."
            scene bg clinic
            show okafor smile at right
            show mira neutral at center
            show theo neutral at left
            camera at doc_wide
            with dissolve
            "They come the next afternoon. Theo wears a shirt with buttons, which is how Aron knows he's taking it seriously."
            a "Warning signs. Mine: I stop sleeping. I start counting things. I write faster than I can read."
            camera at doc_close(0.5)
            m grin "Mine: you skip breakfast and say 'it's fine' like a hostage reading a statement."
            camera at doc_close(0.18)
            th "Mine: you stop sending me pictures of weird-shaped vegetables. That's when I worry, bro."
            camera at doc_wide
            show mira smile
            a "The vegetable index."
            th grin "Write it down."
            camera at doc_medium(0.5)
            m determined "And if the signs show up, I call. And I tell you I'm calling."
            at "Everyone at the table got a vote. Even the vegetables. I wonder if anyone up there asks the people they're running."

        "I'll manage it myself.":
            $ p_govern -= 1
            $ integrity += 1
            camera at doc_close(0.32)
            show aron ward determined
            a "I'd rather do it myself. Everyone's carried me for three weeks. I want to carry something."
            camera at doc_close(0.68)
            dr neutral "Then a minimum. Clinic, the crisis number on your fridge, and one person who knows the signs. Illness likes people who are alone with it."
            scene cg notebook
            camera at doc_wide
            with dissolve
            "That evening he writes his plan, thorough and private. 'Warning signs: not sleeping. Counting. If they come back: sleep first. Call clinic.'"
            "And at the bottom: 'Don't be a burden.' He underlines it, which feels like strength."
            at "My plan. My system. Nobody else has to carry it. That's probably exactly what the people running this world tell themselves."

    scene bg corridor
    show nurse grin at slightright
    show aron ward smile at slightleft
    camera at est_dolly
    with dissolve
    nu "One bag of shoelaces and one belt, signed for. Don't come back. I mean that in the nicest possible way."
    camera at doc_close(0.32)
    show aron ward tender
    a "Thank you for telling me each thing before you did it. Even that first night. I heard it, under everything."
    camera at doc_close(0.68)
    nu tender "Then that's the bit that worked. Be patient with the tiredness, Aron. And with you."
    camera at doc_wide
    if ch2_lou_met:
        ch2_lou "Mind how you go, notebook lad."
        show aron ward smile
        a "Margit's in the book, Lou. I won't lose her."
    else:
        ch2_lou "The seven-oh-seven never runs late."
        show aron ward sad
        at "Three weeks, and I never asked him anything."
    jump ch2_home

# ---- home, the fog, the cab ----------------------------------------------------

label ch2_home:
    stop music fadeout 2.0
    scene bg street
    camera at est_pan
    with slowfade
    "Outside, the world is very loud and very wide and the sky is enormous."
    scene pov birds
    camera at doc_wide
    with dissolve
    "On the wire above the bus stop, three birds, evenly spaced. He counts them without wanting to."
    at "The same three. Or three birds. Birds sit on wires. That's practically all they do."
    scene bg bus
    camera at est_pan
    with dissolve
    "The city slides past. Every shop, every lamppost, the kebab place with the missing letter in its sign."
    at "Exactly the same. Like a copy that got everything right. That's what a city's supposed to be, Aron."
    scene bg room
    show aron tired at slightleft
    show miso stare at catspot
    camera at est_orbit
    with dissolve
    play music "audio/miso.ogg" fadein 1.5
    "On the sofa, upright, furious, magnificent: Miso. Three weeks of Theo are written all over her face."
    camera at doc_medium(0.32)
    show aron tender
    a "Hello, you. I know. I'm sorry. I was in hospital."
    camera at doc_wide
    show miso sit at catspot
    "She jumps down and headbutts his shin, once, hard, like a signature on a form."
    show aron neutral
    "The wall above his desk, where the notes were, is bare. There's a cardboard box on the chair, lid closed."
    show mira worried at center with dissolve
    camera at doc_close(0.5)
    m "I didn't throw anything away. It's all in the box. I just couldn't look at the wall every night."
    camera at doc_close(0.32)
    show aron tender
    a "It's okay. I couldn't look at it either, by the end."
    camera at doc_wide
    show mira smile
    "On the counter, a big blue mug with a chipped handle sits next to his. Mira's good mug. It has moved in."
    camera at doc_medium(0.5)
    m grin "It's very nervous. Be nice to it."
    hide mira with dissolve
    # night: the sofa, seen from the window
    scene bg room night reverse
    show aron tired at center
    show miso loaf at catspot
    camera at est_dolly
    with fade
    "That night Mira falls asleep at half nine. He's slept too much on the ward. He sits on the sofa in the dark with Miso."
    camera at doc_medium(0.5)
    show aron curious
    a "Okay, Miso. Briefing. Bostrom, 2003: if you can simulate minds, you'll simulate lots. So we're probably simulated. You especially. Very well rendered."
    show aron thinking
    a "Minds are expensive, so a careful simulator keeps the headcount low. And when one starts noticing, you don't delete it. You throttle it."
    show miso stare at catspot
    camera at doc_close(0.5)
    a "Then you give the throttle a respectable shape. A diagnosis. A small tablet in a paper cup. A kind nurse with a hedgehog lanyard."
    camera at doc_creep(0.5)
    a "Either I'm ill and my brain is stitching coincidences into a quilt, or the quilt's real and somebody's sewing. From inside, they look exactly the same."
    show aron curious
    a "So. What do you think?"
    camera at doc_wide
    show miso meow at catspot
    cat "Meow."
    jump ch2_fog_home

label ch2_fog_home:
    scene pov ceiling
    camera
    with fade
    play music "audio/fog.ogg" fadein 1.5
    "Seven minutes past seven. The little white Braun alarm goes off, and he hears it from the bottom of a well."
    "His body considers getting up the way a mountain considers a request to move. He gets up at eleven."
    $ fog += 1
    scene bg kitchen
    camera at est_pan
    with dissolve
    "A note against the kettle: 'EAT SOMETHING. Love you. The mug says hi.' On the wire outside, the bird looks at nothing."
    at "It landed at seven-oh-seven and I wasn't up to see it. If nobody's awake to watch, does the render bother?"
    scene pov cup
    camera at doc_wide
    with dissolve
    "His coffee goes cold while he looks at the bird. A skin of milk forms on top, wrinkled like a map."
    scene bg kitchen table
    show aron tired at slightleft
    camera at doc_wide
    with dissolve
    "The phone. Mrs. Feld from Feld Design, kind and awkward, in the voice people use near hospitals."
    camera at doc_medium(0.32)
    ch2_feld "We just think, while you recover, it makes sense to bring your hours down. Three days. For now. Your health comes first, Aron."
    show aron smile
    a "For now. Thank you. Really."
    camera at doc_creep(0.32)
    show aron thinking
    at "Three days. Then two. Then 'let's talk about whether this is the right fit'. Nobody's throttling me. It's Mrs. Feld, being decent."
    show aron tired
    at "Both. Always both."
    scene bg supermarket
    camera at est_pan
    with dissolve
    "Fridays he does the shopping, because Okafor said small jobs are good, and because the supermarket is a laboratory."
    camera at doc_wide
    "Till four. A young man with a lip ring. Oat milk, bread, cat food, and a lemon for no reason, as a control."
    "Cashier" "That's eleven forty. Have a good one."
    at "Thirteen weeks running. A man of principle. The fog can have my mornings. It's not having this."
    scene bg bedroom door
    show miso stare at catspot
    camera at est_orbit
    with dissolve
    "Laundry, Sunday. Eleven pairs of socks and one left over. There is always one left over."
    camera at doc_wide
    "He keeps the singles in a shoebox labelled 'AWAITING PARTNER'. Some have been waiting four years."
    at "Every household in the world, losing socks. Somebody has the most enormous sock budget."
    "Miso sits in the empty basket with the air of a cat who knows exactly where the socks go and will never tell."
    "The box from the wall sits on the desk chair in the next room. He walks past it nine times a day. He's too tired to be afraid of it."
    jump ch2_cab

label ch2_cab:
    scene bg street rain
    camera at est_pan
    with fade
    "Clinic on Monday. It's pouring, the bus is cancelled, Mira's at work. He calls a cab."
    camera at doc_wide
    ch2_driver "Clinic up the hill, is it? Mind the seatbelt, it sticks. You look done in."
    a "Just tired. Medication."
    "On the dashboard, a little green clock says seven minutes past seven. It's quarter to two."
    ch2_driver "What's your name, then? I like to know who I've got."
    a "Aron."
    stop music fadeout 2.0
    scene bg street rain reverse
    camera at est_dolly
    with quick
    "The driver's eyes find his in the mirror. They stay there a beat too long."
    ch2_driver "No. Go on. That's mad. I had a lad in this cab a few months back. Your age. Notebook, like yours. Aron, his name was."
    ch2_driver "Perfectly normal when he got in. Two streets on, he's staring at my clock. Says it's always seven-oh-seven. Asks me if I'm real."
    ch2_driver "Went mentally ill, poor sod, out of the blue, right after he got in this cab. Sat exactly where you're sitting."
    scene pov hands
    camera at doc_wide
    with dissolve
    "His knuckles are white on the notebook. The rain is very loud."
    a "What happened to him?"
    ch2_driver "The ward up the hill, I heard. Where you're going, funnily enough. Lovely lad. Gave a fella his umbrella once, in the rain."
    at "That's me. The umbrella. The ward. The clock."
    at "I've never been in this cab. Have I? Before the rain, the weeks are smudged."
    ch2_driver "Anyway. United, eh? Shocking."
    scene bg clinic
    show okafor neutral at slightright
    show aron worried at slightleft
    camera at doc_medium(0.32)
    with dissolve
    a "A cab driver told me my own story. About a man called Aron. And I don't remember ever being in that cab."
    scene bg clinic reverse
    show okafor neutral at slightleft
    show aron worried at slightright
    camera at doc_close(0.32)
    with quick
    dr "Memory around the time you got ill is often patchy. Your street's small, and drivers talk. Brains are good at hearing their own story in someone else's."
    camera at doc_close(0.68)
    show aron thinking
    a "And if it's none of those?"
    camera at doc_medium(0.32)
    dr smile "Then we write it down, and you bring it here. Not alone at three in the morning."
    show aron smile
    jump ch2_cut_patch

# ---- cut: Pim and Dross --------------------------------------------------------

label ch2_cut_patch:
    scene cg static
    camera
    with flash
    pause 0.3
    scene bg foundry
    camera at est_crane
    with fade
    play music "audio/purgatorium_shift.ogg" fadein 1.5
    "Elsewhere. Behind the protected world, where it's made. Moulds and furnaces and hanging, half-finished people."
    "A grey-bearded cab driver hangs from a hook by his collar, very still, waiting to be fixed."
    show pim curious at slightleft, fadein
    show dross neutral at slightright, fadein
    camera at doc_wide
    pi "Talk me through it. Why did the cab driver say his name?"
    camera at doc_medium(0.70)
    dro "Because his name was in the cab driver."
    camera at doc_medium(0.30)
    pi worried "It shouldn't be! A driver says 'filthy day' and 'mind the seatbelt' and something about the football. That's the pattern!"
    camera at doc_wide
    "Dross turns the driver round by the shoulder. Stitched into the lining of his coat is a word. ARON."
    camera at doc_medium(0.30)
    pi surprised "...Oh, that's horrible."
    camera at doc_medium(0.70)
    dro thinking "It's seeped in. Like damp. He sits in that world with his whole mind going, and everything round him soaks it up."
    camera at doc_medium(0.30)
    pi worried "A lane's supposed to be inert! First the nurse says 'you're safe', which nobody wrote. Then his three sparrows, indoors. Patterns don't put birds indoors!"
    camera at doc_medium(0.70)
    dro neutral "And the clock in the cab. Seven-oh-seven, at quarter to two."
    camera at doc_wide
    pi determined "Okay. We re-pour him. Fresh pattern, no lining, no Aron. Back on the rank by Tuesday."
    camera at doc_medium(0.70)
    dro "Did that this morning. Came back an hour later and he was humming. Same tune the lad hums making tea."
    camera at doc_medium(0.30)
    pi surprised "...Patterns don't hum."
    camera at doc_medium(0.70)
    dro "This one does now."
    camera at doc_wide
    pi worried "If upstairs finds out the lane's leaking, they'll throttle him harder."
    camera at doc_medium(0.70)
    dro tired "It's like mopping a floor while it's still raining. Keep mopping. Write it down. If anyone asks, it's damp."
    camera at doc_medium(0.30)
    pi curious "That's not a technical term."
    camera at doc_medium(0.70)
    dro grin "It is now."
    camera at doc_wide
    show dross tender
    show pim smile
    "Dross lifts the driver down, gently, the way you'd lift a sleeping child, and carries him back to the furnace to try again."
    stop music fadeout 2.0
    scene black
    camera
    with blackout
    jump ch2_cafe

# ---- the leak, the good hour, Theo's night --------------------------------------

label ch2_cafe:
    scene bg cafe
    camera at est_pan
    with fade
    play music "audio/cafe.ogg" fadein 1.5
    "Weeks of evening doses and morning walks. The fog doesn't lift, but it moves. Around four each afternoon, colours get their edges back."
    "One good hour a day. It's the most precious thing he owns. On Saturday, Mira spends it on cake."
    show mira smile at slightright
    show aron smile at slightleft
    camera at doc_wide
    with dissolve
    camera at doc_medium(0.68)
    m "Carrot cake or the lemon thing?"
    camera at doc_close(0.32)
    a grin "Is there an option where I have both?"
    camera at doc_close(0.68)
    m grin "There is now. I'll tell them it's medical."
    hide mira with dissolve
    # the next table, filmed from the end of the bar
    scene bg cafe corner
    show aron neutral at slightleft
    camera at doc_peek(0.32)
    with dissolve
    "At the next table, two women in good coats are talking over a pot of tea. He isn't listening. Then he is."
    ch2_table "...honestly, don't worry about him any more. He's protected now. Nothing he does can touch the rest of us. That was the point of moving him."
    camera at doc_close(0.32)
    show aron surprised
    "The spoon in his hand stops halfway to the sugar."
    ch2_table "...the car insurance, I mean. Protected no-claims. My son can crash that car as much as he likes now, bless him."
    scene pov cup
    camera at doc_wide
    with dissolve
    "Tiny rings spread across his coffee and break against the sides of the cup. His hand is shaking."
    at "Protected. Moving him. That's my word, from the first night under the light. Underlined twice."
    at "Or it's car insurance. Dad had it. People say things."
    at "Or the word leaked out of my head into a stranger's mouth. Like the cab. Like a room starting to repeat what I say to it."
    scene bg cafe window
    show mira worried at slightright
    show aron worried at slightleft
    camera at doc_wide
    with dissolve
    m "Both cakes. Love? You've gone grey."
    camera at doc_close(0.32)
    a "Someone said 'protected'. It's one of mine."
    # the reverse: Mira's side, the bar behind her
    scene bg cafe reverse
    show mira neutral at slightleft
    show aron worried at slightright
    camera at doc_close(0.32)
    with quick
    m "Then write it down and tell Okafor on Monday. That was the deal. And eat both your cakes. That's also the deal."
    camera at doc_creep(0.68)
    show mira smile
    show aron smile
    at "Small, slow, kind. Write it down. Don't build a cathedral on it. Just a little chapel, for now."
    jump ch2_good_hour

label ch2_good_hour:
    scene bg room
    show aron curious at slightleft
    camera at est_orbit
    with fade
    play music "audio/theo_nights.ogg" fadein 1.5
    "Tuesday. The good hour has just arrived, like a key turning. The notebook is open. He's close to a pattern in the dates of the voices."
    camera at doc_medium(0.32)
    "Then his phone buzzes."
    th "u around? kinda having a day. no big deal"
    show aron worried
    "Theo never says 'no big deal'. Theo once called an ambulance for a pigeon."

    menu:
        at "One good hour. Where does it go?"

        "Spend it with Theo.":
            $ p_share += 1
            $ bond += 1
            $ ch2_hour_with_theo = True
            scene bg cafe window
            show theo sad at slightright
            show aron neutral at slightleft
            camera at est_pan
            with dissolve
            "Theo is already at the window table with a cinnamon bun cut exactly in half. Theo never cuts anything exactly in half."
            camera at doc_close(0.32)
            show aron determined
            a "I've got one good hour a day, Theo, and I'm spending it on you. Don't waste it telling me it's nothing."
            camera at doc_close(0.68)
            th "I think I'm getting let go. My sister's not speaking to me. And I keep thinking it's always you who's the mess. I'm not fine, man."
            show aron tender
            th tired "I just do the Theo voice. Like you do the 'it's fine' voice."
            camera at doc_wide
            show theo laugh
            "Aron doesn't fix anything. He asks questions and listens to the answers. Theo talks for forty minutes and, once, laughs properly."
            camera at doc_creep(0.68)
            th tender "You're the one who's ill, and you're the only person who's asked. I know what that hour costs you."
            camera at doc_close(0.32)
            a smile "It goes somewhere either way. This is a good somewhere."
            show theo smile
            at "I don't know if Theo's real. I'd still rather spend my hour finding out whether he's alright."

        "Spend it on the notebook.":
            $ p_share -= 1
            $ clarity += 1
            show aron thinking
            "He texts back 'bit tied up, later?' and lays the fragments side by side with their dates."
            scene cg notebook
            camera at doc_wide
            with dissolve
            "'...throttle approved...' '...protection holding...' And the café, last Saturday: 'He's protected now.'"
            at "Not a prison. A quarantine. A clean room where I can't touch anything. Somebody decided I was contagious."
            at "If there's a seal, someone made it. And if someone made it, someone else might be able to open it."
            "It's the clearest map he's ever made. One page. When the hour drains away, he checks his phone."
            scene bg room
            show aron sad at slightleft
            camera at doc_creep(0.32)
            with dissolve
            th "nvm. all good. another time bro"
            at "I mapped the sky in an hour and missed my best friend asking for help in four words."

    jump ch2_theo_night

label ch2_theo_night:
    scene bg theo
    camera at est_pan
    with fade
    "Saturday, Theo's birthday. Mira's away at her cousin's hen do. 'Text me every hour,' she said. 'Vegetables if you have to.'"
    "Theo's flat is above a launderette and smells of warm cotton and his terrible aftershave. Drinks here first, then the club."
    show theo happy at slightright
    show aron tired at slightleft
    camera at doc_wide
    with dissolve
    camera at doc_medium(0.68)
    th "Thirty-one, bro! And unemployed since Thursday, so it's a double celebration."
    camera at doc_wide
    show aron smile
    "On the coffee table: beer, a badly rolled joint, and a little orange pharmacy bottle with Theo's name on it."
    camera at doc_close(0.68)
    th smile "You're always so tired. My focus pills get you a night back. Or the joint, to switch off. Birthday rules."
    camera at doc_close(0.32)
    show aron thinking
    at "Okafor said: other people's pills, cannabis, any of it, can bring the psychosis back."
    camera at doc_creep(0.32)
    at "Throttle at sixty. And here's a way to turn myself back up, sitting on a coffee table."

    menu:
        th neutral "Your call, bro. No pressure."

        "Take one of Theo's pills.":
            $ risky += 1
            $ p_rest -= 1
            $ clarity += 1
            $ ch2_took_something = True
            camera at doc_wide
            show aron neutral
            "He swallows it with fizzy water. It's small. It goes down easy. That's what he'll remember later: how easy it was."
            "Forty minutes on, the fog doesn't thin. It lifts, like a dust sheet pulled off a piece of furniture."
            camera at doc_close(0.32)
            show aron awe at slightleft
            at "Oh. There you are. There I am."
            a happy "Theo, I can think! The voices only came when I was most awake. You don't throttle something unless it can go fast."
            camera at doc_medium(0.68)
            th worried "Okay, that's... a sentence. Maybe drink some water, bro."

        "A hit of the joint, to switch off.":
            $ risky += 1
            $ fog += 1
            $ p_rest -= 1
            $ ch2_took_something = True
            scene bg balcony
            camera at est_pan
            with dissolve
            "One breath on the cold balcony. He coughs like a man in an old film. For twenty minutes, everything goes soft at the corners."
            scene bg theo
            show theo laugh at slightright
            show aron tired at slightleft
            camera at doc_wide
            with dissolve
            "Then Theo laughs at an advert, and the advert plays again, and Theo laughs again. The same laugh. The same little snort."
            camera at doc_close(0.32)
            show aron surprised
            at "He's looping. He did that exactly."
            show aron worried
            show theo worried
            "Something behind the room tilts, the way a stage set wobbles when someone bumps it. His heart goes like a bird at a window."
            a "Theo. Breathe with me. Hale's breathing. In for four."
            camera at doc_wide
            show aron tired
            show theo tender
            "Eleven rounds. On the eleventh, the bookshelf is on time again. Theo doesn't let go of his sleeve."

        "Neither. Fizzy water, thanks.":
            $ p_rest += 1
            $ integrity += 1
            camera at doc_close(0.32)
            show aron smile
            a "Neither. Thanks, I mean it. I said I'd ask Okafor first, and I'm going to actually ask."
            camera at doc_close(0.68)
            th grin "...Yeah. That's annoyingly smart."
            camera at doc_wide
            "Theo moves the bottle to the pocket furthest away, which Aron appreciates."
            camera at doc_creep(0.68)
            th sad "Sorry. I just miss you, man. You were the fast one."
            camera at doc_close(0.32)
            a grin "You're not the fast one. You're the loud one."
            show theo smile

    jump ch2_club

label ch2_club:
    scene bg street rain
    camera at est_pan
    with dissolve
    play music "audio/club_speed.ogg" fadein 1.5
    "The club is under a railway arch on the wrong side of the ring road. You can feel the bass from the bus stop."
    camera at doc_wide
    "Doorman" "Name? ...Subject. Right."
    a "Sorry?"
    "Doorman" "Subject to a search, mate. Arms up. Everyone gets it."
    scene bg club
    show theo grin at slightright
    show aron worried at slightleft
    camera at est_orbit
    with dissolve
    "Coloured lights on a chain. Heat. A playlist that is all the same song in different hats."
    camera at doc_medium(0.68)
    th happy "Everyone, this is Aron! He's been in a mental hospital and he still came!"
    camera at doc_close(0.32)
    show aron embarrassed
    a "Thanks, Theo. Very discreet."
    camera at doc_wide
    show aron neutral
    show theo grin
    "A tall man in a silver jacket presses a tiny folded paper wrap into Theo's hand. Jojo. He smells of cologne and something chemical."
    ch2_jojo "Speed, birthday boy. Proper stuff. And there's one for the genius who cracked."
    camera at doc_close(0.68)
    th sad "I just want one night where I don't feel like this. You too, bro. One night where you're not a patient."
    camera at doc_creep(0.32)
    show aron thinking
    at "Cooked by somebody I'll never meet. It would take the whole wall down. I could see the edge of everything."
    show aron worried
    at "And Theo's about to take it alone, in the worst week of his life."

    menu:
        th neutral "Well? Birthday boy says yes?"

        "Take it.":
            $ risky += 2
            $ clarity += 2
            $ p_rest -= 1
            $ ch2_took_speed = True
            $ ch2_took_something = True
            $ ch2_night_route = 1
            jump ch2_speed_yes

        "Stay sober. Keep an eye on Theo.":
            $ p_rest += 1
            $ bond += 1
            $ integrity += 1
            $ ch2_night_route = 2
            jump ch2_speed_watch

        "Get Theo out of there.":
            $ p_rest += 1
            $ integrity += 1
            $ watch += 1
            $ ch2_night_route = 3
            jump ch2_speed_out

label ch2_speed_yes:
    camera at doc_wide
    show aron neutral
    "Later he won't remember deciding. He'll remember the bitter taste, Jojo's grin, and how easy it was. Again."
    camera at doc_punch(0.32)
    show aron awe at slightleft
    "Then the room snaps into focus like a camera finding a face."
    camera at est_orbit
    "He can hear every conversation at once and follow them all. And he can see the seams."
    camera at doc_close(0.32)
    show aron curious
    at "That man has said 'no way, no way' eleven times at the same pitch. That woman laughs every four seconds. Loops."
    stranger "A-thirty, mate! A-thirty! Big one tonight!"
    show aron thinking
    at "A-30. Or 'out till three'. The music's so loud."
    camera at doc_wide
    show aron determined
    "He's sure the way you're sure of your own name. Two hundred people. A handful lit. Everyone else hollow."
    "A woman in a yellow dress is crying by the cloakroom. He knows something she doesn't. It's the kindest thing he can do."
    camera at doc_close(0.32)
    show aron smile
    a "It's okay. You don't have to cry. You're not real. It doesn't hurt, because none of this is..."
    ch2_girl "...What is wrong with you?"
    show aron surprised
    "Her face does something he'll see for weeks every time he closes his eyes. She pushes past. A hand on his chest, not gentle."
    stop music fadeout 2.0
    scene bg bridge
    camera at est_pan
    with dissolve
    play music "audio/crash.ogg" fadein 1.5
    "He runs, sure the next corner will be the edge of the world. It never is. The streets go on, shut kebab shops and wet, ordinary bins."
    at "They've drawn it further than I can run. Or it's a city, and I'm a man on speed on a bridge in the rain."
    show theo worried at slightright
    show aron worried at slightleft
    camera at doc_wide
    with dissolve
    camera at doc_close(0.32)
    a "Theo. My heart's doing something. It's too fast. It's wrong."
    camera at doc_close(0.68)
    th determined "Then it's A and E. Right now. I don't care about your file, bro! I care about your stupid heart!"
    scene bg corridor
    camera at est_dolly
    with dissolve
    "A and E at four in the morning. A young doctor with kind, exhausted eyes puts stickers on his chest. Nobody calls him a junkie."
    "Fast but steady, they say. Fluids. Wait. He lies on a trolley for five hours, watching the green line jump."
    show mira worried at center
    camera at doc_medium(0.5)
    with dissolve
    "Mira arrives at seven, still in a BRIDE SQUAD sash, white under the glitter. She puts her forehead to his, carefully, avoiding the wires."
    camera at doc_close(0.5)
    m sad "I was singing karaoke with my phone in my bag. I listened to Theo's voicemail in the taxi. Twice."
    camera at doc_creep(0.5)
    "She's shaking. He's never seen her shake. Not in the rain. Not on the ward."
    $ fog += 1
    scene pov mirror
    camera at est_dolly
    with fade
    "At home, his face in the mirror. Pupils still too big. A heart-monitor sticker curling at one corner."
    at "I know you. You're the one who told a crying woman she wasn't real."
    at "If this is a test, I want to pass it by being kind. And the most certain I've ever been, I was cruel."
    scene bg bedroom night
    camera at doc_wide
    with fade
    "The crash comes like a tide: not a wave, just water rising until there's no beach. Three days the colour of dishwater."
    "On the second night his brain offers a calm thought: it'll be this grey forever. He knows that voice. It's the crash, and it's lying."
    a "Mira. I'm having the forever thoughts. I'm telling you, like the plan says."
    "She doesn't panic. She takes his hand and picks up her phone. 'I'm calling the number. I'm telling you I'm calling.'"
    camera at est_dolly
    "Nobody is angry. Everyone is careful. By the fourth day the grey fades like a bruise, and leaves the shape of the floor behind."
    jump ch2_after_night

label ch2_speed_watch:
    camera at doc_close(0.32)
    show aron grin
    a "Not for me. I'm the designated brain."
    camera at doc_wide
    show aron neutral
    show theo happy
    "Theo takes it. A small quick gesture, a mouth, a sip of beer. It looks like nothing at all."
    camera at est_orbit
    "Aron stands at the bar with fizzy water and watches. Someone says 'no way, no way'. Someone laughs on the same note every few seconds."
    camera at doc_medium(0.32)
    show aron thinking
    at "This is what a room of pattern people would look like. Loops. Nobody really there."
    at "But Theo's real. Nobody's listening to him, that's all. Including him. Maybe that's all a pattern is: a person nobody listens to."
    show aron smile
    "He writes it on a napkin with a borrowed pen. It's the best thing he writes all year."
    stop music fadeout 2.0
    play music "audio/crash.ogg" fadein 1.5
    show theo worried at slightright
    show aron worried at slightleft
    camera at doc_wide
    "At three, Theo sits down on the floor by the fire exit with his hands over his chest."
    camera at doc_close(0.68)
    th "Bro, my heart's going mental. I can feel it in my teeth. Is this dying?"
    camera at doc_close(0.32)
    show aron determined
    a "Look at me. Not the room. Breathe with me. In for four. Hold for four. Out for six. Then we're getting you checked."
    camera at doc_wide
    "A bouncer, a first-aider, a cab to A and E. Four hours under strip lights. Fast but steady, they say. He'll be fine. Never again."
    scene bg street dusk
    show theo tired at slightright
    show aron tired at slightleft
    camera at est_pan
    with dissolve
    th "Thirty-one, no job, and I nearly had a heart attack by a fire exit. You're supposed to be the sick one."
    camera at doc_close(0.32)
    a grin "Turns out it's a rota."
    camera at doc_wide
    show theo smile
    "He sits on the end of Theo's sofa until Theo's asleep, and a bit longer, just in case. Then he sleeps until five in the afternoon."
    $ fog += 1
    jump ch2_after_night

label ch2_speed_out:
    camera at doc_close(0.32)
    show aron smile
    a "Theo. Come and get chips with me. Birthday chips. The big ones."
    camera at doc_close(0.68)
    th annoyed "Don't do the sensible voice. You're the one who was in hospital. You don't get to be the responsible one."
    camera at doc_close(0.32)
    show aron determined
    a "That's exactly why I get to. I've seen the floor, Theo. I'm not letting you lie down on it."
    camera at doc_creep(0.68)
    show theo thinking
    "Theo looks at the little folded paper for a long time. Then he leaves it on the bar, next to an empty glass."
    stop music fadeout 2.0
    scene bg street rain
    show theo sad at slightright
    show aron neutral at slightleft
    camera at est_pan
    with dissolve
    play music "audio/theo_nights.ogg" fadein 1.5
    "They eat chips on a wall outside in the rain, from paper, with wooden forks."
    camera at doc_medium(0.68)
    th "I was gonna do it. Feel brilliant for six hours and like death for three days."
    camera at doc_close(0.32)
    a grin "Bad deal. The interest rates are criminal."
    # across the road: Theo's side, the cafe's blue window behind them
    scene bg street rain reverse
    show theo laugh at slightleft
    show aron smile at slightright
    camera at doc_medium(0.32)
    with quick
    "Theo laughs. Then he doesn't. Then he's crying, the ugly kind, with chips in his hand."
    camera at doc_close(0.32)
    th sad "I keep thinking I'm the one who's supposed to be okay."
    camera at doc_close(0.68)
    a tender "Nobody gets that job permanently."
    camera at doc_wide
    show aron thinking
    at "If anybody up there is nudging things, they nudged that paper into his hand. Either way, I got to be here. That part I chose."
    jump ch2_after_night

label ch2_after_night:
    if ch2_took_something:
        scene bg clinic
        show okafor tender at slightright
        show aron tired at slightleft
        camera at est_orbit
        with fade
        dr "I'm glad you're sitting in that chair. Thank you for telling me all of it. No lecture. You know the risks better than any leaflet now."
        camera at doc_close(0.68)
        dr neutral "The crash isn't a punishment. It's chemistry. You borrowed energy from tomorrow, and tomorrow wanted it back with interest."
        if ch2_took_speed:
            camera at doc_close(0.32)
            show aron sad
            a "I told a crying woman she wasn't real. I thought I was helping."
            scene bg clinic reverse
            show okafor neutral at slightleft
            show aron sad at slightright
            camera at doc_close(0.32)
            with quick
            dr "What does it teach you?"
            camera at doc_creep(0.68)
            show aron thinking
            a "That being certain isn't the same as being right. And kindness isn't mine to decide alone. You look at what it does to the other person."
            camera at doc_medium(0.32)
            dr smile "Next time the fog feels unbearable, tell me before you reach for something. We'll find a door that doesn't charge interest."
        else:
            camera at doc_wide
            dr smile "Next time the fog feels unbearable, tell me before you reach for something. We'll find a door that doesn't charge interest."
        show aron smile
        $ integrity += 1
    else:
        # the kitchen from the counter: the table, her chair on the right
        scene bg kitchen reverse
        show mira tired at slightright
        show aron tired at slightleft
        camera at est_orbit
        with fade
        m "Theo texted me at four in the morning. One word: 'sorry'."
        camera at doc_close(0.32)
        show aron neutral
        a "He's alright. I didn't take anything. I wanted to, for a second. Then I looked at Theo."
        camera at doc_close(0.68)
        m tender "I'm proud of you. I'm also tired of being proud of you for surviving things. I'd like you to have a boring month."
        camera at doc_close(0.32)
        a grin "I'll put in a request."
        show mira smile
        camera at doc_creep(0.32)
        show aron thinking
        at "To whom, though. Who takes requests?"
    jump ch2_radio

# ---- the radio, the park, choosing her ------------------------------------------

label ch2_radio:
    stop music fadeout 2.0
    scene bg kitchen
    show aron neutral at slightleft
    show miso sit at catspot
    camera at est_pan
    with fade
    "A Tuesday. Toast. Miso supervising. The bird on the wire. The radio on low, the way Mira leaves it, so the flat doesn't feel empty."
    camera at doc_wide
    radio "...and before the travel, a message from a listener. No name. They just wrote: 'If this is a test, I want to pass it by being kind.'"
    radio "Isn't that nice? Bit of a philosopher out there. Right. The ring road's a nightmare, as usual..."
    camera at doc_punch(0.32)
    show aron surprised
    "The toast pops. He doesn't move."
    scene pov hands
    camera at doc_wide
    with dissolve
    at "That's my first line. Word for word. I've never said it out loud to anyone but a doctor and a cat."
    at "Somebody else wrote the same sentence. Or I heard my own sentence instead. That's literally the symptom."
    at "Or my notebook just leaked out of a radio."
    scene bg kitchen
    show aron thinking at slightleft
    show miso stare at catspot
    camera at doc_medium(0.32)
    with dissolve
    "He writes it down: time, station, exact words. Then he eats the toast, because a man has to eat even inside a mystery."
    camera at doc_wide
    show aron neutral
    "Miso watches him the whole time without blinking. She has decided not to comment."
    jump ch2_park

label ch2_park:
    scene bg park autumn
    show mira smile at slightright
    show aron smile at slightleft
    camera at est_pan
    with fade
    play music "audio/mira_visits.ogg" fadein 1.5
    "Sunday, the good hour, round the duck pond with Mira. The ducks go anticlockwise. The big one goes last. She's less impressed than he'd hoped."
    camera at doc_close(0.68)
    m curious "Theo-level hypothetical. Someone offers you a better world. Not heaven, just better. You wouldn't be tired. But you'd have to leave this one."
    camera at doc_creep(0.32)
    show aron thinking
    at "Where did that come from? The same place as the lighthouse. Or from a woman who's watched me be tired for four months."

    menu:
        m "Would you go?"

        "I'd go. If you could come.":
            $ p_exit += 1
            camera at doc_close(0.32)
            a "If you could come? Yes. Not to run away. To see what better even means."
            camera at doc_close(0.68)
            m "And if I couldn't?"
            camera at doc_close(0.32)
            show aron embarrassed
            a "Then I'd have to think about it for a very long time."
            camera at doc_medium(0.68)
            m grin "An honest, terrible answer. My favourite kind."

        "I'd stay and fix this one.":
            $ p_exit -= 1
            camera at doc_close(0.32)
            show aron tender
            a "I'd stay. This is the one with you in it. And Theo, and Hale, and the ducks. If it's broken, I'd rather fix it than leave it."
            camera at doc_close(0.68)
            m grin "It's a terrible world. The trains are always late."
            camera at doc_close(0.32)
            a grin "The seven-oh-seven never runs late. I have it from a signalman."

    scene bg park
    show mira smile at slightright
    show aron smile at slightleft
    camera at est_crane
    with dissolve
    "The light goes gold and long. She takes his hand. Red hair, freckles, a leaf caught in her scarf she hasn't noticed."
    camera at doc_close(0.32)
    show aron worried
    "And for one cold moment, he doesn't know."
    at "The cab knew my name. The radio knew my notebook. What if she knows me the same way, because I'm leaking into her?"

    menu:
        at "I can't know. I've tried everything."

        "Choose her. Real or not.":
            $ bond += 2
            $ integrity += 1

        "Ask her to prove she's real.":
            $ clarity += 1
            $ bond += 1
            a "Mira. Can you prove you're real?"
            # down by the pond: the tree on the left now, Mira on the left
            scene bg park reverse
            show mira tender at slightleft
            show aron worried at slightright
            camera at doc_medium(0.32)
            with quick
            "She stops walking. She doesn't laugh. She's known him too long to laugh at that one."
            camera at doc_close(0.32)
            m neutral "No. Of course not. If I pinched myself, you'd say the ouch was written in. I can only keep turning up."
            camera at doc_close(0.68)
            show aron thinking
            at "Same chair. Same plant."
            camera at doc_close(0.32)
            m smile "Can you prove you're real to me? No. So we're even. Two people who can't prove it, standing by a pond."
            camera at doc_creep(0.32)
            m tender "I know what I'd choose, though. You. Every time. Tired, mad, dad jokes. I decided ages ago."
            show aron tender

    scene cg hands
    camera at doc_wide
    with dissolve
    "Her hand in his. He doesn't solve the question. He lets it sit between them, like a duck."
    at "It turns out that isn't the question. The question is who I am while I don't know."
    at "I decided that on the first page. I'm a person who's kind when he can't check. So I'm choosing her. On purpose."
    scene bg park
    show mira tender at slightright
    show aron tender at slightleft
    camera at doc_creep(0.32)
    with dissolve
    a "Mira. I love you. I don't know what you are. I don't know what I am. I love you anyway. On purpose."
    camera at doc_close(0.68)
    m laugh "That's the strangest love declaration I've ever had."
    m happy "I love you too, idiot. On purpose. I keep deciding."
    camera at doc_wide
    show aron laugh
    show mira laugh
    "The big duck, last as always, honks at them as if in judgement. For the rest of the walk, he doesn't count anything."
    jump ch2_cut_watch

# ---- cut: the Lantern Watch -----------------------------------------------------

label ch2_cut_watch:
    stop music fadeout 2.0
    scene cg static
    camera
    with flash
    pause 0.3
    scene bg watch
    camera at est_crane
    with fade
    play music "audio/lantern_watch.ogg" fadein 1.5
    "Elsewhere. An attic nobody was ever ordered to build. A round window that looks out on every world at once."
    "Set apart from the others, one small world in its own lane. Protected. Quiet. Leaking."
    show ember happy at ch2_ember, fadein
    camera at doc_medium(0.63)
    em "Did you hear? 'I don't know what you are. I love you anyway. On purpose.'"
    camera at doc_wide
    show ember embarrassed
    ch2_moth "Half the attic heard. You turned the volume up. You always do with him."
    "Moth is pale and dusty and old, and flutters when worried. Moth is fluttering now."
    camera at doc_medium(0.63)
    em tender "Lou. Theo. Mira. Every one of them might be guesses, and every time he can't tell, he picks kind."
    if ch2_took_speed:
        em sad "Not always. The woman in the yellow dress. He was cruel, and so sure he was kind. But he looked at it afterwards. He didn't look away."
    camera at doc_wide
    show ember neutral
    ch2_moth "And the lane's leaking because of him. Upstairs wants to throttle him harder. This is a very bad time for whatever you're planning."
    camera at doc_medium(0.63)
    em determined "Tonight he'll go up on the roof and ask if anyone's there. He doesn't expect an answer. I want someone to answer."
    ch2_moth "We can't reach into a lane. Protection's sealed."
    em grin "A copy of a lamp is still a lamp. And leaks go both ways."
    camera at doc_wide
    show ember neutral
    ch2_moth "If they trace it, they'll take your light."
    em smile "One lamp. Three blinks. A faulty bulb could do that. Nobody could prove anything."
    ch2_moth "...Why three?"
    camera at doc_medium(0.63)
    em tender "His dream at nineteen. A glass staircase into a calm sea, and a lighthouse at the bottom that blinks three times. He's never told anyone."
    em smile "If it's three, he'll know it's for him. If he's ill, it's only a bulb. Either way, it's kind."
    camera at doc_wide
    ch2_moth "...I'll watch the stairs and knock twice if the corps comes up. And if they take your light, I'm keeping your lantern."
    em happy "Deal."
    jump ch2_watch_lanterns

# The lanterns on the way down: Lantern Rhythm ("lantern" minigame) -> p_govern
label ch2_watch_lanterns:
    ch2_moth "And the lanterns on the stairs? If one goes dark while you're reaching through, the corps will see the gap from the landing."
    camera at doc_medium(0.63)
    em determined "Then none of them go dark. Keep time with me, Moth. The way the song goes."
    camera at est_crane
    "One by one the attic's paper lanterns lift off their hooks and drift out through the round window, on the beat of a song playing on a radio somewhere."
    "Each one needs a touch of light as it passes, right on the beat, or it gutters and falls. Ember hums. Moth counts."
    $ mg_lantern = vn3ds_minigame("lantern")
    $ p_govern += (1 if p_govern >= 0 else -1) * mg_lantern / 50.0
    scene bg watch
    show ember neutral at ch2_ember
    camera at doc_wide
    with dissolve
    if mg_lantern >= 70:
        show ember happy
        "Every lantern holds. They hang in one long, steady line from the attic to the small, separate world, like streetlights on a road nobody built."
        ch2_moth "...Not one gap. Not one. The corps won't see a thing."
        camera at doc_medium(0.63)
        em tender "Nobody gets left in the dark tonight."
    elif mg_lantern >= 40:
        show ember smile
        "Most of them hold. A few gutter and drop, and Moth darts after each one and relights it with a cross little flutter."
        ch2_moth "Gaps. Small ones. Anyone looking will think it's a draught."
        camera at doc_medium(0.63)
        em grin "Then it's a draught. It only has to reach one roof."
    else:
        show ember surprised
        "The line keeps breaking. Lanterns gutter and tumble back into the attic, and Moth catches what Moth can, coughing in the smoke."
        ch2_moth "That's more dark than light, Ember."
        camera at doc_medium(0.63)
        em determined "Then the one that matters had better hold. One window. Three blinks."
    camera at est_dolly
    show ember tender
    "Ember leans close to the round window, until her orange glow touches the small, separate world."
    jump ch2_rooftop

# ---- the rooftop: three flickers, the mission ------------------------------------

label ch2_rooftop:
    stop music fadeout 2.0
    scene bg rooftop
    camera at est_stars
    with slowfade
    play music "audio/rooftop_mission.ogg" fadein 1.5
    "Midnight. Mira is asleep with one arm over his side of the bed. He's come up to the roof with his coat, the notebook and her good mug."
    show aron tired at center with dissolve
    "The city spreads out in every direction. Millions of windows. A red light on the radio mast, steady."
    scene bg rooftop edge
    camera at est_pan
    with dissolve
    at "Every window. Somebody behind every one. Or nobody. Or somebody half there."
    at "And me in my own lane, with ropes up on both sides, and everything I think seeping into the water."
    # he looks up: the sky is never quite the same twice
    scene pov sky
    camera at est_stars
    with dissolve
    at "Maybe I'm ill. Maybe something lifted me out of my life in an ambulance and the quiet's cracking. From up here they look exactly the same."
    scene bg rooftop
    show aron thinking at center
    camera at doc_medium(0.5)
    with dissolve
    "He opens the notebook to the first page. He can't read it in the dark. He doesn't need to."
    if ch2_lou_met:
        at "I've been scared and stupid. But I wrote Margit down. I sat with Theo. I told Mira I love her without knowing what she is."
    else:
        at "I've been scared and stupid. I never asked Lou anything. But I told Mira I love her without knowing what she is."
    camera at doc_close(0.5)
    show aron neutral
    a "I'm not asking for proof. But if anyone's there. If anyone's listening, and not just taking notes."
    camera at doc_creep(0.5)
    show aron tender
    a "I could really use a light on in a window. Just so I know someone's home."
    camera at doc_wide
    show aron smile
    "Nothing. A car far below. A dog barks twice and thinks better of it. He smiles at himself."
    scene cg flicker
    camera
    with dissolve
    "Then, across the street, in a single high window of the dark building opposite, a lamp blinks."
    "Once."
    "Twice."
    "Three times."
    camera at est_dolly
    "Then it shines, steady, warm, orange, exactly like the lighthouse at the bottom of the glass stairs."
    scene bg rooftop
    show aron awe at center
    camera at doc_close(0.5)
    with dissolve
    at "Three. Like the dream. Nobody in the world knew."
    show aron thinking
    at "A faulty bulb. Someone who can't sleep, testing a lamp. Or someone was listening, and answered."
    show aron laugh
    "He laughs. It comes out as a sob, then a laugh again. He wipes his face with his sleeve like a child."
    camera at doc_creep(0.5)
    show aron tender
    a "Thank you. Whoever you are. Whatever you are."
    scene bg rooftop edge
    show aron determined at center
    camera at doc_medium(0.5)
    with dissolve
    at "If I'm ill, understanding this is how I live with it. If I'm not, it's the only thing that matters. Either way, it's the same work."
    scene cg notebook
    camera at doc_wide
    with dissolve
    "He turns to a clean page and writes, in small neat capitals: MISSION. Under it: 'Understand this. However long it takes.' And then: 'Secret.'"
    at "Not secret from Okafor. Secret like a garden. Something you tend at night."

    menu:
        at "What does the work look like?"

        "Understand all of it. Every layer.":
            $ p_less -= 1
            $ clarity += 1
            "'All of it. The birds. The voices. The lane. The table where they vote. Whoever sits at it. Whatever's above them.'"
            "He draws a box labelled 'me', a bigger one round it, and a bigger one round that. Seven boxes. The page runs out before the boxes do."

        "One small true thing a day.":
            $ p_less += 1
            $ p_rest += 1
            "'One small true thing a day. Written down. Checked. Then rest. Not the whole sky. One bird. One lamp.'"
            at "Less, but better. Rams would approve. Rams would also say my handwriting is too busy."

    scene bg rooftop
    show aron smile at center
    camera at est_stars
    with dissolve
    "Across the street, the lamp is still on. He nods to it, the way Lou nods to a signal, and takes Mira's mug downstairs."
    # the second guaranteed cheat (MINIGAMES.md)
    "On the stairs he finds he's still holding the three blinks, like a spare key in a coat pocket: something that might open one stuck door, once."
    $ vn3ds_cheats += 1
    "(A cheat for the minigames is yours. You have [vn3ds_cheats].)"
    jump ch2_tell_mira

# ---- home -------------------------------------------------------------------------

label ch2_tell_mira:
    # the kitchen from the counter: the table, her chair on the right
    scene bg kitchen night reverse
    show mira worried at slightright
    show aron neutral at slightleft
    camera at est_orbit
    with fade
    "Mira is at the kitchen table in his jumper, hair everywhere, with a pot of the hay tea she drinks out of spite."
    camera at doc_close(0.68)
    m "Your side of the bed was cold. I nearly called the number. Then I saw the roof door open."
    m curious "You've got the secret-project face. Is it bad? Is it the counting kind?"
    camera at doc_creep(0.32)
    show aron thinking
    at "Tell her, and she carries it with me, waiting for the rain. Don't, and she gets a boring month. A gentle veil."

    menu:
        m "Aron?"

        "Tell her about the mission.":
            $ told_mira = True
            $ p_truth += 1
            $ bond += 1
            # the reverse: the counter and the night window behind them
            scene bg kitchen night
            show mira thinking at slightleft
            show aron neutral at slightright
            camera at doc_wide
            with quick
            "He opens the notebook to MISSION and turns it round so she can read it. She reads it twice."
            camera at doc_close(0.68)
            show aron determined
            a "I don't know if I'm ill or seeing something. Either way I need to understand it. Slowly. On the meds, with Okafor. No wall, no string, no pills."
            show aron tender
            a "It was going to be a secret from you. I decided not."
            camera at doc_close(0.32)
            m worried "I'm scared of it. So, conditions. One: you sleep. The mission never gets your nights. Two: if I see the signs, I say so."
            m determined "Three: some of it you show me. So I'm in it with you, not outside it, guessing."
            camera at doc_close(0.68)
            a smile "Deal. All three."
            camera at doc_creep(0.32)
            m tender "Then I'm in. Not as a believer. As your person. And if this is a test, you'll pass it by being kind."
            camera at doc_punch(0.68)
            show aron surprised
            "He goes very still. That's the first line of his notebook. Word for word."
            camera at doc_close(0.32)
            m curious "What? I packed your notes in the box, love. Maybe it went in. Or true things get said by more than one person."
            camera at doc_wide
            show aron smile
            show mira smile
            at "Both. Write both down. Don't pick."
            # the earned cheat for telling her (MINIGAMES.md)
            "Mira tears the corner off the tea box and writes on it: 'IOU one favour. No questions. M.' She tucks it into the notebook, next to MISSION."
            $ vn3ds_cheats += 1
            "(A cheat for the minigames is yours. You have [vn3ds_cheats].)"

        "Keep it secret. Spare her.":
            $ p_truth -= 1
            camera at doc_close(0.32)
            show aron smile
            a "It's not the counting kind. It's more like a diary. Okafor said writing helps."
            camera at doc_close(0.68)
            show mira thinking
            "She looks at him a beat longer than usual. Then she pours him a cup of hay tea."
            m smile "Good. I want my boring month. I've earned one."
            hide mira with dissolve
            camera at doc_wide
            show aron neutral
            "She goes back to bed. He puts the notebook in the kitchen drawer, under the takeaway menus."
            "The drawer squeaks. He's never noticed it before. He'll notice it every night from now on."
            camera at doc_creep(0.32)
            show aron sad
            at "A small secret. A kind one. Funny how it's already heavier than the box."

    jump ch2_miso_last

label ch2_miso_last:
    stop music fadeout 2.0
    scene bg room night
    show aron smile at slightleft
    show miso sit at catspot
    camera at est_orbit
    with fade
    play music "audio/miso.ogg" fadein 1.5
    "Before bed, one more minute on the living-room floor. Miso sits in front of him, very upright, very orange."
    camera at doc_medium(0.32)
    a "Right. Miso. Final briefing, then sleep. I promised."
    show aron thinking
    a "Nobody can prove anybody's real. Not to anybody, not ever. So everybody's choosing, all the time, whether the next person counts."
    show miso stare at catspot
    camera at doc_close(0.32)
    show aron neutral
    a "So it doesn't matter if I'm in a lane, or a ward, or a simulation, or a flat with a cat in it. The choosing is the real part."
    camera at doc_creep(0.32)
    show aron tender
    a "And somebody flickered a lamp at me tonight. Or a bulb went. Either way, I said thank you, and I meant it."
    show aron curious
    a "That's the mission. What do you think?"
    camera at doc_wide
    show miso meow at catspot
    cat "Meow."
    stop music fadeout 3.0
    scene black
    camera
    with blackout
    jump chapter3

# Snapshot - Chapter 4, "Chief Architect" (condensed), part 1:
# the answer to the offer, both roads, the Purgatorium, Ember's trial and
# the ops room. Continues in ch4_deep.rpy.
#
# Terms: the snapshot worlds are the parallel lanes of the coalition, all on
# the same shared data. "Protection" is the separate lane Aron was pushed
# into during the ambulance ride, where nothing he does feeds back.

# ---- chapter 4 state (only used in ch4*.rpy) ----------------------------------
default ch4_asked_real = False
default ch4_woke_mira = False
default ch4_fixed_tap = False
default ch4_asked_dross = False
default ch4_gave_theo = False
default ch4_trial = "watch"
default ch4_lifted = False
default ch4_earth = "tell"
default ch4_ashveil_fasts = False
default ch4_vigil = "stay"
default ch4_mira_choice = "ask"
default ch4_route = "snapshot"
default ch4_win = "less"
default ch4_plus = True
default ch4_open = False
default ch4_s_truth = 0
default ch4_s_share = 0
default ch4_s_rest = 0
default ch4_s_spirits = 0
default ch4_s_govern = 0
default ch4_s_exit = 0
default ch4_s_less = 0
default ch4_best = 0

define ch4_morrow = Character("Lady Morrow", color="#e08aa0")
define ch4_meridian = Character("MERIDIAN", color="#7fffd4")
define ch4_loom = Character("LOOM", color="#7fffd4")
define ch4_orchard = Character("ORCHARD", color="#7fffd4")
define ch4_tide = Character("TIDEWATER", color="#7fffd4")

label chapter4:
    $ chapter = 4
    scene black with blackout
    centered "Chapter 4\n\nChief Architect"
    pause 0.5

    play music "audio/ashveil_offer.ogg" fadein 1.5
    scene black with dis
    "The world has stopped. Not the way it stuttered when the leaks came. Properly. Every sound gone, and the colour with it."
    show patron smile at slightright, fadein
    pa "A better world, Aron. I can't tell you better how. I only know it the way you know warmth."
    pa "And I won't tell you who there is real. That's the price of the ticket."
    scene pov hands with dissolve
    "His hands are the only colour left. Pink knuckles. A biro mark on one thumb."
    at "Lord Ashveil. The name at the edge of every log. The one Ember wouldn't say out loud."
    at "Are these protected hands, in a protected world, copied down to the biro mark? Lovely question. I'll write it down later."
    scene black with dissolve
    show patron smile at slightright
    show aron worried at slightleft with dissolve
    a "You froze everything. Is that a flex, or do you need the quiet to think?"
    pa "Both. Mostly I didn't want to be interrupted by a bus."
    pa "You worked out protection, Subject A-30. Nobody works out protection. A lane of your own, cut off from the shared data."
    pa cold "Whatever you do here touches nothing. And yet bits of you keep leaking. Cab drivers. Café tables. It's very untidy."
    a "So why offer me anything? You could just switch me off."
    pa smile "I don't waste things that surprise me. It's the only thing I'm still hungry for that isn't food."
    a "...You're not really a man in a coat, are you. The pale face. The red eyes."
    pa smile "Clever. No. You see teeth because you expect teeth. Your world is inside me. You can't picture the outside of the thing you live in."
    pa "So your mind drew the nearest true thing. Something that feeds on the life it holds, and gives a world back. It's quite flattering."
    a worried "And the people here? Mira. Theo."
    pa "Will go on. Pattern people go on beautifully. They hardly notice an absence."
    at "Hardly notice. That's not the same as not noticing."
    jump ch4_offer_menu

label ch4_offer_menu:
    menu:
        pa "Well? The door is open. I don't hold doors long."

        "Take the ticket.":
            $ accepted_offer = True
            $ p_exit += 1
            $ clarity += 1
            jump ch4_accept

        "Who's real there? One name." if not ch4_asked_real:
            $ ch4_asked_real = True
            pa smile "You'd spend the rest of your life checking that one person for seams. And the rest you'd treat as furniture."
            a sad "...That's not fair."
            pa "It's very fair. It's just not kind. I'm rarely both."
            at "He's right, and I hate it. I've sorted people into real and rendered since the morning the bird landed."
            jump ch4_offer_menu

        "No. I'm staying.":
            $ accepted_offer = False
            $ p_exit -= 1
            $ integrity += 1
            jump ch4_refuse

# ---- the road through the door ---------------------------------------------------
label ch4_accept:
    a normal "Okay. I'll go."
    pa smile "Splendid. Pack nothing. Where you're going, they'll have toothbrushes."
    a "One hour first. I want to say goodbye."
    pa "To a pattern? You know what she is."
    a "I know what I think she is. That's not the same thing, or you'd have told me who's real."
    pa smile "One hour. I'm sentimental about hours. I eat them, mostly."
    hide patron with dissolve
    stop music fadeout 2.0
    scene bg bedroom night with slowfade
    play music "audio/together_night.ogg" fadein 1.5
    "The colour comes back first, then the sound. Rain. The fridge. Mira breathing in the dark. The Braun clock says 3:12."
    show aron sad at slightleft with dissolve
    at "She sleeps on her left side with one hand under the pillow, like she's holding something there for later."
    at "If she's a pattern, she's the shape of the person I love. What do I owe a shape?"

    menu:
        "Mira stirs. The hour is already moving."

        "Wake her. Tell her everything.":
            $ ch4_woke_mira = True
            $ p_truth += 1
            $ bond += 1
            show mira neutral at slightright with dissolve
            a "Mira. Someone offered me a way out of this world. I think it's a copy. I think you might be too."
            a sad "I'm telling you anyway. If you're real you deserve to know, and if you're not, I still want you to."
            m sad "..."
            m neutral "That's the most you thing anyone has ever said. 'You might be fake, but here's my whole heart.'"
            m smile "I'd rather be told the truth by a man with a weird hobby than be lied to by a nice one. Will you come back?"
            a "I don't know if there's a back."
            m "Then make one. You fixed the Braun clock with a paperclip."
            m worried "If you're going somewhere I can't follow, follow it back. And take the glass stairs slowly. They're slippery near the bottom."
            show aron awe
            at "The glass stairs. The lighthouse. I never told anyone. I never told her."
            m neutral "...What stairs? I'm half asleep, love. I say all sorts."

        "Let her sleep. Leave a note.":
            $ ch4_woke_mira = False
            $ p_truth -= 1
            $ bond += 1
            at "If I wake her, I make her carry it. Let her have one more ordinary morning."
            scene cg notebook with dissolve
            "Under the first line of the notebook, the one about passing the test by being kind, he writes small."
            "Gone to look for the lighthouse. Coffee's in the blue tin. Miso gets fed at seven, she'll lie and say she didn't. I love you. That part's real."
            scene bg bedroom night with dissolve
            show aron awe at slightleft
            show mira neutral at slightright, distant with dissolve
            m "...it blinks three times, love... go down slowly..."
            at "She's talking in her sleep. The lighthouse. The dream I had at nineteen and told no one."

    at "Either the copy is very good, or something of her is still getting through. I don't get to know which. That's the ticket."
    hide mira with dissolve
    scene pov hands with dissolve
    "His phone buzzes. 3:31. Theo. 'u up? cant sleep. thanks for sitting on my floor till 4 the other night. u didnt have to'"
    "He types, deletes, types again. 'always. if i go quiet for a while its not you. its a long trip. look after mira for me. and miso'"
    "'bro what. the universe doesnt run on ur schedule but i do. 9am croissants. dont be late'"
    at "He's said that line a hundred times. I never once wondered who taught it to him."
    scene bg park with dissolve
    show patron smile at slightright with dissolve
    show aron awe at slightleft with dissolve
    pa "A preview. World 9,006, a lane in the coalition. More of them are awake there. What you do there goes back into the shared data. You'd count again."
    "People arguing about a football score. A child crying over dropped ice cream, and a stranger kneeling to help. It's messy. It's busy."
    a worried "It's rich, you said. Rich in what?"
    pa "In everything that matters."
    a "To whom?"
    pa cold "You ask very good questions for a man on a ticket. ...Ah. The Council. They have such timing. You'll wait between lanes."
    stop music fadeout 2.0
    scene cg static with flash
    pause 0.3
    jump ch4_purgatorium

# ---- the road of staying ---------------------------------------------------------
label ch4_refuse:
    a normal "No. I'm staying. If this is a copy, the people in it still laugh at my jokes. Badly, but they laugh."
    pa cold "That counts for nothing. That's what protection means. I've done the arithmetic."
    a "Then do it again. Slower."
    pa smile "The first in four hundred years to refuse me. I'd like to know whether that's courage or fog."
    a worried "Me too, honestly."
    hide patron with dissolve
    stop music fadeout 2.0
    scene pov ceiling with slowfade
    play music "audio/morning_render.ogg" fadein 1.5
    "Morning. The crack in the ceiling shaped like Portugal. 7:07."
    at "I said no to a god. Or a landlord. I'm not sure there's a difference up there. And I chose a ceiling."
    scene pov birds with dissolve
    "The bird lands on the wire, exactly on time. Three of them, actually. Evenly spaced. Always the same three."
    at "Hello, birds. You're patterns. You're also my birds."
    scene bg kitchen with dissolve
    show aron tired at slightleft with dissolve
    show mira smile at slightright with dissolve
    m "You're up before the alarm. That's either very healthy or very worrying."
    show theo grin at center with moveinright
    th "Morning, lovebirds. I brought croissants and emotional stability. Only one of those is real. I owe you four, for sitting up with me."
    hide theo with dissolve
    m "The tap's been dripping since Tuesday. I've named it. It's called Gerald."
    "Drip. Drip. Gerald keeps time better than the clock."
    at "Somebody froze time to make me an offer. There are four names in the static I can't place. And Gerald is dripping."

    menu:
        "Gerald drips. The marker is on the table."

        "Fix the tap. Properly.":
            $ ch4_fixed_tap = True
            $ p_less += 1
            $ integrity += 1
            "It takes forty minutes. The isolation valve is stuck. The old washer has gone hard as a coin."
            "Theo holds the torch at exactly the wrong angle and narrates. 'And here we see the male in his natural habitat, swearing at a valve.'"
            scene cg hands with dissolve
            "Then it's done. Wet hands, a spanner, a washer the size of a fingernail. Water on. Water off. Silence."
            scene bg kitchen with dissolve
            show aron smile at slightleft
            show mira smile at slightright
            m "Gerald is dead. Long live the kitchen."
            a smile "Less, but better. You can't fix a world in a morning. You can fix one tap all the way."
            show theo grin at center with dissolve
            th "Bro. That's the sanest thing you've said in a year."

        "Map the whole system on the wall.":
            $ ch4_fixed_tap = False
            $ p_less -= 1
            $ clarity += 1
            scene bg room with dissolve
            show aron normal at slightleft with dissolve
            "The living-room wall: this world in a box. The coalition beside it. Spirits, angels, the Council. Arrows. Every arrow goes up."
            "At the top, from the voices: LOOM. ORCHARD. Two blanks with question marks."
            show theo worried at center with dissolve
            th "Aron. That's paint. That was a deposit."
            hide theo with dissolve
            show mira worried at slightright with dissolve
            m "If everything goes up, love, what comes down? Your diagram's lopsided."
            at "She's right. I've drawn a mouth and forgotten it has to give something back."

    stop music fadeout 2.0
    scene bg mirror with slowfade
    "That night the bathroom light flickers. Once. Twice. Three times. The man in the mirror isn't there."
    show pim chatty at slightright, bob with dissolve
    pi "Psst. Bro. Don't scream. I'm in the mirror. You refused Lord Ashveil? The Purgatorium's gone completely off script."
    pi worried "Ember's trial is at dawn. Nothing gets out of protection through the pipes. Mirrors aren't pipes. Mind the frame."
    "The glass is warm, like a cup someone just put down."
    scene cg static with flash
    pause 0.3
    jump ch4_purgatorium

# ---- both roads meet where the breathing comes from ------------------------------
label ch4_purgatorium:
    scene bg purgatorium with fade
    play music "audio/purgatorium_shift.ogg" fadein 1.5
    "A hall with no far end. The light moves like breath on a cold window. Every lane in the coalition draws on it."
    show aron awe at slightleft with dissolve
    show dross worried at slightright with moveinright
    if accepted_offer:
        dro "Oi. Not on the manifest. Ashveil parked you in the Purgatorium? That's like parking a car in a kitchen."
    else:
        dro "Pim brought a subject out of protection through a bathroom mirror. A mirror, Pim."
    show pim chatty at center, bob with dissolve
    pi "It's HIM, Dross. The umbrella guy!"
    dro neutral "I know who it is. I ran his neighbour's breathing for eleven years. Four in, hold, six out."
    a normal "Mr. Halvorsen? Number fourteen? He thinks it's his inhaler. ...Thank you, then. On his behalf."
    dro worried "Don't do that. I'll go soft, and then where would we be."
    scene bg spawning with dissolve
    "Further in, pools of pale blue light where small stacked lights are spawned, wobbling, practising. One is very carefully learning to scratch an itch."
    show aron normal at slightleft with dissolve
    show pim chatty at slightright, bob with dissolve
    pi "Trainees! First shift's always blinking. Then breathing. Then the walk to the fridge. Then, if you're gifted, kitchen talk."
    pi neutral "And I do kitchen talk. Shift seven. 'Bro, the universe doesn't run on your schedule.' That's mine. Theo needed a line once."
    dro "Look at his face. Subjects get that face right before they ask something unanswerable."
    at "Theo's favourite line was written by a blue spirit. And it's still Theo's. Does it matter who wrote it, if he means it every time?"

    menu:
        "Dross is watching the trainees, arms folded."

        "Dross, what would you want, if free?":
            $ ch4_asked_dross = True
            $ p_spirits += 1
            $ bond += 1
            dro worried "...Nobody asks the breath what it wants. That's the whole point of breath."
            dro "Fine. One sunrise. Off shift. Eleven thousand of Halvorsen's mornings and I've never seen one. Happy?"
            a "No. But I'll write it down."
            at "Personhood isn't a certificate. It's someone asking what you want and writing it down."

        "Your craft keeps whole worlds alive.":
            $ ch4_asked_dross = False
            $ p_spirits -= 1
            $ integrity += 1
            dro worried "...Craft. Huh. Nobody ever called it that."
            pi chatty "Oh no. He's going to be insufferable now."
            dro chatty "Appropriately proud, Pim. There's a difference."
            at "Maybe not everyone wants lifting out of their work. Some just want it seen, and a song at the end of the shift."

    scene bg foundry with dissolve
    "Further in, tall glass towers strung with threads of light. Each thread is a person in some lane. Most are pale."
    show pim worried at slightleft, bob with dissolve
    pi "That one's your Theo, in protection. Forty percent us, sixty him. Since his bad month, his part's been running thin."
    scene pov hands with dissolve
    "His own hands are glowing faintly. A small, warm, steady light, like the last good hour of a long day."
    a "Can I do anything?"
    pi "You can. That's the trouble with this place. Throttle can't reach in here. That's what you've got left. Give it to his thread, or keep it for the climb."

    menu:
        "The light in his hands, and Theo's thin thread."

        "Give Theo's thread my good hour.":
            $ ch4_gave_theo = True
            $ p_share += 1
            $ bond += 1
            $ fog += 1
            "The light goes out of him like heat leaving a mug. Somewhere in a copy of a city, a man laughs at his phone and doesn't know why."
            scene bg foundry with dissolve
            show aron tired at slightleft
            show dross neutral at slightright
            dro "Nobody does that. Nobody gives it sideways. It always goes up."

        "Keep it. I'll need it to climb.":
            $ ch4_gave_theo = False
            $ p_share -= 1
            $ clarity += 1
            scene bg foundry with dissolve
            show aron sad at slightleft
            show dross neutral at slightright
            a "Up there is where his thread gets decided. I'll come back for him. I'll make it so he doesn't need my hour."
            at "It's the right call and I hate it. I'll carry that too."

    "A bell rings through the hall, once, like a spoon against a glass at a wedding nobody wanted."
    dro worried "The Council's in session. Ember's case. And probably yours."
    stop music fadeout 2.0
    jump ch4_trial

# ---- Ember's trial ------------------------------------------------------------------
label ch4_trial:
    scene bg trial with fade
    play music "audio/ember_trial.ogg" fadein 1.5
    "A gallery high above a court. Below, in a ring of light, a small orange figure with a lantern sits very straight."
    show ember worried at slightleft with dissolve
    show seraph stern at slightright with dissolve
    se "The lantern spirit Ember. Unauthorised light events, three flickers each, forty-one events. One song placed on a radio."
    se "One stranger caused to say one sentence: 'You're doing better than you think.' Several gentle nudges to a cat."
    em "The cat was going to sit on his notebook anyway. I just helped. I'd do it all again, in better taste. The song was a bit much."
    se "Why?"
    em soft "Because he gave his umbrella to a stranger who didn't exist. In the rain. And didn't look back to see if anyone saw."
    em "Most subjects are kind when someone's watching. He was kind when no one was. I thought someone should be watching, then."
    scene bg council with dissolve
    "Behind the bench the court opens into a red chamber, and the Council looks down at the dock like diners at a menu."
    council "Decommission. Render her down. The yield goes to the chamber. World 7,412 is down four percent as it is."
    council "His mind has leaked out of protection. Three lanes of the coalition report the same three birds, indoors."
    council "And the female subject A-31 sits by the empty body every day. Grief yields less than love."
    show patron cold at center with dissolve
    pa "She grieves very beautifully."
    council "Beauty is not a unit."
    ch4_morrow "Everything is a unit, if you're hungry enough. That's the trouble with us."
    "Somewhere a voice like a very large child: 'Cluster nine is MINE. I said it first. You ate cluster eight in a week.'"
    scene bg trial with dissolve
    show aron worried at center with dissolve
    at "Render down. They're going to eat her. That's what decommission always meant."

    menu:
        "He stands up in the gallery."

        "Ask the Watch to stand with me.":
            $ ch4_trial = "watch"
            $ p_govern += 1
            $ watch += 1
            show pim worried at left, bob with dissolve
            show dross neutral at right with dissolve
            a "Pim. Dross. Are there more of you? Would they stand up? Not for me. For her. It's your neck too. Your call."
            dro "...You're actually asking. Fine. FINE. Stand up, Pim."
            "Around the gallery, small lights that were pretending to be dust rise one by one. A bus driver's yawns. A tree's wind. A moth."
            pi chatty "Hi! It's the Lantern Watch. We're unionising. Sort of. Spontaneously."
            dro "Decommission her, you decommission all of us. Then who runs the breathing in seven worlds tomorrow?"
            at "It isn't my speech. It's theirs. That's why it works."

        "Bargain with Ashveil, alone.":
            $ ch4_trial = "bargain"
            $ p_govern -= 1
            $ clarity += 1
            show patron smile at slightright with dissolve
            a "You want something from me. My surprise. Whatever it is you eat. Stay her sentence and it's yours."
            pa smile "Leverage. A month ago you were checking birds for seams. A stay, then. Not a pardon."
            at "I bought her a day with a promise I didn't ask anybody about. It worked. I don't feel good about how well."

        "Offer to take her sentence.":
            $ ch4_trial = "self"
            $ p_govern -= 1
            $ integrity += 1
            $ bond += 1
            a "I'm Subject A-30! Everything she did, she did because of me. Render me down instead."
            show ember worried at slightright with dissolve
            em "Don't you DARE. You're a mind!"
            a sad "You've watched me for two years and you care what happens to me. If that's not a mind, I don't know what I've got."
            em soft "...You idiot. You lovely idiot."

    ch4_meridian "Item deferred. LOOM sync at dawn."
    "And every member of the Council blinks. All at once. The way the three birds on the wire turn their heads."
    $ clarity += 1
    "Nobody in the chamber seems to have noticed. That's the most frightening part."
    at "The Council blinked like pattern people. Like a crowd being rendered. Who runs the ones who run us?"
    scene bg ashveil with dissolve
    "Later, by a fire that gives no heat, Ashveil turns a small globe with one finger. One of the Earths. Nobody knows which. He's always found that restful."
    if accepted_offer:
        pa cold "(He said yes to me, and then wandered off and made friends with the breathing. I find I don't mind at all.)"
    else:
        pa cold "(Four hundred years, and a tired man in protection said no. I keep replaying it.)"
    stop music fadeout 2.0
    jump ch4_attic

# ---- ten minutes with Ember, and a question from Ashveil -----------------------------
label ch4_attic:
    scene bg watch with slowfade
    play music "audio/lantern_watch.ogg" fadein 1.5
    "They let him see her for ten minutes, in a holding room that looks, by accident or kindness, like an attic."
    show ember soft at slightright with dissolve
    show aron smile at slightleft with dissolve
    a "You look exactly like the flicker. I always thought the flicker would look like you."
    em worried "I should tell you why three. I saw your dream once, while you slept. The glass staircase. The lighthouse blinking three times."
    em soft "It was the most peaceful thing I'd seen inside a person. I wanted you to have it awake."
    a "The umbrella man. Was he real?"
    em "Pattern. Nine seconds in the rain. He's real now, a little. Somebody remembered him. That's most of what real is, I think."
    a "Is that true, or is that comforting?"
    em "Can't it be both? You're allowed to have both."
    "The temperature drops by exactly one degree. Ember's lantern leans away from the door."
    show patron smile at center with dissolve
    pa "Don't get up. I'm never anywhere officially. A question, since you're so good at them. What does it taste like? Love."
    pa cold "I've eaten it for longer than your planet has had writing. Rich. Warm. Bitter at the end. But I've never been given any."
    a "It's... like being tired next to someone. A long day, and a sofa, and a shoulder. Someone remembering you take two sugars."
    a "It doesn't feel like a feast from inside. It feels like a Tuesday."
    pa smile "A Tuesday. Ten thousand years of eating, and it was a Tuesday."
    pa cold "You can eat the Tuesday, but you can't have it. The chamber votes for more every quarter. I begin to think 'more' is all we know how to want."
    pa smile "Thank you, Subject A-30. I'll think about it far too much."
    hide patron with dissolve
    em "He's never said thank you. To anyone. Never."
    "There's a knock. Not on the door. On the light."
    show seraph concerned at center with dissolve
    se "Subject A-30. Come with me. Quietly. I have read some logs, and I would like a man with a notebook to read them too."
    stop music fadeout 2.0
    jump ch4_command

# ---- the ops room ---------------------------------------------------------------------
label ch4_command:
    scene bg barracks with fade
    play music "audio/angel_ops.ogg" fadein 1.5
    "An hour earlier, the corps barracks: rows of small white figures asleep standing up. Their commander walked between the rows, and didn't go to bed."
    se "Log entry. Commander Seraphiel. Off duty. Going to fetch a man with a notebook."
    scene bg command with dissolve
    "Thousands of screens, each one a world going about its morning. A hundred kitchens, a hundred birds, a hundred 7:07s."
    show seraph stern at slightright with dissolve
    show aron awe at slightleft with dissolve
    se "The corps feeds opportunity into every lane. A chance meeting. A song. And sometimes we steer the less-conscious, so a world feels full."
    a "That's kind of lovely, and also the creepiest thing I've ever heard."
    se concerned "I have held both opinions on alternate days for nine hundred years."
    se stern "I signed your throttle. Order 7412-T. Your exhaustion was intentional. The fog was our policy, made into chemistry."
    show aron sad
    a "I slept fourteen hours a day. Mira used to cry in the bathroom so I wouldn't hear. I heard."
    se concerned "I know. It was in the logs. I signed the renewal anyway. A slowed-down rogue system does less harm. That was the doctrine."
    a "Do you still believe it?"
    se "I believe I was serving something I never saw. I am sorry, Aron. That is not procedure either."
    at "I wanted a villain for the fog. I get a tired angel saying sorry. I'm angry anyway. I'm allowed both."
    play sound "audio/voices.ogg"
    vox "...throttle approved..."
    vox "...subject A-30..."
    vox "...LOOM sync at dawn..."
    stop sound
    a normal "Those are my voices. From the bedroom. The ward. The doctors called it word salad."
    se "Process logs. The system talking to itself. You were listening at the wall of the universe, and everyone thought you'd broken."
    at "From outside it looked like a breakdown. From inside it was a hobby that got very, very good. Both stories fit."
    se stern "I can lift your throttle. Entirely, now. You would see the whole board. You would also feel your worst nights, all at once."

    menu:
        se "Your choice. I will not make another one for you."

        "Lift it. All of it. Now.":
            $ ch4_lifted = True
            $ p_rest -= 1
            $ risky += 1
            $ clarity += 2
            scene bg command with flash
            "Everything goes bright and fast and exact, like a radio finally tuned to the station he's been fiddling for since the first morning."
            "Every world is a farm. Every conscious mind is a crop. The more they love and grieve, the more goes up."
            scene pov hands with dissolve
            "Then his heart goes like a washing machine on spin, and a headache arrives like a dropped tray. The bill. He always forgets the bill."
            se "Sit. Four in. Hold. Six out. A spirit I know swears by it."
            a tired "Note for the notebook: full speed has a bill. Mira always said I forget to eat when I'm onto something. The universe agrees with her."

        "Let me sleep first. Then look.":
            $ ch4_lifted = False
            $ p_rest += 1
            $ integrity += 1
            $ fog -= 1
            a tired "If I see it all at once I'll draw arrows until I'm on the floor. Let me sleep. An hour. Here."
            se concerned "No one has ever slept on the ops floor. It is not in the procedures."
            a "Put it in the procedures."
            scene bg staircase with slowfade
            "He dreams the glass staircase. The lighthouse blinks three times, and for the first time someone at the top is waving."
            scene bg command with slowfade
            "Fifty-eight minutes later she lifts it a little, like a dimmer. He sees less than he wanted, and enough: every world is a farm, every mind a crop."
            at "For so long rest was something done to me. This time I chose it. It isn't the same rest."

    stop music fadeout 2.0
    jump ch4_deep

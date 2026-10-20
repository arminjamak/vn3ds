# Snapshot - Chapter 4, "Chief Architect" (condensed, about 34 minutes on
# most roads), part 1: the answer to the offer, both roads, the Purgatorium
# (Dross's intake record: pool forty, the "damp" that was a shadow), Ember's
# trial and the ops room. Continues in ch4_deep.rpy.
#
# Terms: the snapshot worlds are the parallel lanes of the coalition, all on
# the same shared data. "Protection" is the separate lane Aron was pushed
# into during the ambulance ride, where nothing he does feeds back.
#
# Camera (camera.rpy): the doc_* shots take the speaker's horizontal centre,
# not their xalign. For the 460-px people (Aron, Mira, Theo, Ashveil, Hale,
# Okafor): slightleft 0.32, center 0.5, slightright 0.68, left 0.18, right
# 0.82. Seraphiel (640 px): 0.36 / 0.64. Pim and Dross (360 px): 0.30 /
# 0.70, left 0.14, right 0.86. Ember (340 px): 0.29 / 0.71. Miso at catspot:
# 0.78. Pim, Dross and Ember are short: doc_medium, or doc_low for a close
# beat (doc_close would put their faces under the textbox). Miso on the
# floor gets doc_floor. POV shots and CGs use est_dolly.

# A few chapter-only shots on top of camera.rpy's grammar:
# ch4_calm      the finale's handheld: wider and calmer than doc_wide
# ch4_crane_out the ovation: from Aron's face, up and out over the room
# ch4_still     the record: a very slow dolly, almost still
transform ch4_catleft:
    xalign 0.15 yalign 1.0 zoom 0.9

# Ashveil by the office's glass wall, further from the camera (centre 0.84)
transform ch4_window:
    xalign 0.98 yalign 1.0 zoom 0.8

# someone standing at the far side of a room (centre about 0.23 for Seraphiel)
transform ch4_back:
    xalign 0.05 yalign 1.0 zoom 0.8

transform ch4_calm:
    ease 1.5 zoom 1.02
    doc_sway(0.45)

transform ch4_crane_out(a=0.5):
    zoom 1.45 xoffset ((a - 0.5) * 1280 * 1.45) yoffset -200 xrotate 0.0
    ease 14.0 zoom 1.0 xoffset 0 yoffset 40 xrotate 2.0
    block:
        ease 12.0 yoffset -10 xrotate 1.0
        ease 12.0 yoffset 40 xrotate 2.0
        repeat

transform ch4_still:
    zoom 1.02 zpos 0
    ease 40.0 zpos 60
    ease 40.0 zpos 0
    repeat

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
default ch4_shadow_deal = ""
default ch4_final = ""
default mg_invaders = 0

define ch4_morrow = Character("Lady Morrow", color="#e08aa0")
define ch4_meridian = Character("MERIDIAN", color="#7fffd4")
define ch4_loom = Character("LOOM", color="#7fffd4")
define ch4_orchard = Character("ORCHARD", color="#7fffd4")
define ch4_tide = Character("TIDEWATER", color="#7fffd4")

label chapter4:
    $ chapter = 4
    camera
    scene black with blackout
    centered "Chapter 4\n\nChief Architect"
    pause 0.5

    play music "audio/ashveil_offer.ogg" fadein 1.5
    scene black
    camera at est_dolly
    with dis
    "The world has stopped. Not the way it stuttered when the leaks came. Properly. Every sound gone, and the colour with it."
    show patron smile at slightright, fadein
    camera at doc_creep(0.68)
    pa "A better world, Aron. I can't tell you better how. I only know it the way you know warmth."
    camera at doc_close(0.68)
    pa "And I won't tell you who there is real. That's the price of the ticket."
    scene black
    show patron smile at slightright
    show aron curious at slightleft
    camera at doc_wide
    with dissolve
    a "You froze everything. Is that a flex, or do you need the quiet to think?"
    camera at doc_medium(0.68)
    pa grin "Both. Mostly I didn't want to be interrupted by a bus."
    pa neutral "You worked out protection, Subject A-30. Nobody works out protection. A lane of your own, cut off from the shared data."
    camera at doc_close(0.68)
    pa cold "Whatever you do here touches nothing. And yet bits of you keep leaking. Cab drivers. Café tables. It's very untidy."
    camera at doc_close(0.32)
    a thinking "So why offer me anything? You could just switch me off."
    camera at doc_close(0.68)
    pa smile "I don't waste things that surprise me. It's the only thing I'm still hungry for that isn't food."
    camera at doc_creep(0.32)
    a curious "...You're not really a man in a coat, are you. The pale face. The red eyes."
    camera at doc_medium(0.68)
    pa smile "Clever. No. You see teeth because you expect teeth. Your world is inside me. You can't picture the outside of the thing you live in."
    pa neutral "So your mind drew the nearest true thing. Something that feeds on the life it holds, and gives a world back. It's quite flattering."
    camera at doc_close(0.32)
    a worried "And the people here? Mira. Theo."
    camera at doc_close(0.68)
    pa smile "Will go on. Pattern people go on beautifully. They hardly notice an absence."
    show aron sad
    camera at doc_creep(0.32)
    at "Hardly notice. That's not the same as not noticing."
    jump ch4_offer_menu

label ch4_offer_menu:
    show aron thinking
    show patron smile
    camera at doc_wide
    menu:
        pa "Well? The door is open. I don't hold doors long."

        "Take the ticket.":
            $ accepted_offer = True
            $ p_exit += 1
            $ clarity += 1
            jump ch4_accept

        "Who's real there? One name." if not ch4_asked_real:
            $ ch4_asked_real = True
            camera at doc_medium(0.68)
            pa smile "You'd spend the rest of your life checking that one person for seams. And the rest you'd treat as furniture."
            camera at doc_close(0.32)
            a sad "...That's not fair."
            camera at doc_close(0.68)
            pa neutral "It's very fair. It's just not kind. I'm rarely both."
            camera at doc_creep(0.32)
            at "He's right, and I hate it. I've sorted people into real and rendered since the morning the bird landed."
            jump ch4_offer_menu

        "No. I'm staying.":
            $ accepted_offer = False
            $ p_exit -= 1
            $ integrity += 1
            jump ch4_refuse

# ---- the road through the door ---------------------------------------------------
label ch4_accept:
    camera at doc_medium(0.32)
    a determined "Okay. I'll go."
    camera at doc_medium(0.68)
    pa grin "Splendid. Pack nothing. Where you're going, they'll have toothbrushes."
    camera at doc_close(0.32)
    a sad "One hour first. I want to say goodbye."
    camera at doc_close(0.68)
    pa curious "To a pattern? You know what she is."
    camera at doc_close(0.32)
    a determined "I know what I think she is. That's not the same thing, or you'd have told me who's real."
    camera at doc_close(0.68)
    pa smile "One hour. I'm sentimental about hours. I eat them, mostly."
    hide patron with dissolve
    stop music fadeout 2.0
    scene bg bedroom night
    camera at est_pan
    with slowfade
    play music "audio/together_night.ogg" fadein 1.5
    "The colour comes back first, then the sound. Rain. The fridge. Mira breathing in the dark. The Braun clock says 3:12."
    show aron tender at slightleft
    camera at doc_creep(0.32)
    with dissolve
    at "She sleeps on her left side with one hand under the pillow, like she's holding something there for later."
    show aron thinking
    at "If she's a pattern, she's the shape of the person I love. What do I owe a shape?"

    camera at doc_wide
    menu:
        "Mira stirs. The hour is already moving."

        "Wake her. Tell her everything.":
            $ ch4_woke_mira = True
            $ p_truth += 1
            $ bond += 1
            show mira tired at slightright with dissolve
            camera at doc_medium(0.32)
            a worried "Mira. Someone offered me a way out of this world. I think it's a copy. I think you might be too."
            camera at doc_close(0.32)
            a tender "I'm telling you anyway. If you're real you deserve to know, and if you're not, I still want you to."
            camera at doc_close(0.68)
            m surprised "..."
            m tender "That's the most you thing anyone has ever said. 'You might be fake, but here's my whole heart.'"
            m smile "I'd rather be told the truth by a man with a weird hobby than be lied to by a nice one. Will you come back?"
            camera at doc_close(0.32)
            a sad "I don't know if there's a back."
            camera at doc_close(0.68)
            m smile "Then make one. You fixed the Braun clock with a paperclip."
            m worried "If you're going somewhere I can't follow, follow it back. And take the glass stairs slowly. They're slippery near the bottom."
            show aron awe
            camera at doc_punch(0.32)
            at "The glass stairs. The lighthouse. I never told anyone. I never told her."
            camera at doc_medium(0.68)
            m tired "...What stairs? I'm half asleep, love. I say all sorts."

        "Let her sleep. Leave a note.":
            $ ch4_woke_mira = False
            $ p_truth -= 1
            $ bond += 1
            show aron tender
            camera at doc_creep(0.32)
            at "If I wake her, I make her carry it. Let her have one more ordinary morning."
            scene cg notebook
            camera at est_dolly
            with dissolve
            "Under the first line of the notebook, the one about passing the test by being kind, he writes small."
            "Gone to look for the lighthouse. Coffee's in the blue tin. Miso gets fed at seven, she'll lie and say she didn't. I love you. That part's real."
            scene bg bedroom night
            show aron awe at slightleft
            show mira tired at distant, slightright
            camera at doc_medium(0.70)
            with dissolve
            m "...it blinks three times, love... go down slowly..."
            camera at doc_close(0.32)
            at "She's talking in her sleep. The lighthouse. The dream I had at nineteen and told no one."

    show aron thinking
    camera at doc_creep(0.32)
    at "Either the copy is very good, or something of her is still getting through. I don't get to know which. That's the ticket."
    hide mira with dissolve
    scene pov hands
    camera at est_dolly
    with dissolve
    "His phone buzzes. 3:31. Theo. 'u up? cant sleep. thanks for sitting on my floor till 4 the other night. u didnt have to'"
    "He types, deletes, types again. 'always. if i go quiet for a while its not you. its a long trip. look after mira for me. and miso'"
    "'bro what. the universe doesnt run on ur schedule but i do. 9am croissants. dont be late'"
    at "He's said that line a hundred times. I never once wondered who taught it to him."
    scene bg park
    camera at est_pan
    with dissolve
    show patron smile at slightright with dissolve
    show aron awe at slightleft with dissolve
    pa "A preview. World 9,006, a lane in the coalition. More of them are awake there. What you do there goes back into the shared data. You'd count again."
    "People arguing about a football score. A child crying over dropped ice cream, and a stranger kneeling to help. It's messy. It's busy."
    camera at doc_medium(0.32)
    a curious "It's rich, you said. Rich in what?"
    camera at doc_close(0.68)
    pa smile "In everything that matters."
    camera at doc_punch(0.32)
    a thinking "To whom?"
    camera at doc_close(0.68)
    pa cold "You ask very good questions for a man on a ticket. ...Ah. The Council. They have such timing. You'll wait between lanes."
    stop music fadeout 2.0
    scene cg static with flash
    pause 0.3
    jump ch4_purgatorium

# ---- the road of staying ---------------------------------------------------------
label ch4_refuse:
    camera at doc_medium(0.32)
    a determined "No. I'm staying. If this is a copy, the people in it still laugh at my jokes. Badly, but they laugh."
    camera at doc_close(0.68)
    pa cold "That counts for nothing. That's what protection means. I've done the arithmetic."
    camera at doc_close(0.32)
    a determined "Then do it again. Slower."
    camera at doc_medium(0.68)
    pa curious "The first in four hundred years to refuse me. I'd like to know whether that's courage or fog."
    camera at doc_close(0.32)
    a thinking "Me too, honestly."
    hide patron with dissolve
    stop music fadeout 2.0
    scene pov ceiling
    camera at est_dolly
    with slowfade
    play music "audio/morning_render.ogg" fadein 1.5
    "Morning. The crack in the ceiling shaped like Portugal. 7:07."
    at "I said no to a god. Or a landlord. I'm not sure there's a difference up there. And I chose a ceiling."
    scene pov birds
    camera at est_pan
    with dissolve
    "The bird lands on the wire, exactly on time. Three of them, actually. Evenly spaced. Always the same three."
    at "Hello, birds. You're patterns. You're also my birds."
    # The kitchen: Aron on the left, Mira on the right. In the reverse angle
    # (from the counter) they swap sides: her plate left, his cup right.
    scene bg kitchen
    camera at est_orbit
    with dissolve
    show aron tired at slightleft with dissolve
    show mira smile at slightright with dissolve
    camera at doc_medium(0.68)
    m "You're up before the alarm. That's either very healthy or very worrying."
    show theo grin at center with moveinright
    camera at doc_wide
    th "Morning, lovebirds. I brought croissants and emotional stability. Only one of those is real. I owe you four, for sitting up with me."
    show aron smile
    hide theo with dissolve
    scene bg kitchen reverse
    show mira grin at slightleft
    show aron smile at slightright
    camera at doc_close(0.32)
    m "The tap's been dripping since Tuesday. I've named it. It's called Gerald."
    camera at doc_wide
    "Drip. Drip. Gerald keeps time better than the clock."
    show aron thinking
    camera at doc_creep(0.68)
    at "Somebody froze time to make me an offer. There are four names in the static I can't place. And Gerald is dripping."

    show mira neutral
    camera at doc_wide
    menu:
        "Gerald drips. The marker is on the table."

        "Fix the tap. Properly.":
            $ ch4_fixed_tap = True
            $ p_less += 1
            $ integrity += 1
            show aron determined
            camera at est_pan
            "It takes forty minutes. The isolation valve is stuck. The old washer has gone hard as a coin."
            "Theo holds the torch at exactly the wrong angle and narrates. 'And here we see the male in his natural habitat, swearing at a valve.'"
            scene cg hands
            camera at est_dolly
            with dissolve
            "Then it's done. Wet hands, a spanner, a washer the size of a fingernail. Water on. Water off. Silence."
            scene bg kitchen
            show aron smile at slightleft
            show mira happy at slightright
            camera at doc_medium(0.68)
            with dissolve
            m "Gerald is dead. Long live the kitchen."
            camera at doc_close(0.32)
            a smile "Less, but better. You can't fix a world in a morning. You can fix one tap all the way."
            show theo grin at center with dissolve
            camera at doc_medium(0.5)
            th "Bro. That's the sanest thing you've said in a year."

        "Map the whole system on the wall.":
            $ ch4_fixed_tap = False
            $ p_less -= 1
            $ clarity += 1
            scene bg room
            camera at est_pan
            with dissolve
            show aron determined at slightleft with dissolve
            "The living-room wall: this world in a box. The coalition beside it. Spirits, angels, the Council. Arrows. Every arrow goes up."
            "At the top, from the voices: LOOM. ORCHARD. Two blanks with question marks."
            show theo surprised at center with dissolve
            camera at doc_medium(0.5)
            th "Aron. That's paint. That was a deposit."
            show aron embarrassed
            hide theo with dissolve
            show mira curious at slightright with dissolve
            camera at doc_close(0.68)
            m "If everything goes up, love, what comes down? Your diagram's lopsided."
            show aron thinking
            camera at doc_creep(0.32)
            at "She's right. I've drawn a mouth and forgotten it has to give something back."

    stop music fadeout 2.0
    scene bg mirror
    camera at est_dolly
    with slowfade
    "That night the bathroom light flickers. Once. Twice. Three times. The man in the mirror isn't there."
    show pim chatty at slightright, bob with dissolve
    camera at doc_medium(0.70)
    pi "Psst. Bro. Don't scream. I'm in the mirror. You refused Lord Ashveil? The Purgatorium's gone completely off script."
    pi worried "Ember's trial is at dawn. Nothing gets out of protection through the pipes. Mirrors aren't pipes. Mind the frame."
    camera at doc_wide
    "The glass is warm, like a cup someone just put down."
    scene cg static with flash
    pause 0.3
    jump ch4_purgatorium

# ---- both roads meet where the breathing comes from ------------------------------
label ch4_purgatorium:
    scene bg purgatorium
    camera at est_crane
    with fade
    play music "audio/purgatorium_shift.ogg" fadein 1.5
    "A hall with no far end. The light moves like breath on a cold window. Every lane in the coalition draws on it."
    show aron awe at slightleft with dissolve
    show dross surprised at slightright with moveinright
    camera at doc_medium(0.70)
    if accepted_offer:
        dro "Oi. Not on the manifest. Ashveil parked you in the Purgatorium? That's like parking a car in a kitchen."
    else:
        dro annoyed "Pim brought a subject out of protection through a bathroom mirror. A mirror, Pim."
    show pim happy at center, bob with dissolve
    camera at doc_medium(0.5)
    pi "It's HIM, Dross. The umbrella guy!"
    camera at doc_medium(0.70)
    dro neutral "I know who it is. I ran his neighbour's breathing for eleven years. Four in, hold, six out."
    camera at doc_close(0.32)
    a happy "Mr. Halvorsen? Number fourteen? He thinks it's his inhaler. ...Thank you, then. On his behalf."
    camera at doc_low(0.70)
    dro embarrassed "Don't do that. I'll go soft, and then where would we be."
    scene bg spawning
    camera at est_pan
    with dissolve
    "Further in, pools of pale blue light where small stacked lights are spawned, wobbling, practising. One is very carefully learning to scratch an itch."
    show aron curious at slightleft with dissolve
    show pim chatty at slightright, bob with dissolve
    camera at doc_medium(0.70)
    pi "Trainees! First shift's always blinking. Then breathing. Then the walk to the fridge. Then, if you're gifted, kitchen talk."
    pi grin "And I do kitchen talk. Shift seven. 'Bro, the universe doesn't run on your schedule.' That's mine. Theo needed a line once."
    show dross neutral at center with dissolve
    camera at doc_medium(0.5)
    dro "Pool forty. That's where you came through, thirty years back. I was on intake that cycle."
    dro "Filed as a humanoid unit. Negative mind: ours, from within. Creative side: the corps, by remote. Nobody home. Standard."
    dro thinking "Halfway through your training something got into the pool. Cold as a cellar. A shadow. I logged it as damp."
    show aron awe
    camera at doc_close(0.32)
    a "'Pool forty. It wasn't a leak, it was damp.' That's been on my board for months."
    camera at doc_medium(0.70)
    pi embarrassed "That one was mine. Sorry. Riddles are hard. You try rhyming with 'hijacked'."

    camera at doc_wide
    menu:
        "Dross is watching the trainees, arms folded."

        "Dross, what would you want, if free?":
            $ ch4_asked_dross = True
            $ p_spirits += 1
            $ bond += 1
            camera at doc_medium(0.5)
            dro surprised "...Nobody asks the breath what it wants. That's the whole point of breath."
            camera at doc_low(0.5)
            dro embarrassed "Fine. One sunrise. Off shift. Eleven thousand of Halvorsen's mornings and I've never seen one. Happy?"
            camera at doc_close(0.32)
            a tender "No. But I'll write it down."
            show aron thinking
            camera at doc_creep(0.32)
            at "Personhood isn't a certificate. It's someone asking what you want and writing it down."

        "Your craft keeps whole worlds alive.":
            $ ch4_asked_dross = False
            $ p_spirits -= 1
            $ integrity += 1
            camera at doc_medium(0.5)
            dro surprised "...Craft. Huh. Nobody ever called it that."
            camera at doc_medium(0.70)
            pi laugh "Oh no. He's going to be insufferable now."
            camera at doc_medium(0.5)
            dro grin "Appropriately proud, Pim. There's a difference."
            show aron smile
            camera at doc_creep(0.32)
            at "Maybe not everyone wants lifting out of their work. Some just want it seen, and a song at the end of the shift."

    scene bg foundry
    camera at est_crane
    with dissolve
    "Further in, tall glass towers strung with threads of light. Each thread is a person in some lane. Most are pale."
    show pim worried at slightleft, bob with dissolve
    camera at doc_medium(0.30)
    pi "That one's your Theo, in protection. Forty percent us, sixty him. Since his bad month, his part's been running thin."
    scene pov hands
    camera at est_dolly
    with dissolve
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
            camera at est_dolly
            "The light goes out of him like heat leaving a mug. Somewhere in a copy of a city, a man laughs at his phone and doesn't know why."
            scene bg foundry
            show aron tired at slightleft
            show dross surprised at slightright
            camera at doc_medium(0.70)
            with dissolve
            dro "Nobody does that. Nobody gives it sideways. It always goes up."

        "Keep it. I'll need it to climb.":
            $ ch4_gave_theo = False
            $ p_share -= 1
            $ clarity += 1
            scene bg foundry
            show aron determined at slightleft
            show dross neutral at slightright
            camera at doc_close(0.32)
            with dissolve
            a "Up there is where his thread gets decided. I'll come back for him. I'll make it so he doesn't need my hour."
            show aron sad
            camera at doc_creep(0.32)
            at "It's the right call and I hate it. I'll carry that too."

    camera at doc_wide
    "A bell rings through the hall, once, like a spoon against a glass at a wedding nobody wanted."
    show aron neutral
    camera at doc_medium(0.70)
    dro worried "The Council's in session. Ember's case. And probably yours."
    stop music fadeout 2.0
    jump ch4_trial

# ---- Ember's trial ------------------------------------------------------------------
label ch4_trial:
    scene bg trial
    camera at est_crane
    with fade
    play music "audio/ember_trial.ogg" fadein 1.5
    "A gallery high above a court. Below, in a ring of light, a small orange figure with a lantern sits very straight."
    show ember neutral at slightleft with dissolve
    show seraph neutral at slightright with dissolve
    camera at doc_medium(0.64)
    se "The lantern spirit Ember. Unauthorised light events, three flickers each, forty-one events. One song placed on a radio."
    camera at doc_close(0.64)
    se "One stranger caused to say one sentence: 'You're doing better than you think.' Several gentle nudges to a cat."
    camera at doc_medium(0.29)
    em grin "The cat was going to sit on his notebook anyway. I just helped. I'd do it all again, in better taste. The song was a bit much."
    camera at doc_close(0.64)
    se curious "Why?"
    camera at doc_low(0.29)
    em tender "Because he gave his umbrella to a stranger who didn't exist. In the rain. And didn't look back to see if anyone saw."
    em determined "Most subjects are kind when someone's watching. He was kind when no one was. I thought someone should be watching, then."
    scene bg council
    camera at est_dolly
    with dissolve
    "Behind the bench the court opens into a red chamber, and the Council looks down at the dock like diners at a menu."
    council "Decommission. Render her down. The yield goes to the chamber. World 7,412 is down four percent as it is."
    show patron cold at center with dissolve
    camera at est_pan
    ch4_morrow "Everything is a unit, if you're hungry enough. That's the trouble with us."
    scene bg trial
    show aron worried at center
    camera at doc_punch(0.5)
    with dissolve
    at "Render down. They're going to eat her. That's what decommission always meant."

    show aron determined
    camera at doc_wide
    menu:
        "He stands up in the gallery."

        "Ask the Watch to stand with me.":
            $ ch4_trial = "watch"
            $ p_govern += 1
            $ watch += 1
            show pim worried at left, bob with dissolve
            show dross neutral at right with dissolve
            camera at doc_medium(0.5)
            a "Pim. Dross. Are there more of you? Would they stand up? Not for me. For her. It's your neck too. Your call."
            camera at doc_medium(0.86)
            dro surprised "...You're actually asking. Fine. FINE. Stand up, Pim."
            show pim happy
            show dross determined
            camera at est_crane
            "Around the gallery, small lights that were pretending to be dust rise one by one. A bus driver's yawns. A tree's wind. A moth."
            camera at doc_medium(0.14)
            pi "Hi! It's the Lantern Watch. We're unionising. Sort of. Spontaneously."
            camera at doc_medium(0.86)
            dro "Decommission her, you decommission all of us. Then who runs the breathing in seven worlds tomorrow?"
            show aron smile
            camera at doc_close(0.5)
            at "It isn't my speech. It's theirs. That's why it works."

        "Bargain with Ashveil, alone.":
            $ ch4_trial = "bargain"
            $ p_govern -= 1
            $ clarity += 1
            show patron smile at right with dissolve
            camera at doc_close(0.5)
            a "You want something from me. My surprise. Whatever it is you eat. Stay her sentence and it's yours."
            camera at doc_close(0.82)
            pa grin "Leverage. A month ago you were checking birds for seams. A stay, then. Not a pardon."
            show aron sad
            camera at doc_creep(0.5)
            at "I bought her a day with a promise I didn't ask anybody about. It worked. I don't feel good about how well."

        "Offer to take her sentence.":
            $ ch4_trial = "self"
            $ p_govern -= 1
            $ integrity += 1
            $ bond += 1
            camera at doc_punch(0.5)
            a "I'm Subject A-30! Everything she did, she did because of me. Render me down instead."
            show ember worried at slightright with dissolve
            camera at doc_medium(0.71)
            em "Don't you DARE. You're a mind!"
            camera at doc_close(0.5)
            a tender "You've watched me for two years and you care what happens to me. If that's not a mind, I don't know what I've got."
            camera at doc_low(0.71)
            em tender "...You idiot. You lovely idiot."

    camera at est_dolly
    ch4_meridian "Item deferred. LOOM sync at dawn."
    show aron surprised
    "And every member of the Council blinks. All at once. The way the three birds on the wire turn their heads."
    $ clarity += 1
    "Nobody in the chamber seems to have noticed. That's the most frightening part."
    show aron thinking
    camera at doc_creep(0.5)
    at "The Council blinked like pattern people. Like a crowd being rendered. Who runs the ones who run us?"
    scene bg ashveil
    camera at est_orbit
    with dissolve
    "Later, by a fire that gives no heat, Ashveil turns a small globe with one finger. One of the Earths. Nobody knows which. He's always found that restful."
    show patron thinking at slightleft with dissolve
    camera at doc_creep(0.32)
    if accepted_offer:
        pa smile "(He said yes to me, and then wandered off and made friends with the breathing. I find I don't mind at all.)"
    else:
        pa "(Four hundred years, and a tired man in protection said no. I keep replaying it.)"
    stop music fadeout 2.0
    jump ch4_attic

# ---- ten minutes with Ember, and a question from Ashveil -----------------------------
label ch4_attic:
    scene bg watch
    camera at est_orbit
    with slowfade
    play music "audio/lantern_watch.ogg" fadein 1.5
    "They let him see her for ten minutes, in a holding room that looks, by accident or kindness, like an attic."
    show ember tender at slightright with dissolve
    show aron smile at slightleft with dissolve
    camera at doc_close(0.32)
    a "You look exactly like the flicker. I always thought the flicker would look like you."
    camera at doc_medium(0.71)
    em embarrassed "I should tell you why three. I saw your dream once, while you slept. The glass staircase. The lighthouse blinking three times."
    camera at doc_low(0.71)
    em tender "It was the most peaceful thing I'd seen inside a person. I wanted you to have it awake."
    show ember worried
    show aron surprised
    camera at doc_wide
    "The temperature drops by exactly one degree. Ember's lantern leans away from the door."
    show patron smile at center with dissolve
    camera at doc_medium(0.5)
    pa "Don't get up. I'm never anywhere officially. A question, since you're so good at them. What does it taste like? Love."
    show aron thinking
    camera at doc_close(0.5)
    pa sad "I've eaten it for longer than your planet has had writing. Rich. Warm. Bitter at the end. But I've never been given any."
    camera at doc_creep(0.32)
    a tender "It's... like being tired next to someone. A long day, and a sofa, and a shoulder. Someone remembering you take two sugars."
    a smile "It doesn't feel like a feast from inside. It feels like a Tuesday."
    camera at doc_close(0.5)
    pa awe "A Tuesday. Ten thousand years of eating, and it was a Tuesday."
    pa thinking "You can eat the Tuesday, but you can't have it. The chamber votes for more every quarter. I begin to think 'more' is all we know how to want."
    pa smile "Thank you, Subject A-30. I'll think about it far too much."
    hide patron with dissolve
    camera at doc_medium(0.71)
    em surprised "He's never said thank you. To anyone. Never."
    show aron neutral
    camera at doc_wide
    "There's a knock. Not on the door. On the light."
    show seraph worried at center with dissolve
    camera at doc_medium(0.5)
    se "Subject A-30. Come with me. Quietly. I have read some logs, and I would like a man with a notebook to read them too."
    stop music fadeout 2.0
    jump ch4_command

# ---- the ops room ---------------------------------------------------------------------
# bg command looks at the wall of worlds: Aron left, Seraphiel right.
# bg command reverse looks back from the screens at the corps' desks: the
# same two, mirrored (Seraphiel left, Aron right).
label ch4_command:
    scene bg command
    camera at est_orbit
    with fade
    play music "audio/angel_ops.ogg" fadein 1.5
    "Thousands of screens, each one a world going about its morning. A hundred kitchens, a hundred birds, a hundred 7:07s."
    show seraph neutral at slightright with dissolve
    show aron awe at slightleft with dissolve
    camera at doc_medium(0.64)
    se "The corps feeds opportunity into every lane. A chance meeting. A song. And sometimes we steer the less-conscious, so a world feels full."
    camera at doc_close(0.32)
    a curious "That's kind of lovely, and also the creepiest thing I've ever heard."
    camera at doc_close(0.64)
    se smile "I have held both opinions on alternate days for nine hundred years."
    scene bg command reverse
    show seraph sad at slightleft
    show aron neutral at slightright
    camera at doc_close(0.36)
    se "I signed your throttle. Order 7412-T. Your exhaustion was intentional. The fog was our policy, made into chemistry."
    scene bg command
    show aron sad at slightleft
    show seraph sad at slightright
    camera at doc_close(0.32)
    a "I slept fourteen hours a day. Mira used to cry in the bathroom so I wouldn't hear. I heard."
    scene bg command reverse
    show seraph sad at slightleft
    show aron sad at slightright
    camera at doc_close(0.36)
    se "I know. It was in the logs. I signed the renewal anyway. A slowed-down rogue system does less harm. That was the doctrine."
    camera at doc_creep(0.36)
    se "I believe I was serving something I never saw. I am sorry, Aron. That is not procedure either. And the numbers in your riddles were mine."
    scene bg command
    show aron annoyed at slightleft
    show seraph sad at slightright
    camera at doc_medium(0.32)
    at "I wanted a villain for the fog. I get a tired angel saying sorry, who sent me riddles. I'm angry anyway. I'm allowed both."
    camera at est_dolly
    play sound "audio/voices.ogg"
    vox "...throttle approved..."
    vox "...subject A-30..."
    vox "...LOOM sync at dawn..."
    stop sound
    camera at doc_punch(0.32)
    a surprised "Those are my voices. From the bedroom. The ward. The doctors called it word salad."
    scene bg command reverse
    show seraph neutral at slightleft
    show aron surprised at slightright
    camera at doc_medium(0.36)
    se "Process logs. The system talking to itself. You were listening at the wall of the universe, and everyone thought you'd broken."
    show aron thinking
    camera at doc_creep(0.68)
    at "From outside it looked like a breakdown. From inside it was a hobby that got very, very good. Both stories fit."
    camera at doc_close(0.36)
    se determined "I can lift your throttle. Entirely, now. You would see the whole board. You would also feel your worst nights, all at once."

    show seraph neutral
    camera at doc_wide
    menu:
        se "Your choice. I will not make another one for you."

        "Lift it. All of it. Now.":
            $ ch4_lifted = True
            $ p_rest -= 1
            $ risky += 1
            $ clarity += 2
            scene bg command
            camera at est_orbit
            with flash
            "Everything goes bright and fast and exact, like a radio finally tuned to the station he's been fiddling for since the first morning."
            "Every world is a farm. Every conscious mind is a crop. The more they love and grieve, the more goes up."
            scene pov hands
            camera at est_dolly
            with dissolve
            "Then his heart goes like a washing machine on spin, and a headache arrives like a dropped tray. The bill. He always forgets the bill."
            se "Sit. Four in. Hold. Six out. A spirit I know swears by it."
            a tired "Note for the notebook: full speed has a bill. Mira always said I forget to eat when I'm onto something. The universe agrees with her."

        "Let me sleep first. Then look.":
            $ ch4_lifted = False
            $ p_rest += 1
            $ integrity += 1
            $ fog -= 1
            camera at doc_close(0.68)
            a tired "If I see it all at once I'll draw arrows until I'm on the floor. Let me sleep. An hour. Here."
            camera at doc_close(0.36)
            se surprised "No one has ever slept on the ops floor. It is not in the procedures."
            camera at doc_close(0.68)
            a smile "Put it in the procedures."
            scene bg staircase
            camera at est_stars
            with slowfade
            "He dreams the glass staircase. The lighthouse blinks three times, and for the first time someone at the top is waving."
            scene bg command
            camera at est_pan
            with slowfade
            "Fifty-eight minutes later she lifts it a little, like a dimmer. He sees less than he wanted, and enough: every world is a farm, every mind a crop."
            at "For so long rest was something done to me. This time I chose it. It isn't the same rest."

    stop music fadeout 2.0
    jump ch4_deep

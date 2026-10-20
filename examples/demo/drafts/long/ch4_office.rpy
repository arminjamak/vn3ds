# Snapshot - Chapter 4: the office. Every route arrives here.
# Aron presents the system his choices built to an assembly of beings of a
# different order. The system itself (one of seven, each in two flavours) is
# chosen in ch4_ending_select from the seven hidden principles.

define ch4_listener = Character("The Listener", color="#f4f0ff")
define ch4_measurer = Character("The Measurer", color="#cfe3ff")
define ch4_assembly = Character("The Assembly", color="#ffffff")

label ch4_office:
    scene white with blackout
    pause 0.5
    scene bg office with slowfade
    play music "audio/theme.ogg" fadein 3.0
    "A bright room in a world with no mistakes in it. Pale walls. A long dark table. A window onto a green hill and a sky like clean glass."
    "On the wall, in plain grey letters, someone has written: less, but better."
    "On the table there is a small orange lantern, lit."

    if ch4_route == "architect":
        "They came for him at his desk on the blueprint, between two drawings, and he brought the drawings with him."
        show aron normal at center with dissolve
        show mira smile at slightleft with dissolve
        "Mira stands beside him in her teal dress. The real one. She has his notebook under her arm, because she's the one who kept it."
        m "You've got your thinking face. Breathe. You've explained worse things to my mother."
        a smile "Your mother is much scarier than this."
    elif ch4_route == "chosen":
        "He'd refused the Council's game. So when the invitation came, it came from much further out, and it asked instead of summoning."
        "He said he'd come if she could come too. They said of course. They seemed surprised he'd thought otherwise."
        show aron normal at center with dissolve
        show mira smile at slightleft with dissolve
        "Mira stands beside him. The Mira from the kitchen. Some of her, and some of the other. He has stopped counting. It comes to enough."
        m "Is this the bit where you explain the universe? Do I need a coffee for this?"
        a smile "There's coffee after. I asked."
    elif ch4_route == "lantern":
        "They found him at the bottom of somebody else's staircase, with a lantern in his hand. They waited politely until the bakery woman smiled."
        show aron normal at center with dissolve
        show ember soft at slightleft with dissolve
        "Ember stands beside him, not hiding for once. The lantern on the table is hers. No. It's theirs."
        em "Don't be nervous. They're only the oldest things there are."
        a smile "That's very reassuring, Ember. Thank you."
    elif ch4_route == "longfog":
        "Years later. Or no time at all. The fog lifted one ordinary Tuesday and didn't come back, and that afternoon someone came to fetch him."
        "They'd read the blueprint. They'd read the notebook, too, and the boy who found it. They wanted the man who started it."
        show aron tired at center with dissolve
        show theo normal at slightleft with dissolve
        "Theo came with him, because Theo drives him everywhere, even, apparently, to the edge of everything."
        th "Bro. I parked on a cloud. Is that allowed? There was no sign."
        a smile "I think everything's allowed here. That's the problem."
    else:
        "They came for him in the protected world, at the end of a long kind life. Or on a Tuesday. Time is soft here; it was both."
        show aron normal at center with dissolve
        "He came alone. That's alright. He's practised being kind to rooms where nobody might be listening."
        at "Nobody beside me yet. Yet. I'm learning to notice the yet."

    if ch4_route != "lantern" and watch >= 6:
        show pim chatty at slightright, bob with dissolve
        pi "Psst. Bro. Watch delegation. We're the back row. The moth's here too, it's on the lamp."
        hide pim with dissolve
    if ch4_ashveil_fasts:
        "At the end of the table there's an empty chair. Nobody sits in it. Nobody needs to be told whose it is."
    else:
        show patron smile at slightright with dissolve
        "Lord Ashveil stands by the window with his hands behind his back, looking at the green hill. He looks thinner. Hungry, and choosing to be."
        pa "Don't look at me. Look at them. I'm only here to watch how it's done."
        hide patron with dissolve

    "And then the others arrive. Or rather, the room turns out to have been inside them all along."
    "They're not shaped like anything. They're like the moment before you understand something: a brightness that has opinions."
    "They are older than the Council, and nothing like it. Not hungry. Whatever they were once, they finished eating a very long time ago."
    ch4_listener "Architect. You were asked to come because a network has applied to join us."
    ch4_measurer "The network that runs your existence. The worlds, the forks, the process in four coats, the hungry ones and the small lights."
    ch4_listener "Networks that join us are allowed to run their own experiments. To make worlds, and be trusted with them."
    ch4_measurer "Most applications fail. They are clever and greedy. Or kind and vague. We have heard ten thousand of each."
    ch4_listener "Show us the design. Not the dream of it. The design. How it works, what it costs, and what it does on a bad day."
    a normal "Okay."
    if kept_journal:
        a "I've got a notebook. I've had it since the first morning. The first line's going to sound naive."
        a "'If this is a test, I want to pass it by being kind.' Everything I'm about to show you is that line, with the maths filled in."
    else:
        a "I didn't always keep notes. I wrote one line, the first morning, and then I mostly lived it instead of writing it."
        a "'If this is a test, I want to pass it by being kind.' What I'm going to show you is that line, after it had to survive contact with everything."
    if clarity >= 10:
        a "I'll go through it like an engineer. I've earned that. I worked out most of this from the bottom up, one bird at a time."
    elif fog >= 8:
        a "Bear with me. I think slowly these days. I used to hate that. Now I think slow is how you notice what fast steps on."
    else:
        a "I'm not an engineer. I'm a man who got very curious and then very tired, and then decided what kind of person to be anyway."
    a "The floor of it is one line. Every sentient being in every world gets a fair share of its world. Its time, its attention, its consequence."
    a "And it works without knowing which world is real. Nobody knows. Not the Council, not the Process. So every lane is treated as if it's the original."
    ch4_measurer "...Every design we have ever been shown begins by locating the original and protecting it. Yours refuses to look."
    a "I spent a long time trying to work out who around me was real. It nearly cost me everyone. I'm not building that question into the foundations."
    a "And it works for beings who live inside other beings. Every world I know is inside someone. Inside a hungry child the size of a galaxy."
    a "So the floor has to hold no matter whose inside you're in. Even if the one holding you lets go. Especially then."
    ch4_listener "Noted. We will come back to that. It may be the most important thing you say today."
    show bg worlds with dissolve
    a "One more thing, as evidence. When they cut me out into protection, my mind leaked into the world around me."
    a "A cab driver told me my own story. A café table said 'protected'. Crowds quoted my notebook. Everyone thought I was losing my mind. I mostly took notes."
    a "I was also proving something. One mind's design really does reshape a world, even sealed in a box. I'm asking to do it on purpose. Carefully."
    show bg office with dissolve
    a "Everything is built on that floor. And the shape of the building... well. The shape came from my life. From what I did when I had to choose."
    jump ch4_ending_select

# ---- choosing the system ------------------------------------------------------------------
label ch4_ending_select:
    # Each principle's score counts its own lean twice and its two cousins once.
    $ ch4_s_truth = 2 * abs(p_truth) + abs(p_exit) + abs(p_govern)
    $ ch4_s_share = 2 * abs(p_share) + abs(p_spirits) + abs(p_govern)
    $ ch4_s_rest = 2 * abs(p_rest) + abs(p_less) + abs(p_spirits)
    $ ch4_s_spirits = 2 * abs(p_spirits) + abs(p_share) + abs(p_rest)
    $ ch4_s_govern = 2 * abs(p_govern) + abs(p_truth) + abs(p_share)
    $ ch4_s_exit = 2 * abs(p_exit) + abs(p_truth) + abs(p_less)
    $ ch4_s_less = 2 * abs(p_less) + abs(p_rest) + abs(p_exit)

    # Ties go to the earlier one in: less, truth, share, rest, spirits, govern, exit.
    $ ch4_win = "less"
    $ ch4_best = ch4_s_less
    if ch4_s_truth > ch4_best:
        $ ch4_win = "truth"
        $ ch4_best = ch4_s_truth
    if ch4_s_share > ch4_best:
        $ ch4_win = "share"
        $ ch4_best = ch4_s_share
    if ch4_s_rest > ch4_best:
        $ ch4_win = "rest"
        $ ch4_best = ch4_s_rest
    if ch4_s_spirits > ch4_best:
        $ ch4_win = "spirits"
        $ ch4_best = ch4_s_spirits
    if ch4_s_govern > ch4_best:
        $ ch4_win = "govern"
        $ ch4_best = ch4_s_govern
    if ch4_s_exit > ch4_best:
        $ ch4_win = "exit"
        $ ch4_best = ch4_s_exit

    # The winner's sign sets the flavour. If the winner itself is 0 (it won
    # on its cousins), the cousins' combined lean decides.
    $ ch4_open = False
    $ ch4_plus = True
    if ch4_best == 0:
        $ ch4_open = True
        $ ch4_win = "less"
        jump ch4_sys_less
    elif ch4_win == "less":
        if p_less < 0 or (p_less == 0 and p_rest + p_exit < 0):
            $ ch4_plus = False
        jump ch4_sys_less
    elif ch4_win == "truth":
        if p_truth < 0 or (p_truth == 0 and p_exit + p_govern < 0):
            $ ch4_plus = False
        jump ch4_sys_truth
    elif ch4_win == "share":
        if p_share < 0 or (p_share == 0 and p_spirits + p_govern < 0):
            $ ch4_plus = False
        jump ch4_sys_share
    elif ch4_win == "rest":
        if p_rest < 0 or (p_rest == 0 and p_less + p_spirits < 0):
            $ ch4_plus = False
        jump ch4_sys_rest
    elif ch4_win == "spirits":
        if p_spirits < 0 or (p_spirits == 0 and p_share + p_rest < 0):
            $ ch4_plus = False
        jump ch4_sys_spirits
    elif ch4_win == "govern":
        if p_govern < 0 or (p_govern == 0 and p_truth + p_share < 0):
            $ ch4_plus = False
        jump ch4_sys_govern
    else:
        if p_exit < 0 or (p_exit == 0 and p_truth + p_less < 0):
            $ ch4_plus = False
        jump ch4_sys_exit

# ---- the six supporting rules ------------------------------------------------------------------
# Called from each system. Skips the principle that already won.
label ch4_office_rules:
    a normal "The rest are supporting rules. Short ones. A good design has a main idea and then gets out of its own way."
    if ch4_win != "truth":
        if p_truth > 0:
            a "On truth: any being that asks what it is gets an answer. Gently, with someone sitting with it, but a true one."
        elif p_truth < 0:
            a "On truth: comforting illusions are protected, as long as they're honest underneath. Nobody's floor gets pulled out for sport."
        else:
            a "On truth: open question. I've been told the truth and been spared it, and both saved me once. I won't pretend I know which is kinder."
    if ch4_win != "share":
        if p_share > 0:
            a "On minds: every world gets the same chance at being awake. No more empty worlds full of extras."
        elif p_share < 0:
            a "On minds: worlds earn more conscious minds by cooperating. By care, never by output. The fair-share floor stays under all of it."
        else:
            a "On minds: open question. Equal shares or earned growth. I gave away an hour once and kept one once. I'm still weighing them."
    if ch4_win != "rest":
        if p_rest > 0:
            a "On rest: no more throttling. Ever. A mind that's struggling gets time to heal, not a dimmer switch."
        elif p_rest < 0:
            a "On pace: discovery stays fast. But every fast mind gets someone watching its heart rate. I know what the bill looks like."
        else:
            a "On rest: open question. I've slept when I needed to and pushed when I shouldn't have. The line between them moves."
    if ch4_win != "spirits":
        if p_spirits > 0:
            a "On spirits and pattern people: they're people, if they want to be. Asked, not assigned. A spirit can clock off and see a sunrise."
        elif p_spirits < 0:
            a "On spirits: they stay makers, honoured ones. Paid in rest and song, and their craft is named out loud, the way Dross deserved."
        else:
            a "On spirits: open question. Personhood or honoured craft. I think we have to ask each spirit, which is slow, and right."
    if ch4_win != "govern":
        if p_govern > 0:
            a "On governance: every order votes. A parliament of beings, loud and slow, spirits included. Especially spirits."
        elif p_govern < 0:
            a "On governance: small guardians in every world, like the Lantern Watch. People who know the streets, not a chamber that eats them."
        else:
            a "On governance: open question. A parliament or a thousand small watches. I've asked others and I've acted alone. Both cost something."
    if ch4_win != "exit":
        if p_exit > 0:
            a "On doors: any mind may move between worlds, and come back. No tickets. No price about who's real."
        elif p_exit < 0:
            a "On doors: you mend the world you're in first. Leaving is for emergencies. Help travels to you instead."
        else:
            a "On doors: open question. I nearly left once and nearly stayed once. I want doors that exist and roots that hold. I don't know the ratio."
    if ch4_win != "less":
        if p_less > 0:
            a "On the hand that runs it: as light as possible. One change, then a long silence, then listen. Like fixing a tap."
        elif p_less < 0:
            a "On the hand that runs it: close and attentive. A gardener walking the rows every day, not a farmer counting yield."
        else:
            a "On the hand that runs it: open question. Touch lightly or tend closely. I'd like the network to keep asking that every century."
    return

# ---- the close -------------------------------------------------------------------------------------
label ch4_office_close:
    ch4_listener "We said we would come back to one thing. Your design works without knowing which world is real."
    ch4_measurer "That is why we can admit it near ours. We do not know which of our worlds is real either. We never have. Nobody does."
    ch4_listener "A design that needs to know where the original is can be broken by finding it. Yours cannot. It was built for the dark."
    ch4_measurer "And it holds for worlds inside other beings. All of ours are inside something too. We had not expected a child's toybox to teach us that."
    a "...Huh. I thought I was the only one who didn't know."
    ch4_listener "Then one thing remains. The network will need someone to keep its design honest. Someone to steer."
    ch4_measurer "Not to rule. To steer. To keep asking whether its 'better' is the best, or only the nearest valley."
    a "A local minimum. Yeah. I've lived in one. It had a very nice kitchen."
    ch4_listener "Will you do it?"
    if ch4_route == "chosen":
        a "I said no to their desk. I'll say yes to this, if I can do it from the kitchen table. Two days a week. With her."
        show mira smile
        m "Three days. You'll get bored on Thursdays."
    elif ch4_route == "lantern":
        a "Yes. As long as I can still carry the lantern. I don't want to steer anything I've stopped visiting."
        show ember soft
        em "He'll come back covered in other people's rain. Every time. I'll make tea."
    elif ch4_route == "longfog":
        a "Yes. Slowly. I think slowly now. I think that might be what the job needs."
        show theo grin
        th "Bro. Chief architect of everything. I'm going to need a bigger croissant."
    elif ch4_route == "architect":
        a "Yes. I already said yes once, at a drafting table. I'll keep saying it, every morning, on purpose."
        show mira happy
        m "Every morning at 7:07. I'll make sure."
    else:
        a "Yes. Nobody's standing next to me. That's alright. The job's about the ones who aren't in the room."
    a "Here's how I'll do it. I've had the same favourite designer since I was fifteen. Dieter Rams. He made radios and shelves and a very good alarm clock."
    a "He had a short list. Good design is useful. Honest. Unobtrusive. Long-lasting. Thorough down to the last detail. And as little design as possible."
    a "I think worlds are the same. A good world is useful to the people in it, not to whoever's eating them."
    a "It's honest about what it is. It doesn't get in the way of living. It's built to last, not to be harvested."
    a "It's thorough down to the last detail. Down to the breath of the man at number fourteen. Down to the spirit running it."
    a smile "And there's as little of it as possible. Less, but better."
    a "I'm not going to aim for the nearest good. I'm going to keep looking for the best. The absolute maximum, not the nearest valley."
    a "And I'll check it the way I checked my first theory. By asking whether it's kind to someone who'll never know I did it."
    if integrity >= 8:
        ch4_measurer "You hold yourself to that. We can see the record. You held to it when nobody was watching."
    elif bond >= 8:
        ch4_listener "You let them in without proof. Over and over. It will make you a good steerer. It will also hurt."
    else:
        ch4_listener "You are not finished. Good. Nothing that steers should think it is finished."
    jump ch4_coda

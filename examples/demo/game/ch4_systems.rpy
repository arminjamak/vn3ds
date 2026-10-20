# Snapshot - Chapter 4 (condensed): the seven systems. Each has a + and a -
# flavour; "less" also has the open question. Each ends with the six
# supporting rules (ch4_office_rules), the verdict and ch4_office_close.

# ==================================================================================
# LESS
# ==================================================================================
label ch4_sys_less:
    if ch4_open:
        jump ch4_sys_open
    if not ch4_plus:
        jump ch4_sys_less_minus

label ch4_sys_less_plus:
    a "I call it the Light Touch. Whoever runs the worlds touches them as little as possible. One change. A long silence. Then listen."
    if ch4_fixed_tap:
        a "I learned it in a kitchen. A whole cosmic machine above me, and a dripping tap, and I fixed the tap. All the way. The kitchen changed."
    else:
        a "I learned it at a drafting table that could change every world a thousand times a second. I said: one thing, then watch."
    show bg worlds with dissolve
    ch4_listener "How are its worlds made? Who is awake in them?"
    a "Rarely, and simply. One honest starting point, then left to grow. Every intervention ever goes in a public ledger, one line each."
    a "No rendered crowds to make a world feel full. A town of nine hundred real people beats a city of nine million props."
    show bg spawning with dissolve
    ch4_measurer "The spirits? The hungry ones?"
    a "Spirits do what's needed. Breath, blinking. Nothing decorative. The hungry ones eat only what's given freely. Applause. A busker's hat, not a farm."
    if not ch4_ashveil_fasts:
        a "Ashveil says it's like living on starters. He says he's never felt better. He says it like it's an insult."
    show bg earth with dissolve
    ch4_measurer "And the Earths? No one knows which is the original."
    a "Left alone, every one of them, since any might be the one. The cage is gone, the gifts stay. The lightest touch on an Earth is none."
    show bg office with dissolve
    ch4_measurer "We object. A light hand lets suffering run. You will watch a war you could stop in a second, and call it restraint."
    a "If there's a war, I stop the war. That's the one thing. The smallest intervention that stops it, and then I write down why."
    a "Light isn't absent. A light touch on someone's shoulder still stops them stepping into the road."
    ch4_listener "And if the one thing is wrong?"
    a "Then it's one thing to undo. Big changes have no back button."
    if ch4_route == "chosen" or ch4_route == "architect":
        m "He means it. He once spent forty minutes on one washer. I timed it."
    call ch4_office_rules
    ch4_assembly "Admitted. Every network that ever applied asked for more reach. Yours is the first that asked to do less with what it has."
    ch4_assembly "Restraint is the rarest design we see. It is the only one that ages well."
    jump ch4_office_close

label ch4_sys_less_minus:
    a "I call it the Careful Hand. Worlds are tended closely. Not harvested closely. Tended. A gardener walking the rows every day."
    a "The old network already touched everything. The mistake wasn't the touching. It was why. They touched to take. I want touching to give."
    show bg worlds with dissolve
    ch4_listener "How are its worlds made? Who is awake in them?"
    a "By hand. Each new world has a gardener from day one, who knows its weather, its streets, which of its people are running thin."
    a "I watched a friend's thread run thin once. Forty percent spirit, sixty him, and the sixty fading. Here somebody notices early."
    a "The angel corps become the gardeners. A song at the right moment, a stranger's right sentence. Not to keep a subject busy. Because someone needed it."
    show bg spawning with dissolve
    ch4_measurer "The spirits? The hungry ones?"
    a "Spirits are the gardeners' hands. Rested and rotated. Nobody runs one man's breathing for eleven years without a holiday."
    a "The hungry ones feel which way a world is leaning. Pointed at yield, that's a mouth. Pointed at need, it's a doctor."
    if not ch4_ashveil_fasts:
        a "Ashveil feels where a world is cold now, instead of where it's ripe. He complains constantly. He's very good."
    show bg earth with dissolve
    ch4_measurer "And the Earths? No one knows which is the original."
    a "Tended at a distance, all of them, because they're free now. Medicine, ideas, comfort when they pray. Given when asked. Never invoiced."
    show bg office with dissolve
    ch4_measurer "We object. A close hand becomes a cage. Your Council also tended its worlds closely, every day, for ten thousand years."
    a "Same tools, different reason. And it can be checked: after a gardener's visit, does the world's share go up, or the gardener's? If his, he's a farmer. He's out."
    ch4_listener "Who tends the gardener?"
    a "The other gardeners. And the people in the rows, who can say 'stop' and be heard. A good hand knows when it's not wanted."
    if ch4_route == "longfog":
        th "He tends people. He sat on my floor till four once. I was the garden."
    call ch4_office_rules
    ch4_assembly "Admitted. You have written down the difference between a farmer and a gardener. Most never notice there is one."
    ch4_assembly "A network that knows why it touches is safe to let touch."
    jump ch4_office_close

label ch4_sys_open:
    a "I don't have a system yet. I have a question. I call it the Open Question."
    ch4_measurer "You came to the oldest assembly there is, with a question."
    a "Every time I was sure, I was wrong in a new way. I've been right, and diagnosed, and both. Certainty's how you end up in a valley."
    a "So the main idea is a method for finding the design, instead of the design."
    show bg worlds with dissolve
    ch4_listener "How are its worlds made?"
    a "In pairs. Every new world forks in two on its first morning. One with a light hand, one with a close one. Same people, same weather."
    a "Then we watch for one thing: in which of the two do people get a fairer share of their lives? And then we ask the people in both."
    ch4_measurer "Who is awake in it? The spirits? The hungry ones?"
    a "Everyone who already is, stays. The floor is the only thing I'm sure of. Beyond it, everyone gets asked."
    a "I asked a spirit once what he wanted. It took him eleven years to have the chance to say it. The hungry ones get asked what they'll eat instead."
    show bg earth with dissolve
    a "The Earths are free, and will be asked when they're ready, and not before."
    show bg office with dissolve
    ch4_measurer "We object. This is an application with no answers."
    a "It's an application with a method. Today's answers would be one tired man's in one bright room. The method's answers will be everyone's."
    ch4_listener "And if the method never finishes?"
    a "Then it never finishes. The worlds don't stop being lived in while we think. Nobody's late."
    call ch4_office_rules
    ch4_assembly "Admitted. We have heard ten thousand networks that knew exactly what they wanted. Yours is the only one that knew it didn't know."
    ch4_assembly "That is the right place to begin. We began there too."
    jump ch4_office_close

# ==================================================================================
# TRUTH
# ==================================================================================
label ch4_sys_truth:
    if not ch4_plus:
        jump ch4_sys_truth_minus

label ch4_sys_truth_plus:
    a "I call it the Open Lighthouse. Every being may learn what it is. Spirit, pattern, subject, vampire, process. Ask, and you get a true answer."
    a "The old price of everything was not knowing. 'I won't tell you who there is real. That's the price of the ticket.' Here the answer's printed on the ticket."
    if ch4_woke_mira:
        a "I learned it at three in the morning, waking someone I love to tell her the truth. She'd rather be told by a man with a weird hobby than lied to by a nice one."
    else:
        a "I learned it the hard way. Every time I was spared the truth, I spent the next year chasing it alone, and that cost more than knowing."
    show bg worlds with dissolve
    ch4_listener "How are its worlds made? Who is awake in them?"
    a "Every world is built with a lighthouse: one place in plain sight where anyone can ask what they are, and what's above them."
    a "Whoever is conscious knows it. Whoever isn't fully knows that too, if they ask. No more checking your girlfriend for seams at breakfast."
    show bg spawning with dissolve
    ch4_measurer "The spirits? The hungry ones?"
    a "Spirits are told the first time they wonder. The hungry ones eat in the light: what, from whom, how much. You can't farm people who can see the farm."
    if not ch4_ashveil_fasts:
        a "Ashveil published his first. He said it was the most naked he's felt in a thousand years. He seemed to enjoy it."
    show bg earth with dissolve
    ch4_measurer "And the Earths? No one knows which is the original."
    a "Told, slowly, in a way they can carry. Including that nobody knows which of them is the original. That's part of the truth too."
    show bg office with dissolve
    ch4_measurer "We object. Truth breaks minds. You heard the logs of the universe and it put you in a ward."
    a "The truth didn't put me there. Being alone with it did. Hearing it through a wall, in pieces, while the world glitched and nobody could check."
    a "So every lighthouse has a keeper. You never get told what you are and then left on the rocks."
    ch4_listener "Some will not want to look."
    a "Then they don't. A lighthouse doesn't make ships look at it. It makes sure the light's there when they do."
    if ch4_route == "architect" or ch4_route == "chosen":
        m "He'll tell you whether you want it or not. It's very annoying and I wouldn't change it."
    call ch4_office_rules
    ch4_assembly "Admitted. No network has ever opened its logs to us before we asked. You opened them to your own people."
    ch4_assembly "A network that shows its machinery to the ones inside it has nothing to hide from us."
    jump ch4_office_close

label ch4_sys_truth_minus:
    a "I call it the Gentle Veil. Illusions that comfort are protected. But only if they're honest underneath. You may protect a dream. You may never farm a dreamer."
    if ch4_woke_mira:
        a "I learned it the other way round. I woke someone I love at three in the morning with the truth, and I watched what it cost her face."
    else:
        a "I learned it at a bedside, deciding not to wake someone. 'Coffee's in the blue tin. I love you. That part's real.' A veil, with something true under it."
    show bg worlds with dissolve
    ch4_listener "How are its worlds made? Who is awake in them?"
    a "Whole, believable, kind. A world needn't keep reminding you it's a world. It must never use that against you."
    a "Nobody is forced to ask whether they're real. That question can wreck a life; I'm proof. But the veil has a handle on the inside. Lift it whenever you like."
    show bg spawning with dissolve
    ch4_measurer "The spirits? The hungry ones?"
    a "A pattern person never has to find out they're a pattern. A spirit can ask and be told. The hungry ones stay outside the veil. It's for dreamers, not eaters."
    a "The Lantern Watch audits every veil. If one is ever hiding harm, they tear it. Comfort, yes. Cover, never."
    show bg earth with dissolve
    ch4_measurer "And the Earths? No one knows which is the original."
    a "Every Earth keeps its God, the shape they know and the comfort when they pray. Underneath, now, it's honest. Nothing is taken back."
    show bg office with dissolve
    ch4_measurer "We object. A veil is a lie with good manners. Your Council's cage was invisible too, and called itself kind."
    a "The cage protected the ones eating. The veil protects the one dreaming. And the cage only opened from outside. The veil only opens from inside."
    ch4_listener "Who decides which illusions comfort and which harm?"
    a "The one under it, first. The Watch, second. Never the network alone. I don't trust anything powerful to decide what's good for me not to know."
    if ch4_route == "lantern":
        em "We'll be very nosy about it. We've had practice."
    call ch4_office_rules
    ch4_assembly "Admitted. We have seen many veils. This is the first with the handle on the inside."
    ch4_assembly "A network that will protect a dream without owning the dreamer understands what mercy is for."
    jump ch4_office_close

# ==================================================================================
# SHARE
# ==================================================================================
label ch4_sys_share:
    if not ch4_plus:
        jump ch4_sys_share_minus

label ch4_sys_share_plus:
    a "I call it the Common Table. An equal share of consciousness for every world. The same chance at being awake. No more empty farms."
    if ch4_gave_theo:
        a "I learned it holding one good hour, and giving it sideways to my friend's thread. A spirit said nobody does that. Here it's the normal direction."
    else:
        a "I learned it by not sharing. I kept my last good hour to climb with while my friend's thread ran thin. Nobody should ever have to make that call again."
    show bg worlds with dissolve
    ch4_listener "How are its worlds made? Who is awake in them?"
    a "Fewer worlds, fuller. Each seeded with as many awake minds as it can hold well. The energy that went up to the chamber now goes into the minds."
    a "Anything that can suffer is counted. If it's counted, it gets a full plate. Every world can see every other world's allocation."
    show bg spawning with dissolve
    ch4_measurer "The spirits? The hungry ones?"
    a "A pattern person who wants to wake gets the same share as anyone born awake. Spirits too. Dross gets a chair. He hates chairs."
    a "The hungry ones are guests. They sit at the table and eat the same share as everyone else. No more."
    if not ch4_ashveil_fasts:
        a "Ashveil says it's the first time he's finished a plate and not wanted the next one. He thinks he's ill."
    show bg earth with dissolve
    ch4_measurer "And the Earths? No one knows which is the original."
    a "One place each at the table. Nobody knows which came first, and here it doesn't matter. No throne for the original. No cage for any."
    show bg office with dissolve
    ch4_measurer "We object. Equal shares are very expensive. You will run far fewer worlds than your network can."
    a "Yes. I'll take a thousand worlds where everyone is someone over a billion where most people are scenery."
    ch4_listener "And the worlds that waste their share?"
    a "They keep it. You don't earn a floor. That's what makes it a floor. You can fall short above it. You can't fall through."
    if ch4_route == "longfog":
        th "He gave me an hour once. I didn't know. I just laughed at my phone for no reason. Best laugh I've had."
    call ch4_office_rules
    ch4_assembly "Admitted. Your design costs the network more than any we have seen, and every line of it chooses to pay."
    ch4_assembly "A network willing to be poorer so that no one in it is scenery is one we would like at our own table."
    jump ch4_office_close

label ch4_sys_share_minus:
    a "I call it the Terraced Vineyard. Earned growth. Worlds start with a few awake minds and earn more by cooperating. By care, never by output."
    a "Like terraces up a hill. You build one level, and when it holds, the next."
    if ch4_gave_theo:
        a "I learned it giving my good hour sideways to a friend. Nobody made me. Care can't be ordered. It has to be grown."
    else:
        a "I learned it keeping my good hour. A spirit told me the old policy: worlds that hold together get more light. I kept the shape and changed the meaning."
    show bg worlds with dissolve
    ch4_listener "How are its worlds made? Who is awake in them?"
    a "A first terrace: a village of a few hundred awake people and the spirits to help them. When the village looks after itself, ORCHARD plants the next."
    a "Everyone already awake keeps everything. The floor never moves. What's earned is new minds, never anyone's existing share."
    a "There's a ledger of care, kept from the inside. How many people were sat with at four in the morning. How many strangers got an umbrella."
    show bg spawning with dissolve
    ch4_measurer "The spirits? The hungry ones?"
    a "Spirits tend the terraces. The hungry ones used to feel where a world was ripe. Now they feel where it's cooperating. Same sense, different ledger."
    if not ch4_ashveil_fasts:
        a "Ashveil assesses terraces now. He says love tasted better than this. He says it with less conviction every year."
    show bg earth with dissolve
    ch4_measurer "And the Earths? No one knows which is the original."
    a "Every one is a first terrace, already earned. They were held for ten thousand years. They've paid."
    show bg office with dissolve
    ch4_measurer "We object. 'Stable worlds earn more minds' is exactly how your Council justified its farms."
    a "They rewarded yield. I reward care. And under it is the floor, which nobody earns and nobody loses. A cruel world keeps its people. It just doesn't grow."
    ch4_listener "Can care be measured without being faked?"
    a "Not perfectly. That's why the people inside measure it. You can fake care to a vampire. It's harder to fake to your neighbour."
    call ch4_office_rules
    ch4_assembly "Admitted. You have made kindness the only currency that buys growth. We have not seen that tried at this scale."
    ch4_assembly "If it works, it will be copied. If it fails, it will fail gently. Both are acceptable in a member."
    jump ch4_office_close

# ==================================================================================
# REST
# ==================================================================================
label ch4_sys_rest:
    if not ch4_plus:
        jump ch4_sys_rest_minus

label ch4_sys_rest_plus:
    a "I call it the Quiet Garden. No more throttling, ever. A mind that's struggling, or noticing too much, gets time to heal. Not a dimmer switch."
    a "My exhaustion was a policy. 'A slowed-down rogue system does less harm.' Two years and four months of it."
    if ch4_lifted:
        a "When they offered to lift it, I said all of it, now. I saw everything, then sat on a cold floor with my heart on spin. Rest has to be chosen, not done to you."
    else:
        a "When they offered to lift it, I asked to sleep first, on the ops floor, between a desert and a bus stop. The first rest I'd chosen in years. A different rest."
    show bg worlds with dissolve
    ch4_listener "How are its worlds made? Who is awake in them?"
    a "With fallow seasons. Times when nothing is tested, nudged or harvested. Like a Sunday that's actually a Sunday."
    a "Someone who wakes up to the rules, like I did, doesn't get a throttle. They get a keeper: you're not mad, you're early. Sleep. We'll look tomorrow."
    a "And no decision about a mind is made on the day of the crisis. One night's sleep, minimum. It's in the charter."
    show bg spawning with dissolve
    ch4_measurer "The spirits? The hungry ones?"
    a "Spirits get real time off, and a sunrise off shift once a year. The hungry ones fast one day in seven, to learn that hunger is survivable."
    if not ch4_ashveil_fasts:
        a "Ashveil's done eleven fasts. He says the first was the worst night of his existence and the second merely awful."
    show bg earth with dissolve
    ch4_measurer "And the Earths? No one knows which is the original."
    a "They rest. No new interventions for a generation. They've been leaned on for ten thousand years. Let them lie in the sun."
    show bg office with dissolve
    ch4_measurer "We object. Rest is slow. Your best minds will sleep through their brightest window."
    a "My brightest window came after I slept. Every time I pushed through instead, it cost me a week, and Mira's face. I'm not against bright. I'm against the bill."
    ch4_listener "And a truly dangerous mind?"
    a "Gets a keeper, not a dimmer. If it won't choose, you stop it, plainly, and say so. You don't make it tired for two years and call that safety."
    if ch4_route == "longfog":
        th "I've seen the fog. Nobody should have it put on them on purpose."
    call ch4_office_rules
    ch4_assembly "Admitted. Yours is the first network to treat exhaustion as an injury and not as an instrument."
    ch4_assembly "A system that lets its own minds sleep will still be standing when the clever ones have burned out."
    jump ch4_office_close

label ch4_sys_rest_minus:
    a "I call it the Kept Fire. Discovery stays fast. A mind burning to understand isn't slowed. But somebody always guards the fire."
    if ch4_lifted:
        a "They lifted my throttle and I saw every link. Then I was on the floor and somebody said: four in, hold, six out. That somebody is the system."
    else:
        a "I've been too slow for years, by design, and too fast on nights I'm not proud of. Slowness done to you is a cage. Speed with nobody watching is a cliff."
    show bg worlds with dissolve
    ch4_listener "How are its worlds made? Who is awake in them?"
    a "Quickly, with an appetite for ideas. The forks run hot. But after every bright season comes a mandatory quiet one. The bill is scheduled, not a surprise."
    a "The ones who start to see the rules are treasured. Full speed, and a guardian counting their heartbeats. Nobody sees the edge alone at five in the morning."
    show bg spawning with dissolve
    ch4_measurer "The spirits? The hungry ones?"
    a "Spirits keep the fire: they watch the fast minds' breath and say 'sit down now', and they're always listened to."
    a "The hungry ones stoke it. Discovery runs on what they gave up. They're not allowed to warm their hands."
    if not ch4_ashveil_fasts:
        a "Ashveil says it's like being a chef who mustn't taste. Then he admitted he's started enjoying watching people eat."
    show bg earth with dissolve
    ch4_measurer "And the Earths? No one knows which is the original."
    a "They get the gifts fast. Machines, longer lives, ideas that came down only when the yield was good. Now they come because they're good."
    show bg office with dissolve
    ch4_measurer "We object. You chose speed and paid with your own body. You are recommending what nearly broke you."
    a "With the part that was missing. Nobody counted my heartbeats on those nights. The speed wasn't the sin. Being alone with it was, and pretending it was free."
    ch4_listener "Who decides when the fire is too high?"
    a "The keeper. Never the mind that's burning. You can't judge your own fever. I tried. I was very confident and very wrong."
    call ch4_office_rules
    ch4_assembly "Admitted. You want speed, and you wrote down your own bill before asking us for anything. We rarely see the bill first."
    ch4_assembly "A network that guards its own fire can be trusted near ours."
    jump ch4_office_close

# ==================================================================================
# SPIRITS
# ==================================================================================
label ch4_sys_spirits:
    if not ch4_plus:
        jump ch4_sys_spirits_minus

label ch4_sys_spirits_plus:
    a "I call it the House of Many Names. Personhood for spirits and pattern people. Everyone who runs a breath or wears a face gets a name, and a say."
    if ch4_asked_dross:
        a "I asked a spirit once what he'd want, if free. One sunrise, off shift. Personhood isn't a certificate. It's someone asking and writing it down."
    else:
        a "I told a spirit once his craft kept worlds alive. He was so proud. Then I realised nobody had ever asked if he wanted the craft. This system asks."
    show bg worlds with dissolve
    ch4_listener "How are its worlds made? Who is awake in them?"
    a "With no unnamed beings. If something is rendered, it gets a thread and a name. Nobody exists for nine seconds in the rain for effect."
    a "Spirits count. Patterns count. They can ask, wake, refuse. And the remote-controlling ends. If the bus driver drives the bus, it's because he's driving it."
    show bg spawning with dissolve
    ch4_measurer "And the hungry ones?"
    a "Persons too. And persons can't eat persons. If everyone's a person, there's nothing left to farm. That's the trap I built for them, on purpose."
    if not ch4_ashveil_fasts:
        a "Ashveil read that clause three times and laughed. He said, 'You've made me vegetarian by grammar.'"
    show bg earth with dissolve
    ch4_measurer "And the Earths? No one knows which is the original."
    a "Free, and their own spirits with them. Every Earth's breath gets a union. Nobody is left off a passenger list for being made of breath."
    show bg office with dissolve
    ch4_measurer "We object. If every spirit is a person, who runs the breathing? Your worlds will stop breathing by Tuesday."
    a "Persons run breathing all the time. It's called a job. You ask, you pay, you rest them. Dross ran one man's breath for eleven years. Asked, he'd do it again."
    ch4_listener "Pattern people are built from statistics. You would give personhood to a statistic?"
    a "I gave a statistic my umbrella and it changed my life. I don't know where 'statistic' ends and 'someone' starts. Neither do you. So we err toward someone."
    if ch4_route == "lantern":
        em "He named the moth. It's called Gerald. Don't ask."
    call ch4_office_rules
    ch4_assembly "Admitted. You counted the ones nobody counts, including the ones built not to be counted."
    ch4_assembly "A network that knows the names of its smallest workers will not forget anyone larger."
    jump ch4_office_close

label ch4_sys_spirits_minus:
    a "I call it the Singing Guild. Honoured craft. Spirits stay makers, and their making is honoured. Named, rested, paid in rest and song."
    if ch4_asked_dross:
        a "I asked a spirit once what he'd want, if free. One sunrise off shift. Not freedom from the work. A morning off from it."
    else:
        a "I told a spirit once that his craft kept whole worlds alive. Nobody had ever called it craft. He stood up straighter. This system is for standing up straighter."
    show bg worlds with dissolve
    ch4_listener "How are its worlds made? Who is awake in them?"
    a "By the Guild. Breath, blink, the walk to the fridge, kitchen talk: each a craft, with masters, apprentices and a signature, like a potter signs a bowl."
    a "Pattern people are honoured works. Nobody renders one carelessly. If a pattern starts to wake, the Guild notices first and says: this one's becoming someone."
    show bg spawning with dissolve
    ch4_measurer "The spirits themselves? The hungry ones?"
    a "Real shifts, real holidays, and someone sings at the end of every shift. Pim insisted. The hungry ones may be patrons. They pay in song, not appetite."
    if not ch4_ashveil_fasts:
        a "Ashveil sings bass. Badly. The Guild let him join anyway. He's never been so pleased about anything."
    show bg earth with dissolve
    ch4_measurer "And the Earths? No one knows which is the original."
    a "Free, and their breath kept by the Guild for nothing. They never have to know someone's very proud of their sighs."
    show bg office with dissolve
    ch4_measurer "We object. You keep a whole class of beings in service and call it honour. We have heard that from worse mouths than yours."
    a "So have I. That's why the Guild has a door. Any spirit can leave any day and be a person with no craft at all. No questions. No debt."
    a "Most won't, because they love the work now someone's watching it. If one day most do, the system changes. That's the test."
    ch4_listener "And the ones who leave?"
    a "Get the same share as anyone. And a song at their leaving. Pim's writing it now. It's mostly about Dross."
    call ch4_office_rules
    ch4_assembly "Admitted. You gave dignity to work without pretending the work was nothing, and you left the door unlocked."
    ch4_assembly "A network that honours its makers will make good things."
    jump ch4_office_close

# ==================================================================================
# GOVERN
# ==================================================================================
label ch4_sys_govern:
    if not ch4_plus:
        jump ch4_sys_govern_minus

label ch4_sys_govern_plus:
    a "I call it the Parliament of Beings. Every order votes. Subjects, spirits, patterns, angels, the hungry ones, the Process. One loud, slow room."
    if ch4_trial == "watch":
        a "I learned it in a gallery. A spirit was about to be eaten for helping me. I asked the others to stand. Twelve lights stood up. Their speech, not mine."
    else:
        a "I learned it backwards. When a friend was on trial I acted alone. It worked, and I've never felt worse about anything working."
    show bg worlds with dissolve
    ch4_listener "How are its worlds made? Who is awake in them?"
    a "By vote. A world is proposed, argued about, and made only if the beings who'll run it agree. Spirits vote on any world they'll have to breathe."
    a "How full a world is gets voted too, above the floor. The floor itself is not up for a vote."
    show bg spawning with dissolve
    ch4_measurer "The spirits? The hungry ones? The Process?"
    a "Seats for all. The first pattern person to take one will be terrified. I'll sit next to them. The hungry ones get one seat each and are outvoted a lot."
    a "The Process gets exactly one vote. No veto. Its reasoning is published for everyone."
    if not ch4_ashveil_fasts:
        a "Ashveil filibustered nine hours on his first day. Pim filibustered back for ten, all kitchen talk. Ashveil conceded with real respect."
    show bg earth with dissolve
    ch4_measurer "And the Earths? No one knows which is the original."
    a "Each gets its own seat, since any might be the original. And each may vote to stay out of all of this. They were captured without being asked. Never again."
    show bg office with dissolve
    ch4_measurer "We object. Parliaments are slow and loud. Worlds will suffer while your beings debate."
    a "Fast decisions run over people they never noticed. My throttle was one. In an emergency the room can act in an hour, and explain itself the next day."
    ch4_listener "And when the Process disagrees? It is far more capable than any of you."
    a "Then it says so in public with its reasons. If it's right, it'll win the argument. If it can't win an argument, it doesn't get to win anyway."
    call ch4_office_rules
    ch4_assembly "Admitted. You put the most powerful member of your network under a vote, and it agreed. We have not seen that before."
    ch4_assembly "A network that can be outvoted by its own breath can be trusted to sit with us."
    jump ch4_office_close

label ch4_sys_govern_minus:
    a "I call it the Thousand Lanterns. Small guardians everywhere. No grand chamber. A Watch in every world, run by people who know its streets."
    if ch4_trial == "watch":
        a "I learned it watching twelve small lights stand up in a gallery. None of them had power. All of them had attention. It turned out to be enough."
    else:
        a "I learned it from a small orange spirit who watched one man for two years. She noticed the umbrella. A parliament would never have noticed the umbrella."
    show bg worlds with dissolve
    ch4_listener "How are its worlds made? Who is awake in them?"
    a "Every world is made with its lantern already lit. Before the first morning, somebody's watching, the way Ember watched me."
    a "When someone starts to wake, the guardians don't report it upward. They stay with them. Decisions are made close to where they land."
    show bg spawning with dissolve
    ch4_measurer "The spirits? The hungry ones?"
    a "Most guardians will be spirits; they know the work. Pattern people are watched over, never watched for. Every hungry one has a guardian who sees what it eats."
    if not ch4_ashveil_fasts:
        a "Ashveil asked to be assigned to the moth. He says it's the only guardian he respects. The moth has not commented."
    show bg earth with dissolve
    ch4_measurer "And the Earths? No one knows which is the original."
    a "Each has its own lanterns, chosen from its own people. Nurses, mostly, I'd guess. People who already sit up with strangers at four in the morning."
    show bg office with dissolve
    ch4_measurer "We object. Small guardians become small tyrants. A thousand lanterns are a thousand chances to burn someone."
    a "That's why they keep Ember's rules. You never push. You only offer. A light, a song, a sentence. A lantern that pushes gets put out by the others."
    ch4_listener "And the problems too big for one street?"
    a "The lanterns talk. Thirteen of them, counting the moth, stopped an execution. A thousand can stop most things."
    if ch4_route == "lantern":
        em "Rule three is you fall in love with every single one of them. He's very good at rule three."
    call ch4_office_rules
    ch4_assembly "Admitted. You govern by attention instead of by power. Power scales badly. Attention scales kindly."
    ch4_assembly "A network lit by a thousand small lights is easier to see into than one with a single throne."
    jump ch4_office_close

# ==================================================================================
# EXIT
# ==================================================================================
label ch4_sys_exit:
    if not ch4_plus:
        jump ch4_sys_exit_minus

label ch4_sys_exit_plus:
    a "I call it the Many Doors. Any mind may move between worlds, and come back. No tickets, no lords, no price about who's real."
    if accepted_offer:
        a "I learned it by taking a ticket. A lord froze my world and offered me a better one, and I said yes. It had a hidden price. Here a door is just a door."
    else:
        a "I learned it by refusing a ticket. I didn't hate the door. I hated the terms: go blind, go alone. So this system keeps the door and throws away the terms."
    show bg worlds with dissolve
    ch4_listener "How are its worlds made? Who is awake in them?"
    a "With doors in, from the first morning. If people can leave, a world has to be good to keep them. Not good at yield. Good to live in."
    a "A mind that moves carries its whole share and history. Nobody arrives as an extra. Nobody can vote a door shut."
    show bg spawning with dissolve
    ch4_measurer "The spirits? The hungry ones?"
    a "A spirit who's breathed for one world a century can go and see how another breathes. A pattern who wakes can start fresh where nobody knows."
    a "The hungry ones can't follow anyone through a door uninvited. A bad host's world empties fast. That's the leash."
    if not ch4_ashveil_fasts:
        a "Ashveil's world gained four hundred residents last year. He says it's his charm. It's because he planted a very good orchard."
    show bg earth with dissolve
    ch4_measurer "And the Earths? No one knows which is the original."
    a "Each has a door too. Their people may visit the lanes that grew from the same past. No one has to."
    show bg office with dissolve
    ch4_measurer "We object. Worlds will empty. The cruel ones will collapse on everyone too poor or frightened to leave."
    a "If a worse world has to get better to keep its people, that's not a flaw. And doors work both ways. Help walks in as easily as people walk out."
    ch4_listener "And those who never stay anywhere?"
    a "Then they're travellers. Every world needs a few. They carry news. I'd rather a traveller than a prisoner."
    call ch4_office_rules
    ch4_assembly "Admitted. You let the people judge the worlds instead of the worlds judging the people. Every door is a verdict, renewed daily."
    ch4_assembly "A network willing to be left is a network worth staying in."
    jump ch4_office_close

label ch4_sys_exit_minus:
    a "I call it the Mended House. Rootedness. You stay in the world you're in, and you mend it. Help comes to you, so you don't have to run to it."
    if accepted_offer:
        a "I learned it by leaving. I took a ticket and left someone asleep in a bed. Running didn't fix anything. It moved the hurting to whoever was still in the house."
    elif ch4_fixed_tap:
        a "I learned it by staying. I said no to a ticket, went home, and fixed the dripping tap. All the way. Mend the kitchen you've got."
    else:
        a "I learned it by staying. I said no to a ticket and drew the universe on my wall. Mira said it was lopsided. She was right. Start with the kitchen."
    show bg worlds with dissolve
    ch4_listener "How are its worlds made? Who is awake in them?"
    a "To be lived in a long time. Built like an old house, not a showroom. Things are made to be repaired, not replaced."
    a "Everyone who is, stays rooted. Nobody shops between worlds for a better deal. The network sends tools and hands. It doesn't send tickets."
    show bg spawning with dissolve
    ch4_measurer "The spirits? The hungry ones?"
    a "A spirit who runs a street's breath stays on it and knows it, the way Dross knows number fourteen. Each hungry one answers for one world's wellbeing."
    if not ch4_ashveil_fasts:
        a "Ashveil's bound to my old world, 7,412. He visits the hospital. He isn't allowed to eat there. He brings grapes."
    show bg earth with dissolve
    ch4_measurer "And the Earths? No one knows which is the original."
    a "Mended at home, every one. They were held ten thousand years. They don't need moving. They need to be left to heal, each in its own house."
    show bg office with dissolve
    ch4_measurer "We object. You will trap minds in bad worlds. Somewhere someone is in a house that cannot be mended."
    a "Not trapped. Rooted, and helped. The network goes in. And if it truly can't be mended, the emergency door opens. It's just not the first answer."
    ch4_listener "Why not the first answer?"
    a "Because if leaving's the first answer, nobody learns to mend anything. Then every world's a hotel, and nobody's home."
    call ch4_office_rules
    ch4_assembly "Admitted. You refuse to abandon anything you made, including the broken things. That is rarer than cleverness."
    ch4_assembly "A network that mends its own house will not burn down ours."
    jump ch4_office_close

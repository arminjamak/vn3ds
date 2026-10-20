# Snapshot - Chapter 4: the seven systems, part A (less, truth, share).
# Each system has a + and a - flavour; "less" also has the open question.

# =====================================================================================
# LESS
# =====================================================================================
label ch4_sys_less:
    if ch4_open:
        jump ch4_sys_open
    if not ch4_plus:
        jump ch4_sys_less_minus

label ch4_sys_less_plus:
    a "I call it the Light Touch."
    a "The main idea is that whoever runs the worlds should touch them as little as possible. One change. Then a long silence. Then listen."
    a "I learned it in a kitchen. A tap was dripping, and there was a whole cosmic machine above me, and I fixed the tap. All the way."
    a "Nothing in the universe changed. The kitchen did. That's the scale I trust."
    show bg worlds with dissolve
    ch4_listener "How are its worlds made?"
    a "Rarely, and simply. A new world starts from one honest starting point and then it's left alone to grow. No hourly nudging. No stage crew."
    a "Every intervention, ever, goes in a public ledger. One line each. If the ledger gets long, the network's doing something wrong."
    ch4_measurer "Who is conscious in it?"
    a "Whoever's there. No more rendered crowds to make a world feel full. A smaller world with no extras beats a big one full of cardboard."
    a "If that means a town of nine hundred real people instead of a city of nine million props, fine. Nine hundred is a lot of people."
    ch4_listener "And who governs?"
    a "The charter fits on one page. The fair-share floor and six short rules. Everything above that, the worlds work out for themselves."
    a "The network isn't a government. It's the plumbing. Good plumbing is the kind you never think about."
    show bg spawning with dissolve
    ch4_measurer "The spirits? The pattern people?"
    a "Spirits keep doing what's needed. Breathing, blinking, the hard automatic stuff. Nothing decorative. No more running crowds for effect."
    a "And no pattern person is rendered for nine seconds in the rain just so somebody's world looks busy. I gave one my umbrella. Once is enough."
    show bg council with dissolve
    ch4_listener "The hungry ones."
    a "They can stay. They can eat what's given freely. Applause. A song somebody sings on purpose. A busker's hat, not a farm."
    if not ch4_ashveil_fasts:
        a "Ashveil tells me it's like living on starters. He says he's never felt better. He says it like it's an insult."
    show bg earth with dissolve
    ch4_measurer "And the Earths? One of them is the captured original. No one knows which."
    a "Left alone, every one of them, since any of them might be the one. The cage is gone. They keep their gifts. The lightest touch on an Earth is none."
    a "Transfers are rare. One door per world, opened on request, logged in the ledger like everything else."
    show bg office with dissolve
    ch4_measurer "We object. A light hand lets suffering run. You will watch a war you could stop in a second, and call it restraint."
    a "No. If there's a war, I stop the war. That's the one thing. The smallest intervention that stops it, and then I write down why."
    a "Light isn't absent. A light touch on someone's shoulder still stops them stepping into the road."
    ch4_listener "And if the one thing is wrong?"
    a "Then it's one thing to undo. That's the other reason to keep it small. Big changes have no back button."
    if ch4_route == "chosen":
        m "He means it. He spent forty minutes on one washer. I timed it."
    elif ch4_route == "lantern":
        em "It's how we work. One light. Three flickers. Then you trust them to look up."
    call ch4_office_rules
    ch4_assembly "..."
    ch4_assembly "Admitted. Every network that ever applied asked for more reach. Yours is the first that asked to do less with what it has."
    ch4_assembly "Restraint is the rarest design we see. It is the only one that ages well."
    jump ch4_office_close

label ch4_sys_less_minus:
    a "I call it the Careful Hand."
    a "The main idea is that worlds should be tended closely. Not harvested closely. Tended. A gardener walking the rows every day."
    a "The old network already touched everything. The mistake wasn't the touching. It was why. They touched to take. I want touching to give."
    show bg worlds with dissolve
    ch4_listener "How are its worlds made?"
    a "Carefully, by hand. Each new world has a gardener from day one, who knows its weather, its streets, which of its people are running thin."
    a "The angel corps becomes the gardeners. They already know how to feed opportunity into a world. Now they do it for the world's sake."
    a "A song on the radio at the right moment. A stranger saying the right sentence. Not to keep a subject busy. Because somebody needed it."
    ch4_measurer "Who is conscious in it?"
    a "Minds are grown carefully. Pattern people get tended like seedlings; if one starts to wake, the gardener notices and helps it along."
    a "I watched a friend's thread run thin once. Forty percent spirit, sixty him, and the sixty fading. In this system, somebody sees that early."
    ch4_listener "And who governs?"
    a "The Process steers, but every gardener reports to the floor: does each being have its fair share? If not, that's the work today."
    show bg spawning with dissolve
    ch4_measurer "The spirits? The pattern people?"
    a "The spirits are the gardeners' hands. Honoured, rested, rotated. Nobody runs the same man's breathing for eleven years without a holiday."
    show bg council with dissolve
    ch4_listener "The hungry ones."
    a "The vampires can feel which way a world is leaning. That's a brilliant instrument. Pointed at yield, it's a mouth. Pointed at need, it's a doctor."
    if not ch4_ashveil_fasts:
        a "Ashveil's the first. He feels where a world is cold now, instead of where it's ripe. He complains about it constantly. He's very good."
    show bg earth with dissolve
    ch4_measurer "And the Earths? One of them is the captured original. No one knows which."
    a "Tended at a distance, all of them, because they're free now. Medicine, ideas, comfort when they pray. Given when asked. Never invoiced."
    a "Transfers are transplants. A mind is moved only if its soil is wrong for it, and moved with its roots, and checked on after."
    show bg office with dissolve
    ch4_measurer "We object. A close hand becomes a cage. Your Council also tended its worlds closely. Every day. For ten thousand years."
    a "Same tools. Different reason for holding them. And the difference can be checked: after a gardener's visit, does the world's share go up, or the gardener's?"
    a "If it's the gardener's, he's a farmer. Then he's out."
    ch4_listener "Who tends the gardener?"
    a "The other gardeners. And the people in the rows, who can say 'stop' and be heard. A good hand knows when it's not wanted."
    if ch4_route == "longfog":
        th "He tends people. Trust me. He sat on my floor till four in the morning once. I was the garden."
    call ch4_office_rules
    ch4_assembly "..."
    ch4_assembly "Admitted. You have written down the difference between a farmer and a gardener. Most never notice there is one."
    ch4_assembly "A network that knows why it touches is safe to let touch."
    jump ch4_office_close

label ch4_sys_open:
    a "I don't have a system yet. I have a question. I call it the Open Question."
    ch4_measurer "You came to the oldest assembly there is, with a question."
    a "Yes. Because every time I was sure, I was wrong in a new way. I've been right, and diagnosed, and both. Certainty's how you end up in a valley."
    a "So the main idea is a method for finding the design, instead of the design."
    show bg worlds with dissolve
    ch4_listener "How are its worlds made?"
    a "In pairs. Every new world is forked into two from the first morning. One with a light hand, one with a close one. Same people. Same weather."
    a "Then we watch. Not for yield. For one thing: in which of the two do people get a fairer share of their lives?"
    a "And then we ask the people in both, which is the part your ten thousand clever applications left out."
    ch4_measurer "Who is conscious in it?"
    a "Everyone who already is, stays. The fair-share floor is the only thing I'm sure of. Beyond that, ORCHARD asks every world how full it wants to be."
    ch4_listener "Who governs?"
    a "Whoever the experiment says works best, world by world, and the network has to publish its reasoning when it decides."
    show bg spawning with dissolve
    ch4_measurer "The spirits? The pattern people? The hungry ones? Earth?"
    a "Asked. Each of them. The spirits get asked what they want. I asked one once; he wanted a sunrise. It took him eleven years to say it."
    a "The vampires get asked what they'll eat instead. Earth is free, and will be asked when it's ready, and not before."
    a "Transfers: open question too. Some doors, some roots. We'll find the ratio by watching, not by guessing."
    show bg office with dissolve
    ch4_measurer "We object. This is an application with no answers."
    a "It's an application with a method. The answers you get from me today would be the answers of one tired man in one bright room."
    a "The method's answer will be everyone's it touched. That's slower. It's also the only way I know to find the absolute best instead of the nearest good."
    ch4_listener "And if the method never finishes?"
    a "Then it never finishes. The worlds don't stop being lived in while we think. Nobody's late."
    call ch4_office_rules
    ch4_assembly "..."
    ch4_assembly "Admitted. We have heard ten thousand networks that knew exactly what they wanted. Yours is the only one that knew it didn't know."
    ch4_assembly "That is the right place to begin. We began there too."
    jump ch4_office_close

# =====================================================================================
# TRUTH
# =====================================================================================
label ch4_sys_truth:
    if not ch4_plus:
        jump ch4_sys_truth_minus

label ch4_sys_truth_plus:
    a "I call it the Open Lighthouse."
    a "The main idea is that every being may learn what it is. Spirit, pattern, subject, vampire, process. Ask, and you'll get a true answer."
    a "For a long time the price of everything was not knowing. 'I won't tell you who there is real. That's the price of the ticket.'"
    a "In this system there's no price on that. The ticket is free, and the answer's printed on it."
    if ch4_woke_mira:
        a "I learned it at three in the morning, waking someone I love to tell her the truth when I didn't know if she was real."
        a "She said she'd rather be told the truth by a man with a weird hobby than lied to by a nice one. I've built a whole system out of that sentence."
    else:
        a "I learned it the hard way. Every time I was spared the truth, I spent the next year chasing it alone, and it cost more than knowing."
    show bg worlds with dissolve
    ch4_listener "How are its worlds made?"
    a "Every world is built with a lighthouse. One place, in plain sight, where anyone can go and ask what they are, and what's above them."
    a "And every intervention the network makes is logged where the people of that world can read it. The angels work in daylight now."
    ch4_measurer "Who is conscious in it?"
    a "Whoever is, knows it. And whoever isn't fully, knows that too, if they ask. No more checking your girlfriend for seams at breakfast."
    ch4_listener "Who governs?"
    a "Whoever governs, governs in the open. Every decision posted where the governed can read it, in words they can understand."
    show bg spawning with dissolve
    ch4_measurer "The spirits? The pattern people?"
    a "Told what they are, the first time they wonder. Then asked what they'd like to be. Some will want to keep running breath. That's fine. Knowing, they choose it."
    show bg council with dissolve
    ch4_listener "The hungry ones."
    a "They have to eat in the light. Every vampire's feeding is public: what, from whom, how much. You can't farm people who can see the farm."
    if not ch4_ashveil_fasts:
        a "Ashveil volunteered to publish his first. He said it was the most naked he's felt in a thousand years. He seemed to enjoy it."
    show bg earth with dissolve
    ch4_measurer "And the Earths? One of them is the captured original. No one knows which."
    a "Told. Every Earth, slowly, gently, in a way it can carry. Including that nobody knows which of them is the original. That's part of the truth too."
    a "Transfers are honest. If you move worlds, you're told exactly who at the other end is real. No mystery tickets."
    show bg office with dissolve
    ch4_measurer "We object. Truth breaks minds. You of all beings should know. You heard the logs of the universe and it put you in a ward."
    a "It did. But the truth didn't put me there. Being alone with it did. Hearing it through a wall, in pieces, while the world glitched and nobody could check."
    a "So every lighthouse has a keeper. You never get told what you are and then left on the rocks."
    ch4_listener "Some will not want to look."
    a "Then they don't have to. A lighthouse doesn't make ships look at it. It just makes sure the light's there when they do."
    if ch4_route == "architect":
        m "He told me. Eventually. I was furious. I'm still glad."
    elif ch4_route == "chosen":
        m "He'll tell you. He'll tell you whether you want it or not. It's very annoying and I wouldn't change it."
    call ch4_office_rules
    ch4_assembly "..."
    ch4_assembly "Admitted. No network has ever opened its logs to us before we asked for them. You have opened them to its own people."
    ch4_assembly "A network that shows its machinery to the ones inside it has nothing it needs to hide from us."
    jump ch4_office_close

label ch4_sys_truth_minus:
    a "I call it the Gentle Veil."
    a "The main idea is that illusions that comfort are protected. Nobody's world gets pulled out from under them just because someone else knows the trick."
    a "But a veil is only allowed if it's honest underneath. You may protect a dream. You may never farm a dreamer. That's the whole charter, in two lines."
    if ch4_woke_mira:
        a "I learned it the other way round. I woke someone I love at three in the morning with the truth, and I watched what it cost her face."
        a "I'd do it again. But I don't think everyone should have to be woken like that, at three in the morning, by a man with a notebook."
    else:
        a "I learned it at a bedside, deciding not to wake someone. I left a note instead. 'Coffee's in the blue tin. I love you. That part's real.'"
        a "It was a veil. The thing underneath it was true. That's the only kind I'll allow."
    show bg worlds with dissolve
    ch4_listener "How are its worlds made?"
    a "Whole. Believable. Kind. A world doesn't need to keep reminding you it's a world. It just needs to never use that against you."
    ch4_measurer "Who is conscious in it?"
    a "Everyone who is, is. Nobody is forced to ask whether they're real. That question can wreck a life. I'm proof."
    a "But anyone who does ask, gets an answer. The veil has a handle on the inside. You can lift it whenever you want. Nobody can lift it for you."
    ch4_listener "Who governs?"
    a "The veil's keepers are audited by beings who've seen behind it. The Lantern Watch. They know exactly what's being hidden and from whom."
    a "If the veil is ever hiding harm, they tear it. That's their whole job. Comfort, yes. Cover, never."
    show bg spawning with dissolve
    ch4_measurer "The spirits? The pattern people?"
    a "They keep their roles undisturbed if they want to. A pattern person never has to find out they're a pattern. A spirit can ask, and be told."
    show bg council with dissolve
    ch4_listener "The hungry ones."
    a "They're outside the veil. It's for the dreamers, not the eaters. A vampire can't hide behind a kindness meant for someone else."
    show bg earth with dissolve
    ch4_measurer "And the Earths? One of them is the captured original. No one knows which."
    a "Every Earth keeps its God. The shape they know, the comfort when they pray. But underneath it's honest now. Nothing is taken in return."
    a "Transfers are quiet. If a mind moves, it isn't haunted by the question of who's real at the other end. It can ask. It doesn't have to."
    show bg office with dissolve
    ch4_measurer "We object. A veil is a lie with good manners. Your Council's cage was also invisible, and also called itself kind."
    a "The difference is who it protects. The cage protected the ones eating. The veil protects the one dreaming."
    a "And the cage only opened from outside. The veil only opens from inside. Anyone in it can step out. Nobody out here can step in and take."
    ch4_listener "Who decides which illusions comfort, and which ones harm?"
    a "The one under it, first. The Watch, second. Never the network alone. I don't trust anything powerful to decide what's good for me to not know."
    call ch4_office_rules
    ch4_assembly "..."
    ch4_assembly "Admitted. We have seen many veils. This is the first with the handle on the inside."
    ch4_assembly "A network that will protect a dream without owning the dreamer understands what mercy is for."
    jump ch4_office_close

# =====================================================================================
# SHARE
# =====================================================================================
label ch4_sys_share:
    if not ch4_plus:
        jump ch4_sys_share_minus

label ch4_sys_share_plus:
    a "I call it the Common Table."
    a "The main idea is an equal share of consciousness for every world. Every world gets the same chance at being awake. No more empty farms."
    a "The old system gave minds to worlds that produced. A fresh world got a handful of real people and a million extras. That's where I lived."
    if ch4_gave_theo:
        a "I learned it holding one good hour in my hands, and giving it sideways, to my friend's thread. Everything there flowed upward. I made one arrow go sideways."
        a "A spirit told me nobody ever does that. This system is built so it's the normal direction."
    else:
        a "I learned it by not sharing. I kept my last good hour to climb with, while my friend's thread ran thin. It was the right call. I hated it."
        a "This system is built so nobody ever has to make that call again. Nobody's hour should be the only thing holding a friend up."
    show bg worlds with dissolve
    ch4_listener "How are its worlds made?"
    a "Fewer of them. Fuller. Every new world is seeded with as many awake minds as it can hold well. Not a city of props."
    a "The energy that used to go up to the chamber now goes into the minds. That's what pays for it."
    ch4_measurer "Who is conscious in it?"
    a "Everyone at the table. Anything that can suffer is awake enough to be counted. If it's counted, it gets a full plate."
    ch4_listener "Who governs?"
    a "Shares are audited. Every world can see every other world's allocation. If one table's plates are smaller, the whole network sees it."
    show bg spawning with dissolve
    ch4_measurer "The spirits? The pattern people?"
    a "Offered seats. A pattern person who wants to wake gets the same share as anyone born awake. Spirits too. Dross gets a chair. He hates chairs."
    show bg council with dissolve
    ch4_listener "The hungry ones."
    a "Guests. They sit at the table and eat the same share as everyone else. No more. It's a smaller meal than they're used to."
    if not ch4_ashveil_fasts:
        a "Ashveil says it's the first time in his life he's ever finished a plate and not wanted the next one. He thinks he's ill."
    show bg earth with dissolve
    ch4_measurer "And the Earths? One of them is the captured original. No one knows which."
    a "One place each at the table. Nobody knows which Earth was first, and at this table it doesn't matter. No throne for the original. No cage for any."
    a "Transfers carry your share with you. You can't lose your place by moving. Your plate follows you."
    show bg office with dissolve
    ch4_measurer "We object. Equal shares are very expensive. You will run far fewer worlds than your network can."
    a "Yes. Fewer, fuller worlds instead of billions of empty ones. I'll take a thousand worlds where everyone is someone over a billion where most people are scenery."
    ch4_listener "And the worlds that waste their share?"
    a "They keep it. You don't earn a floor. That's what makes it a floor. You can fall short above it. You can't fall through."
    if ch4_route == "longfog":
        th "He gave me an hour once. I didn't know till later. I just laughed at my phone for no reason. Best laugh I've had."
    call ch4_office_rules
    ch4_assembly "..."
    ch4_assembly "Admitted. Your design costs the network more than any we have seen, and it chooses to pay. Every line of it chooses to pay."
    ch4_assembly "A network willing to be poorer so that no one in it is scenery is one we would like at our own table."
    jump ch4_office_close

label ch4_sys_share_minus:
    a "I call it the Terraced Vineyard."
    a "The main idea is earned growth. Worlds start with a few awake minds and earn more by cooperating. By care. Never by output."
    a "Like terraces up a hill. You don't plant the whole slope at once. You build one level, and when it holds, the next."
    if ch4_gave_theo:
        a "I learned it the strange way. I gave my good hour sideways once, to a friend. Nobody made me. That's when I knew care can't be ordered. It has to be grown."
        a "So I wanted a system where care is what grows things."
    else:
        a "I learned it by keeping my last good hour to climb with. A spirit told me: worlds that hold together get more light. That was the old policy."
        a "I kept the shape of it and changed the meaning. Worlds that hold together, that look after their own, earn more minds."
    show bg worlds with dissolve
    ch4_listener "How are its worlds made?"
    a "Small. A first terrace with a few hundred awake people and the spirits to help them. No stage crowds. Just a village."
    a "When the village learns to look after itself, ORCHARD plants the next terrace. More minds. More room. The hill fills slowly."
    ch4_measurer "Who is conscious in it?"
    a "Everyone already awake keeps everything. The fair-share floor never moves. What's earned is new minds, not anyone's existing share."
    ch4_listener "Who governs?"
    a "There's a ledger of care. Not yield. How many people were sat with at four in the morning. How many strangers got an umbrella."
    a "It's measured from the inside, by the people in the world. Not by the chamber that wanted to eat it."
    show bg spawning with dissolve
    ch4_measurer "The spirits? The pattern people?"
    a "They tend the terraces. A pattern person who starts to wake becomes the newest mind on the hill. Earned by the hill, given to her."
    show bg council with dissolve
    ch4_listener "The hungry ones."
    a "The vampires used to measure yield. They're very good at feeling where a world is warm. Now they measure cooperation. Same sense. Different ledger."
    if not ch4_ashveil_fasts:
        a "Ashveil assesses terraces now. He says love tasted better than this. Then he says it with less conviction every year."
    show bg earth with dissolve
    ch4_measurer "And the Earths? One of them is the captured original. No one knows which."
    a "The first terrace, every one of them. An Earth doesn't have to earn anything. They were held for ten thousand years. They've paid."
    a "Transfers go up the hill, never down. If your world is still a small terrace, you can visit a bigger one, learn, and bring it home."
    show bg office with dissolve
    ch4_measurer "We object. Earned growth is exactly how your Council justified its farms. 'Stable worlds earn more minds.'"
    a "They rewarded yield. I reward care. And under all of it is the floor, which nobody earns and nobody loses."
    a "If a world is cruel, it doesn't lose its people. It just doesn't get to grow until it's kinder."
    ch4_listener "Can care be measured without being faked?"
    a "Not perfectly. That's why the people inside measure it, not us. You can fake care to a vampire. It's harder to fake to your neighbour."
    call ch4_office_rules
    ch4_assembly "..."
    ch4_assembly "Admitted. You have made kindness the only currency that buys growth. We have not seen that tried at this scale."
    ch4_assembly "If it works, it will be copied. If it fails, it will fail gently. Both are acceptable in a member."
    jump ch4_office_close

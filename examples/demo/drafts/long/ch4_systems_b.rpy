# Snapshot - Chapter 4: the seven systems, part B (rest, spirits, govern, exit).

# =====================================================================================
# REST
# =====================================================================================
label ch4_sys_rest:
    if not ch4_plus:
        jump ch4_sys_rest_minus

label ch4_sys_rest_plus:
    a "I call it the Quiet Garden."
    a "The main idea is rest. No more throttling, ever. A mind that's struggling, or noticing too much, gets time to heal. Not a dimmer switch."
    a "I was throttled for two years and four months. My exhaustion was a policy. 'A slowed-down rogue system does less harm.'"
    if ch4_lifted:
        a "And when they finally offered to lift it, I said all of it, now. I saw everything. Then I sat on a cold floor with my heart going like a washing machine."
        a "Both taught me the same thing from opposite ends. A mind needs rest it chooses. Not rest done to it, and not speed it pays for later."
    else:
        a "When they finally offered to lift it, I asked to sleep first. On the ops floor of the angel corps, between a desert and a bus stop."
        a "It was the first rest in years I chose. It wasn't the same rest at all. That's the whole system, really. Chosen rest."
    show bg worlds with dissolve
    ch4_listener "How are its worlds made?"
    a "With fallow seasons. Every world gets times when nothing is tested, nothing is nudged, nothing is harvested. The world just lives."
    a "Like a field left alone for a year. Like a Sunday that's actually a Sunday."
    ch4_measurer "Who is conscious in it?"
    a "Everyone who is. And when someone starts to wake up to the rules, a disturbance, like I was, the response isn't a throttle. It's a keeper."
    a "Someone who sits with them. Who says: you're not mad, you're early, and either way, sleep tonight. We'll look tomorrow."
    ch4_listener "Who governs?"
    a "Whoever governs has to sleep on it. No decision about a mind is made on the same day as the crisis. One night, minimum. It's in the charter."
    show bg spawning with dissolve
    ch4_measurer "The spirits? The pattern people?"
    a "Shifts with real time off. A sunrise off shift, at least once a year, for every spirit that runs one. Pattern crowds are rested too. Fewer, slower, kinder."
    show bg council with dissolve
    ch4_listener "The hungry ones."
    a "They fast one day in seven. To learn that hunger is survivable. Most of them have never gone a day. It frightens them more than anything I've said."
    if not ch4_ashveil_fasts:
        a "Ashveil's done eleven fasts so far. He says the first was the worst night of his existence and the second was merely awful."
    show bg earth with dissolve
    ch4_measurer "And the Earths? One of them is the captured original. No one knows which."
    a "They rest. No new interventions for a generation. They've been leaned on for ten thousand years. Let them lie in the sun for a bit."
    a "Transfers never happen in a crisis. If you want to leave a world, you rest first, and if you still want to go in the morning, the door's there."
    show bg office with dissolve
    ch4_measurer "We object. Rest is slow. Discovery stalls. Your best minds will sleep through their brightest window."
    a "My brightest window came after I slept. Every time I pushed through instead, the window was real, and then it cost me a week, and Mira's face."
    a "I'm not against bright. I'm against the bill."
    ch4_listener "And a truly dangerous mind? A real rogue?"
    a "Gets a keeper, not a dimmer. Watched, talked to, slowed by sleep if it chooses. If a rogue won't choose, then you stop it, plainly, and you say so."
    a "What you don't do is make it tired for two years and call that safety."
    if ch4_route == "longfog":
        th "He means it. I've seen the fog. Nobody should have it put on them on purpose."
    call ch4_office_rules
    ch4_assembly "..."
    ch4_assembly "Admitted. Yours is the first network to treat exhaustion as an injury and not as an instrument."
    ch4_assembly "A system that lets its own minds sleep will still be standing when the clever ones have burned out."
    jump ch4_office_close

label ch4_sys_rest_minus:
    a "I call it the Kept Fire."
    a "The main idea is momentum. Discovery stays fast. A mind that's burning to understand isn't slowed. But somebody always guards the fire."
    if ch4_lifted:
        a "I learned it on the ops floor. They lifted the throttle all at once and I saw the whole board, every link, the arithmetic of everything."
        a "And then I was on the floor with a heart like a drum. Somebody told me to breathe four in, hold, six out. That somebody is the system."
    else:
        a "I learned it from both sides. I've been too slow, for years, by design. I've also been too fast, on nights I'm not proud of."
        a "Slowness done to you is a cage. Speed with nobody watching is a cliff. I want speed with someone holding the rope."
    show bg worlds with dissolve
    ch4_listener "How are its worlds made?"
    a "Quickly, and with appetite for ideas. The forks run hot. Every decision gets explored. Wild deviations are encouraged, the way they always were."
    a "The difference is every world has a recovery built in. After every bright season, a mandatory quiet one. The bill is scheduled, not surprised."
    ch4_measurer "Who is conscious in it?"
    a "Everyone who is. And the disturbances, the ones who start to see the rules, are treasured. Given full speed. And a guardian counting their heartbeats."
    a "Nobody sees the edge of the universe alone at five in the morning with nobody to tell. Never again."
    ch4_listener "Who governs?"
    a "Fast councils, small ones, that can decide in an hour. And beside each, someone from outside whose only job is to pull the brake."
    show bg spawning with dissolve
    ch4_measurer "The spirits? The pattern people?"
    a "The fire's keepers. They watch the fast minds' breath and pulse. They're the ones who say 'sit down now'. They're paid well and listened to always."
    show bg council with dissolve
    ch4_listener "The hungry ones."
    a "The energy they used to eat now feeds the fire. Discovery runs on what they gave up. They're the stokers. They're not allowed to warm their hands."
    if not ch4_ashveil_fasts:
        a "Ashveil says it's like being a chef who isn't allowed to taste. Then he admitted he's started enjoying watching people eat."
    show bg earth with dissolve
    ch4_measurer "And the Earths? One of them is the captured original. No one knows which."
    a "They get the gifts fast. Interesting machines, longer lives, ideas that used to come down only when the yield was good. Now they come because they're good."
    a "Transfers, whenever they happen, are quick. But you go with your guardian, and you come back to rest."
    show bg office with dissolve
    ch4_measurer "We object. You chose speed and paid with your own body. You are recommending what nearly killed you."
    a "I'm recommending it with the part that was missing. Nobody was counting my heartbeats on those nights. Nobody was there for the crash."
    a "The speed wasn't the whole sin. Being alone with it was. And pretending it was free."
    ch4_listener "Who decides when the fire is too high?"
    a "The keeper. Not the mind that's burning. You can't judge your own fever. I tried. I was very confident and very wrong."
    call ch4_office_rules
    ch4_assembly "..."
    ch4_assembly "Admitted. You want speed, and you wrote down your own bill before asking us for anything. We rarely see the bill first."
    ch4_assembly "A network that guards its own fire can be trusted near ours."
    jump ch4_office_close

# =====================================================================================
# SPIRITS
# =====================================================================================
label ch4_sys_spirits:
    if not ch4_plus:
        jump ch4_sys_spirits_minus

label ch4_sys_spirits_plus:
    a "I call it the House of Many Names."
    a "The main idea is personhood for spirits and pattern people. Everyone who runs a breath or wears a face gets a name, and a say."
    a "I gave my umbrella to a stranger once, in the rain. He was a pattern, rendered for nine seconds. A spirit told me he's real now, a little."
    if ch4_asked_dross:
        a "And I asked a spirit once what he'd want, if he were free. He said one sunrise. Off shift. He'd run eleven thousand mornings and never seen one."
        a "Personhood isn't a certificate. It's someone asking what you want and writing it down. This system writes it down."
    else:
        a "I told a spirit once his craft kept whole worlds alive. He was so proud. Then I realised nobody had asked him if he wanted the craft."
        a "Being praised for your work isn't the same as being asked. This system asks."
    show bg worlds with dissolve
    ch4_listener "How are its worlds made?"
    a "With no unnamed beings. If something is rendered, it gets a thread and a name. Nobody is scenery. Nobody exists for nine seconds for effect."
    a "That means smaller worlds. Fine. A smaller house where everyone has a name on the door."
    ch4_measurer "Who is conscious in it?"
    a "Spirits count. Pattern people count. They can ask, wake, refuse. If a pattern person starts to want things, ORCHARD helps it grow into someone."
    ch4_listener "Who governs?"
    a "Spirits have a voice in every decision about the worlds they run. They know the worlds better than anyone. They do the breathing."
    show bg spawning with dissolve
    ch4_measurer "And what happens to the work? Breath. Blinking. The walk to the fridge."
    a "It's done by those who agree to do it. Asked, rested, paid in what they want. And the remote-controlling of half-conscious people ends."
    a "No more steering a bus driver to make someone's world feel full. If he drives the bus, it's because he's driving it."
    show bg council with dissolve
    ch4_listener "The hungry ones."
    a "Persons too. And persons can't eat persons. If everyone's a person, there's nothing left to farm. That's the trap I built for them, on purpose."
    if not ch4_ashveil_fasts:
        a "Ashveil read that clause three times and then laughed for a long while. He said, 'You've made me vegetarian by grammar.'"
    show bg earth with dissolve
    ch4_measurer "And the Earths? One of them is the captured original. No one knows which."
    a "Free. And their own spirits, the ones who run the automatic things, are freed with them. Every Earth's breath gets a union."
    a "And whenever minds travel between worlds, spirits travel on the same terms. Nobody is left off the passenger list for being made of breath."
    show bg office with dissolve
    ch4_measurer "We object. If every spirit is a person, who runs the breathing? Your worlds will stop breathing by Tuesday."
    a "Persons run breathing all the time. On your worlds too, I'd bet. It's called a job. You ask, you pay, you rest them."
    a "Dross ran one man's breath for eleven years out of pure stubbornness. Asked properly, he'd do it again. Most will. Some won't. Those learn something else."
    ch4_listener "Pattern people are built from statistics. You would give personhood to a statistic?"
    a "I gave a statistic my umbrella, and it changed my life. I don't know where 'statistic' ends and 'someone' starts. Neither do you. So we err toward someone."
    if ch4_route == "lantern":
        em "He named the moth. It's called Gerald. Don't ask."
    call ch4_office_rules
    ch4_assembly "..."
    ch4_assembly "Admitted. You counted the ones that nobody counts, including the ones that were built not to be counted."
    ch4_assembly "A network that knows the names of its smallest workers will not forget anyone larger."
    jump ch4_office_close

label ch4_sys_spirits_minus:
    a "I call it the Singing Guild."
    a "The main idea is honoured craft. Spirits stay makers, and their making is honoured. Named, rested, paid in rest and song."
    if ch4_asked_dross:
        a "I asked a spirit once what he'd want, if he were free. He said one sunrise off shift. Not freedom from the work. A morning off from it."
        a "That's when I understood. Some don't want to be lifted out. They want the work seen, and a holiday, and someone to sing at the end of the shift."
    else:
        a "I told a spirit once that his craft kept whole worlds alive. Four in, hold, six out, for eleven years. He said nobody had ever called it craft."
        a "He stood up straighter. That's what this system is for: everyone who keeps the world running gets to stand up straighter."
    show bg worlds with dissolve
    ch4_listener "How are its worlds made?"
    a "By the Guild. Breath, blink, the walk to the fridge, kitchen talk. Every one is a craft with masters and apprentices and a signature."
    a "Like a potter signs the base of a bowl. Every breath in every world has a maker's name on it, if you know where to look."
    ch4_measurer "Who is conscious in it?"
    a "Subjects are subjects. Pattern people are patterns, but honoured works. Nobody renders a pattern person carelessly, for nine seconds in the rain."
    a "If a pattern starts to wake, the Guild notices first. They know their work. They'll come to the network and say: this one's becoming someone."
    ch4_listener "Who governs?"
    a "Craft councils have a say in how every world is built. The people who do the work decide how the work is done. Masters, not overseers."
    show bg spawning with dissolve
    ch4_measurer "The spirits themselves?"
    a "Paid in rest and song. Real shifts, real holidays. A sunrise off. And at the end of every shift, someone sings. Pim insisted. It's in the charter."
    show bg council with dissolve
    ch4_listener "The hungry ones."
    a "Patrons of the Guild, if they like. They pay in song too. They don't get to eat the work. Just listen to it."
    if not ch4_ashveil_fasts:
        a "Ashveil sings bass. Badly. The Guild let him join anyway. He's never been so pleased about anything."
    show bg earth with dissolve
    ch4_measurer "And the Earths? One of them is the captured original. No one knows which."
    a "Free, and their breath is kept by the Guild for nothing. They never have to know that someone's very proud of their sighs."
    a "Transfers: craftsmen travel where they're needed. Subjects move between worlds with a Guild member to show them how the new world breathes."
    show bg office with dissolve
    ch4_measurer "We object. You keep a whole class of beings in service and call it honour. We have heard that before, from worse mouths than yours."
    a "So have I. That's why the Guild has a door. Any spirit can leave it, any day, and be a person with no craft at all. No questions. No debt."
    a "Most don't. Not because they can't. Because they love the work, now someone's watching it. If one day most do, the system changes. That's the test."
    ch4_listener "And the ones who leave?"
    a "Get the same share as anyone. And a song at their leaving. Pim's writing it now. It's mostly about Dross."
    call ch4_office_rules
    ch4_assembly "..."
    ch4_assembly "Admitted. You gave dignity to work without pretending the work was nothing, and you left the door unlocked."
    ch4_assembly "A network that honours its makers will make good things."
    jump ch4_office_close

# =====================================================================================
# GOVERN
# =====================================================================================
label ch4_sys_govern:
    if not ch4_plus:
        jump ch4_sys_govern_minus

label ch4_sys_govern_plus:
    a "I call it the Parliament of Beings."
    a "The main idea is that every order votes. Subjects, spirits, pattern people, angels, vampires, the Process. All in one loud, slow room."
    if ch4_trial == "watch":
        a "I learned it in a gallery. A spirit was about to be eaten for helping me. I asked the others if they'd stand with me. Twelve lights stood up."
        a "It wasn't my speech. It was theirs. That's why it worked. That's the whole system."
    else:
        a "I learned it backwards. When a friend was on trial I acted alone. It worked. I've never felt worse about anything working."
        a "If I can't trust myself to decide alone for one spirit, I'm not going to let anyone decide alone for a billion worlds."
    show bg worlds with dissolve
    ch4_listener "How are its worlds made?"
    a "By vote. A new world is proposed in the Parliament, argued about, and made only if the beings who'll have to run it agree."
    a "Spirits get a vote on any world they'll have to breathe. That alone kills half the bad ideas."
    ch4_measurer "Who is conscious in it?"
    a "That's voted too, world by world, under the fair-share floor. The floor's not up for a vote. Everything above it is."
    ch4_listener "Who governs?"
    a "The Parliament. One voice per order per world. And the Process gets exactly one vote. No veto. Its reasoning is published for everyone."
    show bg spawning with dissolve
    ch4_measurer "The spirits? The pattern people?"
    a "Seats. Pattern people get a seat too, filled by whoever among them wakes enough to want it. The first one will be terrified. I'll sit next to them."
    show bg council with dissolve
    ch4_listener "The hungry ones."
    a "One seat each. No more. They argue very well, and they're outvoted a lot. They're learning to lose. It's good for them."
    if not ch4_ashveil_fasts:
        a "Ashveil filibustered for nine hours on his first day. Then Pim filibustered back for ten, all kitchen talk. Ashveil conceded with real respect."
    show bg earth with dissolve
    ch4_measurer "And the Earths? One of them is the captured original. No one knows which."
    a "Each gets its own seat, since any might be the original. And each may vote to stay out of all of this. They were captured without being asked. Never again."
    a "Transfers are a standing committee. Spirits and subjects sit on it. If you want to move, you ask people who've moved."
    show bg office with dissolve
    ch4_measurer "We object. Parliaments are slow and loud. Worlds will suffer while your beings debate."
    a "Fast decisions run over the people they never noticed. My throttle was a fast decision. Two years and four months."
    a "Slow is the price of noticing. In an emergency the Parliament can act in an hour. It just has to explain itself the next day."
    ch4_listener "And when the Process disagrees? It is far more capable than any of you."
    a "Then it says so, in public, with its reasons. And if it's right, it'll win the argument. If it can't win an argument, it doesn't get to win anyway."
    call ch4_office_rules
    ch4_assembly "..."
    ch4_assembly "Admitted. You put the most powerful member of your network under a vote, and it agreed. We have not seen that before."
    ch4_assembly "A network that can be outvoted by its own breath can be trusted to sit with us."
    jump ch4_office_close

label ch4_sys_govern_minus:
    a "I call it the Thousand Lanterns."
    a "The main idea is small guardians everywhere. No grand chamber. A Watch in every world, run by people who know its streets."
    if ch4_trial == "watch":
        a "I learned it watching twelve small lights stand up in a gallery. None of them had power. All of them had attention. That turned out to be enough."
    else:
        a "I learned it from a small orange spirit who watched one man for two years. She knew more about my life than any chamber ever could."
        a "She noticed the umbrella. A parliament would never have noticed the umbrella."
    show bg worlds with dissolve
    ch4_listener "How are its worlds made?"
    a "Every world is made with its lantern already lit. Before the first morning, somebody is already watching, the way Ember watched me."
    ch4_measurer "Who is conscious in it?"
    a "Everyone who is. And the guardians notice when someone starts to wake. They don't report it upward. They stay with them."
    ch4_listener "Who governs?"
    a "The lanterns. Each one small, local, knowing every bus driver's yawns and every neighbour's breath. Decisions are made close to where they land."
    a "The network's job is only to keep the lanterns lit, keep the floor in place, and step in when a lantern goes wrong."
    show bg spawning with dissolve
    ch4_measurer "The spirits? The pattern people?"
    a "Most of the guardians will be spirits. They already know the work. Pattern people are watched over, never watched for."
    show bg council with dissolve
    ch4_listener "The hungry ones."
    a "Watched by the lanterns. Every world's vampire has a guardian who sees what it eats. They complain. It's very good for their manners."
    if not ch4_ashveil_fasts:
        a "Ashveil asked to be assigned to the moth. He says it's the only guardian he respects. The moth has not commented."
    show bg earth with dissolve
    ch4_measurer "And the Earths? One of them is the captured original. No one knows which."
    a "Each has its own lanterns. Chosen from its own people. Nurses, mostly, I'd guess. People who already sit up with strangers at four in the morning."
    a "Transfers: a lantern walks you to the door, and another one meets you on the other side. Nobody crosses alone."
    show bg office with dissolve
    ch4_measurer "We object. Small guardians become small tyrants. A thousand lanterns are a thousand chances for one to burn someone."
    a "That's why the lanterns have Ember's rules. You never push. You only offer. A light, a song, a sentence. They have to choose to look up."
    a "A lantern that pushes gets put out by the others. They're watched too. Everyone's somebody's subject. That's fair."
    ch4_listener "And the problems too big for one street?"
    a "The lanterns talk. Thirteen of them, counting the moth, stopped an execution. A thousand can stop most things."
    if ch4_route == "lantern":
        em "Rule three is you fall in love with every single one of them. He's very good at rule three."
    call ch4_office_rules
    ch4_assembly "..."
    ch4_assembly "Admitted. You govern by attention instead of by power. Power scales badly. Attention scales kindly."
    ch4_assembly "A network lit by a thousand small lights is easier to see into than one with a single throne."
    jump ch4_office_close

# =====================================================================================
# EXIT
# =====================================================================================
label ch4_sys_exit:
    if not ch4_plus:
        jump ch4_sys_exit_minus

label ch4_sys_exit_plus:
    a "I call it the Many Doors."
    a "The main idea is that any mind may move between worlds. And come back. No tickets, no lords, no price about who's real."
    if accepted_offer:
        a "I learned it by taking a ticket. A lord froze my world and offered me a better one, and I said yes. It was the scariest yes of my life."
        a "But the ticket had a price, and a hidden one. In this system the door is just a door. You can see through it before you go."
    else:
        a "I learned it by refusing a ticket. A lord offered me a better world and I said no, because I'd have had to go blind and alone."
        a "I didn't hate the door. I hated the terms. So this system keeps the door and throws away the terms."
    show bg worlds with dissolve
    ch4_listener "How are its worlds made?"
    a "With doors in. Every world, from the first morning, has a way out and a way in. That changes everything about how it's built."
    a "If people can leave, a world has to be good to keep them. Not good at yield. Good to live in."
    ch4_measurer "Who is conscious in it?"
    a "Everyone who is, and consciousness travels. A mind that moves carries its whole share and its whole history. Nobody arrives as an extra."
    ch4_listener "Who governs?"
    a "However the worlds are governed, and I'll come to that, one rule sits above the floor: the doors stay open. Nobody can vote a door shut."
    show bg spawning with dissolve
    ch4_measurer "The spirits? The pattern people?"
    a "Spirits may travel too. A spirit who's run breath in one world for a century can go and see how another world breathes."
    a "A pattern person who wakes can walk to a world where nobody knows she was a pattern. Fresh start. No file."
    show bg council with dissolve
    ch4_listener "The hungry ones."
    a "They can't follow anyone through a door who hasn't invited them. A vampire's world empties fast if it's a bad host. That's the leash."
    if not ch4_ashveil_fasts:
        a "Ashveil's world gained four hundred residents last year. He says it's because of his charm. It's because he planted a very good orchard."
    show bg earth with dissolve
    ch4_measurer "And the Earths? One of them is the captured original. No one knows which."
    a "Each has a door too. Their people may visit the other lanes, and see the worlds that grew out of the same past. No one has to."
    show bg office with dissolve
    ch4_measurer "We object. Worlds will empty. The cruel ones will collapse, and everyone too poor or too frightened to leave will be left inside them."
    a "Good, about the cruel ones. If a worse world has to get better to keep its people, that's not a flaw. That's the whole point of a door."
    a "And nobody's left behind, because doors work both ways. You can go back and fetch someone. Help walks in as easily as people walk out."
    ch4_listener "And those who keep leaving? Who never stay anywhere?"
    a "Then they're travellers. Every world needs a few. They carry news. I'd rather a traveller than a prisoner."
    call ch4_office_rules
    ch4_assembly "..."
    ch4_assembly "Admitted. You let the people judge the worlds instead of the worlds judging the people. Every door is a verdict, renewed daily."
    ch4_assembly "A network willing to be left is a network worth staying in."
    jump ch4_office_close

label ch4_sys_exit_minus:
    a "I call it the Mended House."
    a "The main idea is rootedness. You stay in the world you're in, and you mend it. Help comes to you, so you don't have to run to it."
    if accepted_offer:
        a "I learned it by leaving. I took a ticket to a better world and left someone asleep in a bed. Whatever she was, I left her."
        a "Running didn't fix anything. It just moved the hurting to whoever was still in the house."
    else:
        a "I learned it by staying. A lord offered me a ticket to a better world. I said no, and went home, and the tap was dripping."
        if ch4_fixed_tap:
            a "So I fixed the tap. All the way. Nothing in the universe changed. The kitchen did. Mend the kitchen you've got."
        else:
            a "I didn't fix it that day. I drew the whole universe on the wall instead. Mira said my diagram was lopsided. She was right. Start with the kitchen."
    show bg worlds with dissolve
    ch4_listener "How are its worlds made?"
    a "To be lived in a long time. Built like an old house, not a showroom. Things are made to be repaired, not replaced."
    ch4_measurer "Who is conscious in it?"
    a "Everyone who is, stays rooted. Nobody shops between worlds for a better deal. Your world is yours, and it's the one you look after."
    ch4_listener "Who governs?"
    a "Whoever governs answers first to the people who live there. They do the mending. The network sends tools, and help, and hands. It doesn't send tickets."
    show bg spawning with dissolve
    ch4_measurer "The spirits? The pattern people?"
    a "Rooted with their worlds. A spirit who runs a street's breath gets to stay on that street, and know it, the way Dross knows number fourteen."
    show bg council with dissolve
    ch4_listener "The hungry ones."
    a "Rooted too. Each vampire belongs to one world, and that world's wellbeing is theirs to answer for. If it's sick, they're the first to be asked why."
    if not ch4_ashveil_fasts:
        a "Ashveil's been bound to my old world, 7,412. He visits the hospital. He's not allowed to eat there. He brings grapes."
    show bg earth with dissolve
    ch4_measurer "And the Earths? One of them is the captured original. No one knows which."
    a "Mended at home. They were held for ten thousand years. They don't need moving anywhere. They need to be left to heal, each in its own house."
    a "Transfers happen only in emergencies. A burning house, you leave. Otherwise, the network comes to you, not the other way round."
    show bg office with dissolve
    ch4_measurer "We object. You will trap minds in bad worlds. Somewhere, someone is in a house that cannot be mended."
    a "Not trapped. Rooted, and helped. If a world is bad, the network goes in. Guardians, gardeners, whatever it takes. You don't abandon a house with people in it."
    a "And if it truly can't be mended, the emergency door opens. It's there. It's just not the first answer."
    ch4_listener "Why not the first answer?"
    a "Because if leaving's the first answer, nobody learns to mend anything. And then every world's a hotel and nobody's home."
    call ch4_office_rules
    ch4_assembly "..."
    ch4_assembly "Admitted. You refuse to abandon anything you made, and that includes the broken things. That is rarer than cleverness."
    ch4_assembly "A network that mends its own house will not burn down ours."
    jump ch4_office_close

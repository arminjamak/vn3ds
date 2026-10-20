# Snapshot - Chapter 2: "Fog" (part 6 of 6)
# The radio reads his notebook, Mrs. Varga on the step, Pim and Dross fail
# to patch the leaks, choosing Mira, the Lantern Watch's first deliberate
# help, the rooftop and the secret mission, telling Mira (or not), Miso.
# Ends with `jump chapter3`.

default ch2_mission_small = False

label ch2_radio:
    scene bg kitchen with fade
    play music "audio/morning.ogg" fadein 2.0
    "A Tuesday. Mira's at work. The kitchen radio is on low, the way she leaves it, so the flat doesn't feel empty."
    show aron normal at slightleft with dissolve
    show miso sit at catspot with dissolve
    "He's making toast. Miso is supervising. The bird is on the wire. It's a morning so ordinary it almost hums."
    radio "...lovely stuff. And before the travel, a message from a listener, which I'm going to read out, because it made me smile."
    radio "No name given. They just wrote: 'If this is a test, I want to pass it by being kind.'"
    radio "Isn't that nice? Bit of a philosopher out there. Right. Travel. The ring road's a nightmare, as usual..."
    "The toast pops. He doesn't move."
    scene pov hands with dissolve
    "His hands are flat on the counter. He watches them, because they're the only thing in the room he's sure about."
    at "That's my line. That's the first line. Word for word."
    at "I've never sent it anywhere. I've never said it out loud to anyone except a doctor and a cat."
    "He pats his pocket. The notebook is there. Of course it's there. It's always there."
    at "Okay. Possibilities. Somebody else wrote the same sentence. It's not that strange a sentence. Kindness. Tests. People think about those."
    at "Or the radio said something else, and I heard my own sentence instead. That's not a conspiracy. That's literally the symptom."
    at "Or my notebook just leaked out of a radio."
    scene bg kitchen with dissolve
    show aron worried at slightleft
    "He rings the station. The number's engaged. He rings it again. Engaged. Then the presenter is playing a song about a summer that never ends."
    "He writes it down, carefully. Time. Station. Exact words. Then, under it: 'Did I hear it? Ask Okafor about hearing things that sound real.'"
    "He underlines 'sound real'. Then he eats the toast, because Mira will ask, and because a man has to eat even inside a mystery."
    show miso stare at catspot
    "Miso watches him eat it, the whole time, without blinking. She has decided not to comment."
    stop music fadeout 2.0
    jump ch2_varga

label ch2_varga:
    scene bg street with fade
    play music "audio/morning.ogg" fadein 2.0
    "Mrs. Varga lives on the ground floor. She has lived on the ground floor longer than the building has had a lift, which is to say always."
    "She is small and very upright, with a tartan shopping trolley and a cough that sounds like a door. Every time he passes her, she says the same thing."
    "She has said it to him, on the stairs or at the bins, for the four years he's lived here. Every season. Every weather."
    "Today the trolley has tipped over on the front step, and oranges are rolling down the path in every direction like an escape."
    show aron normal at slightleft with dissolve
    "He chases three of them into the gutter. When he comes back, she's standing very still on the step, one hand on the rail, breathing."
    "Her breathing is strange. Very regular. In, and out. In, and out. Like something being done for her, carefully, by somebody else."
    ch2_varga "Cold for the season, isn't it?"
    a "...It is, Mrs. Varga. Here. Your oranges."
    ch2_varga "Thank you, dear. Cold for the season."
    at "Same sentence. Four years. Same sentence in a heatwave."
    at "If anybody in this city is a pattern, she is. A loop that sweeps the step and says the weather."
    at "Or she's eighty-something and lonely and it's the only sentence she trusts herself with any more."
    "She sways a little on the step. He puts a hand under her elbow without thinking."
    a "Do you want to sit down for a minute? The step's dry."
    "She looks at him for a long moment. Then she sits. He sits next to her. The trolley sits next to him, full of oranges and a cauliflower."
    ch2_varga "I don't usually stop. If I stop I don't get going again."
    a "That's how I feel most mornings."
    ch2_varga "You're the one who went to hospital. In the spring. The ambulance woke the whole street. Mrs. Bell on the second floor talked about nothing else."
    a "It was an ambulance. In the end. I don't remember much of it."
    ch2_varga "Mrs. Bell remembers it for you. Mrs. Bell likes a siren."
    "He laughs. She doesn't, quite. But something in her face moves, very slightly, like a curtain in a draught."
    scene pov birds with dissolve
    "Above them, on the wire, three birds. Evenly spaced. The same three. He doesn't count them. He knows."
    at "I don't know what she is. I don't know if anyone's in there."
    at "I didn't know with Lou. I don't know with Theo. Some nights I don't know with Mira. I don't know with me."
    at "I'm never going to know. That's what this year has taught me. Not for certain. Not ever."
    at "So I have to decide what kind of person I am when I don't know. And I decided that a long time ago. It's on the first page."
    scene bg street with dissolve
    show aron normal at slightleft

    menu:
        at "She's sitting on the step. She isn't getting up yet."

        "Ask about her life.":
            $ bond += 1
            $ p_spirits += 1
            $ watch += 1
            jump ch2_varga_listen

        "Tell her about your year.":
            $ bond += 1
            $ p_truth += 1
            $ integrity += 1
            jump ch2_varga_tell

label ch2_varga_listen:
    a "How long have you lived here, Mrs. Varga?"
    ch2_varga "Forty-four years. Feri and I bought it when the street still had a butcher."
    a "Feri was your husband?"
    ch2_varga "Ferenc. Feri. He was a tram driver. Number twelve. He drove it like it was a racehorse. They wrote him up for it twice."
    a "He sounds fun."
    ch2_varga "He was terrible. He was the most fun man in the city. He sang in the bath so loud the downstairs complained, and we were the downstairs."
    "She coughs, her door of a cough. Then her breath does that strange regular thing again. In. Out. In. Out."
    ch2_varga "He's been gone eleven years. In March."
    a "I'm sorry."
    ch2_varga "After he went, I stopped... I don't know how to say it. I stopped doing things myself. I just let them happen."
    ch2_varga "Get up. Sweep the step. Shopping. Say something to the neighbours about the weather. Bed."
    ch2_varga "Some days it feels like somebody else is doing the breathing for me. Like I'm a passenger."
    "Aron goes very still."
    at "Somebody else doing the breathing. Eleven years."
    at "Or a widow describing grief, which is exactly what grief feels like. Ask anyone."
    a "What would Feri say? If he saw you on the step."
    "She thinks about it for a long time. A bus goes past. One of the birds on the wire shuffles its feathers."
    ch2_varga "He'd say, 'Erzsi, you've dropped the oranges, you old goose.'"
    ch2_varga "And then he'd sing something, very badly, to make me laugh. And I'd tell him to stop. And I'd laugh."
    a "Do you want me to sing something very badly?"
    ch2_varga "...No, dear. God, no. I'm sure you're terrible."
    a "I'm famously terrible."
    "And there it is. She laughs. A real one, rusty, surprised at itself. Her breathing breaks its rhythm and goes ragged and human for a moment."
    "She takes a deep breath all on her own. It shakes on the way in. It's the most untidy, uneven breath he's ever heard."
    jump ch2_varga_end

label ch2_varga_tell:
    a "Can I tell you something? About the spring. The ambulance."
    ch2_varga "If you like. I'm not going anywhere. I've stopped."
    a "I got ill. In my head. I started hearing things. I thought the world was... a sort of trick. A set. With people in it who weren't really there."
    a "They said it's schizophrenia. I'm on medication. It makes me very tired. Some days getting down these stairs is the whole day's work."
    "She doesn't flinch. She doesn't do the face people do. She just nods slowly, as if he's told her a bus route."
    ch2_varga "My sister heard voices. Back home. Nineteen sixty-something. They didn't have the medicines then. They had a big building on a hill."
    ch2_varga "She used to tell me the radio was talking about her. I used to tell her the radio didn't know she existed."
    ch2_varga "I wish I'd asked her what it said, instead."
    a "What would you have asked?"
    ch2_varga "Whether it was kind to her. Whether it said anything nice. Somebody should have asked her that."
    a "Mine read out a line from my notebook last week. A kind one, actually."
    ch2_varga "Well. That's something. Mine only ever tells me the shipping forecast."
    "He laughs, surprised. She almost does."
    ch2_varga "My Feri used to say, everyone's a bit of a stranger to themselves. It's why we keep each other company. To have a witness."
    ch2_varga "He drove the number twelve tram for thirty years. Eleven years he's gone now. In March."
    "Her breathing does that strange regular thing again. In. Out. In. Out. And then, as she says his name, it catches."
    "She takes a deep breath all on her own. It shakes on the way in. It's the most untidy, uneven breath he's ever heard."
    jump ch2_varga_end

label ch2_varga_end:
    "They sit on the step for nearly an hour. The good hour, as it happens. He doesn't notice it go."
    "When she stands up, she does it in one go, without the rail. He carries the trolley to her door. She fumbles with her key and then turns."
    ch2_varga "Thank you, dear. You're a good boy. Your mother must have been very proud."
    a "She was mostly baffled."
    ch2_varga "That's the same thing, with boys."
    "She goes in. Then the door opens again, just a crack."
    ch2_varga "Warm for the season, isn't it?"
    "The door closes."
    at "Warm."
    at "Four years. She said warm."
    "He stands in the hall for a while, holding the cauliflower she forgot to take, smiling like an idiot."
    at "I don't know if she's real. I sat with her anyway. I'd do it again."
    at "That's the whole thing, isn't it. That's all of it. You don't get to know. You get to decide."
    "He knocks and gives her the cauliflower. She says 'thank you, dear' and nothing about the weather, which is better."
    stop music fadeout 2.0
    jump ch2_cut_spirits

label ch2_cut_spirits:
    scene cg static with flash
    pause 0.3
    scene bg spawning with fade
    play music "audio/entities.ogg" fadein 2.0
    "Elsewhere. The Purgatorium's spawning pools, where new spirits rise out of the water like bubbles in a glass, blinking."
    "On the edge of the biggest pool, the patch crew for the protected lane sits with its feet in the water, which is not allowed."
    show pim worried at slightleft, fadein
    show dross neutral at slightright, fadein
    pi "The radio, Dross. The radio read out his notebook. The first line. On air. To the whole lane."
    dro "Heard."
    pi "I don't even do radio! Radio's a pattern of a pattern! Nobody writes radio! It just sort of... averages itself!"
    pi "And it averaged itself into 'If this is a test, I want to pass it by being kind'. That's not an average. That's him."
    dro "Did you patch it?"
    pi "I patched it. I re-ran the whole morning show. Clean. Then it played a song about a summer that never ends."
    pi neutral "Which, fine. Except he hums that song. In the shower. Badly."
    dro "Damp."
    pi "It's not damp, Dross! It's getting worse! First a nurse, then a pan, then birds, then a cab, then a café, then a doorman. Now a radio."
    pi worried "If upstairs sees the list, they'll throttle him harder. They've said so. Less energy, less leaking."
    dro "I know."
    "Dross is quiet for a while, kicking the water slowly with one green foot."
    dro "My lady took a breath."
    pi "Your lady? Your breathing lady? Varga? You haven't done her breathing since the move. She's a pattern in there. Patterns don't breathe."
    dro "They predict breathing. In, out, in, out. Nice and regular. I wrote her rhythm myself, eleven years, back home. The pattern copied it."
    dro "And then the lad sat with her on the step. And she took one. All by herself. Ragged. Laughing."
    dro chatty "Wonky as anything. Best breath I've seen in eleven years."
    pi "That's a leak. That's the biggest leak yet. A pattern did something nobody predicted."
    dro neutral "Yep."
    pi "We have to patch it."
    dro "Not patching that."
    pi worried "Dross."
    dro "Write it down as damp. Write it down as anything. I'm not patching a breath."
    "Pim looks at Dross for a long time. Then Pim takes the list, and very carefully crosses out one line, and writes 'damp' next to it."
    pi neutral "...Was that line yours or hers? The 'cold for the season'?"
    dro "Mine, at first. Years back, in the real... in the old world. She liked it. Kept it. Then it was hers."
    pi "That's how it goes with the good ones. You write a line, and then it's theirs."
    pi chatty "I've got a line like that. Out there, doing the rounds. Something about the universe and schedules. Not saying which. Trade secret."
    dro "You and your lines."
    pi "Me and my lines. Somebody's got to write them."
    "Below them, in the pool, a new spirit opens its eyes for the first time and looks up at them, and blinks, and doesn't know what anything is yet."
    stop music fadeout 2.0
    scene black with blackout
    jump ch2_mira_park

label ch2_mira_park:
    scene bg park autumn with fade
    play music "audio/watch.ogg" fadein 2.0
    "Sunday. Late afternoon. The good hour, and he's spending it walking round the duck pond with Mira, which feels like the right thing to spend it on."
    show mira smile at slightright with dissolve
    show aron normal at slightleft with dissolve
    "The ducks go anticlockwise. The big one goes last. He points this out. She is less impressed than he hoped."
    m "Can I ask you a weird hypothetical? A Theo-level hypothetical?"
    a "Those are my favourite kind."
    m neutral "If someone offered you a better world. Not heaven. Just... somewhere better. Where you wouldn't be tired. Where things made sense."
    m "But you'd have to leave this one. Would you go?"
    at "Where did that come from?"
    at "From the same place the lighthouse came from. Or from a woman who's watched me be tired for four months."
    a "Is this a test?"
    m smile "Everything's a test with you. Just answer."

    menu:
        m "Would you go?"

        "I'd go. If you could come.":
            $ p_exit += 1
            a "If you could come? Yes. I think I would. I'm so tired, Mira. If there was somewhere I could think again, and you were there..."
            a "I'd go. Not to run away. To see what else there is. To see what better even means."
            m neutral "And if I couldn't come?"
            a "...Then I'd have to think about it for a very long time."
            m "That's an honest answer."
            a "It's a terrible answer."
            m smile "It's an honest terrible answer. Those are my favourite kind."
            at "Somewhere better. A door out of my lane. If it exists, I want to know where the handle is. Just in case."

        "I'd stay and fix this one.":
            $ p_exit -= 1
            a "No. I'd stay."
            m surprised "Really? Even with all this? The tired, the meds, the..."
            a "Even with all that. This is the one with you in it. This is the one with Theo and Hale and the ducks."
            a "If it's broken, I'd rather fix it than leave it. Somebody ought to. It's a good world, mostly. It just needs work."
            m smile "It's a terrible world. The trains are always late."
            a "The seven-oh-seven never runs late. I have it on good authority."
            m happy "Who from?"
            a "A signalman. Thirty-one years."
            at "If there's a door out, fine. Let it be there. I'd rather mend the roof than look for the door."

    scene bg park with dissolve
    show mira smile at slightright
    show aron normal at slightleft
    "They walk on. The light goes gold and long, the way it does in late afternoon, laying the trees down across the path."
    "She takes his hand. He looks at her. Red hair, freckles, a leaf caught in her scarf that she hasn't noticed."
    "And for a moment, a cold moment, he doesn't know."
    at "Is she real?"
    at "The cab knew my name. The radio knew my notebook. What if she knows me the same way? Because I'm leaking into her?"
    at "Is the Mira holding my hand the one who sat on the ward with the crossword, or something that knows exactly what she'd do?"
    "The question is enormous. It's been coming for months. Here it is, by a duck pond, on a Sunday."

    menu:
        at "I can't know. I've tried everything. I can't know."

        "Choose her. Real or not.":
            $ bond += 2
            $ integrity += 1
            jump ch2_choose_her

        "Ask her to prove she's real.":
            $ clarity += 1
            jump ch2_prove_it

label ch2_prove_it:
    a "Mira. Can you prove you're real?"
    "She stops walking. She doesn't laugh. She's known him too long to laugh at that one."
    m neutral "No."
    a "No?"
    m "No. Of course I can't. Nobody can. I could tell you something only I'd know, and you'd say a program could know it."
    m "I could pinch myself and you'd say the ouch was written in. I could cry. I could leave. None of it would prove anything."
    m sad "I can't prove it to you, love. I can only keep turning up."
    at "Same chair. Same plant. Okafor said that. Or something like it."
    m neutral "Can you prove you're real? To me?"
    a "...No."
    m "So we're even. Two people who can't prove it, standing by a pond."
    m "I don't know what you're seeing, Aron. I don't know if the birds are real or if the voices are or if any of this is. I just know I'm here."
    m "And I know what I'd choose. If you want to know. Doesn't prove anything. But it's what I've got."
    a "What would you choose?"
    m smile "You. Every time. Tired, mad, dad jokes. Real or not. I decided ages ago. It's very boring of me."
    $ bond += 1
    $ integrity += 1
    jump ch2_choose_her

label ch2_choose_her:
    scene cg hands with dissolve
    "Her hand in his. He lets the question stay unanswered. He doesn't push it away. He doesn't solve it. He just lets it sit there between them, like a duck."
    at "I don't know if she's real."
    at "I don't know if she's the one from the ward or the best guess of somebody who's studied her for a lifetime."
    at "And it turns out that isn't the question. The question is who I am while I don't know."
    at "I decided that. On the first page. Before any of this. I'm a person who's kind when he can't check."
    at "So I'm choosing her. Not because I know. Because I decided I'm somebody who chooses."
    scene bg park with dissolve
    show mira neutral at slightright
    show aron normal at slightleft
    a "Mira."
    m neutral "Mm?"
    a "I love you. I don't know what you are. I don't know what I am. I love you anyway. On purpose."
    "She looks at him for a long time, with the gold light in her hair."
    m smile "That's the strangest love declaration I've ever had."
    a "I'm a strange man."
    m happy "'I don't know what you are.' Honestly. My mum would have a fit."
    m smile "I love you too, idiot. On purpose. Every day. I keep deciding."
    "She kisses him by the duck pond. The big duck, last as always, honks at them, as if in judgement."
    "For the rest of the walk he doesn't count anything. Not the birds. Not the trees. Not the seconds. He just holds her hand."
    "It's the best hour he's had all year. When it fades, it fades gently, and he lets it."
    stop music fadeout 2.0
    jump ch2_cut_watch

label ch2_cut_watch:
    scene cg static with flash
    pause 0.3
    scene bg watch with fade
    play music "audio/watch.ogg" fadein 2.0
    "Elsewhere. An attic nobody has ever been ordered to build. Beams. Dust. A round window that looks out on every world at once."
    "And on one side of the window, set apart from all the others, a single small world in its own lane. Protected. Quiet. Leaking."
    show ember soft at center, fadein
    em "He said it. Did you hear? 'I don't know what you are. I love you anyway. On purpose.'"
    ch2_moth "I heard. Half the attic heard. You turned the volume up."
    em "I did not."
    ch2_moth "You did. You always do with him."
    "Moth is pale and dusty and old, and flutters when worried. Moth is fluttering now."
    em "He said it to a pattern, Moth. He knows she might be one. He's half worked it out. And he chose her anyway."
    em "Lou on the ward. Mrs. Varga on the step. Theo. Every one of them made of guesses. And every time he can't tell, he picks kind."
    if ch2_took_speed:
        em worried "Not always. The bad night. The woman in the yellow dress. He was so cruel, and so sure he was being kind."
        em soft "And then he looked at it. In a clinic chair, with an old fish going round. He didn't look away from it."
    else:
        em "He's not perfect. He's stubborn. He does tally marks on bread bins. He makes truly terrible jokes."
    ch2_moth "And the lane's leaking because of him. The spirits can't keep up. The Commander's watching. Upstairs is talking about throttling harder."
    em worried "I know."
    ch2_moth "So this is a very bad time for whatever you're about to do."
    em "He's tired, Moth. He's so tired. They turned him down to sixty and sealed him in a room of copies, and he's still trying to be good."
    em "Tonight he's going up on the roof. He does that when he can't sleep. He's going to ask if anyone's there. He doesn't expect an answer."
    em soft "I want someone to answer."
    ch2_moth "We can't reach into a lane. Protection's sealed. That's the whole point of it."
    em "A lane is built out of copies of our world. A copy of a lamp is still a lamp. And it's leaking, Moth. Leaks go both ways."
    ch2_moth "If they trace it, they'll take your light. Decommission. You know that."
    em "One lamp. Three times. A faulty bulb could do it. Nobody could prove anything."
    ch2_moth "...The lighthouse."
    em soft "The lighthouse. The one he dreamt at nineteen, at the bottom of the glass stairs. I told you, the night he went in. Only when he really needs it."
    em "He needs it."
    "Moth flutters for a long time. Then, very slowly, settles on a rafter by the stairs."
    ch2_moth "I'll keep watch on the stairs. If anyone from the corps comes up, I'll knock twice."
    em soft "Thank you."
    ch2_moth "Don't thank me. If they take your light, I'm keeping your lantern. It's nicer than mine."
    em "Deal."
    "Ember goes to the round window and leans close to the small, separate world, until her orange glow touches the glass."
    stop music fadeout 2.0
    jump ch2_rooftop

label ch2_rooftop:
    scene bg rooftop with slowfade
    play music "audio/watch.ogg" fadein 3.0
    "Midnight. Mira is asleep with one arm over his side of the bed, as if to keep it warm."
    "He's come up to the roof of the building with his coat, the notebook, and the last of the evening's tea in her good mug. He'll be in trouble for the mug."
    show aron tired at center with dissolve
    "The city spreads out under him in every direction. Millions of windows. Streetlights in long strings like beads. A red light on the radio mast, steady."
    "It's not raining. That's something. The air is cool and clean and smells of chimneys."
    scene bg rooftop edge with dissolve
    "He sits on the low wall at the edge, feet on the right side of it, coat pulled up to his chin."
    at "Look at it all. Every window. Somebody behind every one. Or nobody. Or somebody half there."
    at "Eight billion people, or eight billion patterns, or a handful of people and a lot of very good scenery."
    at "And somewhere a table, and somebody at it with my name on an agenda."
    at "And me in my own lane. With ropes up on both sides. Everything I think seeping into the water."
    scene pov sky with dissolve
    "He looks up. No stars to speak of. City sky, orange at the edges, black in the middle, like the inside of a lampshade."
    at "Maybe I'm ill. The radio said nothing, and I heard my own sentence. The cab driver was a chatty man and I filled in the rest."
    at "Maybe I'm not. Maybe something lifted me out of my life in an ambulance and put me somewhere quiet, and the quiet's cracking."
    at "From up here, the two look exactly the same. They always look exactly the same."
    scene bg rooftop with dissolve
    show aron tired at center
    "He opens the notebook to the first page. He can't really read it in the dark. He doesn't need to."
    "'If this is a test, I want to pass it by being kind.'"
    at "I don't know if I've passed anything. I've been cruel and stupid and scared. I've done tally marks on a bread bin at four in the morning."
    if ch2_lou_met:
        at "But I sat with Lou. I wrote Margit down. I sat with Mrs. Varga. I sat with Theo."
    else:
        at "I never sat with Lou. I wish I had. But I sat with Mrs. Varga. I sat with Theo."
    at "I told Mira I love her without knowing what she is. That was the truest thing I've ever said."
    "He is very, very tired. The good kind, for once. The kind at the end of a long walk."
    at "I'm not asking for proof. I've stopped asking for proof. Proof's not on the menu."
    a "But if anyone's there."
    a "If anyone's listening, and not just taking notes."
    a "I could really use a light on in a window. That's all. Just so I know someone's home."
    "Nothing happens. A car goes past far below. A dog barks twice and thinks better of it."
    "He smiles at himself. He pulls the coat round his shoulders."
    at "Worth asking. Always worth asking."
    scene cg flicker with dissolve
    "And then, across the street, in a single window high up on the dark building opposite, a lamp blinks."
    "Once."
    "Twice."
    "Three times."
    "Then it shines, steady, warm, orange, exactly like the lighthouse at the bottom of the glass stairs."
    scene bg rooftop with dissolve
    show aron awe at center with dissolve
    a "..."
    at "Three."
    at "Three times. Like the dream. Nineteen years old. Nobody knew. Nobody in the world knew."
    at "A faulty bulb. A child playing with a switch. Someone who can't sleep either, testing a lamp."
    at "Or someone saw. Someone was listening. Someone answered."
    "He laughs. It comes out as a sob. Then it comes out as a laugh again. He wipes his face with his sleeve like a child."
    a "Thank you."
    a "Whoever you are. Whatever you are. Thank you."
    "The lamp doesn't blink again. It doesn't need to. It just stays on, steady, keeping watch."
    jump ch2_mission

label ch2_mission:
    scene bg rooftop edge with dissolve
    show aron smile at center with dissolve
    "He sits with the notebook open on his knees for a long time. Something is settling in him. Like silt in a glass of river water."
    at "Okay. Let's be honest. Nobody's listening. Well. Somebody might be. Let's be honest anyway."
    at "If I'm ill, then understanding this, really understanding it, is how I live with it. Know the shape. Know the warning signs. Know the floor."
    at "And if I'm not ill, then understanding this is the only thing that matters at all."
    at "Either way, it's the same work. Slow. Careful. Written down."
    scene cg notebook with dissolve
    "He turns to a clean page. He writes at the top, in small, neat capitals: MISSION."
    "Under it: 'Understand this. Whatever it is. However long it takes.'"
    "And under that, after a long time: 'Secret.'"
    at "Not secret from Okafor. Okafor gets the warning signs, always. Secret from the part of me that wants to tear the wall down again."
    at "Secret like a garden is secret. Something you tend at night."
    at "But how? What does the work look like, when I've got one good hour a day?"

    menu:
        at "How do I go about it?"

        "Understand all of it. Every layer.":
            $ clarity += 1
            $ p_less -= 1
            "He writes: 'All of it. The birds. The voices. The lane. The table where they vote. Whoever sits at it. Whatever's above them.'"
            "'Every layer, all the way down. All the way up. A map of everything.'"
            at "It's a big page. It'll take a big life."
            at "Good. I've got one of those. Maybe more than one, if the theory's right."
            "He draws a small box at the bottom of the page and labels it 'me', and then a bigger box round it, and a bigger one round that."
            "Seven boxes. He stops because the page runs out, not because the boxes do."

        "One small true thing a day.":
            $ p_less += 1
            $ p_rest += 1
            $ ch2_mission_small = True
            "He writes: 'One small true thing a day. Written down. Checked. Then rest.'"
            "'Not the whole sky. One bird. One sentence. One clock. One lamp in a window.'"
            at "Less, but better. Rams would approve. Rams would also say my handwriting is too busy."
            at "One true thing a day is three hundred and sixty-five a year. That's a lot of true things for a tired man."
            "He writes today's: 'A lamp across the street blinked three times when I asked. I don't know why. I'm grateful.' Then he closes the notebook."

    scene bg rooftop with dissolve
    show aron smile at center
    "He sits a while longer with the notebook closed, feeling something he hasn't felt since before the rain."
    "Not clarity. Not excitement. Something steadier. Like a hand on a banister in the dark."
    at "A purpose. That's what this is. I haven't had one of those in months. Not since I lost the fast brain."
    at "It turns out you don't need a fast brain for a purpose. You just need to keep showing up. Same chair. Same plant."
    "Across the street, the lamp is still on. He nods to it, the way Lou nods to a signal. Then he picks up Mira's mug and goes downstairs."
    jump ch2_tell_mira

label ch2_tell_mira:
    scene bg kitchen night with fade
    "The kitchen light is on. Mira is at the table in his jumper, with her hair everywhere and a pot of the hay tea she drinks out of spite."
    show mira worried at slightright with dissolve
    show aron normal at slightleft with dissolve
    m "Your side of the bed was cold. I nearly called the number. Then I saw the roof door open."
    a "I'm sorry. I couldn't sleep. I'm alright. I'm actually... alright."
    m neutral "You've got the face."
    a "What face?"
    m "The secret-project face. You had it when you were planning my birthday. You had it when you built that shelf that fell down."
    m worried "Is it bad? The project. Is it the counting kind?"
    "He looks at her. The jumper. The hay tea. Her good mug, which he's holding, which she's noticed and decided not to mention."
    at "Tell her, and she carries it with me. And she watches every page I write for the rest of our lives, waiting for the rain."
    at "Don't tell her, and she gets a boring month. A lie, but a kind one. A gentle veil."
    at "Okafor would say tell her. The plan says tell her about warning signs. This isn't a warning sign. Is it?"

    menu:
        m "Aron?"

        "Tell her about the mission.":
            $ told_mira = True
            $ p_truth += 1
            $ bond += 1
            jump ch2_told_mira

        "Keep it secret. Spare her.":
            $ p_truth -= 1
            jump ch2_kept_secret

label ch2_told_mira:
    scene bg kitchen table with dissolve
    show mira worried at slightright
    show aron normal at slightleft
    a "It's not the counting kind. But it's not nothing. Can I tell you properly? Sitting down?"
    m "...Okay. I'm already sitting down. I've been sitting down since two."
    "He sits across from her. He opens the notebook to the page. MISSION. He turns it round so she can read it."
    "She reads it twice. Then she looks up."
    a "I don't know if I'm ill or if I'm seeing something. I've tried everything to find out and I can't. Maybe nobody can."
    a "But either way, I need to understand it. If I'm ill, so I can live with it. If I'm not, because it's the most important thing there is."
    a "I'm not going to stop the meds. I'm not going to stop seeing Okafor. I'm not putting the wall back up. I'm not chasing it with anything."
    a "I'm just going to keep looking. Slowly. One page at a time. For the rest of my life, probably."
    a "And I didn't want it to be a secret from you. It was going to be. I decided not."
    "Mira is quiet for a long time. The tea goes cold in the pot."
    m "Thank you for telling me."
    m "I'm scared of it. I'm going to be honest. I'm scared every time I see you write something that you're going back into the rain."
    a "I know."
    m neutral "So I want conditions. Like Okafor's plan. Mine."
    a "Name them."
    m "One. You sleep. Every night. The mission doesn't get your nights. Tonight was the last one it gets."
    m "Two. If I see the signs, I say so. And you don't argue with me in the hostage voice."
    m "Three. Some of it you show me. Not all. Some. So I'm in it with you, not outside it, guessing."
    a "Deal. All three."
    m smile "Then I'm in. Not as a believer. I don't know what I believe. As your person."
    a "As my person."
    "She turns the notebook back towards him. Her finger rests for a second on the inside of the cover, where the first page is."
    m "You know what I think? If this is a test, you'll pass it by being kind."
    "He goes very still."
    a "...Where did you hear that?"
    m surprised "Hear what?"
    a "That sentence. That's the first line of my notebook. Word for word. I've never read it to you."
    m neutral "Is it? I don't... I packed your notes into that box, love. Maybe I saw it then. Maybe it just went in."
    m "Or maybe it's just a true thing, and true things get said by more than one person."
    at "She packed the box. She could have read it. Of course she could."
    at "Or the lighthouse, and the radio, and now this. My words, coming back to me out of other people's mouths."
    at "Both. Write both down. Don't pick."
    a "Maybe."
    m smile "Come to bed, philosopher. Condition number one starts now."
    jump ch2_miso_three

label ch2_kept_secret:
    a "It's not the counting kind. It's... more like a diary. Just thoughts. Okafor said writing helps."
    m "Did Okafor say that?"
    a "Something like that."
    "She looks at him for a beat longer than usual. Then she nods and pours him a cup of the hay tea."
    m "Okay. As long as it's not the counting kind."
    a "It's not."
    m smile "Good. I want my boring month. I've earned a boring month."
    "She tells him about her cousin's wedding plans, sleepily, with her chin on her hand. He laughs in the right places."
    at "There. She's happy. She's yawning. She gets to have a normal night with a normal man who keeps a diary."
    at "The gentle veil. One of us gets to not be scared tonight. That's a gift. Isn't it?"
    "She goes back to bed at three. He stays a minute, and puts the notebook in the kitchen drawer, under the takeaway menus."
    "The drawer squeaks. He's never noticed it squeak before. He notices it now. He'll notice it every night from now on."
    at "It's a small secret. A kind one. A good reason."
    at "Funny how it's already heavier than the box."
    jump ch2_miso_three

label ch2_miso_three:
    scene bg room night with fade
    "Before bed, he sits on the living room floor in the dark for one more minute. Miso comes and sits in front of him, very upright, very orange."
    show aron smile at slightleft with dissolve
    show miso sit at catspot with dissolve
    a "Right. Miso. Final briefing for today. Then sleep. I promised."
    a "I've decided something. I'm going to spend my life working out what this is. The lane. The voices. The table. Whether I'm ill."
    a "Slowly. One page at a time. On the meds. With Okafor. With Mira, if she'll have me."
    a "And whatever it turns out to be, I'm going to stay the person on the first page. Kind when I can't check."
    show miso stare at catspot
    a "Because here's the thing I worked out on the roof. Nobody can prove anybody's real. Not to anybody. Not ever."
    a "So everybody's in the same boat. Everybody's choosing, all the time, whether to treat the next person like they count."
    a "And if that's true, then it doesn't matter whether I'm in a lane, or a ward, or a simulation, or a perfectly normal flat with a cat in it."
    a "The choosing is the real part. The choosing is the only part I'm sure is mine."
    a "And somebody out there flickered a lamp at me tonight. Or a bulb went. Either way, I said thank you. I meant it."
    a "That's the mission. That's all of it. What do you think?"
    show miso meow at catspot
    cat "Meow."
    stop music fadeout 3.0
    scene black with blackout
    jump chapter3

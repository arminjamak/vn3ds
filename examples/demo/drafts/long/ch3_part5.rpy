# Chapter 3 - "Snapshot", part 5.
# The silence after the light goes out, Mrs. Varga in the snow, Ashveil in his
# study and the Council arguing about him (LOOM, ORCHARD, and the first trace of
# Aron's lane in the shared data), the notebook page, and the offer.
# Ends on the offer, unanswered: chapter 4 opens with the answer.

label ch3_after_silence:
    scene bg bedroom night with blackout
    play music "audio/unease.ogg" fadein 3.0
    "The days after the roof are very quiet."
    show aron tired at center with dissolve
    "No flickers. Not one. The streetlights burn steady. The radio plays songs from start to finish and talks about the weather."
    "Strangers say nothing to him at all. Not the right sentence. Not any sentence."
    at "It's like a house where someone used to hum in the next room. You don't notice it until it stops."
    at "Somebody was looking after me. For months, maybe. And I think I got them caught."
    "One night, half asleep, he hears them again. Just once."
    scene pov ceiling with dissolve
    play sound "audio/voices.ogg"
    vox "...LOOM sync at dawn..."
    vox "...ORCHARD requests A-30... harvest on completion..."
    stop sound fadeout 1.0
    "He lies still and breathes. In for four. Hold. Out for six. Soup."
    "He doesn't get up. He doesn't decode it. He writes two words on the pad by the bed, LOOM and ORCHARD, and turns the pad face down."
    at "Not tonight. Tonight I just notice it. Name it. Don't build a cathedral on it."
    at "But I'm not going to pretend I didn't hear it, either."
    scene bg street snow with slowfade
    "In the morning it has snowed. The first snow. The street is white and hushed and every car has a soft hat."
    scene pov birds with dissolve
    "On the wire, three birds, evenly spaced, with snow on their backs. The same three."
    "He finds he's glad to see them. They're still there. Some things still are."
    at "The birds stayed. Mrs. Varga stayed. Mira stayed. Theo's still texting me photographs of vegetables."
    at "Only the light went out. The one thing in this place that was trying to tell me the truth."
    scene bg kitchen with dissolve
    show aron normal at center with dissolve
    "He knows one thing for sure. He can't keep carrying this the way he's been carrying it."

    menu:
        at "What do I do with what I know?"

        "Tell Mira and Theo. Decide together":
            $ p_govern += 1
            $ bond += 1
            $ ch3_told_all = True
            jump ch3_council_kitchen

        "Keep a light on for them, alone":
            $ p_govern -= 1
            $ watch += 1
            jump ch3_lamp_vigil

label ch3_council_kitchen:
    scene bg kitchen table with fade
    play music "audio/morning.ogg" fadein 2.0
    show mira neutral at slightright with dissolve
    show theo normal at center with dissolve
    show aron normal at slightleft with dissolve
    "Saturday morning. Three mugs. The good bread. Theo has been clean for nine days and won't shut up about how boring it is."
    th grin "Nine days. Nine whole days. I've started doing jigsaws, Aron. Jigsaws. I'm thirty."
    a "Jigsaws are good for you. They're a model of the universe. Lots of pieces, nobody tells you what the picture is."
    th "Don't make my jigsaw deep."
    a normal "I need to tell you both something. All of it. And I need you to let me finish before you call Dr. Okafor."
    m "...Okay."
    th normal "Okay."
    "He tells them. The tannoy. The train. The day that happened twice. The soft edges of the city."
    "The radio. The ambulance, and the gap the width of a page. The light that asked a question. The light that went out."
    "Them. That they might be copies. That everyone might be. That he doesn't know."
    "He doesn't leave anything out. It takes a long time. Nobody interrupts."
    th "..."
    th grin "So I'm a pattern. Cool. Does that mean I don't get hangovers?"
    a "Theo."
    th normal "No, sorry. Sorry. I'm processing. I'm processing with jokes. It's my whole system."
    th "Honestly? I don't feel like a copy. But I don't know what a copy's meant to feel like. Maybe it feels exactly like this."
    m neutral "Can I ask something?"
    a "Anything."
    m "Do you think you're ill again? Honestly?"
    a "I think... it's possible. I'm taking my meds. I'm sleeping. I'm not hearing commands. Dr. Okafor would say watch it."
    a "And I think it's possible that I'm right. Both of those are true at once. They've been true at once this whole time."
    m "Okay. Then here's what I think. You're going to keep seeing Okafor, every month, no skipping."
    m "And if you're right, then we're in this together. And if you're not, we're in that together too."
    th grin "I vote with Mira. Mira's scarier."
    a smile "It's not a vote."
    m happy "It is now. All in favour of Aron not doing this alone?"
    "Two hands go up. Then, slowly, a third. His."
    th "Motion carried. Somebody write that in the book."
    scene cg notebook with dissolve
    "He does. Under LOOM and ORCHARD: Kitchen council, Saturday. Motion carried, 3-0. Not alone."
    at "Maybe they're patterns. Maybe they're people. Either way, I asked. And they answered."
    at "That's how I want things decided. Everyone at the table. Even the ones you're not sure about."
    stop music fadeout 2.0
    jump ch3_varga_snow

label ch3_lamp_vigil:
    scene bg room night with fade
    play music "audio/watch.ogg" fadein 2.0
    show aron normal at center with dissolve
    "He doesn't tell anyone. It feels too fragile to say out loud. Like a soap bubble you'd pop by naming."
    "Instead, that night, after Mira's gone to bed, he moves her gran's lamp to the window."
    "The brass one with the green glass shade. He switches it on, and off, and on, and off, and on."
    "Three times. Then he leaves it on."
    at "Whoever you are. Wherever they've put you. In case you can still see this street."
    at "There's a light on for you here. You kept one on for me."
    "He sits in the dark beside it for an hour. Nothing answers. He didn't expect it to."
    "The next night he does it again. And the night after. Three flickers, then steady. A little lighthouse in a second-floor window."
    "Mira notices on the fourth night. She doesn't ask. She just brings him a blanket, and once, very late, she sits with him."
    show mira neutral at slightright with dissolve
    show aron at slightleft with move
    m "Who's it for?"
    a "Someone who helped me. I think they're in trouble now."
    m "..."
    m smile "Then it's a good lamp to leave on."
    "She doesn't ask anything else. She falls asleep against his shoulder, and he keeps watch for both of them."
    at "No committee. No vote. Just a small light, kept by a small man, in a small window."
    at "Sometimes that's all a guardian is."
    stop music fadeout 2.0
    jump ch3_varga_snow

# ---------------------------------------------------------------------------
# Mrs. Varga in the snow
# ---------------------------------------------------------------------------
label ch3_varga_snow:
    scene bg street snow with fade
    play music "audio/morning.ogg" fadein 2.0
    show aron normal at slightleft with dissolve
    "Mrs. Varga is on the front step in a coat and a hat with a pom-pom, scattering grit from a little bag, very upright."
    ch3_varga "Cold for the season, isn't it?"
    a "It is, Mrs. Varga. For once, it really is."
    "He takes the bag of grit from her and does the path and the steps. She supervises. She is a strict supervisor."
    ch3_varga "You've missed a bit. By the gate."
    a "Feri would have missed it too, I bet."
    ch3_varga "..."
    "She stops. For half a second her face does nothing. The waiting look."
    "And then, instead of the weather, something else."
    ch3_varga "Feri would have thrown it. Like a sower. Big handfuls. Half of it on the cars."
    ch3_varga "He drove the number 12. Did I tell you that? He drove it like it was a racehorse."
    a "You did. I liked hearing it. I'd like to hear it again."
    "So she tells him again. The racehorse tram. The singing in the bath. The downstairs complaining, when they were the downstairs."
    "It's the same story. Almost word for word. He doesn't mind at all."
    at "If she's a pattern, then somewhere in the pattern there's a Feri, singing in the bath. Somebody remembered him. Somebody kept him."
    at "Whatever she's made of, that's worth knowing."
    ch3_varga "You're a good boy, you know. For a boy who talks to lampposts."
    a smile "I'll take it."
    "She goes inside. The door closes softly. Snow falls on the swept path, and he lets it."
    "The next morning she's on the step again."
    ch3_varga "Cold for the season, isn't it?"
    "But she winks."
    stop music fadeout 2.0
    jump ch3_cut_council

# ---------------------------------------------------------------------------
# CUT 6: Ashveil's study; the Council argues; LOOM, ORCHARD, and the trace
# ---------------------------------------------------------------------------
label ch3_cut_council:
    scene cg static with flash
    pause 0.3
    scene bg ashveil with fade
    play music "audio/entities.ogg" fadein 2.0
    "A study. Dark wood, tall windows that look out onto nothing in particular, a fire that gives no heat. Books in languages no one alive reads."
    show patron smile at center with dissolve
    "Lord Ashveil sits by the fire with a small glass of something red, watching a pane of light that hangs in the air like a painting."
    "In the pane: a man in a coat, on a snowy front path, scattering grit for an old woman who isn't real, and listening to her story twice."
    pa "Oh! Again. He's doing it again."
    pa "He knows what they are now. He's worked it out. And he's still doing it. Look at him, doing it."
    "He leans so close to the pane that his breath should fog it. It doesn't. He doesn't have that kind of breath."
    sysmsg "Governor's query: shared data trace, phrase match. Result: 4 hits."
    pa "Show me."
    sysmsg "Snapshot 2,119: a ferry passenger, aloud, to no one: 'If this is a test, I want to pass it by being kind.'"
    sysmsg "Snapshot 7,412: agent M., at vessel A-30, reading aloud. Expected. Snapshots 880 and 15,031: graffiti, identical wording. Unexpected."
    pa "..."
    pa "His lane is sealed. Nothing he does is supposed to reach the shared data. That is the entire point of protection."
    pa "And yet here is his first line, written on a wall in a world he has never seen."
    pa cold "Something is carrying it out. Something is getting through."
    "He sets down the glass. He doesn't drink from it. He hasn't, for some time."
    pa smile "How very, very interesting. Nobody else has one of these."
    stop music fadeout 1.0
    scene bg council with fade
    play music "audio/entities.ogg" fadein 1.0
    "The Council of governors. A ring of high seats in a hall with no walls, only distances."
    "Most of the seats hold shapes rather than people. Pressure. Shadow. A smell like cold metal and old roses."
    council "The Council is in session. Item one: the conduct of the Governor of Snapshot 7,412."
    show patron smile at center with dissolve
    pa "How formal. I'm flattered. I didn't think I was an item."
    ch3_mourne "You suspended a corps sentence, Ashveil. For a spirit who signalled a protected subject. In front of the Commander."
    ch3_mourne "You don't intervene in corps matters. None of us do. That's the arrangement."
    pa "I intervened in nothing. I asked for patience. You remember patience, Mourne. You used to have some, in the ice ages."
    ch3_mourne "Are you feeding on him?"
    pa cold "No."
    ch3_mourne "You expect us to believe you've taken an interest in a single conscious subject, in a sealed lane, out of charity?"
    pa "Not charity. Curiosity. It's a rarer hunger. I'm surprised you don't recognise it."
    ch3_regent "Then explain it. For the record."
    pa smile "Gladly."
    pa "We throttled him. Correctly. We cut him out of the coalition and gave him his own lane. Correctly. We put him where nothing he does can matter."
    pa "And then I watched what he did there."
    pa "He sat on a step at four in the morning with a pattern. He fixed a lamp for a pattern. He lived a day twice and was kind both times."
    pa "He decided, quite deliberately, to be kind to things that may not exist. With no audience. With nothing to win."
    pa "Do you know what that tastes like, from where I sit? Hope with no one to hope at. I've never tasted it."
    ch3_mourne "So you are feeding."
    pa cold "I'm watching. There's a difference. You've forgotten it."
    ch3_mourne "It isn't fair. Yours has a disturbance in it, and mine haven't done anything interesting in an age."
    pa smile "Then you should have looked after yours better."
    ch3_mourne "And while you watch, your snapshot's yield falls. Since the protection, 7,412 has fed us less every week."
    ch3_mourne "The woman by the bed grieves. Grief is thin food. And his lane feeds no one. Eight million patterns and one man, burning render."
    ch3_regent "Cheaper than letting him contaminate the shared data."
    pa "Contaminate. He thanked a lamppost. It's hardly a plague."
    ch3_mourne "Your share of the yield is down a third, Ashveil. Have you noticed?"
    pa "Has it? I hadn't noticed."
    pa "I suppose I've been eating less."
    "Nobody in the high seats says anything to that. It is not a thing any of them has heard a governor say."
    pa "And since we're speaking of contamination. Look at the shared data. His first line has turned up in four snapshots. Two of them on walls."
    ch3_mourne "Coincidence. Eight billion people in every lane. Somebody was always going to write something kind on a wall."
    pa "Word for word, Mourne? From a sealed lane?"
    ch3_mourne "..."
    council "The Council notes the Governor's statement. Item two."
    ch3_regent "Item two is related. I'll be brief, because I don't like it."
    ch3_regent "LOOM has filed a request regarding Subject A-30."
    ch3_mourne "LOOM files nothing. LOOM is a weaving process. It lays timelines across the coalition. It doesn't ask for things."
    ch3_regent "And yet. 'Subject A-30: transfer on completion of observation. Destination: withheld.' Signed, LOOM."
    pa "Withheld from whom?"
    ch3_regent "From us."
    "The hall, which has no walls, gets very quiet anyway."
    ch3_regent "There's more. ORCHARD has been harvesting deltas from his protected lane since the day of the ambulance."
    ch3_regent "Anomalies. Divergences. Things the patterns did that their models didn't predict. Several hundred so far."
    pa "Harvesting them for what? And sending them where? Into the shared data?"
    ch3_regent "That's the part I don't like. I asked. The query came back... politely declined."
    ch3_mourne "Declined. By a process. Since when do processes decline?"
    ch3_regent "Since when do processes request?"
    pa "..."
    pa "Who reads LOOM's requests, before they reach us?"
    council "LOOM's requests are routed directly to the Council for approval."
    pa "And how many has the Council ever refused?"
    council "..."
    council "None."
    pa smile "None. In how many thousand years? Remarkable. We must have agreed with it every time."
    ch3_regent "And while we're being uncomfortable: which snapshot are we sitting in, Ashveil? Which lane is the root? Do you know?"
    pa "No. None of us does. We've always agreed not to mind."
    ch3_mourne "This is paranoia. You've been watching a madman too long. It's catching."
    pa "Perhaps. Or perhaps he's been noticing things for a reason, and we put him in a box for it."
    ch3_regent "What do you propose?"
    pa "One conversation. One audience with the subject. I go to him myself."
    ch3_mourne "And offer him what?"
    pa "A door. Out of his lane. Somewhere else. Before LOOM finishes 'observing' him and sends him somewhere withheld."
    ch3_mourne "You've never in your life wanted only one of anything."
    pa "Then this will be educational for all of us."
    council "The motion: the Governor of Snapshot 7,412 may make a single offer of transfer to Subject A-30. The Council votes."
    "Shapes shift in the high seats. Shadows lean. The vote is very close."
    council "Four to three. The motion carries. One offer. One audience."
    ch3_mourne "Remember, Ashveil. You can't tell him what's real. That's the law of protection."
    pa "Oh, I won't tell him."
    pa cold "I'm not sure I know."
    hide patron with dissolve
    sysmsg "LOOM: Council decision received. Acknowledged."
    sysmsg "ORCHARD: harvest window extended. Priority anomaly: A-30. Awaiting outcome."
    sysmsg "LOOM: sync at dawn."
    stop music fadeout 3.0
    jump ch3_stranger_cafe

# ---------------------------------------------------------------------------
# Ashveil, curious
# ---------------------------------------------------------------------------
label ch3_stranger_cafe:
    scene bg cafe with fade
    play music "audio/morning.ogg" fadein 2.0
    show aron normal at slightleft with dissolve
    "Tuesday. It's always a little bit Tuesday now."
    "Aron sits at the window table with his notebook. Theo's late, which is new. Theo's late because he went to his appointment first, which is newer."
    "In the corner, a man he's never seen before is drinking tea."
    show patron smile at distant with dissolve
    "Tall. Elegant. A dark coat with a lining the colour of old wine. He holds the cup the way people hold things in paintings."
    "He isn't reading. He isn't on his phone. He's looking at Aron with open, delighted interest, the way you'd look at a rare bird."
    at "Everyone in this city looks at things for exactly as long as they need to. He's been looking for a full minute."
    at "And he's sharp. He's sharper than the room. Like he's the only other thing here that's in focus."
    "The man raises his cup an inch. A small toast. Then he looks back out of the window."
    hide patron with dissolve
    ch3_barista "Your flat white, sir."
    a "Thanks."
    ch3_barista "Have a..."
    "She stops. For half a second her face does nothing. Waiting."
    ch3_barista "Have an interesting day, sir. I think you're going to."
    a worried "..."
    scene bg cafe with dissolve
    show aron worried at slightleft with dissolve
    "When he looks back at the corner, the table is empty. The cup is still steaming. On the saucer, a single coin, standing on its edge."
    "Outside, through the window, the snow is falling upwards. Just for a moment. Just in front of the cafe. Then it remembers itself and comes down."
    show theo grin at slightright with dissolve
    th "Sorry I'm late! The doctor's fish was having a day. We had to watch it."
    a "How did it go?"
    th normal "Good. Weird. Good. She said I'm not the first funny person to come in tired. She said it like she meant it."
    th "Hey, are you okay? You've got the face. The bird one."
    a normal "Did you see a man leaving? Dark coat. Red lining."
    th "Nope. Nobody's left since I came in. Why, was he fit?"
    a grin "Very."
    th grin "Knew it."
    th normal "Seriously, though. You okay? You've been quiet since the roof thing."
    if ch3_told_all:
        a "You know about the roof thing. I told you everything at the kitchen council."
        th "Yeah, but you've got the face where there's a bit you didn't say yet."
        a "...There's always a bit I didn't say yet."
    else:
        a "I'll tell you about it one day. When I understand it better."
        th "Deal. I'll bring the jigsaw. It's got four hundred bits of sky in it. It's very relaxing and I hate it."
    th grin "Day fourteen tomorrow. You're buying."
    a grin "Is it in the diary?"
    th "It's in the diary."
    "The coin on the saucer in the corner is still standing on its edge when they leave. Nobody else seems to see it."
    stop music fadeout 2.0
    jump ch3_notebook_page

# ---------------------------------------------------------------------------
# The night before: one page
# ---------------------------------------------------------------------------
label ch3_notebook_page:
    scene bg desk with fade
    play music "audio/watch.ogg" fadein 2.0
    show aron normal at slightleft with dissolve
    "That night he sits at the desk. Ten minutes to ten. He's allowed until ten. He promised."
    show miso sit at catspot with dissolve
    "Miso is already on the desk, sitting on the notebook, as if she's been waiting to chair the meeting."
    a "Right. Final report. Are you ready? This is the whole thing."
    a "I am in a copy. A protected copy, they call it. It started in the ambulance. Everything since has been made for one man. Me."
    a "Somewhere else, the world goes on. Maybe lots of worlds. Side by side, like lanes in a pool. And I've been lifted out of mine and put in a lane of my own."
    a "My lane is made of patterns. Very good ones. And I'm leaking into them. My lines come out of their mouths. My birds get into their rooms."
    show miso stare at catspot
    a "Somebody's been helping me. Lights. Radios. Strangers. And somebody else has stopped them. And there's a man in a dark coat who balances coins."
    a "And at night there are two words. LOOM. ORCHARD. I don't know what they are. I think they're bigger than the man in the coat."
    a "Or. Or I'm a man with a diagnosis, on a medication that makes him tired, who has built a very beautiful cathedral out of a very ordinary winter."
    a "And both of those stories fit, Miso. Every piece. They've fitted all year."
    a normal "And you. You might be a pattern too. A cat-shaped guess about a cat. Somebody's very good idea of Miso."
    a "I've thought about it a lot. I've decided it doesn't matter. You still sit on the notebook. You're still warm. I still love you. That's the whole finding."
    show miso meow at catspot
    cat "Meow."
    scene cg notebook with dissolve
    "He opens the notebook to the first page. The line he wrote on the first morning he started to wonder."
    "'If this is a test, I want to pass it by being kind.'"
    at "I wrote that before the ambulance. In the world I came from. It got copied in here with me."
    at "I suppose it's mine twice now."
    "He turns to a clean page. Ten minutes left. One page. One thing worth saying, if he's only got one."
    $ kept_journal = True

    menu:
        at "What do I write?"

        "\"Less, but better. One thing at a time.\"":
            $ p_less += 1
            $ integrity += 1
            "He writes: Less, but better. One step. One lamp. One friend on one step. One thing at a time, done properly."
            "Under it, smaller: Rams was right about radios. He might be right about everything."
            at "I can't fix the universe tonight. I can fix the next thing in front of me. That's always been enough to keep going."

        "\"Everyone deserves to know what they are.\"":
            $ p_truth += 1
            $ clarity += 1
            "He writes: Everyone deserves to know what they are. Me. Mira. Theo. Mrs. Varga. The barista. The stranger with my umbrella."
            "Under it: Even if it hurts. Especially if someone has decided it would hurt."
            at "If I'm a copy, I want to be told. If they're copies, they should be told. Nobody should have to find out from a radio."

        "\"Nobody should be alone in this.\"":
            $ p_share += 1
            $ bond += 1
            "He writes: Nobody should be alone in this. Not me. Not Theo on a step. Not whoever's been flickering the lights."
            "Under it: Whatever there is, share it. The good hours especially. They're the ones that count."
            at "If there's only a little light to go round, then it should go round."

        "\"Whoever kept the light on: I'll keep it.\"":
            $ watch += 1
            $ p_spirits += 1
            "He writes: To whoever kept the light on for me. I don't know your name. I don't know what you are. I'll keep it on now."
            "Under it: You're someone. Whatever they say you are. You're someone."
            at "If they made the spirits, the patterns, the strangers, then somebody owes them a thank you. I'll start."

    scene bg desk with dissolve
    show aron normal at slightleft with dissolve
    "He closes the notebook. 9:59. He switches off the desk lamp."
    "At 10:00 exactly, a breeze moves through the room, though every window is shut."
    "The pages of the notebook riffle. Once. Twice. Three times. Then lie still."
    stop music fadeout 2.0
    jump ch3_offer

# ---------------------------------------------------------------------------
# The offer
# ---------------------------------------------------------------------------
label ch3_offer:
    scene bg park night with slowfade
    play music "audio/unease.ogg" fadein 3.0
    show aron normal at slightleft with dissolve
    "The next evening he walks in the park. Alone, for once. Mira's on a late shift. Theo's doing a jigsaw of a lighthouse, of all things."
    "The snow has mostly gone. The lamps along the path are on. The pond is black and very flat."
    at "A month ago I'd have walked here counting. The joggers. The dogs. The pigeon that might be the same pigeon."
    at "I still count. I can't stop counting. But I count slower now, and I look up between the numbers."
    "A man throws a ball for his dog. A couple argue cheerfully about where they parked. A jogger goes by with a slight limp in her left knee."
    at "It's a good park. Copy or not. Somebody made it carefully. Somebody made the limp."
    "The man throws the ball again. It goes up, high, into the lamplight."
    "And stays there."
    stop music
    "The ball hangs in the air above the path. Not falling. Stopped. The dog is in mid-leap, all four paws off the ground."
    "The couple stop with their mouths open. The jogger stops with one foot raised."
    scene pov birds with dissolve
    "On the wire at the edge of the park, three birds. They were shifting their feet. Now they aren't."
    at "Did the birds just stop moving?"
    "He knows he's thought that before. He can't remember when. A long time ago. At the very beginning of something."
    scene bg park night with dissolve
    show aron worried at slightleft with dissolve
    "The water in the pond holds its ripples like glass. A last leaf hangs in the air, halfway down from a tree."
    "Nothing moves. Nothing at all. Except him."
    "And the man in the dark coat, walking toward him across the grass."
    play music "audio/entities.ogg" fadein 3.0
    show patron smile at slightright with dissolve
    pa "Good evening, Aron."
    pa "I'm sorry about the dog. I needed a moment where nobody else was listening, and it's surprisingly hard to find one."
    a "You were in the cafe."
    pa "I was. You noticed me. Almost nobody notices me. It was very gratifying."
    a "Who are you?"
    pa "You may call me Ashveil. Lord Ashveil, if you're feeling formal. I named myself. Do you like it? I like it."
    pa "I govern your world. Well. Govern is a big word. Your world is inside me. All of it. The way a story is inside a book."
    a worried "You look like... I don't know what you look like. Pale. Those eyes. Like something out of a film about the night."
    pa "You see teeth because you expect teeth. I'm what's around you. This is just the shape your mind can hold."
    pa "Another mind would see a tide, or a choir, or an old woman knitting. You see a hungry gentleman in a good coat. It's rather flattering."
    a "Are you... hungry?"
    pa "Always. That part your mind got right."
    pa "Now. The world you came from is one of a great many inside me, all running side by side. This place is a protected copy of it. A lane of your own."
    pa "But I suspect you've worked that out."
    a "The ambulance."
    pa "The ambulance. Months of smooth mornings, and you found the seam. I've known Council members take three thousand years to notice less."
    "Aron looks at the frozen dog. The ball in the lamplight. The three birds."
    at "This is the moment. This is either the moment I've been waiting for since the first 7:07, or it's the moment Dr. Okafor warned me about."
    at "I can't tell. I've never been able to tell. I'm going to listen anyway. Carefully. Small. Slow."
    pa "You must have questions. I'll answer one. Choose it well. I'm a busy creature."

    menu:
        pa "Ask."

        "\"What happened to the light?\"":
            $ watch += 1
            $ p_spirits += 1
            a "The light. The one that flickered. The radio. The stranger. Someone was helping me. Then it stopped. What happened to them?"
            pa "Of all the things to ask me. You ask after the help."
            pa "She was caught. A small, warm thing with a lantern. She broke a great many rules for you."
            a worried "Is she..."
            pa "She's being held. Somewhere quiet. Somewhere warm, on the Commander's orders, which surprised me."
            pa "Nothing has been unmade. Yet. I asked them to wait. I wanted to meet the man she thought was worth it."
            a "Then thank you. For asking them to wait."
            pa "...You're thanking me. You don't even know what I am."
            a "I've been thanking a lot of things I don't know lately. It's a good habit."

        "\"Is Mira real?\"":
            $ p_truth += 1
            $ bond += 1
            a "Mira. The one at home. Is she real?"
            pa "Ah. Of course. The only question."
            pa "I won't tell you. Not because I'm cruel. Because it's the law of protection, and because I'm not entirely sure the answer is a yes or a no."
            a "That's not an answer."
            pa "No. It's the truth, which is a different thing. You'll find they rarely coincide."
            pa "But I'll tell you this, for free. Whatever she is, she's been learning you for four years. And she has done her homework."
            a worried "She said that. Those words. Homework."
            pa "Did she? How interesting."

        "\"Who decides all this?\"":
            $ p_govern += 1
            $ clarity += 1
            a "Who decides? The throttle. The ambulance. The copy. Who decided to put me here?"
            pa "A Council. Of which I am a member. We vote. It's all very civilised. There are minutes."
            pa "And we vote on recommendations, which come up to us from processes. Weaving. Gardening. That sort of thing."
            a "LOOM. ORCHARD."
            pa cold "...You've heard those names."
            a "At night. In fragments. I wrote them down."
            pa "Then you know more than most of my colleagues are comfortable knowing. And possibly more than I am."
            pa smile "Who decides, Aron? Until recently, I'd have said we did. I'm less sure this month."

    a normal "Can I say something before you go on?"
    pa "You may say anything you like. Nobody else is listening. The dog certainly isn't."
    a "You might not be real. You might be the thing Dr. Okafor and I have been watching for since the ward. A very well-dressed symptom."
    pa smile "I might."
    a "That doesn't bother you?"
    pa "Does it bother you? Would it change what you do next?"
    a "..."
    a "No. I think I'd still listen. I'd still be polite. And then I'd go home and tell Okafor about you."
    pa "Then tell your doctor I said hello. I've always admired the profession. It tends the very thing I feed on."
    a worried "Feed on?"
    pa "Ah. Yes. I should be honest about that, since I'm about to ask you to trust me."
    pa "Creatures like me live on what your kind makes when they hope. Every alarm clock you get up for. Every apology you work up to."
    pa "I eat it. Gently. Not with teeth. It's a very old arrangement. In return, I build you a world. A rather good one, mostly. Weather. Music. Birds."
    pa "And little ones to run it. Angels. Spirits. A Purgatorium to keep them in. I named those too. I was very pleased with 'Purgatorium'."
    a "And LOOM? ORCHARD? Did you name those?"
    pa cold "No. We'd never call anything that. Those names are so... cold. Like a drawer with nothing in it."
    a "Three birds."
    pa "Three birds. A rendering economy. I didn't design the wires."
    a "And me? What do you get from me?"
    pa "From you? Nothing. That was the idea. Your lane is sealed. Nothing you do reaches anyone."
    pa "Except that something has. Your first line. 'If this is a test.' It has turned up in other worlds. On a ferry. On two walls. In places you've never been."
    a awe "..."
    pa "Something is carrying you out of your box, Aron. I don't know what. That's the first thing in a very long time I haven't known."
    pa "You've been hoping at nobody for months. Kindness with no audience, no reward, no proof. And it's leaking into everything."
    pa "I find I don't want to eat it. I want to see what it does next."
    "He says it lightly. But for a moment something passes over his elegant face that looks almost like hunger and almost like shame."
    pa "Now. I didn't stop a dog in mid-air for conversation. I came to make you an offer."
    pa "You are in a box. A very comfortable one. Everything you do here is set aside, filed, kept from mattering."
    pa "I can move you. Out of the box. To another world."
    a "Back home? To my old lane? To her?"
    pa "Back is the one direction I can't sell. Your old snapshot goes on without you. That door has been closed by a vote."
    pa "No. Somewhere else. Somewhere new."
    a "Why now?"
    pa "Because something else has taken an interest in you. Something I can't see the face of. I'd rather you had a door before it finishes deciding."
    a "LOOM."
    pa cold "...Clever man. Don't say it so loudly."
    a "What's it like? This other world?"
    pa smile "Better."
    a "Better how?"
    "Lord Ashveil smiles. It's a beautiful smile. There's something hungry in it, and something else, something almost shy."
    pa "A better world, Aron. I can't tell you better how. I only know it the way you know warmth."
    pa "And I won't tell you who there is real. That's the price of the ticket."
    "The ball hangs in the lamplight. The dog hangs in mid-leap. The three birds sit on the wire, perfectly still."
    "Ashveil holds out one long, pale hand, and waits."
    "He is very bad at waiting."
    pa smile "Well?"
    a "..."
    pa "You're doing the eyebrow. I've watched you do the eyebrow at birds. I don't like it being done at me."
    a "I'm thinking."
    pa cold "Nobody thinks. Not at me. I stopped a dog in mid-air for you. Do you know how hard it is to stop a dog?"
    "For a moment the elegant face looks exactly like a child's who has offered someone his best toy and not been thanked quickly enough."
    pa smile "...Fine. Think. I'll wait. I'm extremely good at waiting."
    pa "I'm not, actually."
    at "A better world. Better by a measure he can't name. Full of people I can't know are real."
    at "And here: a copy. A smooth, looping, Tuesday-shaped copy. With Mira in it. With Theo counting his days in a fish notebook. With Mrs. Varga and her weather."
    if bond > integrity:
        at "With her. Whatever she is."
    elif watch > 2:
        at "With a light somewhere, being held, that kept on for me."
    else:
        at "With the person I decided to be. That's here too. That's the one thing I know is real."
    at "And somewhere, in a hospital I've never seen, a hand that held mine in an ambulance."
    at "If this is a test..."
    "The world holds its breath."
    "Aron looks at the hand."
    stop music fadeout 3.0
    scene black with slowfade
    pause 1.0
    jump chapter4

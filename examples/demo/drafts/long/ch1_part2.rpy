# Snapshot - Chapter 1, "The Morning Render" (part 2 of 4)
# The park and the lighthouse, Pim and Dross, dinner, Miso hears about
# Bostrom, the notebook, the first tests, and Seraphiel raising the flag.

label ch1_park:
    scene bg park autumn with slowfade
    play music "audio/morning.ogg" fadein 2.0
    "In the afternoon they walk in the park with the parcel, because Mira wants to wrap it on a bench in the sun."
    "She says presents wrapped outdoors have better luck. She says her grandmother said so. Her grandmother said a lot of things."
    show mira happy at slightleft with dissolve
    show aron normal at slightright with dissolve
    m "Hold this corner. No, the other corner. Your other other corner."
    a "I only have two corners. I'm a man of limited corners."
    m smile "Hold the tape, then. You're the tape man."
    "The paper is dark blue with small gold stars. Mira folds it with nurse's-daughter precision, hospital corners on a scarf box."
    a "What's in it?"
    m "A scarf. Green. She'll say it's too much and wear it every day until it falls apart."
    a smile "Like you with my hoodie."
    m happy "Your hoodie is a family heirloom now. It's been decided."
    "A gust shakes the trees. Leaves come down around them, yellow and slow."
    scene pov sky with dissolve
    "Aron tips his head back and watches one leaf fall the whole way down out of the sky, spinning."
    at "If you were going to fake a world, leaves would be the hardest part. Every one different. Every fall different."
    at "Unless you didn't fake every leaf. Only the ones somebody's looking at."
    at "That's how games do it. They don't draw what's behind you. Why would you, if nobody's looking?"
    scene bg park with quick
    show aron worried at slightright with dissolve
    "He turns his head sharply to look behind him."
    "Trees. A path. A jogger in a red jacket. Leaves falling there too, as if they'd been falling all along."
    show mira neutral at slightleft with dissolve
    m "What?"
    a "Nothing. Thought I heard something."
    m "You've been doing that all day. Looking at things like they owe you money."
    a "Have I?"
    m "Theo texted me."
    a "Theo texted you?"
    m smile "He said, and I quote, 'your boyfriend is counting birds, please administer cuddles'."
    a "Traitor."
    m "He's worried about you. In his Theo way. With emojis."
    "She tapes the last corner and sets the present on the bench between them. Then she turns to him, properly."
    m neutral "So. Are you counting birds?"
    a normal "...A little."
    m "How many?"
    a "Three. It's always three."
    "She doesn't laugh. She looks up at the trees, as if checking."
    m "I sometimes think you look at the world like it's a puzzle box. Like if you turn it right, a little drawer opens."
    a smile "Isn't that what you're supposed to do with puzzle boxes?"
    m smile "Sure. But you also get to just hold it. It's a nice box. Somebody made it nicely."
    "She leans her head on his shoulder. Her hair smells of apples and the cold."
    m neutral "This morning in the kitchen you had this look. Just for a second. Very far away."
    m "Like you were at the lighthouse at the bottom of the stairs."
    "Aron goes very still."
    play music "audio/unease.ogg" fadein 1.0
    scene bg staircase with slowfade
    at "The lighthouse at the bottom of the stairs."
    at "I was nineteen. A dream. A staircase made of glass going down and down into a calm sea."
    scene bg lighthouse with dissolve
    at "And at the bottom, under the water, a lighthouse. Its light blinked three times. Then I woke up."
    at "I never told anyone. Not my mother. Not Theo. Not Mira. I never even wrote it down."
    at "I didn't tell anyone because it felt like it was mine. The only thing that was completely mine."
    scene bg park autumn with dissolve
    show mira neutral at slightleft with dissolve
    show aron worried at slightright with dissolve
    a "What did you say?"
    m "Hm?"
    a "Just now. The lighthouse."
    m "Did I say lighthouse?"
    a "You said 'the lighthouse at the bottom of the stairs'."
    m "..."

    menu:
        at "How could she know?"

        "Ask her how she knows that":
            $ clarity += 1
            jump ch1_park_ask

        "Let it go. Kiss her.":
            $ bond += 1
            jump ch1_park_kiss

        "Tell her the whole dream":
            $ p_truth += 1
            $ bond += 1
            $ ch1_told_dream = True
            jump ch1_park_tell

label ch1_park_ask:
    a worried "Mira. Where did that come from? The lighthouse. The stairs."
    m surprised "I don't know. It's just... a thing to say? Like 'miles away'. 'Away with the fairies'."
    a "That's not a thing people say. 'At the lighthouse at the bottom of the stairs.' Nobody says that."
    m neutral "Then maybe I read it somewhere. A poem or something. Why does it matter?"
    a "Because I had a dream. Years ago. Exactly that. A lighthouse at the bottom of a glass staircase."
    a "And I never told you. I never told anyone."
    m surprised "..."
    m worried "Okay, that's a bit spooky."
    a "A bit?"
    m "Maybe you did tell me and you forgot. Maybe you talk in your sleep. You do talk in your sleep, you know."
    a "Do I?"
    m smile "Last week you said 'the spoons are unionising'. Very clearly. With conviction."
    a "That's... plausible, actually."
    m neutral "So maybe you said 'lighthouse' one night, and it went into my head, and it came out today."
    a "Maybe."
    "She takes his hand. Her fingers are cold and real and slightly sticky from the tape."
    m worried "Hey. You look scared."
    a "I'm not scared. I'm interested."
    m "Your hand is shaking, interested man."
    at "She has an explanation. It's a good explanation. Sleep-talking. Memory. Coincidence."
    at "I want it to be true so badly I can feel it in my teeth."
    at "But the light blinked three times. She didn't say that part. If I'd said it in my sleep, wouldn't I have said that?"
    jump ch1_park_end

label ch1_park_kiss:
    a normal "...Nothing. It's a nice phrase."
    m smile "Is it? I don't know where it came from. It just arrived."
    "He turns and kisses her, quickly, before the question can grow any bigger in his chest."
    "She laughs against his mouth, surprised, and kisses him back."
    m happy "What was that for?"
    a smile "For saying nice phrases."
    m "I should say nice phrases more often."
    a "You should."
    "They sit with the present between them and watch a dog chase a stick it has no chance of catching."
    "The question doesn't go away. It goes quiet, the way a cat goes quiet under a bed. Still there. Waiting."
    at "She couldn't know. Nobody could know."
    at "But I'm sitting here with her head on my shoulder, and it's warm, and I choose this. Right now I choose this."
    at "The lighthouse can wait. It's been waiting eleven years. It's good at waiting."
    jump ch1_park_end

label ch1_park_tell:
    a normal "Mira, I've never told anyone this."
    m surprised "Oh. Okay. Big one?"
    a "Medium. Medium-strange."
    scene bg staircase with dissolve
    a "When I was nineteen I had a dream. I was standing at the top of a staircase. It was made of glass."
    a "It went down and down, into the sea. The sea was completely calm, like a mirror. Not a wave."
    a "I walked down the stairs and went under the water, and I could breathe, and it didn't feel strange."
    scene bg lighthouse with dissolve
    a "And at the bottom there was a lighthouse. Under the sea. And its light blinked. Three times."
    a "Then I woke up. And for a whole day I felt like somebody had told me a secret and I'd forgotten what it was."
    scene bg park autumn with dissolve
    show mira neutral at slightleft with dissolve
    show aron normal at slightright with dissolve
    m "..."
    m "And you never told anyone?"
    a "Never. It felt like... mine. Like if I said it out loud it'd get worn out."
    m worried "Then how did I know?"
    a "That's what I'm asking."
    "Mira is quiet for a long time. She picks at the tape on the present."
    m neutral "I don't know. It just came into my mouth. Like I'd always known the phrase."
    m "Maybe you talked in your sleep. Maybe you said it one night and I heard it and kept it."
    a "Maybe."
    m smile "It's a beautiful dream, though. I'm glad you told me. I'm glad it's not only yours anymore."
    a "You don't think it's worn out now?"
    m "No. I think now there are two of us keeping it. That's sturdier."
    at "Two of us keeping it. If anyone else had said that I'd have found it cheesy."
    at "She says it and it holds weight. Like a load-bearing wall."
    jump ch1_park_end

label ch1_park_end:
    stop music fadeout 2.0
    scene bg street rain with dissolve
    show mira neutral at slightleft with dissolve
    show aron normal at slightright with dissolve
    "They walk home as the sky clouds over. At the corner, the first drop of rain lands on Aron's wrist."
    "He looks at his phone. 18:40."
    at "'Rain by evening. That's what they said.'"
    m "Told you it'd rain."
    a "You did."
    m smile "I'm always right about weather. It's my superpower. That and your hoodie."
    "On the wire above them, three birds sit in the rain, evenly spaced, watching it begin."
    scene cg static with flash
    pause 0.3
    jump ch1_cut_purgatorium

# ---------------------------------------------------------------------------
# CUT 2: the Purgatorium. Pim and Dross on shift seven.
# ---------------------------------------------------------------------------
label ch1_cut_purgatorium:
    scene bg spawning with fade
    play music "audio/entities.ogg" fadein 2.0
    "Far below every world, or beside it, or underneath it like a basement under a hundred houses, there is the Purgatorium."
    "In its shallow pools, little lights are being born. Some are learning to blink. Some are learning to walk to the fridge."
    scene bg purgatorium with dissolve
    "It is grey and soft and endless, and it hums with breathing. Not one breath. Millions. In and out, in and out."
    show pim chatty at slightleft, float
    pi "Shift seven, kitchen talk, coming in hot! Okay. Okay okay okay. Queue's full."
    pi "'Lovely morning for it.' 'Can't complain.' 'Rain by evening.' 'Did you sleep okay?' Love these. Classics."
    show dross neutral at slightright, fadein
    dro "Stop narrating your queue."
    pi neutral "I'm not narrating, I'm warming up. You have to warm up the voice, Dross. It's a craft."
    dro "It's a list."
    pi chatty "It's an ART. Do you know how hard it is to make 'can't complain' sound like a man with a knee?"
    dro "Do you know how hard it is to keep Albers breathing for eleven years without a day off?"
    pi neutral "...Okay, that's also hard."
    dro "Two and a breath. Two and a breath. Eleven years. You know what he gave me? Not a thank-you. A cough."
    pi "He doesn't know you're there."
    dro "Nobody knows we're there. That's the job. You blink for them, you breathe for them, you walk them to the fridge."
    dro "And they think they did it."
    pi chatty "Most of them did do some of it! Half of them are at least a bit there. That's the fun bit."
    pi "Like the girl. Mira. She's all there. Fully conscious. But even she runs on autopilot sometimes. Everyone does."
    pi "'Coffee's on.' Mine. 'Did you sleep okay?' Mine. Slipped it in when she was thinking about something else."
    pi neutral "He caught that one, actually. 'You were there.' Ha. Fair. Bad placement. My fault."
    dro "You like her."
    pi neutral "I like everyone I talk for. It's hard not to. You live in someone's mouth for a while, you get fond."
    dro "Mm."
    "Dross's light flickers. Somewhere, in a city, a hundred people take a step at exactly the same time."
    dro worried "We had a problem today."
    pi worried "I know. I know. 'Lovely morning for it'. The batch went out to the whole east district. Twice."
    dro "To the same man."
    pi "To the same man. The subject. A-30. The one the angels keep pinging us about."
    dro "He noticed."
    pi "He did NOT. He... okay, he made a face. People make faces."
    dro "His feet stopped at the crossing. I don't watch words. I watch feet. His feet stopped."
    pi chatty "Feet stop all the time! Feet are notoriously stoppy!"
    dro neutral "Pim."
    pi neutral "Yeah."
    dro "The park. This afternoon. 'The lighthouse at the bottom of the stairs.'"
    pi "..."
    dro "Was that line yours or hers?"
    pi worried "Not mine."
    dro "You're sure."
    pi "I had 'are you cold?' queued. It's right there. Look. Unsent. 'Are you cold?' I was going to do a little shiver with it."
    dro worried "Then it was hers."
    pi "It can't have been hers. She can't know that. That's in HIS file. That's archive-level. Nobody reads that."
    dro "Somebody read it."
    pi "..."
    "In the grey hum of the Purgatorium, the two small lights drift closer together, the way people do when it's cold."
    pi worried "Should we tell the angels?"
    dro neutral "Tell them what? That a conscious woman said a sentence? They'll say 'good, that's what conscious women do'."
    pi "Right. Right. Totally normal. Totally fine."
    dro "Totally fine."
    pi "...Dross?"
    dro "What."
    pi "Do you ever wonder who writes OUR lines?"
    dro "No."
    dro worried "...Get back to work. Albers is about to cough."
    stop music fadeout 2.0
    jump ch1_dinner

# ---------------------------------------------------------------------------
# Saturday night. Pasta, and Mira's mum on the phone.
# ---------------------------------------------------------------------------
label ch1_dinner:
    scene bg kitchen night with slowfade
    play music "audio/morning.ogg" fadein 2.0
    "Back home, the kitchen windows steam up while the pasta water boils. Rain taps at the glass like it wants to come in."
    show mira smile at slightright with dissolve
    show aron normal at slightleft with dissolve
    "Mira sits on the counter, which she's not allowed to do, with the phone on speaker beside her. Her mum is singing to herself."
    "It's her mum's birthday. Her mum is singing her own birthday song, because, she says, nobody else does it properly."
    m happy "Mum. Mum. You can stop now. We get it. You were born."
    "Over the speaker, her mum laughs and asks if Aron is feeding her properly."
    a "I'm making pasta, I promise. With a sauce. The sauce has vegetables in it. Some of them are green."
    "Her mum says that's acceptable. Then she asks Mira, in a lower voice she thinks he can't hear, whether he's sleeping."
    m neutral "...He's fine, Mum. He's right here. He's stirring."
    "Her mum says something about the eyes. You can always tell from the eyes. Thirty years on the wards teaches you."
    m smile "Okay, Nurse Mum. Happy birthday. I'll bring the present Sunday. No, I won't tell you what it is. Love you."
    "She hangs up and looks at him over the steam."
    m neutral "She says you look tired. From the phone. She can't even see you."
    a "Your mother has supernatural powers. We've discussed this."
    m "She's not wrong, though."
    a smile "I'm fine. I just thought a lot today. Thinking's tiring. That's why I usually avoid it."
    "He drains the pasta. Steam fills the kitchen and for a moment he can't see her at all, just a red blur by the window."
    "Then it clears and she's there, swinging her legs against the cupboard, exactly where she was."
    at "Of course she's there. Where else would she be?"
    m "Can I ask you something weird?"
    a "That's usually my line."
    m "Do you ever feel like you're being watched?"
    "He nearly drops the pan."
    a worried "...Why?"
    m smile "Because you've been watching me all day like I'm a documentary about penguins."
    a "Oh. Ha. That."
    m "That."
    a normal "You're a very good documentary."
    m happy "I know. I'm very watchable. Plate me some pasta, cameraman."
    scene bg kitchen table with dissolve
    show mira neutral at slightright with dissolve
    show aron normal at slightleft with dissolve
    if ch1_told_dream:
        "They eat at the little table by the window. Halfway through, Mira puts her fork down."
        m "I keep thinking about your lighthouse. Under the sea. Blinking."
        a "Me too."
        m smile "I think it's a nice thing to have in your head. A light that's always there, even if you can't see it."
        a "Even if it's at the bottom of the sea."
        m "Especially then."
    else:
        "They eat at the little table by the window. Neither of them mentions lighthouses. It sits at the table with them anyway."
        "Once, when he looks up, she's already looking at him, as if she'd been about to say something. Then she smiles and doesn't."
    "Afterwards she washes and he dries, and she flicks water at him, and he flicks the towel at her, and the evening is very nice."
    "At ten she yawns so widely her jaw clicks."
    m "Bed. Coming?"
    a "In a bit. I just want to sit for a while."
    m neutral "Don't sit too long."
    a smile "Never."
    "She kisses him on the top of his head and goes. He hears the bedroom door, the creak of the bed, then quiet."
    stop music fadeout 2.0
    jump ch1_notebook

# ---------------------------------------------------------------------------
# Miso hears about Bostrom. Then the notebook.
# ---------------------------------------------------------------------------
label ch1_notebook:
    scene bg room night with slowfade
    play music "audio/unease.ogg" fadein 3.0
    "The living room. One lamp. The rain has settled into a steady hiss against the window."
    show aron normal at slightleft with dissolve
    show miso sit at catspot with dissolve
    "Miso is sitting on the arm of the sofa, watching him with the steady, faintly disappointed look of a cat who has seen everything."
    a "Okay. Miso. You and me. I need to say this out loud to someone and you're the only one awake."
    a "There's a philosopher called Nick Bostrom. Very serious man. Oxford. He wrote a paper. You'd hate it, it has no tuna in it."
    a "He says: take any civilisation like ours. Humans. Or cats, if cats ever get around to it."
    a "Door one: they all die out before they can build computers powerful enough to simulate a whole world."
    a "I don't believe door one. People are reckless, but they're stubborn. Somebody would make it."
    a "Door two: they get the power and almost none of them ever use it to simulate their ancestors. They politely decline."
    a "That's the door I'd like. The kind door. But I've met people. I've met myself."
    a "If I could run a world, would I really not? Just once? Just to see? I'd run one. You'd run one, and fill it with birds."
    "Miso's tail twitches at the word 'birds'."
    a "So that leaves door three. They run simulations. Lots of them. And then almost every mind that asks 'am I real?'..."
    a "...is a simulated one. Just by the numbers. One real world, a million copies. The odds are terrible."
    a "And here's my bit. Not Bostrom's. Mine. Minds must be expensive. Not trees. Not rain. Rain is bacon, Theo says."
    a "But somebody who looks back. Somebody who notices the coffee machine is early. That costs something."
    a "So if I were careful, starting a new world, I'd keep the minds few. A handful of real ones. Everyone else, very good actors."
    a "Kessler. The woman at the crossing. 'Can't complain.' 'Lovely morning for it.'"
    a "And then, if the world held, I'd add more. Let them find each other. Let them grow."
    a "So the real question isn't 'am I in a simulation'. It's 'how many of us are actually here?'"
    a worried "Including you, by the way. I'm not ruling you out. You're very suspicious. You sleep sixteen hours a day. That's very cheap to run."
    a "So. That's the theory. That's my whole theory. What do you think?"
    "Miso looks at him for a long moment. She blinks, slowly."
    cat "Meow."
    scene bg desk with dissolve
    show aron normal at center with dissolve
    "In the drawer of the desk, under the takeaway menus, there is a notebook he bought years ago and never used."
    "Plain grey cover. Squared paper. No logo. The kind of object that doesn't try to be anything but itself."
    at "Theo said I'd have a notebook by tonight. I hate it when he's right."
    "He opens it to the first page. It is very white. It feels like the first morning of something."
    "He looks toward the bedroom door. It's half open. He can hear Mira breathing, slow and even."
    at "Is she?"
    at "Is Theo?"
    scene pov hands with dissolve
    "He looks down at his own hands, flat on the desk. The lamp makes them gold. They look like anyone's hands."
    at "Am I alone in here?"
    "The thought arrives cold and clear. Then, in the next room, Mira snores very gently, and it gets a little less cold."
    a "Okay. Steady. It's a hobby, not a horror film."
    at "She knew the lighthouse. If she's scenery, how does scenery know the one thing I never told anyone?"
    at "Unless the thing writing the scenery has read my mind. Which would be rude, frankly."
    at "Or she's real, and it's a coincidence, and I talk in my sleep. That's the most likely. It's the most likely."
    at "Most likely isn't certain. And I can't live in 'most likely' forever. I need to know."
    at "So: tests. Small, careful, private ones. Like a birdwatcher. Like someone who wants the truth more than a scary story."
    at "And nobody gets hurt, and nobody gets worried, and I still do the washing up. Those are the rules of the hobby."
    at "If it is a test, then I'm being graded. On what? Efficiency? Curiosity? How fast I figure it out?"
    at "I don't care about any of that. If I'm going to be graded, I'll pick the subject myself."
    "He picks up the pen. His hand is steady now. He writes, slowly, in his neatest handwriting."
    scene cg notebook with dissolve
    centered "If this is a test, I want to pass it by being kind."
    $ kept_journal = True
    at "There. That's the first line. Whatever else goes in here, that goes first."
    at "Less, but better. Rams would approve. One sentence. No decoration."
    scene bg desk with dissolve
    show aron normal at center with dissolve
    "Under it, he draws a line with a ruler. Then he writes TESTS in capitals, and stares at the empty space."

    menu:
        at "How do you test a world?"

        "One small test, done really well":
            $ p_less += 1
            $ integrity += 1
            $ ch1_test = "small"
            jump ch1_test_small

        "Test everything at once":
            $ p_less -= 1
            $ clarity += 1
            $ ch1_test = "grand"
            jump ch1_test_grand

        "See what happens when no one looks":
            $ clarity += 1
            $ ch1_test = "unseen"
            jump ch1_test_unseen

label ch1_test_small:
    at "One thing. Not everything. One thing, measured perfectly. If the world cheats, it'll cheat there."
    at "The bird. The bird on the kitchen wire. Mira says it comes at 7:07. Let's see."
    "He writes:"
    centered "TEST 1. The kitchen bird.\nWatch the wire 7:00 to 7:15.\nWrite the exact time it lands.\nDo this for four mornings. Change nothing else."
    scene bg kitchen with slowfade
    play music "audio/morning.ogg" fadein 2.0
    "Sunday. 6:58. He stands at the kitchen window in his socks with the notebook and a pen and his phone's stopwatch."
    show aron tired at slightleft with dissolve
    "The wire is empty. The street is grey. A newspaper delivery bike goes past, its chain clicking."
    "7:03. 7:04. 7:05."
    "7:06. He holds his breath without meaning to."
    scene pov birds with quick
    "7:07. A small dark bird drops out of nowhere onto the wire and folds its wings."
    a "Seven-oh-seven and... four seconds."
    at "Four seconds. Write it down. Exactly. Don't round it. Rounding is how people lie to themselves."
    scene bg kitchen with dissolve
    show aron tired at slightleft with dissolve
    "Monday. 7:07 and four seconds. He's late for work at the studio and doesn't mind."
    "Tuesday. 7:07 and four seconds. The bird turns its head left, right, left. Then still."
    "Three mornings. Three identical times. He looks at the three entries in the notebook. They look like three birds on a wire."
    at "Okay. Now the important one. Day four. What if I don't watch?"
    at "I'll film it instead. Phone on the windowsill. I'll stay in bed. If it only lands when someone's looking..."
    scene pov ceiling with dissolve
    "Wednesday. He stays in bed with his eyes shut, listening. The clock says 7:07. Of course it does."
    "In the kitchen, Mira is making coffee. He hears her say, to no one:"
    m "Morning, birdy."
    "At 7:20 he goes to collect the phone. He sits on the kitchen floor and plays the video with his heart pounding."
    scene bg kitchen with dissolve
    show aron worried at slightleft with dissolve
    "7:00. Empty wire. 7:05. Empty wire. 7:07..."
    "Empty wire. 7:08. 7:10. 7:15. Empty wire. The bird never comes."
    a "..."
    show mira neutral at slightright with dissolve
    m "Why are you sitting on the floor?"
    a "Did you see the bird this morning?"
    m smile "Sure. Seven-oh-seven, like always. I said good morning to it. It ignored me, like always."
    a worried "It's not on the video."
    m surprised "What video?"
    a "I filmed the wire. From the windowsill. The bird isn't there. Look."
    "She crouches beside him and watches. Empty wire, empty wire. Her face does something complicated."
    m neutral "Maybe the phone angle's wrong? Maybe it landed further along?"
    a "Maybe."
    m "Or maybe I'm confusing it with yesterday. I don't exactly take notes on the bird, love."
    a "Maybe."
    m worried "...You've been doing this every morning, haven't you? Standing at the window."
    a "Just for a few days."
    m "Okay."
    "She doesn't say anything else. She puts her hand on the back of his neck for a moment, and then goes to get dressed."
    at "One small thing. Measured well. And it came out clean: when I watch, the bird comes. When I don't, it doesn't."
    at "Or the phone was pointing at the wrong bit of wire. Or Mira misremembered. Or birds are birds."
    at "That's the problem with one small test. It gives you one small answer. And one small answer can be explained away."
    at "But it's a real answer. I did it properly. Nobody can say I didn't do it properly."
    "He writes the result under the three times. Then, under that: 'Inconclusive. Do it again. Do it better.'"
    jump ch1_test_clock

label ch1_test_grand:
    at "One test isn't enough. One test can be explained away. I need a web. Everything, cross-checked."
    "He writes fast, filling the page, then the next one, then the next."
    centered "TEST 1. Birds on the street wire: count daily.\nTEST 2. Repeated sentences: log.\nTEST 3. 7:07 rule.\nTEST 4. Kessler's lines.\nTEST 5-23. ..."
    at "Twenty-three tests. If the world is consistent, it'll pass them all. If it cheats, one of them will catch it."
    scene bg desk with dissolve
    play music "audio/unease.ogg" fadein 1.0
    show aron worried at center with dissolve
    "By Sunday night the wall above the desk is covered in notes. Yellow squares, blue squares, red string from Mira's sewing tin."
    "Lines connect the birds to the market. The market to the clock. The clock to the crossing. The crossing to the lighthouse."
    scene bg studio with dissolve
    show aron tired at center with dissolve
    "On Monday he goes to the studio, sits under the Rams quote on the wall, and does not design a single kettle."
    "Instead he counts the number of times the clients on the video call say 'cheers'. Fourteen. He writes it on his hand."
    "He doesn't know what it means. He writes it down anyway."
    "On Tuesday he eats his sandwich on a bench and times the traffic lights. They're very regular. He's delighted."
    at "Everything is regular. That's either the answer, or it's how traffic lights work. Either way, I'm having a lovely time."
    scene bg desk with dissolve
    "On Tuesday night, Mira comes in with two cups of tea and stops in the doorway."
    show aron worried at slightleft with dissolve
    show mira surprised at slightright with dissolve
    m "Aron. What is this?"
    a "It's... a project."
    m "It's my sewing string."
    a "I'll buy you new string."
    m neutral "That's not... Aron. There are about a hundred notes on the wall."
    a "Eighty-seven."
    m surprised "You counted them."
    a normal "I'm testing some things. About the world. It's a hobby. Like a crossword. A big crossword."
    "She steps closer and reads one. In his handwriting: 'Kessler said can't complain x2. Loaded line? Check Thursday.'"
    m "Is this about the bird? The lighthouse?"
    a "Partly."
    m neutral "Is this a fun crossword or a worrying crossword?"
    a smile "Fun. Ninety percent fun."
    m "And the other ten?"
    a "Curious. Mira, I'm fine. I'm just thorough."
    "She puts the tea down on the desk, carefully, between two pieces of string."
    m smile "You're thorough with kettles. This is very you, but more."
    at "From where she's standing it probably looks like a crime show. From where I'm sitting it looks like a very good puzzle."
    a smile "I'll take some down after this week. I promise. You can have your string back."
    m "I want the red one back first. That's my good red."
    "She kisses him on the top of the head and goes to bed. He takes down the red string. He's a man of his word."
    jump ch1_test_clock

label ch1_test_unseen:
    at "If someone's rendering this, they'd skimp where nobody's watching. Every game does. It's just efficient."
    at "So: leave a camera somewhere no one's looking. See if the world keeps going when its audience leaves."
    centered "TEST 1. The empty room.\nPhone recording in the living room.\nBoth of us out for one hour.\nCheck: does anything change? Does time skip?"
    scene bg room with dissolve
    show aron normal at slightleft with dissolve
    show mira neutral at slightright with dissolve
    "On Sunday he props his phone on the bookshelf, pointed at the empty sofa, the window, the clock on the wall."
    m "You're filming the sofa."
    a "I'm filming the room. The sofa is a participant."
    m smile "Is this an art project?"
    a "It's science."
    m "Should I worry that you're doing science on our sofa?"
    a grin "The sofa consented."
    m happy "Okay, weirdo. Brunch. And shut the door, or Miso will sit in front of your camera for an hour out of spite."
    scene bg cafe with dissolve
    "They have brunch at the corner cafe. Aron checks his watch nine times. Mira notices seven of them."
    scene bg room with dissolve
    show aron worried at center with dissolve
    "When they get back, he sits on the sofa that was the subject of the experiment and plays the video at double speed."
    scene pov hands with dissolve
    "The phone in his hands. The light changes across the floor. A car passes. The clock on the wall ticks. Nothing happens."
    "Until the timestamp. 14:06:59. Then 14:07:07."
    "Eight seconds are gone. The picture doesn't jump. The light, the clock's hands, the shadows, all exactly where they should be."
    "But the counter skips, as if the world had kept going without telling the phone."
    at "Phones drop frames. Storage hiccups. Background apps. It happens. Theo would say it happens."
    at "Fourteen oh seven. Two-oh-seven in the afternoon, and the phone loses eight seconds."
    at "That's either the most meaningful thing that's ever happened to me, or my phone is four years old."
    scene bg room with dissolve
    show aron worried at center with dissolve
    "He watches the gap again. Twenty times. The sofa sits there before the gap and after, completely innocent."
    at "When nobody's watching, the world skips. Or the phone skips. And I can't tell which, because the phone is IN the world."
    at "Every instrument I have is made of the thing I'm trying to measure."
    "He writes that down. He underlines it twice."
    jump ch1_test_clock

# ---------------------------------------------------------------------------
# The 7:07 rule.
# ---------------------------------------------------------------------------
label ch1_test_clock:
    scene bg desk with dissolve
    show aron normal at center with dissolve
    "Whatever the first test said, there is still the clock."
    "Every morning, 7:07. Whatever time he goes to bed. Whatever he drinks. Whatever he dreams."
    at "The 7:07 rule. It's the simplest thing in the whole puzzle. Which means it should be the easiest to break."
    at "If I can make myself wake at any other time, even once, the rule's broken and I can relax."
    at "And if I can't..."
    at "Let's not think about 'if I can't'."

    menu:
        at "How do I break the 7:07 rule?"

        "Set the alarm for six":
            jump ch1_clock_alarm

        "Stay up all night and watch it":
            $ p_rest -= 1
            $ clarity += 1
            jump ch1_clock_stayup

        "Ask Mira to help with the test":
            $ p_govern += 1
            $ bond += 1
            jump ch1_clock_mira

        "Quietly change Mira's alarm too":
            $ p_govern -= 1
            $ clarity += 1
            jump ch1_clock_secret

label ch1_clock_alarm:
    scene bg bedroom night with dissolve
    show aron normal at center with dissolve
    at "Simple. Set the alarm. Six o'clock. Machines don't care about patterns."
    "He turns the little yellow hand on the white clock to six, and pulls the switch to ON. It clicks."
    "He checks it twice. Then a third time. Then he gets into bed and lies with his eyes open for an hour."
    scene black with blackout
    "..."
    scene pov ceiling with dissolve
    "He wakes."
    "The light through the curtains is the colour of weak tea. From the kitchen, the coffee machine."
    "The clock says 7:07."
    a "No. No, no."
    scene bg bedroom with dissolve
    show aron worried at center with dissolve
    "He grabs the clock. The alarm switch is in the OFF position."
    a "I turned it on. I turned it on, I checked it three times, I..."
    scene bg kitchen with dissolve
    "He goes into the kitchen holding the clock like a dead fish."
    show aron worried at slightleft with dissolve
    show mira neutral at slightright with dissolve
    a "Did you turn off my alarm?"
    m surprised "Your what? Good morning to you too."
    a "My alarm. I set it for six. It's off."
    m neutral "I didn't touch it. I don't even know how that thing works. It has no numbers."
    a "It has numbers. They're just... understated."
    m smile "Maybe you turned it off in your sleep. You do that. You've snoozed your phone without waking up a hundred times."
    a "Have I?"
    m "Constantly. You argue with it. Very politely. 'Not now, thank you.' Or Miso walked on it. She walks on everything."
    at "She's probably right. She's almost certainly right. I've done it before. I just can't remember doing it."
    at "Which is exactly what it would feel like if somebody else did it for me."
    "Out of the window, the bird is already on the wire. He doesn't need to check the time."
    jump ch1_clock_end

label ch1_clock_stayup:
    at "If the clock only reads 7:07 when I wake up, then I just won't sleep. I'll watch it the whole way."
    at "No sleep, no waking. Checkmate, clock."
    "He makes a pot of coffee at eleven, and another at two. He sits on the edge of the bed with the clock in his hands."
    scene bg bedroom night with dissolve
    show aron tired at center with dissolve
    "Mira sleeps beside him. At one point she murmurs 'come to bed' without waking up. He strokes her hair."
    "3:00. 4:00. The red second hand goes round and round. He starts to see it when he closes his eyes."
    "5:30. Birds begin outside. Not three. Dozens. A whole dawn chorus. He finds that oddly reassuring."
    "6:45. His eyes are burning. He props them open with his thumbs, which doesn't work, and then with stubbornness, which does."
    "7:00. 7:03. 7:05."
    "7:06. He blinks."
    scene black with dissolve
    "..."
    scene pov ceiling with dissolve
    "He is lying on his back across the duvet with the clock on his chest. The light is the colour of weak tea."
    "The clock says 7:07."
    a "..."
    at "I blinked. That's all I did. I blinked at 7:06."
    at "And I fell asleep for one minute and woke up at 7:07. Exactly. Like a door closing behind me."
    at "Or I fell asleep at 7:06 because I'd been awake for twenty-four hours and that's what bodies do."
    scene bg bedroom with dissolve
    show aron tired at center with dissolve
    "His head is pounding. His mouth tastes of old coffee. He feels like a hollowed-out loaf of bread, and he's grumpy all day."
    at "Note to self: staying awake is not a great experimental method. The experimenter gets very stupid and snaps at the kettle."
    "He writes the result anyway, in handwriting he can barely read the next day."
    jump ch1_clock_end

label ch1_clock_mira:
    scene bg room with dissolve
    show mira neutral at slightright with dissolve
    show aron normal at slightleft with dissolve
    "He finds Mira on the sofa with a book and sits down at the other end, holding the notebook."
    a "Can I ask you for help with something? It's going to sound strange."
    m smile "Is it the sofa experiment? I'm not filming furniture again."
    a "No. It's... I always wake up at 7:07. Every day. Have you noticed?"
    m neutral "I've noticed you never need an alarm. I'm very jealous."
    a "I want to see if I can wake up at any other time. But I think I might cheat. Without meaning to. In my sleep."
    a "So would you wake me? At a different time. Any time. Don't tell me when."
    "She closes the book over her finger and looks at him. Really looks."
    m "And if I do it, and you wake up at whatever time, you'll feel better?"
    a "I think so. Yes."
    m smile "Then of course I'll do it."
    a "You don't think it's stupid?"
    m "I think it's a little bit stupid. But you asked instead of just doing something weird on your own. I'll take that."
    a smile "Thank you."
    m happy "You can pay me in breakfast."
    scene bg bedroom night with blackout
    "..."
    "Something soft on his cheek. A kiss. A voice, very close."
    m "Wakey wakey, test subject."
    scene bg bedroom with dissolve
    show mira smile at slightright with dissolve
    show aron tired at slightleft with dissolve
    "He opens his eyes. The light is different. Thinner. Bluer."
    "The clock says 6:15."
    a awe "Six fifteen."
    m "Six fifteen and twelve seconds. I set my phone. I'm very scientific."
    a "Six fifteen. It's not seven-oh-seven."
    m happy "Congratulations. You've been woken at a different time. Like a normal person. Welcome to the club."
    a smile "Mira, you're a genius."
    m "I'm aware. Now go back to sleep. I'm going back to sleep. You owe me pancakes."
    "She pulls the duvet over her head. He lies awake beside her, grinning at the ceiling."
    at "It broke. The rule broke. When someone else is involved, it breaks."
    at "That's good. That's very good. It means it was me. My body clock. My weird brain. Not the world."
    at "...Or it means the rule only holds when I'm alone."
    at "When there's two of us, the world bends. When it's just me, it snaps back to 7:07."
    at "I don't know which of those is the comforting one."
    "He falls asleep again, holding her hand. When he wakes, it's 9:30, and the bird is long gone."
    jump ch1_clock_end

label ch1_clock_secret:
    at "If I tell her, she'll be part of the test. Contaminated. I need her not to know."
    at "Her alarm. She sets it every night for 6:45. If I move it to 7:07, does she wake at 7:07?"
    at "Or does she wake at 6:45 anyway, because she's real and her body knows her own time?"
    scene bg bedroom night with dissolve
    "While she's in the shower, he picks up her phone. He knows the code. He's always known the code. She trusts him."
    "He moves her alarm from 6:45 to 7:07. His thumb hesitates over it. Then he presses save."
    scene black with blackout
    "..."
    scene bg bedroom with dissolve
    "In the morning the alarm goes off. Her phone chimes on the nightstand. He's already awake, watching."
    show mira neutral at slightright with dissolve
    show aron worried at slightleft with dissolve
    "The phone says 7:07. She fumbles for it, and silences it, and frowns at the screen."
    m "That's weird. I set it for quarter to."
    a "Maybe you set it wrong."
    m "I set it for quarter to every day for three years."
    m surprised "...Did you change my alarm?"
    a "..."
    m worried "Aron. Did you change my alarm?"
    a "I wanted to see if you'd wake up on your own. At your normal time. If you didn't know."
    m neutral "You went into my phone."
    a "I'm sorry. It was for the test."
    m "The test."
    "She sits up and pulls her knees to her chest."
    m sad "You could have just asked me. I would have helped. I always help."
    a "I know. I know. I thought if you knew, it wouldn't count."
    m "It wouldn't count if I knew. So you decided for me."
    a "...Yes."
    m worried "I'm not a sofa, Aron. I'm not a bird on a wire. If you're doing tests on me, I want to know."
    a "You're right. I'm sorry. I mean it."
    "She looks at him for a long moment. Then she lets out a breath and leans her forehead against his shoulder."
    m neutral "Okay. Don't do it again."
    a "I won't."
    at "And the result? She didn't wake at 6:45. She slept until 7:07, like I do. Like the bird does."
    at "Which means something, or means she was tired. And I can't tell her I'm pleased about it, because I'm not."
    at "I got my data and lost something for it. I'm not sure the trade was any good."
    jump ch1_clock_end

label ch1_clock_end:
    scene bg desk with dissolve
    show aron normal at center with dissolve
    "That night the notebook gets three more pages. Times. Places. Words people said. Little drawings of birds."
    "At the top of each page he copies the first line again, so he won't forget it."
    centered "If this is a test, I want to pass it by being kind."
    at "Kind. Remember kind. Whatever the clock does."
    stop music fadeout 2.0
    jump ch1_laundry

# ---------------------------------------------------------------------------
# Sunday laundry. The sock test.
# ---------------------------------------------------------------------------
label ch1_laundry:
    scene bg kitchen with slowfade
    play music "audio/morning.ogg" fadein 2.0
    show mira smile at slightright with dissolve
    show aron normal at slightleft with dissolve
    "Sunday afternoon is laundry. The washing machine lives under the kitchen counter and spins like it's trying to leave."
    "Mira folds. Aron pairs socks. Miso sits in the empty laundry basket, which is her right."
    m "Why are you counting the socks?"
    a "I'm not counting them. I'm auditing them."
    m "Aron."
    a "Okay. Small experiment. Twelve socks went in. If a world is cheap, socks are where it would save. Nobody tracks socks."
    m happy "Every world loses socks. It's not a conspiracy. It's the machine. It eats them. It's a sock predator."
    a "That's one theory."
    "He lays them out on the counter. Pair, pair, pair. Pair, pair."
    "One left over. Blue with a hole in the heel. Its partner nowhere."
    a "Eleven."
    m smile "Told you. Sock predator."
    a "Or the world didn't bother rendering the twelfth because nobody was looking at it."
    m "Or it's in the basket under the cat."
    "Mira lifts Miso, who goes boneless in protest. Underneath her: one blue sock with a hole in the heel."
    a "...Twelve."
    m happy "Science!"
    a grin "Okay. Fine. The world is solid. The cat is a thief. I'm writing that down."
    m "Write down that I was right."
    a "I'm writing down that you were right. In capitals."
    "He does, too. On a fresh page: SOCK TEST. RESULT: MIRA WAS RIGHT. CAT IS A THIEF."
    at "Most days the world passes. Most days it's just socks and cats and a woman laughing in a kitchen."
    at "That's the best result there is. I don't mind at all."
    stop music fadeout 2.0
    scene cg static with flash
    pause 0.3
    jump ch1_cut_flag

# ---------------------------------------------------------------------------
# CUT 3: Seraphiel raises the flag.
# ---------------------------------------------------------------------------
label ch1_cut_flag:
    scene bg command with fade
    play music "audio/entities.ogg" fadein 2.0
    show seraph stern at center, fadein
    "In the ops room, the large wall shows a desk, a lamp, and a grey notebook lying open."
    ch1_vael "Commander. You asked to be told if A-30 started keeping records."
    se "He has."
    ch1_vael "Since Saturday night. Eleven pages. Timestamps, repeated phrases, bird counts."
    if ch1_test == "small":
        ch1_vael "He tested the kitchen bird for four mornings. On the fourth he filmed it unobserved."
        se "And?"
        ch1_vael "The bird wasn't rendered for an unwatched lens. Standard economy. We don't fly birds for phones."
        se concerned "Standard economy, and he caught it on the first try. With one test."
    elif ch1_test == "grand":
        ch1_vael "He's built a wall of notes. Eighty-seven items, linked with string. Most of it is noise."
        se "Most of it."
        ch1_vael "Item forty-one is the loaded-line problem with the baker. Item sixty is the street wire. Both correct."
        se concerned "Two correct out of eighty-seven. Give him a month and it'll be twenty."
    else:
        ch1_vael "He left a camera in an empty room. It recorded an eight-second render gap at 14:07."
        se "We pause empty rooms. Everyone pauses empty rooms."
        ch1_vael "He doesn't know that, Commander. He just knows the counter skipped."
        se concerned "Then he knows more than most of them ever do."
    scene bg archive with dissolve
    "Behind the ops room, shelves run up into the dark: every life in the world, filed. One drawer is pulled out, labelled A-30."
    show seraph stern at center with dissolve
    se "Show me the first page."
    scene cg notebook with dissolve
    ch1_vael "'If this is a test, I want to pass it by being kind.'"
    "The ops room, which is never quiet, is quiet for a moment."
    scene bg command with dissolve
    show seraph concerned at center with dissolve
    ch1_vael "Shall I log it as noise?"
    se "No."
    se "Log it as written."
    ch1_vael "Commander, the protocol for subjects who start mapping the rules is clear. They're to be flagged."
    se stern "I know the protocol, Vael. I helped write it."
    se "A conscious subject who works out the rules isn't a subject anymore. He's a process running on his own."
    se "Upstairs calls that a disturbance. A rogue process. They don't like rogue processes."
    ch1_vael "What happens to them?"
    se "That depends on how far they get."
    se concerned "He wants to be kind. Most of them, when they find the edges, want to tear them down."
    ch1_vael "Does it change anything?"
    se stern "It doesn't change the protocol."
    se "Raise the flag. World 7,412. Subject A-30. Status: disturbance, early stage. Send it upstairs."
    ch1_vael "Flag raised."
    "Somewhere very far above the ops room, something receives the message and doesn't answer yet."
    se concerned "And Vael."
    ch1_vael "Commander?"
    se "Keep feeding him opportunities. Good ones. Whatever happens next, I want it on record that we did our job well."
    stop music fadeout 2.0
    jump ch1_shop

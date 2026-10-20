# Snapshot - Chapter 2: "Fog" (part 4 of 6)
# The routine, a word at the next table, Miso hears the lane theory, the
# one good hour, a night with weed at Theo's. Continues in ch2_part5.rpy.

default ch2_took_weed = False
default ch2_hour_with_theo = False

label ch2_routine:
    play music "audio/morning.ogg" fadein 2.0
    scene bg park autumn with dis
    "Evening dose. Morning walk. Same wake-up time."
    "The first week it's awful. The second week it's merely bad. By the fourth week, something has changed. Not much. Something."
    show aron tired at center with dissolve
    "He walks round the park pond at half eight every morning, ten minutes, slow, with his hands in his pockets."
    "The leaves are turning. The paths are slippery with them, yellow and brown, like somebody spilled a box of old letters."
    "The ducks have a system. He's working it out, slowly, without the notebook. They always go anticlockwise. The big one goes last."
    at "Nothing urgent about ducks. No logs. No throttle. Just a system that's fine with being watched."
    scene bg park with dissolve
    "The tiredness is still there. But it's moved. Now it lives mostly in the mornings and late evenings."
    "And in the middle of the afternoon, around four, there's an hour. A good hour. Like a window that opens in a stuffy room."
    "He learns to feel it coming. A lightness behind the eyes. Colours getting their edges back."
    "One good hour a day. It isn't much. It's the most precious thing he owns."
    jump ch2_cafe_word

label ch2_cafe_word:
    scene bg cafe with fade
    "Saturday. Mira drags him to the café on the corner, because, she says, people who've been in hospital deserve cake."
    show mira smile at slightright with dissolve
    show aron normal at slightleft with dissolve
    m "Carrot cake or the lemon thing?"
    a "Is there a third option where I have both?"
    m happy "There is now. I'll tell them it's medical."
    "She goes to the counter. He sits by the radiator and listens to the café hum. Spoons. Steam. A baby somewhere, considering crying."
    "At the next table, two women in good coats are talking over a pot of tea. He isn't listening. Then he is."
    ch2_table "...honestly, don't worry about him any more. He's protected now."
    ch2_table "Nothing he does can touch the rest of us. That was the whole point of moving him."
    "The spoon in his hand stops halfway to the sugar."
    at "Protected."
    at "Moving him."
    at "That's my word. That's the word on the first night, under the light. It's underlined in my notebook. Twice."
    "He turns, very slowly. The woman who spoke is pouring tea. She's sixty, perhaps, with pearl earrings and a kind, tired face."
    ch2_table "...the policy, I mean. Protected no-claims bonus. My son can crash that car as much as he likes now, bless him."
    "Her friend laughs. They move on to someone's hip replacement."
    scene pov cup with dissolve
    "He looks down into his coffee. His hand is shaking. Tiny rings spread across the surface and break against the sides of the cup."
    at "Car insurance. A woman talking about car insurance. Protected no-claims. It's a real thing. Dad had it."
    at "And 'moving him'? Moving him... onto her policy. Probably. People say things."
    at "Or the word leaked. Out of my notebook, out of my head, into a stranger's mouth in a café."
    at "Like the cab. Like the birds. Like a room that's starting to repeat what I say to it."
    scene bg cafe with dissolve
    show mira neutral at slightright with dissolve
    show aron worried at slightleft with dissolve
    m "Both cakes. The lady says 'feel better soon'. Love? You've gone grey."
    a "Someone said a word."
    m worried "Which word?"
    a "'Protected'."
    m "...Is that a bad word?"
    a "It's one of mine. From the ward. From the first night. It's in the notebook."
    "Mira glances at the next table. At the pearl earrings, the teapot, the hip replacement."
    m neutral "Okay. Write it down. And tell Okafor on Monday. That was the deal, wasn't it? Bring the weird things there."
    a "That was the deal."
    m smile "Then eat your cake. Both of your cakes. That's also the deal."
    scene bg cafe window with dissolve
    "They sit by the window. Rain starts, lightly. People hurry past with newspapers over their heads."
    "He eats both cakes. They're very good. He's almost sure they're very good. He tells himself to taste them, so he does."
    at "Small, slow, kind. Write it down. Don't build a cathedral."
    at "Just a little chapel. Just for now."
    jump ch2_miso_two

label ch2_miso_two:
    scene bg room night with fade
    "That night, Mira's on the phone to her mother for an hour about mattress legs. He sits on the floor of the living room with Miso."
    show aron normal at slightleft with dissolve
    show miso sit at catspot with dissolve
    a "Okay, Miso. Update. New data. I need a second opinion and you're the only one in the flat without a diagnosis."
    a "If there's a throttle, there's somebody throttling. If there's somebody throttling, there's a budget. Throttling costs something."
    a "If there's a budget, there's a committee that sets it. I heard them, on the ward. 'Council motion. Next session.'"
    a "So: a council. People who vote about me. In the third person. I'm an item on an agenda somewhere."
    show miso stare at catspot
    a "And then I came out, and the world is... the same. But louder. Like it's been tuned to me."
    a "The cab driver knew my story. The woman in the café used my word. The birds came indoors."
    a "It feels like I'm in my own lane, Miso. Like a swimming pool where somebody put the ropes up while I was underwater."
    a "Everyone else is swimming next to me. I can see them. I can hear them. But the water in my lane is mine. Only mine."
    a "And it's starting to go the colour of whatever I'm thinking."
    a "Or I'm ill. And ill people hear their own words in strangers' mouths. That's called... there's a word for it. Okafor told me. Ideas of reference."
    a "Ideas of reference. It even sounds like a filing system."
    a "So. Lane, or ideas of reference. Committee, or brain chemistry. You've known me six years. What do you reckon?"
    show miso meow at catspot
    cat "Meow."
    jump ch2_good_hour

label ch2_good_hour:
    scene bg room with fade
    show aron normal at slightleft with dissolve
    "It's Tuesday, and the good hour has just arrived. He can feel it. Like a key turning in a lock."
    "On the desk, the notebook is open where he left it. He's close to something. A pattern in the dates of the voices. He can feel it."
    "Then his phone buzzes."
    th "u around? kinda having a day"
    th "no big deal. just. u know"
    "Theo never says 'no big deal'. Theo thinks everything is a big deal. Theo once called an ambulance for a pigeon."
    at "One hour. Theo, or the notebook."
    at "The notebook will still be here tomorrow. Will the good hour?"
    at "Will Theo?"

    menu:
        at "One good hour. Where does it go?"

        "Spend it with Theo.":
            $ p_share += 1
            $ bond += 1
            $ ch2_hour_with_theo = True
            jump ch2_hour_theo

        "Spend it on the notebook.":
            $ p_share -= 1
            $ clarity += 1
            jump ch2_hour_notes

label ch2_hour_theo:
    a "cafe on the corner? 10 mins"
    th "rly?? ok!!!!"
    scene bg street dusk with dissolve
    "He walks there faster than he's walked in months. The afternoon is going gold at the edges."
    scene bg cafe window with dissolve
    show theo sad at slightright with dissolve
    show aron normal at slightleft with dissolve
    "Theo is already at the window table, with two coffees and a cinnamon bun cut exactly in half. Theo never cuts anything exactly in half."
    a "You cut the bun in half."
    th normal "I had a lot of time. I've been here since you texted. I ran."
    a "What's going on?"
    th sad "Nothing. Dumb stuff. It's stupid next to your stuff."
    a "Theo. I've got one good hour a day. I'm spending it on you. Don't waste it telling me it's nothing."
    "Theo looks at the bun for a long time."
    th "I think I'm getting let go. At work. They had a 'conversation' with me. The kind with a second person in the room."
    th "And my sister's not speaking to me again. And my flat smells of damp. And I keep forgetting to eat, and then I eat a whole pizza at midnight."
    th "And when you were in hospital I kept thinking, it's always you that's the mess, and I'm the one who's fine. And I'm not fine, man."
    th "I'm really not fine. I just do the voice. The Theo voice. Like you do the 'it's fine' voice."
    a "...The hostage statement."
    th "Exactly. Mine's just louder."
    "Aron doesn't fix anything. He's too tired to fix anything, and he's learning that most things don't want fixing anyway."
    "He just asks questions and listens to the answers. What did the second person in the room say? When did your sister last call?"
    "Theo talks for forty minutes. Somewhere in the middle he laughs, properly, at something stupid, and he looks surprised at himself."
    th "You know what's mad? You're the one who's ill and you're the only person who's asked."
    a "I've had a lot of practice being asked. On the ward. A nurse called Hale asks you how you are like she's actually waiting for the answer."
    th "Hale sounds terrifying."
    a "Hale's the best person I've ever met. Don't tell Mira."
    "When the hour starts fading, he feels it go, like the sun going behind a cloud. He doesn't say anything. He finishes his half of the bun."
    th normal "Thanks, man. Seriously. I know what that hour costs you."
    a "It didn't cost anything. That's the thing I'm learning. It goes somewhere either way. This is a good somewhere."
    th grin "Bro, you got deep in the nuthouse."
    a "Psychiatric ward."
    th "Bro, you got deep in the psychiatric ward."
    at "I don't know if Theo's real. I don't know if anybody is. But I know I'd rather spend my hour finding out whether he's alright."
    jump ch2_weed_setup

label ch2_hour_notes:
    a "sorry mate, bit tied up right now. later?"
    th "ya no worries"
    scene bg desk with dissolve
    show aron normal at center with dissolve
    "He sits down at the desk. The good hour hums behind his eyes. The notebook opens like a door."
    "He's been writing down every fragment of the voices with the date and time. Now, with his head clear, he lays them out side by side."
    scene cg notebook with dissolve
    "'...throttle approved...' Night before the hospital. '...protection holding...' The ambulance. The first night."
    "'...stable in protection...' Week one. '...keep it inert...' Week two. And the cab. And the café. 'He's protected now.'"
    at "Protection. Inert. Moved."
    at "Not a prison. Prisons are for punishment. This is... quarantine. A clean room. Somewhere I can't touch anything."
    at "Somebody decided I was contagious. And they moved me somewhere I can't infect anyone."
    "He writes it all down, faster now. Throttle: to slow me. Protection: to seal me. The leaks: the seal isn't perfect."
    "It's the clearest map he's ever made. One page. Neat. Not a single bit of string."
    at "If there's a seal, someone made it. If someone made it, someone else might be able to open it."
    at "Somebody out there might be on my side."
    scene bg desk with dissolve
    show aron normal at center
    "He looks up. The hour is going. He can feel it draining, like warmth out of a bath."
    "He checks his phone for the first time in an hour. Three messages from Theo."
    th "ok actually it was kind of a big deal"
    th "nvm. all good. another time bro"
    "Then a single thumbs-up. It sits on the screen like a closed door."
    a "hey, sorry, im here now. whats up?"
    "No reply. Not that evening. Not until the next afternoon, when Theo sends a vegetable. A potato, shaped like nothing in particular."
    th "all good. forget it. how r u"
    at "I mapped the whole sky in an hour and I missed my best friend asking for help in four words."
    at "Kind. That was the first line. Kind."
    jump ch2_weed_setup

label ch2_weed_setup:
    scene bg theo with fade
    "Saturday. Mira is at her mother's overnight. The new mattress has, as predicted, arrived with the wrong legs."
    "Theo's flat is above a launderette. It smells of warm cotton and damp and, faintly, of Theo's terrible aftershave."
    show theo grin at slightright with dissolve
    show aron tired at slightleft with dissolve
    th "Lads' night. Mira's orders. She said, quote, 'Don't let him sit in the dark looking at the box.'"
    a "She said that?"
    th normal "She said a lot of things. She said no beer for you, and she said it twice. So the beer's for me. You get fizzy water. Fancy fizzy water."
    "On the coffee table, next to a terrible film and a six-pack, there's a small paper bag."
    a "And the bag?"
    "Theo opens it. Inside, a joint, rolled badly. It smells like a festival field."
    th "Look. Before you say anything. It's not the pills. I learned. It's just weed. It's chill. It's a plant."
    th grin "It's basically a vegetable. Vegetable index, bro. Very healthy reading on the vegetable index."
    a "Okafor said cannabis is the one thing I really shouldn't. For psychosis."
    th worried "Yeah. Yeah, okay. That's fair. I didn't... I just thought you could do with switching off for one night."
    th "I'll smoke it on the balcony. You do whatever. No pressure. Seriously this time."
    scene bg balcony with dissolve
    "He goes out onto the little balcony. The smell drifts in through the door, sweet and heavy. The film's title music starts, too loud."
    show aron tired at center with dissolve
    at "Switch off. Or switch on. The last thing that switched me on turned the lane up so loud I could hear it humming."
    at "But that was a stimulant. This is the other direction. Down, not up. Maybe down is safer."
    at "Maybe that's exactly the kind of thought Okafor warned me about."

    menu:
        th "You coming out, or what?"

        "Go out and take a hit.":
            $ clarity += 1
            $ fog += 1
            $ ch2_took_weed = True
            jump ch2_weed_yes

        "Stay in. Just hang out.":
            $ p_rest += 1
            $ bond += 1
            jump ch2_weed_no

label ch2_weed_yes:
    scene bg balcony with dissolve
    show theo normal at slightright with dissolve
    show aron tired at slightleft with dissolve
    "The balcony is cold. The street below is wet and orange under the lamps."
    "Theo hands it over without a word. Aron takes it. One breath. He coughs like a man in an old film."
    th grin "Graceful. Very graceful."
    scene bg theo with dissolve
    "For twenty minutes, it's lovely. Everything goes soft at the corners. The film is hilarious, even the parts that aren't jokes."
    "They laugh until Theo slides off the sofa. Aron laughs so much he has to lie on the floor."
    scene pov ceiling with dissolve
    "And then, lying there, looking at Theo's ceiling, which slowly breathes, it arrives. Very quietly. Very clear."
    at "The voices aren't talking to me."
    at "They never were. They're talking about me. Like notes. Like minutes of a meeting I wasn't invited to."
    at "I'm not the one they're speaking to. I'm the item on the agenda."
    "It feels enormous and simple, like finding out the moon's been there the whole time behind a cloud."
    a "Theo. Theo, I'm on the agenda."
    th "What agenda, bro?"
    a "The agenda. There's a table somewhere. And they're talking about me. In the third person."
    scene bg theo with dissolve
    show aron awe at slightleft with dissolve
    "On the TV, an advert for a car insurance company plays. A cartoon dog says, 'Peace of mind. Fully protected.'"
    "Theo laughs at it."
    "The advert finishes. Another starts. The same advert. The same dog. 'Peace of mind. Fully protected.'"
    "Theo laughs at it. Exactly the same laugh. The same length. The same little snort at the end."
    show aron worried at slightleft
    at "No."
    at "No no no. He did that. He did that exactly. He's looping."
    "The room tilts. Not physically. Something behind the room tilts, the way a stage set wobbles when someone bumps it."
    "He can feel the flat being drawn just ahead of where he looks. The corner of the bookshelf arrives a fraction late."
    a "Theo, stop. Stop laughing. Please. Say something different. Say something you'd never say."
    show theo worried at slightright with dissolve
    th "Bro? Hey. Hey, what's... you've gone white."
    a "Say something you'd never say!"
    th "Uh... uh... I like jazz? I genuinely like jazz?"
    a "...You hate jazz."
    th "I know! That's why I said it! What's happening, man, talk to me!"
    "His heart is going like a bird against a window. His hands won't stay still. The ceiling is very close and very far away."
    a "I can't... I can't breathe right. My heart's going wrong. I can't get a breath in."
    th "Okay. Okay. Okay. What do I do? Tell me what to do. Do I call someone?"
    "From somewhere a long way down, a voice that isn't a log. Hale's voice. A plastic cup of very sweet tea."
    a "Breathing. Hale's breathing. Do it with me. In for four."
    th "In for four. Okay. In for four."
    "They breathe in. Theo counts out loud, badly, too fast. Aron slows him down with his hand."
    a "Hold for four."
    th "Two, three, four."
    a "Out for six."
    "They do it eleven times. Aron counts every one. On the eleventh, the bookshelf is on time again."
    "The cartoon dog is gone. The film is back, playing to nobody."
    th sad "Bro. That was the scariest thing I've ever seen. And I saw you in the rain."
    a "Sorry."
    th "Don't be sorry. Just... I'm never bringing that stuff round you again. Ever. I'll smoke oregano."
    "They sit on the floor with their backs against the sofa until three, not talking much. Theo doesn't let go of his sleeve."
    scene bg bedroom with fade
    "The next day is thick. Thicker than the meds alone. As if somebody poured syrup into the fog."
    show aron sad at center with dissolve
    "Mira comes home at noon. She smells it on his jumper before she takes her coat off."
    show mira sad at slightright with dissolve
    m "Weed."
    a "Once. One breath. It was bad."
    m "How bad?"
    a "Hale's breathing bad. Eleven rounds."
    "She sits on the end of the bed. She doesn't shout. She looks like someone who has run a long way and seen the finish line move."
    m worried "That's the one thing, Aron. Okafor said it like it was the one thing. Cannabis and psychosis."
    a "I know. I thought down would be safer than up."
    m "Down's not safer than up. Down's just a different stair."
    m sad "I'm not angry. I'm just so scared of the next time being the time it doesn't wear off."
    a "There won't be a next time."
    m "You said that about the pill."
    if ch2_took_pill:
        a "...I did. I did say that."
        "She doesn't say anything else. She doesn't have to. He hears it all anyway, louder than any voice."
    else:
        a "I didn't take the pill. I said no to the pill."
        m neutral "...You did. You did say no to the pill. Okay. Okay, that's true."
        m "Then say no to the next thing too. Please. For me, if it's too hard for you."
    scene cg notebook with dissolve
    "He writes it in the notebook afterwards. Not the realisation, though he remembers it. Just: 'Agenda. Third person. Not worth the floor.'"
    jump ch2_speed_setup

label ch2_weed_no:
    scene bg theo with dissolve
    show aron tired at slightleft with dissolve
    a "I'm staying in. Enjoy your vegetable."
    th "Respect, bro. Respect."
    "Theo stays out on the balcony for ten minutes. Then he comes back in, leaves the rest in the bag, and puts the bag in a drawer."
    show theo normal at slightright with dissolve
    th "Actually it's not that fun on your own. It's just standing in the cold smelling like a tent."
    "The film is genuinely terrible. A man fights a shark using a helicopter. Then a second shark. Then, somehow, the helicopter is a shark."
    a "Is the helicopter a shark?"
    th "I think the helicopter was always a shark, bro. I think that's the twist."
    "They laugh. Aron laughs slower than he used to, but he laughs. Theo pauses the film to laugh more."
    "Somewhere in the second half, when the shark gets a love interest, Theo goes quiet."
    th sad "Can I say something weird?"
    a "Everything you say is weird."
    th "When you were in there. On the ward. I kept driving past at night. Like, round the car park. I didn't come in. I just drove round."
    a "Why?"
    th "I don't know. To check the building was still there. Like if I didn't look, it might not be."
    at "If I didn't look, it might not be. That's my whole theory. Theo says it like it's nothing."
    a "That's not weird, Theo."
    th "It's a bit weird."
    a "It's a bit weird. It's also the nicest thing anyone's ever done for a car park."
    th grin "I'm very good to car parks."
    "They watch the end. The shark saves the helicopter. Theo cries. He denies it."
    scene bg street rain with dissolve
    "When Aron leaves, Theo hugs him at the door, longer than usual, with both arms. Then he walks him to the corner in the rain, for no reason."
    th normal "Night, bro. Glad you're in there."
    scene bg kitchen with fade
    "Mira comes home at noon the next day. The flat smells of nothing in particular. She checks. He watches her check."
    show mira smile at slightright with dissolve
    show aron tired at slightleft with dissolve
    m "Good night?"
    a "A shark saved a helicopter."
    m happy "Oh, that one. The helicopter's a shark, you know."
    a "We worked it out."
    jump ch2_speed_setup

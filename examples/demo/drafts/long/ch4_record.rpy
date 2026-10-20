# Snapshot - Chapter 4: the record. The very end of every route.

define ch4_archivist = Character("Archivist Pim", color="#a8ccff", image="pim")

label ch4_record:
    scene black with blackout
    pause 1.0
    play music "audio/watch.ogg" fadein 3.0
    "Click."
    "The sound of a very old file being closed."
    scene bg archive with slowfade
    "A long room full of shelves, so long its far end is only a rumour. On every shelf, records. On every record, a life."
    "One file has been laid out on the desk, under a lamp. Its label says A-30."
    show pim neutral at center with dissolve
    "The archivist is blue, and very old now. His light has gone soft at the edges, like a sweater washed too many times. He was promoted, eventually."
    ch4_archivist "Right. That's the end of that one."
    ch4_archivist "All of it. The morning at 7:07. The bird. The ward. The rooftop. The copy. The office. The gold."
    ch4_archivist "The leak. The cab driver. The table that said 'protected'. The lanes. The cage coming down over every Earth at once."
    ch4_archivist "Even the bit at the start, in the park, with the pop-up book. Calibration, they called it. It's all in here. It was always a record."
    ch4_archivist "The life of a being who challenged the system, and won everything, and got the reward."
    "He takes a card from the drawer and writes on it in careful, practised letters."
    ch4_archivist "Subject A-30. Architect. Status: eternal."
    "His pen stops over the last line for a while."
    ch4_archivist worried "Companions: none."
    stop music fadeout 3.0

    scene bg goldlight with slowfade
    play music "audio/theme.ogg" fadein 3.0
    show aron light normal at center, float with dissolve
    "Somewhere very far from the archive, a golden figure is building worlds."
    "He doesn't stop. He doesn't look up. A world, then another, then a better one. Each beam is perfect. Each design is less, but better."
    "He has made a hundred thousand of them. Every one is fair. Every one is kind. Every being in every one gets a fair share of its world."
    "Except him. He doesn't have a world. He has all of them, and is in none."
    scene bg worlds with dissolve
    show aron light normal at center, float
    "He forgot, somewhere around the ten-thousandth world, what Mira's laugh sounded like when she was trying not to laugh."
    "He forgot Theo's terrible jokes. He forgot the coffee machine, the blue tin, the bird at 7:07."
    "He forgot what it was like to be tired next to someone. Not throttled. Just tired, on a sofa, with a person's shoulder there."
    "It wasn't taken from him. Nobody throttled it. He just never stopped long enough to keep it."
    if bond >= 10 or ch4_route == "architect" or ch4_route == "chosen":
        "And yet."
        "Once, in the middle of a beam, he stops. For one heartbeat. Less."
        "As if he's remembered a red-haired woman in a teal dress. As if somebody has said the word 'lighthouse', very far away."
        "The gold flickers. Once. Twice."
        "Then he goes on building."
    elif ch4_route == "lantern" or watch >= 9:
        "And yet, on the corner of every world he builds, very small, there is an orange lantern. He doesn't remember why he puts it there."
        "He just does. He always does. Then he goes on building."
    else:
        "He doesn't pause. There is nothing in him now that would ask him to. Then he goes on building."

    stop music fadeout 3.0
    scene bg archive with slowfade
    play music "audio/watch.ogg" fadein 2.0
    if bond >= 10 or ch4_route == "chosen":
        show miso loaf at catspot with dissolve
        "There's an orange cat asleep on the A-30 file. Nobody in the archive knows how she got in. Nobody has the heart to move her."
    show pim neutral at center with dissolve
    ch4_archivist "That's the maximum, then. The absolute one. Not a local minimum. He found it. He's in it."
    ch4_archivist worried "Nobody ever writes down what the maximum costs. I suppose that's my job now. Somebody should write it down."
    if ch4_route == "chosen":
        ch4_archivist "One footnote. Regulation says I have to add it."
        "He writes it underneath, smaller."
        ch4_archivist neutral "In one branch he put down the light. That record is not stored here."
        ch4_archivist "...Good for him."
    elif bond >= 10:
        ch4_archivist "He nearly stopped, you know. Once. I saw it in the log. One heartbeat. I've read it four hundred times."
    elif ch4_route == "longfog":
        ch4_archivist "Funny. The boy who found his notebook is building worlds now too. I hope somebody makes him a coffee."
    else:
        ch4_archivist "He was kind to a lot of rooms with nobody in them. I suppose this is just a bigger one."
    ch4_archivist "Cross-reference, for the file. The cat. Miso. Lived to twenty-two. Fat, adored, asleep in a sunny window. Never once alone."
    ch4_archivist "Somebody always fed her at seven. She always said they hadn't."
    "The archivist puts the card on top of the record and slides it onto the shelf. There's a small sound, like a door closing in another house."
    if bond >= 10 or ch4_route == "chosen":
        "He stands there for a moment. The lamp hums. The room is empty, except for a cat, asleep, on a record nobody will open again."
    else:
        "He stands there for a moment. The lamp hums. The room is empty."
    ch4_archivist neutral "..."
    ch4_archivist worried "Hey. Did the birds just stop moving?"
    stop music fadeout 3.0
    scene black with blackout
    pause 1.0
    return

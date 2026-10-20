# Snapshot - tutorial and opening. The story continues in ch1.rpy .. ch4.rpy.

label start:
    scene black
    centered "Snapshot is a work of fiction. It touches on psychosis, hospitalisation, medication and drug use.\nIf any of that is close to home, please play gently."

    play music "audio/theme.ogg" fadein 1.0
    scene bg room with fade

    "This room sits behind the screen. Slide the 3D slider up to push it back."

    show mira happy at center, popin
    m "Hi! I stand right on the screen plane, like a paper cut-out."
    m surprised "And this textbox floats in front of me. Try it!"

    menu:
        m "How does it look?"

        "It pops out!":
            $ bond += 1
            m happy "That's the pop-up book effect."

        "I can't see any difference.":
            m sad "Is the slider all the way down?"
            jump tutorial_slider_help

    jump tutorial_park

label tutorial_slider_help:
    "Push the slider on the right edge of the top screen upwards."
    m happy "There we go."
    jump tutorial_park

label tutorial_park:
    scene bg park with slowfade
    show mira happy at slightleft
    show aron normal at right
    with moveinright

    a "Did somebody say pop-up book?"
    show mira at bob
    m "Aron! You're standing a little nearer than me."

    a grin "Why did the sprite never leave? It was too attached to its layer."
    m surprised "..."
    m smile "That's terrible. I love you anyway."

    show aron normal at center with move
    a "Watch this." with vpunch
    m happy "Okay, okay. That's the tutorial. Say goodbye, Aron."
    a normal "Goodbye, tutorial."
    a "..."
    a worried "Hey, Mira. Did the birds just stop moving?"
    m neutral "What birds?"
    stop music fadeout 2.0
    scene cg static with flash
    pause 0.4

    # The first cut away: someone was watching the tutorial.
    scene bg command with fade
    play music "audio/entities.ogg" fadein 2.0
    show seraph stern at center, fadein
    se "Calibration complete."
    se "Depth perception within tolerance. Attachment to the female unit: high. Humour: regrettable."
    se concerned "And at the very end he noticed the birds."
    se stern "Log it. Begin the morning render. Subject A-30 wakes at seven."
    stop music fadeout 2.0
    jump chapter1

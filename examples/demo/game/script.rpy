# Snapshot - tutorial and opening. The story continues in ch1.rpy .. ch4.rpy.
#
# Camera (see camera.rpy): a handheld crew is already filming. Human sprites
# are 460 px wide, so someone at xalign a has their face at a * 0.64 + 0.18:
# slightleft 0.32, center 0.5, slightright 0.68, right 0.82.

label start:
    camera
    scene black
    centered "Snapshot is a work of fiction. It touches on psychosis, hospitalisation, medication and drug use.\nIf any of that is close to home, please play gently."

    play music "audio/theme.ogg" fadein 1.0
    camera at est_orbit
    scene bg room with fade

    "This room sits behind the screen. Slide the 3D slider up to push it back."

    show mira happy at center, popin
    camera at doc_medium(0.5)
    m "Hi! I stand right on the screen plane, like a paper cut-out."
    camera at doc_close(0.5)
    m grin "And this textbox floats in front of me. Try it!"

    menu:
        m "How does it look?"

        "It pops out!":
            $ bond += 1
            m happy "That's the pop-up book effect."

        "I can't see any difference.":
            m curious "Is the slider all the way down?"
            jump tutorial_slider_help

    jump tutorial_park

label tutorial_slider_help:
    "Push the slider on the right edge of the top screen upwards."
    m happy "There we go."
    jump tutorial_park

label tutorial_park:
    camera at est_pan
    scene bg park with slowfade
    show mira happy at slightleft
    show aron smile at right
    with moveinright

    a "Did somebody say pop-up book?"
    camera at doc_wide
    show mira at bob
    m "Aron! You're standing a little nearer than me."

    camera at doc_medium(0.82)
    a grin "Why did the sprite never leave? It was too attached to its layer."
    camera at doc_punch(0.32)
    m surprised "..."
    camera at doc_medium(0.32)
    show aron happy
    m laugh "That's terrible. I love you anyway."

    camera at doc_wide
    show aron grin at center with move
    a "Watch this." with vpunch
    m happy "Okay, okay. That's the tutorial. Say goodbye, Aron."
    camera at doc_medium(0.5)
    a smile "Goodbye, tutorial."
    camera at doc_creep(0.5)
    a curious "..."
    a "Hey, Mira. Did the birds just stop moving?"
    show mira curious
    m "What birds?"
    stop music fadeout 2.0
    camera
    scene cg static with flash
    pause 0.4

    # The first cut away: someone was watching the tutorial.
    camera at est_orbit
    scene bg command with fade
    play music "audio/entities.ogg" fadein 2.0
    show seraph neutral at center, fadein
    se "Calibration complete."
    camera at doc_medium(0.5)
    se "Depth perception within tolerance. Attachment to the female unit: high. Humour: regrettable."
    camera at doc_close(0.5)
    se worried "And at the very end he noticed the birds."
    camera at doc_wide
    se neutral "Log it. Begin the morning render. Subject A-30 wakes at seven."
    se "And file the standard allowance. Every new subject gets one exception. His to spend."
    camera at doc_creep(0.5)
    sysmsg "Calibration complete. One exception granted."
    $ vn3ds_cheats += 1
    "(A cheat for the minigames is yours. You have [vn3ds_cheats].)"
    stop music fadeout 2.0
    camera
    jump chapter1

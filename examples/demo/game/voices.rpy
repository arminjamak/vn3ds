# Machine voices - speech-like syllables in no language, one pitch per
# character. On the 3DS, vn3ds plays single syllables from audio/vox/
# following the text (configured in vn3ds.json "voices"). In Ren'Py on a
# PC this callback plays the speaker's babble loop while their line types out.

init -5 python:
    renpy.music.register_channel("vox", "voice", loop=True)

    VOX_BABBLE = {
        "a": "babble_a", "m": "babble_m", "th": "babble_th", "dr": "babble_dr",
        "nu": "babble_nu", "se": "babble_se", "pi": "babble_pi", "dro": "babble_dro",
        "em": "babble_em", "pa": "babble_pa", "council": "babble_council",
        "stranger": "babble_stranger", "radio": "babble_radio",
    }

    def vox_callback(event, interact=True, **kwargs):
        if not interact:
            return
        who = getattr(store, "_last_say_who", None)
        name = VOX_BABBLE.get(who)
        if event == "show" and name:
            renpy.music.play("audio/vox/" + name + ".ogg", channel="vox", loop=True,
                             fadein=0.05, relative_volume=0.35)
        elif event in ("slow_done", "end"):
            renpy.music.stop(channel="vox", fadeout=0.1)

    config.all_character_callbacks.append(vox_callback)

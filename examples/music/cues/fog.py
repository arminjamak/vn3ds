"""Fog - life on the medication: crushing tiredness, lost hours, the bed.
Drowsy downtempo in a slow waltz, because My Buddy is a waltz.
Motifs: Aron's question slowed to half speed on a low flute, still not landing.
Sample: My Buddy (1922), pitched down a tone and stretched, as the bed of the
whole cue: a song about missing someone, heard through cotton."""
from vnsynth import *

s = Song(bpm=60, bars=20, key="A minor", beats_per_bar=3)
s.texture("tape", "tape", gain=0.6)
m = snap("my_buddy_1922", 104.0)
s.sample("buddy", "my_buddy_1922", start=m, length=6.0, every=4, fit=4,
         fx=["pitch-2", "stretch2", "dreamy", "warble", "lp1600"], gain=0.9, reverb=0.6, chorus_mix=0.3)
s.chords("pad", "Am9 Fmaj7 Cmaj7 E7sus4", inst=warm_pad, octave=3, bars_per_chord=2, gain=0.7, reverb=0.6)
s.chords("piano", "Am7 Fmaj7 Cmaj7 Em7", inst=felt_piano, octave=3, bars_per_chord=2, rhythm="x.....",
         gain=0.5, reverb=0.5)
s.notes("aron", "1 ~ ~ ~ 5 ~ | ~ ~ ~ ~ ~ ~ | 4 ~ ~ 3 ~ ~ | ~ ~ ~ ~ ~ ~ | 2 ~ ~ ~ ~ ~ | ~ ~ ~ ~ ~ ~ | ~ ~ ~ ~ ~ ~ | "
        "~ ~ ~ ~ ~ ~ | ~ ~ ~ ~ ~ ~ | ~ ~ ~ ~ ~ ~", inst=flute, octave=0, start_bar=0, gain=1.0, reverb=0.6,
        delay=0.2)
s.notes("bass", "1, _ _ _ _ _ | ~ ~ ~ ~ ~ ~ | 6,, _ _ _ _ _ | ~ ~ ~ ~ ~ ~ | 3, _ _ _ _ _ | ~ ~ ~ ~ ~ ~ | 5,, _ _ _ _ _ "
        "| ~ ~ ~ ~ ~ ~", inst=sub_bass, gain=0.4, legato=1.8)
s.drums("softkick: x........... | brush: ......x.....", gain=0.4, reverb=0.3)
s.render(out("fog"), lowpass_master=5000)

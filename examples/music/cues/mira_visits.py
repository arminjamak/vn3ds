"""Mira Visits - the love theme, built from the Mira motif: her warm turn, then
an answer that climbs to the sixth. The visits get harder, so the second half
of the progression leans into the minor.
Sample: Somebody Loves Me (1924) pitched into D-flat, reversed into a swell,
then forward and far, like a song she used to hum."""
from vnsynth import *

s = Song(bpm=70, bars=16, key="Db major")
s.texture("vinyl", "vinyl", gain=0.3)
s.chords("strings", "Dbmaj7 Bbm7 Gbmaj7 Ab7sus4 Fm7 Bbm9 Ebm9 Ab6", inst=strings, octave=3, bars_per_chord=2,
         gain=0.8, reverb=0.6, chorus_mix=0.3)
s.notes("guitar", "1 5 1' 3' 5' 3' 1' 5 | 1 5 1' 3' 5' 3' 1' 5 | 6, 3 6 1' 3' 1' 6 3 | 6, 3 6 1' 3' 1' 6 3 | "
        "4, 1 4 6 1' 6 4 1 | 4, 1 4 6 1' 6 4 1 | 5, 2 5 7b 2' 7b 5 2 | 5, 2 5 7b 2' 7b 5 2 | "
        "3, 7, 3 5 7 5 3 7, | 3, 7, 3 5 7 5 3 7, | 6, 3 6 1' 3' 1' 6 3 | 6, 3 6 1' 3' 1' 6 3 | "
        "2, 6, 2 4 6 4 2 6, | 2, 6, 2 4 6 4 2 6, | 5, 2 5 7b 2' 7b 5 2 | 5, 2 5 7b 2' 7b 5 2",
        inst=dream_guitar, octave=0, gain=0.8, chorus_mix=0.5, reverb=0.5, pan_=0.3, vel=0.7)
s.notes("love", MOTIFS["mira_love"], inst=felt_piano, octave=1, every=8, gain=1.0, reverb=0.5, delay=0.15)
s.notes("love_flute", MOTIFS["mira_love"], inst=flute, octave=1, start_bar=8, every=8, gain=0.6, reverb=0.6,
        pan_=-0.25)
s.notes("bass", "1, ~ ~ ~ ~ ~ ~ ~ | ~ ~ ~ ~ 5,, ~ ~ ~ | 6,, ~ ~ ~ ~ ~ ~ ~ | ~ ~ ~ ~ 3, ~ ~ ~ | 4,, ~ ~ ~ ~ ~ ~ ~ | "
        "~ ~ ~ ~ 1, ~ ~ ~ | 5,, ~ ~ ~ ~ ~ ~ ~ | ~ ~ ~ ~ 5,, ~ ~ ~ | 3, ~ ~ ~ ~ ~ ~ ~ | ~ ~ ~ ~ 7,, ~ ~ ~ | "
        "6,, ~ ~ ~ ~ ~ ~ ~ | ~ ~ ~ ~ 3, ~ ~ ~ | 2, ~ ~ ~ ~ ~ ~ ~ | ~ ~ ~ ~ 6,, ~ ~ ~ | 5,, ~ ~ ~ ~ ~ ~ ~ | "
        "~ ~ ~ ~ 5,, ~ ~ ~", inst=sub_bass, gain=0.6, legato=1.5)
s.drums("softkick: x.........x..... | brush: ....x.......x...", gain=0.35)
m = snap("somebody_loves_me_1924", 56.0)
s.sample("swell", "somebody_loves_me_1924", start=m, length=2.2, at_bar=[7], fit=1,
         fx=["pitch+3", "reverse", "78rpm", "dreamy", "swell"], gain=0.9, reverb=0.7)
s.sample("hum", "somebody_loves_me_1924", start=m, length=4.4, at_bar=[12], fit=2,
         fx=["pitch+3", "78rpm", "far", "wobble", "arch"], gain=0.8, reverb=0.6, pan_=-0.4)
s.render(out("mira_visits"))

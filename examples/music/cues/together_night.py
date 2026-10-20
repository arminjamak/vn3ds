"""Together Night - chapter 3's intimate night (fade to black). The love
theme at its most private. The two motifs talk, then intertwine: Mira's turn
on felt piano, Aron's question answering on flute; in the last four bars both
play at once and his question finally lands on her root.
Sample: Somebody Loves Me (1924), faint, stretched, in the next room."""
from vnsynth import *

s = Song(bpm=66, bars=16, key="Eb major")
s.texture("vinyl", "vinyl", gain=0.35)
s.chords("pad", "Ebmaj9 Cm9 Abmaj7 Bb6", inst=warm_pad, octave=3, bars_per_chord=2, gain=0.8, reverb=0.6)
s.notes("guitar", "1 5 1' 5 3' 5 1' 5 | 6, 3 6 3 1' 3 6 3 | 4, 1 4 1 6 1 4 1 | 5, 2 5 2 7 2 5 2", inst=dream_guitar,
        octave=0, every=8, gain=0.4, chorus_mix=0.6, reverb=0.55, pan_=0.3, vel=0.6)
s.motif("mira", "mira", inst=felt_piano, octave=1, end_bar=12, every=4, gain=0.95, reverb=0.5)
s.notes("aron", "~ ~ ~ ~ ~ ~ ~ ~ | ~ ~ ~ ~ ~ ~ ~ ~ | 1 ~ 5 ~ 4 3 ~ ~ | 2 ~ ~ ~ ~ ~ ~ ~", inst=flute, octave=1,
        end_bar=12, gain=0.85, reverb=0.55, pan_=-0.2)
# together: her love theme and his question at once, his last note resolving to her 1
s.notes("mira_love", MOTIFS["mira_love"], inst=felt_piano, octave=1, start_bar=12, gain=0.95, reverb=0.5)
s.notes("aron_with", "1' ~ 5 ~ 4 3 ~ ~ | 2 ~ ~ ~ ~ ~ ~ ~ | 1' ~ 5 ~ 6 5 ~ ~ | 2 ~ ~ ~ 1 ~ ~ ~", inst=flute, octave=1,
        start_bar=12, gain=0.75, reverb=0.6, pan_=-0.2)
s.notes("bass", "1, ~ ~ ~ ~ ~ ~ ~ | 1, ~ ~ ~ ~ ~ ~ ~ | 6,, ~ ~ ~ ~ ~ ~ ~ | 6,, ~ ~ ~ ~ ~ ~ ~ | "
        "4,, ~ ~ ~ ~ ~ ~ ~ | 4,, ~ ~ ~ ~ ~ ~ ~ | 5,, ~ ~ ~ ~ ~ ~ ~ | 5,, ~ ~ ~ ~ ~ ~ ~", inst=sub_bass, gain=0.55,
        legato=1.6)
s.drums("softkick: x.........x..... | brush: ....x.......x...", gain=0.3)
m = snap("somebody_loves_me_1924", 140.0)
s.sample("next_room", "somebody_loves_me_1924", start=m, length=4.4, at_bar=[2, 10], fit=4,
         fx=["stretch2", "78rpm", "far", "lp1300", "arch"], gain=0.85, reverb=0.7, pan_=0.4)
s.render(out("together_night"))

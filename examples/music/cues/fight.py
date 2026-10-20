"""Fight - Aron and Mira fight. Tense, driving, both of them talking over each
other: her motif in the minor on strings, his question cutting in on top of
it before she finishes, neither landing.
Sample: Somebody Loves Me (1924) reversed and a semitone flat through a
telephone: the love song turned against itself."""
from vnsynth import *

s = Song(bpm=104, bars=16, key="B minor")
s.texture("hiss", "tape", gain=0.5)
s.chords("stabs", "Bm Gmaj7 Em7 F#7sus4", inst=strings, octave=3, rhythm="x..x..x...x..x..", gain=0.75, reverb=0.4)
s.notes("pulse", "1, 1, 1, 1, 1, 1, 1, 1, | 6,, 6,, 6,, 6,, 6,, 6,, 6,, 6,, | 4,, 4,, 4,, 4,, 4,, 4,, 4,, 4,, | "
        "5,, 5,, 5,, 5,, 5,, 5,, 5,, 5,,", inst=round_bass, gain=0.35, reverb=0.05)
s.notes("mira", "3 4 5 ~ 3 ~ ~ ~ | 2 ~ ~ ~ ~ ~ ~ ~", inst=strings, octave=1, every=4, gain=1.0, reverb=0.5, pan_=-0.3)
s.notes("aron", "~ ~ ~ ~ ~ ~ ~ ~ | ~ ~ ~ ~ 1' ~ 5 ~ | 4 3 ~ ~ ~ ~ ~ ~ | ~ ~ ~ ~ ~ ~ ~ ~", inst=soft_lead, octave=1,
        every=4, gain=0.7, reverb=0.45, pan_=0.3)
s.fx("aron", sweep_lp=[(0, 900), (12, 2600), (16, 900)])
s.drums("tom: x..x..x.....x.x. | softkick: x.......x....... | hat: ..x...x...x...x. | snare: ....x.......x...",
        gain=0.45)
m = snap("somebody_loves_me_1924", 16.0)
s.sample("sour", "somebody_loves_me_1924", start=m, length=2.2, at_bar=[3, 7, 11, 15], fit=1,
         fx=["reverse", "pitch-1", "telephone", "swell"], gain=0.65, reverb=0.4, pan_=0.4)
s.render(out("fight"))

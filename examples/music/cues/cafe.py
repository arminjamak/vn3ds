"""Cafe - the cafe and its window, coffee with Mira in the protected world.
Lo-fi dream pop: chorused guitar, Rhodes, a tired boom-bap, vinyl.
Motifs: Mira's turn on vibes, a little too exactly on the beat (is she real?),
answered by a dream-pop guitar that isn't.
Sample: Somebody Loves Me (1924), pitched into F, as the lo-fi loop."""
from vnsynth import *

s = Song(bpm=82, bars=16, key="F major", swing=0.15)
s.texture("vinyl", "vinyl", gain=0.55)
m = snap("somebody_loves_me_1924", 132.0)
s.sample("loop", "somebody_loves_me_1924", start=m, length=8 * 0.262, every=2, fit=2,
         fx=["pitch+2", "lofi", "lp2200", "hp200", "wobble"], gain=0.4, reverb=0.3, duck=0.3)
s.chords("rhodes", "Fmaj9 Dm9 Bbmaj7 C7sus4", inst=glass_keys, octave=3, bars_per_chord=2, rhythm="x......x",
         gain=0.75, reverb=0.4, chorus_mix=0.4)
s.notes("guitar", "~ 5 1' 3' ~ 5 3' 1' | ~ 5 1' 3' ~ 5 3' 1' | ~ 3 6 1' ~ 3 1' 6 | ~ 3 6 1' ~ 3 1' 6 | "
        "~ 1 4 6 ~ 1 6 4 | ~ 1 4 6 ~ 1 6 4 | ~ 2 5 7b ~ 2 7b 5 | ~ 2 5 7b ~ 2 7b 5", inst=dream_guitar,
        octave=0, gain=0.5, chorus_mix=0.6, reverb=0.5, pan_=0.3, vel=0.7)
s.motif("mira", "mira", inst=mallet, octave=1, start_bar=4, every=4, gain=0.7, reverb=0.35)
s.notes("answer", "~ ~ ~ ~ ~ ~ ~ ~ | ~ ~ 3' ~ 2' ~ 1' ~ | 6 ~ ~ ~ ~ ~ ~ ~ | ~ ~ ~ ~ ~ ~ ~ ~", inst=dream_guitar,
        octave=0, start_bar=8, every=8, gain=0.9, chorus_mix=0.6, reverb=0.6, delay=0.25, pan_=-0.3)
s.notes("bass", "1, ~ ~ 1, ~ ~ ~ ~ | 1, ~ ~ 1, ~ ~ 5,, ~ | 6,, ~ ~ 6,, ~ ~ ~ ~ | 6,, ~ ~ 6,, ~ ~ 3, ~ | "
        "4,, ~ ~ 4,, ~ ~ ~ ~ | 4,, ~ ~ 4,, ~ ~ 1, ~ | 5,, ~ ~ 5,, ~ ~ ~ ~ | 5,, ~ ~ 5,, ~ ~ 2, ~",
        inst=round_bass, gain=0.5, reverb=0.05)
s.drums("softkick: x......x..x..... | snare: ....x.......x... | hat: x.x.x.x.x.x.x.x.", gain=0.45)
s.fx("drums_snare", crush=True, lp=4000)
s.render(out("cafe"))

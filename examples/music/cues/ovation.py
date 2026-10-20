"""Ovation - the Council erupts in ovation. Euphoric dream pop: everything
open, chorused guitars, a full soft kit, the choir.
Motifs: the Light as the chorus hook on lead and choir; Mira's turn answering
it on guitar (she is part of what he built); the Aron question, now
resolving every time.
Samples: Somebody Loves Me (1924) reversed into swells and a forward phrase;
Parade of the Wooden Soldiers tutti as distant applause from another age."""
from vnsynth import *

s = Song(bpm=104, bars=24, key="E major")
s.chords("pad", "Emaj9 C#m9 Amaj7 B6", inst=shimmer_pad, octave=3, bars_per_chord=2, gain=0.8, reverb=0.6, duck=0.5)
s.chords("choir", "E C#m A B", inst=choir, octave=3, bars_per_chord=2, start_bar=8, gain=0.55, reverb=0.7, duck=0.3)
s.notes("guitar", "1 5 1' 3' 5' 3' 1' 5 | 1 5 1' 3' 5' 3' 1' 5 | 6, 3 6 1' 3' 1' 6 3 | 6, 3 6 1' 3' 1' 6 3 | "
        "4, 1 4 6 1' 6 4 1 | 4, 1 4 6 1' 6 4 1 | 5, 2 5 7 2' 7 5 2 | 5, 2 5 7 2' 7 5 2", inst=dream_guitar, octave=0,
        gain=0.5, chorus_mix=0.6, reverb=0.5, delay=0.2, pan_=0.35, duck=0.3)
s.motif("light", "light", inst=soft_lead, octave=1, every=4, gain=0.85, reverb=0.55, delay=0.3)
s.notes("light_hi", MOTIFS["light"], inst=vocal_chop, octave=1, start_bar=16, every=4, gain=0.6, reverb=0.6,
        delay=0.3)
s.notes("mira", "~ ~ ~ ~ ~ ~ ~ ~ | ~ ~ ~ ~ ~ ~ ~ ~ | 3' 4' 5' ~ 3' ~ ~ ~ | 2' ~ 1' ~ ~ ~ ~ ~", inst=dream_guitar,
        octave=0, start_bar=8, every=4, gain=0.9, chorus_mix=0.6, reverb=0.55, pan_=-0.35)
s.notes("bass", "1, ~ 1, ~ 1, ~ 1, 5,, | 1, ~ 1, ~ 1, ~ 1, ~ | 6,, ~ 6,, ~ 6,, ~ 6,, 3, | 6,, ~ 6,, ~ 6,, ~ 6,, ~ | "
        "4,, ~ 4,, ~ 4,, ~ 4,, 1, | 4,, ~ 4,, ~ 4,, ~ 4,, ~ | 5,, ~ 5,, ~ 5,, ~ 5,, 2, | 5,, ~ 5,, ~ 5,, ~ 5,, ~",
        inst=round_bass, gain=0.5, reverb=0.05, duck=0.4)
s.drums("kick: x.......x.x..... | snare: ....x.......x... | hat: x.x.x.x.x.x.x.x. | tom: ..............xx",
        gain=0.45)
m = snap("somebody_loves_me_1924", 140.0)
s.sample("swell", "somebody_loves_me_1924", start=m, length=2.3, at_bar=[7, 15, 23], fit=1,
         fx=["pitch+1", "reverse", "78rpm", "dreamy", "swell"], gain=0.9, reverb=0.6)
s.sample("phrase", "somebody_loves_me_1924", start=m, length=4.6, at_bar=[12], fit=2,
         fx=["pitch+1", "78rpm", "far", "arch"], gain=0.8, reverb=0.6, pan_=-0.4)
w = snap("wooden_soldiers_1923", 120.0)
s.sample("applause", "wooden_soldiers_1923", start=w, length=4.0, at_bar=[0, 16], fit=8,
         fx=["stretch3", "far", "lp1400", "arch"], gain=0.7, reverb=0.8)
s.render(out("ovation"))

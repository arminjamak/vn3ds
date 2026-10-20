"""Umbrella Rain - the rainy street; Aron gives his umbrella to a soaked
stranger who doesn't exist. Tender. This is why Ember starts watching.
Motifs: Aron's question softened on felt piano; the first, unnoticed hint of
the Lantern's three flickers on glass harmonica.
Sample: My Buddy (1922), a phrase from a doorway, pitched into A-flat."""
from vnsynth import *

s = Song(bpm=66, bars=12, key="Ab major")
s.texture("rain", "softrain", gain=0.55)
s.chords("pad", "Abmaj7 Fm9 Dbmaj7 Eb6", inst=warm_pad, octave=3, gain=0.8, reverb=0.6)
s.notes("piano", "1 ~ 3 5 ~ 3 1' ~ | 6, ~ 1 3 ~ 5 3 ~ | 4, ~ 6, 1 ~ 3 4 ~ | 5, ~ 2 5 ~ 6 5 ~",
        inst=felt_piano, octave=1, gain=0.55, reverb=0.5, pan_=0.2)
s.motif("aron", "aron", inst=felt_piano, octave=1, start_bar=2, every=4, gain=0.8, reverb=0.55, delay=0.2,
        pan_=-0.15)
s.notes("flicker", "5 ~ 5 ~ 5 ~ 6 1' | ~ ~ ~ ~ ~ ~ ~ ~", inst=glass_harmonica, octave=1, start_bar=9, end_bar=11,
        gain=1.2, reverb=0.7, delay=0.3)
s.notes("bass", "1, ~ ~ ~ ~ ~ ~ ~ | 6,, ~ ~ ~ ~ ~ ~ ~ | 4,, ~ ~ ~ ~ ~ ~ ~ | 5,, ~ ~ ~ ~ ~ ~ ~", inst=sub_bass, gain=0.6)
s.drums("softkick: x.........x..... | brush: ....x.......x...", gain=0.35, reverb=0.3)
m = snap("my_buddy_1922", 132.0)
s.sample("buddy", "my_buddy_1922", start=m, length=3.0, at_bar=[5], fit=2,
         fx=["pitch+4", "78rpm", "far", "wobble", "arch"], gain=0.9, reverb=0.7, pan_=0.4)
s.render(out("umbrella_rain"))

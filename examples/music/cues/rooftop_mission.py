"""Rooftop Mission - the night city, the three flickers at exactly the moment
he needs a sign, the decision that understanding this is his secret life's
mission. Resolve. The Aron motif grows: plain, then asked twice and higher,
then carried by strings and lead together.
Motifs: Aron (plain -> rising -> doubled); the Lantern's flickers at bar 8.
Sample: April Showers (1921) reversed into swells at each new section:
"though April showers may come your way"."""
from vnsynth import *

s = Song(bpm=92, bars=24, key="A minor")
s.texture("wind", "wind", gain=0.5)
s.chords("pad", "Am9 Fmaj7 Cmaj7 G6", inst=shimmer_pad, octave=3, bars_per_chord=2, gain=0.75, reverb=0.6,
         duck=0.4)
s.notes("guitar", "1 5 1' 5 3' 5 1' 5 | 1 5 1' 5 3' 5 1' 5 | 6, 3 6 3 1' 3 6 3 | 6, 3 6 3 1' 3 6 3 | "
        "4, 1 4 1 6 1 4 1 | 4, 1 4 1 6 1 4 1 | 5, 2 5 2 7 2 5 2 | 5, 2 5 2 7 2 5 2",
        inst=dream_guitar, octave=1, gain=0.45, chorus_mix=0.5, reverb=0.5, delay=0.2, pan_=0.3, vel=0.7)
s.motif("aron", "aron", inst=glass_keys, octave=1, end_bar=8, every=4, gain=0.9, reverb=0.5, delay=0.25)
s.notes("flicker", "5 ~ 5 ~ 5 ~ 6 1' | ~ ~ ~ ~ ~ ~ ~ ~", inst=glass_harmonica, octave=1, start_bar=8, end_bar=10,
        gain=1.0, reverb=0.7, delay=0.3, pan_=-0.3)
s.notes("rising", MOTIFS["aron_rising"], inst=flute, octave=1, start_bar=10, end_bar=16, every=6, gain=1.0,
        reverb=0.55, delay=0.2)
s.notes("rising_str", MOTIFS["aron_rising"], inst=strings, octave=1, start_bar=16, end_bar=24, gain=0.9, reverb=0.6)
s.notes("rising_lead", MOTIFS["aron_rising"], inst=soft_lead, octave=1, start_bar=16, end_bar=22, gain=0.6,
        reverb=0.6, delay=0.3)
s.notes("bass", "1, ~ ~ 1, ~ ~ 1, ~ | 1, ~ ~ 1, ~ ~ 5,, ~ | 6,, ~ ~ 6,, ~ ~ 6,, ~ | 6,, ~ ~ 6,, ~ ~ 3, ~ | "
        "4,, ~ ~ 4,, ~ ~ 4,, ~ | 4,, ~ ~ 4,, ~ ~ 1, ~ | 5,, ~ ~ 5,, ~ ~ 5,, ~ | 5,, ~ ~ 5,, ~ ~ 2, ~",
        inst=round_bass, gain=0.5, reverb=0.05, duck=0.3)
s.drums("softkick: x.......x....... | shaker: ..x...x...x...x.", end_bar=8, gain=0.45)
s.drums("softkick: x.......x.x..... | snare: ....x.......x... | shaker: ..x...x...x...x.", start_bar=8, end_bar=16,
        gain=0.45)
s.drums("kick: x.......x.x..... | snare: ....x.......x... | hat: x.x.x.x.x.x.x.x. | tom: ............x.x.",
        start_bar=16, end_bar=22, gain=0.45)
s.drums("softkick: x.......x....... | shaker: ..x...x...x...x.", start_bar=22, gain=0.45)
a = snap("april_showers_1921", 52.0)
s.sample("swell", "april_showers_1921", start=a, length=2.6, at_bar=[7, 15, 23], fit=1,
         fx=["pitch-5", "reverse", "78rpm", "dreamy", "swell"], gain=0.9, reverb=0.6)
s.render(out("rooftop_mission"))

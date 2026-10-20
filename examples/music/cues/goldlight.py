"""Goldlight - the light technique: matter out of nothing, beam-like golden
energy, the new coat of the elevated being. Radiant.
Motifs: the Light in full, on glass harmonica and choir, every phrase landing;
a shimmer of arpeggios like particles condensing.
Sample: April Showers (1921) stretched six-fold into a golden haze: the
first morning transfigured."""
from vnsynth import *

s = Song(bpm=72, bars=16, key="E lydian")
s.texture("air", "room", gain=0.4)
s.chords("pad", "Emaj7#11 C#m9 Amaj9 B6add9", inst=shimmer_pad, octave=3, bars_per_chord=2, gain=0.8, reverb=0.7)
s.chords("choir", "Emaj7 C#m7 Amaj7 B6", inst=choir, octave=3, bars_per_chord=2, gain=0.55, reverb=0.8)
s.notes("sparkle", "1' 5 3' 5 2' 5 1' 5 | 1' 6 3' 6 1' 6 5' 6 | 6 4 1' 4 6 4 3' 4 | 7 5 2' 5 7 5 1' 5", inst=mallet,
        octave=1, every=8, gain=0.4, reverb=0.6, delay=0.35, pan_=0.3)
s.motif("light", "light", inst=glass_harmonica, octave=1, every=4, gain=1.0, reverb=0.65, delay=0.25)
s.notes("light_lead", MOTIFS["light"], inst=flute, octave=1, start_bar=8, every=4, gain=0.6, reverb=0.6, pan_=-0.3)
s.notes("bass", "1, _ _ _ _ _ _ _ | 1, _ _ _ _ _ _ _ | 6,, _ _ _ _ _ _ _ | 6,, _ _ _ _ _ _ _ | "
        "4,, _ _ _ _ _ _ _ | 4,, _ _ _ _ _ _ _ | 5,, _ _ _ _ _ _ _ | 5,, _ _ _ _ _ _ _", inst=sub_bass, gain=0.5)
s.drums("softkick: x.........x..... | shaker: ..x...x...x...x.", gain=0.3)
a = snap("april_showers_1921", 152.0)
s.sample("haze", "april_showers_1921", start=a, length=1.4, at_bar=[0, 8], fit=8,
         fx=["pitch+4", "stretch6", "dreamy", "hp250", "arch"], gain=0.9, reverb=0.8, chorus_mix=0.4)
s.render(out("goldlight"), reverb_seconds=6.0)

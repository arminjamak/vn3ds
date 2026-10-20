"""The Hungry Sky - Heaven's Gate Defence: the angels hold the gate while the
hungry ones come down. Driving and celestial: angelic choir pads and bowed
glass above, a hungry low pulse below that gulps on every eighth note.
Motifs: the System as the angels' brass fanfare (as in `angel_ops`, same
key); Ashveil's chromatic descent creeping up from the bass in the second
half, the hunger getting closer; the Lantern's flickers on glass, high, a
small light holding.
Samples: Parade of the Wooden Soldiers (1923), the angels' procedure;
The St. Louis Blues (1925) pitched down into a dark smear, the hunger."""
from vnsynth import *
from _mg import SUB, hungry_bass

s = Song(bpm=120, bars=24, key="B minor")      # 48.0 s, exactly 1 536 000 samples
s.texture("wind", "wind", gain=0.35)
s.chords("choir", "Bm9 Gmaj7 Dmaj7 F#7", inst=choir, octave=3, bars_per_chord=2, gain=0.85, reverb=0.8,
         duck=0.35)
s.chords("choir_hi", "Bm Gmaj7 D F#", inst=choir, octave=4, bars_per_chord=2, start_bar=8, gain=0.55,
         reverb=0.85, duck=0.35)
s.chords("glass", "Bm9 Gmaj7 Dmaj7 F#7", inst=shimmer_pad, octave=4, bars_per_chord=2, gain=0.3, reverb=0.7,
         duck=0.4)
# the hungry pulse: eighths, a gulp on every one
s.notes("hunger", "1, 1, 1, 1, 1, 1, 1, 1, | 1, 1, 1, 1, 1, 1, 7,, 1, | 6,, 6,, 6,, 6,, 6,, 6,, 6,, 6,, | "
        "6,, 6,, 6,, 6,, 6,, 6,, 5,, 6,, | 3, 3, 3, 3, 3, 3, 3, 3, | 3, 3, 3, 3, 3, 3, 2, 3, | "
        "5,, 5,, 5,, 5,, 5,, 5,, 5,, 5,, | 5,, 5,, 5,, 5,, 5,, @6,, 5,, @6,,", inst=hungry_bass, octave=-1,
        gain=0.5, reverb=0.03, legato=0.8, duck=0.25)
s.notes("arp", "1' 5 3' 5 1' 5 2' 5 | 1' 5 3' 5 1' 5 2' 5 | 1' 3 6 3 1' 3 7 3 | 1' 3 6 3 1' 3 7 3 | "
        "1' 5 3' 5 1' 5 2' 5 | 1' 5 3' 5 1' 5 2' 5 | 2' 7# 5 7# 2' 7# 4' 7# | 2' 7# 5 7# 2' 7# 4' 7#",
        inst=glass_keys, octave=1, start_bar=8, gain=0.32, reverb=0.45, delay=0.25, pan_=0.3, vel=0.7)
s.notes("fanfare", "1 1 1 ~ 7, ~ ~ ~ | ~ ~ ~ ~ ~ ~ ~ ~ | 6, 6, 6, ~ 5, ~ ~ ~ | ~ ~ ~ ~ 5, ~ 7#, ~",
        inst=soft_brass, octave=1, start_bar=4, end_bar=16, every=8, gain=0.75, reverb=0.5)
s.notes("lantern", MOTIFS["lantern"], inst=glass_harmonica, octave=2, start_bar=2, end_bar=8, every=4, gain=0.45,
        reverb=0.7, delay=0.3, pan_=-0.3)
s.notes("descent", MOTIFS["ashveil"], inst=strings, octave=-1, start_bar=16, every=4, legato=1.1, gain=0.8,
        reverb=0.5)
s.drums("kick: x...x...x...x... | snare: ....x.......x... | shaker: x.x.x.x.x.x.x.x.", gain=0.45)
s.drums("openhat: ..x...x...x...x.", start_bar=8, gain=0.4)
s.drums("tom: ..........x.x.x.", start_bar=7, end_bar=8, gain=0.45)
s.drums("tom: ..........x.x.x.", start_bar=15, end_bar=16, gain=0.45)
s.drums("tom: ........x.x.x.xx", start_bar=23, end_bar=24, gain=0.45)
w = snap("wooden_soldiers_1923", 100.0)
s.sample("soldiers", "wooden_soldiers_1923", start=w, length=4 * 0.578, at_bar=[3, 11, 19], fit=1,
         fx=["78rpm", "lp2400", "arch"], gain=0.55, reverb=0.45, pan_=-0.25)
b = snap("st_louis_blues_1925", 24.0)
s.sample("smear", "st_louis_blues_1925", start=b, length=4.0, at_bar=[16], fit=8,
         fx=["pitch-12", "stretch2", "lp1000", "hp120", "arch"], gain=0.85, reverb=0.6, chorus_mix=0.3)
s.render(out("invaders", sub=SUB))

"""The Hungry Sky: the vampire - the energy-vampire boss of Heaven's Gate
Defence. Bigger, darker, childlike: a toddler's music box over a bass the
size of a galaxy that opens its mouth on every beat; still the score's dream
pop (chorused pad, glass, the choir from `invaders`).
Motifs: Ashveil's music box (`ashveil_box`, as in `council`, same key) in two
octaves; his chromatic descent as the bass line itself (C, B, Bb, A, Ab);
the Lantern's three flickers once, high and small, refusing to go out.
Samples: The St. Louis Blues (1925), Bessie Smith and Louis Armstrong
pitched down into a breathing smear, and a warbling fragment close by."""
from vnsynth import *
from _mg import SUB, hungry_bass

s = Song(bpm=96, bars=16, key="C minor")       # 40.0 s, exactly 1 280 000 samples
s.texture("room", "room", gain=0.6)
# the descent is the bass: one bar per step, the last phrase sinking one step further
roots = ["1,", "@-1,", "@-2,", "@-3,"] * 3 + ["1,", "@-1,", "@-2,", "@-4,"]
for bar, r in enumerate(roots):
    s.notes("hunger", f"{r} _ _ {r} _ _ {r} _", inst=hungry_bass, octave=0, start_bar=bar, end_bar=bar + 1,
            gain=0.7, reverb=0.03, legato=1.0, duck=0.2)
    s.notes("drone", f"{r} _ _ _", inst=deep_drone, octave=0, start_bar=bar, end_bar=bar + 1, gain=0.4, reverb=0.5,
            legato=1.0)
chords = ["Cm", "G", "Gm", "F"] * 3 + ["Cm", "G", "Gm", "Abmaj7"]
for bar, c in enumerate(chords):
    s.chords("choir", c, inst=choir, octave=3, start_bar=bar, end_bar=bar + 1, gain=0.7, reverb=0.8, duck=0.3)
    s.chords("pad", c, inst=shimmer_pad, octave=4, start_bar=bar, end_bar=bar + 1, gain=0.28, reverb=0.7,
             chorus_mix=0.5, duck=0.4)
s.notes("box", MOTIFS["ashveil_box"], inst=music_box, octave=1, every=2, gain=0.9, reverb=0.55, delay=0.3, pan_=0.25)
s.notes("box_hi", MOTIFS["ashveil_box"], inst=music_box, octave=2, start_bar=8, every=4, gain=0.5, reverb=0.6,
        delay=0.35, pan_=-0.3)
s.notes("lantern", MOTIFS["lantern"], inst=glass_harmonica, octave=2, start_bar=12, end_bar=14, gain=0.45,
        reverb=0.7, delay=0.3, pan_=-0.35)
s.drums("kick: x.....x...x..... | clap: ........x....... | hat: x.x.x.x.x.x.x.x.", gain=0.5)
s.drums("heartbeat: x...............", gain=0.35)
for b in (3, 7, 11):
    s.drums("tom: x...........x.x.", start_bar=b, end_bar=b + 1, gain=0.45, reverb=0.5)
s.drums("tom: x.......x.x.x.xx", start_bar=15, end_bar=16, gain=0.45, reverb=0.5)
b = snap("st_louis_blues_1925", 24.0)
s.sample("bessie", "st_louis_blues_1925", start=b, length=4.0, at_bar=[0, 8], fit=8,
         fx=["pitch-14", "stretch2", "lp1100", "hp120", "arch"], gain=0.9, reverb=0.7, chorus_mix=0.3)
h = snap("st_louis_blues_1925", 112.0)
s.sample("bessie_hi", "st_louis_blues_1925", start=h, length=2.0, at_bar=[5, 13], fit=2,
         fx=["pitch-2", "78rpm", "far", "warble", "arch"], gain=0.7, reverb=0.7, pan_=-0.4)
s.render(out("invaders_boss", sub=SUB))

"""Worlds Upon Worlds - the coda's reveal: worlds upon worlds upon worlds, his
changes rippling through one subsection of the whole organism; other
councils, other architects arguing for their worlds.
Motifs: the Light at three speeds at once (a canon at 1x, 2x and 1/2x, in
three octaves and places), like the same idea occurring in different worlds;
the System's pulses as the organism's slow heartbeat.
Samples: fragments of four different records at once, far and panned,
other worlds' radios: Ogopogo, Krooked Blues, April Showers, My Buddy."""
from vnsynth import *

s = Song(bpm=64, bars=16, key="B lydian")
s.texture("air", "room", gain=0.5)
s.chords("pad", "Bmaj7#11 G#m9 Emaj9 F#6add9", inst=shimmer_pad, octave=3, bars_per_chord=4, gain=0.8, reverb=0.7)
s.fx("pad", lp=1800)
s.notes("light", MOTIFS["light"], inst=glass_keys, octave=1, every=4, gain=0.8, reverb=0.6, delay=0.3)
s.fx("light", lp=1600)
# the same idea twice as fast, higher, on the right
s.notes("light_fast", "1 5 4 3 2 3 5 1' | ~ ~ ~ ~ ~ ~ ~ ~", inst=mallet, octave=1, start_bar=2, every=2, gain=0.55,
        reverb=0.6, delay=0.3, pan_=0.6)
# and half as fast, low, on the left
s.notes("light_slow", "1 _ _ _ 5 _ _ _ | 4 _ 3 _ _ _ _ _ | 2 _ _ _ 3 _ _ _ | 5 _ _ _ 1' _ _ _", inst=strings,
        octave=0, start_bar=4, every=8, gain=0.75, reverb=0.6, pan_=-0.5)
s.notes("pulse", MOTIFS["system"], inst=pulse_blip, octave=1, every=4, gain=0.7, reverb=0.6)
s.notes("bass", "1, _ _ _ _ _ _ _", inst=sub_bass, every=4, legato=4.0, gain=0.5)
s.drums("softkick: x...............", gain=0.35, reverb=0.4)
for name, src, t, bar, p, fx in [("w_ogo", "ogopogo_1925", 148.0, 1, -0.7, "pitch+3"),
                                 ("w_krooked", "krooked_blues_1923", 56.0, 5, 0.7, "pitch-6"),
                                 ("w_april", "april_showers_1921", 116.0, 9, -0.5, "pitch-1"),
                                 ("w_buddy", "my_buddy_1922", 132.0, 13, 0.5, "pitch+7")]:
    s.sample(name, src, start=snap(src, t), length=2.6, at_bar=[bar], fit=3,
             fx=[fx, "stretch2", "78rpm", "far", "arch"], gain=0.8, reverb=0.8, pan_=p)
s.render(out("worlds_upon_worlds"), reverb_seconds=6.0)

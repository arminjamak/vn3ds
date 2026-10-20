"""Deepest Layer - behind everything, the superintelligence being built,
hiding inside the world-building processes: LOOM, ORCHARD, MERIDIAN,
TIDEWATER. Vast and cold.
Motifs: the System's three pulses as four separate processes in canon, each
in its own octave, place and tempo (one every bar, every 1.5, 2 and 3 bars),
drifting in and out of sync; underneath, a glacier of a drone.
Sample: Parade of the Wooden Soldiers (1923) stretched eightfold into a frozen
chord, the toy march as machinery."""
from vnsynth import *

s = Song(bpm=60, bars=16, key="C# phrygian")
s.texture("air", "room", gain=0.6)
s.notes("drone", "1, _ _ _ _ _ _ _ | 1, _ _ _ _ _ _ _ | 2b, _ _ _ _ _ _ _ | 1, _ _ _ _ _ _ _", inst=deep_drone,
        every=4, legato=1.3, gain=0.6, reverb=0.6)
s.chords("glass", "C#sus2 Dmaj7 C#sus2 Bm", inst=glass_harmonica, octave=3, bars_per_chord=4, gain=0.7, reverb=0.8)
SYS = "1 1 1 ~ 7, ~ ~ ~"
s.notes("loom", SYS, inst=pulse_blip, octave=2, every=1, gain=0.5, reverb=0.6, delay=0.3, pan_=-0.6)
s.notes("orchard", SYS, inst=pulse_blip, octave=1, every=2, gain=0.6, reverb=0.6, delay=0.3, pan_=0.6)
s.notes("meridian", SYS, inst=glass_keys, octave=1, start_bar=1, every=3, gain=0.5, reverb=0.7, pan_=-0.2)
s.notes("tidewater", SYS, inst=sub_bass, octave=0, start_bar=2, every=4, gain=0.5, reverb=0.3, pan_=0.2)
s.notes("ghost", MOTIFS["aron"], inst=glass_harmonica, octave=1, start_bar=10, end_bar=12, gain=0.9, reverb=0.8)
w = snap("wooden_soldiers_1923", 84.0)
s.sample("frozen", "wooden_soldiers_1923", start=w, length=1.0, at_bar=[0, 8], fit=8,
         fx=["pitch+2", "stretch8", "lp1200", "hp150", "arch"], gain=1.0, reverb=0.8)
s.render(out("deepest_layer"), reverb_seconds=6.0)

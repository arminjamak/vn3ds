"""Ember Trial - the Lantern Watch caught helping; Ember on trial before the
Council and the corps. Solemn, under threat of decommissioning.
Motifs: the Lantern's flickers in the minor on a fragile music box, the third
flicker missing (then, defiantly, all three); Ashveil's descent in the low
strings; a slow gavel.
Sample: Parade of the Wooden Soldiers (1923) an octave down and stretched:
procedure as a funeral march."""
from vnsynth import *

s = Song(bpm=76, bars=16, key="G minor")
s.texture("room", "room", gain=0.6)
s.notes("drone", "1, _ _ _ _ _ _ _", inst=deep_drone, every=4, legato=4.2, gain=0.5, reverb=0.6)
s.chords("choir", "Gm Ebmaj7 Cm9 D7sus4", inst=choir, octave=3, bars_per_chord=2, gain=0.75, reverb=0.7)
s.notes("flicker", "5 ~ 5 ~ ~ ~ ~ ~ | ~ ~ ~ ~ ~ ~ ~ ~ | 5 ~ 5 ~ ~ ~ ~ ~ | ~ ~ ~ ~ ~ ~ ~ ~ | "
        "5 ~ 5 ~ ~ ~ ~ ~ | ~ ~ ~ ~ ~ ~ ~ ~ | 5 ~ 5 ~ 5 ~ 6 1' | ~ ~ ~ ~ ~ ~ ~ ~", inst=music_box, octave=1, gain=0.9,
        reverb=0.6, delay=0.35, pan_=0.25)
s.notes("descent", MOTIFS["ashveil"], inst=strings, octave=0, start_bar=4, every=4, legato=1.2, gain=0.8, reverb=0.6)
s.drums("tom: x............... | softkick: x.......x.......", gain=0.4, reverb=0.5)
w = snap("wooden_soldiers_1923", 116.0)
s.sample("procedure", "wooden_soldiers_1923", start=w, length=4 * 0.578, at_bar=[0, 8], fit=4,
         fx=["pitch-12", "stretch2", "78rpm", "lp1500", "arch"], gain=0.9, reverb=0.6, pan_=-0.3)
s.render(out("ember_trial"))

"""Council - the energy vampires meet: Ashveil and the others, feeding,
politics, arguing over a quarantine that has already happened. Vast and
childlike: a music box over drones the size of galaxies.
Motifs: Ashveil's slow chromatic descent twice: as a toddler's music box
(with its little hungry leap) and as a deep string line under the floor.
Sample: The St. Louis Blues (1925), Bessie Smith and Louis Armstrong pitched
down and stretched into a dark, breathing smear."""
from vnsynth import *

s = Song(bpm=60, bars=16, key="C minor")
s.texture("room", "room", gain=0.7)
s.notes("drone", "1, _ _ _ _ _ _ _ | 1, _ _ _ _ _ _ _ | 6,, _ _ _ _ _ _ _ | 6,, _ _ _ _ _ _ _", inst=deep_drone,
        legato=1.2, gain=0.6, reverb=0.6)
s.chords("choir", "Cm Abmaj7 Fm Gsus4", inst=choir, octave=2, bars_per_chord=4, gain=0.6, reverb=0.8)
s.notes("box", MOTIFS["ashveil_box"], inst=music_box, octave=1, every=4, gain=0.9, reverb=0.6, delay=0.35, pan_=0.25)
s.notes("descent", MOTIFS["ashveil"], inst=strings, octave=0, start_bar=8, every=4, legato=1.2, gain=0.9,
        reverb=0.6)
s.drums("tom: x............... | softkick: x.......x.......", gain=0.4, reverb=0.5)
b = snap("st_louis_blues_1925", 24.0)
s.sample("bessie", "st_louis_blues_1925", start=b, length=4.0, at_bar=[0, 8], fit=8,
         fx=["pitch-14", "stretch2", "lp1100", "hp120", "arch"], gain=1.0, reverb=0.7, chorus_mix=0.3)
h = snap("st_louis_blues_1925", 112.0)
s.sample("bessie_hi", "st_louis_blues_1925", start=h, length=2.0, at_bar=[5, 13], fit=2,
         fx=["pitch-2", "78rpm", "far", "warble", "arch"], gain=0.8, reverb=0.7, pan_=-0.4)
s.render(out("council"))

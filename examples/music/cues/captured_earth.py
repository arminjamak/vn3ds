"""Captured Earth - the real Earth in its invisible cage, its people
experiencing the occupation as something spiritual, as God. Choir and organ,
god-like awe, and something mechanical under the hymn.
Motifs: the System's three pulses slowed to whole notes in the organ pedal
(the occupier inside the hymn); Aron's question in awe on high strings.
Sample: The St. Louis Blues (1925) harmonium and cornet, stretched into a
hymn-like smear: the same hungry beings, worshipped."""
from vnsynth import *

s = Song(bpm=63, bars=16, key="Db lydian")
s.texture("air", "room", gain=0.5)
s.chords("choir", "Dbmaj7 Ebsus4 Bbm7 Gbmaj7#11", inst=choir, octave=3, bars_per_chord=2, gain=0.9, reverb=0.8)
s.chords("organ", "Dbmaj9 Eb6 Bbm9 Gbmaj7", inst=organ, octave=3, bars_per_chord=2, gain=0.6, reverb=0.6)
s.notes("pedal", "1, _ _ _ _ _ _ _ | 1, _ _ _ _ _ _ _ | 1, _ _ _ _ _ _ _ | 7,, _ _ _ _ _ _ _", inst=organ, octave=-1,
        gain=0.7, reverb=0.5)
s.notes("awe", MOTIFS["aron"], inst=strings, octave=2, start_bar=4, every=4, gain=0.8, reverb=0.7)
s.drums("tom: x............... ", gain=0.35, reverb=0.6)
b = snap("st_louis_blues_1925", 8.0)
s.sample("hymn", "st_louis_blues_1925", start=b, length=3.0, at_bar=[0, 8], fit=8,
         fx=["pitch-1", "stretch3", "lp1600", "hp200", "arch"], gain=0.95, reverb=0.8, chorus_mix=0.3)
s.render(out("captured_earth"), reverb_seconds=6.0)

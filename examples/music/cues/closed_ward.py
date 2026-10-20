"""Closed Ward - the ward, Dr. Okafor, Nurse Hale, the fluorescent hum.
Sterile and uneasy, but not cruel: the staff are kind. Also aliased as `ward`.
Motifs: the 7:07 clock as the ward clock (an exact sine ping, the seventh
slightly wrong); Aron's question in fragments on felt piano, too tired to finish.
Sample: April Showers frozen into a pale drone, the morning behind glass."""
from vnsynth import *

s = Song(bpm=64, bars=12, key="F# phrygian")
s.texture("hum", "hum", gain=0.7)
s.chords("glass", "F#m G F#sus2 Em7", inst=glass_harmonica, octave=3, bars_per_chord=3, gain=0.8, reverb=0.7)
s.notes("clock", "1 ~ ~ @11 ~ ~ 1 ~", inst=pulse_blip, octave=2, every=2, gain=0.55, reverb=0.5, delay=0.2,
        pan_=0.3)
s.notes("aron", "1 ~ 5 ~ ~ ~ ~ ~ | ~ ~ ~ ~ ~ ~ ~ ~ | 4 3 ~ ~ ~ ~ ~ ~ | ~ ~ ~ ~ ~ ~ ~ ~", inst=felt_piano, octave=1,
        start_bar=2, every=6, gain=0.8, reverb=0.6, pan_=-0.2)
s.notes("bass", "1, _ _ _ _ _ _ _", inst=sub_bass, every=3, legato=2.0, gain=0.5)
s.drums("tick: x.......x.......", gain=0.3)
a = snap("april_showers_1921", 116.0)
s.sample("frozen", "april_showers_1921", start=a, length=0.8, at_bar=[0, 6], fit=6,
         fx=["pitch+6", "stretch6", "lp1200", "hp200", "arch"], gain=1.0, reverb=0.8)
s.render(out("closed_ward"))

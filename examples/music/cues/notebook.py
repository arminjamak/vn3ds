"""Notebook - Aron at the desk, the wall of notes, the first line: "If this is
a test, I want to pass it by being kind." Introspective.
Motifs: Aron's question on felt piano, with a new answering phrase that
almost resolves (it will return, completed, as the Light); a pen-and-clock tick.
Sample: Farewell Blues (1923), very far and slow: the record that closes the
story is already on, in another room."""
from vnsynth import *

s = Song(bpm=70, bars=16, key="B minor")
s.texture("tape", "tape", gain=0.5)
s.chords("pad", "Bm9 Gmaj7 Dmaj7 A6", inst=warm_pad, octave=3, bars_per_chord=2, gain=0.75, reverb=0.6)
s.motif("aron", "aron", inst=felt_piano, octave=1, every=4, gain=0.9, reverb=0.45)
s.notes("thought", "~ ~ ~ ~ ~ ~ ~ ~ | ~ ~ 3 ~ 4 ~ 5 ~ | 3 ~ ~ ~ 2 ~ ~ ~ | ~ ~ ~ ~ ~ ~ ~ ~", inst=felt_piano, octave=1,
        start_bar=4, every=8, gain=0.75, reverb=0.5, pan_=0.2)
s.notes("glass", "5' ~ ~ ~ ~ ~ ~ ~ | 3' ~ ~ ~ ~ ~ ~ ~", inst=glass_harmonica, octave=1, start_bar=8, every=4,
        gain=1.0, reverb=0.7, pan_=-0.3)
s.notes("bass", "1, ~ ~ ~ ~ ~ ~ ~ | 1, ~ ~ ~ ~ ~ 5,, ~ | 6,, ~ ~ ~ ~ ~ ~ ~ | 6,, ~ ~ ~ ~ ~ ~ ~ | "
        "3, ~ ~ ~ ~ ~ ~ ~ | 3, ~ ~ ~ ~ ~ ~ ~ | 7,, ~ ~ ~ ~ ~ ~ ~ | 7,, ~ ~ ~ ~ ~ ~ ~", inst=sub_bass, gain=0.6)
s.drums("tick: x...x...x...x... | softkick: x......x..x.....", gain=0.35)
f = snap("farewell_blues_1923", 140.0)
s.sample("farewell", "farewell_blues_1923", start=f, length=2.8, at_bar=[2, 10], fit=4,
         fx=["pitch-3", "stretch2", "78rpm", "far", "arch"], gain=1.0, reverb=0.8, pan_=-0.4)
s.render(out("notebook"))

"""The Record - the ultimate twist: everything was an archived life. "Subject
A-30. Architect. Status: eternal. Companions: none." The golden figure,
alone, building worlds without stopping. Solitude.
Motifs: Aron's question, left unresolved again on felt piano, as at the very
beginning; the Light's answer appears only as a ghost in the glass and breaks
off before its last note; an arpeggio that never stops building.
Sample: Farewell Blues (1923), far away, through a closed door."""
from vnsynth import *

s = Song(bpm=60, bars=16, key="F# minor")
s.texture("vinyl", "vinyl", gain=0.6)
s.chords("pad", "F#m9 Dmaj7 Bm9 C#7sus4", inst=warm_pad, octave=3, bars_per_chord=4, gain=0.75, reverb=0.7)
s.notes("arp", "1 5 1' 5 3' 5 1' 5 | 1 5 1' 5 3' 5 1' 5 | 1 5 1' 5 3' 5 1' 5 | 1 5 1' 5 3' 5 1' 5 | "
        "6, 3 6 3 1' 3 6 3 | 6, 3 6 3 1' 3 6 3 | 6, 3 6 3 1' 3 6 3 | 6, 3 6 3 1' 3 6 3 | "
        "4, 1 4 1 6 1 4 1 | 4, 1 4 1 6 1 4 1 | 4, 1 4 1 6 1 4 1 | 4, 1 4 1 6 1 4 1 | "
        "5, 2 5 2 7 2 5 2 | 5, 2 5 2 7 2 5 2 | 5, 2 5 2 7 2 5 2 | 5, 2 5 2 7 2 5 2", inst=mallet, octave=0, gain=0.4,
        reverb=0.55, delay=0.3, pan_=0.3)
s.motif("aron", "aron", inst=felt_piano, octave=1, every=4, gain=0.95, reverb=0.6)
s.notes("ghost", "~ ~ ~ ~ ~ ~ ~ ~ | 2 ~ 3 ~ 5 ~ ~ ~", inst=glass_harmonica, octave=1, start_bar=8, every=8, gain=1.2,
        reverb=0.8, pan_=-0.3)
s.notes("bass", "1, _ _ _ _ _ _ _", inst=sub_bass, every=4, legato=4.0, gain=0.5)
f = snap("farewell_blues_1923", 64.0)
s.sample("farewell", "farewell_blues_1923", start=f, length=6.0, at_bar=[3, 11], fit=4,
         fx=["pitch-4", "78rpm", "far", "wobble", "arch"], gain=0.9, reverb=0.8, pan_=0.4)
s.render(out("the_record"), reverb_seconds=6.0)

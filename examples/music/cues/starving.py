"""Starving - Lord Ashveil chooses to starve himself and free humanity.
Childlike and moving. The Ashveil motif decays: each music-box phrase has
fewer notes than the last, the box slowing, until only the first note
remains, then it begins again, a child winding it up once more.
Motifs: Ashveil (decaying music box; the full descent once, high and tender,
on strings); Aron's question underneath, softly, as company.
Sample: The St. Louis Blues (1925), stretched and closing, fading out."""
from vnsynth import *

s = Song(bpm=58, bars=12, key="A minor")
s.texture("vinyl", "vinyl", gain=0.4)
s.chords("pad", "Am9 Fmaj7 Dm9 E7sus4", inst=warm_pad, octave=3, bars_per_chord=3, gain=0.8, reverb=0.7)
box = ("1' ~ @11 ~ @10 ~ @9 ~ | @8 ~ ~ 5 1' ~ ~ ~ | "
       "1' ~ @11 ~ ~ ~ @9 ~ | @8 ~ ~ ~ ~ ~ ~ ~ | "
       "1' ~ ~ ~ @10 ~ ~ ~ | ~ ~ ~ ~ ~ ~ ~ ~ | "
       "1' ~ ~ ~ ~ ~ ~ ~ | ~ ~ ~ ~ ~ ~ ~ ~ | "
       "~ ~ ~ ~ ~ ~ ~ ~ | ~ ~ ~ ~ ~ ~ ~ ~ | "
       "~ ~ ~ ~ ~ ~ ~ ~ | ~ ~ ~ ~ 5 ~ ~ ~")
s.notes("box", box, inst=music_box, octave=1, gain=1.0, reverb=0.6, delay=0.35, pan_=0.2)
s.notes("descent", "~ ~ ~ ~ ~ ~ ~ ~ | ~ ~ ~ ~ ~ ~ ~ ~ | ~ ~ ~ ~ ~ ~ ~ ~ | ~ ~ ~ ~ ~ ~ ~ ~ | 1' _ _ _ @11 _ _ _ | "
        "@10 _ _ _ @9 _ @8 _ | @8 _ _ _ _ _ _ _", inst=strings, octave=1, gain=0.85, reverb=0.65)
s.notes("aron", MOTIFS["aron"], inst=felt_piano, octave=0, start_bar=8, end_bar=10, gain=0.7, reverb=0.6)
s.notes("bass", "1, _ _ _ _ _ _ _", inst=sub_bass, every=3, legato=2.6, gain=0.5)
b = snap("st_louis_blues_1925", 144.0)
s.sample("fading", "st_louis_blues_1925", start=b, length=3.0, at_bar=[0, 6], fit=6,
         fx=["stretch2", "78rpm", "dreamy", "fadeout"], gain=0.9, reverb=0.7, pan_=-0.3)
s.fx("fading", sweep_lp=[(0, 1800), (6, 400), (6.01, 1800), (12, 400)])
s.render(out("starving"))

"""Ashveil Offer - the end of chapter 3: Lord Ashveil appears to Aron and
offers a transfer to a better world. "I can't tell you better *how*."
Seductive, childlike, hungry: a slow sultry beat, velvet strings, a music box.
Motifs: Ashveil's music-box descent; and, at the end of each loop, the music
box plays the completion of Aron's question (the Light's last four notes)
in the minor: the offer sounds like the answer, in the wrong mode.
Sample: The St. Louis Blues (1925), Bessie Smith's voice in its own D minor,
warbling, close and then far."""
from vnsynth import *

s = Song(bpm=69, bars=16, key="D minor")
s.texture("vinyl", "vinyl", gain=0.4)
s.chords("velvet", "Dmmaj7 Bbmaj7 Gm9 A7sus4", inst=strings, octave=3, bars_per_chord=2, gain=0.8, reverb=0.6,
         chorus_mix=0.4)
s.notes("drone", "1, _ _ _ _ _ _ _", inst=deep_drone, every=4, legato=4.2, gain=0.4, reverb=0.6)
s.notes("box", MOTIFS["ashveil_box"], inst=music_box, octave=1, end_bar=14, every=4, gain=0.9, reverb=0.55,
        delay=0.35, pan_=0.25)
s.notes("offer", "~ ~ ~ ~ ~ ~ ~ ~ | 2 ~ 3 ~ 5 ~ 1' ~", inst=music_box, octave=1, start_bar=14, gain=1.0,
        reverb=0.6, delay=0.35, pan_=0.25)
s.notes("bass", "1, ~ ~ ~ ~ ~ 1, ~ | ~ ~ ~ ~ 5,, ~ ~ ~ | 6,, ~ ~ ~ ~ ~ 6,, ~ | ~ ~ ~ ~ 3, ~ ~ ~ | "
        "4,, ~ ~ ~ ~ ~ 4,, ~ | ~ ~ ~ ~ 1, ~ ~ ~ | 5,, ~ ~ ~ ~ ~ 5,, ~ | ~ ~ ~ ~ 5,, ~ ~ ~", inst=round_bass, gain=0.5)
s.drums("softkick: x.......x..x.... | brush: ....x.......x... | rim: ......x.......x.", gain=0.4, swing=0.15)
b = snap("st_louis_blues_1925", 24.0)
s.sample("bessie", "st_louis_blues_1925", start=b, length=3.6, at_bar=[2, 10], fit=2,
         fx=["78rpm", "warble", "dreamy", "arch"], gain=0.8, reverb=0.55, pan_=-0.3)
s.sample("bessie_far", "st_louis_blues_1925", start=b + 3.6, length=3.6, at_bar=[6], fit=4,
         fx=["stretch2", "reverse", "far", "swell"], gain=0.8, reverb=0.7, pan_=0.3)
s.render(out("ashveil_offer"))

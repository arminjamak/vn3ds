"""Blueprint - the architect's space: Aron designs his own system, a fair
share of its world for every sentient being. Arpeggios like drafting lines.
Motifs: Aron's question, then the Light emerging out of it: for eight bars
only the question, then the answering half ("2 - 3 - 5 - 1'") arrives, first
on vibes, then on flute; the System's pulses repurposed as the grid.
Sample: Parade of the Wooden Soldiers (1923), lo-fi and tiny: toy soldiers on
the drafting table, re-arranged."""
from vnsynth import *

s = Song(bpm=96, bars=24, key="D lydian")
s.texture("air", "room", gain=0.4)
s.chords("pad", "Dmaj7#11 Bm9 Gmaj9 A6add9", inst=shimmer_pad, octave=3, bars_per_chord=2, gain=0.7, reverb=0.6,
         duck=0.3)
s.notes("arp", "1 3 5 1' 3' 5 3 1' 2' 1' 5 3 1' 5 3 2 | 6, 1 3 6 1' 3 1 6 7 6 3 1 6 3 1 7, | "
        "4, 6, 1 4 6 1 6, 4 5 4 1 6, 4 1 6, 5, | 5, 7, 2 5 7 2 7, 5 6 5 2 7, 5 2 7, 6,", inst=arp_pluck, octave=1,
        gain=0.3, reverb=0.4, delay=0.25, pan_=0.25, duck=0.3)
s.notes("grid", MOTIFS["system"], inst=mallet, octave=1, every=1, gain=0.35, reverb=0.3, pan_=-0.35)
s.motif("aron", "aron", inst=glass_keys, octave=1, end_bar=8, every=4, gain=0.9, reverb=0.5)
s.motif("light", "light", inst=mallet, octave=1, start_bar=8, end_bar=16, every=4, gain=0.8, reverb=0.5, delay=0.2)
s.motif("light_fl", "light", inst=flute, octave=1, start_bar=16, every=4, gain=0.95, reverb=0.55, delay=0.2)
s.notes("bass", "1, ~ ~ 1, ~ ~ 1, ~ | 6,, ~ ~ 6,, ~ ~ 6,, ~ | 4,, ~ ~ 4,, ~ ~ 4,, ~ | 5,, ~ ~ 5,, ~ ~ 5,, ~",
        inst=round_bass, gain=0.5, reverb=0.05, duck=0.3)
s.drums("softkick: x.......x....... | rim: ....x.......x... | shaker: ..x...x...x...x.", gain=0.4)
w = snap("wooden_soldiers_1923", 100.0)
s.sample("toys", "wooden_soldiers_1923", start=w, length=4 * 0.289, at_bar=[3, 7, 11, 15, 19, 23], fit=1,
         fx=["pitch+3", "lofi", "lp2500", "hp300"], gain=0.6, reverb=0.4, delay=0.25, pan_=0.4)
s.render(out("blueprint"))

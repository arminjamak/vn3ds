"""Angel Ops - Commander Seraphiel's ops room: the angel corps feeding
opportunity into worlds, remote-controlling the less conscious. Choir, a
stately march, procedure. Also aliased as `entities` for the cuts.
The tempo is Parade of the Wooden Soldiers slowed a fourth, so its march
fragments drop into the bar exactly, like toy soldiers wound down.
Motifs: the System as a brass fanfare (procedure); Aron's question, faint, on
glass (Subject A-30 on the board).
Sample: Parade of the Wooden Soldiers (1923), pitched down, 78rpm."""
from vnsynth import *

s = Song(bpm=77.4, bars=16, key="B minor")
s.texture("room", "room", gain=0.4)
s.chords("choir", "Bm G Em F#", inst=choir, octave=3, gain=0.85, reverb=0.7)
s.chords("strings", "Bm G Em7 F#7sus4", inst=strings, octave=2, gain=0.7, reverb=0.6, chorus_mix=0.3)
s.notes("fanfare", "1 1 1 ~ 7, ~ ~ ~ | ~ ~ ~ ~ ~ ~ ~ ~ | 6, 6, 6, ~ 5, ~ ~ ~ | ~ ~ ~ ~ 5, ~ 7, ~",
        inst=soft_brass, octave=1, gain=0.8, reverb=0.5)
s.motif("subject", "aron", inst=glass_keys, octave=1, start_bar=8, every=8, gain=0.9, reverb=0.6, delay=0.3, pan_=0.3)
s.notes("bass", "1, ~ ~ ~ 1, ~ ~ ~ | 6,, ~ ~ ~ 6,, ~ ~ ~ | 4,, ~ ~ ~ 4,, ~ ~ ~ | 5,, ~ ~ ~ 5,, ~ 5,, ~",
        inst=sub_bass, gain=0.7)
s.drums("tom: x.......x....... | snare: x..x.xx.x...x.x. | softkick: x...x...x...x...", gain=0.45, reverb=0.3)
w = snap("wooden_soldiers_1923", 100.0)
s.sample("soldiers", "wooden_soldiers_1923", start=w, length=4 * 0.578, at_bar=[3, 7, 11, 15], fit=1,
         fx=["pitch-5", "78rpm", "lp2400", "arch"], gain=0.8, reverb=0.45, pan_=-0.2)
s.render(out("angel_ops"))

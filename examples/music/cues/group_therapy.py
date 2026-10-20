"""Group Therapy - a circle of chairs, breathing exercises, other people's
stories, the boredom. Gentle. The pad breathes: in for four, out for four.
Motifs: Aron's question on felt piano, and for the first time someone answers
it, half-way (flute: 2 - 3 - 1), the way a stranger's story half-helps.
Sample: My Buddy (1922), one phrase, far down the corridor."""
from vnsynth import *

s = Song(bpm=76, bars=16, key="F major")
s.texture("room", "room", gain=0.5)
s.chords("breath", "Fmaj7 Dm9 Bbmaj7 C6", inst=warm_pad, octave=3, bars_per_chord=2, gain=0.9, reverb=0.6)
s.fx("breath", tremolo=(76 / 60 / 8, 0.45))
s.notes("guitar", "1 5 1' 5 3' 5 1' 5 | 6, 3 6 3 1' 3 6 3 | 4, 1 4 1 6 1 4 1 | 5, 2 5 2 7 2 5 2",
        inst=dream_guitar, octave=1, every=8, gain=0.9, reverb=0.5, chorus_mix=0.5, pan_=0.3, vel=0.7)
s.motif("aron", "aron", inst=felt_piano, octave=1, every=4, gain=0.85, reverb=0.45)
s.notes("answer", "~ ~ ~ ~ ~ ~ ~ ~ | ~ ~ ~ ~ ~ ~ ~ ~ | 2 ~ 3 ~ 1 ~ ~ ~ | ~ ~ ~ ~ ~ ~ ~ ~", inst=flute, octave=1,
        start_bar=4, every=8, gain=0.9, reverb=0.55, pan_=-0.25)
s.notes("bass", "1, ~ ~ ~ ~ ~ ~ ~ | 1, ~ ~ ~ 5,, ~ ~ ~ | 6,, ~ ~ ~ ~ ~ ~ ~ | 6,, ~ ~ ~ 3, ~ ~ ~ | "
        "4,, ~ ~ ~ ~ ~ ~ ~ | 4,, ~ ~ ~ 1, ~ ~ ~ | 5,, ~ ~ ~ ~ ~ ~ ~ | 5,, ~ ~ ~ 2, ~ ~ ~", inst=round_bass, gain=0.55)
s.drums("softkick: x.........x..... | brush: ....x.......x... | shaker: ..x...x...x...x.", gain=0.35)
m = snap("my_buddy_1922", 88.0)
s.sample("buddy", "my_buddy_1922", start=m, length=3.5, at_bar=[10], fit=3,
         fx=["pitch+5", "78rpm", "far", "wobble", "arch"], gain=0.9, reverb=0.7, pan_=0.4)
s.render(out("group_therapy"))

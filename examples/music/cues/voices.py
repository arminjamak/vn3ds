"""Voices - the transmissions: "...throttle approved...", "...subject A-30...",
"...LOOM sync at dawn...". Glitchy, otherworldly, a radio between stations.
Motifs: the System's three pulses as cold sine pings answered by themselves
in other octaves (process logs talking to each other); the clock, broken.
Samples: Parade of the Wooden Soldiers and Ogopogo, glitched and telephoned,
heard through the static as if the records were the carrier."""
from vnsynth import *

s = Song(bpm=90, bars=12, key="C# minor")
s.texture("static", "hiss", gain=0.6)
s.notes("drone", "1, _ _ _ _ _ _ _", inst=deep_drone, legato=4.0, every=4, gain=0.3, reverb=0.4)
s.notes("pings", MOTIFS["system"], inst=pulse_blip, octave=2, every=2, gain=0.8, reverb=0.6, delay=0.4, pan_=0.3)
s.notes("pings_lo", MOTIFS["system"], inst=pulse_blip, octave=1, start_bar=1, every=3, gain=0.7, reverb=0.6,
        delay=0.3, pan_=-0.35)
s.notes("clock", "1 ~ ~ @11 ~ ~ 1 ~", inst=music_box, octave=1, transpose=1, start_bar=5, every=6, gain=0.4,
        reverb=0.7, delay=0.4)
s.notes("breath", "1 ~ ~ ~ 3 ~ ~ ~ | ~ ~ 5 ~ ~ ~ ~ ~", inst=vocal_chop, octave=1, every=4, gain=0.35, reverb=0.8)
s.fx("breath", lp=1400, tremolo=(6.0, 0.6))
w = snap("wooden_soldiers_1923", 8.0)
s.sample("carrier", "wooden_soldiers_1923", start=w, length=1.8, at_bar=[0, 4, 8], fit=2,
         fx=["glitch", "telephone", "lp2400", "crackle"], gain=0.55, reverb=0.5, pan_=-0.3)
o = snap("ogopogo_1925", 100.0)
s.sample("carrier2", "ogopogo_1925", start=o, length=1.2, at_bar=[2, 6, 10], fit=1,
         fx=["reverse", "glitch", "telephone", "lp2000"], gain=0.5, reverb=0.6, pan_=0.35)
s.drums("tick: x..x..x.....x... | softkick: x.........x.....", gain=0.4)
s.fx("drums_tick", crush=True)
s.render(out("voices"))

"""Questions - Aron thinking through Bostrom: odds are we're simulated, and a
careful simulator keeps the conscious headcount low. Is he alone?
Curious, patient, counting. Motifs: Aron's question on glass keys, asked
again higher; a plucked arpeggio that counts like a proof.
Sample: April Showers stretched into a slow chord, the morning remembered."""
from vnsynth import *

s = Song(bpm=72, bars=16, key="E dorian")
s.texture("tape", "tape", gain=0.4)
s.chords("pad", "Em9 Cmaj7 G6 D", inst=warm_pad, octave=3, bars_per_chord=2, gain=0.8, reverb=0.6)
s.notes("count", "1 5 2' 5 3' 5 2' 5 | 6, 3 7 3 1' 3 7 3 | 3 1' 5' 1' 7 1' 5' 1' | 5, 2 6 2 7 2 6 2",
        inst=arp_pluck, octave=1, gain=0.3, reverb=0.45, delay=0.3, pan_=0.25, vel=0.8)
s.motif("aron", "aron", inst=glass_keys, octave=1, every=4, gain=0.8, reverb=0.55, delay=0.25)
s.notes("aron_hi", MOTIFS["aron_rising"], inst=flute, octave=1, start_bar=8, end_bar=16, gain=0.7, reverb=0.55,
        pan_=-0.25)
s.notes("bass", "1, ~ ~ ~ ~ ~ ~ ~ | 6,, ~ ~ ~ ~ ~ ~ ~ | 3, ~ ~ ~ ~ ~ ~ ~ | 7,, ~ ~ ~ ~ ~ ~ ~",
        inst=sub_bass, gain=0.7, legato=1.0)
s.drums("softkick: x.........x..... | rim: ........x....... | shaker: ..x...x...x...x.", gain=0.45)
a = snap("april_showers_1921", 52.0)
s.sample("memory", "april_showers_1921", start=a, length=1.6, at_bar=[0, 8], fit=4,
         fx=["pitch+2", "stretch4", "dreamy", "lp1400", "arch"], gain=0.9, reverb=0.7)
s.render(out("questions"))

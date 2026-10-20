"""Theme - the tutorial (a calibration, though nobody says so). Bright,
clean, a little Dieter Rams: few elements, each one exact.
Motifs: Aron's question stated plainly on vibraphone; the 7:07 clock as the
Braun alarm's tick; the System's three pulses hidden in the rim.
Less, but better."""
from vnsynth import *

s = Song(bpm=96, bars=16, key="C major")
s.texture("air", "room", gain=0.3)
s.chords("keys", "Cmaj7 Am7 Fmaj9 G6", inst=felt_piano, octave=3, bars_per_chord=2, rhythm="x.....x.",
         gain=0.75, reverb=0.3, chorus_mix=0.0)
arp = ("1 5 1' 3' 5' 3' 1' 5 | 1 5 1' 3' 5' 3' 1' 5 | 6, 3 6 1' 3' 1' 6 3 | 6, 3 6 1' 3' 1' 6 3 | "
       "4, 1 4 6 1' 6 4 1 | 4, 1 4 6 1' 6 4 1 | 5, 2 5 7 2' 7 5 2 | 5, 2 5 7 2' 7 5 2")
s.notes("arp", arp, inst=mallet, octave=0, gain=0.38, reverb=0.35, delay=0.18, pan_=0.25, vel=0.8)
s.motif("aron", "aron", inst=flute, octave=1, start_bar=2, every=4, gain=1.2, reverb=0.45, delay=0.2)
s.notes("answer", "~ ~ ~ ~ ~ ~ ~ ~ | 1' ~ 7 ~ 5 ~ ~ ~", inst=glass_keys, octave=1, start_bar=12, end_bar=14,
        gain=0.5, reverb=0.5, pan_=-0.3)
s.notes("bass", "1, ~ ~ ~ ~ ~ 5,, ~ | 1, ~ ~ ~ 1, ~ ~ ~ | 6,, ~ ~ ~ ~ ~ 3, ~ | 6,, ~ ~ ~ 6,, ~ ~ ~ | "
        "4,, ~ ~ ~ ~ ~ 1, ~ | 4,, ~ ~ ~ 4,, ~ ~ ~ | 5,, ~ ~ ~ ~ ~ 2, ~ | 5,, ~ ~ ~ 5,, ~ ~ ~",
        inst=round_bass, gain=0.5, reverb=0.05)
s.drums("softkick: x.......x....... | rim: ....x.......x..x | tick: x.x.x.x.x.x.x.x.", gain=0.5)
s.render(out("theme"))

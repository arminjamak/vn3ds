"""Purgatorium Shift - Pim and Dross on kitchen-talk shift 7, running the small
talk, the blinking, the walk to the fridge. Quirky, jazzy, busy.
The tempo is the Ogopogo record's own (two of its beats per half bar), so the
1925 band loops at its natural speed like the shift radio.
Motifs: the System's three pulses as a woodblock time clock; Mira's turn on a
muted horn ("was that line yours or hers?"), slightly too jaunty.
Samples: Ogopogo (1925) as a one-bar loop; Krooked Blues (1923) stabs."""
from vnsynth import *

s = Song(bpm=109, bars=24, key="Ab major", swing=0.18)
s.texture("vinyl", "vinyl", gain=0.3)
o = snap("ogopogo_1925", 148.0)
s.sample("ogo", "ogopogo_1925", start=o, length=8 * 0.2725, every=1, end_bar=16, fit=1,
         fx=["telephone", "lp1800", "crackle"], gain=0.32, reverb=0.2, pan_=0.15)
s.sample("ogo_rev", "ogopogo_1925", start=o, length=8 * 0.2725, every=1, at_bar=16, end_bar=24, fit=1,
         fx=["reverse", "telephone", "lp1800"], gain=0.38, reverb=0.3, pan_=-0.15)
k = snap("krooked_blues_1923", 56.0)
s.sample("krooked", "krooked_blues_1923", start=k, length=2 * 0.595, at_bar=[3, 7, 11, 19, 23], fit=0.5,
         fx=["pitch+3", "78rpm", "far"], gain=0.8, reverb=0.4, pan_=-0.4)
s.chords("comp", "Abmaj7 Fm7 Bbm7 Eb7", inst=glass_keys, octave=3, rhythm="..x...x.", gain=0.6, reverb=0.25)
s.notes("walk", "1, 3, 5, 6, | 6,, 1, 3, 5, | 2, 4, 6, 1 | 5,, 7,, 2, 4,", inst=round_bass, gain=0.35, reverb=0.05)
s.notes("tc", MOTIFS["system"], inst=pulse_blip, octave=2, every=2, gain=0.55, reverb=0.25, pan_=0.4)
s.motif("mira_horn", "mira", inst=soft_brass, octave=1, start_bar=8, end_bar=16, every=4, gain=1.3, reverb=0.35)
s.notes("chatter", "5' 3' ~ 5' 6' 5' 3' ~ | ~ 2' 3' 2' 1' ~ ~ ~", inst=mallet, octave=0, start_bar=16, every=2,
        gain=0.55, reverb=0.3, pan_=0.35)
s.drums("softkick: x.......x....... | brush: ....x.......x... | wood: ..x....x..x...x. | hat: x.x.x.x.x.x.x.x.",
        gain=0.5)
s.render(out("purgatorium_shift"))

"""The Leak - his mind leaks into the pattern-copy world: the cab driver says
his name, a restaurant table says "protected", a radio host reads his
notebook, strangers say "A-30". Glitches and stuttering samples.
Motifs: the 7:07 clock stuck and skipping; the System's pulses crushed to
bits; Aron's question cut off after three notes.
Samples: all three records of his old world at once, buffer-glitched:
April Showers, Krooked Blues and Ogopogo."""
from vnsynth import *

s = Song(bpm=90, bars=16, key="F minor")
s.texture("hiss", "hiss", gain=0.5)
s.chords("pad", "Fm9 Dbmaj7 Bbm9 C7sus4", inst=shimmer_pad, octave=3, bars_per_chord=2, gain=0.8, reverb=0.6)
s.fx("pad", tremolo=(6.0, 0.75))
s.notes("clock", "1 ~ ~ 7 1 ~ ~ 7 | 1 7 1 7 ~ ~ ~ ~", inst=music_box, octave=1, every=4, gain=0.6, reverb=0.4,
        delay=0.3)
s.notes("system", MOTIFS["system"], inst=pulse_blip, octave=1, every=1, gain=0.6, reverb=0.3, pan_=-0.3)
s.fx("system", crush=True)
s.notes("aron", "1 ~ 5 ~ 4 ~ ~ ~ | ~ ~ ~ ~ ~ ~ ~ ~", inst=glass_keys, octave=1, start_bar=2, every=4, gain=0.9,
        reverb=0.5, delay=0.3, pan_=0.2)
s.notes("bass", "1, ~ ~ 1, ~ ~ 1, 1, | 6,, ~ ~ 6,, ~ ~ 6,, 6,, | 4,, ~ ~ 4,, ~ ~ 4,, 4,, | 5,, ~ ~ 5,, ~ ~ 5,, 5,,",
        inst=round_bass, every=4, gain=0.5, reverb=0.05)
s.drums("softkick: x.....x...x..... | tick: x.xx..x.x..xx.x. | snare: ....x.......x...", gain=0.45)
s.fx("drums_tick", crush=True)
a = snap("april_showers_1921", 116.0)
s.sample("april", "april_showers_1921", start=a, length=2.6, at_bar=[0, 8], fit=2,
         fx=["glitch", "telephone", "crackle"], gain=0.65, reverb=0.35, pan_=-0.4)
k = snap("krooked_blues_1923", 148.0)
s.sample("krooked", "krooked_blues_1923", start=k, length=2.4, at_bar=[4, 12], fit=2,
         fx=["pitch-2", "glitch", "lofi", "lp2600"], gain=0.65, reverb=0.35, pan_=0.4)
o = snap("ogopogo_1925", 100.0)
s.sample("ogo", "ogopogo_1925", start=o, length=1.1, at_bar=[3, 7, 11, 15], fit=1,
         fx=["stutter", "reverse", "telephone"], gain=0.55, reverb=0.4, delay=0.2)
s.render(out("the_leak"))

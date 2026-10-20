"""Unraveling - no sleep, the decoding gets obsessive, the mirror, the rain.
Rising tension: an ostinato whose filter climbs for twenty bars, then the
floor drops and it starts again. Also aliased as `unease`.
Motifs: Aron's question broken into pieces on strings; the 7:07 clock with
its seventh bent wrong; the System's pulses creeping in under everything.
Sample: April Showers reversed and a semitone flat, the morning gone sour."""
from vnsynth import *

s = Song(bpm=96, bars=24, key="C minor")
s.texture("hiss", "tape", gain=0.5)
s.notes("ostinato", "1 5 1' 5 2' 5 1' 5 | 1 5 1' 5 3' 5 2' 5 | 6, 3 6 3 1' 3 6 3 | 7, 2 5 2 7 2 5 2",
        inst=arp_pluck, octave=1, gain=0.35, reverb=0.4, delay=0.25, pan_=0.2)
s.fx("ostinato", sweep_lp=[(0, 500), (20, 3200), (24, 500)])
s.chords("pad", "Cm Abmaj7 Fm9 G7sus4", inst=shimmer_pad, octave=3, gain=0.7, reverb=0.6)
s.notes("aron", "1 ~ 5 ~ ~ ~ ~ ~ | ~ ~ ~ ~ 4 3 ~ ~ | ~ ~ ~ ~ ~ ~ ~ ~ | 2 ~ ~ ~ ~ ~ 2 ~", inst=strings, octave=1,
        start_bar=4, gain=1.2, reverb=0.55)
s.notes("clock", "1 ~ ~ @11 ~ ~ 1 ~", inst=music_box, octave=1, start_bar=2, every=4, gain=0.45, reverb=0.6, delay=0.3)
s.notes("system", MOTIFS["system"], inst=pulse_blip, octave=1, start_bar=12, every=1, gain=0.5, reverb=0.4,
        pan_=-0.3)
s.notes("bass", "1, ~ 1, ~ 1, ~ 1, ~ | 1, ~ 1, ~ 1, ~ 1, ~ | 6,, ~ 6,, ~ 6,, ~ 6,, ~ | 5,, ~ 5,, ~ 5,, ~ 5,, ~",
        inst=round_bass, gain=0.6, reverb=0.05)
s.drums("softkick: x...x...x...x... | hat: ..x...x...x...x.", gain=0.45)
s.drums("tom: ..........x.x.x. | snare: ....x.......x...", start_bar=16, gain=0.4)
a = snap("april_showers_1921", 52.0)
s.sample("sour", "april_showers_1921", start=a, length=2.6, at_bar=[6, 14], fit=2,
         fx=["reverse", "pitch-1", "78rpm", "warble", "swell"], gain=0.8, reverb=0.6, pan_=-0.35)
s.sample("sour_glitch", "april_showers_1921", start=a + 2.6, length=2.6, at_bar=[18, 21], fit=1,
         fx=["pitch-1", "glitch", "telephone"], gain=0.6, reverb=0.4, pan_=0.35)
s.render(out("unraveling"))

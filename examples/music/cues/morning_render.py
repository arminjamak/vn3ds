"""Morning Render - Aron wakes at 7:07. Warm, a little too regular.
Motifs: clock (7:07) in the music box, Aron's question on glass keys.
Sample: April Showers (1921), a phrase drifting up from a radio that isn't on."""
from vnsynth import *

s = Song(bpm=78, bars=16, key="D major")
s.texture("vinyl", "vinyl", gain=0.25)
s.chords("pad", "Dmaj7 Bm7 Gmaj9 A6", inst=shimmer_pad, bars_per_chord=2, gain=0.8, reverb=0.6)
s.motif("clock", "clock", inst=music_box, octave=1, every=2, gain=0.6, reverb=0.5, delay=0.3)
s.motif("aron", "aron", inst=glass_keys, octave=1, start_bar=4, every=4, gain=0.85, reverb=0.5, delay=0.25)
s.notes("guitar", "1 5 1' 3' 5' 3' 1' 5 | 6, 3 6 1' 3' 1' 6 3", inst=dream_guitar, start_bar=8,
        chorus_mix=0.5, reverb=0.55, gain=0.4)
s.notes("bass", "1, ~ ~ ~ 1, ~ ~ ~ | 6,, ~ ~ ~ 6,, ~ ~ ~ | 4,, ~ ~ ~ 4,, ~ ~ ~ | 5,, ~ ~ ~ 5,, ~ ~ ~",
        inst=sub_bass, every=4, reverb=0.1, duck=0.5, gain=0.6)
s.drums("kick: x............... | hat: ..x...x...x...x. | tick: x.......x.......", end_bar=8, gain=0.45)
s.drums("kick: x.......x....... | snare: ....x.......x... | hat: ..x...x...x...x.", start_bar=8, gain=0.5)
# the morning's memory: April Showers, pitched into D, smeared like something half-heard
a = snap("april_showers_1921", 116.0)
s.sample("radio", "april_showers_1921", start=a, length=8 * 0.35, at_bar=[5, 13], fit=2,
         fx=["pitch+2", "78rpm", "dreamy", "wobble", "arch"], gain=0.9, reverb=0.6, pan_=-0.3)
s.sample("radio_rev", "april_showers_1921", start=a + 2.8, length=2.8, at_bar=[11], fit=1,
         fx=["pitch+2", "reverse", "78rpm", "dreamy", "swell"], gain=0.7, reverb=0.7, pan_=0.35)
s.render(out("morning_render"))

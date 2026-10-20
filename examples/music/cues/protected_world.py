"""Protected World - chapter 3's too-smooth copy of World 7,412: pattern
people, conversations that loop, Mira lovely but sometimes *too* right.
Perfect muzak, looping, slightly off. No swing, no variation, every two bars
the same; then, once per loop, a wrong note nobody else hears.
The tempo is April Showers' own (eight of its beats per bar), so the 1921
record loops seamlessly at its natural speed, a perfect copy of itself.
Motifs: the 7:07 clock on vibes, exact, every bar; once, 35 cents sharp.
Sample: April Showers (1921) as a clean muzak loop; one repeat a semitone sharp."""
from vnsynth import *

a = snap("april_showers_1921", 152.0)
beat = beat_period("april_showers_1921", a, lo=140, hi=230)
s = Song(bpm=60 / (2 * beat), bars=16, key="C major")
s.sample("muzak", "april_showers_1921", start=a, length=8 * beat, every=2, fit=1, end_bar=16,
         fx=["lp3000", "hp200"], gain=0.6, reverb=0.2)
s.sample("muzak_b", "april_showers_1921", start=a + 8 * beat, length=8 * beat, at_bar=[1, 3, 5, 7, 9, 13, 15],
         fit=1, fx=["lp3000", "hp200"], gain=0.6, reverb=0.2)
s.sample("wrong", "april_showers_1921", start=a + 8 * beat, length=8 * beat, at_bar=[11], fit=1,
         fx=["pitch+1", "lp3000", "hp200"], gain=0.6, reverb=0.2)
s.chords("vibes", "Cmaj7 Am7 Dm7 G7", inst=mallet, octave=3, rhythm="x..x..x.", gain=0.5, reverb=0.2)
s.motif("clock", "clock", inst=mallet, octave=1, end_bar=13, gain=0.4, reverb=0.25)
s.notes("clock_off", MOTIFS["clock"], inst=mallet, octave=1, transpose=0.35, start_bar=13, end_bar=14, gain=0.45,
        reverb=0.25)
s.motif("clock_end", "clock", inst=mallet, octave=1, start_bar=14, gain=0.4, reverb=0.25)
s.notes("bass", "1, ~ ~ 5,, 1, ~ 5,, ~ | 6,, ~ ~ 3, 6,, ~ 3, ~ | 2, ~ ~ 6,, 2, ~ 6,, ~ | 5,, ~ ~ 2, 5,, ~ 2, ~",
        inst=round_bass, gain=0.5, reverb=0.05)
s.drums("softkick: x..x....x..x.... | rim: ...x..x....x..x. | shaker: xxxxxxxxxxxxxxxx", gain=0.4, reverb=0.1)
s.render(out("protected_world"), reverb_seconds=2.0)

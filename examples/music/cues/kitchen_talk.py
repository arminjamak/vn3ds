"""Kitchen Talk - coffee, the bird on the wire, Mira's small talk.
Domestic and light. Motifs: Mira's warm turn on felt piano (answered by
guitar), the 7:07 clock as a tiny music-box aside when the bird lands.
Sample: April Showers on a kitchen radio, far away."""
from vnsynth import *

s = Song(bpm=88, bars=16, key="G major")
s.texture("room", "room", gain=0.35)
s.chords("keys", "Gmaj7 Em7 Cmaj7 D6", inst=glass_keys, octave=3, bars_per_chord=2, rhythm="x..x..x.",
         gain=0.8, reverb=0.35, chorus_mix=0.3)
s.notes("guitar", "1 3 5 1' 3 5 1' 5 | 6, 3 5 1' 3 5 1' 5 | 4, 1 3 5 1 3 5 3 | 5, 2 4 6 2 4 6 4",
        inst=dream_guitar, octave=1, every=8, chorus_mix=0.5, reverb=0.45, gain=0.45, pan_=0.3, vel=0.8)
s.motif("mira", "mira", inst=felt_piano, octave=1, start_bar=2, every=4, gain=0.8, reverb=0.4)
s.notes("mira_answer", "~ ~ ~ ~ ~ ~ ~ ~ | ~ ~ ~ ~ 5 6 5 3 | 2 ~ ~ ~ ~ ~ ~ ~", inst=dream_guitar, octave=1,
        start_bar=12, end_bar=15, gain=1.0, reverb=0.5, pan_=-0.3, chorus_mix=0.4)
s.motif("clock", "clock", inst=music_box, octave=1, start_bar=7, every=8, gain=0.45, reverb=0.5, delay=0.3)
s.notes("bass", "1, ~ ~ 1, ~ ~ 5,, ~ | 6,, ~ ~ 6,, ~ ~ 3, ~ | 4,, ~ ~ 4,, ~ ~ 1, ~ | 5,, ~ ~ 5,, ~ ~ 2, ~",
        inst=round_bass, every=4, gain=0.6, reverb=0.05)
s.drums("softkick: x.....x...x..... | brush: ....x.......x... | shaker: x.xxx.xxx.xxx.xx", gain=0.5, swing=0.12)
a = snap("april_showers_1921", 152.0)
s.sample("radio", "april_showers_1921", start=a, length=4.2, at_bar=[4, 10], fit=2,
         fx=["pitch-5", "telephone", "far", "crackle"], gain=0.7, reverb=0.35, pan_=-0.5)
s.render(out("kitchen_talk"))

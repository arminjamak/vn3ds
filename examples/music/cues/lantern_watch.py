"""Lantern Watch - Ember's attic: the secret few who watch Aron and help in
tiny deniable ways. Warm and kind. Also aliased as `watch`.
Motifs: the Lantern's three soft flickers and their rising answer on glass and
vibes; Aron's question answered by it once, gently, at the end of the loop.
Sample: My Buddy (1922) in E, "a song on the radio" the Watch puts on for him."""
from vnsynth import *

s = Song(bpm=72, bars=16, key="E major")
s.texture("vinyl", "vinyl", gain=0.4)
s.chords("keys", "Emaj9 C#m7 Amaj7 B6", inst=felt_piano, octave=3, bars_per_chord=2, rhythm="x...x...",
         gain=0.7, reverb=0.45)
s.chords("pad", "Emaj7 C#m9 Amaj9 Bsus4", inst=warm_pad, octave=3, bars_per_chord=2, gain=0.55, reverb=0.6)
s.motif("lantern", "lantern", inst=glass_harmonica, octave=1, every=2, gain=0.9, reverb=0.6, delay=0.3)
s.motif("lantern_vibes", "lantern", inst=mallet, octave=1, start_bar=8, every=4, gain=0.6, reverb=0.5, pan_=0.35)
s.notes("guitar", "1 5 1' 5 3' 5 1' 5 | 6, 3 6 3 1' 3 6 3", inst=dream_guitar, octave=0, start_bar=4, every=2,
        gain=0.45, chorus_mix=0.5, reverb=0.5, pan_=-0.3, vel=0.7)
s.notes("aron", "1 ~ 5 ~ 4 3 ~ ~ | 2 ~ 3 ~ ~ ~ ~ ~", inst=flute, octave=1, start_bar=14, end_bar=16, gain=0.8,
        reverb=0.55)
s.notes("bass", "1, ~ ~ ~ ~ ~ ~ ~ | 1, ~ ~ ~ 5,, ~ ~ ~ | 6,, ~ ~ ~ ~ ~ ~ ~ | 6,, ~ ~ ~ 3, ~ ~ ~ | "
        "4,, ~ ~ ~ ~ ~ ~ ~ | 4,, ~ ~ ~ 1, ~ ~ ~ | 5,, ~ ~ ~ ~ ~ ~ ~ | 5,, ~ ~ ~ 2, ~ ~ ~", inst=sub_bass, gain=0.55)
s.drums("softkick: x.........x..... | brush: ....x.......x... | shaker: ..x...x...x...x.", gain=0.35)
m = snap("my_buddy_1922", 132.0)
s.sample("radio", "my_buddy_1922", start=m, length=4.0, at_bar=[6, 12], fit=2,
         fx=["78rpm", "telephone", "far", "wobble", "arch"], gain=0.8, reverb=0.5, pan_=0.45)
s.render(out("lantern_watch"))

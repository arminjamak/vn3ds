"""Office - the last scene: a bright architectural office in a perfect world,
Aron presenting his system to cosmic beings. Clean and minimal, Rams-like:
"less, but better". The tutorial theme's language, grown up.
Motifs: the Light (Aron's question with its answer) on vibes, plainly, with
room around it; the 7:07 clock as a single soft tick, now in time."""
from vnsynth import *

s = Song(bpm=100, bars=16, key="C major")
s.texture("air", "room", gain=0.3)
s.chords("keys", "Cmaj9 Fmaj7#11 Am9 G6add9", inst=felt_piano, octave=3, bars_per_chord=2, rhythm="x.......",
         gain=0.75, reverb=0.35)
s.notes("pulse", "1 ~ 5 ~ 1' ~ 5 ~ | 1 ~ 5 ~ 1' ~ 5 ~ | 4, ~ 1 ~ 4 ~ 1 ~ | 4, ~ 1 ~ 4 ~ 1 ~ | "
        "6, ~ 3 ~ 6 ~ 3 ~ | 6, ~ 3 ~ 6 ~ 3 ~ | 5, ~ 2 ~ 5 ~ 2 ~ | 5, ~ 2 ~ 5 ~ 2 ~", inst=mallet, octave=0,
        gain=0.45, reverb=0.3, pan_=0.3)
s.motif("light", "light", inst=mallet, octave=1, start_bar=2, every=4, gain=0.8, reverb=0.4, delay=0.2)
s.notes("bass", "1, ~ ~ ~ 1, ~ ~ ~ | 1, ~ ~ ~ 5,, ~ ~ ~ | 4,, ~ ~ ~ 4,, ~ ~ ~ | 4,, ~ ~ ~ 1, ~ ~ ~ | "
        "6,, ~ ~ ~ 6,, ~ ~ ~ | 6,, ~ ~ ~ 3, ~ ~ ~ | 5,, ~ ~ ~ 5,, ~ ~ ~ | 5,, ~ ~ ~ 2, ~ ~ ~", inst=round_bass, gain=0.45)
s.drums("softkick: x.......x....... | rim: ....x.......x... | tick: x...x...x...x...", gain=0.4)
s.render(out("office"), reverb_seconds=3.0)

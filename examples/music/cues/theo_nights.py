"""Theo Nights - Theo's place, late: bad jokes, the stimulants, the weed, the
"bro, the universe doesn't run on your schedule". Lo-fi, warm, a little
hazy, with the cost in the minor turn at the end of each phrase.
King Oliver's band slowed four semitones sets the tempo: one bar of the
cue is exactly four beats of the 1923 record.
Motifs: Theo's shrug-and-grin on Rhodes; Aron's question, half-heard, on vibes.
Sample: Krooked Blues (1923) as the lo-fi loop."""
from vnsynth import *

k = snap("krooked_blues_1923", 12.0)
beat = beat_period("krooked_blues_1923", k, lo=85, hi=120)
s = Song(bpm=60 / beat * 2 ** (-4 / 12), bars=16, key="Db major", swing=0.2)
s.texture("vinyl", "vinyl", gain=0.5)
s.sample("krooked", "krooked_blues_1923", start=k, length=4 * beat, every=1, fit=1,
         fx=["pitch-4", "lofi", "lp1700", "hp150"], gain=0.36, reverb=0.25, duck=0.3)
s.chords("rhodes", "Dbmaj9 Bbm9 Ebm9 Ab7sus4", inst=glass_keys, octave=3, rhythm="x.....x.", gain=0.8, reverb=0.35,
         chorus_mix=0.4)
s.motif("theo", "theo", inst=glass_keys, octave=1, every=4, gain=0.9, reverb=0.4, delay=0.2, pan_=0.2)
s.fx("theo", lp=2000)
s.notes("aron", MOTIFS["aron"], inst=mallet, octave=1, start_bar=10, end_bar=12, gain=0.6, reverb=0.5, pan_=-0.3)
s.notes("bass", "1, ~ ~ 1, ~ ~ 5,, ~ | 6,, ~ ~ 6,, ~ ~ 3, ~ | 2, ~ ~ 2, ~ ~ 6,, ~ | 5,, ~ ~ 5,, ~ 7,, ~ ~",
        inst=round_bass, gain=0.55, reverb=0.05)
s.drums("softkick: x.....x...x..... | snare: ....x.......x... | hat: x.x.x.x.x.x.x.x.", gain=0.5)
s.fx("drums_snare", lp=3500, crush=True)
s.render(out("theo_nights"))

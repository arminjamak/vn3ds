"""The Big Questions - the quiz: contemplative and curious, never stressful.
A clock ticks under everything (tick on the beat, a softer tock between), like
the Braun alarm of `theme`, but patient.
Motifs: Aron's question on flute, then asked twice and higher (`aron_rising`)
on glass keys; the 7:07 clock on music box closing every phrase; a plucked
arpeggio that counts like a proof (as in `questions`, same key).
Sample: April Showers (1921), stretched into a slow, golden chord: the
morning remembered while thinking."""
from vnsynth import *
from _mg import SUB, exact_bpm

s = Song(bpm=exact_bpm(84, 16), bars=16, key="E dorian")
s.texture("tape", "tape", gain=0.3)
s.texture("room", "room", gain=0.25)
s.chords("pad", "Em9 Gmaj7 A6 Bm7", inst=warm_pad, octave=3, bars_per_chord=2, gain=0.6, reverb=0.6)
s.notes("count", "1 5 7 2' 3' 2' 7 5 | 1 5 7 2' 3' 2' 7 5 | 3, 3 5 7 2' 7 5 3 | 3, 3 5 7 2' 7 5 3 | "
        "4, 4 6 1' 2' 1' 6 4 | 4, 4 6 1' 2' 1' 6 4 | 5, 5 7 2' 4' 2' 7 5 | 5, 5 7 2' 4' 2' 7 5",
        inst=mallet, octave=0, gain=0.32, reverb=0.4, delay=0.18, pan_=0.25, vel=0.75)
s.chords("keys", "Em9 Gmaj7 A6 Bm7", inst=felt_piano, octave=3, bars_per_chord=2, rhythm="x.......x.....x.",
         gain=0.5, reverb=0.4)
s.motif("aron", "aron", inst=flute, octave=1, start_bar=2, end_bar=8, every=4, gain=1.0, reverb=0.5, delay=0.2)
s.notes("aron_hi", MOTIFS["aron_rising"], inst=glass_keys, octave=1, start_bar=8, end_bar=12, gain=0.8,
        reverb=0.55, delay=0.25, pan_=-0.2)
s.notes("aron_hi_fl", MOTIFS["aron_rising"], inst=flute, octave=1, start_bar=12, end_bar=16, gain=0.75,
        reverb=0.55, pan_=0.15)
s.notes("clock", "~ ~ ~ ~ ~ ~ ~ ~ | 1 ~ ~ 7 ~ ~ 1 ~", inst=music_box, octave=1, start_bar=2, every=4, gain=0.5,
        reverb=0.5, delay=0.3, pan_=-0.35)
s.notes("bass", "1, ~ ~ ~ ~ ~ 5,, ~ | 1, ~ ~ ~ ~ ~ ~ ~ | 3, ~ ~ ~ ~ ~ 7,, ~ | 3, ~ ~ ~ ~ ~ ~ ~ | "
        "4, ~ ~ ~ ~ ~ 1, ~ | 4, ~ ~ ~ ~ ~ ~ ~ | 5,, ~ ~ ~ ~ ~ 2, ~ | 5,, ~ ~ ~ ~ ~ ~ ~",
        inst=sub_bass, gain=0.6, legato=0.95)
# the clock: tick on every beat, a softer tock on the off-beats, a felt kick on 1
s.drums("tick: X...x...X...x...", gain=0.9, reverb=0.2)
s.drums("wood: ..x...x...x...x.", gain=0.2, reverb=0.2)
s.drums("softkick: x.........x.....", gain=0.4)
s.fx("drums_wood", lp=1800)
a = snap("april_showers_1921", 52.0)
s.sample("memory", "april_showers_1921", start=a, length=1.6, at_bar=[4, 12], fit=4,
         fx=["pitch+2", "stretch4", "dreamy", "lp1400", "arch"], gain=0.8, reverb=0.7)
s.render(out("quiz", sub=SUB))

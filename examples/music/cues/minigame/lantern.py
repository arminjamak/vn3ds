"""Lantern Rhythm - Ember's rhythm game: keep the lantern lit in time.
Warm, steady and kind; the beat must be unmistakable, because a rhythm chart
is written on exactly this grid.

THE GRID (do not change without telling the chart):
    96 BPM, 4/4, 16 bars, 1 beat = 0.625 s = 20000 samples at 32 kHz,
    1 bar = 80000 samples, loop = 40.000 s = 1 280 000 samples.
    Beat 1 of bar 1 is sample 0: no pickup, no silence.
    A warm kick sits on every beat of every bar.
Sections, 4 bars each, density rising:
    bars  1-4   quarters      kick, pulse bass and piano on the beat; the lantern
                              motif in quarter notes
    bars  5-8   eighths       guitar arpeggio and shaker in eighths; the motif as written
    bars  9-12  syncopation   off-beat piano stabs, bass on 1 / 2& / 4, the motif on
                              the off-beats, rim on the "and" of 2 and 4
    bars 13-16  fuller        everything: pad, clap on 2 and 4, sixteenth shaker,
                              the motif doubled, the radio record

Motifs: the Lantern (`5 5 5 6 1'`, three flickers and a rising answer) carries
every section; Aron's question gets the Lantern's warm answer in the last two
bars (as at the end of `lantern_watch`).
Sample: My Buddy (1922), the Watch's "song on the radio", in E."""
from vnsynth import *
from _mg import SUB, beat_kick

BARS = 16
s = Song(bpm=96, bars=BARS, key="E major")
assert s.n_loop == 1280000 and abs(s.length_s - 40.0) < 1e-9
BEAT = 20000                                  # samples
s.texture("vinyl", "vinyl", gain=0.3)

# ---- the beat: a warm kick on every beat of every bar, placed on the exact sample
for b in range(BARS * 4):
    accent = 1.0 if b % 4 == 0 else 0.86
    s.add("beat", beat_kick(accent), t=(b * BEAT + 0.25) / SR, reverb=0.08)
    s.kick_times.append(b * BEAT / SR)

prog = "Emaj9 C#m7 Amaj7 B6"                   # one chord per bar, the Watch's harmony
roots = ["1,", "6,,", "4,,", "5,,"]           # E2 C#2 A1 B1
fifths = ["5,", "3,", "1,", "2,"]

# ---- bars 1-4: quarters
s.chords("piano", prog, inst=felt_piano, octave=3, end_bar=4, rhythm="x...x...x...x...", gain=0.62, reverb=0.4,
         duck=0.25)
s.notes("pulse", " | ".join(" ".join([r] * 4) for r in roots), inst=sub_bass, end_bar=4, legato=0.7, gain=0.62,
        reverb=0.03)
s.notes("lantern", "5 5 5 6 | 1' ~ ~ ~", inst=glass_harmonica, octave=1, end_bar=4, gain=0.95, reverb=0.55,
        legato=0.8)
s.notes("lantern_vibes", "5 5 5 6 | 1' ~ ~ ~", inst=mallet, octave=1, end_bar=4, gain=0.5, reverb=0.45, pan_=0.3)

# ---- bars 5-8: eighths
s.chords("piano2", prog, inst=felt_piano, octave=3, start_bar=4, end_bar=8, rhythm="x...x...x...x...", gain=0.5,
         reverb=0.4, duck=0.25)
s.notes("pulse2", " | ".join(f"{r} {r} {f} {r} {r} {r} {f} {r}" for r, f in zip(roots, fifths)), inst=round_bass,
        start_bar=4, end_bar=8, legato=0.7, gain=0.5, reverb=0.03)
s.notes("guitar", "1 5 1' 5 3' 5 1' 5 | 6, 3 6 3 1' 3 6 3 | 4, 1 4 1 6 1 4 1 | 5, 2 5 2 7 2 5 2", inst=dream_guitar,
        octave=1, start_bar=4, end_bar=8, gain=0.4, chorus_mix=0.5, reverb=0.45, pan_=-0.3, vel=0.7)
s.notes("lantern2", MOTIFS["lantern"], inst=glass_harmonica, octave=1, start_bar=4, end_bar=8, gain=0.95, reverb=0.55)
s.notes("lantern2_vibes", MOTIFS["lantern"], inst=mallet, octave=1, start_bar=4, end_bar=8, gain=0.5, reverb=0.45,
        pan_=0.3)
s.drums("shaker: x.x.x.x.x.x.x.x.", start_bar=4, end_bar=8, gain=0.5)

# ---- bars 9-12: syncopation
s.chords("stabs", prog, inst=felt_piano, octave=3, start_bar=8, end_bar=12, rhythm="..x...x...x..x.x", gain=0.55,
         reverb=0.4, duck=0.25)
s.notes("pulse3", " | ".join(f"{r} ~ ~ ~ ~ ~ {r} ~ ~ ~ {f} ~ {r} ~ ~ {f}" for r, f in zip(roots, fifths)),
        inst=round_bass, start_bar=8, end_bar=12, legato=0.8, gain=0.55, reverb=0.03)
s.notes("lantern3", "~ 5 ~ 5 ~ 5 6 ~ | 1' ~ ~ ~ ~ 6 ~ 5", inst=glass_harmonica, octave=1, start_bar=8, end_bar=12,
        gain=0.95, reverb=0.55)
s.notes("lantern3_vibes", "~ 5 ~ 5 ~ 5 6 ~ | 1' ~ ~ ~ ~ 6 ~ 5", inst=mallet, octave=1, start_bar=8, end_bar=12,
        gain=0.55, reverb=0.45, pan_=0.3)
s.drums("rim: ......x.......x. | shaker: x.x.x.x.x.x.x.x.", start_bar=8, end_bar=12, gain=0.5)

# ---- bars 13-16: fuller
s.chords("pad", "Emaj7 C#m9 Amaj9 Bsus4", inst=warm_pad, octave=3, start_bar=12, end_bar=16, gain=0.5, reverb=0.6,
         duck=0.4)
s.chords("piano4", prog, inst=felt_piano, octave=3, start_bar=12, end_bar=16, rhythm="x.x...x.x.x...x.", gain=0.5,
         reverb=0.4, duck=0.25)
s.notes("pulse4", " | ".join(f"{r} {r} {f} {r} ~ {r} {f} {r}" for r, f in zip(roots, fifths)), inst=round_bass,
        start_bar=12, end_bar=16, legato=0.7, gain=0.55, reverb=0.03)
s.notes("guitar4", "1 5 1' 5 3' 5 1' 5 | 6, 3 6 3 1' 3 6 3 | 4, 1 4 1 6 1 4 1 | 5, 2 5 2 7 2 5 2", inst=dream_guitar,
        octave=1, start_bar=12, end_bar=16, gain=0.32, chorus_mix=0.5, reverb=0.45, pan_=-0.3, vel=0.6)
s.notes("lantern4", MOTIFS["lantern"], inst=glass_harmonica, octave=1, start_bar=12, end_bar=14, gain=0.95, reverb=0.55)
s.notes("lantern4_flute", MOTIFS["lantern"], inst=flute, octave=1, start_bar=12, end_bar=14, gain=0.7, reverb=0.5,
        pan_=-0.2)
s.notes("aron", "1 ~ 5 ~ 4 3 ~ ~ | 2 ~ 3 ~ 5 ~ ~ ~", inst=flute, octave=1, start_bar=14, end_bar=16, gain=0.75,
        reverb=0.5, pan_=-0.2)
s.notes("aron_glass", "~ ~ ~ ~ ~ ~ ~ ~ | 5 ~ 5 ~ 5 ~ 6 ~", inst=glass_harmonica, octave=1, start_bar=14, end_bar=16,
        gain=0.8, reverb=0.55)
s.drums("clap: ....x.......x... | shaker: xxxxxxxxxxxxxxxx", start_bar=12, end_bar=16, gain=0.42)
m = snap("my_buddy_1922", 132.0)
s.sample("radio", "my_buddy_1922", start=m, length=4.0, at_bar=[12], fit=2,
         fx=["78rpm", "telephone", "far", "wobble", "arch"], gain=0.7, reverb=0.5, pan_=0.45)
s.render(out("lantern", sub=SUB))

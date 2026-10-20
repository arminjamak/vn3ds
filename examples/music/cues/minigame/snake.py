"""Crown of the Worm - the snake game: a little worm eats its way to a crown.
Glitchy, bubbly and mischievous, with an occasional detuned or bit-crushed
accent, like a program enjoying a bug.
Motifs: the System's three pulses turned into bubbles (the worm is a
process too); Aron's question, cut short and grinning, on glass keys; at
the end of each half a chord stab is crushed to bits and sinks out of tune.
Samples: Krooked Blues (1923) chopped, glitched and lo-fi; Ogopogo (1925)
stuttered as the worm's crown fanfare."""
from vnsynth import *
from _mg import SUB, bubble, crush, detune, dive, exact_bpm, pizzicato

s = Song(bpm=exact_bpm(116, 16), bars=16, key="G dorian", swing=0.08)
s.texture("tape", "tape", gain=0.3)
s.chords("pad", "Gm9 Ebmaj7 Cm9 D7sus4", inst=shimmer_pad, octave=3, gain=0.5, reverb=0.55, duck=0.5)
s.fx("pad", tremolo=(116 / 60 * 2, 0.5))
# the worm: bubbles on sixteenths (System pulses, then a wiggle)
s.notes("bubbles", "1' 1' 1' ~ 7 ~ ~ 5 ~ ~ 1' ~ 3' ~ 2' ~ | ~ 5 ~ 1' 7 ~ 5 ~ 4 ~ ~ 5 ~ ~ ~ ~",
        inst=bubble, octave=1, gain=0.75, reverb=0.35, delay=0.2, pan_=0.25)
s.notes("bubbles_lo", "~ ~ ~ ~ ~ ~ 1 ~ ~ ~ ~ ~ ~ 5, ~ ~", inst=bubble, octave=1, every=1, gain=0.45, reverb=0.3,
        pan_=-0.3)
s.notes("bass", "1, ~ 1 ~ ~ 1, 5, ~ | 6,, ~ 6, ~ ~ 6,, 3, ~ | 4, ~ 4 ~ ~ 4, 1 ~ | 5, ~ 5 ~ @6, 5, 2 ~",
        inst=round_bass, gain=0.55, reverb=0.05, legato=0.55, duck=0.3)
s.notes("grin", "1 ~ 5 ~ 4 ~ 3 4 | 5 ~ ~ ~ ~ ~ ~ ~", inst=glass_keys, octave=1, start_bar=4, every=8, gain=0.7,
        reverb=0.45, delay=0.3, pan_=-0.2)
s.notes("pluck", "~ ~ 5 ~ ~ 1' ~ ~ | ~ 7 ~ ~ 5 ~ ~ ~", inst=pizzicato, octave=1, start_bar=8, end_bar=12,
        gain=0.6, reverb=0.3, pan_=0.4)
s.drums("kick: x..x..x...x..... | snap: ....x.......x... | hat: x.xxx.x.x.xxx.x.", gain=0.42)
s.drums("tick: ..x....x..x...xx", start_bar=8, gain=0.4)
s.fx("drums_hat", crush=True)
s.fx("drums_tick", crush=True)

# the mischief: a chord stab crushed to bits that sinks out of tune (bars 4, 8, 12 and 16, the last beat)
chord = sum(glass_keys(midi_to_hz(m), 0.3) for m in parse_chord("Gm", 4))
stab = dive(crush(detune(chord, 35), hold=8, levels=12), cents=-500)
for b in (3, 7, 11, 15):
    s.add("stab", stab * 0.55, t=(b + 0.75) * s.bar_s, reverb=0.3, delay=0.15, pan_=0.15 if b % 2 else -0.15)
k = snap("krooked_blues_1923", 148.0)
s.sample("krooked", "krooked_blues_1923", start=k, length=2.4, at_bar=[4, 12], fit=2,
         fx=["pitch-2", "glitch", "lofi", "lp2600"], gain=0.55, reverb=0.35, pan_=0.4)
o = snap("ogopogo_1925", 100.0)
s.sample("crown", "ogopogo_1925", start=o, length=1.1, at_bar=[7, 15], fit=1,
         fx=["pitch+3", "stutter", "telephone", "fadeout"], gain=0.5, reverb=0.4, delay=0.2, pan_=-0.35)
s.render(out("snake", sub=SUB))

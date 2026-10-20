"""Miso's Hunt - Miso stalks something only she can see. Playful and
sneaky: pizzicato on tiptoe, a little swing, and a hint of glitch (the world
she hunts in is rendered, after all).
Motifs: Miso's pounce-pause-fall on pizzicato and vibes (in the minor, which
makes it sneak); a chromatic tiptoe creeping up to the pounce; Aron's
question on low flute, very seriously, interrupted by the pounce; the
System's three pulses, crushed, glitching once per half.
Sample: Ogopogo (1925), a tiny bright stab, buffer-glitched: a toy batted off
a table. A tiny mew closes the loop, as in `miso`."""
from vnsynth import *
from _mg import SUB, crush, exact_bpm, fade_edges, meow, pizzicato

s = Song(bpm=exact_bpm(104, 16), bars=16, key="D minor", swing=0.18)
s.texture("room", "room", gain=0.35)
# tiptoe bass: pizzicato on every other eighth, a cat placing its paws
s.notes("paws", "1, ~ 5, ~ 1 ~ 5, ~ | 6,, ~ 3, ~ 6, ~ 3, ~ | 4, ~ 1 ~ 4, ~ 6, ~ | 5, ~ 7#, ~ 2 ~ 4 ~",
        inst=pizzicato, gain=0.75, reverb=0.25, pan_=-0.1)
s.chords("stabs", "Dm7 Bbmaj7 Gm7 A7", inst=glass_keys, octave=3, rhythm="..x...x.", gain=0.42, reverb=0.35)
s.motif("pounce", "miso", inst=pizzicato, octave=1, start_bar=2, every=4, gain=1.0, reverb=0.35, pan_=0.25)
s.motif("pounce_vibes", "miso", inst=mallet, octave=1, start_bar=10, every=4, gain=0.55, reverb=0.4, pan_=-0.25)
# the creep: chromatically up to the root, then hold still
creep = "~ 5 ~ 6 ~ @9 ~ 7 | ~ @11 ~ 1' ~ ~ ~ ~"
s.notes("creep", creep, inst=pizzicato, octave=1, start_bar=4, end_bar=6, gain=0.75, reverb=0.35, pan_=0.35)
s.notes("creep2", creep, inst=mallet, octave=1, start_bar=12, end_bar=14, gain=0.45, reverb=0.4, pan_=0.35)
s.notes("lecture", "1 ~ 5 ~ 4 3 ~ ~ | ~ ~ ~ ~ ~ ~ ~ ~", inst=flute, octave=0, start_bar=8, end_bar=10, gain=0.8,
        reverb=0.4)
s.drums("snap: ....x.......x... | shaker: ..x...x...x...x. | softkick: x.......x.......", gain=0.4)
s.drums("tick: ...........x..x.", start_bar=3, end_bar=4, gain=0.45)
s.drums("tick: ...........x..x.", start_bar=11, end_bar=12, gain=0.45)

# the glitch: the System's pulses, crushed, once per half; a stuttered pounce in the last bar
s.notes("system", "1' 1' 1' ~ 7 ~ ~ ~", inst=pulse_blip, octave=1, start_bar=7, end_bar=8, gain=0.45, reverb=0.3,
        pan_=-0.4)
s.fx("system", crush=True)
pounce = fade_edges(pizzicato(midi_to_hz(parse_note("1'", s.key_root, s.scale) + 12), 0.2)[: int(0.09 * SR)], 0.001, 0.01)
stut = np.concatenate([pounce * g for g in (1.0, 0.8, 0.65, 0.5)])
s.add("stutter", crush(stut, hold=5, levels=20), t=15 * s.bar_s + 4 * s.bar_s / 8, gain=1.0, reverb=0.3, pan_=0.3)
o = snap("ogopogo_1925", 8.0)
s.sample("toy", "ogopogo_1925", start=o, length=0.55, at_bar=[3.75, 11.75], fx=["pitch+2", "glitch", "78rpm", "lp3000"],
         gain=0.6, reverb=0.35, pan_=-0.4)
s.add("mew", meow(), t=15.62 * s.bar_s, reverb=0.3, pan_=0.2, gain=0.9)
s.render(out("miso", sub=SUB))

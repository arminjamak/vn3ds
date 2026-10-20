"""Echo of a Shape - the drawing game: a shape is shown, then gone, and drawn
again from memory. Minimal and sparse, the tutorial's "less, but better":
a few notes, lots of air, no drums.
Motifs: Aron's question on felt piano, its echo two bars later an octave up
on vibes, fainter (the shape remembered); one long glass note in between;
the Light's last turn (`3 5 1'`) once, at the very end, as if the shape
were almost right.
Sample: My Buddy (1922), stretched far into an airy bed, barely there."""
from vnsynth import *
from _mg import SUB

s = Song(bpm=64, bars=12, key="C lydian")      # 45.0 s, exactly 1 440 000 samples
s.texture("room", "room", gain=0.4)
s.texture("tape", "tape", gain=0.12)
s.chords("pad", "Cmaj9 D6 Em7", inst=warm_pad, octave=3, bars_per_chord=4, gain=0.38, reverb=0.7)
s.notes("shape", "1 ~ 5 ~ 4 3 ~ ~ | 2 ~ ~ ~ ~ ~ ~ ~", inst=felt_piano, octave=1, start_bar=0, every=6, gain=0.75,
        reverb=0.6)
s.notes("echo", "1 ~ 5 ~ 4 3 ~ ~ | 2 ~ ~ ~ ~ ~ ~ ~", inst=mallet, octave=2, start_bar=2, every=6, gain=0.3,
        reverb=0.7, delay=0.35, pan_=0.35, vel=0.7)
s.notes("glass", "~ ~ ~ ~ 5 _ _ _ | _ _ _ _ ~ ~ ~ ~", inst=glass_harmonica, octave=1, start_bar=4, end_bar=6,
        gain=0.5, reverb=0.7, pan_=-0.3)
s.notes("glass2", "~ ~ ~ ~ 4 _ _ _ | _ _ _ _ ~ ~ ~ ~", inst=glass_harmonica, octave=1, start_bar=8, end_bar=10,
        gain=0.45, reverb=0.7, pan_=-0.3)
s.notes("glass3", "~ ~ ~ ~ 2' _ _ _ | ~ ~ ~ ~ ~ ~ ~ ~", inst=glass_harmonica, octave=1, start_bar=11, end_bar=12,
        gain=0.3, reverb=0.75, pan_=0.3)
s.notes("almost", "~ ~ ~ ~ 3 ~ 5 ~ | 1' ~ ~ ~ ~ ~ ~ ~", inst=felt_piano, octave=1, start_bar=10, end_bar=12,
        gain=0.55, reverb=0.65, vel=0.8)
# the floor: one long low note under each chord
for bar, deg in ((0, "1,"), (4, "2,"), (8, "3,")):
    s.add("bass", warm_pad(midi_to_hz(parse_note(deg, s.key_root, s.scale)), 3.6 * s.bar_s), at_bar=bar, gain=0.5,
          reverb=0.3)
m = snap("my_buddy_1922", 104.0)
s.sample("air", "my_buddy_1922", start=m, length=2.0, at_bar=[0, 6], fit=6,
         fx=["stretch3", "dreamy", "lp1200", "hp200", "arch"], gain=0.55, reverb=0.8)
s.render(out("draw", sub=SUB))

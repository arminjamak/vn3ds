"""Real World Vigil - a cut to the original World 7,412: the real Mira by
Aron's comatose body. The monitor keeps time. Sorrow.
Motifs: Mira's turn in the minor, slow, on felt piano and then strings,
stopping one note short of home (the 1 never comes).
Sample: My Buddy (1922): "nights are long since you went away", pitched
into C minor and slowed, very far."""
from vnsynth import *

s = Song(bpm=60, bars=12, key="C minor")
s.texture("room", "room", gain=0.7)
s.notes("monitor", "1'' ~ ~ ~ ~ ~ ~ ~", inst=pulse_blip, octave=0, every=2, gain=0.6, reverb=0.4, pan_=0.4)
s.chords("strings", "Cm9 Abmaj7 Fm9 Gsus4", inst=strings, octave=3, bars_per_chord=3, gain=0.8, reverb=0.6)
s.notes("mira", "3 ~ 4 ~ 5 ~ ~ ~ | 3 ~ ~ ~ ~ ~ ~ ~ | 2 ~ ~ ~ ~ ~ ~ ~ | ~ ~ ~ ~ ~ ~ ~ ~ | ~ ~ ~ ~ ~ ~ ~ ~ | "
        "~ ~ ~ ~ ~ ~ ~ ~", inst=felt_piano, octave=1, gain=1.0, reverb=0.55, delay=0.15)
s.notes("mira_str", "~ ~ ~ ~ ~ ~ ~ ~ | ~ ~ ~ ~ ~ ~ ~ ~ | ~ ~ ~ ~ ~ ~ ~ ~ | 3 _ 4 _ 5 _ _ _ | 3 _ _ _ _ _ _ _ | "
        "2 _ _ _ _ _ _ _", inst=strings, octave=1, gain=0.8, reverb=0.6, pan_=-0.2)
s.notes("bass", "1, _ _ _ _ _ _ _", inst=sub_bass, every=3, legato=2.6, gain=0.5)
b = snap("my_buddy_1922", 104.0)
s.sample("buddy", "my_buddy_1922", start=b, length=4.0, at_bar=[1, 7], fit=4,
         fx=["pitch+1", "stretch2", "78rpm", "far", "arch"], gain=0.9, reverb=0.75, pan_=-0.4)
s.render(out("real_world_vigil"))

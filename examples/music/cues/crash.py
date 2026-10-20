"""Crash - the comedown: paranoia, shame, Mira's fear, Theo's worry. Show the
cost. Everything from the club, slowed, detuned and sinking.
Motifs: Aron's question falling past where it should stop (2 - 1 - 7 - 6...);
the club's arpeggio at half speed under a closing filter.
Sample: Ogopogo (1925) an octave down, stretched and reversed: the party
running backwards at a crawl."""
from vnsynth import *

s = Song(bpm=60, bars=12, key="D minor")
s.texture("tape", "tape", gain=0.7)
s.chords("pad", "Dm9 Bbmaj7 Gm9 A7sus4", inst=warm_pad, octave=3, bars_per_chord=3, gain=0.8, reverb=0.7)
s.chords("pad_detuned", "Dm9 Bbmaj7 Gm9 A7sus4", inst=shimmer_pad, octave=3, bars_per_chord=3, gain=0.35,
         reverb=0.7)
s.fx("pad_detuned", lp=900, tremolo=(0.25, 0.5))
s.notes("falling", "1 ~ 5 ~ 4 3 ~ ~ | 2 ~ ~ 1 ~ ~ 7, ~ | ~ ~ 6, ~ ~ ~ ~ ~ | ~ ~ ~ ~ ~ ~ ~ ~ | ~ ~ ~ ~ ~ ~ ~ ~ | "
        "~ ~ ~ ~ ~ ~ ~ ~", inst=felt_piano, octave=1, gain=0.9, reverb=0.6, delay=0.25)
s.notes("arp", "1 5 1' 3' 5 1' 3' 5' | 6, 3 6 1' 3 6 1' 3'", inst=arp_pluck, octave=1, every=3, gain=0.3,
        reverb=0.5, delay=0.3, pan_=0.25)
s.fx("arp", sweep_lp=[(0, 1600), (12, 350)])
s.notes("bass", "1, _ _ _ _ _ _ _", inst=sub_bass, every=3, legato=2.5, gain=0.6)
s.drums("softkick: x.......x.......", gain=0.4)
o = snap("ogopogo_1925", 8.0)
s.sample("slow_party", "ogopogo_1925", start=o, length=3.3, at_bar=[0, 6], fit=6,
         fx=["pitch-12", "reverse", "dreamy", "warble", "arch"], gain=0.6, reverb=0.6, pan_=-0.2)
s.render(out("crash"), lowpass_master=6000)

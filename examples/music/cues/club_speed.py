"""Club Speed - the night with street speed: a dreamy electronic club track at
126 BPM, everything bright and too fast, a sudden realisation in the breakdown.
(The cost follows in `crash`.) Never glamorous: the top end stays soft.
Motifs: Aron's question as a chopped vocal hook, sped up and repeated until it
almost sounds like an answer; in the breakdown it slows back to itself.
Sample: Ogopogo (1925), stuttered and pitched into A minor, the 1920s dance
floor inside the modern one."""
from vnsynth import *

s = Song(bpm=126, bars=32, key="A minor")
s.chords("pad", "Am9 Fmaj7 Cmaj7 G6", inst=shimmer_pad, octave=3, bars_per_chord=2, gain=0.75, reverb=0.6,
         duck=0.7)
s.notes("arp", "1 5 1' 3' 5 1' 3' 5' | 6, 3 6 1' 3 6 1' 3' | 4, 1 4 6 1 4 6 1' | 5, 2 5 7 2 5 7 2'",
        inst=arp_pluck, octave=1, every=8, gain=0.3, reverb=0.4, delay=0.3, duck=0.5, pan_=0.2)
s.notes("acid", "1, 1, 1 1, 1, 5, 1, 1 | 6,, 6,, 6, 6,, 6,, 3, 6,, 6, | 4,, 4,, 4, 4,, 4,, 1, 4,, 4, | "
        "5,, 5,, 5, 5,, 5,, 2, 5,, 5,", inst=acid_bass, every=8, end_bar=16, gain=0.6, reverb=0.05, duck=0.4)
s.notes("acid2", "1, 1, 1 1, 1, 5, 1, 1 | 6,, 6,, 6, 6,, 6,, 3, 6,, 6, | 4,, 4,, 4, 4,, 4,, 1, 4,, 4, | "
        "5,, 5,, 5, 5,, 5,, 2, 5,, 5,", inst=acid_bass, start_bar=20, every=8, gain=0.6, reverb=0.05, duck=0.4)
hook = "1 1 5 ~ 4 3 ~ 2 | ~ ~ 1 1 5 ~ 4 3"
s.notes("hook", hook, inst=vocal_chop, octave=1, start_bar=4, end_bar=16, every=2, gain=0.7, reverb=0.5, delay=0.3,
        duck=0.5)
s.notes("hook2", hook, inst=vocal_chop, octave=1, start_bar=24, every=2, gain=0.7, reverb=0.5, delay=0.3, duck=0.5)
s.notes("realise", MOTIFS["aron_rising"], inst=soft_lead, octave=1, start_bar=16, end_bar=20, gain=0.8, reverb=0.7,
        delay=0.35)
s.fx("realise", sweep_lp=[(0, 3000), (16, 600), (20, 3000), (32, 3000)])
s.drums("kick: x...x...x...x... | clap: ....x.......x... | openhat: ..x...x...x...x. | shaker: x.x.x.x.x.x.x.x.",
        end_bar=16, gain=0.55)
s.drums("shaker: x.x.x.x.x.x.x.x.", start_bar=16, end_bar=20, gain=0.55)
s.drums("kick: x...x...x...x... | clap: ....x.......x... | openhat: ..x...x...x...x. | shaker: x.x.x.x.x.x.x.x.",
        start_bar=20, gain=0.55)
o = snap("ogopogo_1925", 108.0)
s.sample("ogo", "ogopogo_1925", start=o, length=4 * 0.274, at_bar=[3, 7, 11, 15, 23, 27, 31], fit=1,
         fx=["pitch+1", "stutter", "lp3000", "hp250"], gain=0.6, reverb=0.4, delay=0.2, pan_=-0.3)
s.sample("ogo_far", "ogopogo_1925", start=o, length=8 * 0.274, at_bar=[16], fit=4,
         fx=["pitch+1", "stretch3", "dreamy", "warble", "arch"], gain=0.8, reverb=0.7)
s.render(out("club_speed"))

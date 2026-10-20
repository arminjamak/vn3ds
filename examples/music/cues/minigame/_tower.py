"""The Tower - one piece in four intensities (tower_1..tower_4), one per
difficulty tier. The game switches between them mid-run, so all four share
the key (D minor), the harmony, the motif and the timbres (shimmer pad,
plucked arpeggio, round bass, vibes/flute lead, the same drum kit); only the
tempo and the density rise.

    tier  BPM   bars  added
    1     100   16    pad, arpeggio in eighths, bass on 1 and 3, felt kick, rim, tick
    2     112   20    + bass in eighths, shaker, brush backbeat, flute doubles the motif
    3     124   24    + four-on-the-floor kick, clap, open hats, sixteenth arpeggio, strings,
                        the toy soldiers
    4     138   24    + sixteenth hats, tom fills, the motif an octave up on the lead,
                        and the Light answers it at the top of the loop

Motif: Aron's question asked twice and higher (`aron_rising`): a climb. At
tier 4 the last phrase is the Light (`light`), the question answered at the
top of the tower.
Sample: Parade of the Wooden Soldiers (1923), a toy march climbing the stairs
(tiers 2-4, louder as it climbs)."""
from vnsynth import *
from _mg import SUB, exact_bpm

TIERS = {1: (100, 16), 2: (112, 20), 3: (124, 24), 4: (138, 24)}
PROG = "Dm9 Bbmaj7 Gm9 A7sus4"
ARP8 = "1 5 1' 2' 3' 2' 1' 5 | 6, 3 6 1' 3' 1' 6 3 | 4, 1 4 6 1' 6 4 1 | 5, 2 5 7# 2' 7# 5 2"
ARP16 = ("1 5 1' 2' 3' 5' 3' 2' 1' 5 1' 2' 3' 5' 3' 2' | 6, 3 6 1' 3' 5' 3' 1' 6 3 6 1' 3' 5' 3' 1' | "
         "4, 1 4 6 1' 4' 1' 6 4 1 4 6 1' 4' 1' 6 | 5, 2 5 7# 2' 4' 2' 7# 5 2 5 7# 2' 5' 2' 7#")
BASS2 = "1, ~ ~ ~ 1, ~ ~ ~ | 6,, ~ ~ ~ 6,, ~ ~ ~ | 4,, ~ ~ ~ 4,, ~ ~ ~ | 5,, ~ ~ ~ 5,, ~ ~ ~"
BASS8 = "1, 1, 1 1, 1, 1, 5, 1, | 6,, 6,, 6, 6,, 6,, 6,, 3, 6,, | 4,, 4,, 4, 4,, 4,, 4,, 1, 4,, | " \
        "5,, 5,, 5, 5,, 5,, 5,, 7#,, 5,,"


def build(tier):
    bpm, bars = TIERS[tier]
    s = Song(bpm=exact_bpm(bpm, bars), bars=bars, key="D minor")
    s.texture("tape", "tape", gain=0.25)
    s.chords("pad", PROG, inst=shimmer_pad, octave=3, gain=0.65, reverb=0.55, duck=0.15 + 0.15 * tier)
    if tier >= 3:
        s.notes("arp", ARP16, inst=arp_pluck, octave=1, gain=0.22, reverb=0.4, delay=0.22, duck=0.4, pan_=0.25)
        s.chords("strings", PROG, inst=strings, octave=3, gain=0.5, reverb=0.55, duck=0.3)
    else:
        s.notes("arp", ARP8, inst=arp_pluck, octave=1, gain=0.26, reverb=0.4, delay=0.25, pan_=0.25)
    s.notes("bass", BASS8 if tier >= 2 else BASS2, inst=round_bass, gain=0.5, reverb=0.04, legato=0.75,
            duck=0.1 * tier)

    # the climb: the question asked twice and higher, from bar 4 every 8 bars
    lead = flute if tier >= 2 else mallet
    end = bars - 4 if tier >= 4 else bars        # at tier 4 the last phrase belongs to the Light
    s.notes("motif", MOTIFS["aron_rising"], inst=mallet, octave=1, start_bar=4, end_bar=end, every=8, gain=0.65,
            reverb=0.45, delay=0.2, pan_=-0.2)
    if tier >= 2:
        s.notes("motif_fl", MOTIFS["aron_rising"], inst=lead, octave=1, start_bar=4, end_bar=end, every=8, gain=0.75,
                reverb=0.5, pan_=0.1)
    if tier >= 4:
        s.notes("motif_hi", MOTIFS["aron_rising"], inst=soft_lead, octave=2, start_bar=12, end_bar=16, gain=0.6,
                reverb=0.5, delay=0.25)
        s.notes("light", MOTIFS["light"] + " | " + MOTIFS["light"], inst=soft_lead, octave=2, start_bar=bars - 4,
                gain=0.75, reverb=0.55, delay=0.25)
        s.notes("light_vibes", MOTIFS["light"], inst=mallet, octave=2, start_bar=bars - 4, every=2, gain=0.45,
                reverb=0.45, pan_=0.3)

    if tier == 1:
        s.drums("softkick: x.......x....... | rim: ....x.......x... | tick: x.x.x.x.x.x.x.x.", gain=0.45)
    elif tier == 2:
        s.drums("softkick: x.......x.x..... | brush: ....x.......x... | shaker: x.x.x.x.x.x.x.x. | "
                "rim: ..........x.....", gain=0.45)
    elif tier == 3:
        s.drums("kick: x...x...x...x... | clap: ....x.......x... | openhat: ..x...x...x...x. | "
                "shaker: x.x.x.x.x.x.x.x.", gain=0.45)
    else:
        s.drums("kick: x...x...x...x..x | clap: ....x.......x... | openhat: ..x...x...x...x. | "
                "hat: xxxxxxxxxxxxxxxx | shaker: x.x.x.x.x.x.x.x.", gain=0.45)
        for b in range(3, bars, 4):
            s.drums("tom: ..........x.x.xx", start_bar=b, end_bar=b + 1, gain=0.4)

    if tier >= 2:
        w = snap("wooden_soldiers_1923", 100.0)
        s.sample("soldiers", "wooden_soldiers_1923", start=w, length=4 * 0.578, at_bar=list(range(3, bars, 8)), fit=1,
                 fx=["pitch-5", "78rpm", "lp2400", "arch"], gain=0.45 + 0.1 * tier, reverb=0.45, pan_=-0.3)
    s.render(out(f"tower_{tier}", sub=SUB))

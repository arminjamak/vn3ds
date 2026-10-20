"""Miso - Aron's cat, the running gag: he explains his elaborate theories to
her, at length, in great detail, and she says "Meow." A short playful theme.
Motifs: Miso's pounce-pause-fall on pizzicato guitar and vibes; Aron's
question, very seriously, on bassoon-ish low flute, interrupted by the pounce.
Sample: Ogopogo (1925), a tiny bright stab, like a toy being knocked off a table."""
from vnsynth import *

s = Song(bpm=108, bars=16, key="F major", swing=0.12)
s.texture("room", "room", gain=0.35)
s.chords("keys", "Fmaj7 Dm7 Gm7 C7", inst=glass_keys, octave=3, rhythm="x...x.x.", gain=0.6, reverb=0.3)
s.motif("miso", "miso", inst=dream_guitar, octave=1, every=2, gain=0.45, reverb=0.35, pan_=0.25, legato=0.4)
s.motif("miso_vibes", "miso", inst=mallet, octave=1, start_bar=8, every=4, gain=0.5, reverb=0.4, pan_=-0.25)
s.notes("lecture", "1 ~ 5 ~ 4 3 ~ ~ | 2 ~ ~ ~ ~ ~ ~ ~", inst=flute, octave=0, start_bar=4, every=8, gain=0.8,
        reverb=0.4)
s.notes("bass", "1, ~ 5,, ~ | 6,, ~ 3, ~ | 2, ~ 6,, ~ | 5,, ~ 1, ~", inst=round_bass, gain=0.45, reverb=0.05,
        legato=0.6)
s.drums("softkick: x.......x....... | snap: ....x.......x... | shaker: ..x...x...x...x.", gain=0.4)


def meow(seconds=0.5):
    """A tiny synthesized 'mew': a formant glide down, soft."""
    n = int(seconds * SR)
    t = np.arange(n) / SR
    f = 620 - 220 * (t / seconds) ** 1.5
    src = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.3 * np.sin(4 * np.pi * np.cumsum(f) / SR)
    x = bandpass(src, 900, 2) + 0.6 * lowpass(src, 700)
    return x * np.sin(np.pi * t / seconds) ** 1.5 * 0.25


s.add("meow", meow(), at_bar=[7.5, 15.5], reverb=0.3, pan_=0.2)
o = snap("ogopogo_1925", 8.0)
s.sample("stab", "ogopogo_1925", start=o, length=0.55, at_bar=[3, 11], fx=["pitch+2", "78rpm", "lp3000"],
         gain=0.7, reverb=0.35, pan_=-0.4)
s.render(out("miso"))

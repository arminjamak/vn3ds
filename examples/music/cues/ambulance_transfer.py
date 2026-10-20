"""Ambulance Transfer - the end of chapter 1. Half-conscious on the stretcher;
somewhere above him the entities move him into the protected world.
"Transfer complete." Heartbeat, a filtered siren far off, the Mira motif
closing like a door, the System's pulses taking over.
Sample: Somebody Loves Me (1924), the last warm thing, fading out."""
from vnsynth import *

s = Song(bpm=72, bars=16, key="E minor")
s.texture("room", "room", gain=0.6)
s.drums("heartbeat: x...x...x...x...", gain=0.6, reverb=0.25)
s.notes("drone", "1, _ _ _ _ _ _ _", inst=deep_drone, legato=8.0, every=8, gain=0.45, reverb=0.5)
s.chords("pad", "Em9 Cmaj7 Am9 Bsus4", inst=warm_pad, octave=3, bars_per_chord=2, gain=0.6, reverb=0.6)
# Mira's turn, the filter closing on it over eight bars
s.motif("mira", "mira", inst=felt_piano, octave=1, end_bar=10, every=2, gain=1.0, reverb=0.6, delay=0.25)
s.fx("mira", sweep_lp=[(0, 2400), (8, 260), (15.5, 260), (16, 2400)])
s.notes("system", MOTIFS["system"], inst=pulse_blip, octave=2, start_bar=4, every=2, gain=0.9, reverb=0.5, pan_=0.3)
s.notes("system2", MOTIFS["system"], inst=pulse_blip, octave=1, start_bar=8, every=1, gain=0.8, reverb=0.5,
        pan_=-0.3)


def siren(seconds):
    """Two-tone siren glide, slowed and far: a doppler fall at the end."""
    n = int(seconds * SR)
    t = np.arange(n) / SR
    f = 440 + 110 * np.sign(np.sin(2 * np.pi * 0.35 * t)) * 0.5 + 55 * np.sin(2 * np.pi * 0.35 * t)
    f *= 1 - 0.06 * np.clip(t / seconds - 0.5, 0, 1)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.3 * np.sin(4 * np.pi * np.cumsum(f) / SR)
    return lowpass(x, 900) * np.sin(np.pi * t / seconds) ** 2 * 0.12


s.add("siren", siren(s.bar_s * 6), at_bar=[1, 9], reverb=0.8, pan_=0.5)
m = snap("somebody_loves_me_1924", 140.0)
s.sample("warmth", "somebody_loves_me_1924", start=m, length=4.4, at_bar=[0], fit=4,
         fx=["78rpm", "dreamy", "far", "fadeout"], gain=0.9, reverb=0.6, pan_=-0.3)
s.render(out("ambulance_transfer"))

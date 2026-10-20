"""Alias: `ward` = `closed_ward` (kept because the script uses audio/ward.ogg, the original ward cue name).
Renders cues/closed_ward.py again into audio/ward.ogg."""
from vnsynth import render_as

render_as("closed_ward", "ward")

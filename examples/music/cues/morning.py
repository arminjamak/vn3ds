"""Alias: `morning` = `morning_render` (kept because the script uses audio/morning.ogg, the original chapter 1 morning cue name).
Renders cues/morning_render.py again into audio/morning.ogg."""
from vnsynth import render_as

render_as("morning_render", "morning")

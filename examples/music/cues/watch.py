"""Alias: `watch` = `lantern_watch` (kept because the script uses audio/watch.ogg, the original Lantern Watch cue name).
Renders cues/lantern_watch.py again into audio/watch.ogg."""
from vnsynth import render_as

render_as("lantern_watch", "watch")

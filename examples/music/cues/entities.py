"""Alias: `entities` = `angel_ops` (kept because the script uses audio/entities.ogg, the cue the script plays for every cut to the governing entities).
Renders cues/angel_ops.py again into audio/entities.ogg."""
from vnsynth import render_as

render_as("angel_ops", "entities")

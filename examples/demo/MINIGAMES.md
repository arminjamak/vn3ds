# Minigames in the story

Seven native minigames, each played once in the story (no repeats) and all
replayable from the title screen's Minigames menu. In a script:

    $ mg_quiz = vn3ds_minigame("quiz")      # 0-100

On the 3DS the engine plays the game; on PC `minigames.rpy` shows a stand-in.
Give each game a short lead-in that explains *why* Aron is doing this (in his
everyday life, never a menu or a "game" in-world) and a beat afterwards that
reacts to how it went (`if mg_quiz >= 70:` ... `elif mg_quiz >= 40:` ...).

## Where they go and what they shape

Each score nudges one of the seven principles in the direction it already
leans, up to about as much as two menu choices:

    $ p_truth += (1 if p_truth >= 0 else -1) * mg_quiz / 50.0

| id | game | chapter | moment (suggested) | principle |
|---|---|---|---|---|
| quiz | The Big Questions | 1 | Aron's hobby: quizzing himself on Bostrom, Descartes, the big questions | p_truth |
| miso | Miso's Hunt | 1 | at home: the leak glitches out of the walls, Miso hunts the dots | p_rest |
| draw | Echo of a Shape | 2 | art therapy on the ward: "draw what you saw" | p_less |
| lantern | Lantern Rhythm | 2 | the Lantern Watch cut: Ember keeps the lanterns lit | p_govern |
| snake | Crown of the Worm | 3 | the protected world glitches; the worm grows | p_share |
| tower | The Tower | 3 | before Ashveil's offer: climbing out through the top | p_exit |
| invaders | The Hungry Sky | 4 | the deepest layer: angels, spirits, then the hungry being | p_spirits |

## Cheats: 2 to 5 over the whole game

`default vn3ds_cheats = 0`. The engine shows the count on each minigame's
intro card; using one spends it (at most one per game).

- Guaranteed (2): one at the end of the tutorial (Seraphiel's calibration
  grants "one exception"), one at the end of chapter 2 (the rooftop mission).
- Earned (up to 3), from choices that show who Aron decides to be: kindness to
  a stranger (ch1), telling Mira the truth (ch2), standing with the Lantern
  Watch at Ember's trial (ch3). Pick the exact choices so a player can end
  with anything from 2 to 5.
- When one unlocks, say so in a small, in-world way, then a plain line:
  `"(A cheat for the minigames is yours. You have [vn3ds_cheats].)"`

# Minigame sound effects to make

Each name becomes `examples/demo/game/audio/minigame/<name>.ogg`. They are
loaded into a 6-voice bank per run, so keep them short, clean at both ends
(no clicks) and mono. Some are pitched at runtime with `mg_sfx_pitch` (noted).

## Shared (framework)
| name | sound |
|---|---|
| cheat | magical shimmer, ~0.6 s |
| result | gentle three-note reveal, ~1 s |

## The Big Questions (quiz)
| name | sound |
|---|---|
| quiz_right | bright chime |
| quiz_wrong | soft low thud |
| quiz_timeout | a clock bell |
| quiz_cheat_answer | short "meow"-like synth chirp |
| quiz_tick | soft clock tick, 0.05 s |
| quiz_move | tiny UI blip |
| quiz_next | whoosh, 0.3 s |

## The Tower (tower)
| name | when | sound |
|---|---|---|
| tower_step | every 0.22 s while walking | soft leafy footstep tick, ~0.06 s |
| tower_aligned | lined up under a reachable ring | tiny bright "ting", ~0.12 s |
| tower_jump | jump; also the hop into the hole | springy upward boing, ~0.2 s |
| tower_through_hoop | passing up through a ring (pitch rises 1 semitone per segment) | airy whoosh with a chime, ~0.3 s |
| tower_land | landing on the new leaf (pitch rises per segment) | soft leaf rustle and thump, ~0.15 s |
| tower_bonk | head hits a ring's rim | comic wooden bonk, ~0.15 s |
| tower_miss | jumped nowhere near the ring | short descending wah-wah, ~0.4 s |
| tower_thud | falls back onto his own leaf | dull thud with a dizzy wobble, ~0.3 s |
| tower_faster | new speed tier | rising whoosh and alarm stinger, ~0.5 s |
| tower_warp | cheat tier skip | sparkly teleport shimmer, upward, ~0.5 s |
| tower_summit | lands on the 16th leaf | quick rising arpeggio, ~0.6 s |
| tower_enter_hole | drops into the hole at the top | hollow plunk / falling pop, ~0.3 s |
| tower_pop_out | pops out into the scenery | cork pop plus whoosh, ~0.35 s |
| tower_win | lands in the scenery | short celebratory fanfare, ~1.2-1.5 s |
| tower_cheer | twice during the celebration | small crowd "yay" / party horn, ~0.5 s |
| tower_timeout | 3-minute limit reached | soft buzzer / clock bell, ~0.6 s |

## Echo of a Shape (draw)
| name | when | sound |
|---|---|---|
| draw_reveal | shape appears | soft rising glassy shimmer, 0.5 s |
| draw_tick | last 3 s of viewing, each second | quiet wooden click, 0.08 s |
| draw_vanish | shape disappears | airy reversed whoosh falling away, 0.5 s |
| draw_stroke_start | stylus touches the canvas | soft pencil tap on paper, 0.1 s |
| draw_stroke_end | stylus lifts | short paper lift / scratch tail, 0.1 s |
| draw_undo | last stroke removed | quick eraser rub, rising, 0.2 s |
| draw_clear | canvas wiped | longer eraser swipe / sheet whoosh, 0.35 s |
| draw_empty | Done with nothing drawn | dull soft "nope" thud, 0.15 s |
| draw_time_low | 5 s of drawing time left | two gentle warning pings, 0.4 s |
| draw_submit | drawing handed in | paper slide plus soft stamp, 0.3 s |
| draw_timeout | auto-submit at 25 s | muted bell, falling, 0.4 s |
| draw_score_good | match of 70% or more | bright two-note chime, 0.6 s |
| draw_score_ok | match of 40-69% | neutral single chime, 0.4 s |
| draw_score_bad | match under 40% | low soft descending tone, 0.5 s |
| draw_level_up | next exercise begins | short ascending three-note arpeggio, 0.5 s |
| draw_trace | cheat used | quick golden pen sweep with a sparkle, 0.8 s |

## Lantern Rhythm (lantern)
Bells are pitched per lane at rates 1.0 / 1.2599 / 1.4983 (root, major third,
fifth): record the bell on the lantern loop's tonic.

| name | when | sound |
|---|---|---|
| lantern_count | count-in beats 1-3 of bar 1 | soft wooden tick, 0.15 s |
| lantern_go | beat 4 of bar 1 | brighter tick with a tiny chime, 0.3 s |
| lantern_hit_perfect | perfect hit (pitched per lane) | soft glassy bell on the tonic, warm attack, 0.6 s |
| lantern_hit_good | good hit (pitched per lane) | duller, muted version of the bell, 0.4 s |
| lantern_miss | miss | a lantern sputters: small fizz, papery puff, low thump, 0.5 s |
| lantern_stray | tap with no lantern | quiet muffled paper tap, 0.15 s |
| lantern_streak | every 10 in a row | rising three-note shimmer arpeggio, 0.8 s |
| lantern_streak_break | losing a streak of 10+ | soft falling breathy whoosh, 0.5 s |
| lantern_section | beat 4 of bars 4, 8, 12 | gentle swell into a chime, 1.0 s |
| lantern_ember_help | cheat used | warm swell with a choir-like hum, 1.2 s |
| lantern_finale | last lantern judged | shimmering bell cluster rising and fading, 2.0 s |

## Crown of the Worm (snake)
| name | when | sound |
|---|---|---|
| snake_turn | a turn is queued | soft click, ~40 ms |
| snake_eat | eating food | crunchy bit-crushed digital bite, ~150 ms |
| snake_boost | boost | rising whoosh, ~300 ms |
| snake_boost_ready | boost recharged | tiny bright ping, ~80 ms |
| snake_filter_warn | filter warning (2 s countdown follows) | glitchy two-tone alarm stutter, ~600 ms |
| snake_filter_on | filter starts | static tearing burst, pitch bending down, ~450 ms |
| snake_filter_off | filter ends | reversed static snapping back, ~300 ms |
| snake_reshuffle | slices reshuffle | quick digital riffle, ~200 ms |
| snake_crown_appears | crown pops in | shimmering rising chime sparkle, ~900 ms |
| snake_crown | eating the crown | short triumphant fanfare, ~1.5 s |
| snake_rating | rating stamp on the final shot | stamp thunk plus sparkle, ~400 ms |
| snake_die | death | crunchy glitch collapse, falling, ~700 ms |
| snake_shed | cheat: the skin peels off | papery rip plus airy shimmer, ~500 ms |
| snake_shed_fading | 1.5 s of cheat left | three quick ticks, ~350 ms |
| snake_shed_end | cheat ends | soft thump, skin turns solid, ~250 ms |
| snake_wrap | wrapping through a wall in the cheat | warbly teleport blip, ~150 ms |
| snake_phase | passing through your body in the cheat | ghostly whoosh, ~120 ms |

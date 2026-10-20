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

## Miso's Hunt (miso)
| name | when | sound |
|---|---|---|
| miso_step | paw step (quiet, frequent) | soft paw pad on wood, 0.08 s |
| miso_pounce | pounce | quick airy whoosh plus a small chirp, 0.25 s |
| miso_catch | dot caught | bright glitchy pop, a pixel being eaten, 0.2 s |
| miso_combo | multiplier rises | rising three-note sparkle, 0.4 s |
| miso_combo_break | chain of 3+ times out | soft falling two-note tone, 0.35 s |
| miso_whiff | pounce on nothing | soft thump of paws landing, 0.15 s |
| miso_dot_spawn | a dot leaks from the wall | crackly bitcrushed fizz with a wet seep, 0.5 s |
| miso_dot_fade | a dot expires | short digital fizzle to silence, 0.3 s |
| miso_dot_blink | a blinker jumps (near Miso) | tiny teleport tick/zap, 0.1 s |
| miso_dot_flee | a shy dot runs | skittering glitch squeak, 0.25 s |
| miso_beam_on | a beam fades in | soft airy choir swell, 1.0 s |
| miso_beam_sweep | a beam is near | low gentle hum/whoosh, 0.6 s |
| miso_spotted | Miso is spotted | bright angelic "ting" plus a startled "mrrp?!", 0.6 s |
| miso_recover | the freeze ends | little shake-off ruffle, 0.3 s |
| miso_phase | the leak widens | low glitch rumble with a warble, 0.8 s |
| miso_nap | cheat: nap | cat yawn into a soft purr, 0.9 s |
| miso_wake | nap ends | small chirpy trill, 0.3 s |
| miso_bird | robin outside (ambient) | robin chirp, 0.4 s |
| miso_tick | last 5 seconds | soft clock tick, 0.1 s |
| miso_time_up | time's up | gentle bell, 0.6 s |
| miso_meow | the closing "Meow." | a clear, content synthesised meow, 0.7 s |

## The Hungry Sky (invaders)
Most are played at rate 0.95-1.05 for variety.

| name | sound |
|---|---|
| invaders_shoot | soft bright glassy "pew" of light, 0.12 s |
| invaders_hit_spirit | small airy pop with a sparkle tail, 0.3 s |
| invaders_hit_angel | bright chime burst with a feather flutter, 0.4 s |
| invaders_angel_armor | metallic "ting" (a captain's first hit), 0.15 s |
| invaders_enemy_shot | low golden bell-tone launch, 0.25 s |
| invaders_wisp | faint breathy whoosh, 0.25 s |
| invaders_dive | rising-then-falling wing swoop, 0.6 s |
| invaders_step | soft low thump as the formation steps down, 0.12 s |
| invaders_overrun | ominous low swell, 0.6 s |
| invaders_player_hit | crackling impact, a lantern sputter, 0.35 s |
| invaders_life_lost | two-note falling chime, 0.6 s |
| invaders_game_over | slow descending lantern-going-out tone, 1.5 s |
| invaders_wave_clear | short triumphant shimmer arpeggio, 1.0 s |
| invaders_wave_start | brief rising "here they come" swell, 0.6 s |
| invaders_golden_light | huge warm choir-like bloom (the cheat), 1.2 s |
| invaders_boss_roar | childlike but huge hungry "oooh" with a deep rumble, 1.5 s |
| invaders_boss_phase | hungry growl / stomach rumble, 0.8 s |
| invaders_boss_spread | soft breath-out with a scatter of light tones, 0.4 s |
| invaders_boss_pull | deep inhale that starts the vortex, 1.0 s |
| invaders_boss_pull_end | satisfied little "mm", 0.4 s |
| invaders_boss_spit | wet-cute "ptoo" with two tiny sparkle pops, 0.4 s |
| invaders_boss_hit | dull soft thud with a pitch-bent "hm", 0.15 s |
| invaders_boss_gulp | gulp/slurp (a shot into the open mouth), 0.25 s |
| invaders_boss_defeat | big glowing release winding down, 2.0 s |
| invaders_boss_sleep | tiny yawn into a soft snore, 1.5 s |

# Round 2: redesigned minigames

## The Big Questions, hosted by Adjutant Vael (quiz)
| name | sound |
|---|---|
| quiz_angel_voice | soft bell-like sung syllable, ~80 ms, neutral pitch (played per syllable at 1.2-1.45x) |
| quiz_read_skip | quick paper flick |
| quiz_hourglass_flip | glassy turn plus short sand hiss |
| quiz_quill_tap | light quill nib tap on parchment |
| quiz_angel_pleased | warm happy "mm!" with a shimmer of small bells |
| quiz_angel_sigh | soft sympathetic sigh ("aww") |
| quiz_miso_popin | cartoon pop plus a chirpy "mrrp" |
| quiz_angel_gasp | short scandalised gasp |
| quiz_miso_popout | small reverse pop |

## Lantern Rhythm with the angel and spirit band (lantern)
| name | sound |
|---|---|
| lantern_stage_up | the band levels up: a bright rising flourish in E (played at x1, x1.12, x1.26) |
| lantern_band_cheer | a small band/crowd whoop of angels and spirits |
| lantern_band_gasp | a soft collective "oh!" |
| lantern_whoosh_past | an island flying past: a breathy doppler whoosh, ~0.6 s |

## Echo of a Shape, taught by Pim at a whiteboard (draw)
| name | sound |
|---|---|
| draw_marker_uncap | marker cap popping off |
| draw_marker_squeak | short whiteboard-marker squeak (repeated, varied pitch) |
| draw_board_tap | marker tapping the board |
| draw_board_flip | a board panel flipping over on its stand |
| draw_board_wipe | eraser wiping a whiteboard |
| draw_paper_hold | paper rustle |
| draw_spirit_voice | Pim's short chatty voice blip (varied pitch) |
| draw_spirit_delight | Pim's delighted squeal |
| draw_spirit_hmm | Pim's encouraging "hmm!" |
| draw_spirit_meh | Pim's unimpressed deadpan grunt |
| draw_spirit_oops | Pim's "oops" (distracted by a moth) |

## The Hungry Sky, a vertical scrolling shooter (invaders)
| name | sound |
|---|---|
| invaders_spread | spread-shot volley: a soft fanning "fsh" |
| invaders_beam | piercing beam hum, ~0.6 s loopable (pitched up per level) |
| invaders_homing | homing-spark volley: twinkly seeking chirps |
| invaders_rapid | one rapid-fire shot (very frequent; keep it tiny, ~40 ms) |
| invaders_drop | a pickup falling out of a defeated enemy |
| invaders_pickup_weapon | picked up a new weapon type |
| invaders_weapon_up | same weapon again, level rises (pitched up per level) |
| invaders_weapon_down | a hit costs a weapon level: a deflating descend |
| invaders_pickup_heart | heart restored: warm two-note chime |
| invaders_turret_shot | halo turret angel fires its spread |
| invaders_ram_charge | rammer locks on: a rising tremble |
| invaders_ram | rammer launches its charge: a short whoosh |
| invaders_ram_hit | an enemy flies into the ship: a thud |
| invaders_boss_warning | "Something hungry is coming..." ominous sting, ~2 s |
| invaders_boss_tell | short chime at the start of each boss move's tell (pitched per move) |
| invaders_boss_spiral | spiral of light begins: a swirling shimmer |
| invaders_boss_sweep | cape-beam sweep fires: a long sizzling sweep |
| invaders_boss_stars | starfield cape releases its stars: a sparkly cascade |
| invaders_boss_dash_warn | the dash lane is marked: a sharp alarm blip |
| invaders_boss_dash | Ashveil whooshes across the screen |
| invaders_boss_tantrum | hungry tantrum starts: a comic wail/whine |

## Miso's Hunt, cat-food packages and leaps (miso)
| name | sound |
|---|---|
| miso_leap_side | take-off for a left/right leap: springy whoosh |
| miso_leap_up | take-off leaping away from the camera: whoosh fading away |
| miso_leap_down | take-off leaping toward the camera: whoosh rushing closer |
| miso_land | soft paw thump on landing |
| miso_bonk | a leap into furniture: comic thud |
| miso_leap_multi | two or more packages in one leap: bright bonus jingle |
| miso_pickup | grabbing a pouch or box: crinkle/munch (pitched per combo) |
| miso_pickup_rare | grabbing a golden tin: shiny can clink |
| miso_package_appear | a package shimmering out of the wall: glitchy shimmer |
| miso_rare_appear | a golden tin appearing: distinct sparkly chime |
| miso_package_land | a package plopping onto the floor |
| miso_package_vanish | a package dissolving back into the leak: glitch fizzle |

## Crown of the Worm, apples and the worm king (snake)
| name | sound |
|---|---|
| snake_apple_crunch | crisp apple bite (random pitch); replaces snake_eat |
| snake_golden_spawn | sparkly twinkle as a golden apple appears |
| snake_golden_apple | rich chime plus crunch: eating a golden apple |
| snake_golden_fade | soft dull downward blip: golden apple turns red |
| snake_stage_next | short upbeat stage-clear jingle, next filter announced |
| snake_leak_tires | glitchy wind-down sigh as a filter lifts on its own |
| snake_crowd_cheer | a little crowd of squeaky worm cheers as the crown lands |

## The Tower, an upward platformer around the tower (tower)
| name | sound |
|---|---|
| tower_skid | sneakers skidding when turning around at speed |
| tower_bounce | boing off a red mushroom |
| tower_crack | stone cracking and grinding as a ledge starts to shake |
| tower_crumble | the cracked ledge breaks and falls away |
| tower_stomp | landing on a beetle or crow: squishy pop (pitch rises with combo) |
| tower_hurt | losing a heart: short "oof" sting |
| tower_heart | picking up a heart: warm sparkle |
| tower_falling_warn | a falling acorn/tile/star is coming: whistle-down warning blip |
| tower_falling_hit | a falling thing smashes (wood knock / tile clatter / star burst by pitch) |
| tower_gust | the updraft cheat: a big rushing wind swell |
| tower_fall | dropped off the screen: descending slide whistle |
| tower_ko | out of hearts: deflated tumble |
| tower_milestone | every 50 m: small bright two-note ding |

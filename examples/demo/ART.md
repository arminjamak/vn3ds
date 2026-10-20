# Snapshot: art notes for the chapter scripts

All art comes from `examples/make_demo_assets.py` (characters, expressions,
talking frames, `talking.rpy`, `vn3ds.json`) and `examples/scenes3d.py`
(layered scenes). Run `python3 examples/make_demo_assets.py` to regenerate.
Contact sheets for reviewing faces at 3DS size:
`examples/demo/expressions.png` (everyone) and `examples/demo/expressions/<who>.png`
(one per character, still frame above and talking frame below).

## 1. Expressions

The faces have been redrawn. **`neutral` now looks relaxed and pleasant**
(a soft little smile, calm eyes), so it's the right default for ordinary
talk. Frowning brows appear only in `worried`, `sad`, `annoyed` and
(lightly) `determined`. Match the face to the line. A character who is just
listening, explaining or making small talk is `neutral` or `smile`, not
`worried`.

Every mood below exists for **aron, aron ward, aron light, mira, theo,
okafor, nurse, seraph, patron, ember, pim, dross**, each with its talking
frame (`<name> <mood> open`) and its `talk` animation in `talking.rpy`, so
`m happy "..."` and `show mira curious` both work and the mouth moves.

| mood | use when |
|---|---|
| `neutral` | the default: ordinary talk, listening, explaining. Calm and friendly. |
| `smile` | warm agreement, a pleasant moment, greeting someone. |
| `happy` | real delight: good news, being glad to see someone (eyes crinkle, mouth open). |
| `laugh` | laughing out loud at a joke (eyes shut ^^, big open mouth). |
| `grin` | cheeky, pleased with themselves, a pun, teasing (toothy grin). |
| `curious` | "huh?", interested, asking a question, one brow up. |
| `thinking` | working something out, recalling, "hmm" (eyes glance up and aside). |
| `surprised` | a sudden shock or surprise (wide eyes, small "o"). |
| `awe` | wonder: the stars, the golden light, something beautiful or vast (sparkly eyes). |
| `worried` | genuine concern or nervousness (brows up in the middle, wavy mouth). |
| `sad` | grief, disappointment, a heavy moment (droopy eyes, small frown). |
| `tired` | sleepy, medicated, worn out (heavy lids, shadows). Not grumpy. |
| `embarrassed` | flustered, caught out, shy, a compliment (blush lines, eyes aside). |
| `tender` | love, comfort, a quiet intimate line (soft eyes, small smile, blush). |
| `annoyed` | only for real friction: an argument, being pushed too far. |
| `determined` | resolve: making a decision, facing something, "let's do this". |

Extra moods:

- **pim, dross**: also `chatty` (open-mouthed gossip). `grumpy` is the same as `annoyed` (Dross's resting state).
- **patron** (Lord Ashveil): also `cold` (flat eyes, a straight line of a mouth: menace). His `smile` is the polite, hungry one.
- **miso**: `sit` (the default), `loaf` (curled up, eyes shut), `stare` (flat, unimpressed deadpan: the look before the final "Meow."), `meow` (mouth open), `curious` (head tilted, big round pupils), `sleepy` (sitting, eyes shut, "z z"), `happy` (eyes ^^, pink cheeks, tail up). All of them have a talking frame, `loaf` included.

Old names still work and show the same picture as the new mood:

| old name | is now |
|---|---|
| `<anyone> normal` (aron, aron ward, aron light, mira, theo, okafor, nurse) | `neutral` |
| `seraph stern` | `neutral` (calm, composed; use `determined` for a hard order) |
| `seraph concerned` | `worried` |
| `ember soft` | `tender` |
| `pim/dross grumpy` | `annoyed` |

Suggested re-tagging when you revise lines: `aron normal` in conversation is
fine as is (it's now a relaxed face). Swap `aron worried` for `thinking` or
`curious` where he is musing, not afraid, and use `tender` for Mira's soft
lines in bed or on the ward. Keep `tired` for the medicated stretches; it no
longer reads as a frown.

## 2. New angles of familiar places

Positions refer to the existing transforms: `slightleft` (xalign 0.22),
`center` (0.5), `slightright` (0.78), `catspot` (0.85). "Reverse" means the
same room seen from the other side: what was on the left is on the right,
and the window the original faced is now behind the camera (its light lies
on the floor or wall). The palettes, materials and furniture match the
originals, so cutting `bg kitchen` -> `bg kitchen reverse` is a
shot/reverse-shot in one room.

A good pattern for a conversation: establish with the original, put one
speaker's lines on the original and the other's on the reverse, and cut to
a `door`/`corner` shot for an overheard or observed moment (the documentary
crew filming from the next room). Pair them with `camera at doc_peek(...)`
for that look.

| scene | what you see | blocking |
|---|---|---|
| `bg kitchen reverse` | From the counter, looking back: the kitchen table with two chairs (her plate on the left, his cup on the right), the open door to the hallway (left, a coat on a hook), the wall clock at 7:07, a calendar, the fridge with their photo (right). The window's daylight lies on the floor at right, with the bird's still shadow in it. The coffee machine's corner (blue light) sits in the bottom-left foreground. | Seated at the table: left chair `slightleft`, right chair `slightright`. Coming in from the hallway: xalign 0.15. |
| `bg kitchen door` | The original kitchen (window with the bird at left, coffee machine at right), filmed from the hallway through the doorway; a coat on the hallway wall at left and the open door leaf at right frame the shot. | Keep people inside the door gap: `center` or xalign 0.35-0.65. Good for overheard lines. |
| `bg kitchen night reverse` | `bg kitchen reverse` at night: moonlight on the floor, the hall lamp and the coffee machine's light glowing. | as kitchen reverse |
| `bg room reverse` | The living room seen from its window: the blue sofa with a yellow cushion under the lighthouse picture (the dream), a coffee table with the notebook and a mug, the plant by the sofa's right arm, the doorway to the hallway on the right. The window's cross of light lies on the floor at left; the end of the bookshelf is a blurred edge at the far right. | On the sofa: `center` (two people at xalign 0.35 / 0.6). Standing: `slightleft`. In the doorway: xalign 0.82. Miso: `catspot` (the floor by the plant). |
| `bg room corner` | The original living room (bookshelf left, window right) filmed from behind the plant: its blurred leaves cover the lower left. | `center` or `slightright`; keep faces clear of the left third. |
| `bg room night reverse` | `bg room reverse` at night, the hall light on. | as room reverse |
| `bg bedroom reverse` | From the window, looking at the door: the bed along the left with its headboard and pillow at the right end, the nightstand with the 7:07 clock far left, the open door with warm hall light in the middle-right. Dawn light from the window behind the camera falls on the wall right of the door. | Sitting on the bed: `slightleft`. Standing in the room: `center`. In the doorway: xalign 0.58. |
| `bg bedroom night reverse` | the same at night: moonlight on the wall, the clock glowing. | as bedroom reverse |
| `bg cafe reverse` | From the window seats, looking at the bar: the espresso machine, stacked cups, the pastry case, the chalk menu ("coffee", "the same", "tea"), the pendant lamps, three small tables in front of the bar. Blue daylight from the big window behind the camera on the floor at right. | Behind the bar: xalign 0.3. At a table: `center`. Arriving from the street side: `slightright`. |
| `bg cafe corner` | The original cafe (window with THE SAME CAFE at left, three tables) filmed from the end of the bar: the espresso machine and cups blur across the lower right, with steam. | `slightleft` or `center`. |
| `bg park reverse` | Up the hill, looking back down the path: the town skyline on the horizon, the big tree now on the left, a pond with a bench and a lamp post on the right, the path down the middle. | On the path: `center`. On the bench: `slightright`. Under the tree: `slightleft`. |
| `bg ward reverse` | From the barred window, looking at the door: the door with its little window (left of centre), a sink in the corner (far left), the whiteboard "Nurse: Hale / Dr: Okafor / Today: rest", the visitor's chair, the monitor, the bed along the right with its pillow at the right end. Striped window light on the floor at left. | In the bed / beside it: `slightright`. Visitor's chair: xalign 0.45. Staff at the door: `slightleft`. |
| `bg ward door` | The original ward (bed left, monitor, barred window right), filmed from the corridor through the open door. | `center`; good for staff talking about Aron where he can't hear. |
| `bg ward night reverse` | `bg ward reverse` at night: blue dark, the monitor and the door's window glowing. | as ward reverse |
| `bg office reverse` | The bright office seen from the glass wall: a doorway to a bright room at left, a low white sideboard (radio, calculator, vase) under seven coloured principle cards, the table with the orange model world and its pendant lamp now on the right. Daylight from the glass wall behind floods the floor at left. | Presenting at the table: `slightright`. The audience side / listeners: `slightleft`. |
| `bg street reverse` | From across the road, looking back: the other row of houses, including the cafe's blue window and THE SAME CAFE sign (left), the same wire with the same three birds, evenly spaced, now on the far side at the right, the road and a sidewalk curb in front. | On the sidewalk: any position; `center` default. |
| `bg street rain reverse` / `bg street dusk reverse` | the same in rain / at dusk (match `bg street rain` / `bg street dusk`). | as street reverse |
| `bg command reverse` | Angel ops seen from the wall of worlds: three tiers of winged operators at desks, the great arched doors behind them, the commander's dais front and centre. The screens' colours and the red alarm glow wash over the floor. | Seraphiel on the dais: `center`. Pim/Dross or other visitors: `slightleft` / `slightright`. |
| `bg clinic reverse` | Dr. Okafor's room seen from the poster wall: her desk under a window at left (her chair, notes), the patient's blue armchair in the middle with tissues on a side table, the plant, the door with her nameplate and a coat rack at right. | Okafor at her desk: `slightleft`. Aron in the armchair: xalign 0.55 or `slightright`. |

The existing alternate angles still apply: `bg kitchen table`, `pov cup`,
`bg bedroom door`, `pov ceiling`, `bg ward window`, `bg corridor`,
`bg cafe window`, `bg rooftop edge`, `pov sky`.

## 3. Stars that differ every time

These scenes have a procedural star layer on the 3DS: every time the scene is
shown, the stars are scattered and twinkle differently (Ren'Py on a PC shows
a baked sky). Most of them also keep a faint baked star layer behind for depth.

| scene | stars |
|---|---|
| `bg rooftop`, `pov sky` | 110 twinkling stars over the city sky |
| `bg rooftop dawn` | 35, fading out |
| `bg park night` | 80 above the hills (new: the park now has a starry sky) |
| `bg earth` | 170 around the planet |
| `bg staircase` | 90 above the dream sea |
| `bg lighthouse` | 110 |
| `bg bridge` | 70 |
| `bg watch` | 16 inside the round attic window |

When Aron looks up at the stars, use `scene pov sky` or `scene bg rooftop`
with `camera at est_stars`. Each visit's sky is a little different.

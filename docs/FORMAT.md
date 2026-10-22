# vn3ds file formats

All integers are little-endian. `str` means a `u32` index into the string
table; `0xFFFFFFFF` (written `NONE` below) means "no string".

## Game package layout (on the SD card)

```
sdmc:/3ds/vn3ds/games/<game-id>/
    game.bin          script bytecode + tables (this document)
    pk/H.pak          pack files holding everything below (see "Pack files")
    img/H.ctex        textures, pre-tiled for the PICA200
    img/H.cvh         videos (Ren'Py Movie() images), H.264 for the New 3DS's decoder
    img/H.ctex        ... and next to each .cvh its first frame (the "poster")
    img/H.cvid        videos in the older tiled format (--video-codec cvid)
    snd/H.ogg         Ogg Opus or Ogg Vorbis audio
    port-report.txt   what vn3ds-port skipped or approximated
    files.crc         written by the Wi-Fi receiver: size and CRC-32 of every file sent
```
`H` is 16 hex digits of the SHA-1 of the file's contents, so a rebuild keeps
the name of everything that didn't change, and an update (over Wi-Fi or to
an SD card) only copies what did. The paths in `RES` are these names.

### Pack files

By default (`vnpack --no-packs` turns it off) the files under `img/` and
`snd/` are not stored loose but inside a few pack files in `pk/`, and the
`PACK` section of game.bin says where each one is. A 3DS needs a few hundred
milliseconds to open a file in a folder of a thousand (its SD card's FAT
folders are searched entry by entry), while a seek inside a file that is
already open is free; the engine opens every pack once when the game loads
(`engine/source/vfs.c`) and reads all pictures, sounds and videos from them,
from any thread. Paths that the `PACK` table doesn't name are still read as
loose files, so games packed before pack files existed load unchanged.

A pack file is a 16-byte header, then the files back to back:
```
char magic[4] = "VNPK"
u32  version  = 1
u32  count               files in this pack
u32  reserved
...file data (offsets and sizes are in game.bin's PACK section)
```
Its name `pk/H.pak` is the content hash of the whole pack. vnpack
(`tools/vnpack/packs.py`) groups files by class (sounds, pictures, videos
with their posters), orders each class by first use in the script, and cuts
packs where the content decides: a file ends its pack with a chance
proportional to its size (decided by its own hash), once the pack holds a
quarter of the target size (`--pack-mb`, default 8 MB), and a pack never
grows past twice the target. Changing, adding or removing one file therefore
changes its own pack and seldom a neighbour (on Eternum's Wi-Fi edition, 37
packs: 1.08 packs on average, at most 2), and the receiver skips every pack
it already has by name.

## game.bin

```
char  magic[4]  = "VN3D"
u32   version   = 1
u32   nsections
{ char id[4]; u32 offset; u32 size; } sections[nsections]
```

Sections may appear in any order. Unknown sections are ignored.

### `STR ` string table
```
u32 count
u32 offset[count]      byte offset into the blob that follows
...blob of NUL-terminated UTF-8 strings
```

### `META`
```
str   title
str   version
u16   game_w, game_h       Ren'Py virtual resolution (e.g. 1280x720)
f32   scale                virtual px -> 3DS px
f32   view_x, view_y       top-left of the virtual screen on the 400x240 top screen
f32   view_w, view_h       size of the virtual screen in 3DS px
u32   init_addr            code address of "new game" (init code, then jump to start)
u32   nvars                number of script variables
f32   depth_bg             default depth of full-screen images (positive = behind screen)
f32   depth_sprite         default depth of sprites
f32   depth_ui             depth of the textbox / UI (negative = in front of screen)
f32   max_shift            per-eye pixel shift for depth 1.0 at full slider
i32   title_image          index into IMGS for the title background, -1 if none
i32   title_music          RES index of the title screen's music (config.main_menu_music),
                           looped; -1 if none (absent in older game.bin: none)
```

### `VARS`
```
u32 count
str name[count]           variable index -> name (used by save files)
```

### `RES ` resources
```
u32 count
str path[count]           path relative to the game folder ("img/0003.ctex")
```

### `IMGS` image definitions
```
u32 count
{ str  name            full Ren'Py image name, e.g. "eileen happy"
  i32  res             RES index of the texture, -1 for a solid colour
  u32  color           RGBA for solids
  f32  w, h            logical size in 3DS px
  u32  flags           1 = solid, 2 = full screen, 4 = video (res is a .cvh or .cvid),
                       8 = stereo pair (the .ctex holds the left and right eye's views
                       side by side; w, h are one view's size; vnpack --scenes-3d)
  f32  depth           NaN = use defaults
} [count]
```

### `CHRS` characters
```
u32 count
{ str name              NONE = narrator (no name box)
  str image_tag         NONE if the character has no image
  u32 name_color        RGBA
  u32 text_color        RGBA
  str what_prefix, what_suffix
  u8  kind              0 = adv, 1 = nvl, 2 = centered
  u8  pad[3]
} [count]
```
Character 0 is always the narrator, character 1 is `centered`.

### `TRAN` transitions
```
u32 count
{ u8 type; u8 warper; u8 dir; u8 pad; f32 a, b, c; u32 color } [count]
```
| type | meaning | a, b, c |
|---|---|---|
| 1 DISSOLVE | cross-fade | duration |
| 2 FADE | to colour and back | out, hold, in |
| 3 MOVE | slide moved images to new spots | duration |
| 4 MOVEIN | new images enter from `dir` | duration |
| 5 MOVEOUT | removed images leave to `dir` | duration |
| 6 PUNCH | shake screen; `dir` 0 = vertical, 1 = horizontal | duration |

`dir`: 0 left, 1 right, 2 top, 3 bottom. `warper`: see ATL.

### `ATL ` transform programs
```
u32 count
u32 offset[count]                   relative to the start of the program data
program: u16 nsteps; step[nsteps]
step:    u8 kind; u8 warper; u8 nprops; u8 pad; f32 dur; u16 target; u16 count;
         { u8 prop; u8 abs; u16 pad; f32 value } [nprops]
```
Step kinds: 0 SET (apply props instantly), 1 INTERP (interpolate props
over `dur`), 2 PAUSE (`dur` seconds), 3 REPEAT (go back to step `target`;
`count` 0 = forever).

Warpers: 0 linear, 1 ease, 2 easein, 3 easeout.

Props: 0 xpos, 1 ypos, 2 xanchor, 3 yanchor, 4 xoffset, 5 yoffset,
6 xzoom, 7 yzoom, 8 zoom, 9 alpha, 10 rotate, 11 zpos, 12 xrotate, 13 yrotate
(the last two only matter for the camera). The `camera` statement compiles to
SHOW/SCENE operands with spec and tag `@camera`; its programs drive the
stage's camera instead of a sprite.
`abs` = 1 means the value is in virtual pixels (Ren'Py `int`), otherwise a
fraction (Ren'Py `float`) for positions/anchors.

### Optional sections

Packages without these play as plain Ren'Py games; the engine checks for
each one.

#### `LAYR` layered images
An image drawn as several planes at their own depths, for stereoscopic
scenes. Each layer is placed inside the image's logical box.
```
u32 count
{ u32 image                IMGS index
  u32 nlayers              1..63
  { i32 res                RES index of the layer's texture
    f32 depth              stereo depth (same scale as META depths)
    f32 x, y, w, h         box inside the image, in its logical px (IMGS w, h)
    u32 anim               0 none, 1 sway, 2 pulse, 3 breathe, 4 fall, 5 rise,
                           6 stars (a = count, b = largest size; picture unused),
                           7 patch (see below),
                           8 video (res is a looping .cvh or .cvid clip,
                           drawn in the box; see "Video layers")
    f32 a, b               sway: x/y amplitude in logical px;
                           pulse: minimum alpha; breathe: scale growth;
                           fall/rise: travel distance per loop in logical px
    f32 period             seconds per cycle
  } [nlayers]              40 bytes each
} [count]
```
The renderer also scales each layer's camera drift by
`1 / (1 + 0.55 * max(depth, -0.8))`, so distant planes move less.

**Video layers** (`anim` 8): a vn3ds.json layer whose `file` is a movie
(`{"file": "loops/x.mp4", "depth": 1.2, "box": [x, y, w, h], "stereo": true,
"kbps": 300}`; `box` in the picture's px, default all of it). vnpack codes it
like a movie (.cvh with its poster beside it; .cvid with `--video-codec
cvid`; with `--no-video`, its first frame as an ordinary layer, anim 0) at
`kbps` (default 200 for the whole picture, less for a smaller box by area, at least 50), looping. `stereo`: the movie is a left | right pair
side by side, rendered (not synthesised), and becomes a stereo .cvh with a
median disparity of 0. The engine draws the clip's current frame in the box
like any layer (depth, parallax, camera); a stereo clip gives each eye its
own view on top of the layer's shift (its relief adds to the layer's
depth), and plays flat below the slider's `STEREO_MIN`. One clip decodes at
a time, as for movies; elsewhere (Old 3DS, the desktop build) the layer
shows its poster. A `layers` entry named `gui/main_menu` is the title
screen's picture (the image `__title`) as planes, in place of
`gui/main_menu.png`.

**Patched pictures** (`vnpack --cg-patches`): a CG variant that differs from
a picture stored shortly before it only in one region is written as two
layers: layer 0 is that earlier picture (its `res` is also the IMGS entry's
`res`, box 0, 0, w, h), layer 1 (`anim` 7) an opaque JPEG `.ctex` of the
changed rectangle, with `a`, `b` its top-left corner in texels of layer 0
(multiples of 16, so its edges fall on the JPEG block grid). Both textures
must be JPEG `.ctex` files of the same format. The engine does not draw these as layers: when it
loads the image it decodes the earlier picture and decodes the patch into
it, and from then on the image is an ordinary one-texture image (same depth,
transforms, transitions and stereo shift as any other). Engines that predate
this draw the patch as a second layer over the first.

#### `LABL` labels
```
u32 count
{ str name; u32 addr; } [count]     code address of each Ren'Py label
```
Used by the desktop test build's `--label`, by autoplay and by JMP_NAME /
CALL_NAME (`jump expression` with a computed label).

#### `CAM ` camera drift
```
f32 drift      maximum sway in 3DS px (0 = off)
f32 period     seconds per cycle
f32 zoom       maximum extra zoom (e.g. 0.015 = 1.5 %)
```

#### `MINI` minigames
```
u32 count;  str id[count]      ids passed to vn3ds_minigame() (enables the Minigames menu)
```

#### `AUDN` named audio
```
u32 count;  { str name; i32 res; } [count]   e.g. "minigame/tower_1" -> RES index
```
Everything in `game/audio/minigame/` is packed and listed here; minigames
look up their music and sounds by name.
Ported minigames' sounds are listed as `minigame/@<entry>_<name>` (names
starting `loop_` are streamed in a loop, the others decoded into memory).

#### `PORT` ported minigames
```
u32 count
{ str mechanic             native mechanic: "lockpick", "swing_timing", "instrument", "captions"
  u32 n
  { str key; str value } [n]   parameters, image names, layout (keys may repeat)
} [count]
```
Custom minigame screens of a ported game, rebuilt from vnpack's adapters
(`tools/vnpack/ported.py` lists each mechanic's keys). The script starts entry
`i` with OP_MINIGAME on the string `"@i"`; the game sets the story's variables
itself and its score is discarded. These never appear in the Minigames menu.

#### `PYSC` the game's own screens and Python (optional)
```
utf-8 Python source (no terminator; the section's size is its length)
```
The screen runtime (`tools/vnpack/vn3ds_rt.py`) followed by the game's
program (`tools/vnpack/pyscreens.py`): its image and audio tables, then
`_load_chunks([(where, source), ...])`, every top-level statement of the
game's init python, defines, defaults, styles and translated screens as one
chunk. The engine (`engine/source/pyscreen.c`) runs the whole source in
pocketpy as module `vn3ds_rt`, then each chunk with its own `py_exec` (a
chunk that fails is reported and skipped), then `_finish_load()`. PORT
entries of mechanic `pyscreen` start it: `screen` + `args` (call screen) or
`mode=overlay` (the touch-screen button for shown screens). The story keeps
shown screens in the dict variable `_vn3ds_screens` (screen -> its
arguments' source) and a screen's Jump in `_vn3ds_jump`.

#### `MUSM` music tempo grids (optional)
```
u32 count;  { i32 res; f32 bpm; u8 beats_per_bar; u8 phrase_bars; u16 bars; } [count]
```
From vn3ds.json `"music"`. `bars` is the length of one loop of the file in
bars (0 = unknown; the grid is then `bpm` alone). A change of music waits
for the end of the current track's loop or its next phrase boundary (at
most 8 s), then splices in the new track on the downbeat; tracks without a
grid crossfade on the beat. Several RES entries may share a file.

#### `PACK` pack files (optional)
```
u32 npacks
{ u16 len; char path[len] } [npacks]     e.g. "pk/0123456789abcdef.pak"
u32 count
{ u16 pack; u16 len; u32 offset; u32 size; char path[len] } [count]
```
Strings are inline (not in `STR `), UTF-8, not NUL-terminated. Each entry
maps a path relative to the game folder (a `RES` path, or a video's poster
beside it) to `size` bytes at `offset` in pack `pack`. See "Pack files".
After an update the engine deletes files in `img/`, `snd/` and `pk/` that
game.bin no longer names; a packed game names only its packs.

#### `TALK` speaking attribute
```
str attribute    Ren'Py's config.speaking_attribute (e.g. "talk")
```
While a character's line is being typed out, the attribute is toggled on
their shown image so its mouth moves.

#### `VOX ` machine voices
```
u32 count;  i32 res[count]     syllable bank (.ogg resources), at most 32
f32 volume                     syllable volume
f32 duck                       music volume while someone speaks (0..1)
u32 nchars; f32 pitch[nchars]  semitones per CHRS entry (0 = unpitched)
```
One syllable is played for every vowel group as the text types out, with
the pitch contour following the punctuation.

## Bytecode (`CODE`)

The VM has a value stack (none / bool / number / string), a call stack and
`nvars` variable slots. Operands follow the opcode byte.

| op | name | operands | effect |
|---|---|---|---|
| 0x00 | NOP | | |
| 0x01 | END | | game over, back to title |
| 0x02 | JMP | u32 addr | |
| 0x03 | JZ | u32 addr | pop, jump if falsy |
| 0x04 | JNZ | u32 addr | pop, jump if truthy |
| 0x05 | CALL | u32 addr | push return address |
| 0x06 | RET | | pop return address; END if empty |
| 0x07 | POP | | |
| 0x08 | DUP | | |
| 0x09 | JMP_NAME | | pop a label name, jump there (`jump expression`; unknown: go on) |
| 0x0A | CALL_NAME | | the same as a call (`call expression`, `renpy.call(x)`) |
| 0x10 | PUSH_NUM | f64 | |
| 0x11 | PUSH_STR | str | |
| 0x12 | PUSH_NONE | | |
| 0x13 | PUSH_TRUE | | |
| 0x14 | PUSH_FALSE | | |
| 0x15 | LOAD | u32 var | |
| 0x16 | STORE | u32 var | pop into var |
| 0x20..0x26 | ADD SUB MUL DIV FLOORDIV MOD POW | | binary |
| 0x27..0x28 | NEG NOT | | unary |
| 0x2A..0x2F | EQ NE LT LE GT GE | | compare |
| 0x30 | CALLF | u8 func, u8 nargs | builtin call (see below) |
| 0x31 | IN | | `a in b` for strings |
| 0x40 | SAY | i32 char, str who, str what, u8 flags | interaction; flags: 1 extend, 2 no-wait |
| 0x41 | MENU_BEGIN | | starts a menu (save point) |
| 0x42 | MENU_ITEM | str text, u32 addr | pop condition; add choice if truthy |
| 0x43 | MENU | i32 char, str who, str caption | interaction; jumps to choice, falls through if none |
| 0x44 | PAUSE | u8 has_time | pop seconds if has_time; interaction |
| 0x45 | SCENE | str spec, showargs | clear layer, then show spec (NONE = clear only) |
| 0x46 | SHOW | str spec, showargs | |
| 0x47 | HIDE | str tag | |
| 0x48 | WITH | i32 transition | -1 = `with None` |
| 0x49 | SHOW_ATTR | str spec | re-show only if the tag is on screen (say attributes) |
| 0x50 | PLAY | u8 channel, i32 res, u8 flags, f32 fadein, f32 fadeout | flags: 1 loop, 2 queue, 4 if_changed |
| 0x51 | STOP | u8 channel, f32 fadeout | |
| 0x52 | WINDOW | u8 mode | 0 auto, 1 show, 2 hide |
| 0x53 | MINIGAME | (pops id string) | runs a native minigame; its 0-100 score is pushed when it ends |

`showargs` = `str as_tag, i32 zorder (INT32_MIN = keep), str behind, u8 natl, i32 atl[natl]`.

Channels: 0 music, 1 sound, 2 voice.

Builtins (`CALLF`): 0 randint(a,b), 1 random(), 2 len(x), 3 str(x), 4 int(x),
5 float(x), 6 abs(x), 7 min(a,b...), 8 max(a,b...), 9 round(x), 10 bool(x),
11 s[i], 12 s[a:b], 13-17 upper/lower/title/strip/capitalize,
18 has(c, k), 19 add(c, k), 20 discard(c, k), 21 get(c, k, default), 22 set(c, k, v),
23 len(c) on a story set or dict `c`, 24 getattr(store, name), 25 setattr(store, name, v).

A story set or dict (`default seen = set()`, `default last = {}`) is an
ordinary string variable: one entry per key, `key 0x1F value 0x1E`, the
value's first byte its type (`n` number, `s` text, `b` bool, `-` None; a
set's entries are `b1`). The empty collection is `""`. Builtins 19, 20 and
22 return the new string, which the script stores back.

## .ctex texture

```
char magic[4] = "CTEX"
u16  version = 1
u16  format          0 = RGBA8 (bytes A,B,G,R), 1 = RGB8 (bytes B,G,R), 2 = RGB565
u16  tex_w, tex_h    power of two, 8..1024
u16  img_w, img_h    pixel content in the top-left of the image
f32  logical_w, logical_h   size to draw at, in 3DS px
u32  flags           1 = zlib-compressed payload, 2 = JPEG payload (see below)
u32  raw_size        payload size after decompression (texture bytes for JPEG)
u32  stored_size     bytes that follow the 36-byte header
```

The payload is already in the PICA200's native layout, the same one tex3ds
writes: 8x8 tiles in row-major order starting from the image's top-left,
Morton order inside a tile. The image's top row is the first row in memory
and is sampled at `v = 1.0`, so a sub-texture is `{left 0, top 1,
right img_w/tex_w, bottom 1 - img_h/tex_h}`. Texels right of and below the
image repeat its last column and row, so bilinear filtering at the edges
doesn't pull in anything else.

**JPEG payload** (`flags & 2`, written by `vnpack --jpeg Q` for opaque
images): `format` is 2 (RGB565), `raw_size` is `tex_w * tex_h * 2`, or with
`--jpeg-rgb8` `format` 1 (RGB8, decoded without RGB565's banding) and
`raw_size` `tex_w * tex_h * 3`; the
payload is a baseline JPEG of exactly `img_w` x `img_h` pixels (not padded,
not tiled). The engine decodes it with its own decoder
(`engine/source/jpeg.c`) straight into the tiled texture, filling the
padding as above. The decoder takes baseline and extended-sequential Huffman
JPEGs with 8-bit samples: grayscale or YCbCr, 4:4:4, 4:2:2, 4:2:0 or 4:4:0,
interleaved or not, with or without restart markers. Progressive,
arithmetic-coded, lossless, 12-bit and CMYK files fail to load. vnpack writes
4:2:0 below quality 90 and 4:4:4 from 90 up, with optimised Huffman tables;
with `--jpeg-encoder ffmpeg` the JPEG comes from ffmpeg's MJPEG encoder
(4:2:0, trellis quantisation, optimised Huffman tables, quantiser scale
`--jpeg-qscale`) fed with JFIF YCbCr that vnpack converts itself.
`--jpeg-posters` writes movie poster frames this way too.
Images with transparency keep the zlib path. Older engines can't load these
files.

## .cvh video

Ren'Py `Movie()` images, re-encoded by vnpack with libx264: Main profile,
level 3.0, no B-frames, one slice per frame, an IDR frame at least every 4
seconds (and at scene cuts), two-pass at `--video-kbps`. The size is the
clip's on-screen size rounded to multiples of 16 (432x240 for 16:9 in the
default layout), the frame rate the clip's own, capped by `--video-fps`
(default 30).
```
char magic[4] = "CVH1"
u16  version         1
u16  codec           1 = H.264, Annex B
u16  w, h            coded size, multiples of 16
u16  tex_w, tex_h    power of two textures that hold a frame
f32  logical_w, logical_h
f32  fps
u32  nframes
u32  flags           1 = loop, 2 = stereo side by side (see below)
u32  params_offset   SPS then PPS, each with a 00 00 01 prefix
u32  params_size
u8   profile_idc, level_idc, max_ref_frames, reserved
u32  max_frame_size  largest frame, in bytes
u32  keyframes       number of IDR frames
f32  stereo_mid      stereo clips: the median disparity in coded px (else 0)
u32  reserved        (64 bytes so far)
{ u32 offset, size   the frame's NAL units, each with a 00 00 01 prefix
  u16 nal_count
  u16 flags          1 = IDR
} [nframes]
...SPS, PPS, then the frames in order
```
From `params_offset` to the end the file is a plain H.264 stream
(`ffmpeg -f h264` reads it). Frame 0 is an IDR frame. `img/NNNNN.ctex`
next to it holds the first frame as decoded (RGB565; half size when
`--video-kbps` is 400 or less), drawn wherever there's no hardware decoding.

**Stereo clips** (`flags & 2`, written by `vnpack --video-3d`): each coded
frame is the left eye's view and the right eye's view side by side, each
`w / 2` wide (864x240 for a 16:9 clip: 810 macroblocks, inside level 3.0
like every .cvh, and the same decoding work as a 432x480 frame); `tex_w`
is 1024. The left view is the movie itself, the right view is synthesised
from estimated depth (`tools/vnpack/stereo.py`). Disparity (the right view's
offset, positive = behind the screen) runs from about -2 to +6 coded px at
full 3D; `stereo_mid` is its median over the clip. The right half is coded
with a slightly higher quantiser (libx264 ROI), and the bitrate is 1.5 times
the 2D one. The poster `.ctex` is the left view's first frame.

The engine shows each eye its half while the clip plays, instead of the
image's depth shift. The views were made for full 3D; at other strengths `k`
(3D slider x the depth setting, 0..2) it moves the views by
`(1 - k) * stereo_mid / 2` each, towards each other, so the clip's median
plane goes to `k * stereo_mid` while its relief stays as encoded (a
stereo pair can't be re-rendered at another depth). Below `k = 0.3` the clip
plays flat: the left view, drawn at the image's depth like a 2D clip. Posters
(an Old 3DS, before the first frame, any decoder failure) are flat too.
Engines from before stereo clips show both views squeezed into one picture.

On a New 3DS the engine feeds each NAL unit to `mvdstdProcessVideoFrame`,
renders with `mvdstdRenderVideoFrame` into RGB565 in linear RAM, and the
GPU's transfer engine tiles it into one of two textures. Only one clip
decodes at a time (the most recently shown); others keep their last picture.
Loops restart at frame 0.

## .cvid video

Ren'Py `Movie()` images, re-encoded by vnpack (12 fps and 12 seconds by
default) into the same tiled layout as `.ctex`, so frames upload without
conversion.
```
char magic[4] = "CVID"
u16  version         1 or 2
u16  format          2 = RGB565
u16  tex_w, tex_h    power of two
u16  img_w, img_h
f32  logical_w, logical_h
f32  fps
u32  nframes
u32  flags           1 = loop
u32  reserved
u32  offset[nframes] byte offset of each frame's chunk in the file
u32  size[nframes]
...chunks, each zlib-compressed
```
- **Version 2** (written now): a chunk is a bitmap with one bit per 8x8 tile
  (`tex_w/8 * tex_h/8` bits, LSB first), followed by the 128 bytes of every
  tile whose bit is set. Frame 0 sets every bit. Tiles that changed by at most
  2 levels per channel are left out.
- **Version 1**: a chunk is the whole texture XORed with the previous frame.
  Frame 0 is XORed with black.

The engine decodes into a buffer and alternates between two textures. It
plays videos flat at the depth of the image, with the usual camera parallax.

## Save files

`sdmc:/3ds/vn3ds/saves/<game-id>/slotNN.sav`, written by the engine; see
`engine/source/save.c`. They carry a CRC of `game.bin` and are refused if the
game was repacked.

After the story step every save ends with an extension block, "VNX1" u32
flags u32 n, then n x {u16 len, image name, u16 len, tag, s32 zorder}: what
is on screen by name, so a computer can read a save without Sprite's layout.
Saves converted from Ren'Py (`tools/vnpack/vn3dssave.py`) have no sprites and
set flags: 1 the stage is built from the names, 2 a variable of type 0xFF
keeps the value the game's init code gives it, 4 the story step is unknown.

The Wi-Fi receiver also answers a save sync ("VN3S", `engine/source/savesync.c`,
`tools/vnpack/savesync.py`): it lists slots 0-30 of every game with their
size and time, then reads, writes (keeping the old file as `slotNN.sav.bak`)
or deletes the slots the computer asks for. Afterwards it keeps the
computer's address in `sdmc:/3ds/vn3ds/sync.cfg` and nudges it over UDP
("VN3N", port 5556) when vn3ds opens, after a save, when a game is closed and
on exit.

Next to them: `slot00.thm`, the resume save's snapshot of the top screen
("THM1", u16 width, u16 height, RGB565 pixels, as in `cover.thm`), and the
story timeline's points (`engine/source/story.c`): saves in slots 100-139
with 160x96 snapshots (`slot1NN.thm`), listed in `story.idx` ("STI1", u32
count, then per point u16 slot, u16 0, u32 script address, u32 story step,
u32 time, char preview[96]), in story order.

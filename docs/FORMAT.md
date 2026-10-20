# vn3ds file formats

All integers are little-endian. `str` means a `u32` index into the string
table; `0xFFFFFFFF` (written `NONE` below) means "no string".

## Game package layout (on the SD card)

```
sdmc:/3ds/vn3ds/games/<game-id>/
    game.bin          script bytecode + tables (this document)
    img/NNNN.ctex     textures, pre-tiled for the PICA200
    img/NNNNN.cvh     videos (Ren'Py Movie() images), H.264 for the New 3DS's decoder
    img/NNNNN.ctex    ... and next to each .cvh its first frame (the "poster")
    img/NNNNN.cvid    videos in the older tiled format (--video-codec cvid)
    snd/NNNN.ogg      Ogg Vorbis audio
    port-report.txt   what vn3ds-port skipped or approximated
```

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
  u32  flags           1 = solid, 2 = full screen, 4 = video (res is a .cvh or .cvid)
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
                           7 patch (see below)
    f32 a, b               sway: x/y amplitude in logical px;
                           pulse: minimum alpha; breathe: scale growth;
                           fall/rise: travel distance per loop in logical px
    f32 period             seconds per cycle
  } [nlayers]              40 bytes each
} [count]
```
The renderer also scales each layer's camera drift by
`1 / (1 + 0.55 * max(depth, -0.8))`, so distant planes move less.

**Patched pictures** (`vnpack --cg-patches`): a CG variant that differs from
a picture stored shortly before it only in one region is written as two
layers: layer 0 is that earlier picture (its `res` is also the IMGS entry's
`res`, box 0, 0, w, h), layer 1 (`anim` 7) an opaque JPEG `.ctex` of the
changed rectangle, with `a`, `b` its top-left corner in texels of layer 0
(multiples of 16, so its edges fall on the JPEG block grid). Both textures
must be JPEG `.ctex` files. The engine does not draw these as layers: when it
loads the image it decodes the earlier picture and decodes the patch into
it, and from then on the image is an ordinary one-texture image (same depth,
transforms, transitions and stereo shift as any other). Engines that predate
this draw the patch as a second layer over the first.

#### `LABL` labels
```
u32 count
{ str name; u32 addr; } [count]     code address of each Ren'Py label
```
Used by the desktop test build's `--label` and by autoplay.

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
5 float(x), 6 abs(x), 7 min(a,b...), 8 max(a,b...), 9 round(x), 10 bool(x).

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
images): `format` is 2 (RGB565), `raw_size` is `tex_w * tex_h * 2`, and the
payload is a baseline JPEG of exactly `img_w` x `img_h` pixels (not padded,
not tiled). The engine decodes it with its own decoder
(`engine/source/jpeg.c`) straight into the tiled RGB565 texture, filling the
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
u32  flags           1 = loop
u32  params_offset   SPS then PPS, each with a 00 00 01 prefix
u32  params_size
u8   profile_idc, level_idc, max_ref_frames, reserved
u32  max_frame_size  largest frame, in bytes
u32  keyframes       number of IDR frames
u32  reserved[2]     (64 bytes so far)
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

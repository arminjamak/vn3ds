"""vn3ds save files (sdmc:/3ds/vn3ds/saves/<id>/slotNN.sav), as written by
engine/source/save.c, read and written here for the Mac's save sync.

    s = read(data)           # dict: time, preview, pc, calls, vars, specs, music, ...
    data = write(...)        # a save vn3ds loads (see write's arguments)

Little-endian throughout:
  "VNSV" u32 version(2) u32 game_crc u32 time char preview[96]
  u32 resume_pc u32 ncalls u32 calls[ncalls]
  u32 nvars, per variable: u8 type (0 none, 1 bool, 2 number, 3 string,
      0xFF "the game's default"), then f64 for bool/number, u32 len + bytes
      for a string
  s32 last_char char last_text[1024]
  u32 nsprites u32 next_order Sprite[nsprites]      (raw structs)
  s32 music_res u8 loop u8 window_mode u8 has_camera Sprite camera
  u32 story_step
  "VNX1" u32 flags u32 n, n x {u16 len, image name, u16 len, tag, s32 zorder}
"""

import struct
import zlib

MAGIC = b"VNSV"
VERSION = 2
PREVIEW = 96
VM_TEXT = 1024
VM_CALLS = 64
# sizeof(Sprite) in engine/source/stage.h (the same on the 3DS and the
# desktop build: no pointers, 4-byte alignment). Reading finds it by
# itself; writing needs it (tests/test_savesync.py checks it).
SPRITE_SIZE = 752

VAL_NONE, VAL_BOOL, VAL_NUM, VAL_STR, VAL_DEFAULT = 0, 1, 2, 3, 0xFF
SAVEX_STAGE, SAVEX_DEFAULTS, SAVEX_NO_STEP = 1, 2, 4
NO_STEP = 0xFFFFFFFF


class SaveError(ValueError):
    pass


def game_crc(game_bin_path):
    with open(game_bin_path, "rb") as f:
        return zlib.crc32(f.read()) & 0xFFFFFFFF


def peek(data):
    """(time, preview) from a save's header, or None."""
    if len(data) < 16 + PREVIEW or data[:4] != MAGIC:
        return None
    t = struct.unpack_from("<I", data, 12)[0]
    return t, data[16:16 + PREVIEW].split(b"\0")[0].decode("utf-8", "replace")


def read(data):
    if data[:4] != MAGIC:
        raise SaveError("not a vn3ds save")
    version, crc, t = struct.unpack_from("<III", data, 4)
    if version != VERSION:
        raise SaveError(f"vn3ds save version {version} (expected {VERSION})")
    o = 16
    preview = data[o:o + PREVIEW].split(b"\0")[0].decode("utf-8", "replace")
    o += PREVIEW
    pc, ncalls = struct.unpack_from("<II", data, o)
    o += 8
    if ncalls > VM_CALLS:
        raise SaveError("damaged save (call stack)")
    calls = list(struct.unpack_from(f"<{ncalls}I", data, o))
    o += 4 * ncalls
    nvars = struct.unpack_from("<I", data, o)[0]
    o += 4
    values = []
    for _ in range(nvars):
        typ = data[o]
        o += 1
        if typ in (VAL_BOOL, VAL_NUM):
            v = struct.unpack_from("<d", data, o)[0]
            o += 8
            values.append(bool(v) if typ == VAL_BOOL else v)
        elif typ == VAL_STR:
            n = struct.unpack_from("<I", data, o)[0]
            o += 4
            values.append(data[o:o + n].decode("utf-8", "replace"))
            o += n
        elif typ == VAL_DEFAULT:
            values.append(Default)
        else:
            values.append(None)
    last_char = struct.unpack_from("<i", data, o)[0]
    o += 4
    last_text = data[o:o + VM_TEXT].split(b"\0")[0].decode("utf-8", "replace")
    o += VM_TEXT
    nspr, next_order = struct.unpack_from("<II", data, o)
    o += 8
    base = o
    # sizeof(Sprite) from where the extension block sits
    rest = len(data) - base
    sprite_size, ext_at = None, None
    for size in [SPRITE_SIZE] + list(range(200, 4000, 4)):
        at = base + (nspr + 1) * size + 4 + 3 + 4
        if at + 12 <= len(data) and data[at:at + 4] == b"VNX1":
            sprite_size, ext_at = size, at
            break
    out = dict(crc=crc, time=t, preview=preview, pc=pc, calls=calls, vars=values,
               last_char=last_char, last_text=last_text, nsprites=nspr,
               music=-1, loop=0, window=0, step=None, flags=0, specs=None)
    if sprite_size is None:   # (a save from before the extension block)
        if rest >= nspr * SPRITE_SIZE + 6:
            o = base + nspr * SPRITE_SIZE
            out["music"], out["loop"], out["window"] = struct.unpack_from("<iBB", data, o)
        return out
    o = base + nspr * sprite_size
    out["music"], out["loop"], out["window"] = struct.unpack_from("<iBB", data, o)
    out["step"] = struct.unpack_from("<I", data, ext_at - 4)[0]
    flags, n = struct.unpack_from("<II", data, ext_at + 4)
    o = ext_at + 12
    specs = []
    for _ in range(n):
        ln = struct.unpack_from("<H", data, o)[0]
        name = data[o + 2:o + 2 + ln].decode("utf-8", "replace")
        o += 2 + ln
        ln = struct.unpack_from("<H", data, o)[0]
        tag = data[o + 2:o + 2 + ln].decode("utf-8", "replace")
        o += 2 + ln
        z = struct.unpack_from("<i", data, o)[0]
        o += 4
        specs.append((name, tag, z))
    out.update(flags=flags, specs=specs, sprite_size=sprite_size)
    return out


class _Default:
    """A variable left at the value the game's init code gives it."""

    def __repr__(self):
        return "Default"


Default = _Default()


def _fixed(text, size):
    b = text.encode("utf-8")[:size - 1]
    # don't cut a UTF-8 sequence in half
    while b and (b[-1] & 0xC0) == 0x80:
        b = b[:-1]
    if b and b[-1] >= 0xC0:
        b = b[:-1]
    return b + b"\0" * (size - len(b))


def write(crc, time, preview, pc, calls, values, last_text="", last_char=0, music=-1,
          loop=True, window=0, specs=(), step=None):
    """A save vn3ds loads: `values` lines up with the game's variables
    (Default for the game's own default, None, bool, number or str); the
    stage is built on the 3DS from `specs` [(image name, tag, zorder)]."""
    if len(calls) > VM_CALLS:
        raise SaveError("too many calls")
    b = bytearray(MAGIC + struct.pack("<III", VERSION, crc, int(time) & 0xFFFFFFFF))
    b += _fixed(preview, PREVIEW)
    b += struct.pack("<II", pc, len(calls)) + struct.pack(f"<{len(calls)}I", *calls)
    b += struct.pack("<I", len(values))
    flags = SAVEX_STAGE | (SAVEX_NO_STEP if step is None else 0)
    for v in values:
        if v is Default:
            b += bytes([VAL_DEFAULT])
            flags |= SAVEX_DEFAULTS
        elif v is None:
            b += bytes([VAL_NONE])
        elif isinstance(v, bool):
            b += bytes([VAL_BOOL]) + struct.pack("<d", 1.0 if v else 0.0)
        elif isinstance(v, (int, float)):
            b += bytes([VAL_NUM]) + struct.pack("<d", float(v))
        else:
            s = str(v).encode("utf-8")
            b += bytes([VAL_STR]) + struct.pack("<I", len(s)) + s
    b += struct.pack("<i", last_char) + _fixed(last_text, VM_TEXT)
    b += struct.pack("<II", 0, 0)                     # no sprites: built from specs
    b += struct.pack("<iBBB", music, 1 if loop else 0, window, 0)
    b += bytes(SPRITE_SIZE)                           # the camera (unused)
    b += struct.pack("<I", NO_STEP if step is None else step)
    b += b"VNX1" + struct.pack("<II", flags, len(specs))
    for name, tag, z in specs:
        for s in (name, tag):
            e = s.encode("utf-8")[:255]
            b += struct.pack("<H", len(e)) + e
        b += struct.pack("<i", int(z))
    return bytes(b)

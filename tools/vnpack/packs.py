"""Pack files: a game's pictures, sounds and videos in a few big files.

A 3DS takes a few hundred milliseconds to open a file in a folder of a
thousand (the SD card's FAT directory is searched entry by entry), but
seeking inside a file that is already open costs nothing. So after vnpack has
written the game's files (img/, snd/), `make_packs` moves them into pack files
in pk/ and adds a PACK section to game.bin naming where each file now is; the
engine opens every pack once when the game loads (see engine/source/vfs.c and
docs/FORMAT.md).

Wi-Fi updates send only the packs that changed, so packs are cut to keep one
changed picture from resending everything:

- files are grouped by class (sounds, pictures, videos) and, within a class,
  ordered by their first use in the script (so a pack holds what a stretch of
  the story needs, and what's read together sits together on the card);
- a pack ends after a file whose content hash (its name) makes it a
  "boundary" (with a chance proportional to its size, so boundaries come
  every target size or so), once the pack holds at least a quarter of the
  target, or when it would grow past twice the target. The cut points
  depend on the files themselves, not on their positions, so changing or
  adding a file changes its own pack and at most a neighbour; the packs after
  it come out byte-identical (and are named by their contents, so the
  receiver already has them).
"""

import hashlib
import os
import re
import struct

PACK_MAGIC = b"VNPK"
PACK_HEADER = 16
TARGET = 8 << 20    # bytes; packs are mostly between TARGET/4 and 2 * TARGET

# op -> operand bytes (see FORMAT.md "Bytecode"); SCENE/SHOW have a variable tail
_FIXED = {0x02: 4, 0x03: 4, 0x04: 4, 0x05: 4, 0x10: 8, 0x11: 4, 0x15: 4, 0x16: 4,
          0x30: 2, 0x40: 13, 0x42: 8, 0x43: 12, 0x44: 1, 0x47: 4, 0x48: 4, 0x49: 4,
          0x50: 14, 0x51: 5, 0x52: 1}
_NOARGS = {0x00, 0x01, 0x06, 0x07, 0x08, 0x12, 0x13, 0x14, 0x31, 0x41, 0x53} | \
    set(range(0x20, 0x29)) | set(range(0x2A, 0x30))


def read_game(path):
    data = open(path, "rb").read()
    if data[:4] != b"VN3D":
        raise ValueError(f"{path} is not a vn3ds game.bin")
    _, n = struct.unpack_from("<II", data, 4)
    sections = []
    for i in range(n):
        tag = data[12 + i * 12:16 + i * 12]
        off, size = struct.unpack_from("<II", data, 16 + i * 12)
        sections.append((tag, data[off:off + size]))
    return sections


def write_game(path, sections):
    header = 12 + 12 * len(sections)
    out = bytearray(b"VN3D" + struct.pack("<II", 1, len(sections)))
    offset = header
    for tag, data in sections:
        out += tag + struct.pack("<II", offset, len(data))
        offset += (len(data) + 3) & ~3
    for tag, data in sections:
        out += data + b"\0" * (((len(data) + 3) & ~3) - len(data))
    tmp = path + ".tmp"
    with open(tmp, "wb") as f:
        f.write(out)
    os.replace(tmp, path)


def _strings(sec):
    (count,) = struct.unpack_from("<I", sec, 0)
    offs = struct.unpack_from(f"<{count}I", sec, 4)
    blob = sec[4 + 4 * count:]
    return [blob[o:blob.index(b"\0", o)].decode("utf-8", "replace") for o in offs]


def _natural(s):
    return [int(t) if i % 2 else t for i, t in enumerate(re.split(r"(\d+)", s))]


def first_use(sections):
    """RES indices in the order the script first uses them (a straight walk
    through the bytecode, which follows the script files), then the rest."""
    sec = dict(sections)
    strings = _strings(sec[b"STR "])

    def s(i):
        return strings[i] if i < len(strings) else None
    (nres,) = struct.unpack_from("<I", sec[b"RES "], 0)
    imgs = sec[b"IMGS"]
    (nimg,) = struct.unpack_from("<I", imgs, 0)
    img_res = []
    by_name, by_tag = {}, {}
    for i in range(nimg):
        name_i, res = struct.unpack_from("<Ii", imgs, 4 + 28 * i)
        name = s(name_i) or ""
        img_res.append([res] if res >= 0 else [])
        by_name[name] = i
        words = name.split()
        if words:
            by_tag.setdefault(words[0], []).append((i, set(words[1:])))
    lay = sec.get(b"LAYR")
    if lay:
        (n,) = struct.unpack_from("<I", lay, 0)
        p = 4
        for _ in range(n):
            img, nl = struct.unpack_from("<II", lay, p)
            p += 8
            for k in range(nl):
                (res,) = struct.unpack_from("<i", lay, p + 40 * k)
                if 0 <= img < nimg and res >= 0:
                    img_res[img].append(res)
            p += 40 * nl
    for lst in by_tag.values():
        lst.sort(key=lambda e: _natural(s(struct.unpack_from("<I", imgs, 4 + 28 * e[0])[0]) or ""))

    order, seen = [], set()

    def use(res):
        if 0 <= res < nres and res not in seen:
            seen.add(res)
            order.append(res)

    shown = set()

    def show(spec):
        if spec is None or spec in shown:
            return
        shown.add(spec)
        i = by_name.get(spec)
        if i is not None:
            for r in img_res[i]:
                use(r)
            return
        words = spec.split()
        if not words:
            return
        want = {w for w in words[1:] if not w.startswith("-")}
        for i, attrs in by_tag.get(words[0], ()):
            if want <= attrs:
                for r in img_res[i]:
                    use(r)

    code = sec[b"CODE"]
    pc = 0
    while pc < len(code):
        op = code[pc]
        pc += 1
        if op in (0x45, 0x46):   # SCENE, SHOW
            spec, _, _, _, natl = struct.unpack_from("<IIiIB", code, pc)
            pc += 17 + 4 * natl
            show(s(spec))
        elif op == 0x49:          # SHOW_ATTR
            show(s(struct.unpack_from("<I", code, pc)[0]))
            pc += 4
        elif op == 0x50:          # PLAY
            use(struct.unpack_from("<i", code, pc + 1)[0])
            pc += 14
        elif op == 0x11:          # PUSH_STR: renpy.show("name") and the like
            st = s(struct.unpack_from("<I", code, pc)[0])
            if st in by_name:
                show(st)
            pc += 4
        elif op in _FIXED:
            pc += _FIXED[op]
        elif op in _NOARGS:
            pass
        else:
            break   # an opcode this walk doesn't know: the rest keeps its order
    for i in range(nimg):   # pictures the walk never reached, by name
        for r in img_res[i]:
            use(r)
    for r in range(nres):
        use(r)
    return order, [s(i) for i in struct.unpack_from(f"<{nres}I", sec[b"RES "], 4)]


def music_resources(code):
    """RES indices the bytecode plays on the music channel (PLAY ch 0)."""
    out, pc = set(), 0
    while pc < len(code):
        op = code[pc]
        pc += 1
        if op in (0x45, 0x46):
            (natl,) = struct.unpack_from("<B", code, pc + 16)
            pc += 17 + 4 * natl
        elif op == 0x50:
            ch, res = struct.unpack_from("<Bi", code, pc)
            if ch == 0 and res >= 0:
                out.add(res)
            pc += 14
        elif op in _FIXED:
            pc += _FIXED[op]
        elif op in _NOARGS:
            pass
        else:
            break
    return out


def _class(rel):
    if rel.endswith((".cvh", ".cvid")):
        return "vid"
    if rel.startswith("snd/") or rel.endswith((".ogg", ".opus")):
        return "snd"
    return "img"


def _boundary(rel, size, span):
    """True with probability size / span, decided by the file itself: its
    name (content-named files: 16 hex digits of a hash of the content) or a
    hash of the name. Weighting by size puts about `span` bytes between
    boundaries whatever the files' sizes, so packs rarely hit the maximum
    (a forced cut is the one thing that can ripple into the next packs)."""
    base = rel.rsplit("/", 1)[-1]
    try:
        v = int(base[:8], 16) if len(base) > 16 and base[16] == "." else None
    except ValueError:
        v = None
    if v is None:
        v = int.from_bytes(hashlib.sha1(rel.encode()).digest()[:4], "little")
    return v / 2.0 ** 32 < size / float(span)


def plan(files, target=TARGET):
    """files: [(rel, size, class)] in order (class "snd", "img" or "vid").
    Returns [[(rel, size), ...], ...]: the packs, per class, in
    content-defined chunks of mostly target/4 to 2 * target bytes.

    Measured on Eternum's Wi-Fi edition (14,354 files, 284 MiB, 37 packs at
    8 MiB): changing, adding or removing one file changes 1.08 packs on
    average and never more than 2 (12 MiB resent on average)."""
    classes = {}
    for rel, size, cls in files:
        classes.setdefault(cls, []).append((rel, size))
    packs = []
    lo, hi = target // 4, target * 2
    for cls in ("snd", "img", "vid"):
        items = classes.get(cls, [])
        cur, size = [], 0
        for rel, sz in items:
            if cur and size + sz > hi:
                packs.append(cur)
                cur, size = [], 0
            cur.append((rel, sz))
            size += sz
            if size >= lo and _boundary(rel, sz, target - lo):
                packs.append(cur)
                cur, size = [], 0
        if cur:
            packs.append(cur)
    return packs


def make_packs(out_dir, target=TARGET, quiet=True):
    """Moves the game's loose files into pk/*.pak and records them in
    game.bin. Returns dict(packs=n, files=n, bytes=n)."""
    gb = os.path.join(out_dir, "game.bin")
    sections = [(t, d) for t, d in read_game(gb) if t != b"PACK"]
    order, res = first_use(sections)
    files, seen = [], set()

    def add(rel):
        if not rel or rel in seen:
            return
        full = os.path.join(out_dir, rel)
        if os.path.isfile(full):
            seen.add(rel)
            files.append((rel, os.path.getsize(full)))
    for r in order:
        rel = res[r]
        add(rel)
        if rel and rel.endswith(".cvh"):
            add(rel[:-4] + ".ctex")    # its poster, looked up beside it
    for sub in ("img", "snd"):         # anything else vnpack wrote
        d = os.path.join(out_dir, sub)
        if os.path.isdir(d):
            for fn in sorted(os.listdir(d)):
                if not fn.endswith((".part", ".tmp")):
                    add(f"{sub}/{fn}")
    # a video's poster goes with the video (it is read when the video opens)
    posters = {rel[:-4] + ".ctex" for rel, _ in files if rel.endswith(".cvh")}
    files = [(rel, sz, "vid" if rel in posters else _class(rel)) for rel, sz in files]
    groups = plan(files, target)
    if not groups:   # nothing to pack (a script-only build)
        write_game(gb, sections)
        for sub in ("pk", "img", "snd"):
            try:
                os.rmdir(os.path.join(out_dir, sub))
            except OSError:
                pass
        return dict(packs=0, files=0, bytes=0, names=[])

    pk = os.path.join(out_dir, "pk")
    os.makedirs(pk, exist_ok=True)
    for fn in os.listdir(pk):
        os.remove(os.path.join(pk, fn))
    names, entries, total = [], [], 0
    for group in groups:
        h = hashlib.sha1()
        offsets, at = [], PACK_HEADER
        for rel, sz in group:
            offsets.append(at)
            at += sz
        tmp = os.path.join(pk, "pack.tmp")
        with open(tmp, "wb") as f:
            head = PACK_MAGIC + struct.pack("<III", 1, len(group), 0)
            f.write(head)
            h.update(head)
            for rel, sz in group:
                with open(os.path.join(out_dir, rel), "rb") as src:
                    data = src.read()
                if len(data) != sz:
                    raise OSError(f"{rel} changed while packing")
                f.write(data)
                h.update(data)
        name = f"pk/{h.hexdigest()[:16]}.pak"
        os.replace(tmp, os.path.join(out_dir, name))
        for (rel, sz), off in zip(group, offsets):
            entries.append((len(names), rel, off, sz))
        names.append(name)
        total += at
    sec = bytearray(struct.pack("<I", len(names)))
    for n in names:
        b = n.encode()
        sec += struct.pack("<H", len(b)) + b
    sec += struct.pack("<I", len(entries))
    for pack, rel, off, sz in entries:
        b = rel.encode()
        sec += struct.pack("<HHII", pack, len(b), off, sz) + b
    write_game(gb, sections + [(b"PACK", bytes(sec))])
    for _, rel, _, _ in entries:
        os.remove(os.path.join(out_dir, rel))
    for sub in ("img", "snd"):
        try:
            os.rmdir(os.path.join(out_dir, sub))
        except OSError:
            pass
    if not quiet:
        print(f"  packs: {len(entries)} files in {len(names)} packs "
              f"({total / (1 << 20):.1f} MiB)", flush=True)
    return dict(packs=len(names), files=len(entries), bytes=total, names=names)


def unpack(out_dir):
    """The reverse (for tools and tests): loose files again, no PACK section."""
    gb = os.path.join(out_dir, "game.bin")
    sections = read_game(gb)
    sec = dict(sections).get(b"PACK")
    if not sec:
        return 0
    (np_,) = struct.unpack_from("<I", sec, 0)
    p, names = 4, []
    for _ in range(np_):
        (n,) = struct.unpack_from("<H", sec, p)
        names.append(sec[p + 2:p + 2 + n].decode())
        p += 2 + n
    (ne,) = struct.unpack_from("<I", sec, p)
    p += 4
    blobs = {}
    for _ in range(ne):
        pack, n, off, sz = struct.unpack_from("<HHII", sec, p)
        rel = sec[p + 12:p + 12 + n].decode()
        p += 12 + n
        if names[pack] not in blobs:
            with open(os.path.join(out_dir, names[pack]), "rb") as f:
                blobs[names[pack]] = f.read()
        full = os.path.join(out_dir, rel)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "wb") as f:
            f.write(blobs[names[pack]][off:off + sz])
    write_game(gb, [(t, d) for t, d in sections if t != b"PACK"])
    for n in names:
        os.remove(os.path.join(out_dir, n))
    try:
        os.rmdir(os.path.join(out_dir, "pk"))
    except OSError:
        pass
    return ne

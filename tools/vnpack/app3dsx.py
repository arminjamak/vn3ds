"""A ported game as one Homebrew Launcher app: vn3ds.3dsx with the game in its romfs.

    vn3ds-port GAME --app          ->  build/<id>.3dsx

The .3dsx format keeps code first, then (in its extended header) the
offsets of the SMDH (the icon, title and author the Homebrew Launcher
shows) and of a romfs, a read-only file system appended to the file. So a
prebuilt engine becomes a standalone app with plain Python, no devkitPro:
copy the code, write a new SMDH, append a romfs holding games/<id>/. This is
what `3dsxtool vn3ds.elf out.3dsx --smdh=... --romfs=dir` writes.

The engine sees the romfs on start (engine/source/3ds/main_3ds.c,
appfs_open), opens romfs:/games/<id>/ straight away instead of its library
and keeps that game's saves and settings in sdmc:/3ds/<id>/. The romfs
layout is libctru's (3ds/romfs.h): the engine reads loose files through
libctru's romfs:/ device and the pack files straight from the .3dsx, so
the entries must be where libctru's hash lookup and its directory walk
expect them.
"""

import os
import shutil
import struct

UNUSED = 0xFFFFFFFF
ROMFS_HEADER = 0x28
SMDH_SIZE = 0x36C0
ALIGN = 0x10   # file data, as 3dsxtool aligns it


# --------------------------------------------------------------------------
# romfs
# --------------------------------------------------------------------------

def _utf16(name):
    return name.encode("utf-16-le")


def _hash(parent, name, total):
    """libctru's romfs calcHash (parent: the parent folder's table offset)."""
    h = parent ^ 123456789
    for i in range(0, len(name), 2):
        c = name[i] | (name[i + 1] << 8)
        h = ((h >> 5) | (h << 27)) & 0xFFFFFFFF
        h ^= c
    return h % total


def _table_len(count):
    """Hash table buckets for count entries (3dstools' romfs builder)."""
    if count < 3:
        return 3
    if count < 19:
        return count | 1
    while any(count % p == 0 for p in (2, 3, 5, 7, 11, 13, 17)):
        count += 1
    return count


def _pad4(b):
    return b + b"\0" * (-len(b) % 4)


class _Dir:
    def __init__(self, name, parent):
        self.name, self.parent = name, parent
        self.dirs, self.files = [], []
        self.off = 0


def _tree(files):
    """files: [(path in the romfs, source file)] -> the root _Dir, folders
    and files sorted by name."""
    root = _Dir("", None)
    index = {"": root}
    for rel, src in sorted(files):
        parts = rel.replace("\\", "/").strip("/").split("/")
        d, path = root, ""
        for p in parts[:-1]:
            path = f"{path}/{p}"
            if path not in index:
                index[path] = _Dir(p, d)
                d.dirs.append(index[path])
            d = index[path]
        d.files.append([parts[-1], src, 0, 0, 0])   # name, source, entry offset, data offset, size

    def order(d):   # each folder's folders and files by name (as engine/source/export.c)
        d.dirs.sort(key=lambda c: c.name.encode())
        d.files.sort(key=lambda f: f[0].encode())
        for c in d.dirs:
            order(c)
    order(root)
    return root


def build_romfs(files, out, progress=None):
    """Writes a romfs holding files ([(romfs path, source file)]) to the
    open binary file out, at its current position. progress(done, total)
    in bytes. Returns the romfs's size."""
    root = _tree(files)
    dirs, all_files = [], []

    def walk(d):          # folders depth first, the root at offset 0
        dirs.append(d)
        for c in d.dirs:
            walk(c)
    walk(root)
    off = 0
    for d in dirs:
        d.off = off
        off += 0x18 + len(_pad4(_utf16(d.name)))
    dir_table_size = off
    off = 0
    for d in dirs:
        for f in d.files:
            f[2] = off
            off += 0x20 + len(_pad4(_utf16(f[0])))
            all_files.append((d, f))
    file_table_size = off
    data = 0
    for _, f in all_files:
        f[4] = os.path.getsize(f[1])
        data += -data % ALIGN
        f[3] = data
        data += f[4]

    nd, nf = _table_len(len(dirs)), _table_len(len(all_files))
    dir_hash, file_hash = [UNUSED] * nd, [UNUSED] * nf
    dir_next, file_next = {}, {}
    for d in dirs:        # each bucket chains through the entries' nextHash
        parent = d.parent.off if d.parent else 0
        h = _hash(parent, _utf16(d.name), nd)
        dir_next[d.off] = dir_hash[h]
        dir_hash[h] = d.off
    for d, f in all_files:
        h = _hash(d.off, _utf16(f[0]), nf)
        file_next[f[2]] = file_hash[h]
        file_hash[h] = f[2]

    dir_table = bytearray()
    for d in dirs:
        name = _utf16(d.name)
        parent = d.parent.off if d.parent else 0
        sibling = UNUSED
        if d.parent:
            sibs = d.parent.dirs
            k = sibs.index(d)
            sibling = sibs[k + 1].off if k + 1 < len(sibs) else UNUSED
        dir_table += struct.pack("<6I", parent, sibling, d.dirs[0].off if d.dirs else UNUSED,
                                 d.files[0][2] if d.files else UNUSED, dir_next[d.off],
                                 len(name)) + _pad4(name)
    file_table = bytearray()
    for d, f in all_files:
        name = _utf16(f[0])
        k = d.files.index(f)
        sibling = d.files[k + 1][2] if k + 1 < len(d.files) else UNUSED
        file_table += struct.pack("<2I2Q2I", d.off, sibling, f[3], f[4], file_next[f[2]],
                                  len(name)) + _pad4(name)
    assert len(dir_table) == dir_table_size and len(file_table) == file_table_size

    dh_off = ROMFS_HEADER
    dt_off = dh_off + nd * 4
    fh_off = dt_off + dir_table_size
    ft_off = fh_off + nf * 4
    data_off = ft_off + file_table_size
    data_off += -data_off % ALIGN
    head = struct.pack("<10I", ROMFS_HEADER, dh_off, nd * 4, dt_off, dir_table_size,
                       fh_off, nf * 4, ft_off, file_table_size, data_off)
    meta = (head + struct.pack(f"<{nd}I", *dir_hash) + dir_table +
            struct.pack(f"<{nf}I", *file_hash) + file_table)
    out.write(meta + b"\0" * (data_off - len(meta)))
    pos, done = 0, 0
    for _, f in all_files:
        out.write(b"\0" * (f[3] - pos))
        with open(f[1], "rb") as src:
            shutil.copyfileobj(src, out, 1 << 20)
        pos = f[3] + f[4]
        done += f[4]
        if progress:
            progress(done, data)
    return data_off + pos


def read_romfs(blob):
    """{path: (data offset in blob, size)} of a romfs image, looked up the
    way libctru does (hash table, then nextHash chain) - for tests."""
    h = struct.unpack_from("<10I", blob, 0)
    _, dh_off, dh_size, dt_off, _, fh_off, fh_size, ft_off, _, data_off = h
    nd, nf = dh_size // 4, fh_size // 4

    def dir_entry(off):
        p = dt_off + off
        parent, sib, cdir, cfile, nxt, nlen = struct.unpack_from("<6I", blob, p)
        return parent, sib, cdir, cfile, nxt, blob[p + 24:p + 24 + nlen]

    def file_entry(off):
        p = ft_off + off
        parent, sib, doff, dsize, nxt, nlen = struct.unpack_from("<2I2Q2I", blob, p)
        return parent, sib, doff, dsize, nxt, blob[p + 32:p + 32 + nlen]

    def lookup_dir(parent, name):
        off = struct.unpack_from("<I", blob, dh_off + 4 * _hash(parent, name, nd))[0]
        while off != UNUSED:
            e = dir_entry(off)
            if e[0] == parent and e[5] == name:
                return off
            off = e[4]
        return None

    def lookup_file(parent, name):
        off = struct.unpack_from("<I", blob, fh_off + 4 * _hash(parent, name, nf))[0]
        while off != UNUSED:
            e = file_entry(off)
            if e[0] == parent and e[5] == name:
                return e
            off = e[4]
        return None

    out = {}

    def walk(doff, prefix):
        e = dir_entry(doff)
        f = e[3]
        while f != UNUSED:
            fe = file_entry(f)
            name = fe[5].decode("utf-16-le")
            hit = lookup_file(doff, fe[5])   # the hash lookup must find it too
            assert hit and hit[2] == fe[2], f"{prefix}{name}: not in the file hash table"
            out[prefix + name] = (data_off + fe[2], fe[3])
            f = fe[1]
        c = e[2]
        while c != UNUSED:
            ce = dir_entry(c)
            assert lookup_dir(doff, ce[5]) == c, "a folder isn't in the folder hash table"
            walk(c, prefix + ce[5].decode("utf-16-le") + "/")
            c = ce[1]
    walk(0, "")
    return out


# --------------------------------------------------------------------------
# SMDH: the Homebrew Launcher's icon, title and author
# --------------------------------------------------------------------------

def _tile_order(size):
    """(x, y) of each pixel in the 3DS's tiled order: 8x8 tiles row by row,
    the pixels of a tile in Morton (Z) order."""
    order = []
    for ty in range(0, size, 8):
        for tx in range(0, size, 8):
            for i in range(64):
                x = (i & 1) | ((i >> 1) & 2) | ((i >> 2) & 4)
                y = ((i >> 1) & 1) | ((i >> 2) & 2) | ((i >> 3) & 4)
                order.append((tx + x, ty + y))
    return order


def _icon_bytes(img, size):
    from PIL import Image
    im = img.convert("RGBA").resize((size, size), Image.LANCZOS)
    bg = Image.new("RGBA", im.size, (0, 0, 0, 255))   # transparency over black
    px = Image.alpha_composite(bg, im).convert("RGB").load()
    out = bytearray()
    for x, y in _tile_order(size):
        r, g, b = px[x, y]
        out += struct.pack("<H", ((r * 31 + 127) // 255) << 11 |
                           ((g * 63 + 127) // 255) << 5 | ((b * 31 + 127) // 255))
    return bytes(out)


def _text(s, chars):
    b = s.encode("utf-16-le")[:chars * 2 - 2]   # leave room for the terminator
    return b + b"\0" * (chars * 2 - len(b))


def make_smdh(title, description, author, icon, base=None):
    """An SMDH (0x36C0 bytes) with title, description and author in every
    language and icon (a PIL image, any size) as the 24x24 and 48x48 icons.
    base: an SMDH whose settings (region, ratings, flags) to keep."""
    smdh = bytearray(base[:SMDH_SIZE] if base and len(base) >= SMDH_SIZE and
                     base[:4] == b"SMDH" else b"\0" * SMDH_SIZE)
    if not base or base[:4] != b"SMDH":
        smdh[0:4] = b"SMDH"
        struct.pack_into("<I", smdh, 0x2018, 0x7FFFFFFF)   # every region
        struct.pack_into("<I", smdh, 0x2028, 0x1)          # visible
    entry = _text(title, 0x40) + _text(description, 0x80) + _text(author, 0x40)
    for lang in range(16):
        smdh[8 + lang * 0x200:8 + (lang + 1) * 0x200] = entry
    smdh[0x2040:0x2040 + 0x480] = _icon_bytes(icon, 24)
    smdh[0x24C0:0x24C0 + 0x1200] = _icon_bytes(icon, 48)
    return bytes(smdh)


def read_smdh(blob):
    """(title, description, author) of an SMDH's first language."""
    def s(a, n):
        return blob[a:a + n].decode("utf-16-le").split("\0")[0]
    return s(8, 0x80), s(0x88, 0x100), s(0x188, 0x80)


def smdh_icon(blob, size=48):
    """The large (or small) icon of an SMDH as a PIL image."""
    from PIL import Image
    off = 0x24C0 if size == 48 else 0x2040
    im = Image.new("RGB", (size, size))
    px = im.load()
    for i, (x, y) in enumerate(_tile_order(size)):
        v = struct.unpack_from("<H", blob, off + i * 2)[0]
        px[x, y] = ((v >> 11) * 255 // 31, ((v >> 5) & 63) * 255 // 63, (v & 31) * 255 // 31)
    return im


# --------------------------------------------------------------------------
# .3dsx
# --------------------------------------------------------------------------

def read_3dsx(path):
    """(code: bytes up to the SMDH / romfs, header fields dict) of a .3dsx."""
    with open(path, "rb") as f:
        head = f.read(0x2C)
        if head[:4] != b"3DSX":
            raise ValueError(f"{path} is not a .3dsx")
        hsize = struct.unpack_from("<H", head, 4)[0]
        smdh_off = smdh_size = fs_off = 0
        if hsize >= 0x2C:
            smdh_off, smdh_size, fs_off = struct.unpack_from("<3I", head, 0x20)
        end = os.path.getsize(path)
        cut = min(x for x in (smdh_off, fs_off, end) if x)   # the code and relocations
        f.seek(0)
        code = f.read(cut)
        smdh = b""
        if smdh_off and smdh_size:
            f.seek(smdh_off)
            smdh = f.read(smdh_size)
    return code, dict(header_size=hsize, smdh=smdh, fs_offset=fs_off)


def build_app(engine, out_path, game_dir, game_id, title, author, icon,
              description=None, progress=None):
    """Writes out_path: the engine .3dsx with game_dir as romfs:/games/<id>/
    and an SMDH for title, author and icon (a PIL image). Returns its size."""
    code, info = read_3dsx(engine)
    if info["header_size"] < 0x2C:
        raise ValueError(f"{engine} has no extended header (built without --smdh?)")
    files = []
    for root, dirs, names in os.walk(game_dir):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for n in names:
            if n.startswith(".") or n.endswith(".part") or n in ("port-report.txt", "savemap.json"):
                continue
            full = os.path.join(root, n)
            files.append((f"games/{game_id}/" + os.path.relpath(full, game_dir).replace(os.sep, "/"),
                          full))
    smdh = make_smdh(title, description or "A visual novel for vn3ds", author, icon,
                     base=info["smdh"])
    code = bytearray(code)
    smdh_off = len(code)
    fs_off = smdh_off + len(smdh)
    fs_off += -fs_off % 4
    struct.pack_into("<3I", code, 0x20, smdh_off, len(smdh), fs_off)
    tmp = out_path + ".part"
    with open(tmp, "wb") as f:
        f.write(code)
        f.write(smdh)
        f.write(b"\0" * (fs_off - smdh_off - len(smdh)))
        build_romfs(files, f, progress)
        size = f.tell()
    os.replace(tmp, out_path)
    return size

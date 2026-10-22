"""savemap.json: what the Mac needs to turn Ren'Py saves into vn3ds saves
and back, written next to game.bin when a game is ported (it stays on the
computer: the senders leave it out).

A Ren'Py save says where the story is by a statement's name: a label's name,
or (file, version, serial) for any other statement, a name that lives only in
the game's compiled .rpyc files. The .rpyc files give each name its file and
line; the compiler's line map gives each line its place in game.bin's code.

    {"version": 1, "id", "title", "crc" (of game.bin), "save_directory",
     "source" (the game's folder or .app),
     "vars": [names in game.bin's order],
     "statements": [[file, line, code start, code end], ...],
     "labels": {name: code address},
     "nodes": {name: [file, line, kind]}, "next": {call's name: name after it},
     "music": {file as the script plays it: resource index}}
"""

import io
import json
import os
import re
import struct
import zlib
import bisect

from . import renpysave

NAME = "savemap.json"
VERSION = 1

SAVE_DIR_RE = re.compile(r"""config\.save_directory\s*=\s*(?:u|r)?(["'])(.+?)\1""")


def norm_file(f):
    f = renpysave.text(f).replace("\\", "/")
    while f.startswith("./"):
        f = f[2:]
    if f.startswith("game/"):
        f = f[5:]
    return f


def save_directory(sources):
    """config.save_directory from the scripts' text (the last one set wins,
    as in Ren'Py's own init order more or less)."""
    found = None
    for src in sources:
        for m in SAVE_DIR_RE.finditer(src):
            found = m.group(2)
    return found


# --------------------------------------------------------------------------
# .rpyc files: statement names -> file and line
# --------------------------------------------------------------------------

def _rpyc_blob(raw):
    if not raw.startswith(b"RENPY RPC2"):
        return zlib.decompress(raw)
    pos, chunks = 10, {}
    while pos + 12 <= len(raw):
        slot, start, length = struct.unpack_from("<III", raw, pos)
        if slot == 0:
            break
        chunks[slot] = raw[start:start + length]
        pos += 12
    if 1 not in chunks:
        raise ValueError("no slot 1")
    return zlib.decompress(chunks[1])


def _is_node(o):
    return renpysave.is_stub(o) and type(o).__module__ == "renpy.ast"


def read_rpyc(raw, nodes, nexts):
    """Adds the statements of one .rpyc to nodes {name: [file, line, kind]}
    and nexts {call: following statement}."""
    data, stmts = renpysave._Unpickler(io.BytesIO(_rpyc_blob(raw)), encoding="bytes").load()
    seen = set()

    def visit_block(block):
        prev = None
        for n in block:
            if _is_node(n):
                if prev is not None and type(prev).__name__ == "Call":
                    nexts[renpysave.node_key(prev.get("name"))] = renpysave.node_key(n.get("name"))
                prev = n
            visit(n)

    def visit(o):
        if id(o) in seen:
            return
        seen.add(id(o))
        if _is_node(o):
            name = o.get("name")
            line = o.get("linenumber")
            fn = o.get("filename")
            if name is not None and line is not None and fn is not None:
                nodes.setdefault(renpysave.node_key(name),
                                 [norm_file(fn), int(line), type(o).__name__])
            for v in o.fields().values():
                visit(v)
        elif isinstance(o, list):
            if o and all(_is_node(x) for x in o):
                visit_block(o)
            else:
                for x in o:
                    visit(x)
        elif isinstance(o, tuple):
            for x in o:
                visit(x)
        elif isinstance(o, dict):
            for x in o.values():
                visit(x)

    visit(stmts if isinstance(stmts, list) else [stmts])


def build(comp, fs, out_dir, game_id, title, source, sources, warn=None):
    """Writes out_dir/savemap.json. `fs` is the packager's AssetFS (for the
    .rpyc files, loose or in archives); `sources` the scripts' text."""
    nodes, nexts, bad = {}, {}, 0
    for key in sorted(fs.keys()):
        if not key.endswith(".rpyc") or key.startswith(("renpy/", "tl/")):
            continue
        try:
            read_rpyc(fs.read(key), nodes, nexts)
        except Exception:   # an obfuscated or unusual .rpyc: its saves can't be placed
            bad += 1
    if bad and warn:
        warn(None, f"{bad} compiled scripts could not be read for save conversion")
    seen, statements = set(), []
    for fn, line, start, end in comp.linemap:
        k = (norm_file(fn), line)
        if k not in seen:
            seen.add(k)
            statements.append([k[0], line, start, end])
    statements.sort(key=lambda s: (s[0], s[1]))
    labels = {name: r.addr for name, r in comp.labels.items()
              if r.addr is not None and name in comp.defined_labels}
    m = dict(version=VERSION, id=game_id, title=title,
             crc=zlib.crc32(open(os.path.join(out_dir, "game.bin"), "rb").read()) & 0xFFFFFFFF,
             save_directory=save_directory(sources), source=source,
             vars=sorted(comp.vars, key=comp.vars.get), statements=statements,
             labels=labels, nodes=nodes, next=nexts, music=dict(comp.audio_res))
    with open(os.path.join(out_dir, NAME), "w", encoding="utf-8") as f:
        json.dump(m, f, separators=(",", ":"))
    return m


# --------------------------------------------------------------------------
# using it
# --------------------------------------------------------------------------

class SaveMap:
    def __init__(self, game_dir):
        self.game_dir = game_dir
        with open(os.path.join(game_dir, NAME), encoding="utf-8") as f:
            m = json.load(f)
        self.m = m
        self.id = m["id"]
        self.title = m.get("title") or m["id"]
        self.crc = m["crc"]
        self.vars = m["vars"]
        self.var_index = {n: i for i, n in enumerate(self.vars)}
        self.nodes = m["nodes"]
        self.next = m["next"]
        self.labels = m["labels"]
        self.music = m["music"]
        self.music_name = {v: k for k, v in self.music.items()}
        self.by_file = {}
        for fn, line, start, end in m["statements"]:
            self.by_file.setdefault(fn, []).append((line, start, end))
        for v in self.by_file.values():
            v.sort()
        # code address -> statement, innermost first
        spans = sorted(((start, end, fn, line) for fn, line, start, end in m["statements"]),
                       key=lambda s: (s[0], -(s[1] - s[0])))
        self.spans = spans
        self.span_starts = [s[0] for s in spans]
        self.lines = {}   # (file, line) -> [node names] (labels last)
        for name, (fn, line, kind) in self.nodes.items():
            self.lines.setdefault((fn, line), []).append((kind, name))
        # ported again since (the game.bin on the card is another one)
        bin_path = os.path.join(game_dir, "game.bin")
        self.stale = os.path.exists(bin_path) and \
            zlib.crc32(open(bin_path, "rb").read()) & 0xFFFFFFFF != self.crc

    @property
    def save_directory(self):
        return self.m.get("save_directory")

    @property
    def source(self):
        return self.m.get("source")

    # Ren'Py -> vn3ds

    def node_pc(self, key, after=False):
        """(code address, exact) for a Ren'Py statement name; after=True
        gives the address after the statement (a call's return point)."""
        if key in self.labels and not after:
            return self.labels[key], True
        n = self.nodes.get(key)
        if not n:
            return None, False
        fn, line, _ = n
        rows = self.by_file.get(fn)
        if not rows:
            return None, False
        i = bisect.bisect_left(rows, (line, -1, -1))
        if i < len(rows) and rows[i][0] == line:
            return (rows[i][2] if after else rows[i][1]), True
        # not compiled as such (a statement vn3ds leaves out, or the
        # decompiled script's lines moved a little): the nearest one after it
        # in the same file, within a few lines, else the one before
        if i < len(rows) and rows[i][0] - line <= 6:
            return (rows[i][2] if after else rows[i][1]), False
        if i > 0 and line - rows[i - 1][0] <= 6:
            return (rows[i - 1][2] if after else rows[i - 1][1]), False
        return None, False

    # vn3ds -> Ren'Py

    def statement_at(self, pc):
        """(file, line) of the innermost statement whose code holds pc."""
        best = None
        i = bisect.bisect_right(self.span_starts, pc)
        for j in range(i - 1, max(-1, i - 400), -1):
            start, end, fn, line = self.spans[j]
            if start <= pc < end and (best is None or end - start < best[0]):
                best = (end - start, fn, line)
                if start == pc:
                    break
        return (best[1], best[2]) if best else None

    def statement_ending(self, pc):
        """The statement (a call) whose code ends exactly at pc."""
        found = None
        for start, end, fn, line in self.spans:
            if end == pc and (found is None or start > found[0]):
                found = (start, fn, line)
        return (found[1], found[2]) if found else None

    def node_at(self, fn, line, kinds=None):
        names = self.lines.get((fn, line)) or []
        order = sorted(names, key=lambda kn: (kinds is not None and kn[0] not in kinds,
                                              kn[0] == "Label"))
        return order[0][1] if order else None

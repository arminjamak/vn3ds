"""Ren'Py save files, read and written without Ren'Py.

A Ren'Py save (`1-1-LT1.save`, `auto-1.save`, ...) is a zip: `log` is a
pickle of (roots, RollbackLog), with `json`, `extra_info`, `screenshot.png`,
`renpy_version` and, since Ren'Py 8.1/7.6, `signatures`. Ren'Py's own classes
are needed to unpickle it, so they are stood in for by stub classes that keep
whatever the pickle gave them (constructor arguments, state, list and dict
items) and give it back when pickled again. A save can be read, changed in a
few places (where the story is, its variables, the pictures on screen, the
music) and written so that Ren'Py loads it.

    info = read(path)          # SaveInfo: node, calls, variables, images, music
    write_from(template, out, node=..., return_nodes=..., variables=..., ...)

Ren'Py 7 saves are Python 2 pickles: their byte strings are kept as bytes
and written back as Python 2 str, so Ren'Py 7 reads them as it wrote them.
"""

import base64
import copyreg
import io
import json
import os
import pickle
import re
import sys
import time
import types
import zipfile
from collections import namedtuple

# --------------------------------------------------------------------------
# stub classes
# --------------------------------------------------------------------------


class Stub:
    """Stands in for any class the pickle names. NEWOBJ makes one with
    __new__ (no __init__); REDUCE calls the class, which runs __init__."""

    def __new__(cls, *args):
        o = object.__new__(cls)
        o._rp_args = args
        o._rp_reduce = False
        o._rp_state = None
        o._rp_has_state = False
        o._rp_items = []
        o._rp_dict = {}
        return o

    def __init__(self, *args):
        self._rp_reduce = True

    def __setstate__(self, state):
        self._rp_state = state
        self._rp_has_state = True

    # list, set and dict subclasses (RevertableList, RevertableSet, ...)
    def append(self, x):
        self._rp_items.append(x)

    def extend(self, xs):
        self._rp_items.extend(xs)

    def add(self, x):
        self._rp_items.append(x)

    def __setitem__(self, k, v):
        self._rp_dict[k] = v

    def __reduce_ex__(self, proto):
        cls = type(self)
        state = self._rp_state if self._rp_has_state else None
        items = iter(self._rp_items) if self._rp_items else None
        dictitems = iter(self._rp_dict.items()) if self._rp_dict else None
        if self._rp_reduce:
            return (cls, self._rp_args, state, items, dictitems)
        return (copyreg.__newobj__, (cls,) + tuple(self._rp_args), state, items, dictitems)

    def __repr__(self):
        return f"<{type(self).__module__}.{type(self).__name__}>"

    # the fields of the state, wherever pickle put them
    def fields(self):
        st = self._rp_state
        if isinstance(st, dict):
            return st
        if isinstance(st, tuple) and len(st) == 2:   # (dict state, slot state)
            merged = {}
            for part in st:
                if isinstance(part, dict):
                    merged.update(part)
            return merged
        return {}

    def get(self, key, default=None):
        k = _key_in(self.fields(), key)
        return self.fields().get(k, default) if k is not None else default

    def set(self, key, value):
        st = self._rp_state
        dicts = [st] if isinstance(st, dict) else [p for p in st if isinstance(p, dict)] \
            if isinstance(st, tuple) else []
        for d in dicts:
            k = _key_in(d, key)
            if k is not None:
                d[k] = value
                return
        if dicts:
            dicts[0][_like(dicts[0], key)] = value
        else:
            self._rp_state = {key: value}
            self._rp_has_state = True


def _key_in(d, key):
    """The key as the dict spells it (str, or bytes in a Python 2 pickle)."""
    if key in d:
        return key
    b = key.encode() if isinstance(key, str) else None
    return b if b is not None and b in d else None


def _like(d, key):
    return key.encode() if any(isinstance(k, bytes) for k in d) else key


_stub_modules = {}


def _stub_class(module, name):
    mod = _stub_modules.get(module)
    if mod is None:
        mod = types.ModuleType(module)
        _stub_modules[module] = mod
    cls = getattr(mod, name, None)
    if cls is None:
        cls = type(name, (Stub,), {"__module__": module, "__qualname__": name})
        setattr(mod, name, cls)
    return cls


class _Unpickler(pickle.Unpickler):
    def find_class(self, module, name):
        if module in ("copy_reg", "copyreg") and name == "_reconstructor":
            return _Reconstruct
        if module in ("__builtin__", "builtins"):
            import builtins
            return getattr(builtins, name)
        if module in ("collections", "datetime", "decimal", "fractions", "_codecs", "codecs"):
            return super().find_class(module, name)
        return _stub_class(module, name)


class _Reconstruct:
    """copy_reg._reconstructor as it appeared in the pickle (old-style
    classes pickled with protocol < 2)."""

    def __new__(cls, klass, base, state):
        if isinstance(klass, type) and issubclass(klass, Stub):
            o = klass.__new__(klass)
            o._rp_reconstruct = (base, state)
            return o
        return copyreg._reconstructor(klass, base, state)


class _Pickler(pickle._Pickler):
    """Writes stubs under the names they were read with; in a Python 2 save,
    bytes are written back as Python 2 str."""

    def __init__(self, f, protocol, py2):
        super().__init__(f, protocol, fix_imports=True)
        self.py2 = py2

    def save_global(self, obj, name=None):
        if isinstance(obj, type) and issubclass(obj, Stub) or obj is _Reconstruct:
            module, qn = (("copy_reg" if self.py2 else "copyreg", "_reconstructor")
                          if obj is _Reconstruct else (obj.__module__, obj.__qualname__))
            self.write(pickle.GLOBAL + module.encode("utf-8") + b"\n" + qn.encode("utf-8") + b"\n")
            self.memoize(obj)
            return
        super().save_global(obj, name)

    def save_bytes(self, obj):
        if not self.py2:
            return super().save_bytes(obj)
        n = len(obj)
        if n < 256:
            self.write(pickle.SHORT_BINSTRING + bytes([n]) + obj)
        else:
            self.write(pickle.BINSTRING + n.to_bytes(4, "little") + obj)
        self.memoize(obj)

    def save_reduce(self, func, args, state=None, listitems=None, dictitems=None,
                    state_setter=None, obj=None):
        # an object rebuilt by copy_reg._reconstructor goes back the same way
        if obj is not None and isinstance(obj, Stub) and hasattr(obj, "_rp_reconstruct"):
            base, st = obj._rp_reconstruct
            return super().save_reduce(_Reconstruct, (type(obj), base, st), state,
                                       listitems, dictitems, obj=obj)
        return super().save_reduce(func, args, state, listitems, dictitems,
                                   state_setter=state_setter, obj=obj)


_Pickler.dispatch = dict(pickle._Pickler.dispatch)
_Pickler.dispatch[bytes] = _Pickler.save_bytes


def is_py2(data):
    """A Python 2 pickle has Python 2 str (BINSTRING) among its first
    strings (the names in roots, at least); Python 3 never writes one."""
    import pickletools
    try:
        for i, (op, _, _) in enumerate(pickletools.genops(io.BytesIO(data))):
            if op.name in ("SHORT_BINSTRING", "BINSTRING", "STRING"):
                return True
            if i > 20000:
                break
    except Exception:
        pass
    return False


def loads(data):
    """(roots, log, py2, protocol) from a save's `log`."""
    proto = data[1] if data[:1] == b"\x80" else 0
    py2 = is_py2(data)   # (its str stays bytes, as written)
    u = _Unpickler(io.BytesIO(data), encoding="bytes" if py2 else "ASCII")
    roots, log = u.load()
    return roots, log, py2, proto


def dumps(obj, py2, protocol):
    f = io.BytesIO()
    _Pickler(f, max(2, protocol), py2).dump(obj)
    return f.getvalue()


def text(v):
    """A str from a str or Python 2 bytes."""
    if isinstance(v, bytes):
        try:
            return v.decode("utf-8")
        except UnicodeDecodeError:
            return v.decode("latin-1")
    return v


def is_stub(o, name=None):
    return isinstance(o, Stub) and (name is None or type(o).__name__ == name)


# --------------------------------------------------------------------------
# reading
# --------------------------------------------------------------------------

# the music channel's key among a context's MusicContexts: its name, or (Ren'Py 7) 7
MUSIC_KEYS = ("music", b"music", 7)

SLOT_RE = re.compile(r"^(?:(\d+)-(\d+)|(auto|quick)-(\d+))(-LT1)?\.save$")

SaveInfo = namedtuple("SaveInfo", "path slot node return_nodes call_nodes variables images "
                                  "music say_who say_what mtime renpy_version name py2")


def node_key(name):
    """A statement's name as a string key: labels are their name,
    statements (filename, version, serial)."""
    name = text(name) if not isinstance(name, tuple) else tuple(text(x) for x in name)
    if isinstance(name, tuple):
        return "|".join(str(x) for x in name)
    return str(name)


def _current_rollback(log):
    cur = log.get("current")
    if cur is None:
        entries = log.get("log") or []
        entries = entries._rp_items if is_stub(entries) else entries
        cur = entries[-1] if entries else None
    return cur


def _items(v):
    return v._rp_items if is_stub(v) else (v or [])


def read(path):
    """What a Ren'Py save holds, as plain Python values."""
    z = zipfile.ZipFile(path)
    roots, log, py2, _ = loads(z.read("log"))
    meta = {}
    try:
        meta = json.loads(z.read("json"))
    except (KeyError, ValueError):
        pass
    try:
        name = z.read("extra_info").decode("utf-8", "replace")
    except KeyError:
        name = ""
    try:
        version = z.read("renpy_version").decode("utf-8", "replace").strip()
    except KeyError:
        version = ""
    rb = _current_rollback(log)
    ctx = rb.get("context") if rb is not None else None
    if ctx is None:
        raise ValueError("no story position in this save")
    roots = roots if isinstance(roots, dict) else roots._rp_dict
    variables = {}
    for k, v in roots.items():
        k = text(k)
        if k.startswith("store.") and "." not in k[6:]:
            variables[k[6:]] = text(v) if isinstance(v, bytes) else v
    # the store as it was when this statement began: Ren'Py rolls back to it
    stores = rb.get("stores") or {}
    for sk, sv in (stores.items() if isinstance(stores, dict) else []):
        if text(sk) == "store" and isinstance(sv, dict):
            for k, v in sv.items():
                if not is_stub(v, "deleted") and text(k) in variables:
                    variables[text(k)] = text(v) if isinstance(v, bytes) else v
    images = []
    sl = ctx.get("scene_lists")
    layers = sl.get("layers") if is_stub(sl) else None
    for e in _items((layers or {}).get(_key_in(layers or {}, "master") or "master", [])):
        if not is_stub(e):
            continue
        nm = e.get("name")
        if isinstance(nm, tuple) and nm:
            images.append((" ".join(text(x) for x in nm), text(e.get("tag") or text(nm[0])),
                           int(e.get("zorder") or 0)))
    music = None
    mus = ctx.get("music") or {}
    for key in MUSIC_KEYS:
        mc = mus.get(key) if isinstance(mus, dict) else None
        if is_stub(mc):
            files = _items(mc.get("last_filenames"))
            if files:
                music = re.sub(r"^<[^>]*>", "", text(files[0]))
            break
    m = SLOT_RE.match(os.path.basename(path))
    slot = None
    if m:
        slot = f"{m.group(1)}-{m.group(2)}" if m.group(1) else f"{m.group(3)}-{m.group(4)}"
    return SaveInfo(
        path=path, slot=slot, node=node_key(ctx.get("current")),
        return_nodes=[node_key(n) for n in _items(ctx.get("return_stack"))],
        call_nodes=[node_key(n) for n in _items(ctx.get("call_location_stack"))],
        variables=variables, images=images, music=music,
        say_who=text(roots.get(_key_in(roots, "store._last_say_who") or "", "") or ""),
        say_what=text(roots.get(_key_in(roots, "store._last_say_what") or "", "") or ""),
        mtime=meta.get("_ctime") or os.path.getmtime(path),
        renpy_version=version or ".".join(str(x) for x in meta.get("_renpy_version", [])),
        name=name, py2=py2)


# --------------------------------------------------------------------------
# writing
# --------------------------------------------------------------------------

def _node_name(key, py2):
    """A node key back into Ren'Py's name (see node_key)."""
    parts = key.split("|")
    if len(parts) == 3 and parts[1].lstrip("-").isdigit() and parts[2].isdigit():
        fn = parts[0].encode() if py2 else parts[0]
        return (fn, int(parts[1]), int(parts[2]))
    return key.encode() if py2 else key


def _deepcopy_stub(o, memo):
    """A copy of a pickled object graph (stubs, lists, dicts, tuples)."""
    if id(o) in memo:
        return memo[id(o)]
    if isinstance(o, Stub):
        c = type(o).__new__(type(o), *o._rp_args)
        memo[id(o)] = c
        c._rp_reduce = o._rp_reduce
        c._rp_has_state = o._rp_has_state
        c._rp_state = _deepcopy_stub(o._rp_state, memo)
        c._rp_items = [_deepcopy_stub(x, memo) for x in o._rp_items]
        c._rp_dict = {k: _deepcopy_stub(v, memo) for k, v in o._rp_dict.items()}
        if hasattr(o, "_rp_reconstruct"):
            c._rp_reconstruct = o._rp_reconstruct
        return c
    if isinstance(o, list):
        c = []
        memo[id(o)] = c
        c.extend(_deepcopy_stub(x, memo) for x in o)
        return c
    if isinstance(o, dict):
        c = {}
        memo[id(o)] = c
        for k, v in o.items():
            c[k] = _deepcopy_stub(v, memo)
        return c
    if isinstance(o, tuple):
        return tuple(_deepcopy_stub(x, memo) for x in o)
    return o


def _find_image_refs(o, seen=None):
    """Every ImageReference inside a displayable."""
    seen = seen if seen is not None else set()
    if id(o) in seen:
        return []
    seen.add(id(o))
    found = []
    if is_stub(o):
        if type(o).__name__ == "ImageReference":
            found.append(o)
        for v in o.fields().values():
            found += _find_image_refs(v, seen)
        for v in o._rp_items:
            found += _find_image_refs(v, seen)
    elif isinstance(o, (list, tuple)):
        for v in o:
            found += _find_image_refs(v, seen)
    elif isinstance(o, dict):
        for v in o.values():
            found += _find_image_refs(v, seen)
    return found


def _set_list(holder, key, values):
    cur = holder.get(key)
    if is_stub(cur):
        cur._rp_items = list(values)
    else:
        holder.set(key, list(values))


def write_from(template, out, node, return_nodes=(), call_nodes=(), variables=None,
               images=None, music=None, say=("", ""), mtime=None, extra_info=None,
               screenshot=None):
    """Writes a Ren'Py save at `out` that resumes at `node`: the template (a
    save of the same game made by Ren'Py) gives everything vn3ds doesn't
    know. Returns notes about what had to be approximated.

    images: [(spec, tag, zorder)] or None to keep the template's. Pictures
    are rebuilt from the template's own ones (its transforms and
    positions), so a picture the template never showed takes the place of
    one it did."""
    notes = []
    z = zipfile.ZipFile(template)
    roots, log, py2, proto = loads(z.read("log"))
    k = (lambda s: s.encode()) if py2 else (lambda s: s)
    rb = _current_rollback(log)
    ctx = rb.get("context")

    # where the story is
    ctx.set("current", _node_name(node, py2))
    _set_list(ctx, "return_stack", [_node_name(n, py2) for n in return_nodes])
    _set_list(ctx, "call_location_stack", [_node_name(n, py2) for n in call_nodes])
    dyn = ctx.get("dynamic_stack")
    if dyn is not None:   # one scope per call level
        items = _items(dyn)
        while len(items) < len(return_nodes) + 1:
            items.append({})
        del items[len(return_nodes) + 1:]
    for f in ("translate_identifier", "deferred_translate_identifier",
              "alternate_translate_identifier"):
        if ctx.get(f) is not None:
            ctx.set(f, None)
    if ctx.get("line_log") is not None:
        _set_list(ctx, "line_log", [])

    # the rollback history becomes just this point (rolling back past a
    # converted position would land in the template's story)
    if rb.get("forward") is not None:
        rb.set("forward", None)
    entries = log.get("log")
    if entries is not None:
        _set_list(log, "log", [rb])
    if log.get("forward") is not None:
        _set_list(log, "forward", [])

    # variables, in roots and in the rollback's snapshot of the store
    rootd = roots if isinstance(roots, dict) else roots._rp_dict
    stores = rb.get("stores") or {}
    snap = None
    for sk, sv in (stores.items() if isinstance(stores, dict) else []):
        if text(sk) == "store" and isinstance(sv, dict):
            snap = sv
    for name, v in (variables or {}).items():
        if isinstance(v, str) and py2:
            v = v.encode("utf-8")
        old = rootd.get(_key_in(rootd, "store." + name) or "")
        if isinstance(v, float) and v.is_integer() and (isinstance(old, int) and not
                                                        isinstance(old, bool) or old is None):
            v = int(v)
        rootd[_key_in(rootd, "store." + name) or k("store." + name)] = v
        if snap is not None:
            sk_ = _key_in(snap, name)
            if sk_ is not None:
                snap[sk_] = v
    # history and the last line: what the template said is no longer true
    hl = rootd.get(_key_in(rootd, "store._history_list") or "")
    if is_stub(hl):
        hl._rp_items = []
    who, what = say
    for name, v in (("_last_say_who", who), ("_last_say_what", what)):
        key = _key_in(rootd, "store." + name)
        if key is not None:
            rootd[key] = (v.encode("utf-8") if py2 else v) if v else (k("") if what else None)

    # pictures
    if images is not None:
        sl = ctx.get("scene_lists")
        layers = sl.get("layers") if is_stub(sl) else None
        mkey = _key_in(layers or {}, "master")
        old = list(_items(layers[mkey])) if mkey is not None else []
        protos = [e for e in old if is_stub(e) and _find_image_refs(e.get("displayable"))]
        if images and not protos:
            notes.append("pictures: your Ren'Py save shows none to build them from; "
                         "they appear at the next scene")
            images = []
        new = []
        memo_time = time.time()
        for spec, tag, zorder in images:
            words = spec.split()
            proto_e = next((e for e in protos if text(e.get("tag")) == tag), protos[0])
            e = _deepcopy_stub(proto_e, {})
            e.set("tag", k(tag) if py2 else tag)
            e.set("name", tuple(k(w) for w in words))
            e.set("zorder", zorder)
            for f in ("show_time", "animation_time"):
                if e.get(f) is not None:
                    e.set(f, memo_time)
            for ref in _find_image_refs(e.get("displayable")):
                ref.set("name", tuple(k(w) for w in words))
            new.append(e)
        if mkey is not None:
            if is_stub(layers[mkey]):
                layers[mkey]._rp_items = new
            else:
                layers[mkey] = new
        # what Ren'Py knows is shown (for attribute changes, "show eileen happy")
        for holder in (ctx.get("images"), sl.get("shown") if is_stub(sl) else None):
            if not is_stub(holder):
                continue
            attrs = holder.get("attributes")
            shown = holder.get("shown")
            if isinstance(attrs, dict):
                for key in [x for x in attrs if text(x[0]) == "master"]:
                    del attrs[key]
                for spec, tag, _ in images:
                    attrs[(k("master"), k(tag))] = tuple(k(w) for w in spec.split()[1:])
            if isinstance(shown, set):
                for key in [x for x in shown if text(x[0]) == "master"]:
                    shown.discard(key)
                for spec, tag, _ in images:
                    shown.add((k("master"), k(tag)))
        at = sl.get("at_list") if is_stub(sl) else None
        if isinstance(at, dict):
            ak = _key_in(at, "master")
            if ak is not None and isinstance(at[ak], dict):
                at[ak] = {k(tag): [] for _, tag, _ in images}

    # music
    mus = ctx.get("music")
    if isinstance(mus, dict):
        for key in MUSIC_KEYS:
            mc = mus.get(key)
            if is_stub(mc):
                _set_list(mc, "last_filenames", [k(music)] if music else [])
                break

    data = dumps((roots, log), py2, proto)
    _write_zip(z, out, data, extra_info, mtime, screenshot)
    if mtime:
        os.utime(out, (mtime, mtime))
    return notes


def _write_zip(template_zip, out, log_data, extra_info, mtime, screenshot):
    tmp = out + ".part"
    when = time.localtime(mtime or time.time())[:6]
    meta = None
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zo:
        for info in template_zip.infolist():
            if info.filename in ("log", "signatures"):
                continue
            data = template_zip.read(info.filename)
            if info.filename == "extra_info" and extra_info is not None:
                data = extra_info.encode("utf-8")
            elif info.filename == "screenshot.png" and screenshot is not None:
                data = screenshot
            elif info.filename == "json":
                try:
                    meta = json.loads(data)
                    if "_ctime" in meta and mtime:
                        meta["_ctime"] = mtime
                    if "_save_name" in meta and extra_info is not None:
                        meta["_save_name"] = extra_info
                    data = json.dumps(meta).encode("utf-8")
                except ValueError:
                    pass
            zi = zipfile.ZipInfo(info.filename, when)
            zi.compress_type = info.compress_type
            zo.writestr(zi, data)
        zi = zipfile.ZipInfo("log", when)
        zi.compress_type = zipfile.ZIP_DEFLATED
        zo.writestr(zi, log_data)
        sig = sign(log_data)
        if sig:
            zi = zipfile.ZipInfo("signatures", when)
            zo.writestr(zi, sig)
    os.replace(tmp, out)


# --------------------------------------------------------------------------
# save tokens (Ren'Py 8.1 / 7.6 and later)
# --------------------------------------------------------------------------

def token_dirs():
    if sys.platform == "darwin":
        return [os.path.expanduser("~/Library/RenPy/tokens")]
    if sys.platform.startswith("win"):
        return [os.path.join(os.environ.get("APPDATA", ""), "RenPy", "tokens")]
    return [os.path.expanduser("~/.renpy/tokens")]


def sign(log_data):
    """Ren'Py checks a save's `signatures` against the keys of this computer
    and asks before loading one it can't verify. A save written here is
    signed with this computer's key (if Ren'Py made one and the ecdsa module
    is there); otherwise Ren'Py asks once whether to trust it."""
    try:
        import ecdsa   # noqa: F401 - optional
    except ImportError:
        return None
    for d in token_dirs():
        path = os.path.join(d, "security_keys.txt")
        if not os.path.exists(path):
            continue
        lines = []
        for line in open(path, encoding="utf-8", errors="replace"):
            parts = line.split()
            if len(parts) == 2 and parts[0] == "signing-key":
                key = ecdsa.SigningKey.from_der(base64.b64decode(parts[1]))
                vk = key.get_verifying_key().to_der()
                sig = key.sign(log_data)
                lines.append("signature " + base64.b64encode(vk).decode() + " " +
                             base64.b64encode(sig).decode())
        if lines:
            return "\n".join(lines) + "\n"
    return None

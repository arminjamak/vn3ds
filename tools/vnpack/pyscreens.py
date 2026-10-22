"""A game's own screens and Python, for the engine's embedded Python.

vnpack's script compiler turns the story into the engine's bytecode; what
that bytecode can't hold (a minigame's class, its lists and timers, a phone
UI's screens) runs here instead, unchanged: the game's init python, its
defines and defaults that aren't plain values, its style statements and
every screen (translated by screenlang.py), with vn3ds_rt.py, the screen
runtime, under them. The result is one Python program, game.bin's PYSC
section, which the engine runs with pocketpy (engine/source/pyscreen.c):

    `call screen x` (for a screen that needs it)  ->  a "pyscreen" PORT entry
    `show screen x(args)` / `hide screen x`       ->  the story dict
                                                     _vn3ds_screens, drawn over
                                                     the story, with a button
                                                     on the touch screen

Story variables stay in the VM (and so in saves): the program reads and
writes them through _get/_set (screenlang.Resolver). Python objects (the
snake game's state) live in the program only, for the session.

The images and sounds the program names are packed under their own names
("_scrN" images, "scr/N" sounds), with each image's size, and for buttons
their opaque area and a coarse alpha mask, so touches and the d-pad find a
`focus_mask` button by its visible shape.
"""

import ast
import io
import os
import re

from . import pkcompat, rpy
from .assets import AUDIO_EXTS, IMAGE_EXTS
from .screenlang import Resolver, screen_scope_names, translate_screen, translate_style

RUNTIME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vn3ds_rt.py")

# Screens the script calls that need the runtime: anything a choice menu
# would lose. (An imagemap whose hotspots jump is a map: the menu keeps it.)
_RUNTIME_FEATURES = re.compile(
    r"\b(timer|key|Function|SetVariable|SetScreenVariable|ToggleScreenVariable|SetField|"
    r"ToggleField|ToggleVariable|ToggleScreen|Show|ShowMenu|Hide|SetDict|SetLocalVariable|"
    r"viewport|vpgrid|bar|vbar|input|use|drag|draggroup|mousearea)\b")


def needs_runtime(body):
    """Does a screen use more than buttons that Jump / Call / Return?"""
    for ln in _walk(body):
        t = ln.text
        if t.startswith(("$", "for ", "default ", "python", "while ")):
            return True
        if _RUNTIME_FEATURES.search(t):
            return True
    return False


def _walk(lines):
    for ln in lines or ():
        yield ln
        yield from _walk(ln.block)


def _screen_params(line):
    m = re.match(r"screen\s+[\w.]+\s*(\(.*\))?\s*:?\s*$", line.text, re.S)
    return m.group(1)[1:-1].strip() if m and m.group(1) else ""


def _header_props(body):
    out = {}
    for ln in body:
        m = re.match(r"(modal|zorder|tag|variant|style_prefix)\s+(.+)$", ln.text)
        if m and not ln.block:
            v = m.group(2).strip()
            if m.group(1) == "tag" and re.match(r"[A-Za-z_]\w*$", v):
                v = repr(v)
            out[m.group(1)] = v
    return out


class Program:
    def __init__(self):
        self.source = ""
        self.extra_defs = {}     # engine image name -> ("file", key)
        self.screens = set()
        self.errors = 0
        self.used_images = set()   # engine image names the program draws


def _items(files):
    """Init-time statements in Ren'Py's order: (priority, seq, kind, node)."""
    out = []
    seq = 0
    for nodes in files:
        stack = [(0, n) for n in nodes]
        while stack:
            prio, n = stack.pop(0)
            seq += 1
            if isinstance(n, rpy.Init):
                stack[0:0] = [(n.priority, c) for c in n.block]
                for c in n.block:
                    if isinstance(c, rpy.Python):
                        c.init = True
                continue
            if isinstance(n, (rpy.Label, rpy.If, rpy.While, rpy.Menu)):
                from .compiler import child_nodes
                stack[0:0] = [(prio, c) for c in child_nodes(n)]
                continue
            if isinstance(n, rpy.Python) and n.init:
                out.append((prio + getattr(n, "priority", 0), seq, "py", n))
            elif isinstance(n, rpy.Define):
                out.append((prio + (n.priority or 0), seq, "define", n))
            elif isinstance(n, rpy.Default):
                out.append((100000, seq, "default", n))
            elif isinstance(n, rpy.Unsupported) and n.what == "style statements":
                out.append((prio, seq, "style", n))
            elif isinstance(n, rpy.Screen):
                out.append((100001, seq, "screen", n))
            elif isinstance(n, rpy.Transform):
                out.append((prio, seq, "transform", n))
    out.sort(key=lambda t: (t[0], t[1]))
    return out


RENPY_MODULES = ("store", "renpy", "_renpy", "pygame", "pygame_sdl2", "_ren_py")


class _RenpyImports(ast.NodeTransformer):
    """`import store`, `from renpy.display import im`: Ren'Py's own
    modules are the runtime's objects."""

    def visit_Import(self, node):
        out = []
        for a in node.names:
            root = a.name.split(".")[0]
            if root in RENPY_MODULES:
                bind = a.asname or root
                if bind != root or root not in ("renpy", "store"):
                    out.append(ast.parse(f"{bind} = _import_name({a.name!r}, {root!r})").body[0])
            else:
                out.append(ast.Import([a]))
        return out or ast.Pass()

    def visit_ImportFrom(self, node):
        root = (node.module or "").split(".")[0]
        if root not in RENPY_MODULES:
            return node
        out = []
        for a in node.names:
            if a.name == "*":
                continue
            bind = a.asname or a.name
            if bind == a.name and root == "store":
                continue   # already a global
            out.append(ast.parse(f"{bind} = _import_name({node.module!r}, {a.name!r})").body[0])
        return out or ast.Pass()


def _unparse(tree):
    return ast.unparse(ast.fix_missing_locations(tree))


def _wrap_try(src, where):
    body = "\n".join("    " + l for l in src.split("\n"))
    return f"try:\n{body}\nexcept Exception as _e:\n    _init_error({where!r}, _e)"


def build_program(comp, files, fs, warn, gw, gh, defs):
    """The program for the screens the story uses (comp.pyscreen_used), or
    None when it uses none. `defs`: the image definitions (name -> def), to
    which the program's own images are added."""
    used = set(getattr(comp, "pyscreen_used", ()))
    if not used:
        return None
    prog = Program()
    # the VM holds None, bools, numbers and strings (and its encoded sets and
    # dicts); a constant list or tuple is the program's own
    vm_value = (type(None), bool, int, float, str)
    store = set(comp.vars) | {n for n, v in comp.constants.items() if isinstance(v, vm_value)} | \
        set(comp.collections)
    store -= {n for n, v in comp.constants.items() if not isinstance(v, vm_value)}
    py_only = set()
    for _p, _s, kind, n in _items(files):
        if kind not in ("default", "define"):
            continue
        const = comp.constants.get(n.name, store)   # (store: a marker for "none")
        if n.name not in comp.collections and (const is store or not isinstance(const, vm_value)):
            py_only.add(n.name)
    store -= py_only
    store -= {"_vn3ds_unused"}
    out = []   # (where, statement source): loaded one by one (a failure stays local)
    where_n = 0

    def where(n):
        return f"{n.line.filename}:{n.line.lineno}"

    def add_code(src, n, module=True, screen_names=None):
        nonlocal where_n
        try:
            tree = ast.parse(src)
        except SyntaxError as e:
            warn(n.line, f"python (for the screen runtime) cannot be parsed: {e.msg}; skipped")
            return
        tree = _RenpyImports().visit(tree)
        tree = Resolver(store, screen_names, module=module).run(tree)
        for st in tree.body:
            out.append((where(n), ast.Module([st], [])))

    screen_src = []
    for _p, _s, kind, n in _items(files):
        if kind == "py":
            add_code(n.code, n)
        elif kind == "define":
            name = n.name
            if name in store or name.startswith(("build.", "_")):
                continue
            if name.startswith("config.") and name.split(".")[1] not in (
                    "keymap", "name", "version"):
                continue
            op = getattr(n, "op", "=") or "="
            add_code(f"{name} {op} {n.expr}", n)
        elif kind == "default":
            if n.name in store or "." in n.name:
                continue
            add_code(f"{n.name} = {n.expr}", n)
        elif kind == "style":
            for call in translate_style(n.line, warn):
                add_code(call, n)
        elif kind == "transform":
            rest = atl_rest_state(n.block)
            out.append((where(n), ast.parse(f"{rpy_ident(n.name)} = _ATL({n.name!r}, {rest!r})")))
        elif kind == "screen":
            screen_src.append(n)

    # screens: every one the game defines (any can be shown from another)
    for n in screen_src:
        name = n.name
        params = _screen_params(n.line)
        fn = translate_screen(name, params, n.body, warn)
        try:
            ftree = ast.parse(fn)
        except SyntaxError as e:
            warn(n.line, f"screen {name}: the translation doesn't parse ({e.msg}); skipped")
            prog.errors += 1
            continue
        pnames = set()
        if params:
            try:
                ptree = ast.parse(f"def _p({params}): pass").body[0].args
                for a in ptree.posonlyargs + ptree.args + ptree.kwonlyargs:
                    pnames.add(a.arg)
                if ptree.vararg:
                    pnames.add(ptree.vararg.arg)
                if ptree.kwarg:
                    pnames.add(ptree.kwarg.arg)
            except SyntaxError:
                warn(n.line, f"screen {name}: cannot read its parameters; skipped")
                continue
        scope = screen_scope_names(ftree) | pnames
        ftree = Resolver(store, scope).run(ftree)
        ident = rpy_ident(name)
        out.append((where(n), ftree))
        if params:
            binder = ast.parse(f"def _args_{ident}({params}):\n    return {{" +
                               ", ".join(f"{p!r}: {p}" for p in sorted(pnames)) + "}")
            binder = Resolver(store, module=False).run(binder)
            out.append((where(n), binder))
            bname = f"_args_{ident}"
        else:
            bname = "None"
        hdr = _header_props(n.body)
        hdr_src = "{" + ", ".join(f"{k!r}: ({v})" for k, v in hdr.items()) + "}"
        try:
            hdr_tree = Resolver(store, module=False).run(ast.parse(hdr_src, mode="eval"))
            hdr_src = _unparse(hdr_tree)
        except SyntaxError:
            hdr_src = "{}"
        out.append((where(n), ast.parse(
            f"_screens[{name!r}] = (_scr_{ident}, {bname}, {hdr_src})")))
        prog.screens.add(name)

    # script-side arguments of show screen / call screen
    args_tbl = {}
    for src in sorted(getattr(comp, "pyscreen_args", ())):
        if not src:
            continue
        try:
            t = Resolver(store, module=False).run(ast.parse(f"_UI.pack({src})", mode="eval"))
            args_tbl[src] = _unparse(t)
        except SyntaxError:
            warn(None, f"screen arguments ({src}) cannot be parsed")

    for raw, tr in args_tbl.items():
        out.append(("arguments", ast.parse(f"_ARGS[{raw!r}] = (lambda: {tr})")))
    images, audio = collect_assets(ast.Module([st for _w, t in out for st in t.body], []),
                                   comp, fs, warn, defs, prog)
    # each statement in the interpreter's dialect (pkcompat.py)
    chunks = []
    for w, t in out:
        try:
            chunks.append((w, pkcompat.unparse(pkcompat.transform(t))))
        except Exception as e:   # noqa: BLE001 - a statement we can't rewrite is left out
            warn(None, f"{w}: cannot prepare a statement for the screen runtime ({e})")
    head = [f"init({gw}, {gh})", f"_IMAGES.update({images!r})", f"_AUDIO.update({audio!r})",
            f"_load_chunks({chunks!r})"]
    prog.source = "\n".join(head) + "\n"
    prog.chunks = len(chunks)
    with open(RUNTIME, encoding="utf-8") as f:
        prog.runtime = pkcompat.convert_source(f.read())
    return prog


ATL_PROPS = {"xpos", "ypos", "xanchor", "yanchor", "xalign", "yalign", "align", "pos", "anchor",
             "xoffset", "yoffset", "offset", "alpha", "zoom", "xzoom", "yzoom", "xycenter",
             "xcenter", "ycenter", "around"}
ATL_WARPERS = {"linear", "ease", "easein", "easeout", "pause"}


def atl_rest_state(block):
    """The properties an ATL block ends on: assignments and the targets of
    interpolations, in order, parallel blocks included; `on` handlers other
    than show/start/appear, and repeats, left out. Only constant values."""
    out = {}

    def value(src):
        try:
            return ast.literal_eval(src)
        except (ValueError, SyntaxError):
            return None

    def props_of(text):
        words = text.split(None, 1)
        if not words:
            return
        rest = text
        if words[0] in ATL_WARPERS or words[0].startswith(("ease_", "warp")):
            parts = text.split(None, 2)
            if words[0] == "pause" or len(parts) < 3:
                return
            rest = parts[2]
        from .screenlang import split_props
        sp = split_props(rest, first_prop=True)
        if sp is None:
            return
        for name, src in sp[1]:
            if name in ATL_PROPS:
                v = value(src)
                if v is not None:
                    out[name] = v

    def walk(lines):
        for ln in lines:
            t = ln.text.rstrip(":").strip()
            w = t.split()[0] if t else ""
            if w in ("block", "parallel", "contains", "choice"):
                walk(ln.block)
            elif w == "on":
                if any(e in t for e in ("show", "start", "appear", "replace")):
                    walk(ln.block)
            elif w in ("repeat", "function", "time", "event", "pass"):
                continue
            elif not ln.block:
                props_of(t)
    walk(block or [])
    return out


def rpy_ident(name):
    return re.sub(r"\W", "_", name)


# ---------------------------------------------------------------------------
# images and sounds named by the program

STATES = ("idle", "hover", "selected_idle", "selected_hover", "insensitive",
          "selected_insensitive", "selected", "ground")


def _norm(s):
    return " ".join(str(s).replace("\\", "/").lower().split())


def _strings(tree):
    for n in ast.walk(tree):
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and 0 < len(n.value) < 200:
            yield n.value


MASK_W = 48   # alpha mask cells across (rows follow the aspect)


def image_meta(data):
    """(w, h, bbox or None, mask or None) of an image file's pixels: the box
    of its opaque pixels and a coarse alpha mask, for focus_mask buttons."""
    from PIL import Image
    im = Image.open(io.BytesIO(data))
    w, h = im.size
    if im.mode not in ("RGBA", "LA", "PA") and not (im.mode == "P" and "transparency" in im.info):
        return w, h, None, None
    a = im.convert("RGBA").getchannel("A")
    box = a.point(lambda v: 255 if v >= 8 else 0).getbbox()   # focus_mask: any alpha
    if box is None:
        return w, h, (0, 0, 0, 0), None
    bbox = (box[0], box[1], box[2] - box[0], box[3] - box[1])
    if bbox == (0, 0, w, h):
        return w, h, None, None
    mw = MASK_W
    mh = max(1, round(MASK_W * h / w))
    small = a.resize((mw, mh), Image.BOX)
    px = small.load()
    bits = []
    for y in range(mh):
        for x in range(mw):
            bits.append(1 if px[x, y] >= 8 else 0)
    while len(bits) % 4:
        bits.append(0)
    hexs = "".join("%x" % (bits[k] * 8 + bits[k + 1] * 4 + bits[k + 2] * 2 + bits[k + 3])
                   for k in range(0, len(bits), 4))
    return w, h, bbox, (mw, mh, hexs)


def collect_assets(tree, comp, fs, warn, defs, prog):
    """{name: (engine image, w, h, bbox, mask)}, {path: engine audio}."""
    images, audio = {}, {}
    by_key = {}
    seen = set()
    cands = set()
    for s in _strings(tree):
        if "%s" in s:
            for st in STATES:
                cands.add(s.replace("%s", st))
        else:
            cands.add(s)
    names_lower = {}
    for name in defs:
        names_lower.setdefault(_norm(name), name)
    for s in sorted(cands):
        n = _norm(s)
        if n in seen or not n or "[" in n:
            continue
        seen.add(n)
        if n.endswith(IMAGE_EXTS):
            key = fs.find(s, dirs=("", "images/"))
            if key is None:
                continue
            eng = by_key.get(key)
            if eng is None:
                try:
                    meta = image_meta(fs.read(key))
                except Exception as e:   # noqa: BLE001 - a broken file is just skipped
                    warn(None, f"screen image {s}: {e}")
                    continue
                eng = f"_scr{len(prog.extra_defs)}"
                prog.extra_defs[eng] = ("file", key)
                by_key[key] = eng
                images[_norm(key)] = (eng,) + meta
            images[n] = images[_norm(key)]
        elif n.endswith(tuple(AUDIO_EXTS)):
            key = fs.find(s, dirs=("", "audio/"))
            if key is None:
                continue
            idx = comp.audio_index(key)
            name = f"scr/{idx}"
            comp.named_audio[name] = idx
            audio[n] = name
            audio[_norm(key)] = name
        elif n in names_lower and len(n) < 64:
            dname = names_lower[n]
            d = defs[dname]
            meta = None
            if d[0] == "file":
                try:
                    meta = image_meta(fs.read(d[1]))
                except Exception:   # noqa: BLE001
                    meta = None
            elif d[0] == "expr":
                m = re.match(r"""\s*["']([^"']+\.(?:png|jpe?g|webp))["']\s*$""", d[1] or "", re.I)
                key = fs.find(m.group(1), dirs=("", "images/")) if m else None
                if key:
                    try:
                        meta = image_meta(fs.read(key))
                    except Exception:   # noqa: BLE001
                        meta = None
            if meta is None:
                meta = (comp.meta.get("width") or 1920, comp.meta.get("height") or 1080, None, None)
            images[n] = (dname,) + meta
    prog.used_images = {v[0] for v in images.values()}
    return images, audio

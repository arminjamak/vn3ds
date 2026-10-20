"""Ported minigames: a game's custom screens rebuilt as native vn3ds games.

Some Ren'Py games play a minigame through a screen of their own (a
displayable written in Python, a timer-driven screen, an imagemap that
plays notes). vn3ds can't run those screens, but its engine has native
versions of common mechanics (engine/source/mg_lockpick.c and friends,
listed in engine/source/minigame.c). An adapter tells vnpack which screen
is which mechanic:

    tools/vnpack/adapters/<game id>.json      (shipped with vnpack), or
    "minigames" in the game folder's vn3ds.json (wins over the adapter)

    {"minigames": {"<screen name>": {"mechanic": "<id>", ...}}}

An adapter holds only names from the game's own files (screens, labels,
variables, constants, image and audio paths): the mechanic's numbers, art,
sounds and text are read from the game's scripts and files when the game is
packed, so they end up only in that game's own build. Each `call screen`
of an adapted screen compiles into vn3ds_minigame("@i") (i: its entry in
game.bin's PORT table, with the mechanic's parameters), followed by the
screen's own Jump if it had one; the native game sets the story variables
the original screen set.

Mechanics and what their adapter entries name:

  lockpick       class (the Python displayable class: its constructor's
                 defaults), images {plate, cylinder, tension, pick,
                 pick_broken}, sounds {unlock, pick_break, loop_moving,
                 loop_jiggling, loop_moving_back}, result (default _return).
                 The parameters come from the displayable passed to the
                 screen: `$ lock = LockClass(sweet_angle=3, ...)` then
                 `call screen lock_screen(lock)`.
  swing_timing   window, speed, speed_alt, angle_offset (constants),
                 speed_if, score, rotation_var, clockwise_var (variables).
                 Layout, art and the Jump come from the screen.
  instrument     nothing else: the imagemap's hotspots, their SetVariable /
                 Play actions, the background and the Stop hotspot's Jump
                 come from the screen.
  captions       nothing else: the timed text frames (their ATL fades), the
                 spinning icon and the timer's Jump come from the screen.
"""

import ast
import json
import os
import re

from . import rpy

ADAPTER_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "adapters")
MECHANICS = ("lockpick", "swing_timing", "instrument", "captions")


def load_spec(game_id, cfg):
    """The screen -> entry map for a game: its adapter, then vn3ds.json."""
    spec = {}
    path = os.path.join(ADAPTER_DIR, f"{game_id}.json")
    if game_id and os.path.isfile(path):
        with open(path) as f:
            spec.update(json.load(f).get("minigames", {}))
    spec.update(cfg.get("minigames", {}) or {})
    return {k: v for k, v in spec.items() if isinstance(v, dict) and v.get("mechanic")}


def _strip_str(src):
    src = src.strip()
    if len(src) >= 2 and src[0] in "\"'" and src[-1] == src[0]:
        return src[1:-1]
    return None


class _Eval:
    """Arithmetic over numbers and the game's constants."""

    def __init__(self, consts):
        self.consts = consts

    def __call__(self, src, env=None, default=None):
        if src is None:
            return default
        if isinstance(src, (int, float)):
            return src
        try:
            return self.ev(ast.parse(str(src).strip(), mode="eval").body, env or {})
        except (SyntaxError, ValueError, KeyError, TypeError, ZeroDivisionError):
            return default

    def ev(self, n, env):
        if isinstance(n, ast.Constant):
            return n.value
        if isinstance(n, ast.Name):
            if n.id in env:
                return env[n.id]
            if n.id in self.consts:
                return self.consts[n.id]
            raise KeyError(n.id)
        if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == "store":
            return self.ev(ast.Name(id=n.attr), env)
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.USub, ast.UAdd)):
            v = self.ev(n.operand, env)
            return -v if isinstance(n.op, ast.USub) else v
        if isinstance(n, ast.BinOp):
            a, b = self.ev(n.left, env), self.ev(n.right, env)
            ops = {ast.Add: lambda: a + b, ast.Sub: lambda: a - b, ast.Mult: lambda: a * b,
                   ast.Div: lambda: a / b, ast.Pow: lambda: a ** b}
            if type(n.op) in ops:
                return ops[type(n.op)]()
        if isinstance(n, (ast.Tuple, ast.List)):
            return tuple(self.ev(e, env) for e in n.elts)
        raise ValueError(ast.dump(n))


def _lines(block):
    for l in block:
        yield l
        yield from _lines(l.block)


_PROPS = r"(?:xalign|yalign|align|xpos|ypos|pos|xsize|ysize|xysize|xanchor|yanchor|anchor|" \
         r"style|at|xoffset|yoffset|xmaximum|ymaximum|xminimum|yminimum)"


def _prop(line, key):
    """`key value` on a screen line or among its children (a property on a
    line of its own takes the rest of the line: `ysize radius * 2`)."""
    for l in [line] + list(_lines(line.block)):
        m = re.match(rf"\s*{key}\s+(.+?)\s*$", l.text)
        if m and l is not line:   # up to the next property on the line
            return re.split(rf"\s+(?={_PROPS}\s)", m.group(1))[0]
        m = re.search(rf"(?:^|\s){key}\s+(\([^)]*\)|\"[^\"]*\"|'[^']*'|[^\s:]+)", l.text)
        if m:
            return m.group(1)
    return None


_JUMP = re.compile(r"\bJump\s*\(\s*(?:\"([^\"]+)\"|'([^']+)')\s*\)")


def _jump(text):
    m = _JUMP.search(text)
    return (m.group(1) or m.group(2)) if m else None


class Ported:
    def __init__(self, spec, files, warn):
        self.spec = spec
        self.warn = warn
        self.entries = []          # [(mechanic, [(key, value)])]
        self.deferred = []         # callables(fs) run by prepare_assets
        # `$ name = Something(...)` anywhere in the story: the displayables
        # passed to screens.
        self.assignments = {}
        self.defaults = {}         # `default x = ...` anywhere, even inside a label
        for nodes in files:
            for n in rpy.iter_nodes(nodes):
                if isinstance(n, rpy.Default):
                    self.defaults.setdefault(n.name, n.expr)
                if isinstance(n, rpy.Python) and not getattr(n, "init", False):
                    try:
                        tree = ast.parse(n.code)
                    except SyntaxError:
                        continue
                    for st in tree.body:
                        if isinstance(st, ast.Assign) and len(st.targets) == 1 and \
                                isinstance(st.targets[0], ast.Name) and isinstance(st.value, ast.Call):
                            self.assignments.setdefault(st.targets[0].id, []).append((n.line, st.value))

    def handles(self, screen):
        return screen in self.spec

    # -- compiling ------------------------------------------------------

    def compile_call(self, comp, n):
        cfg = self.spec[n.name]
        mech = cfg["mechanic"]
        if mech not in MECHANICS:
            raise ValueError(f"adapter for screen {n.name}: unknown mechanic '{mech}'")
        body = comp.screen_bodies.get(n.name)
        if body is None:
            raise ValueError(f"adapter names screen {n.name}, which the scripts don't define")
        idx = len(self.entries)
        params = []
        ctx = dict(comp=comp, n=n, cfg=cfg, body=body, idx=idx, params=params,
                   ev=_Eval(comp.constants), jump=None)
        getattr(self, "c_" + mech)(ctx)
        if n.with_:   # the screen's own transition: the game fades in over it
            tid = comp.transition(n.with_, n.line)
            if tid >= 0:
                typ, _, _, ta, tb, tc, _ = comp.transitions[tid]
                self.add(ctx, "fade_in", ta + tb + tc if typ == 2 else ta)
        self.entries.append((mech, params))
        comp.warn_once(f"ported:{n.name}", n.line,
                       f"call screen {n.name} plays as vn3ds's native {mech} minigame")
        code = comp.code
        code.op("PUSH_STR")
        code.u32(comp.s(f"@{idx}"))
        code.op("MINIGAME")
        code.op("POP")
        if ctx["jump"]:
            code.op("JMP")
            code.ref(comp.label_ref(comp.qualify(ctx["jump"], n.line)))

    # helpers --------------------------------------------------------------

    def image(self, ctx, key, src, crop=None):
        """Packs an image for the entry: `src` is an image name, a file path
        or a constant holding either. Returns the spec the engine looks up."""
        comp, n = ctx["comp"], ctx["n"]
        v = comp.constants.get(src, src) if isinstance(src, str) else src
        if not isinstance(v, str) or not v:
            return None
        if crop is None and not re.search(r"\.(png|jpe?g|webp|bmp|gif)$", v, re.I) \
                and v.split()[0] not in ("Crop",):
            comp.used_specs.setdefault(v, n.line)   # an image the game defines
            return v
        spec = f"_mg{ctx['idx']} {key}"
        if crop:
            x, y, w, h = crop
            comp.image_defs[spec] = ("expr", f"Crop(({x}, {y}, {w}, {h}), {v!r})", n.line)
        else:
            comp.image_defs[spec] = ("expr", repr(v), n.line)
        comp.used_specs.setdefault(spec, n.line)
        return spec

    def sound(self, ctx, name, src):
        """Packs a sound as the entry's named clip "minigame/@i_<name>"."""
        comp = ctx["comp"]
        v = comp.constants.get(src, src)
        if not isinstance(v, str) or not v:
            return
        path = comp.audio_names.get(v, v)
        comp.named_audio[f"minigame/@{ctx['idx']}_{name}"] = comp.audio_index(path)

    @staticmethod
    def add(ctx, key, value):
        if value is not None:
            ctx["params"].append((key, value if isinstance(value, str) else _fmt(value)))

    # -- lockpick --------------------------------------------------------

    def c_lockpick(self, ctx):
        comp, n, cfg, ev = ctx["comp"], ctx["n"], ctx["cfg"], ctx["ev"]
        values = {}
        cls = cfg.get("class")
        node = comp.py_classes.get(cls) if cls else None
        init_args = []
        if node is not None:      # the constructor's defaults
            for st in node.body:
                if isinstance(st, ast.FunctionDef) and st.name == "__init__":
                    a = st.args
                    init_args = [x.arg for x in a.args[1:]]
                    for x, d in zip(a.args[len(a.args) - len(a.defaults):], a.defaults):
                        values[x.arg] = ev(ast.unparse(d))
        # The displayable handed to the screen: `call screen s(lock)` after
        # `$ lock = Lock(...)` (the closest one before it), or inline.
        arg = n.args.strip()[1:-1].strip() if n.args else ""
        call, best = None, None
        for line, c in self.assignments.get(arg, []):
            if cls and (rpy_dotted(c.func) or "").split(".")[-1] != cls:
                continue
            here = line.filename == n.line.filename and line.lineno <= n.line.lineno
            rank = (here, line.lineno if here else -line.lineno)
            if best is None or rank > best:
                call, best = c, rank
        if call is None and arg:
            try:
                e = ast.parse(arg, mode="eval").body
                call = e if isinstance(e, ast.Call) else None
            except SyntaxError:
                call = None
        if call is not None:
            for name, a in zip(init_args, call.args):
                values[name] = ev(ast.unparse(a))
            for k in call.keywords:
                if k.arg:
                    values[k.arg] = ev(ast.unparse(k.value))
        for key in ("sweet_angle", "pick_dmg", "attempts", "resize"):
            if isinstance(values.get(key), (int, float)):
                self.add(ctx, key, values[key])
        self.add(ctx, "result", cfg.get("result", "_return"))
        for key, src in (cfg.get("images") or {}).items():
            self.lock_image(ctx, key, src)
        for key, src in (cfg.get("sounds") or {}).items():
            self.sound(ctx, key, src)

    def lock_image(self, ctx, key, src):
        """Packed cropped to what is drawn; the engine gets the box."""
        comp = ctx["comp"]
        path = comp.constants.get(src, src)
        spec = f"_mg{ctx['idx']} {key}"
        self.add(ctx, key, spec)
        params = ctx["params"]

        def crop(fs, n=ctx["n"]):
            img = _open(fs, path)
            if img is None:
                self.warn(n.line, f"minigame image '{path}' not found")
                return
            box = img.getchannel("A").getbbox() if img.mode == "RGBA" else None
            box = box or (0, 0, img.width, img.height)
            x0, y0, x1, y1 = box
            comp.image_defs[spec] = ("expr", f"Crop(({x0}, {y0}, {x1 - x0}, {y1 - y0}), {path!r})",
                                     n.line)
            params.append((f"box_{key}", f"{x0} {y0} {x1} {y1} {img.width} {img.height}"))
        comp.image_defs[spec] = ("expr", repr(path), ctx["n"].line)
        comp.used_specs.setdefault(spec, ctx["n"].line)
        self.deferred.append(crop)

    # -- swing timing -------------------------------------------------------

    def c_swing_timing(self, ctx):
        comp, cfg, ev, body = ctx["comp"], ctx["cfg"], ctx["ev"], ctx["body"]
        for key in ("window", "speed", "speed_alt", "angle_offset"):
            if key in cfg:
                v = ev(cfg[key])
                if isinstance(v, (int, float)):
                    self.add(ctx, key, v)
        for key in ("speed_if", "score", "rotation_var", "clockwise_var"):
            if key in cfg:
                self.add(ctx, key, cfg[key])
        gw, gh = comp.meta["width"] or 1280, comp.meta["height"] or 720
        adds = []
        for l in _lines(body):
            t = l.text.strip()
            m = re.match(r"add\s+(\"[^\"]+\"|'[^']+')(?:\s+at\s+(\w+)\s*\(([^)]*)\))?", t)
            if m:
                adds.append((_strip_str(m.group(1)), m.group(2), m.group(3)))
            if _jump(t) and not ctx["jump"]:
                ctx["jump"] = _jump(t)
            if t.startswith("fixed") and not any(k == "box" for k, _ in ctx["params"]):
                xs, ys = ev(_prop(l, "xsize"), default=None), ev(_prop(l, "ysize"), default=None)
                xa, ya = ev(_prop(l, "xalign"), default=0.0), ev(_prop(l, "yalign"), default=0.0)
                if isinstance(xs, (int, float)) and isinstance(ys, (int, float)):
                    self.add(ctx, "box", f"{_fmt((gw - xs) * xa)} {_fmt((gh - ys) * ya)} "
                                         f"{_fmt(xs)} {_fmt(ys)}")
        bar = next((a for a in adds if not a[1]), None)
        ball = next((a for a in adds if a[1]), None)
        if bar:
            self.add(ctx, "bar", self.image(ctx, "bar", bar[0]))
        if ball:
            self.add(ctx, "ball", self.image(ctx, "ball", ball[0]))
            self.size_param(ctx, "ball_size", ball[0])
            tr = comp.transform_nodes.get(ball[1])
            if tr is not None:     # around / radius / angle of the polar transform
                names = [p.strip().split("=")[0].strip() for p in (tr.params or "()")[1:-1].split(",")
                         if p.strip()]
                env = {nm: 0 for nm in names}
                for l in _lines(tr.block):
                    t = l.text.strip()
                    m = re.match(r"(around|radius|angle)\s+(.+)$", t)
                    if not m:
                        continue
                    v = ev(m.group(2), env)
                    if m.group(1) == "around" and isinstance(v, tuple):
                        self.add(ctx, "center", f"{_fmt(v[0])} {_fmt(v[1])}")
                    elif m.group(1) == "radius" and isinstance(v, (int, float)):
                        self.add(ctx, "radius", v)
                    elif m.group(1) == "angle" and isinstance(v, (int, float)) and \
                            "angle_offset" not in cfg:
                        self.add(ctx, "angle_offset", v)

    def size_param(self, ctx, key, src):
        params, comp = ctx["params"], ctx["comp"]
        v = comp.constants.get(src, src)

        def size(fs, n=ctx["n"]):
            img = _open(fs, v)
            if img is not None:
                params.append((key, f"{img.width} {img.height}"))
        self.deferred.append(size)

    # -- instrument -----------------------------------------------------------

    def c_instrument(self, ctx):
        comp, body = ctx["comp"], ctx["body"]
        lists = {}
        hover = ground = None
        bg_var = None
        strings, stop = [], None
        keys = {}
        for l in _lines(body):
            t = l.text.strip()
            m = re.match(r"\$\s*(\w+)\s*=\s*(\[.*\])\s*$", t, re.S)
            if m:
                lists[m.group(1)] = m.group(2)
                continue
            m = re.match(r"add\s+([A-Za-z_]\w*)\s*$", t)
            if m:   # a picture named by a variable
                bg_var = m.group(1)
                continue
            m = re.match(r"(ground|idle|hover)\s+(\"[^\"]+\"|'[^']+')", t)
            if m:
                if m.group(1) == "hover":
                    hover = _strip_str(m.group(2))
                elif ground is None:
                    ground = _strip_str(m.group(2))
                continue
            m = re.match(r"hotspot\s*\(([^)]*)\)\s*action\s+(.+)$", t)
            if m:
                rect = [ctx["ev"](v, default=0) for v in m.group(1).split(",")[:4]]
                action = m.group(2).strip()
                if _jump(action):
                    stop = (rect, _jump(action))
                else:
                    strings.append((rect, lists.get(action, action)))
                continue
            m = re.match(r"key\s+\S+\s+action\s+(\w+)", t)
            if m:
                keys.setdefault(m.group(1), True)
        if bg_var:
            self.add(ctx, "background_var", bg_var)
        if ground:
            self.add(ctx, "overlay", self.image(ctx, "overlay", ground))
        bg_values = set()
        first = comp.constants.get(bg_var) if bg_var else None
        if bg_var and first is None and bg_var in self.defaults:
            first = ctx["ev"](self.defaults[bg_var])
        if isinstance(first, str):    # the picture before the first note
            bg_values.add(first)
            self.add(ctx, "background", first)
        for k, (rect, action) in enumerate(strings):
            ops, sound, label = [], "", ""
            try:
                items = ast.parse(action, mode="eval").body
                items = items.elts if isinstance(items, (ast.List, ast.Tuple)) else [items]
            except SyntaxError:
                items = []
            for it in items:
                if not isinstance(it, ast.Call):
                    continue
                fn = rpy_dotted(it.func) or ""
                args = it.args
                if fn == "Play" and len(args) >= 2 and isinstance(args[1], ast.Constant):
                    sound = f"s{k}"
                    self.sound(ctx, sound, args[1].value)
                elif fn == "SetVariable" and len(args) == 2 and isinstance(args[0], ast.Constant):
                    var, val = args[0].value, args[1]
                    if isinstance(val, ast.Constant) and isinstance(val.value, str):
                        ops.append(f"set {var}={val.value}")
                        if var == bg_var:
                            bg_values.add(val.value)
                    elif isinstance(val, ast.BinOp) and isinstance(val.op, ast.Add) and \
                            isinstance(val.left, ast.Name) and val.left.id == var and \
                            isinstance(val.right, ast.Constant):
                        r = val.right.value
                        if isinstance(r, str):
                            ops.append(f"cat {var}={r}")
                            label = label or r.upper()
                        elif isinstance(r, (int, float)):
                            ops.append(f"add {var}={_fmt(r)}")
            hov = self.image(ctx, f"hover{k}", hover, crop=tuple(int(v) for v in rect)) if hover else ""
            x, y, w, h = rect
            self.add(ctx, "string", "\t".join([f"{_fmt(x)} {_fmt(y)} {_fmt(w)} {_fmt(h)}",
                                               label or str(k + 1), sound, hov or ""] + ops))
        if stop:
            rect, label = stop
            hov = self.image(ctx, "hover_stop", hover, crop=tuple(int(v) for v in rect)) if hover else ""
            x, y, w, h = rect
            self.add(ctx, "stop", "\t".join([f"{_fmt(x)} {_fmt(y)} {_fmt(w)} {_fmt(h)}", "Stop",
                                             hov or ""]))
            ctx["jump"] = label
        for k, v in enumerate(sorted(bg_values)):
            spec = self.image(ctx, f"bg{k}", v)
            if spec and spec != v:
                self.add(ctx, "bg_alias", f"{v}\t{spec}")
            elif spec:
                self.add(ctx, "bg_alias", f"{v}\t{v}")

    # -- captions -------------------------------------------------------------

    def c_captions(self, ctx):
        comp, body, ev = ctx["comp"], ctx["body"], ctx["ev"]
        gw, gh = comp.meta["width"] or 1280, comp.meta["height"] or 720
        for l in body:
            t = l.text.strip()
            m = re.match(r"timer\s+([\d.]+)\s+action\s+(.+)$", t)
            if m:
                self.add(ctx, "duration", float(m.group(1)))
                ctx["jump"] = _jump(m.group(2))
                continue
            if not t.startswith("frame"):
                continue
            kids = list(_lines(l.block))
            xa = ev(_prop(l, "xalign"), default=None)
            ya = ev(_prop(l, "yalign"), default=0.0)
            xp = ev(_prop(l, "xpos"), default=None)
            add = next((k for k in kids if re.match(r"add\s+[\"']", k.text.strip())), None)
            if add is not None:
                m = re.match(r"add\s+(\"[^\"]+\"|'[^']+')(?:\s+at\s+(\w+))?", add.text.strip())
                name = _strip_str(m.group(1))
                self.add(ctx, "spinner", self.image(ctx, "spinner", name))
                params = ctx["params"]

                def box(fs, name=name, xa=xa, ya=ya):
                    img = _open(fs, name)
                    if img is not None:
                        w, h = img.width, img.height
                        params.append(("spinner_box", f"{_fmt((gw - w) * (xa or 0))} "
                                                      f"{_fmt((gh - h) * (ya or 0))} {w} {h}"))
                self.deferred.append(box)
                tr = comp.transform_nodes.get(m.group(2)) if m.group(2) else None
                if tr is not None:
                    for tl in _lines(tr.block):
                        mm = re.match(r"linear\s+([\d.]+)\s+rotate\s+([\d.]+)", tl.text.strip())
                        if mm and float(mm.group(2)):
                            self.add(ctx, "spinner_period",
                                     float(mm.group(1)) * 360.0 / float(mm.group(2)))
                continue
            text = next((k for k in kids if k.text.strip().startswith("text ")), None)
            at = _prop(l, "at")
            if text is None:
                continue
            sm = rpy.STRING_START.search(text.text)
            if not sm:
                continue
            lx = rpy.Lexer(text, text.text)
            lx.pos = sm.start()
            src = lx.string()
            words = rpy.dialogue_text(src)[0] if src else ""
            fades = self.fades(comp.transform_nodes.get(at)) if at else (0, 0, -1, -1)
            if isinstance(xp, float):      # a fraction of the screen
                x = xp * gw
            elif isinstance(xp, int):
                x = xp
            else:
                x = (xa or 0.0) * gw
            y = (ya if isinstance(ya, (int, float)) else 0) * gh
            self.add(ctx, "caption", f"{' '.join(_fmt(v) for v in fades)}\t{_fmt(x)} {_fmt(y)}\t{words}")

    @staticmethod
    def fades(tr):
        """Fade-in and fade-out times of an alpha-only ATL program:
        (in0, in1, out0, out1), out0 = -1 when it stays."""
        t, alpha, out = 0.0, 1.0, [0.0, 0.0, -1.0, -1.0]
        if tr is None:
            return tuple(out)
        for l in _lines(tr.block):
            s = l.text.strip()
            m = re.match(r"alpha\s+([\d.]+)$", s)
            if m:
                alpha = float(m.group(1))
                continue
            m = re.match(r"pause\s+([\d.]+)$", s)
            if m:
                t += float(m.group(1))
                continue
            m = re.match(r"(?:linear|ease|easein|easeout)\s+([\d.]+)\s+alpha\s+([\d.]+)$", s)
            if m:
                d, a = float(m.group(1)), float(m.group(2))
                if a > alpha:
                    out[0], out[1] = t, t + d
                elif a < alpha:
                    out[2], out[3] = t, t + d
                t += d
                alpha = a
        return tuple(out)

    # -- after compiling --------------------------------------------------

    def prepare_assets(self, fs):
        """Work that needs the game's files (crop boxes, picture sizes)."""
        for fn in self.deferred:
            fn(fs)
        self.deferred = []

    def section(self, s):
        """game.bin's PORT section (see docs/FORMAT.md)."""
        import struct
        out = bytearray(struct.pack("<I", len(self.entries)))
        for mech, params in self.entries:
            out += struct.pack("<II", s(mech), len(params))
            for k, v in params:
                out += struct.pack("<II", s(k), s(v))
        return bytes(out)


def rpy_dotted(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = rpy_dotted(node.value)
        return f"{base}.{node.attr}" if base else None
    return None


def _fmt(v):
    if isinstance(v, bool):
        return "1" if v else "0"
    if isinstance(v, float):
        return f"{v:.6g}"
    return str(v)


def _open(fs, src):
    """A picture by file path or Ren'Py image name (as an auto image)."""
    from io import BytesIO
    from PIL import Image
    key = fs.find(src) if src else None
    if key is None and src:
        want = " ".join(src.lower().split())
        for k in fs.keys():
            if k.startswith("images/") and " ".join(
                    os.path.splitext(os.path.basename(k))[0].lower().split()) == want:
                key = k
                break
    if key is None:
        return None
    try:
        img = Image.open(BytesIO(fs.read(key)))
        img.load()
        return img.convert("RGBA")
    except OSError:
        return None

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
MECHANICS = ("lockpick", "swing_timing", "instrument", "captions", "outcome", "loglist",
             "free_roam", "topics", "shop")
_SETVAR = re.compile(r"SetVariable\(\s*[\"'](\w+)[\"']\s*,\s*([^),]+)\)")


def _adapter(game_id):
    path = os.path.join(ADAPTER_DIR, f"{game_id}.json")
    if game_id and os.path.isfile(path):
        with open(path) as f:
            return json.load(f)
    return {}


def load_spec(game_id, cfg):
    """The screen -> entry map for a game: its adapter, then vn3ds.json."""
    spec = dict(_adapter(game_id).get("minigames", {}))
    spec.update(cfg.get("minigames", {}) or {})
    return {k: v for k, v in spec.items() if isinstance(v, dict) and v.get("mechanic")}


def load_overlays(game_id, cfg):
    """The screen -> overlay map (`show screen` launchers): adapter, then vn3ds.json."""
    spec = dict(_adapter(game_id).get("overlays", {}))
    spec.update(cfg.get("overlays", {}) or {})
    return {k: v for k, v in spec.items() if isinstance(v, dict)}


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
    def __init__(self, spec, files, warn, overlays=None):
        self.spec = spec
        self.overlays = overlays or {}
        self.overlay_entry = {}    # overlay screen -> its loglist entry
        self.outcomes = []         # (screen, how the options were found, [labels]) for the report
        self.after_call = _results_tested_after_calls(files)
        self.warn = warn
        self.entries = []          # [(mechanic, [(key, value)])]
        self.deferred = []         # callables(fs) run by prepare_assets
        # `$ name = Something(...)` anywhere in the story: the displayables
        # passed to screens.
        self.assignments = {}
        self.defaults = {}         # `default x = ...` anywhere, even inside a label
        # free roam (freeroam.py): its screens, the screens that just `use`
        # one, and the loop's code once it is compiled
        from . import freeroam
        self.free = {k: v for k, v in spec.items()
                     if v.get("mechanic") in ("free_roam", "topics", "shop")}
        self.free_wrappers = freeroam.wrappers(files, self.free) if self.free else {}
        self.free_files = files
        self.free_done = set()
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
        return screen in self.spec or screen in self.free_wrappers

    # -- compiling ------------------------------------------------------

    def build_entry(self, comp, n, cfg, mech=None):
        """Builds the PORT entry for screen n.name as mechanic `mech` (default
        the adapter's) and returns its context (ctx["idx"]: the entry)."""
        mech = mech or cfg["mechanic"]
        if mech not in MECHANICS:
            raise ValueError(f"adapter for screen {n.name}: unknown mechanic '{mech}'")
        body = comp.screen_bodies.get(n.name)
        if body is None:
            raise ValueError(f"adapter names screen {n.name}, which the scripts don't define")
        idx = len(self.entries)
        params = []
        ctx = dict(comp=comp, n=n, cfg=cfg, body=body, idx=idx, params=params,
                   ev=_Eval(comp.constants), jump=None, sets=[])
        self.entries.append((mech, params))   # reserved now: builders may add entries
        getattr(self, "c_" + mech)(ctx)
        if getattr(n, "with_", None):   # the screen's own transition: the game fades in over it
            tid = comp.transition(n.with_, n.line)
            if tid >= 0:
                typ, _, _, ta, tb, tc, _ = comp.transitions[tid]
                self.add(ctx, "fade_in", ta + tb + tc if typ == 2 else ta)
        return ctx

    def compile_call(self, comp, n):
        if n.name in self.free or n.name in self.free_wrappers:
            self.compile_free_roam(comp, n)
            return
        cfg = self.spec[n.name]
        ctx = self.build_entry(comp, n, cfg)
        idx, mech = ctx["idx"], cfg["mechanic"]
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

    def compile_free_roam(self, comp, n):
        """`call screen room(...)`: set the room, then the free roam loop
        (compiled the first time, see freeroam.py)."""
        from . import freeroam
        screen, args = n.name, getattr(n, "args", None)
        if screen in self.free_wrappers:
            screen, args = self.free_wrappers[screen]
        cfg = self.free[screen]
        if cfg["mechanic"] == "topics":
            return self.compile_topics(comp, n, screen, cfg, args)
        if cfg["mechanic"] == "shop":
            return self.compile_shop(comp, n, screen, cfg)
        room = freeroam.room_arg(args)
        room_var = cfg.get("room", "current_room")
        if room and room != room_var:
            comp.c_python(f"{room_var} = {room}", n.line)
        comp.warn_once(f"freeroam:{n.name}", n.line,
                       f"call screen {n.name} is free roam: each room's hotspots and the rooms "
                       f"to walk to are choices")
        loop = comp.label_ref(freeroam.LOOP)
        comp.code.op("JMP")
        comp.code.ref(loop)
        if screen in self.free_done:
            return
        self.free_done.add(screen)
        labels = {x.name for nodes in self.free_files for x in rpy.iter_nodes(nodes)
                  if isinstance(x, rpy.Label)}
        text = freeroam.generate(cfg, self.tables(), labels, comp.warn, n.line)
        if text is None:   # (the jump above still needs its label)
            text = f"label {freeroam.LOOP}:\n    \"The rooms can't be shown on the 3DS.\"\n    return\n"
        nodes = rpy.parse_file(text, f"<free roam {screen}>")
        keep = comp.global_label   # (the loop is compiled in the middle of a label)
        comp.c_block(nodes)
        comp.global_label = keep

    def tables(self):
        """The game's init-python tables, with objects of its simple classes."""
        if getattr(self, "_tables", None) is None:
            from .pyinline import Inliner
            self._tables = Inliner(self.free_files).t
        return self._tables

    def compile_shop(self, comp, n, screen, cfg):
        """`call screen gift_menu`: a menu of what can be bought (called: its
        "Go back" carries on after the call screen statement)."""
        from . import freeroam
        comp.warn_once(f"shop:{n.name}", n.line,
                       f"call screen {n.name} is a shop: what can be bought is a choice")
        comp.code.op("CALL")
        comp.code.ref(comp.label_ref(freeroam.SHOP + screen))
        if ("shop", screen) in self.free_done:
            return
        self.free_done.add(("shop", screen))
        labels = {x.name for nodes in self.free_files for x in rpy.iter_nodes(nodes)
                  if isinstance(x, rpy.Label)}
        text = freeroam.generate_shop(cfg, self.tables(), labels,
                                      comp.warn, n.line, screen) or \
            f"label {freeroam.SHOP}{screen}:\n    return\n"
        from .compiler import Ref
        end = Ref()   # (compiled in place: jump over it)
        comp.code.op("JMP")
        comp.code.ref(end)
        keep = comp.global_label
        comp.c_block(rpy.parse_file(text, f"<shop {screen}>"))
        comp.global_label = keep
        comp.code.mark(end)

    def compile_topics(self, comp, n, screen, cfg, args):
        """`call screen robin_interact("livingroom", "day", start_page=...)`:
        that room's talk menu (freeroam.generate_topics), compiled the first
        time it is needed. Without literal room and time: an outcome card."""
        from . import freeroam
        try:
            call = ast.parse("f" + (args or "()"), mode="eval").body
            pos = [ast.literal_eval(a) for a in call.args[:2]]
            kw = {k.arg: ast.literal_eval(k.value) for k in call.keywords if k.arg == "start_page"}
        except (SyntaxError, ValueError):
            pos, kw = [], {}
        roam = next((c for c in self.free.values() if c["mechanic"] == "free_roam"), None)
        if len(pos) < 2 or not all(isinstance(p, str) for p in pos) or roam is None:
            return self.compile_outcome(comp, n)
        rid, slot = pos
        page = kw.get("start_page") if kw.get("start_page") not in (None, "main") else None
        comp.warn_once(f"topics:{n.name}", n.line,
                       f"call screen {n.name} is a talk menu: its pages and topics are choices")
        key = (screen, rid, slot)
        comp.code.op("JMP")
        comp.code.ref(comp.label_ref(freeroam.topics_label(rid, slot, page)))
        if key in self.free_done:
            return
        self.free_done.add(key)
        labels = {x.name for nodes in self.free_files for x in rpy.iter_nodes(nodes)
                  if isinstance(x, rpy.Label)}
        text = freeroam.generate_topics(cfg, roam, self.tables(), labels,
                                        comp.warn, n.line, rid, slot)
        if text is None:
            text = f"label {freeroam.topics_label(rid, slot)}:\n    jump {freeroam.LOOP}\n"
        if page and f"label {freeroam.topics_label(rid, slot, page)}:" not in text:
            text += f"label {freeroam.topics_label(rid, slot, page)}:\n    jump {freeroam.LOOP}\n"
        keep = comp.global_label
        comp.c_block(rpy.parse_file(text, f"<talk menu {rid} {slot}>"))
        comp.global_label = keep

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
                for var, val in _SETVAR.findall(m.group(2)):   # set when it plays to the end
                    self.add(ctx, "set", f"{var}={val.strip()}")
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

    # -- outcome cards: minigames nothing can play ---------------------------

    def compile_outcome(self, comp, n):
        """`call screen X` of a custom screen with no adapter and no buttons
        to turn into choices: a card says the minigame can't be played on the
        3DS and the player picks how it went. The options are the results the
        screen can produce, as far as they can be read from the scripts:
          - values it returns (`Return(True)`, `Return("won")`) and labels it
            jumps to (`Jump("win")`, also from timers);
          - what the script tests `_return` against right after the call
            (`if _return:`, `if _return == "won":`, `if _return >= 3:`);
          - with neither, one "Continue" (the story goes on as the original
            would after the screen closes).
        The chosen option sets _return or takes the jump; the card's score
        is the option's index."""
        body = comp.screen_bodies.get(n.name) or []
        text = "\n".join(l.text for l in _lines(body))
        values, jumps = [], []
        for m in re.finditer(r"\bReturn\(\s*([^()]*?)\s*\)", text):
            try:
                v = ast.literal_eval(m.group(1)) if m.group(1) else None
            except (ValueError, SyntaxError):
                continue
            if isinstance(v, (bool, int, float, str)) and v not in values:
                values.append(v)
        for m in _JUMP.finditer(text):
            t = m.group(1) or m.group(2)
            if t not in jumps:
                jumps.append(t)
        how = []
        if values or jumps:
            how.append("the screen's Return/Jump actions")
        tested = self.after_call.get(n.name, [])
        for v in tested:
            if v not in values:
                values.append(v)
        if tested:
            how.append("the tests of _return after the call")
        opts = _outcome_options(values, jumps)
        if not opts:
            opts = [("Continue", None, None)]
            how.append("nothing to choose: one Continue")
        opts = opts[:6]
        idx = len(self.entries)
        title = re.sub(r"[_]+", " ", n.name).strip()
        title = title[:1].upper() + title[1:]
        params = [("title", title),
                  ("text", "This minigame can't be played on the 3DS." +
                   (" How did it go?" if len(opts) > 1 else ""))]
        params += [("option", label) for label, _, _ in opts]
        self.entries.append(("outcome", params))
        self.outcomes.append((n.name, ", ".join(how), [o[0] for o in opts]))
        comp.warn_once(f"outcome:{n.name}", n.line,
                       f"call screen {n.name} is a minigame vn3ds can't play: a card lets the "
                       f"player choose the outcome ({' / '.join(o[0] for o in opts)})")
        from .compiler import Ref
        code = comp.code
        code.op("PUSH_STR")
        code.u32(comp.s(f"@{idx}"))
        code.op("MINIGAME")
        code.op("STORE")
        code.u32(comp.var("_vn3ds_outcome"))
        end = Ref()
        for k, (label, kind, val) in enumerate(opts):
            nxt = Ref()
            code.op("LOAD")
            code.u32(comp.var("_vn3ds_outcome"))
            code.op("PUSH_NUM")
            code.f64(float(k))
            code.op("EQ")
            code.op("JZ")
            code.ref(nxt)
            if kind == "return":
                comp.c_expr(repr(val), n.line)
                code.op("STORE")
                code.u32(comp.var("_return"))
            elif kind == "jump":
                code.op("JMP")
                code.ref(comp.label_ref(comp.qualify(val, n.line)))
            code.op("JMP")
            code.ref(end)
            code.mark(nxt)
        code.mark(end)

    def c_outcome(self, ctx):   # (built by compile_outcome)
        pass

    # -- overlays: persistent buttons from `show screen` -----------------------

    def handles_overlay(self, screen):
        return screen in self.overlays

    def compile_overlay(self, comp, n, show):
        """`show screen X` / `hide screen X` of an overlay the adapter names:
        the story variable _vn3ds_hud holds the shown overlay's entry (the
        engine draws its button on the bottom screen while it is set)."""
        code = comp.code
        if show:
            idx = self.overlay_entry.get(n.name)
            if idx is None:
                idx = self.overlay_entry[n.name] = self.build_overlay(comp, n)
            code.op("PUSH_STR")
            code.u32(comp.s(f"@{idx}"))
        else:
            code.op("PUSH_STR")
            code.u32(comp.s(""))
        code.op("STORE")
        code.u32(comp.var("_vn3ds_hud"))

    def build_overlay(self, comp, n):
        cfg = self.overlays[n.name]
        kind = cfg.get("kind", "loglist")
        if kind != "loglist":
            raise ValueError(f"overlay {n.name}: unknown kind '{kind}'")
        list_screen = cfg.get("list")
        body = comp.screen_bodies.get(list_screen)
        if body is None:
            raise ValueError(f"overlay {n.name}: no list screen '{list_screen}' in the scripts")
        idx = len(self.entries)
        params = [("button", cfg.get("button", "Extras")),
                  ("title", cfg.get("title", cfg.get("button", "Extras")))]
        self.entries.append(("loglist", params))
        base = cfg.get("item_label", "Log")
        k = 0
        for cond, action in _buttons(body):
            shown = [x for x in re.findall(r"Show\(\s*[\"'](\w+)[\"']", action) if x != n.name]
            if not shown or shown[0] not in comp.screen_bodies:
                continue
            k += 1
            target = shown[0]
            sub = type(n)(n.line, name=target, with_=None, args=None)
            ctx = self.build_entry(comp, sub, {"mechanic": "captions"}, "captions")
            play = re.search(r"Play\(\s*[\"']\w+[\"']\s*,\s*[\"']([^\"']+)[\"']", action)
            if play:
                self.sound(ctx, "loop_recording", play.group(1))
            num = re.search(r"(\d+|last)$", target)
            label = f"{base} {num.group(1)}" if num and num.group(1) != "last" else \
                f"Last {base.lower()}" if num else f"{base} {k}"
            params.append(("item", f"{ctx['idx']}\t{cond}\t{label}"))
        comp.warn_once(f"overlay:{n.name}", n.line,
                       f"show screen {n.name} becomes a \"{cfg.get('button', 'Extras')}\" button "
                       f"on the bottom screen ({k} items)")
        return idx

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


def _buttons(body, cond=""):
    """(condition, action source) of each button in a screen, with the
    condition of an enclosing `if name:` (a plain variable) or ""."""
    for l in body:
        t = l.text.strip()
        m = re.match(r"if\s+(\w+)\s*:$", t)
        if m:
            yield from _buttons(l.block, m.group(1))
            continue
        if re.match(r"(imagebutton|textbutton|button|hotspot)\b", t):
            src = " ".join(x.text.strip() for x in [l] + list(_lines(l.block)))
            m = re.search(r"\baction\s+(.+)$", src)
            if m:
                yield cond, m.group(1)
            continue
        yield from _buttons(l.block, cond)


def _results_tested_after_calls(files):
    """screen -> values the script compares _return with in the statements
    right after `call screen <screen>` (True/False for a plain test)."""
    out = {}

    def tested(src):
        try:
            tree = ast.parse(src, mode="eval")
        except SyntaxError:
            return []
        vals = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Compare) and isinstance(node.left, ast.Name) and \
                    node.left.id == "_return":
                for op, c in zip(node.ops, node.comparators):
                    if isinstance(c, ast.Constant) and isinstance(c.value, (bool, int, float, str)):
                        if isinstance(op, (ast.Eq, ast.NotEq, ast.Is, ast.IsNot)):
                            vals.append(c.value)
                        elif isinstance(c.value, (int, float)) and not isinstance(c.value, bool):
                            # a threshold: one value on each side of it
                            lo = c.value - 1 if isinstance(op, (ast.GtE, ast.Lt)) else c.value
                            hi = c.value if isinstance(op, (ast.GtE, ast.Lt)) else c.value + 1
                            vals += [hi, lo]
        if not vals and re.search(r"\b_return\b", src):
            vals = [True, False]
        return vals

    def walk(block):
        for i, n in enumerate(block):
            if isinstance(n, rpy.CallScreen):
                for after in block[i + 1:i + 4]:
                    if isinstance(after, rpy.If):
                        for cond, _ in after.branches:
                            for v in tested(cond):
                                if v not in out.setdefault(n.name, []):
                                    out[n.name].append(v)
                        break
                    if isinstance(after, (rpy.Say, rpy.Menu, rpy.CallScreen, rpy.Jump)):
                        break
            for attr in ("block", "else_"):
                sub = getattr(n, attr, None)
                if isinstance(sub, list):
                    walk(sub)
            for br in getattr(n, "branches", None) or ():
                walk(br[1])
            for item in getattr(n, "items", None) or ():
                if isinstance(item, tuple) and len(item) == 3 and isinstance(item[2], list):
                    walk(item[2])
    for nodes in files:
        walk(nodes)
    return out


_GOOD = re.compile(r"win|won|succe|pass|good|right|correct|clear|open|unlock", re.I)
_BAD = re.compile(r"lose|lost|fail|bad|wrong|dead|death|over|miss", re.I)


def _outcome_options(values, jumps):
    """[(label, "return"|"jump", value)], the good outcome first."""
    opts = []
    bools = [v for v in values if isinstance(v, bool)]
    nums = sorted({v for v in values if isinstance(v, (int, float)) and not isinstance(v, bool)},
                  reverse=True)
    strs = [v for v in values if isinstance(v, str)]
    for v in sorted(set(bools), reverse=True):
        opts.append(("It went well" if v else "It didn't go well", "return", v))
    for v in nums:
        opts.append((f"Score {v:g}", "return", v))
    for v in strs:
        opts.append((_human(v), "return", v))
    for t in jumps:
        opts.append((_human(t), "jump", t))
    good = [o for o in opts if o[2] is True or (isinstance(o[2], str) and _GOOD.search(o[2]))]
    rest = [o for o in opts if o not in good]
    seen, out = set(), []
    for label, kind, v in good + rest:
        if label in seen and isinstance(v, str):   # two good jumps: name them
            label = _human(v, plain=True)
        if label in seen:
            continue
        seen.add(label)
        out.append((label, kind, v))
    return out


def _human(name, plain=False):
    """'lock_won2' -> 'Lock won 2'; a win/lose name reads as the outcome."""
    if not plain and _GOOD.search(name) and not _BAD.search(name):
        return "It went well"
    if not plain and _BAD.search(name) and not _GOOD.search(name):
        return "It didn't go well"
    t = re.sub(r"[_.]+", " ", name)
    t = re.sub(r"(?<=[a-z])(?=\d)|(?<=\d)(?=[a-z])", " ", t).strip()
    return t[:1].upper() + t[1:]


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

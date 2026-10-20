"""Compile parsed Ren'Py script nodes into vn3ds bytecode and tables.

See docs/FORMAT.md for the binary layout this produces.
"""

import ast
import math
import os
import warnings
import re
import struct

from . import rpy

# Game scripts are full of regexes like "\s" in plain strings; Python's
# SyntaxWarning about them is noise here.
warnings.filterwarnings("ignore", category=SyntaxWarning)

INT32_MIN = -0x80000000
NONE = 0xFFFFFFFF

OP = dict(
    NOP=0x00, END=0x01, JMP=0x02, JZ=0x03, JNZ=0x04, CALL=0x05, RET=0x06,
    POP=0x07, DUP=0x08,
    PUSH_NUM=0x10, PUSH_STR=0x11, PUSH_NONE=0x12, PUSH_TRUE=0x13,
    PUSH_FALSE=0x14, LOAD=0x15, STORE=0x16,
    ADD=0x20, SUB=0x21, MUL=0x22, DIV=0x23, FLOORDIV=0x24, MOD=0x25, POW=0x26,
    NEG=0x27, NOT=0x28,
    EQ=0x2A, NE=0x2B, LT=0x2C, LE=0x2D, GT=0x2E, GE=0x2F,
    CALLF=0x30, IN=0x31,
    SAY=0x40, MENU_BEGIN=0x41, MENU_ITEM=0x42, MENU=0x43, PAUSE=0x44,
    SCENE=0x45, SHOW=0x46, HIDE=0x47, WITH=0x48, SHOW_ATTR=0x49,
    PLAY=0x50, STOP=0x51, WINDOW=0x52, MINIGAME=0x53,
)

BINOPS = {ast.Add: "ADD", ast.Sub: "SUB", ast.Mult: "MUL", ast.Div: "DIV",
          ast.FloorDiv: "FLOORDIV", ast.Mod: "MOD", ast.Pow: "POW"}
CMPOPS = {ast.Eq: "EQ", ast.NotEq: "NE", ast.Lt: "LT", ast.LtE: "LE",
          ast.Gt: "GT", ast.GtE: "GE", ast.Is: "EQ", ast.IsNot: "NE"}
BUILTINS = {"renpy.random.randint": 0, "renpy.random.random": 1, "len": 2,
            "str": 3, "int": 4, "float": 5, "abs": 6, "min": 7, "max": 8,
            "round": 9, "bool": 10, "_getitem": 11, "_slice": 12,
            "_upper": 13, "_lower": 14, "_title": 15, "_strip": 16, "_capitalize": 17}
STR_METHODS = {"upper": "_upper", "lower": "_lower", "title": "_title", "strip": "_strip",
               "capitalize": "_capitalize", "lstrip": "_strip", "rstrip": "_strip"}

# Calls that only affect things the 3DS engine doesn't have.
IGNORED_CALLS = {
    "renpy.block_rollback", "renpy.fix_rollback", "renpy.checkpoint",
    "renpy.notify", "renpy.save_persistent", "renpy.restart_interaction",
    "renpy.free_memory", "renpy.choice_for_skipping", "renpy.retain_after_load",
    "renpy.suspend_rollback", "renpy.music.set_volume", "renpy.sound.set_volume",
    "renpy.music.register_channel", "renpy.start_predict", "renpy.stop_predict",
    "renpy.predict", "renpy.transition", "gui.init", "renpy.dynamic",
    "achievement.grant", "achievement.register", "renpy.vibrate",
    "_dismiss_pause", "renpy.clear_game_runtime", "renpy.effective_saving",
    "config.keymap.update", "renpy.full_restart", "renpy.quit",
}

# ATL ------------------------------------------------------------------

PROP = dict(xpos=0, ypos=1, xanchor=2, yanchor=3, xoffset=4, yoffset=5,
            xzoom=6, yzoom=7, zoom=8, alpha=9, rotate=10, zpos=11)
WARPERS = {"linear": 0, "ease": 1, "easein": 2, "easeout": 3}
STEP_SET, STEP_INTERP, STEP_PAUSE, STEP_REPEAT = 0, 1, 2, 3

ATL_PROPERTIES = {
    "xpos", "ypos", "xanchor", "yanchor", "xalign", "yalign", "align", "pos",
    "anchor", "xoffset", "yoffset", "offset", "xcenter", "ycenter",
    "xycenter", "zoom", "xzoom", "yzoom", "alpha", "rotate", "zpos",
    # accepted but ignored:
    "subpixel", "transform_anchor", "rotate_pad", "additive", "crop", "size",
    "xysize", "xsize", "ysize", "fit", "matrixcolor", "blur", "nearest",
    "around", "radius", "angle", "xpan", "ypan", "xtile", "ytile", "delay",
    "events", "corner1", "corner2", "crop_relative", "mesh", "shader",
    "perspective", "matrixtransform", "matrixanchor", "fps", "show_cancels_hide",
    "xtiles", "ytiles", "mesh_pad", "gl_depth", "zzoom", "point_to",
    "orientation", "xrotate", "yrotate", "zrotate", "maxsize",
}

BUILTIN_POSITIONS = {
    "left": [("xpos", 0.0), ("xanchor", 0.0), ("ypos", 1.0), ("yanchor", 1.0)],
    "right": [("xpos", 1.0), ("xanchor", 1.0), ("ypos", 1.0), ("yanchor", 1.0)],
    "center": [("xpos", 0.5), ("xanchor", 0.5), ("ypos", 1.0), ("yanchor", 1.0)],
    "default": [("xpos", 0.5), ("xanchor", 0.5), ("ypos", 1.0), ("yanchor", 1.0)],
    "truecenter": [("xpos", 0.5), ("xanchor", 0.5), ("ypos", 0.5), ("yanchor", 0.5)],
    "topleft": [("xpos", 0.0), ("xanchor", 0.0), ("ypos", 0.0), ("yanchor", 0.0)],
    "topright": [("xpos", 1.0), ("xanchor", 1.0), ("ypos", 0.0), ("yanchor", 0.0)],
    "top": [("xpos", 0.5), ("xanchor", 0.5), ("ypos", 0.0), ("yanchor", 0.0)],
    "offscreenleft": [("xpos", 0.0), ("xanchor", 1.0), ("ypos", 1.0), ("yanchor", 1.0)],
    "offscreenright": [("xpos", 1.0), ("xanchor", 0.0), ("ypos", 1.0), ("yanchor", 1.0)],
    "reset": [("xpos", 0.5), ("xanchor", 0.5), ("ypos", 1.0), ("yanchor", 1.0),
              ("xoffset", 0), ("yoffset", 0), ("zoom", 1.0), ("xzoom", 1.0),
              ("yzoom", 1.0), ("alpha", 1.0), ("rotate", 0.0)],
}

# Transitions ------------------------------------------------------------

T_DISSOLVE, T_FADE, T_MOVE, T_MOVEIN, T_MOVEOUT, T_PUNCH = 1, 2, 3, 4, 5, 6
DIRS = {"left": 0, "right": 1, "top": 2, "bottom": 3}
BLACK = 0x000000FF


def _builtin_transitions():
    t = {
        "fade": (T_FADE, 0, 0, 0.5, 0.0, 0.5, BLACK),
        "dissolve": (T_DISSOLVE, 0, 0, 0.5, 0, 0, 0),
        "pixellate": (T_DISSOLVE, 0, 0, 1.0, 0, 0, 0),
        "move": (T_MOVE, 0, 0, 0.5, 0, 0, 0),
        "ease": (T_MOVE, 1, 0, 0.5, 0, 0, 0),
        "vpunch": (T_PUNCH, 0, 0, 0.275, 0, 0, 0),
        "hpunch": (T_PUNCH, 0, 1, 0.275, 0, 0, 0),
    }
    for d, n in DIRS.items():
        t["movein" + d] = (T_MOVEIN, 0, n, 0.5, 0, 0, 0)
        t["moveout" + d] = (T_MOVEOUT, 0, n, 0.5, 0, 0, 0)
        t["easein" + d] = (T_MOVEIN, 1, n, 0.5, 0, 0, 0)
        t["easeout" + d] = (T_MOVEOUT, 1, n, 0.5, 0, 0, 0)
    approximated = ["zoomin", "zoomout", "zoominout", "blinds", "squares",
                    "irisin", "irisout"]
    for d in ("left", "right", "up", "down"):
        approximated += ["wipe" + d, "slide" + d, "slideaway" + d, "push" + d]
    for name in approximated:
        t[name] = (T_DISSOLVE, 0, 0, 0.5 if name.startswith("zoom") else 1.0, 0, 0, 0)
    return t


BUILTIN_TRANSITIONS = _builtin_transitions()
APPROX_TRANSITIONS = {"pixellate", "zoomin", "zoomout", "zoominout", "blinds",
                      "squares", "irisin", "irisout"} | {
    p + d for p in ("wipe", "slide", "slideaway", "push")
    for d in ("left", "right", "up", "down")}


def parse_color(s, default=0xFFFFFFFF):
    if not isinstance(s, str):
        return default
    s = s.strip().lstrip("#")
    try:
        if len(s) in (3, 4):
            s = "".join(c * 2 for c in s)
        if len(s) == 6:
            return (int(s, 16) << 8) | 0xFF
        if len(s) == 8:
            return int(s, 16)
    except ValueError:
        pass
    return default


def dotted(node):
    """'a.b.c' for a Name/Attribute chain, else None."""
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
        return ".".join(reversed(parts))
    return None


def var_name(name):
    return name[6:] if name.startswith("store.") else name


class CompileError(Exception):
    pass


class Unsupported(Exception):
    pass


class Ref:
    __slots__ = ("addr", "name")

    def __init__(self, name=None):
        self.addr = None
        self.name = name


class Code:
    def __init__(self):
        self.b = bytearray()
        self.fixups = []

    def here(self):
        return len(self.b)

    def op(self, name):
        self.b.append(OP[name])

    def u8(self, v):
        self.b += struct.pack("<B", v & 0xFF)

    def u32(self, v):
        self.b += struct.pack("<I", v & 0xFFFFFFFF)

    def i32(self, v):
        self.b += struct.pack("<i", v)

    def f32(self, v):
        self.b += struct.pack("<f", v)

    def f64(self, v):
        self.b += struct.pack("<d", v)

    def ref(self, r):
        self.fixups.append((len(self.b), r))
        self.b += b"\0\0\0\0"

    def mark(self, r):
        r.addr = len(self.b)


class Character:
    def __init__(self, name=None, image=None, name_color=0xFFFFFFFF,
                 text_color=0xFFFFFFFF, prefix="", suffix="", kind=0):
        self.name = name
        self.image = image
        self.name_color = name_color
        self.text_color = text_color
        self.prefix = prefix
        self.suffix = suffix
        self.kind = kind

    def copy(self):
        c = Character()
        c.__dict__.update(self.__dict__)
        return c


class Absolute(float):
    """A value Ren'Py would treat as pixels (absolute(...) or an int)."""


class Compiler:
    def __init__(self, warn):
        self.warn = warn
        self.strings = {}
        self.strlist = []
        self.vars = {}
        self.code = Code()
        self.labels = {}
        self.defined_labels = {}
        self.chars = [Character(None), Character(None, kind=2)]
        self.char_by_name = {"narrator": 0, "centered": 1, "vcentered": 1}
        self.transitions = []
        self.trans_cache = {}
        self.atl_programs = []
        self.atl_cache = {}
        self.transform_nodes = {}
        self.defines = {}            # name -> (ast expr, line)
        self.constants = {}          # define/default values known at compile time
        self.image_defs = {}         # name -> ("expr", src, line) | ("atl", block, line)
        self.used_specs = {}         # spec -> first line it was used on
        self.audio_res = {}          # path -> resource index
        self.audio_names = {}        # "audio.x" style names -> path
        self.resources = []          # (kind, path)
        self.init_items = []         # (priority, seq, name, expr src, line)
        self.meta = {"title": None, "version": "", "width": None, "height": None}
        self.expr_images = 0
        self.global_label = None
        self.screens = {}
        self.screen_bgs = {}
        self.minigames = []          # ids passed to vn3ds_minigame(), in order
        self.named_audio = {}        # "minigame/tower_1" -> resource index

    # -- tables ---------------------------------------------------------

    def s(self, text):
        if text is None:
            return NONE
        idx = self.strings.get(text)
        if idx is None:
            idx = len(self.strlist)
            self.strings[text] = idx
            self.strlist.append(text)
        return idx

    def var(self, name):
        name = var_name(name)
        idx = self.vars.get(name)
        if idx is None:
            idx = len(self.vars)
            self.vars[name] = idx
        return idx

    def label_ref(self, name):
        r = self.labels.get(name)
        if r is None:
            r = self.labels[name] = Ref(name)
        return r

    def qualify(self, name, line):
        if name.startswith("."):
            if self.global_label is None:
                raise line.error(f"local label {name} outside a global label")
            return self.global_label + name
        return name

    def resource(self, kind, path):
        self.resources.append((kind, path))
        return len(self.resources) - 1

    # -- pass 1: declarations ------------------------------------------

    def collect(self, files):
        """Gather defines, defaults, images and transforms from all files."""
        seq = 0
        for nodes in files:
            stack = [(0, n) for n in nodes]
            while stack:
                prio, n = stack.pop(0)
                seq += 1
                if isinstance(n, rpy.Init):
                    stack[0:0] = [(n.priority, c) for c in n.block]
                    for c in n.block:
                        if isinstance(c, rpy.Python) and not c.init:
                            c.init = True  # `$` inside init: runs at init time
                elif isinstance(n, rpy.Screen):
                    self.screens[n.name] = n.items
                    self.screen_bgs[n.name] = n.background
                elif isinstance(n, rpy.Define):
                    self.collect_define(n, prio + n.priority, seq)
                elif isinstance(n, rpy.Default):
                    self.init_items.append((100000, seq, n.name, n.expr, n.line))
                    self.remember_constant(n.name, n.expr)
                elif isinstance(n, rpy.Image):
                    if n.name in self.image_defs:
                        pass  # later definitions win, as in Ren'Py
                    self.image_defs[n.name] = (
                        ("expr", n.expr, n.line) if n.expr is not None
                        else ("atl", n.atl, n.line))
                elif isinstance(n, rpy.Transform):
                    self.transform_nodes[n.name] = n
                elif isinstance(n, rpy.Python) and n.init:
                    self.collect_init_python(n, prio + getattr(n, "priority", 0), seq)

    def remember_constant(self, name, src):
        try:
            self.constants[name] = ast.literal_eval(src)
        except (ValueError, SyntaxError, TypeError, MemoryError, RecursionError):
            pass

    def collect_define(self, n, prio, seq):
        name, src, line = n.name, n.expr, n.line
        try:
            expr = ast.parse(src, mode="eval").body
        except SyntaxError:
            self.warn(line, f"cannot parse define {name}")
            return
        if name == "config.name":
            self.meta["title"] = self.const_str(expr)
            return
        if name == "config.version":
            self.meta["version"] = self.const_str(expr) or ""
            return
        if name == "config.speaking_attribute":
            self.meta["speaking_attribute"] = self.const_str(expr)
            return
        if name in ("config.screen_width", "config.screen_height"):
            v = self.const_value(expr)
            if isinstance(v, int):
                self.meta["width" if name.endswith("width") else "height"] = v
            return
        if name.startswith(("config.", "gui.", "build.", "style.", "_")):
            return
        if name.startswith("audio."):
            v = self.const_str(expr)
            if v:
                self.audio_names[name] = v
                self.audio_names[name[6:]] = v
            return
        if isinstance(expr, ast.Call):
            fn = dotted(expr.func)
            if fn in ("Character", "ADVCharacter", "NVLCharacter", "DynamicCharacter"):
                self.define_character(name, expr, fn, line)
                return
        self.defines[name] = (expr, line)
        v = self.const_value(expr)
        if v is not None or (isinstance(expr, ast.Constant) and expr.value is None):
            self.constants[name] = v
            if n.op == "=":
                self.init_items.append((prio, seq, name, src, line))

    def collect_init_python(self, n, prio, seq):
        m = re.search(r"gui\.init\(\s*(\d+)\s*,\s*(\d+)\s*\)", n.code)
        if m:
            self.meta["width"] = int(m.group(1))
            self.meta["height"] = int(m.group(2))
        for key in ("screen_width", "screen_height"):
            m = re.search(r"config\.%s\s*=\s*(\d+)" % key, n.code)
            if m:
                self.meta["width" if key.endswith("width") else "height"] = int(m.group(1))
        try:
            tree = ast.parse(n.code)
        except SyntaxError:
            self.warn(n.line, "cannot parse init python block")
            return
        for st in tree.body:
            if isinstance(st, ast.Assign) and len(st.targets) == 1:
                tname = dotted(st.targets[0])
                if not tname or tname.startswith(("config.", "gui.", "style.", "build.")):
                    continue
                if isinstance(st.value, ast.Call) and dotted(st.value.func) in (
                        "Character", "ADVCharacter", "NVLCharacter", "DynamicCharacter"):
                    self.define_character(tname, st.value, dotted(st.value.func), n.line)
                    continue
                v = self.const_value(st.value)
                if v is not None:
                    self.constants[tname] = v
                    self.init_items.append((prio, seq, tname, ast.unparse(st.value), n.line))
                else:
                    self.defines[tname] = (st.value, n.line)
            elif isinstance(st, (ast.FunctionDef, ast.ClassDef, ast.Import, ast.ImportFrom)):
                self.warn(n.line, "python functions/classes in init python are ignored")

    def const_value(self, expr):
        try:
            return ast.literal_eval(expr)
        except (ValueError, SyntaxError, TypeError, MemoryError, RecursionError):
            if isinstance(expr, ast.Call) and dotted(expr.func) == "_" and expr.args:
                return self.const_value(expr.args[0])
            return None

    def const_str(self, expr):
        v = self.const_value(expr)
        return v if isinstance(v, str) else None

    def define_character(self, name, call, fn, line):
        kw = {k.arg: k.value for k in call.keywords if k.arg}
        base = None
        if "kind" in kw:
            kname = dotted(kw["kind"])
            if kname == "nvl":
                base = Character(kind=1)
            elif kname in self.char_by_name:
                base = self.chars[self.char_by_name[kname]].copy()
        c = base or Character()
        if fn == "NVLCharacter":
            c.kind = 1
        if call.args:
            nm = call.args[0]
            if fn == "DynamicCharacter":
                v = self.const_str(nm)
                c.name = f"[{v}]" if v else None
            else:
                v = self.const_value(nm)
                c.name = v if isinstance(v, str) else None
        elif "name" in kw:
            c.name = self.const_str(kw["name"])
        if kw.get("dynamic") is not None and self.const_value(kw["dynamic"]) and c.name:
            c.name = f"[{c.name}]"
        for key in ("color", "who_color"):
            if key in kw:
                c.name_color = parse_color(self.const_str(kw[key]), c.name_color)
        if "what_color" in kw:
            c.text_color = parse_color(self.const_str(kw["what_color"]), c.text_color)
        if "image" in kw:
            c.image = self.const_str(kw["image"])
        if "what_prefix" in kw:
            c.prefix = self.const_str(kw["what_prefix"]) or ""
        if "what_suffix" in kw:
            c.suffix = self.const_str(kw["what_suffix"]) or ""
        if name in self.char_by_name and name not in ("centered", "vcentered"):
            self.chars[self.char_by_name[name]] = c
        else:
            self.char_by_name[name] = len(self.chars)
            self.chars.append(c)

    # -- pass 2: code ---------------------------------------------------

    def compile(self, files):
        code = self.code
        # Address 0 is an END so a broken jump target can point somewhere sane.
        code.op("END")
        self.end_stub = 0

        self.init_addr = code.here()
        for prio, seq, name, src, line in sorted(self.init_items, key=lambda t: (t[0], t[1])):
            try:
                self.c_expr(src, line)
            except Unsupported as e:
                self.warn(line, f"cannot evaluate '{name}' ({e}); it starts as None")
                code.op("PUSH_NONE")
            code.op("STORE")
            code.u32(self.var(name))
        code.op("JMP")
        code.ref(self.label_ref("start"))

        for nodes in files:
            self.global_label = None
            self.c_block(nodes, top=True)
            code.op("RET")

        if "start" not in self.defined_labels:
            raise CompileError("the game has no 'label start'")
        for pos, r in code.fixups:
            addr = r.addr
            if addr is None:
                self.warn(None, f"label '{r.name}' is never defined; jumps to it end the game")
                addr = self.end_stub
            struct.pack_into("<I", code.b, pos, addr)

    def c_block(self, nodes, top=False):
        for n in nodes:
            try:
                self.c_node(n, top)
            except Unsupported as e:
                self.warn(n.line, str(e))

    def c_node(self, n, top=False):
        code = self.code
        t = type(n)
        if t in (rpy.Define, rpy.Default, rpy.Image, rpy.Transform, rpy.Init, rpy.Pass,
                 rpy.Screen):
            return
        if t is rpy.Python:
            if not n.init:
                self.c_python(n.code, n.line)
            return
        if t is rpy.Label:
            name = self.qualify(n.name, n.line)
            if not n.name.startswith("."):
                self.global_label = name
            if name in self.defined_labels:
                raise n.line.error(f"label {name} is defined twice")
            self.defined_labels[name] = n.line
            code.mark(self.label_ref(name))
            self.c_block(n.block)
            return
        if t is rpy.Say:
            self.c_say(n)
            return
        if t in (rpy.Show, rpy.Scene):
            self.c_show(n, t is rpy.Scene)
            return
        if t is rpy.Hide:
            if n.with_:
                self.c_with("None", n.line)
            code.op("HIDE")
            code.u32(self.s(n.tag))
            if n.with_:
                self.c_with(n.with_, n.line)
            return
        if t is rpy.With:
            self.c_with(n.expr, n.line)
            return
        if t is rpy.Jump:
            self.c_jump(n, "JMP")
            return
        if t is rpy.Call:
            self.c_jump(n, "CALL")
            return
        if t is rpy.Return:
            if n.expr:
                self.c_expr(n.expr, n.line)
                code.op("STORE")
                code.u32(self.var("_return"))
            code.op("RET")
            return
        if t is rpy.Menu:
            self.c_menu(n)
            return
        if t is rpy.If:
            end = Ref()
            for cond, block in n.branches:
                nxt = Ref()
                self.c_expr(cond, n.line)
                code.op("JZ")
                code.ref(nxt)
                self.c_block(block)
                code.op("JMP")
                code.ref(end)
                code.mark(nxt)
            if n.else_:
                self.c_block(n.else_)
            code.mark(end)
            return
        if t is rpy.While:
            top_ref, end = Ref(), Ref()
            code.mark(top_ref)
            self.c_expr(n.cond, n.line)
            code.op("JZ")
            code.ref(end)
            self.c_block(n.block)
            code.op("JMP")
            code.ref(top_ref)
            code.mark(end)
            return
        if t is rpy.Pause:
            if n.expr:
                self.c_expr(n.expr, n.line)
                code.op("PAUSE")
                code.u8(1)
            else:
                code.op("PAUSE")
                code.u8(0)
            return
        if t is rpy.Play:
            self.c_play(n)
            return
        if t is rpy.Stop:
            code.op("STOP")
            code.u8(n.channel)
            code.f32(n.fadeout or 0.0)
            return
        if t is rpy.Window:
            code.op("WINDOW")
            code.u8(n.mode)
            return
        if t is rpy.Screen:
            return
        if t is rpy.CallScreen:
            self.c_call_screen(n)
            return
        if t is rpy.Unsupported:
            if n.what.startswith("unparseable"):
                raise Unsupported(f"{n.what}; skipped")
            raise Unsupported(f"{n.what} is not supported and was skipped")
        raise Unsupported(f"cannot compile {t.__name__}")

    # -- dialogue -------------------------------------------------------

    def resolve_who(self, n):
        """Returns (char index, who string or None, flags)."""
        if n.who is None:
            return 0, None, 0
        if n.who_is_string:
            return 0, n.who, 0
        if n.who == "extend":
            return -2, None, 1
        idx = self.char_by_name.get(n.who)
        if idx is None:
            # A name defined as a plain string variable, or a typo.
            v = self.constants.get(n.who)
            if isinstance(v, str):
                return 0, v, 0
            self.warn(n.line, f"unknown character '{n.who}', using it as a name")
            return 0, n.who, 0
        return idx, None, 0

    def c_say_attrs(self, idx, n):
        if not n.attrs or idx < 0:
            return
        img = self.chars[idx].image
        if not img:
            self.warn(n.line, f"character '{n.who}' has no image= so attributes are ignored")
            return
        spec = img + " " + " ".join(n.attrs)
        self.used_specs.setdefault(spec, n.line)
        self.code.op("SHOW_ATTR")
        self.code.u32(self.s(spec))

    def c_say(self, n):
        code = self.code
        idx, who, flags = self.resolve_who(n)
        if "nw" in n.flags:
            flags |= 2
        self.c_say_attrs(idx, n)
        if n.with_:
            self.c_with("None", n.line)
            self.c_with(n.with_, n.line)
        code.op("SAY")
        code.i32(idx)
        code.u32(self.s(who))
        code.u32(self.s(n.what))
        code.u8(flags)

    def c_menu(self, n):
        code = self.code
        if n.label:
            name = self.qualify(n.label, n.line)
            self.defined_labels[name] = n.line
            code.mark(self.label_ref(name))
        if getattr(n, "with_", None):
            self.c_with("None", n.line)
            self.c_with(n.with_, n.line)
        code.op("MENU_BEGIN")
        refs = []
        for text, cond, _ in n.items:
            r = Ref()
            refs.append(r)
            if cond:
                self.c_expr(cond, n.line)
            else:
                code.op("PUSH_TRUE")
            code.op("MENU_ITEM")
            code.u32(self.s(text))
            code.ref(r)
        idx, who, what = 0, None, None
        if n.caption is not None:
            idx, who, _ = self.resolve_who(n.caption)
            self.c_say_attrs(idx, n.caption)
            what = n.caption.what
        code.op("MENU")
        code.i32(max(idx, 0))
        code.u32(self.s(who))
        code.u32(self.s(what))
        end = Ref()
        code.op("JMP")
        code.ref(end)
        for r, (_, _, block) in zip(refs, n.items):
            code.mark(r)
            self.c_block(block)
            code.op("JMP")
            code.ref(end)
        code.mark(end)

    def c_call_screen(self, n):
        """A navigation screen (buttons that Jump/Call/Return) becomes a menu."""
        code = self.code
        items = self.screens.get(n.name)
        if not items:
            raise Unsupported(f"call screen {n.name} has no Jump/Call buttons vn3ds can turn "
                              "into choices; skipped")
        self.warn_once(f"screenmenu:{n.name}", n.line,
                       f"call screen {n.name} is shown as a choice menu")
        bg = self.screen_bgs.get(n.name)
        if n.with_:
            self.c_with("None", n.line)
        if bg:
            # Show the map itself behind the choices, as a picture over the scene.
            spec = bg if not bg.lower().endswith((".png", ".jpg", ".jpeg", ".webp")) else None
            if spec is None:
                self.expr_images += 1
                spec = f"_screen_{n.name} _bg"
                self.image_defs[spec] = ("expr", repr(bg), n.line)
            self.used_specs.setdefault(spec, n.line)
            code.op("SHOW")
            code.u32(self.s(spec))
            code.u32(self.s("_screen_bg"))
            code.i32(50)
            code.u32(NONE)
            code.u8(0)
        if n.with_:
            self.c_with(n.with_, n.line)
        seen, entries = set(), []
        for conds, kind, target, text, pos in items:
            if target is None or (conds, kind, target) in seen:
                continue
            seen.add((conds, kind, target))
            entries.append((conds, kind, target, text, pos))
        names = self.nav_names(n.name) or sorted({t for _, k, t, _, _ in entries if k != "Return"})
        code.op("MENU_BEGIN")
        refs = []
        for conds, kind, target, text, pos in entries:
            r = Ref()
            refs.append(r)
            if conds:
                self.c_expr(" and ".join(f"({c})" for c in conds), n.line)
            else:
                code.op("PUSH_TRUE")
            code.op("MENU_ITEM")
            code.u32(self.s(text or self.choice_label(kind, target, pos, names)))
            code.ref(r)
        code.op("MENU")
        code.i32(0)
        code.u32(NONE)
        code.u32(NONE)
        end = Ref()
        code.op("JMP")
        code.ref(end)
        for r, (conds, kind, target, text, pos) in zip(refs, entries):
            code.mark(r)
            if bg:
                code.op("HIDE")
                code.u32(self.s("_screen_bg"))
            if kind == "Jump":
                code.op("JMP")
                code.ref(self.label_ref(self.qualify(target, n.line)))
                continue
            if kind == "Call":
                code.op("CALL")
                code.ref(self.label_ref(self.qualify(target, n.line)))
            else:
                try:
                    self.c_expr(target, n.line)
                except Unsupported:
                    code.op("PUSH_NONE")
                code.op("STORE")
                code.u32(self.var("_return"))
            code.op("JMP")
            code.ref(end)
        code.mark(end)

    def nav_names(self, screen):
        """Jump targets of every navigation screen linked to this one by a shared
        target. A free-roam map is usually many two-exit screens ("halls",
        "livings"), so naming patterns only show across the whole map."""
        if not hasattr(self, "_nav_groups"):
            targets = {name: {t for _, k, t, _, _ in items if t and k != "Return"}
                       for name, items in self.screens.items()}
            parent = {name: name for name in targets}

            def find(x):
                while parent[x] != x:
                    parent[x] = parent[parent[x]]
                    x = parent[x]
                return x
            owner = {}
            for name, ts in targets.items():
                for t in ts:
                    if t in owner:
                        parent[find(name)] = find(owner[t])
                    else:
                        owner[t] = name
            groups = {}
            for name, ts in targets.items():
                groups.setdefault(find(name), set()).update(ts)
            self._nav_groups = {name: sorted(groups[find(name)]) for name in targets}
        return self._nav_groups.get(screen)

    def choice_label(self, kind, target, pos, names):
        """Readable text for a button that has none, e.g. 'Piaget (top left)'."""
        if kind == "Return":
            base = "Continue"
        else:
            base = target
            if len(names) > 1:
                prefix = os.path.commonprefix(names)
                rest = target[len(prefix):].strip("_ .0123456789")
                if len(prefix) >= 3 and rest:
                    base = rest
                # a suffix every target shares ("hallwayl", "bedrooml") is noise
                suffix = os.path.commonprefix([x[::-1] for x in names])[::-1]
                if (len(names) >= 3 and suffix and len(suffix) <= 3 and len(base) > len(suffix) + 2
                        and base.endswith(suffix)):
                    base = base[: -len(suffix)]
            base = re.sub(r"[_.]+", " ", base)
            base = re.sub(r"(?<=[a-z])(?=\d)|(?<=\d)(?=[a-z])", " ", base).strip()
            base = base[:1].upper() + base[1:]
        if pos:
            gw = self.meta.get("width") or 1920
            gh = self.meta.get("height") or 1080
            if pos[0] == "frac":
                fx, fy = pos[1], pos[2]
            else:
                fx, fy = pos[1] / gw, pos[2] / gh
            col = "left" if fx < 0.34 else ("right" if fx > 0.66 else "")
            row = "top" if fy < 0.34 else ("bottom" if fy > 0.66 else "")
            where = " ".join(w for w in (row, col) if w) or "centre"
            return f"{base} ({where})"
        return base

    def c_jump(self, n, op):
        target = n.target
        if n.expression:
            try:
                target = ast.literal_eval(target)
            except (ValueError, SyntaxError):
                raise Unsupported(f"{op.lower()} expression with a computed label")
            if not isinstance(target, str):
                raise Unsupported("jump expression needs a string")
        self.code.op(op)
        self.code.ref(self.label_ref(self.qualify(target, n.line)))

    # -- images ---------------------------------------------------------

    def c_show(self, n, scene):
        code = self.code
        if n.with_:
            self.c_with("None", n.line)
        spec = n.spec
        as_tag = n.as_
        if n.expression is not None:
            try:
                val = ast.literal_eval(n.expression)
            except (ValueError, SyntaxError):
                val = None
            if not isinstance(val, str):
                raise Unsupported(f"show expression {n.expression} is not a constant")
            self.expr_images += 1
            tag = as_tag or f"_expr{self.expr_images}"
            spec = f"{tag} _e{self.expr_images}"
            self.image_defs[spec] = ("expr", n.expression, n.line)
            as_tag = tag
        if n.onlayer not in (None, "master"):
            self.warn(n.line, f"layer '{n.onlayer}' is drawn on the master layer")
        if spec:
            self.used_specs.setdefault(spec, n.line)
        atl = []
        for e in n.at:
            atl += self.transform_expr(e, n.line)
        if n.atl:
            atl += self.compile_atl(n.atl, {}, n.line)
        zorder = INT32_MIN
        if n.zorder is not None:
            try:
                zorder = int(self.eval_const(n.zorder, {}))
            except (Unsupported, TypeError, ValueError):
                self.warn(n.line, "zorder must be a constant number")
        code.op("SCENE" if scene else "SHOW")
        code.u32(self.s(spec))
        code.u32(self.s(as_tag))
        code.i32(zorder)
        code.u32(self.s(n.behind[0] if n.behind else None))
        atl = atl[:8]
        code.u8(len(atl))
        for a in atl:
            code.i32(a)
        if n.with_:
            self.c_with(n.with_, n.line)

    # -- transforms / ATL -------------------------------------------------

    def transform_expr(self, src, line):
        """Program ids for an `at` clause entry."""
        key = src.strip()
        if key in self.atl_cache:
            return self.atl_cache[key]
        try:
            expr = ast.parse(key, mode="eval").body
        except SyntaxError:
            self.warn(line, f"cannot parse transform '{src}'")
            return []
        progs = self.transform_ast(expr, line)
        self.atl_cache[key] = progs
        return progs

    def transform_ast(self, expr, line, depth=0):
        if depth > 8:
            return []
        name = dotted(expr)
        if name is not None:
            if name in self.transform_nodes:
                return self.instantiate_transform(name, [], {}, line)
            if name in BUILTIN_POSITIONS:
                return [self.add_program([(STEP_SET, 0, 0.0, 0, 0,
                                           self.expand_props(BUILTIN_POSITIONS[name], line))])]
            if name in self.defines:
                return self.transform_ast(self.defines[name][0], line, depth + 1)
            self.warn(line, f"unknown transform '{name}'")
            return []
        if isinstance(expr, ast.Call):
            fn = dotted(expr.func)
            if fn in self.transform_nodes:
                args = [self.eval_ast(a, {}) for a in expr.args]
                kwargs = {k.arg: self.eval_ast(k.value, {}) for k in expr.keywords if k.arg}
                return self.instantiate_transform(fn, args, kwargs, line)
            if fn in ("Transform", "Position", "Motion"):
                props = []
                for k in expr.keywords:
                    if k.arg in ATL_PROPERTIES:
                        try:
                            props.append((k.arg, self.eval_ast(k.value, {})))
                        except Unsupported:
                            self.warn(line, f"cannot evaluate {k.arg}")
                return [self.add_program([(STEP_SET, 0, 0.0, 0, 0,
                                           self.expand_props(props, line))])]
        self.warn(line, f"unsupported transform expression '{ast.unparse(expr)}'")
        return []

    def instantiate_transform(self, name, args, kwargs, line):
        node = self.transform_nodes[name]
        env = {}
        if node.params:
            try:
                fdef = ast.parse(f"def f{node.params}: pass").body[0]
            except SyntaxError:
                fdef = None
                self.warn(node.line, f"cannot parse parameters of transform {name}")
            if fdef is not None:
                pnames = [a.arg for a in fdef.args.args]
                defaults = fdef.args.defaults
                for pn, d in zip(pnames[len(pnames) - len(defaults):], defaults):
                    try:
                        env[pn] = self.eval_ast(d, {})
                    except Unsupported:
                        pass
                for pn, v in zip(pnames, args):
                    env[pn] = v
                env.update(kwargs)
        return self.compile_atl(node.block, env, line)

    def add_program(self, steps):
        self.atl_programs.append(steps)
        return len(self.atl_programs) - 1

    def compile_atl(self, lines, env, line):
        """Compile an ATL block. Returns a list of program ids: the main
        sequence first, then one per `parallel` block."""
        extra = []
        steps = []
        self.atl_lines(lines, steps, env, 0, extra)
        progs = []
        if steps:
            progs.append(self.add_program(steps))
        for p in extra:
            if p:
                progs.append(self.add_program(p))
        return progs

    def atl_lines(self, lines, steps, env, block_start, extra):
        prev_choice = False
        for line in lines:
            text = line.text
            lex = rpy.Lexer(line)
            was_choice, prev_choice = prev_choice, False
            if text.endswith(":"):
                w = lex.word()
                if w == "block":
                    self.atl_lines(line.block, steps, env, len(steps), extra)
                elif w == "parallel":
                    sub = []
                    self.atl_lines(line.block, sub, env, 0, extra)
                    extra.append(sub)
                elif w == "choice":
                    # Only the first of a run of choice blocks is used.
                    self.warn_once("atl-choice", line, "ATL choice always takes the first choice")
                    if not was_choice:
                        self.atl_lines(line.block, steps, env, block_start, extra)
                    prev_choice = True
                elif w == "on":
                    events = [e.strip() for e in lex.rest_before_colon().split(",")]
                    if any(e in ("show", "replace", "start", "appear", "update")
                           for e in events):
                        self.atl_lines(line.block, steps, env, block_start, extra)
                elif w == "contains":
                    self.warn(line, "ATL 'contains' is not supported")
                else:
                    self.warn(line, f"ATL '{w}:' is not supported")
                continue
            for stmt in split_top_commas(text):
                self.atl_statement(line, stmt, steps, env, block_start)

    def atl_statement(self, line, text, steps, env, block_start):
        lex = rpy.Lexer(line, text)
        if lex.eol():
            return
        save = lex.pos
        w = lex.word()
        if w == "pass":
            return
        if w == "repeat":
            n = 0
            if not lex.eol():
                try:
                    n = int(self.eval_const(lex.rest(), env))
                except (Unsupported, ValueError, TypeError):
                    n = 0
            if n == 1:
                return
            steps.append((STEP_REPEAT, 0, 0.0, block_start, max(0, n - 1), []))
            return
        if w in ("time", "function", "event", "knot", "clockwise",
                 "counterclockwise", "circles", "warp"):
            if w not in ("clockwise", "counterclockwise"):
                self.warn(line, f"ATL '{w}' is not supported")
            return
        if w == "pause":
            d = self.eval_const(lex.rest(), env)
            steps.append((STEP_PAUSE, 0, float(d), 0, 0, []))
            return
        warper = None
        if w in WARPERS:
            warper = WARPERS[w]
        elif w and re.match(r"^ease(in|out)?_", w):
            warper = WARPERS[w.split("_")[0]]
        elif w and (w.startswith("ease") or w in ("linear",)):
            warper = 1
        if warper is not None:
            dur = self.eval_const(lex.simple_expression(), env)
            props = self.atl_props(line, lex, env)
            steps.append((STEP_INTERP, warper, float(dur), 0, 0, props))
            return
        lex.pos = save
        if lex.string() is not None:
            # A displayable inside a transform (image swap); can't do that.
            return
        lex.pos = save
        n = lex.number()
        if n is not None and lex.eol():
            steps.append((STEP_PAUSE, 0, float(n), 0, 0, []))
            return
        lex.pos = save
        if w in ATL_PROPERTIES:
            props = self.atl_props(line, lex, env)
            if props:
                steps.append((STEP_SET, 0, 0.0, 0, 0, props))
            return
        lex.pos = save
        e = lex.simple_expression()
        if e and lex.eol():
            # A transform used as an ATL statement: include its steps inline.
            try:
                expr = ast.parse(e, mode="eval").body
            except SyntaxError:
                expr = None
            name = dotted(expr) if expr is not None else None
            if name in BUILTIN_POSITIONS:
                steps.append((STEP_SET, 0, 0.0, 0, 0,
                              self.expand_props(BUILTIN_POSITIONS[name], line)))
                return
            if name in self.transform_nodes:
                node = self.transform_nodes[name]
                start = len(steps)
                self.atl_lines(node.block, steps, {}, start, [])
                return
        self.warn(line, f"unsupported ATL: {text}")

    def atl_props(self, line, lex, env):
        raw = []
        while not lex.eol():
            p = lex.word()
            if p is None:
                self.warn(line, f"unexpected ATL text: {lex.rest()}")
                break
            if p in ("knot", "clockwise", "counterclockwise"):
                lex.simple_expression() if p == "knot" else None
                continue
            if p == "circles":
                lex.simple_expression()
                continue
            e = lex.simple_expression()
            if e is None:
                self.warn(line, f"missing value for {p}")
                break
            if p not in ATL_PROPERTIES:
                self.warn(line, f"unknown ATL property {p}")
                continue
            try:
                raw.append((p, self.eval_const(e, env)))
            except Unsupported as ex:
                self.warn(line, f"cannot evaluate {p} {e}: {ex}")
        return self.expand_props(raw, line)

    def expand_props(self, raw, line):
        out = []

        def pos(prop, v, force_frac=False):
            if isinstance(v, bool):
                v = float(v)
            if not isinstance(v, (int, float)):
                self.warn(line, f"bad value for {prop}")
                return
            is_abs = (isinstance(v, int) or isinstance(v, Absolute)) and not force_frac
            out.append((PROP[prop], 1 if is_abs else 0, float(v)))

        def pair(v):
            if isinstance(v, (tuple, list)) and len(v) == 2:
                return v
            self.warn(line, "expected a pair")
            return None

        for p, v in raw:
            if p in ("xpos", "ypos", "xanchor", "yanchor"):
                pos(p, v)
            elif p in ("xoffset", "yoffset"):
                out.append((PROP[p], 1, float(v)))
            elif p in ("xalign", "yalign"):
                axis = p[0]
                pos(axis + "pos", v, True)
                pos(axis + "anchor", v, True)
            elif p == "align":
                pv = pair(v)
                if pv:
                    for axis, c in zip("xy", pv):
                        pos(axis + "pos", c, True)
                        pos(axis + "anchor", c, True)
            elif p in ("pos", "anchor"):
                pv = pair(v)
                if pv:
                    for axis, c in zip("xy", pv):
                        pos(axis + p, c)
            elif p == "offset":
                pv = pair(v)
                if pv:
                    out.append((PROP["xoffset"], 1, float(pv[0])))
                    out.append((PROP["yoffset"], 1, float(pv[1])))
            elif p in ("xcenter", "ycenter"):
                pos(p[0] + "pos", v)
                out.append((PROP[p[0] + "anchor"], 0, 0.5))
            elif p == "xycenter":
                pv = pair(v)
                if pv:
                    pos("xpos", pv[0])
                    pos("ypos", pv[1])
                    out.append((PROP["xanchor"], 0, 0.5))
                    out.append((PROP["yanchor"], 0, 0.5))
            elif p in ("zoom", "xzoom", "yzoom", "alpha", "rotate", "zpos"):
                try:
                    out.append((PROP[p], 0, float(v)))
                except (TypeError, ValueError):
                    self.warn(line, f"bad value for {p}")
            # everything else in ATL_PROPERTIES is accepted and ignored
        return out

    # -- transitions ------------------------------------------------------

    def c_with(self, src, line):
        tid = self.transition(src, line)
        self.code.op("WITH")
        self.code.i32(tid)

    def transition(self, src, line):
        key = src.strip()
        if key in ("None", ""):
            return -1
        if key in self.trans_cache:
            return self.trans_cache[key]
        try:
            expr = ast.parse(key, mode="eval").body
        except SyntaxError:
            self.warn(line, f"cannot parse transition '{src}'")
            return -1
        t = self.eval_transition(expr, line, 0)
        if t is None:
            tid = -1
        else:
            self.transitions.append(t)
            tid = len(self.transitions) - 1
        self.trans_cache[key] = tid
        return tid

    def eval_transition(self, expr, line, depth):
        if depth > 8:
            return None
        if isinstance(expr, ast.Constant) and expr.value is None:
            return None
        name = dotted(expr)
        if name is not None:
            if name in self.defines:
                return self.eval_transition(self.defines[name][0], line, depth + 1)
            if name in BUILTIN_TRANSITIONS:
                if name in APPROX_TRANSITIONS:
                    self.warn_once(f"approx:{name}", line,
                                   f"transition '{name}' is drawn as a dissolve")
                return BUILTIN_TRANSITIONS[name]
            self.warn(line, f"unknown transition '{name}', using dissolve")
            return BUILTIN_TRANSITIONS["dissolve"]
        if isinstance(expr, ast.Dict) and expr.values:
            return self.eval_transition(expr.values[0], line, depth + 1)
        if not isinstance(expr, ast.Call):
            self.warn(line, f"unsupported transition '{ast.unparse(expr)}'")
            return BUILTIN_TRANSITIONS["dissolve"]
        fn = dotted(expr.func)
        args = expr.args
        kw = {k.arg: k.value for k in expr.keywords if k.arg}

        def num(i, key=None, default=0.5):
            node = args[i] if i < len(args) else kw.get(key)
            if node is None:
                return default
            try:
                return float(self.eval_ast(node, {}))
            except (Unsupported, TypeError, ValueError):
                return default

        if fn in ("Dissolve", "Pixellate", "AlphaDissolve"):
            return (T_DISSOLVE, 0, 0, num(0, "time"), 0, 0, 0)
        if fn in ("ImageDissolve", "CropMove", "PushMove"):
            return (T_DISSOLVE, 0, 0, num(1, "time", 1.0), 0, 0, 0)
        if fn == "Fade":
            color = BLACK
            if "color" in kw:
                color = parse_color(self.const_str(kw["color"]), BLACK)
            return (T_FADE, 0, 0, num(0, "out_time"), num(1, "hold_time", 0.0),
                    num(2, "in_time", num(0, "out_time")), color)
        if fn == "MoveTransition":
            return (T_MOVE, 0, 0, num(0, "delay"), 0, 0, 0)
        if fn == "MultipleTransition" and args and isinstance(args[0], ast.List):
            elts = args[0].elts
            for e in reversed(elts[1::2]):
                t = self.eval_transition(e, line, depth + 1)
                if t is not None:
                    return t
            return None
        if fn == "ComposeTransition" and args:
            return self.eval_transition(args[0], line, depth + 1)
        if fn == "Move" and len(args) >= 2:
            try:
                a = self.eval_ast(args[0], {})
                horizontal = abs(a[0]) >= abs(a[1])
            except (Unsupported, TypeError, IndexError):
                horizontal = True
            dur = num(99, "delay", 0.275)
            return (T_PUNCH, 0, 1 if horizontal else 0, dur, 0, 0, 0)
        if fn in ("Pause",):
            return (T_FADE, 0, 0, 0.0, num(0, "delay"), 0.0, 0)
        self.warn(line, f"unsupported transition {fn}, using dissolve")
        return BUILTIN_TRANSITIONS["dissolve"]

    def warn_once(self, key, line, msg):
        seen = self.__dict__.setdefault("_warned", set())
        if key not in seen:
            seen.add(key)
            self.warn(line, msg)

    # -- audio ------------------------------------------------------------

    def audio_path(self, expr, line):
        if isinstance(expr, ast.Constant) and isinstance(expr.value, str):
            p = expr.value
        else:
            name = dotted(expr)
            if name is None:
                raise Unsupported("audio file must be a constant")
            p = self.audio_names.get(name) or self.audio_names.get("audio." + name)
            if p is None:
                v = self.constants.get(name)
                if isinstance(v, str):
                    p = v
                else:
                    # Ren'Py defines names for files in game/audio automatically;
                    # the packager resolves these.
                    p = "?auto:" + name.split(".")[-1]
        if p.startswith("<"):
            end = p.find(">")
            self.warn_once("audio-spec", line, "audio <from/to/loop> specifiers are ignored")
            p = p[end + 1:]
        return p

    def audio_index(self, path):
        idx = self.audio_res.get(path)
        if idx is None:
            idx = self.audio_res[path] = self.resource("audio", path)
        return idx

    def c_play(self, n):
        code = self.code
        try:
            expr = ast.parse(n.expr, mode="eval").body
        except SyntaxError:
            raise Unsupported(f"cannot parse audio file {n.expr}")
        files = expr.elts if isinstance(expr, (ast.List, ast.Tuple)) else [expr]
        loop = n.loop if n.loop is not None else (n.channel == 0)
        for i, f in enumerate(files):
            path = self.audio_path(f, n.line)
            flags = (1 if loop else 0) | (2 if (n.queue or i > 0) else 0) | \
                    (4 if n.if_changed else 0)
            code.op("PLAY")
            code.u8(n.channel)
            code.i32(self.audio_index(path))
            code.u8(flags)
            code.f32(n.fadein if i == 0 else 0.0)
            code.f32(n.fadeout if n.fadeout is not None else 0.0)

    # -- expressions ------------------------------------------------------

    def eval_const(self, src, env):
        try:
            return self.eval_ast(ast.parse(src.strip(), mode="eval").body, env)
        except SyntaxError:
            raise Unsupported(f"cannot parse '{src}'")

    def eval_ast(self, node, env):
        """Evaluate a compile-time expression (ATL values, transform args)."""
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, (ast.Tuple, ast.List)):
            return tuple(self.eval_ast(e, env) for e in node.elts)
        if isinstance(node, ast.UnaryOp):
            v = self.eval_ast(node.operand, env)
            if isinstance(node.op, ast.USub):
                return Absolute(-v) if isinstance(v, Absolute) else -v
            if isinstance(node.op, ast.UAdd):
                return v
        if isinstance(node, ast.BinOp) and type(node.op) in BINOPS:
            a = self.eval_ast(node.left, env)
            b = self.eval_ast(node.right, env)
            op = type(node.op)
            try:
                r = {ast.Add: lambda: a + b, ast.Sub: lambda: a - b,
                     ast.Mult: lambda: a * b, ast.Div: lambda: a / b,
                     ast.FloorDiv: lambda: a // b, ast.Mod: lambda: a % b,
                     ast.Pow: lambda: a ** b}[op]()
            except (TypeError, ZeroDivisionError) as e:
                raise Unsupported(str(e))
            if isinstance(a, Absolute) or isinstance(b, Absolute):
                r = Absolute(r)
            return r
        if isinstance(node, ast.Name) or isinstance(node, ast.Attribute):
            name = dotted(node)
            if name in env:
                return env[name]
            if name in self.constants:
                return self.constants[name]
            if name in ("config.screen_width",):
                return self.meta.get("width") or 1280
            if name in ("config.screen_height",):
                return self.meta.get("height") or 720
            raise Unsupported(f"unknown name {name}")
        if isinstance(node, ast.Call):
            fn = dotted(node.func)
            if fn in ("absolute", "int") and node.args:
                v = self.eval_ast(node.args[0], env)
                return Absolute(v) if fn == "absolute" else int(v)
            if fn == "float" and node.args:
                return float(self.eval_ast(node.args[0], env))
            if fn == "renpy.random.random":
                return 0.5
        raise Unsupported(f"cannot evaluate {ast.unparse(node)}")

    def c_expr(self, src, line):
        try:
            node = ast.parse(src.strip(), mode="eval").body
        except SyntaxError:
            raise Unsupported(f"cannot parse expression '{src}'")
        self.c_ast(node, line)

    def c_ast(self, n, line):
        code = self.code
        if isinstance(n, ast.Constant):
            v = n.value
            if v is True:
                code.op("PUSH_TRUE")
            elif v is False:
                code.op("PUSH_FALSE")
            elif v is None:
                code.op("PUSH_NONE")
            elif isinstance(v, (int, float)):
                code.op("PUSH_NUM")
                code.f64(float(v))
            elif isinstance(v, str):
                code.op("PUSH_STR")
                code.u32(self.s(v))
            else:
                raise Unsupported(f"unsupported constant {v!r}")
            return
        if isinstance(n, (ast.Name, ast.Attribute)):
            name = dotted(n)
            if name is None:
                raise Unsupported(f"unsupported expression {ast.unparse(n)}")
            code.op("LOAD")
            code.u32(self.var(name))
            return
        if isinstance(n, ast.BinOp):
            op = BINOPS.get(type(n.op))
            if op is None:
                raise Unsupported(f"operator {type(n.op).__name__}")
            self.c_ast(n.left, line)
            self.c_ast(n.right, line)
            code.op(op)
            return
        if isinstance(n, ast.UnaryOp):
            self.c_ast(n.operand, line)
            if isinstance(n.op, ast.USub):
                code.op("NEG")
            elif isinstance(n.op, ast.Not):
                code.op("NOT")
            elif not isinstance(n.op, ast.UAdd):
                raise Unsupported("operator ~")
            return
        if isinstance(n, ast.BoolOp):
            end = Ref()
            jump = "JZ" if isinstance(n.op, ast.And) else "JNZ"
            for i, v in enumerate(n.values):
                self.c_ast(v, line)
                if i < len(n.values) - 1:
                    code.op("DUP")
                    code.op(jump)
                    code.ref(end)
                    code.op("POP")
            code.mark(end)
            return
        if isinstance(n, ast.Compare):
            left = n.left
            for i, (op, right) in enumerate(zip(n.ops, n.comparators)):
                self.c_ast(left, line)
                self.c_ast(right, line)
                if isinstance(op, (ast.In, ast.NotIn)):
                    code.op("IN")
                    if isinstance(op, ast.NotIn):
                        code.op("NOT")
                else:
                    name = CMPOPS.get(type(op))
                    if name is None:
                        raise Unsupported(f"comparison {type(op).__name__}")
                    code.op(name)
                if i > 0:
                    # a < b < c  ==  (a < b) and (b < c); both are on the stack
                    code.op("MUL")
                    code.op("NOT")
                    code.op("NOT")
                left = right
            return
        if isinstance(n, ast.IfExp):
            other, end = Ref(), Ref()
            self.c_ast(n.test, line)
            code.op("JZ")
            code.ref(other)
            self.c_ast(n.body, line)
            code.op("JMP")
            code.ref(end)
            code.mark(other)
            self.c_ast(n.orelse, line)
            code.mark(end)
            return
        if isinstance(n, ast.Subscript):
            self.c_ast(n.value, line)
            sl = n.slice
            if isinstance(sl, ast.Slice):
                for part in (sl.lower, sl.upper):
                    if part is None:
                        code.op("PUSH_NONE")
                    else:
                        self.c_ast(part, line)
                code.op("CALLF")
                code.u8(BUILTINS["_slice"])
                code.u8(3)
            else:
                self.c_ast(sl, line)
                code.op("CALLF")
                code.u8(BUILTINS["_getitem"])
                code.u8(2)
            return
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and n.func.attr in STR_METHODS and not n.args
                and dotted(n.func.value) not in ("renpy", "store")):
            self.c_ast(n.func.value, line)
            code.op("CALLF")
            code.u8(BUILTINS[STR_METHODS[n.func.attr]])
            code.u8(1)
            return
        if isinstance(n, ast.Call):
            fn = dotted(n.func)
            if fn == "renpy.input":
                # No keyboard: take the default (scripts usually fall back on "").
                kw = {k.arg: k.value for k in n.keywords if k.arg}
                d = kw.get("default") or (n.args[1] if len(n.args) > 1 else None)
                self.warn_once("input", line, "renpy.input returns its default (no keyboard)")
                if d is not None:
                    self.c_ast(d, line)
                else:
                    code.op("PUSH_STR")
                    code.u32(self.s(""))
                return
            if fn in ("_", "__", "renpy.translate_string") and n.args:
                self.c_ast(n.args[0], line)
                return
            if fn == "vn3ds_minigame":
                # vn3ds extension: a native minigame; its 0-100 score is the value.
                # (On PC the game defines vn3ds_minigame() itself.)
                if len(n.args) != 1:
                    raise Unsupported("vn3ds_minigame() takes the game's id")
                a = n.args[0]
                if isinstance(a, ast.Constant) and isinstance(a.value, str) \
                        and a.value not in self.minigames:
                    self.minigames.append(a.value)
                self.c_ast(a, line)
                code.op("MINIGAME")
                return
            if fn in BUILTINS:
                for a in n.args:
                    self.c_ast(a, line)
                code.op("CALLF")
                code.u8(BUILTINS[fn])
                code.u8(len(n.args))
                return
            raise Unsupported(f"call to {fn or ast.unparse(n.func)}()")
        if isinstance(n, ast.JoinedStr):
            code.op("PUSH_STR")
            code.u32(self.s(""))
            for part in n.values:
                if isinstance(part, ast.Constant):
                    self.c_ast(part, line)
                else:
                    self.c_ast(part.value, line)
                    code.op("CALLF")
                    code.u8(BUILTINS["str"])
                    code.u8(1)
                code.op("ADD")
            return
        raise Unsupported(f"unsupported expression {ast.unparse(n)}")

    # -- python statements -------------------------------------------------

    def c_python(self, src, line):
        try:
            tree = ast.parse(src)
        except SyntaxError:
            raise Unsupported("cannot parse python code")
        for st in tree.body:
            try:
                self.c_pystmt(st, line)
            except Unsupported as e:
                self.warn(line, f"python: {e}; statement skipped")

    def c_pystmt(self, st, line):
        code = self.code
        if isinstance(st, (ast.Assign, ast.AnnAssign)):
            targets = st.targets if isinstance(st, ast.Assign) else [st.target]
            if st.value is None:
                return
            names = []
            for t in targets:
                name = dotted(t)
                if name is None:
                    raise Unsupported(f"assignment to {ast.unparse(t)}")
                names.append(name)
            if any(nm.startswith(("config.", "preferences.", "_preferences.", "gui."))
                   for nm in names):
                return
            self.c_ast(st.value, line)
            for i, name in enumerate(names):
                if i < len(names) - 1:
                    code.op("DUP")
                code.op("STORE")
                code.u32(self.var(name))
            return
        if isinstance(st, ast.AugAssign):
            name = dotted(st.target)
            if name is None or type(st.op) not in BINOPS:
                raise Unsupported(f"augmented assignment {ast.unparse(st)}")
            code.op("LOAD")
            code.u32(self.var(name))
            self.c_ast(st.value, line)
            code.op(BINOPS[type(st.op)])
            code.op("STORE")
            code.u32(self.var(name))
            return
        if isinstance(st, ast.If):
            other, end = Ref(), Ref()
            self.c_ast(st.test, line)
            code.op("JZ")
            code.ref(other)
            for s in st.body:
                self.c_pystmt(s, line)
            code.op("JMP")
            code.ref(end)
            code.mark(other)
            for s in st.orelse:
                self.c_pystmt(s, line)
            code.mark(end)
            return
        if isinstance(st, ast.Pass):
            return
        if isinstance(st, ast.Expr) and isinstance(st.value, ast.Call):
            self.c_pycall(st.value, line)
            return
        raise Unsupported(f"{type(st).__name__} statement")

    def c_pycall(self, call, line):
        code = self.code
        fn = dotted(call.func)
        kw = {k.arg: k.value for k in call.keywords if k.arg}
        args = call.args
        if fn in IGNORED_CALLS:
            return
        if fn == "renpy.pause":
            node = args[0] if args else kw.get("delay")
            if node is None:
                code.op("PAUSE")
                code.u8(0)
            else:
                self.c_ast(node, line)
                code.op("PAUSE")
                code.u8(1)
            return
        if fn in ("renpy.jump", "renpy.call"):
            if not args or not isinstance(args[0], ast.Constant):
                raise Unsupported(f"{fn} with a computed label")
            code.op("JMP" if fn == "renpy.jump" else "CALL")
            code.ref(self.label_ref(self.qualify(args[0].value, line)))
            return
        if fn in ("renpy.music.play", "renpy.sound.play", "renpy.play",
                  "renpy.music.queue", "renpy.sound.queue", "renpy.voice"):
            if not args:
                raise Unsupported(f"{fn} without a file")
            channel = 0 if fn.startswith("renpy.music") else (2 if fn == "renpy.voice" else 1)
            if "channel" in kw:
                cname = self.const_str(kw["channel"])
                channel = rpy.channel_index(cname, channel)
            loop = channel == 0
            if "loop" in kw:
                loop = bool(self.const_value(kw["loop"]))
            fadein = float(self.const_value(kw["fadein"]) or 0) if "fadein" in kw else 0.0
            path = self.audio_path(args[0], line)
            code.op("PLAY")
            code.u8(channel)
            code.i32(self.audio_index(path))
            code.u8((1 if loop else 0) | (2 if fn.endswith("queue") else 0))
            code.f32(fadein)
            code.f32(0.0)
            return
        if fn in ("renpy.music.stop", "renpy.sound.stop"):
            channel = 0 if fn.startswith("renpy.music") else 1
            if "channel" in kw:
                channel = rpy.channel_index(self.const_str(kw["channel"]), channel)
            fade = float(self.const_value(kw["fadeout"]) or 0) if "fadeout" in kw else 0.0
            code.op("STOP")
            code.u8(channel)
            code.f32(fade)
            return
        if fn in ("renpy.show", "renpy.hide", "renpy.scene"):
            spec = self.const_str(args[0]) if args else None
            if fn == "renpy.hide":
                if not spec:
                    raise Unsupported("renpy.hide needs a constant name")
                code.op("HIDE")
                code.u32(self.s(spec.split()[0]))
                return
            if spec:
                self.used_specs.setdefault(spec, line)
            atl = []
            if "at_list" in kw and isinstance(kw["at_list"], (ast.List, ast.Tuple)):
                for e in kw["at_list"].elts:
                    atl += self.transform_ast(e, line)
            code.op("SCENE" if fn == "renpy.scene" else "SHOW")
            code.u32(self.s(spec))
            code.u32(NONE)
            code.i32(INT32_MIN)
            code.u32(NONE)
            code.u8(len(atl[:8]))
            for a in atl[:8]:
                code.i32(a)
            return
        if fn == "renpy.with_statement":
            if args:
                tid = -1
                t = self.eval_transition(args[0], line, 0)
                if t is not None:
                    self.transitions.append(t)
                    tid = len(self.transitions) - 1
                code.op("WITH")
                code.i32(tid)
            return
        if fn == "renpy.say":
            if len(args) < 2:
                raise Unsupported("renpy.say needs who and what")
            who = dotted(args[0])
            idx = self.char_by_name.get(who, 0) if who else 0
            what = self.const_str(args[1])
            if what is None:
                raise Unsupported("renpy.say with computed text")
            code.op("SAY")
            code.i32(idx)
            code.u32(NONE)
            code.u32(self.s(what))
            code.u8(0)
            return
        raise Unsupported(f"call to {fn or ast.unparse(call.func)}()")


def split_top_commas(text):
    out, depth, cur, i = [], 0, [], 0
    while i < len(text):
        c = text[i]
        if c in "\"'":
            j = i + 1
            while j < len(text) and text[j] != c:
                j += 2 if text[j] == "\\" else 1
            cur.append(text[i:j + 1])
            i = j + 1
            continue
        if c in "([{":
            depth += 1
        elif c in ")]}":
            depth -= 1
        if c == "," and depth == 0:
            out.append("".join(cur).strip())
            cur = []
        else:
            cur.append(c)
        i += 1
    out.append("".join(cur).strip())
    return [s for s in out if s]


# --------------------------------------------------------------------------
# Binary writer
# --------------------------------------------------------------------------

def encode_atl(programs):
    blob = bytearray()
    offsets = []
    for steps in programs:
        offsets.append(len(blob))
        blob += struct.pack("<H", len(steps))
        for kind, warper, dur, target, count, props in steps:
            blob += struct.pack("<BBBBfHH", kind, warper, len(props), 0, dur,
                                target, count)
            for prop, is_abs, value in props:
                blob += struct.pack("<BBHf", prop, is_abs, 0, value)
    return struct.pack("<I", len(programs)) + b"".join(
        struct.pack("<I", o) for o in offsets) + bytes(blob)


def write_game(path, comp, meta, images, resources, layers=(), voices=None):
    """Serialise everything into game.bin.

    `images` is a list of dicts with name/res/color/w/h/flags/depth;
    `resources` the final resource path list.
    """
    s = comp.s
    sections = []

    def section(tag, data):
        sections.append((tag.encode("ascii"), bytes(data)))

    def strs(values):
        return b"".join(struct.pack("<I", s(v)) for v in values)

    # Interning happens while the tables are built, so the string table is
    # emitted last.
    meta_data = struct.pack(
        "<IIHHfffffIIffffi",
        s(meta["title"]), s(meta["version"]), meta["game_w"], meta["game_h"],
        meta["scale"], meta["view_x"], meta["view_y"], meta["view_w"], meta["view_h"],
        comp.init_addr, len(comp.vars), meta["depth_bg"], meta["depth_sprite"],
        meta["depth_ui"], meta["max_shift"], meta["title_image"])

    var_names = sorted(comp.vars, key=comp.vars.get)
    vars_data = struct.pack("<I", len(var_names)) + strs(var_names)
    res_data = struct.pack("<I", len(resources)) + strs(resources)

    img_data = bytearray(struct.pack("<I", len(images)))
    for im in images:
        img_data += struct.pack("<IiIffIf", s(im["name"]), im["res"], im["color"],
                                im["w"], im["h"], im["flags"], im["depth"])

    chr_data = bytearray(struct.pack("<I", len(comp.chars)))
    for c in comp.chars:
        chr_data += struct.pack("<IIIIIIBBBB", s(c.name), s(c.image), c.name_color,
                                c.text_color, s(c.prefix or None), s(c.suffix or None),
                                c.kind, 0, 0, 0)

    tr_data = bytearray(struct.pack("<I", len(comp.transitions)))
    for typ, warper, d, a, b, c, color in comp.transitions:
        tr_data += struct.pack("<BBBBfffI", typ, warper, d, 0, a, b, c, color)

    section("META", meta_data)
    section("VARS", vars_data)
    section("RES ", res_data)
    section("IMGS", img_data)
    section("CHRS", chr_data)
    section("TRAN", tr_data)
    section("ATL ", encode_atl(comp.atl_programs))
    cam = meta.get("camera")
    if cam:
        section("CAM ", struct.pack("<fff", float(cam.get("drift", 0)), float(cam.get("period", 16)),
                                    float(cam.get("zoom", 0))))
    if comp.meta.get("speaking_attribute"):
        section("TALK", struct.pack("<I", s(comp.meta["speaking_attribute"])))
    if comp.minigames:
        section("MINI", struct.pack("<I", len(comp.minigames)) + strs(comp.minigames))
    if comp.named_audio:
        audn = bytearray(struct.pack("<I", len(comp.named_audio)))
        for name, res in sorted(comp.named_audio.items()):
            audn += struct.pack("<Ii", s(name), res)
        section("AUDN", audn)
    if voices:
        vox = bytearray(struct.pack("<I", len(voices["bank"])))
        for res in voices["bank"]:
            vox += struct.pack("<i", res)
        vox += struct.pack("<ffI", voices["volume"], voices["duck"], len(comp.chars))
        for i in range(len(comp.chars)):
            vox += struct.pack("<f", voices["pitch"].get(i, 0.0))
        section("VOX ", vox)
    if layers:
        lay = bytearray(struct.pack("<I", len(layers)))
        for img_index, items in layers:
            lay += struct.pack("<II", img_index, len(items))
            for res, depth, x, y, w, h, anim in items:
                kind, a1, a2, a3 = anim
                lay += struct.pack("<ifffffIfff", res, depth, x, y, w, h, kind, a1, a2, a3)
        section("LAYR", lay)
    section("CODE", comp.code.b)
    labels = sorted((name, r.addr) for name, r in comp.labels.items()
                    if r.addr is not None and name in comp.defined_labels)
    section("LABL", struct.pack("<I", len(labels)) + b"".join(
        struct.pack("<II", s(name), addr) for name, addr in labels))

    blob = bytearray()
    offsets = []
    for text in comp.strlist:
        offsets.append(len(blob))
        blob += text.encode("utf-8") + b"\0"
    str_data = struct.pack("<I", len(offsets)) + b"".join(
        struct.pack("<I", o) for o in offsets) + bytes(blob)
    sections.insert(0, (b"STR ", str_data))

    header_size = 12 + 12 * len(sections)
    out = bytearray(b"VN3D" + struct.pack("<II", 1, len(sections)))
    offset = header_size
    table = bytearray()
    for tag, data in sections:
        table += tag + struct.pack("<II", offset, len(data))
        offset += (len(data) + 3) & ~3
    out += table
    for tag, data in sections:
        out += data
        out += b"\0" * (((len(data) + 3) & ~3) - len(data))
    with open(path, "wb") as f:
        f.write(out)
    return len(out)

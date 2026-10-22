# vn3ds_rt: a Ren'Py screen runtime for vn3ds.
#
# Runs a game's own screens (translated to Python by screenlang.py) and its
# own init python, inside the engine's embedded Python (pocketpy) on the 3DS,
# or inside CPython for tests. The engine provides the module _vn3ds:
#
#   get(name) / set(name, value) / has(name)   story variables (the VM's)
#   play(channel, audio_name, loop, fade) / stop(channel, fade) / queue(...)
#   playing(channel) -> audio name or ""
#   text_width(s, size) -> width in game pixels of s at font size `size`
#   line_height(size)  -> line height in game pixels
#   log(msg)
#
# and calls, per frame: begin(mode, screen, args) once, then frame(dt, events)
# -> status, and draw_list() -> the display list (see `_emit`). In the story
# (no run): story_frame(dt) and hud_label() for the shown overlays.
#
# Coordinates are the game's (e.g. 1920x1080); the engine scales them.
# Written for the Python subset both interpreters share.

import _vn3ds

# --------------------------------------------------------------------------
# the Python dialect: what pkcompat.py's rewrites call, and the methods and
# built-ins the engine's interpreter lacks (each only where it's missing)

def _with_defaults(f, names, defaults, star, kwonly):
    """A function whose defaults are given here (evaluated where it was
    defined), for parameters the interpreter wants without them."""
    n = len(names)

    def call(*args, **kw):
        pos = list(args[:n])
        extra = list(args[n:])
        k = len(pos)
        while k < n:
            nm = names[k]
            if nm in kw:
                pos.append(kw.pop(nm))
            elif nm in defaults:
                pos.append(defaults[nm])
            else:
                raise TypeError("missing argument '" + nm + "'")
            k += 1
        if extra and not star:
            raise TypeError("too many arguments")
        for nm in kwonly:
            if nm not in kw:
                if nm in defaults:
                    kw[nm] = defaults[nm]
                else:
                    raise TypeError("missing keyword argument '" + nm + "'")
        return f(*(pos + extra), **kw)
    return call


def _merge_dicts(*ds):
    out = {}
    for d in ds:
        for k in d:
            out[k] = d[k]
    return out


def _dict(*args, **kw):
    out = {}
    if args:
        src = args[0]
        if isinstance(src, dict):
            for k in src:
                out[k] = src[k]
        else:
            for pair in src:
                out[pair[0]] = pair[1]
    for k in kw:
        out[k] = kw[k]
    return out


def _patch(tp, name, fn):
    if not hasattr(tp, name):
        try:
            setattr(tp, name, fn)
        except Exception:
            pass


_DIGITS = "0123456789"
_LOWER = "abcdefghijklmnopqrstuvwxyz"
_UPPER = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
_SPACE = " \t\n\r\x0b\x0c"


def _all_in(s, chars):
    if not s:
        return False
    for c in s:
        if c not in chars:
            return False
    return True


def _s_title(s):
    out = []
    prev = False
    for c in s:
        if c in _LOWER or c in _UPPER:
            out.append(c.upper() if not prev else c.lower())
            prev = True
        else:
            out.append(c)
            prev = False
    return "".join(out)


def _s_partition(s, sep):
    k = s.find(sep)
    if k < 0:
        return (s, "", "")
    return (s[:k], sep, s[k + len(sep):])


def _s_rfind(s, sub, start=0, end=None):
    if end is None:
        end = len(s)
    k = end - len(sub)
    while k >= start:
        if s[k:k + len(sub)] == sub:
            return k
        k -= 1
    return -1


def _s_rindex(s, sub, start=0, end=None):
    k = _s_rfind(s, sub, start, end)
    if k < 0:
        raise ValueError("substring not found")
    return k


def _s_rpartition(s, sep):
    k = _s_rfind(s, sep)
    if k < 0:
        return ("", "", s)
    return (s[:k], sep, s[k + len(sep):])


def _s_rsplit(s, sep=None, maxsplit=-1):
    if maxsplit is None or maxsplit < 0:
        return s.split(sep) if sep is not None else s.split()
    parts = s.split(sep) if sep is not None else s.split()
    if len(parts) <= maxsplit + 1:
        return parts
    joiner = sep if sep is not None else " "
    head = parts[:len(parts) - maxsplit]
    return [joiner.join(head)] + parts[len(parts) - maxsplit:]


def _s_center(s, width, fill=" "):
    pad = width - len(s)
    if pad <= 0:
        return s
    left = pad // 2
    return fill * left + s + fill * (pad - left)


def _s_capitalize(s):
    return s[:1].upper() + s[1:].lower()


def _s_swapcase(s):
    return "".join([c.lower() if c in _UPPER else (c.upper() if c in _LOWER else c) for c in s])


def _s_removeprefix(s, p):
    return s[len(p):] if p and s.startswith(p) else s


def _s_removesuffix(s, p):
    return s[:len(s) - len(p)] if p and s.endswith(p) else s


try:
    "a b".split(" ", 1)
except TypeError:
    _str_split = str.split

    def _split(s, sep=None, maxsplit=-1):
        parts = _str_split(s, sep) if sep is not None else _str_split(s)
        if maxsplit is None or maxsplit < 0 or len(parts) <= maxsplit + 1:
            return parts
        if sep is None:   # the rest keeps its own spacing
            rest = s.lstrip()
            for _k in range(maxsplit):
                rest = rest[len(rest.split()[0]):].lstrip()
            return parts[:maxsplit] + [rest]
        return parts[:maxsplit] + [sep.join(parts[maxsplit:])]
    str.split = _split

_patch(str, "isdigit", lambda s: _all_in(s, _DIGITS))
_patch(str, "isdecimal", lambda s: _all_in(s, _DIGITS))
_patch(str, "isnumeric", lambda s: _all_in(s, _DIGITS))
_patch(str, "isalpha", lambda s: _all_in(s, _LOWER + _UPPER))
_patch(str, "isalnum", lambda s: _all_in(s, _LOWER + _UPPER + _DIGITS))
_patch(str, "isspace", lambda s: _all_in(s, _SPACE))
_patch(str, "islower", lambda s: s.lower() == s and s.upper() != s)
_patch(str, "isupper", lambda s: s.upper() == s and s.lower() != s)
_patch(str, "istitle", lambda s: _s_title(s) == s and s.lower() != s)
_patch(str, "isidentifier", lambda s: bool(s) and s[0] not in _DIGITS and
       _all_in(s, _LOWER + _UPPER + _DIGITS + "_"))
_patch(str, "isascii", lambda s: True)
_patch(str, "isprintable", lambda s: True)
_patch(str, "title", _s_title)
_patch(str, "capitalize", _s_capitalize)
_patch(str, "casefold", lambda s: s.lower())
_patch(str, "swapcase", _s_swapcase)
_patch(str, "center", _s_center)
_patch(str, "partition", _s_partition)
_patch(str, "rpartition", _s_rpartition)
_patch(str, "rfind", _s_rfind)
_patch(str, "rindex", _s_rindex)
_patch(str, "rsplit", _s_rsplit)
_patch(str, "removeprefix", _s_removeprefix)
_patch(str, "removesuffix", _s_removesuffix)
_patch(str, "expandtabs", lambda s, n=8: s.replace("\t", " " * n))


def _dict_setdefault(d, k, v=None):
    if k not in d:
        d[k] = v
    return d[k]


def _dict_fromkeys(keys, v=None):
    out = {}
    for k in keys:
        out[k] = v
    return out


_patch(dict, "setdefault", _dict_setdefault)
_patch(dict, "fromkeys", _dict_fromkeys)


def _set_pop(s):
    for v in s:
        s.remove(v)
        return v
    raise KeyError("pop from an empty set")


_patch(set, "pop", _set_pop)


def _t_count(t, v):
    n = 0
    for x in t:
        if x == v:
            n += 1
    return n


def _t_index(t, v):
    k = 0
    for x in t:
        if x == v:
            return k
        k += 1
    raise ValueError("tuple.index(x): x not in tuple")


_patch(tuple, "count", _t_count)
_patch(tuple, "index", _t_index)

_PK = False   # True under the engine's interpreter (some operators are added)
try:
    _x = (1,) + (2,)
except TypeError:
    _PK = True
    tuple.__add__ = lambda a, b: tuple(list(a) + list(b))
    tuple.__mul__ = lambda a, n: tuple(list(a) * n)

# startswith / endswith with a tuple of choices
try:
    "a".startswith(("a", "b"))
except TypeError:
    _str_startswith = str.startswith
    _str_endswith = str.endswith

    def _startswith(s, p, *rest):
        if isinstance(p, tuple):
            for q in p:
                if _str_startswith(s, q):
                    return True
            return False
        return _str_startswith(s, p)

    def _endswith(s, p, *rest):
        if isinstance(p, tuple):
            for q in p:
                if _str_endswith(s, q):
                    return True
            return False
        return _str_endswith(s, p)
    str.startswith = _startswith
    str.endswith = _endswith


def _fmt_spec(v, spec):
    return ("{:" + spec + "}").format(v) if spec else str(v)


def _pct_one(v, flags, width, prec, conv):
    if conv in "di":
        s = str(int(v))
    elif conv in "fF":
        s = ("{:." + str(prec if prec is not None else 6) + "f}").format(float(v))
    elif conv in "eE":
        s = ("{:." + str(prec if prec is not None else 6) + "e}").format(float(v))
    elif conv in "gG":
        s = str(float(v)) if prec is None else ("{:." + str(prec) + "g}").format(float(v))
    elif conv == "x":
        s = "{:x}".format(int(v))
    elif conv == "X":
        s = "{:X}".format(int(v))
    elif conv == "o":
        s = _oct(int(v))[2:]
    elif conv == "c":
        s = chr(v) if isinstance(v, int) else str(v)
    elif conv == "r":
        s = repr(v)
    else:
        s = str(v)
        if prec is not None:
            s = s[:prec]
    if "+" in flags and conv in "difFeEgG" and not s.startswith("-"):
        s = "+" + s
    elif " " in flags and conv in "difFeEgG" and not s.startswith("-"):
        s = " " + s
    if width is not None and len(s) < width:
        if "-" in flags:
            s = s + " " * (width - len(s))
        elif "0" in flags and conv in "difFeEgGxXo":
            sign = s[0] if s[:1] in "+- " else ""
            body = s[len(sign):]
            s = sign + "0" * (width - len(s)) + body
        else:
            s = " " * (width - len(s)) + s
    return s


def _percent(fmt, args):
    """printf-style formatting: fmt % args."""
    if not isinstance(args, (tuple, dict)):
        args = (args,)
    out = []
    i = 0
    ai = 0
    n = len(fmt)
    while i < n:
        c = fmt[i]
        if c != "%":
            out.append(c)
            i += 1
            continue
        i += 1
        if i < n and fmt[i] == "%":
            out.append("%")
            i += 1
            continue
        key = None
        if i < n and fmt[i] == "(":
            j = fmt.find(")", i)
            key = fmt[i + 1:j]
            i = j + 1
        flags = ""
        while i < n and fmt[i] in "-+ 0#":
            flags += fmt[i]
            i += 1
        width = None
        if i < n and fmt[i] == "*":
            width = int(args[ai])
            ai += 1
            i += 1
        else:
            w = ""
            while i < n and fmt[i] in _DIGITS:
                w += fmt[i]
                i += 1
            width = int(w) if w else None
        prec = None
        if i < n and fmt[i] == ".":
            i += 1
            p = ""
            while i < n and fmt[i] in _DIGITS:
                p += fmt[i]
                i += 1
            prec = int(p) if p else 0
        while i < n and fmt[i] in "hlL":
            i += 1
        conv = fmt[i] if i < n else "s"
        i += 1
        if key is not None:
            v = args[key]
        else:
            v = args[ai]
            ai += 1
        out.append(_pct_one(v, flags, width, prec, conv))
    return "".join(out)


def _oct(v):
    if v == 0:
        return "0o0"
    neg = v < 0
    v = -v if neg else v
    d = ""
    while v:
        d = _DIGITS[v % 8] + d
        v = v // 8
    return ("-0o" if neg else "0o") + d


try:
    _x = "%5.2f" % 1.5
except Exception:
    str.__mod__ = _percent

_str_format = str.format


def _resolve_field(name, kw):
    """A named format field: name, name.attr, name[key]."""
    k = 0
    while k < len(name) and name[k] not in ".[":
        k += 1
    v = kw[name[:k]]
    rest = name[k:]
    while rest:
        if rest[0] == ".":
            j = 1
            while j < len(rest) and rest[j] not in ".[":
                j += 1
            v = getattr(v, rest[1:j])
            rest = rest[j:]
        else:
            j = rest.find("]")
            key = rest[1:j]
            v = v[int(key)] if _all_in(key, _DIGITS) else v[key]
            rest = rest[j + 1:]
    return v


def _format_kw(self, *args, **kw):
    if not kw:
        return _str_format(self, *args)
    out = []
    vals = list(args)
    auto = 0
    i = 0
    n = len(self)
    pos = []
    while i < n:
        c = self[i]
        if c == "{":
            if i + 1 < n and self[i + 1] == "{":
                out.append("{{")
                i += 2
                continue
            j = self.find("}", i)
            field = self[i + 1:j]
            cut = len(field)
            for sep in "!:":
                k = field.find(sep)
                if 0 <= k < cut:
                    cut = k
            name, tail = field[:cut], field[cut:]
            if name == "":
                v = vals[auto] if auto < len(vals) else ""
                auto += 1
            elif _all_in(name, _DIGITS):
                v = vals[int(name)]
            else:
                v = _resolve_field(name, kw)
            out.append("{" + str(len(pos)) + tail + "}")
            pos.append(v)
            i = j + 1
            continue
        if c == "}" and i + 1 < n and self[i + 1] == "}":
            out.append("}}")
            i += 2
            continue
        out.append(c)
        i += 1
    return _str_format("".join(out), *pos)


try:
    "{a}".format(a=1)
except Exception:
    str.format = _format_kw


def format(value, spec=""):
    return _fmt_spec(value, spec)


def pow(a, b, m=None):
    r = a ** b
    return r % m if m is not None else r


def oct(v):
    return _oct(v)


def ascii(v):
    return repr(v)


try:
    frozenset
except NameError:
    frozenset = set

W = 1920
H = 1080

# --------------------------------------------------------------------------
# tables the converter fills in (game program)

_screens = {}       # name -> (draw function, argument binder or None, header props)
_IMAGES = {}        # lower-case file path or image name -> (engine name, w, h, bbox, mask)
_AUDIO = {}         # lower-case file path -> engine audio name
_TRANSFORMS = {}    # ATL transform name -> simple description (alpha fades)


def _norm(s):
    return " ".join(str(s).replace("\\", "/").lower().split())


# --------------------------------------------------------------------------
# story variables

_py_store = {}      # variables the VM doesn't have (set from Python)


def _get(name):
    if _vn3ds.has(name):
        return _vn3ds.get(name)
    if name in _py_store:
        return _py_store[name]
    g = _game_globals()
    if name in g:
        return g[name]
    if name.startswith("persistent."):
        return None
    raise NameError(name)


def _set(name, value):
    if _vn3ds.has(name):
        if value is None or isinstance(value, (bool, int, float, str)):
            _vn3ds.set(name, value)
            return
    g = _game_globals()
    if name in g and not _vn3ds.has(name):
        g[name] = value
        return
    _py_store[name] = value


def _game_globals():
    return globals()


_ARGS = {}          # show screen / call screen arguments -> their values (converter)


_CHUNKS = []


def _load_chunks(chunks):
    """The game's program, a statement at a time: one that fails (a
    feature the interpreter lacks) is reported and the rest still loads.
    Under the engine's interpreter the engine runs each one (pyscreen.c:
    exec() there compiles code in a way class bodies don't work in), then
    calls _finish_load()."""
    if _PK:
        _CHUNKS.extend(chunks)
        return
    g = globals()
    for where, src in chunks:
        try:
            exec(src, g)
        except Exception as e:
            _init_error(where, e)
    _finish_load()


def _finish_load():
    _STYLE_CACHE.clear()
    _STATE_CACHE.clear()


def _init_error(where, e):
    _vn3ds.log("init python " + str(where) + ": " + type(e).__name__ + ": " + str(e))


# --------------------------------------------------------------------------
# small Ren'Py objects

class _Bag(object):
    def __init__(self, **kw):
        for k in kw:
            setattr(self, k, kw[k])

    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


class _Gui(_Bag):
    def text_properties(self, kind=None, accent=False):
        out = {}
        pre = (kind + "_") if kind else ""
        for prop in ("font", "size", "color", "xalign", "text_align", "kerning", "outlines"):
            gname = pre + "text_" + prop if prop != "size" else pre + "text_size"
            if prop == "xalign" and kind:
                gname = kind + "_text_xalign"
            v = getattr(self, gname, None)
            if v is None and kind:
                continue
            if v is not None:
                out[prop] = v
        if kind:
            for state in ("hover", "selected", "insensitive", "idle"):
                v = getattr(self, pre + "text_" + state + "_color", None)
                if v is not None:
                    out[state + "_color"] = v
        return out

    def button_properties(self, kind):
        out = {}
        for prop, gname in (("xsize", "_width"), ("ysize", "_height")):
            v = getattr(self, kind + gname, None)
            if v is not None:
                out[prop] = v
        b = getattr(self, kind + "_borders", None)
        if isinstance(b, Borders):
            out["padding"] = b.padding
        return out

    def button_text_properties(self, kind):
        return self.text_properties(kind)

    def init(self, w, h):
        pass

    def rebuild(self):
        pass


class _Nothing(object):
    """What an unknown config / build setting is: callable, indexable,
    appendable, empty and false, so setting one up does nothing."""

    def __call__(self, *a, **kw):
        return self

    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        return self

    def __getitem__(self, k):
        return self

    def __setitem__(self, k, v):
        pass

    def __iter__(self):
        return iter(())

    def __len__(self):
        return 0

    def __contains__(self, k):
        return False

    def __bool__(self):
        return False

    def append(self, *a):
        pass

    def insert(self, *a):
        pass

    def extend(self, *a):
        pass

    def update(self, *a, **kw):
        pass

    def add(self, *a):
        pass

    def remove(self, *a):
        pass


_NOTHING = _Nothing()


class _Settings(object):
    def __init__(self, **kw):
        for k in kw:
            setattr(self, k, kw[k])

    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        return _NOTHING


gui = _Gui()
config = _Settings(screen_width=W, screen_height=H, name="", version="", keymap={
    "rollback": [], "dismiss": ["K_RETURN", "K_SPACE"], "game_menu": ["K_ESCAPE"]},
    custom_text_tags={}, overlay_screens=[], gestures={}, layers=["master", "screens"],
    underlay=[], window_icon=None)
preferences = _Settings()
build = _Settings()
achievement = _Settings()


class Borders(object):
    def __init__(self, left, top, right, bottom, pad_left=0, pad_top=0, pad_right=0,
                 pad_bottom=0):
        self.left = left
        self.top = top
        self.right = right
        self.bottom = bottom
        self.padding = (left + pad_left, top + pad_top, right + pad_right, bottom + pad_bottom)


class _Persistent(object):
    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        return _get("persistent." + name)

    def __setattr__(self, name, value):
        _set("persistent." + name, value)


persistent = _Persistent()
audio = _Bag()


class Character(object):
    def __init__(self, name=None, kind=None, **kw):
        self.name = name
        self.kw = kw

    def __call__(self, *a, **kw):
        pass


ADVCharacter = NVLCharacter = DynamicCharacter = Character
adv = Character()
nvl = Character()
narrator = Character()
centered = Character()


class Position(object):
    def __init__(self, **kw):
        self.kw = kw


left = right = center = truecenter = topleft = topright = top = offscreenleft = None
offscreenright = default = None


def _(s):
    return s


# Ren'Py's own store variables screens read
_in_replay = None
_game_menu_screen = "save"
_window = False
_version = ""
_history_list = []
main_menu = False
save_name = ""
_quit_slot = None


def _p(s):
    return s


class NoRollback(object):
    pass


SlottedNoRollback = RevertableObject = RevertableList = RevertableDict = object
absolute = float
position = float


def renpy_curry(f):
    def curried(*a, **kw):
        def call(*b, **kw2):
            k = dict(kw)
            k.update(kw2)
            return f(*(a + b), **k)
        return call
    return curried


def renpy_partial(f, *a, **kw):
    def call(*b, **kw2):
        k = dict(kw)
        k.update(kw2)
        return f(*(a + b), **k)
    return call


def _import_name(module, name):
    """`from renpy.x import y`: a global of that name, or nothing."""
    g = globals()
    if name in g:
        return g[name]
    return _NOTHING


def __(s):
    return s


unicode = str
basestring = str
long = int


def xrange(*a):
    return range(*a)


# --------------------------------------------------------------------------
# displayables (values a screen can `add`)

class _Disp(object):
    kind = "disp"


class Null(_Disp):
    def __init__(self, width=0, height=0, **kw):
        self.w = width
        self.h = height


class Solid(_Disp):
    def __init__(self, color, xysize=None, **kw):
        self.color = color
        self.xysize = xysize or (kw.get("xsize"), kw.get("ysize"))


class Text(_Disp):
    def __init__(self, text, **kw):
        self.text = text
        self.kw = kw


class Frame(_Disp):
    def __init__(self, image, *a, **kw):
        self.image = image


class Transform(_Disp):
    def __init__(self, child=None, **kw):
        self.child = child
        self.kw = kw

    def __call__(self, child):
        return Transform(child, **self.kw)


class Fixed(_Disp):
    def __init__(self, *children, **kw):
        self.children = children


class _ImageRef(_Disp):
    def __init__(self, name):
        self.name = name


def ImageReference(name):
    return _ImageRef(" ".join(name) if isinstance(name, tuple) else name)


def Image(name, **kw):
    return _ImageRef(name)


class _ATL(object):
    """A named ATL transform used with `at`: its resting state (the
    properties it ends on, worked out by the converter) applies; the
    motion on the way there doesn't."""

    def __init__(self, name, props=None):
        self.name = name
        self.props = props or {}

    def __call__(self, child=None, *a, **kw):
        return self


class Movie(_Disp):
    def __init__(self, play=None, **kw):
        self.play = play


def Composite(size, *a, **kw):
    return Null(size[0], size[1])


def LiveComposite(size, *a, **kw):
    return Null(size[0], size[1])


def ConditionSwitch(*a, **kw):
    for k in range(0, len(a) - 1, 2):
        try:
            if _eval_cond(a[k]):
                return a[k + 1]
        except Exception:
            pass
    return Null()


def _eval_cond(src):
    if src == "True":
        return True
    return bool(_lookup(src, {}))


class im(object):
    @staticmethod
    def Scale(image, w, h, **kw):
        return image

    @staticmethod
    def Crop(image, *a, **kw):
        return image

    @staticmethod
    def Grayscale(image, **kw):
        return image

    @staticmethod
    def MatrixColor(image, *a, **kw):
        return image

    @staticmethod
    def Composite(size, *a, **kw):
        return Null(size[0], size[1])

    @staticmethod
    def Alpha(image, a, **kw):
        return image


# --------------------------------------------------------------------------
# transitions (no-ops on the screen runtime)

class _Transition(object):
    def __init__(self, *a, **kw):
        pass

    def __call__(self, *a, **kw):
        return self


Dissolve = Fade = MoveTransition = Pixellate = ImageDissolve = AlphaDissolve = _Transition
CropMove = PushMove = Swing = MultipleTransition = ComposeTransition = _Transition
Move = MoveIn = MoveOut = ZoomInOut = RevolveInOut = Shake = SnowBlossom = _Transition
Particles = Flatten = AlphaMask = Window = LayeredImageProxy = _Transition
dissolve = fade = None


def ui_interact(*a, **kw):
    return None


# --------------------------------------------------------------------------
# actions

class Action(object):
    def __call__(self):
        return None

    def get_selected(self):
        return False

    def get_sensitive(self):
        return True


# Leaving a screen: Jump / Call / Return raise one of these; the value they
# carry is in _SIG (the interpreter's exceptions take no attributes).
_SIG = [None]


class _Jump(Exception):
    pass


class _Call(Exception):
    pass


class _ReturnValue(Exception):
    pass


def _signal(cls, value):
    _SIG[0] = value
    return cls()


class _EndRun(Exception):
    pass


class NullAction(Action):
    def __init__(self, *a, **kw):
        pass


class Return(Action):
    def __init__(self, value=None):
        self.value = value

    def __call__(self):
        raise _signal(_ReturnValue, self.value)


class Jump(Action):
    def __init__(self, label):
        self.label = label

    def __call__(self):
        raise _signal(_Jump, self.label)


class Call(Action):
    def __init__(self, label, *a, **kw):
        self.label = label

    def __call__(self):
        raise _signal(_Call, self.label)


def Start(label="start"):
    return Jump(label)


class Show(Action):
    def __init__(self, screen, transition=None, *args, **kwargs):
        self.screen = screen
        self.args = args
        self.kwargs = kwargs

    def __call__(self):
        show_screen(self.screen, self.args, self.kwargs)

    def get_selected(self):
        return get_screen(self.screen) is not None


class ShowTransient(Show):
    pass


class ShowMenu(Action):
    def __init__(self, screen=None, *args, **kwargs):
        self.screen = screen
        self.args = args
        self.kwargs = kwargs

    def __call__(self):
        if self.screen is None or self.screen not in _screens:
            return
        _RUN.menu = True
        show_screen(self.screen, self.args, self.kwargs)


class Hide(Action):
    def __init__(self, screen=None, transition=None, **kw):
        self.screen = screen

    def __call__(self):
        if self.screen is None:
            if _CURRENT:
                hide_screen(_CURRENT[-1].name)
            return
        hide_screen(self.screen)


class ToggleScreen(Action):
    def __init__(self, screen, transition=None, *args, **kwargs):
        self.screen = screen
        self.args = args
        self.kwargs = kwargs

    def __call__(self):
        if get_screen(self.screen) is not None:
            hide_screen(self.screen)
        else:
            show_screen(self.screen, self.args, self.kwargs)

    def get_selected(self):
        return get_screen(self.screen) is not None


class SetVariable(Action):
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def __call__(self):
        _set(self.name, self.value)

    def get_selected(self):
        try:
            return _get(self.name) == self.value
        except NameError:
            return False


class ToggleVariable(Action):
    def __init__(self, name, true_value=True, false_value=False):
        self.name = name
        self.t = true_value
        self.f = false_value

    def __call__(self):
        try:
            cur = _get(self.name)
        except NameError:
            cur = self.f
        _set(self.name, self.f if cur == self.t else self.t)

    def get_selected(self):
        try:
            return _get(self.name) == self.t
        except NameError:
            return False


class SetField(Action):
    def __init__(self, obj, field, value):
        self.obj = obj
        self.field = field
        self.value = value

    def __call__(self):
        setattr(self.obj, self.field, self.value)

    def get_selected(self):
        return getattr(self.obj, self.field, None) == self.value


class ToggleField(Action):
    def __init__(self, obj, field, true_value=True, false_value=False):
        self.obj = obj
        self.field = field
        self.t = true_value
        self.f = false_value

    def __call__(self):
        cur = getattr(self.obj, self.field, self.f)
        setattr(self.obj, self.field, self.f if cur == self.t else self.t)

    def get_selected(self):
        return getattr(self.obj, self.field, None) == self.t


class SetDict(Action):
    def __init__(self, d, key, value):
        self.d = d
        self.key = key
        self.value = value

    def __call__(self):
        self.d[self.key] = self.value

    def get_selected(self):
        return self.d.get(self.key) == self.value


class ToggleDict(Action):
    def __init__(self, d, key, true_value=True, false_value=False):
        self.d = d
        self.key = key
        self.t = true_value
        self.f = false_value

    def __call__(self):
        self.d[self.key] = self.f if self.d.get(self.key) == self.t else self.t


class SetScreenVariable(Action):
    def __init__(self, name, value):
        self.name = name
        self.value = value
        self.scope = _SCOPE[-1] if _SCOPE else None

    def __call__(self):
        if self.scope is not None:
            self.scope[self.name] = self.value

    def get_selected(self):
        return self.scope is not None and self.scope.get(self.name) == self.value


SetLocalVariable = SetScreenVariable


class ToggleScreenVariable(Action):
    def __init__(self, name, true_value=True, false_value=False):
        self.name = name
        self.t = true_value
        self.f = false_value
        self.scope = _SCOPE[-1] if _SCOPE else None

    def __call__(self):
        if self.scope is not None:
            self.scope[self.name] = self.f if self.scope.get(self.name) == self.t else self.t

    def get_selected(self):
        return self.scope is not None and self.scope.get(self.name) == self.t


ToggleLocalVariable = ToggleScreenVariable


class Function(Action):
    def __init__(self, callable, *args, **kwargs):
        self.callable = callable
        self.args = args
        self.kwargs = kwargs

    def __call__(self):
        return self.callable(*self.args, **self.kwargs)


class If(Action):
    def __init__(self, expression, true=None, false=None):
        self.expression = expression
        self.true = true
        self.false = false

    def _pick(self):
        return self.true if self.expression else self.false

    def __call__(self):
        return _run_action(self._pick())

    def get_selected(self):
        return _selected(self._pick())

    def get_sensitive(self):
        return self._pick() is not None


class SelectedIf(Action):
    def __init__(self, expression):
        self.expression = expression

    def get_selected(self):
        return bool(self.expression)


class SensitiveIf(Action):
    def __init__(self, expression):
        self.expression = expression

    def get_sensitive(self):
        return bool(self.expression)


class Play(Action):
    def __init__(self, channel, file, selected=None, **kw):
        self.channel = channel
        self.file = file
        self.kw = kw

    def __call__(self):
        renpy.music.play(self.file, channel=self.channel, loop=self.kw.get("loop"),
                         fadein=self.kw.get("fadein", 0))

    def get_selected(self):
        return renpy.music.get_playing(self.channel) == _audio_name(self.file)


class Queue(Play):
    def __call__(self):
        renpy.music.queue(self.file, channel=self.channel, loop=self.kw.get("loop"))


class Stop(Action):
    def __init__(self, channel, fadeout=None, **kw):
        self.channel = channel
        self.fadeout = fadeout

    def __call__(self):
        renpy.music.stop(self.channel, fadeout=self.fadeout)


class PauseAudio(NullAction):
    pass


class Notify(Action):
    def __init__(self, message):
        self.message = message

    def __call__(self):
        renpy.notify(self.message)


class OpenURL(NullAction):
    pass


class Confirm(Action):
    def __init__(self, prompt, yes, no=None, confirm_selected=False):
        self.yes = yes

    def __call__(self):
        return _run_action(self.yes)


class MainMenu(Action):
    def __init__(self, *a, **kw):
        pass

    def __call__(self):
        raise _EndRun()


Quit = MainMenu
Preference = FileSave = FileLoad = FileAction = FileDelete = FilePage = FilePageNext = NullAction
FilePagePrevious = Rollback = RollForward = Skip = Help = With = Replay = Language = NullAction
SetMixer = SetVoiceMixer = ScreenVariableInputValue = VariableInputValue = NullAction
FieldInputValue = DictInputValue = InvertSelected = Scroll = QueueEvent = NullAction
EndReplay = HideInterface = Screenshot = MouseMove = NullAction


class BarValue(object):
    """What a bar shows: get_value() of get_range()."""

    def __init__(self, *a, **kw):
        self.range = kw.get("range", 1)

    def get_value(self):
        return 0

    def get_range(self):
        return self.range


class FieldValue(BarValue):
    def __init__(self, obj, field, range=1, max_is_zero=False, style="bar", offset=0,
                 step=None, action=None, force_step=False):
        self.obj = obj
        self.field = field
        self.range = range

    def get_value(self):
        return getattr(self.obj, self.field, 0)


class VariableValue(BarValue):
    def __init__(self, variable, range=1, **kw):
        self.variable = variable
        self.range = range

    def get_value(self):
        try:
            return _get(self.variable)
        except NameError:
            return 0


class ScreenVariableValue(BarValue):
    def __init__(self, variable, range=1, **kw):
        self.variable = variable
        self.range = range
        self.scope = _SCOPE[-1] if _SCOPE else {}

    def get_value(self):
        return self.scope.get(self.variable, 0)


class DictValue(BarValue):
    def __init__(self, d, key, range=1, **kw):
        self.d = d
        self.key = key
        self.range = range

    def get_value(self):
        return self.d.get(self.key, 0)


class StaticValue(BarValue):
    def __init__(self, value=0.0, range=1.0):
        self.value = value
        self.range = range

    def get_value(self):
        return self.value


AnimatedValue = StaticValue
LocalVariableValue = ScreenVariableValue
MixerValue = AudioPositionValue = XScrollValue = YScrollValue = BarValue


class MusicRoom(object):
    """Ren'Py's music room: a jukebox of tracks the player has heard."""

    def __init__(self, channel="music", fadeout=0.0, fadein=0.0, loop=True,
                 single_track=False, shuffle=False, stop_action=None, alt=None):
        self.channel = channel
        self.loop = loop
        self.single_track = single_track
        self.filenames = []
        self.playing = None

    def add(self, filename, always_unlocked=False, action=None):
        self.filenames.append(filename)

    def is_unlocked(self, filename):
        return True

    def play(self, filename=None, offset=0, queue=False):
        if filename is None:
            if not self.filenames:
                return
            k = self.filenames.index(self.playing) if self.playing in self.filenames else -1
            filename = self.filenames[(k + offset) % len(self.filenames)]
        self.playing = filename
        renpy.music.play(filename, channel=self.channel, loop=self.loop)

    def Play(self, filename=None):
        return _RoomPlay(self, filename)

    def Next(self):
        return _RoomStep(self, 1)

    def Previous(self):
        return _RoomStep(self, -1)

    def Stop(self):
        return _RoomStop(self)

    def RandomPlay(self):
        return self.Next()

    def TogglePlay(self):
        return self.Play()

    def ToggleLoop(self):
        return NullAction()

    def ToggleShuffle(self):
        return NullAction()

    def ToggleSingleTrack(self):
        return NullAction()

    def get_current_index(self):
        return self.filenames.index(self.playing) if self.playing in self.filenames else 0

    def periodic(self, st):
        return None


class _RoomPlay(Action):
    def __init__(self, room, filename):
        self.room = room
        self.filename = filename

    def __call__(self):
        self.room.play(self.filename)

    def get_selected(self):
        return self.filename is not None and self.room.playing == self.filename


class _RoomStep(Action):
    def __init__(self, room, step):
        self.room = room
        self.step = step

    def __call__(self):
        self.room.play(None, self.step)


class _RoomStop(Action):
    def __init__(self, room):
        self.room = room

    def __call__(self):
        self.room.playing = None
        renpy.music.stop(self.room.channel)


class Gallery(object):
    def __init__(self):
        self.buttons = {}
        self.locked_button = None
        self.transition = None
        self.navigation = False
        self.unlocked_advance = False

    def button(self, name):
        self.buttons[name] = []
        self._cur = name

    def image(self, *a, **kw):
        self.buttons[self._cur].append(a)

    def unlock(self, *a):
        pass

    def unlock_image(self, *a):
        self.image(*a)

    def condition(self, *a):
        pass

    def display(self, *a):
        self.image(*a)

    def transform(self, *a):
        pass

    def make_button(self, name, unlocked, locked=None, **kw):
        return _ImageRef(unlocked)

    def Action(self, name):
        return NullAction()

    def Return(self):
        return Return()

    def Next(self, unlocked=False):
        return NullAction()

    def Previous(self, unlocked=False):
        return NullAction()


# --------------------------------------------------------------------------
# renpy.*

def _channel(name):
    n = (name or "sound").lower()
    if n == "music" or "music" in n or "bgm" in n or "ambien" in n:
        return 0
    if "voice" in n:
        return 2
    return 1


def _audio_name(f):
    if f is None:
        return ""
    if isinstance(f, (list, tuple)):
        f = f[0] if f else ""
    n = _norm(f)
    if n.startswith("<"):
        n = n[n.find(">") + 1:]
    return _AUDIO.get(n) or _AUDIO.get("audio/" + n) or ""


class _Music(object):
    def __init__(self, default_channel):
        self.default = default_channel

    def play(self, filenames, channel=None, loop=None, fadeout=None, synchro_start=False,
             fadein=0, tight=None, if_changed=False, relative_volume=1.0):
        ch = channel or self.default
        name = _audio_name(filenames)
        if not name:
            return
        if loop is None:
            loop = _channel(ch) == 0
        if if_changed and _vn3ds.playing(_channel(ch)) == name:
            return
        _vn3ds.play(_channel(ch), name, bool(loop), float(fadein or 0))

    def queue(self, filenames, channel=None, loop=None, clear_queue=True, fadein=0, tight=None,
              relative_volume=1.0):
        ch = channel or self.default
        name = _audio_name(filenames)
        if name:
            _vn3ds.queue(_channel(ch), name, bool(loop if loop is not None else _channel(ch) == 0))

    def stop(self, channel=None, fadeout=None):
        _vn3ds.stop(_channel(channel or self.default), float(fadeout or 0))

    def get_playing(self, channel=None):
        return _vn3ds.playing(_channel(channel or self.default)) or None

    def is_playing(self, channel=None):
        return bool(_vn3ds.playing(_channel(channel or self.default)))

    def set_volume(self, *a, **kw):
        pass

    def set_pause(self, *a, **kw):
        pass

    def register_channel(self, *a, **kw):
        pass

    def get_pos(self, channel=None):
        return None

    def get_duration(self, channel=None):
        return None

    def channel_defined(self, name):
        return True


class _Random(object):
    def __init__(self):
        import random as _r
        self.r = _r

    def seed(self, *a):
        pass

    def random(self):
        return self.r.random()

    def randint(self, a, b):
        return self.r.randint(a, b)

    def choice(self, seq):
        return seq[self.r.randint(0, len(seq) - 1)]

    def shuffle(self, seq):
        self.r.shuffle(seq)

    def uniform(self, a, b):
        return a + (b - a) * self.r.random()

    def randrange(self, a, b=None, step=1):
        if b is None:
            a, b = 0, a
        return a + step * self.r.randint(0, (b - a - 1) // step)

    def sample(self, seq, k):
        pool = list(seq)
        out = []
        for _i in range(k):
            out.append(pool.pop(self.r.randint(0, len(pool) - 1)))
        return out

    def Random(self, seed=None):
        return self


class _Renpy(object):
    def __init__(self):
        self.music = _Music("music")
        self.sound = _Music("sound")
        self.random = _Random()
        self.display = _Bag(im=im)
        self.config = config
        self.TEXT_TEXT = 1
        self.TEXT_TAG = 2
        self.TEXT_DISPLAYABLE = 3

    # displayables for game classes to derive from
    class Displayable(object):
        def __init__(self, *a, **kw):
            pass

        def render(self, *a):
            return None

        def event(self, *a):
            return None

        def visit(self):
            return []

        def per_interact(self):
            pass

    class Render(object):
        def __init__(self, w, h):
            self.width = w
            self.height = h

        def blit(self, *a, **kw):
            pass

        def subpixel_blit(self, *a, **kw):
            pass

        def place(self, *a, **kw):
            pass

        def get_size(self):
            return (self.width, self.height)

    class Container(Displayable):
        pass

    def render(self, d, w, h, st, at):
        return _Renpy.Render(w, h)

    def run_action(self, action):
        return _run_action(action)

    def run(self, action):
        return _run_action(action)

    def is_selected(self, action):
        return _selected(action)

    def is_sensitive(self, action):
        return _sensitive(action)

    def current_screen(self):
        return _CURRENT[-1] if _CURRENT else None

    def get_screen_variable(self, name, screen=None, layer=None):
        s = get_screen(screen) if screen else (_CURRENT[-1] if _CURRENT else None)
        return s.scope.get(name) if s is not None else None

    def set_screen_variable(self, name, value, screen=None, layer=None):
        s = get_screen(screen) if screen else (_CURRENT[-1] if _CURRENT else None)
        if s is not None:
            s.scope[name] = value

    def redraw(self, *a):
        pass

    def restart_interaction(self):
        pass

    def free_memory(self):
        pass

    def pure(self, f):
        return f

    def const(self, f):
        return f

    def play(self, filename, channel="sound", **kw):
        self.music.play(filename, channel=channel, loop=kw.get("loop", False))

    def notify(self, message):
        show_screen("notify", (), {"message": message})

    def jump(self, label):
        raise _signal(_Jump, label)

    def call(self, label, *a, **kw):
        raise _signal(_Call, label)

    def return_statement(self, value=None):
        raise _signal(_ReturnValue, value)

    def show_screen(self, name, *args, **kwargs):
        kwargs.pop("_layer", None)
        kwargs.pop("_tag", None)
        kwargs.pop("_transient", None)
        show_screen(name, args, kwargs)

    def hide_screen(self, name, layer=None):
        hide_screen(name)

    def get_screen(self, name, layer=None):
        return get_screen(name)

    def call_screen(self, name, *args, **kwargs):
        show_screen(name, args, kwargs)
        return None

    def get_widget(self, *a):
        return None

    def loadable(self, f):
        n = _norm(f)
        return n in _IMAGES or n in _AUDIO

    def exists(self, f):
        return self.loadable(f)

    def has_image(self, name, exact=False):
        return _norm(name) in _IMAGES

    def seen_image(self, name):
        return True

    def seen_label(self, name):
        return bool(_vn3ds.seen_label(name))

    def seen_audio(self, name):
        return True

    def mark_image_seen(self, name):
        pass

    def showing(self, name, layer=None):
        return False

    def variant(self, name):
        if isinstance(name, (list, tuple)):
            return any(self.variant(n) for n in name)
        return name in ("pc", "large", "mouse", None)

    def pause(self, *a, **kw):
        return None

    def input(self, prompt="", default="", **kw):
        return default

    def save_persistent(self):
        pass

    def full_restart(self, *a, **kw):
        raise _EndRun()

    def quit(self, *a, **kw):
        raise _EndRun()

    def end_replay(self):
        pass

    def is_in_test(self):
        return False

    def get_physical_size(self):
        return (W, H)

    def version(self, tuple=False):
        return (8, 0, 0) if tuple else "Ren'Py 8.0.0"

    def version_only(self):
        return "8.0.0"

    def image(self, name, d):
        pass

    def with_statement(self, *a, **kw):
        pass

    def transition(self, *a, **kw):
        pass

    def show(self, *a, **kw):
        pass

    def hide(self, *a, **kw):
        pass

    def scene(self, *a, **kw):
        pass

    def say(self, *a, **kw):
        pass

    def predict(self, *a, **kw):
        pass

    def predicting(self):
        return False

    def get_mouse_pos(self):
        return (0, 0)

    def set_mouse_pos(self, *a, **kw):
        pass

    def displayable(self, d):
        return d

    def easy_displayable(self, d):
        return d

    def count_displayables_in_layer(self, *a):
        return 0

    def get_say_attributes(self):
        return None

    def get_attributes(self, *a):
        return ()

    def last_interact_type(self):
        return "say"

    def context(self):
        return _Bag()

    def game_menu(self, *a, **kw):
        pass

    def invoke_in_new_context(self, f, *a, **kw):
        return f(*a, **kw)

    def call_in_new_context(self, *a, **kw):
        return None

    def get_game_runtime(self):
        return 0.0

    def time(self):
        return _RUN.clock


class _Store(object):
    """`store`: the game's globals (here: this module's)."""

    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        g = globals()
        if name in g:
            return g[name]
        return _get(name)

    def __setattr__(self, name, value):
        if _vn3ds.has(name):
            _set(name, value)
        else:
            globals()[name] = value


renpy = _Renpy()
renpy.easy = _Bag(displayable=lambda d: d)
renpy.curry = renpy_curry
renpy.partial = renpy_partial
renpy.store = _Store()
store = renpy.store


# --------------------------------------------------------------------------
# styles

_STYLES = {}        # name -> (parent or None, props dict)

_BASE_STYLES = {
    "default": (None, {"size": 22, "color": "#ffffff", "spacing": 0}),
    "text": ("default", {}),
    "button": ("default", {}),
    "button_text": ("default", {"xalign": 0.0}),
    "image_button": ("default", {}),
    "frame": ("default", {"background": None}),
    "window": ("default", {}),
    "label": ("default", {}),
    "label_text": ("default", {}),
    "vbox": ("default", {}),
    "hbox": ("default", {}),
    "fixed": ("default", {}),
    "grid": ("default", {}),
    "side": ("default", {}),
    "viewport": ("default", {}),
    "vpgrid": ("default", {}),
    "imagemap": ("default", {}),
    "bar": ("default", {"ysize": 30}),
    "vbar": ("default", {"xsize": 30}),
    "input": ("default", {}),
    "hyperlink_text": ("default", {}),
}


def _style(name, parent=None, *dicts, **props):
    if dicts:
        merged = {}
        for d in dicts:
            if isinstance(d, dict):
                merged.update(d)
        merged.update(props)
        props = merged
    old = _STYLES.get(name)
    if old is not None and parent is None:
        parent = old[0]
        merged = dict(old[1])
        merged.update(props)
        props = merged
    _STYLES[name] = (parent, props)


def _style_props(name, props):
    _style(name, None, **props)


def _style_take(name, other):
    p = _STYLES.get(other)
    if p:
        _STYLES[name] = (p[0], dict(p[1]))


def _style_clear(name):
    p = _STYLES.get(name)
    _STYLES[name] = (p[0] if p else None, {})


def _canon_into(out, props):
    """Merges props into out the way Ren'Py's styles do: a later xalign
    overrides an earlier xpos (align, pos, anchor, xycenter, area, offset,
    xysize are expanded to xpos/xanchor/xoffset/xsize and their y)."""
    for k in props:
        v = props[k]
        pre = ""
        base = k
        for p in _STATE_PREFIXES:
            if k.startswith(p):
                pre = p
                base = k[len(p):]
                break
        if base == "align":
            a, b = _pair(v)
            out[pre + "xpos"] = a
            out[pre + "xanchor"] = a
            out[pre + "ypos"] = b
            out[pre + "yanchor"] = b
        elif base == "xalign" or base == "yalign":
            ax = base[0]
            out[pre + ax + "pos"] = v
            out[pre + ax + "anchor"] = v
        elif base == "pos":
            a, b = _pair(v)
            out[pre + "xpos"] = a
            out[pre + "ypos"] = b
        elif base == "anchor":
            a, b = _pair(v)
            out[pre + "xanchor"] = a
            out[pre + "yanchor"] = b
        elif base == "xycenter":
            a, b = _pair(v)
            out[pre + "xpos"] = a
            out[pre + "ypos"] = b
            out[pre + "xanchor"] = 0.5
            out[pre + "yanchor"] = 0.5
        elif base == "xcenter" or base == "ycenter":
            ax = base[0]
            out[pre + ax + "pos"] = v
            out[pre + ax + "anchor"] = 0.5
        elif base == "offset":
            a, b = _pair(v)
            out[pre + "xoffset"] = a
            out[pre + "yoffset"] = b
        elif base == "area" and isinstance(v, (tuple, list)) and len(v) >= 4:
            out[pre + "xpos"] = v[0]
            out[pre + "ypos"] = v[1]
            out[pre + "xanchor"] = 0
            out[pre + "yanchor"] = 0
            out[pre + "xsize"] = v[2]
            out[pre + "ysize"] = v[3]
        elif base == "xysize":
            a, b = _pair(v)
            out[pre + "xsize"] = a
            out[pre + "ysize"] = b
        elif base in ("padding", "margin", "xpadding", "ypadding", "xmargin", "ymargin"):
            kind = "padding" if base.endswith("padding") else "margin"
            if base[0] in "xy":
                sides = ("left", "right") if base[0] == "x" else ("top", "bottom")
                for sd in sides:
                    out[pre + sd + "_" + kind] = v
            else:
                if isinstance(v, (tuple, list)) and len(v) == 2:
                    l, t, r, b = v[0], v[1], v[0], v[1]
                elif isinstance(v, (tuple, list)) and len(v) >= 4:
                    l, t, r, b = v[0], v[1], v[2], v[3]
                else:
                    l = t = r = b = v
                out[pre + "left_" + kind] = l
                out[pre + "top_" + kind] = t
                out[pre + "right_" + kind] = r
                out[pre + "bottom_" + kind] = b
        elif base == "maximum":
            a, b = _pair(v)
            out[pre + "xmaximum"] = a
            out[pre + "ymaximum"] = b
        elif base == "minimum":
            a, b = _pair(v)
            out[pre + "xminimum"] = a
            out[pre + "yminimum"] = b
        else:
            out[k] = v
    return out


def _style_chain(name):
    """Props of a style with its ancestry, nearest last."""
    seen = []
    n = name
    while n and n not in seen and len(seen) < 32:
        seen.append(n)
        if n in _STYLES:
            parent = _STYLES[n][0]
        elif n in _BASE_STYLES:
            parent = _BASE_STYLES[n][0]
        elif "_" in n:
            parent = n.split("_", 1)[1]   # foo_button -> button
        else:
            parent = "default"
        if parent is None and n != "default":
            parent = "default" if n not in ("default",) else None
        n = parent
    out = {}
    for n in reversed(seen):
        base = _BASE_STYLES.get(n)
        if base:
            _canon_into(out, base[1])
        if n in _STYLES:
            _canon_into(out, _STYLES[n][1])
    return out


_STYLE_CACHE = {}


def style_props(name):
    p = _STYLE_CACHE.get(name)
    if p is None:
        p = _STYLE_CACHE[name] = _style_chain(name)
    return p


class _StyleNS(object):
    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        return _StyleRef(name)


_STYLE_REF_NAMES = {}


class _StyleRef(object):
    """style.name: set and read a style's properties (style.default.size = 20)."""

    def __init__(self, name):
        _STYLE_REF_NAMES[id(self)] = name

    def __setattr__(self, k, v):
        _style(_STYLE_REF_NAMES.get(id(self), "default"), None, **{k: v})
        _STYLE_CACHE.clear()
        _STATE_CACHE.clear()

    def __getattr__(self, k):
        if k.startswith("__"):
            raise AttributeError(k)
        return style_props(_STYLE_REF_NAMES.get(id(self), "default")).get(k)


style = _StyleNS()


# --------------------------------------------------------------------------
# colours

_RGBA = {}


def rgba(c, default=0xFFFFFFFF):
    if c is None:
        return default
    if isinstance(c, str):
        v = _RGBA.get(c)
        if v is None:
            v = _RGBA[c] = _rgba(c, default)
        return v
    return _rgba(c, default)


def _rgba(c, default):
    if isinstance(c, int):
        return c
    if isinstance(c, (tuple, list)):
        r, g, b = int(c[0]), int(c[1]), int(c[2])
        a = int(c[3]) if len(c) > 3 else 255
        return (r << 24) | (g << 16) | (b << 8) | a
    s = str(c).strip()
    if not s.startswith("#"):
        return default
    h = s[1:]
    try:
        if len(h) in (3, 4):
            v = [int(ch, 16) * 17 for ch in h]
        elif len(h) in (6, 8):
            v = [int(h[k:k + 2], 16) for k in range(0, len(h), 2)]
        else:
            return default
    except ValueError:
        return default
    if len(v) == 3:
        v.append(255)
    return (v[0] << 24) | (v[1] << 16) | (v[2] << 8) | v[3]


def Color(c=None, **kw):
    return c


def _is_color(s):
    return isinstance(s, str) and s.startswith("#")


# --------------------------------------------------------------------------
# the tree a screen builds

class Node(object):
    def __init__(self, kind, pos, props, nid):
        self.kind = kind
        self.pos = pos
        self.props = props
        self.id = nid
        self.children = []
        self.parent = None
        self.prefix = None       # style_prefix in effect
        self.rect = None         # placed (x, y, w, h)
        self.state = "idle"      # buttons: idle/hover/selected_idle/... ; others: parent's
        self.key = None          # stable identity: (screen, id, occurrence)
        self.screen = None
        self.kids = None         # _children_box, once measured
        self.pad = None          # (l, t, r, b), once measured
        self.mar = None

    def __enter__(self):
        _UI.stack.append(self)
        return self

    def __exit__(self, *a):
        _UI.stack.pop()
        return False


class _Builder(object):
    """The `_ui` of translated screens."""

    def __init__(self):
        self.stack = []
        self.seen = {}
        self.screen = None
        self.transcludes = []

    def _mk(self, kind, pos, kw):
        nid = kw.pop("_id", 0)
        parent = self.stack[-1] if self.stack else None
        n = Node(kind, pos, kw, nid)
        k = (nid,)
        c = self.seen.get(k, 0)
        self.seen[k] = c + 1
        n.key = (self.screen.name if self.screen else "", nid, c)
        n.screen = self.screen
        if "style_prefix" in kw:
            n.prefix = kw["style_prefix"]
        elif "style_group" in kw:
            n.prefix = kw["style_group"]
        elif parent is not None:
            n.prefix = parent.prefix
        if parent is not None:
            n.parent = parent
            parent.children.append(n)
        return n

    def props(self, **kw):
        if not self.stack:
            return
        n = self.stack[-1]
        n.props.update(kw)
        if "style_prefix" in kw or "style_group" in kw:
            n.prefix = kw.get("style_prefix", kw.get("style_group"))
            for c in n.children:   # children made before the line follow it too
                if c.prefix is None:
                    c.prefix = n.prefix

    def pack(self, *a, **k):
        return (a, k)

    def use(self, name, _args=((), {}), _transclude=None, _id=0):
        entry = _screens.get(name)
        if entry is None:
            return
        fn, binder, hdr = entry
        a, k = _args
        scope = binder(*a, **k) if binder else {}
        scope["_transclude_fn"] = _transclude
        _SCOPE.append(scope)
        self.transcludes.append(_transclude)
        try:
            fn(self, scope)
        finally:
            _SCOPE.pop()
            self.transcludes.pop()

    def transclude(self):
        fn = self.transcludes[-2] if len(self.transcludes) > 1 else None
        fn = self.transcludes[-1] if self.transcludes else None
        if fn:
            self.transcludes.append(None)
            try:
                fn()
            finally:
                self.transcludes.pop()


def _maker(kind):
    def make(self, *pos, **kw):
        return self._mk(kind, pos, kw)
    return make


for _k in ("add", "image", "text", "label", "textbutton", "imagebutton", "button", "frame",
           "window", "fixed", "vbox", "hbox", "grid", "vpgrid", "side", "viewport", "imagemap",
           "hotspot", "hotbar", "bar", "vbar", "null", "input", "timer", "key", "mousearea",
           "drag", "draggroup", "nearrect", "dismiss", "transform", "on", "areapicker"):
    setattr(_Builder, _k, _maker(_k))

_UI = _Builder()
_SCOPE = []


# --------------------------------------------------------------------------
# shown screens

class Shown(object):
    def __init__(self, name, scope, persistent=False):
        self.name = name
        self.scope = scope
        self.root = None
        self.persistent = persistent   # shown by the script (kept in _vn3ds_screens)
        self.t = 0.0                   # seconds shown
        hdr = _screens[name][2] if name in _screens else {}
        self.modal = bool(hdr.get("modal", False))
        self.zorder = int(hdr.get("zorder", 0) or 0)
        self.tag = hdr.get("tag") or name
        self.events_shown = False


_SHOWN = []         # Shown, drawing order (zorder, then age)
_CURRENT = []       # screen being drawn (for Hide())
_TIMERS = {}        # node key -> seconds since it was (re)started


def get_screen(name):
    for s in _SHOWN:
        if s.name == name or s.tag == name:
            return s
    return None


def _bind(name, args, kwargs):
    entry = _screens.get(name)
    if entry is None:
        return None
    binder = entry[1]
    try:
        return binder(*args, **kwargs) if binder else dict(kwargs)
    except Exception as e:
        _vn3ds.log("screen " + name + ": " + str(e))
        return {}


def show_screen(name, args=(), kwargs=None, persistent=False):
    if name not in _screens:
        return None
    scope = _bind(name, args, kwargs or {})
    if scope is None:
        return None
    s = Shown(name, scope, persistent)
    old = get_screen(s.tag)
    if old is not None:
        _SHOWN.remove(old)
    k = len(_SHOWN)
    while k > 0 and _SHOWN[k - 1].zorder > s.zorder:
        k -= 1
    _SHOWN.insert(k, s)
    _RUN.changed = True
    return s


def hide_screen(name):
    s = get_screen(name)
    if s is None:
        return
    _SHOWN.remove(s)
    _RUN.changed = True
    if s.persistent:
        _RUN.overlays_changed = True


# --------------------------------------------------------------------------
# drawing a screen: build, style, measure, place

def _render(s):
    _UI.stack = []
    _UI.seen = {}
    _UI.screen = s
    _UI.transcludes = []
    root = Node("fixed", (), {}, 0)
    root.key = (s.name, 0, 0)
    root.screen = s
    root.prefix = None
    _UI.stack.append(root)
    _SCOPE.append(s.scope)
    _CURRENT.append(s)
    try:
        _screens[s.name][0](_UI, s.scope)
    except (_Jump, _Call, _ReturnValue, _EndRun):
        raise
    except Exception as e:
        _err("screen " + s.name, e)
    finally:
        _SCOPE.pop()
        _CURRENT.pop()
        _UI.stack = []
    for k in ("modal", "zorder", "tag"):
        if k in root.props:
            if k == "modal":
                s.modal = bool(root.props[k])
            elif k == "zorder":
                s.zorder = int(root.props[k] or 0)
    s.root = root
    return root


_ERRORS = {}


def _err(where, e):
    msg = where + ": " + type(e).__name__ + ": " + str(e)
    if msg not in _ERRORS:
        _ERRORS[msg] = 1
        _vn3ds.log(msg)


_STYLE_NAMES = {}


def _style_name(n, kind=None):
    st = n.props.get("style")
    if isinstance(st, str):
        return st
    k = n.kind + "|" + str(kind) + "|" + str(n.prefix) + "|" + str(n.props.get("style_suffix"))
    name = _STYLE_NAMES.get(k)
    if name is None:
        name = _STYLE_NAMES[k] = _style_name_of(n, kind)
    return name


def _style_name_of(n, kind):
    kind = kind or {"textbutton": "button", "imagebutton": "image_button", "add": "image",
                    "window": "window", "hotspot": "button", "hotbar": "bar",
                    "label": "label", "null": "default"}.get(n.kind, n.kind)
    suffix = n.props.get("style_suffix")
    if suffix:
        kind = suffix
    if n.prefix:
        return n.prefix + "_" + kind
    return kind


_STATE_CACHE = {}
_MISS = object()


class _Props(object):
    """A node's properties: its own over its style's (no copy of the style)."""

    def __init__(self, own, base):
        self.own = own
        self.base = base

    def get(self, k, d=None):
        v = self.own.get(k, _MISS)
        if v is _MISS:
            return self.base.get(k, d)
        return v

    def __getitem__(self, k):
        v = self.get(k, _MISS)
        if v is _MISS:
            raise KeyError(k)
        return v

    def __contains__(self, k):
        return k in self.own or k in self.base


def _style_state(name, state):
    """A style's properties for a state (cached; styles don't change while
    screens are shown)."""
    k = (name, state)
    p = _STATE_CACHE.get(k)
    if p is None:
        p = _STATE_CACHE[k] = _for_state(style_props(name), state)
    return p


def _sp(n, kind=None):
    """The node's style properties plus its own, for its current state."""
    base = _style_state(_style_name(n, kind), n.state)
    own = n.props
    if not own:
        return base
    for k in own:
        if k[:1] in "ihsa" and _has_state_prefix(k):   # hover_..., selected_...: rare
            own = _for_state(_canon_into({}, own), n.state)
            break
    mine = _canon_into({}, own)
    if "at" in n.props:
        for t in _transforms_of(n):   # `at` transforms: their resting state, on top
            _canon_into(mine, _for_state(_canon_into({}, t), n.state))
    return _Props(mine, base)


def _transforms_of(n):
    at = n.props.get("at")
    if at is None:
        return []
    ats = at if isinstance(at, (list, tuple)) else [at]
    out = []
    for t in ats:
        if isinstance(t, _ATL):
            out.append(t.props)
        elif isinstance(t, Transform):
            out.append(t.kw)
    return out


def _for_state(props, state):
    out = {}
    order = ["", "idle_", "hover_", "selected_", "selected_idle_", "selected_hover_",
             "insensitive_", "selected_insensitive_"]
    want = {"idle": ["", "idle_"], "hover": ["", "hover_"],
            "selected_idle": ["", "idle_", "selected_", "selected_idle_"],
            "selected_hover": ["", "hover_", "selected_", "selected_hover_"],
            "insensitive": ["", "insensitive_"],
            "selected_insensitive": ["", "insensitive_", "selected_", "selected_insensitive_"]
            }.get(state, [""])
    for pre in order:
        if pre not in want:
            continue
        for k in props:
            if pre == "":
                if not _has_state_prefix(k):
                    out[k] = props[k]
            elif k.startswith(pre) and not _has_state_prefix(k[len(pre):]):
                out[k[len(pre):]] = props[k]
    return out


_STATE_PREFIXES = ("idle_", "hover_", "selected_", "insensitive_", "activate_")


def _has_state_prefix(k):
    for p in _STATE_PREFIXES:
        if k.startswith(p):
            return True
    return False


def _num(v, total):
    """A position or size value: float = fraction, int = pixels."""
    if v is None:
        return None
    if isinstance(v, float) and -1.0 <= v <= 2.0 and not isinstance(v, bool):
        return v * total
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _pair(v):
    if isinstance(v, (tuple, list)):
        if len(v) >= 2:
            return v[0], v[1]
        if len(v) == 1:
            return v[0], v[0]
    return v, v


def _padding(p):
    """(left, top, right, bottom); props are canonical (_canon_into)."""
    return (float(p.get("left_padding") or 0), float(p.get("top_padding") or 0),
            float(p.get("right_padding") or 0), float(p.get("bottom_padding") or 0))


def _margin(p):
    return (float(p.get("left_margin") or 0), float(p.get("top_margin") or 0),
            float(p.get("right_margin") or 0), float(p.get("bottom_margin") or 0))


# -- images

def image_info(d):
    """(engine name, w, h, bbox, mask) of a displayable naming an image."""
    if d is None:
        return None
    if isinstance(d, _ImageRef):
        d = d.name
    if isinstance(d, (list, tuple)):
        d = " ".join(str(x) for x in d)
    if not isinstance(d, str):
        return None
    n = _norm(d)
    info = _IMAGES.get(n)
    if info is None and not n.startswith("images/"):
        info = _IMAGES.get("images/" + n)
    return info


def _expand_auto(auto, state):
    names = {"idle": ["idle"], "hover": ["hover", "idle"],
             "selected_idle": ["selected_idle", "selected", "idle"],
             "selected_hover": ["selected_hover", "selected", "hover", "idle"],
             "insensitive": ["insensitive", "idle"],
             "selected_insensitive": ["selected_insensitive", "insensitive", "idle"]}
    for st in names.get(state, ["idle"]):
        cand = auto.replace("%s", st)
        if image_info(cand) is not None:
            return cand
    return None


# -- text

def _strip_tags(s):
    out = []
    k = 0
    while k < len(s):
        c = s[k]
        if c == "{":
            if s.startswith("{{", k):
                out.append("{")
                k += 2
                continue
            j = s.find("}", k)
            if j < 0:
                out.append(s[k:])
                break
            k = j + 1
            continue
        out.append(c)
        k += 1
    return "".join(out)


def _lookup(expr, scope):
    """The value of a simple expression in [interpolation]: names,
    attributes, [index] and calls are left to eval when it is there."""
    g = _game_globals()
    try:
        return eval(expr, g, _ScopeView(scope))
    except Exception:
        pass
    parts = expr.split(".")
    name = parts[0]
    if name in scope:
        v = scope[name]
    elif name in g:
        v = g[name]
    else:
        try:
            v = _get(name)
        except NameError:
            return ""
    for p in parts[1:]:
        v = getattr(v, p, None)
    return v


class _ScopeView(dict):
    def __init__(self, scope):
        dict.__init__(self, scope)

    def __missing__(self, k):
        try:
            return _get(k)
        except NameError:
            raise KeyError(k)


def interpolate(s, scope):
    if not isinstance(s, str):
        s = str(s)
    if "[" not in s:
        return s
    out = []
    k = 0
    while k < len(s):
        c = s[k]
        if c == "[":
            if s.startswith("[[", k):
                out.append("[")
                k += 2
                continue
            j = s.find("]", k)
            if j < 0:
                out.append(s[k:])
                break
            expr = s[k + 1:j]
            if "!" in expr:
                expr = expr.split("!")[0]
            if ":" in expr and "[" not in expr:
                expr = expr.split(":")[0]
            v = _lookup(expr.strip(), scope)
            out.append("" if v is None else str(v))
            k = j + 1
            continue
        out.append(c)
        k += 1
    return "".join(out)


def _wrap(text, size, maxw):
    lines = []
    for para in text.split("\n"):
        if maxw is None or _vn3ds.text_width(para, size) <= maxw:
            lines.append(para)
            continue
        cur = ""
        for word in para.split(" "):
            cand = word if not cur else cur + " " + word
            if cur and _vn3ds.text_width(cand, size) > maxw:
                lines.append(cur)
                cur = word
            else:
                cur = cand
        lines.append(cur)
    return lines


# -- measuring

def _size_prop(p, aw, ah):
    w = h = None
    if p.get("xysize") is not None:
        a, b = _pair(p["xysize"])
        w, h = _num(a, aw), _num(b, ah)
    if p.get("area") is not None and len(p["area"]) >= 4:
        w, h = _num(p["area"][2], aw), _num(p["area"][3], ah)
    if p.get("xsize") is not None:
        w = _num(p["xsize"], aw)
    if p.get("ysize") is not None:
        h = _num(p["ysize"], ah)
    if p.get("xfill"):
        w = aw
    if p.get("yfill"):
        h = ah
    return w, h


def _minmax(p, w, h, aw, ah, text=False):
    """xminimum / xmaximum (canonical: minimum and maximum are expanded)."""
    if not text:
        v = p.get("xminimum")
        if v is not None:
            w = max(w, _num(v, aw))
        v = p.get("yminimum")
        if v is not None:
            h = max(h, _num(v, ah))
    v = p.get("xmaximum")
    if v is not None:
        w = min(w, _num(v, aw))
    v = p.get("ymaximum")
    if v is not None:
        h = min(h, _num(v, ah))
    return w, h


def _children_box(n):
    """Children that draw (timers, keys and `on` don't); kept on the node."""
    k = n.kids
    if k is None:
        k = n.kids = [c for c in n.children if c.kind not in ("timer", "key", "on")]
    return k


def measure(n, aw, ah):
    """Size of node n given the available area; sets n.sp (style props)."""
    if n.kind in ("button", "textbutton", "imagebutton", "hotspot"):
        _button_state(n)
    elif n.parent is not None:
        n.state = n.parent.state
    p = n.sp = _sp(n)
    fw, fh = _size_prop(p, aw, ah)
    pl, pt, pr, pb = n.pad = _padding(p)
    ml, mt, mr, mb = n.mar = _margin(p)
    inner_w = (fw if fw is not None else aw) - pl - pr - ml - mr
    inner_h = (fh if fh is not None else ah) - pt - pb - mt - mb
    if p.get("xmaximum") is not None:
        inner_w = min(inner_w, _num(p["xmaximum"], aw) - pl - pr)
    k = n.kind
    w = h = 0.0
    if k in ("text", "label"):
        lim = inner_w if fw is None else min(fw, aw) - pl - pr
        w, h = _measure_text(n, lim, inner_h)
        fw = None
    elif k == "textbutton":
        w, h = _measure_text(n, inner_w, inner_h)
    elif k in ("add", "image"):
        w, h = _measure_image(n, aw, ah)
    elif k == "imagebutton":
        w, h = _measure_imagebutton(n)
    elif k == "null":
        w = _num(p.get("width", 0), aw) or 0
        h = _num(p.get("height", 0), ah) or 0
    elif k in ("vbox", "hbox"):
        w, h = _measure_box(n, inner_w, inner_h, k == "vbox")
    elif k in ("grid", "vpgrid"):
        w, h = _measure_grid(n, inner_w, inner_h)
    elif k == "imagemap":
        w, h = _measure_imagemap(n, aw, ah)
    elif k == "hotspot":
        r = n.pos[0] if n.pos else (0, 0, 0, 0)
        w, h = float(r[2]), float(r[3])
    elif k in ("bar", "vbar"):
        w = fw if fw is not None else (aw if k == "bar" else 30)
        h = fh if fh is not None else (30 if k == "bar" else ah)
    elif k in ("viewport", "side", "fixed", "drag", "draggroup", "mousearea", "nearrect",
               "dismiss", "transform"):
        kids = _children_box(n)
        if k == "fixed" and n.parent is not None and fw is None and fh is None and \
                not p.get("xfit") and not p.get("yfit"):
            for c in kids:
                measure(c, inner_w, inner_h)
            w, h = inner_w, inner_h
        else:
            mw = mh = 0.0
            for c in kids:
                cw, ch = measure(c, inner_w, inner_h)
                mw, mh = max(mw, cw + _cpos_extent(c, "x")), max(mh, ch + _cpos_extent(c, "y"))
            w, h = (inner_w, inner_h) if k in ("viewport", "side", "dismiss") else (mw, mh)
            if k == "transform" and not kids:
                w, h = 0, 0
    elif k in ("frame", "window", "button", "input"):
        kids = _children_box(n)
        if len(kids) == 1:
            w, h = measure(kids[0], inner_w, inner_h)
            w += _cpos_extent(kids[0], "x")
            h += _cpos_extent(kids[0], "y")
        elif kids:
            for c in kids:
                measure(c, inner_w, inner_h)
            w, h = inner_w, inner_h
        if k == "input":
            w, h = _measure_text(n, inner_w, inner_h)
    if k in ("frame", "window", "button", "textbutton", "imagebutton", "input"):
        bg = p.get("background")
        if bg is not None and not _is_color(bg) and not isinstance(bg, Solid) and \
                not kids_any(n) and image_info(bg) is not None:
            info = image_info(bg)
            w, h = max(w, info[1] - pl - pr), max(h, info[2] - pt - pb)
    w += pl + pr
    h += pt + pb
    if fw is not None:
        w = fw - ml - mr if k not in ("add", "image") else fw
    if fh is not None:
        h = fh - mt - mb if k not in ("add", "image") else fh
    w, h = _minmax(p, w, h, aw, ah, text=k in ("text", "label"))
    n.mw = max(0.0, w)
    n.mh = max(0.0, h)
    return n.mw + ml + mr, n.mh + mt + mb


def kids_any(n):
    return len(_children_box(n)) > 0


def _cpos_extent(c, axis):
    """Extra room a child's pixel offset needs inside a fit-to-children box."""
    return 0.0


def _text_value(n):
    if n.kind == "input":
        v = n.props.get("default", "")
        return interpolate(v, n.screen.scope if n.screen else {})
    if not n.pos:
        return ""
    v = n.pos[0]
    if isinstance(v, Text):
        v = v.text
    scope = n.screen.scope if n.screen else {}
    s = interpolate(v, scope) if isinstance(v, str) else str(v)
    return _strip_tags(s)


def _text_style(n):
    """Style props for a text node: a textbutton's text uses <style>_text."""
    if n.kind == "textbutton":
        name = _style_name(n, "button") + "_text"
        tp = _canon_into(dict(style_props(name)),
                         {k[5:]: n.props[k] for k in n.props if k.startswith("text_")})
        return _for_state(tp, n.state)
    if n.kind == "label":
        name = _style_name(n, "label") + "_text"
        tp = _canon_into(dict(style_props(name)),
                         {k[5:]: n.props[k] for k in n.props if k.startswith("text_")})
        return _for_state(tp, n.state)
    return n.sp


def _measure_text(n, maxw, maxh):
    p = _text_style(n)
    size = float(p.get("size") or 22)
    n.text_props = p
    n.text_size = size
    s = _text_value(n)
    lim = maxw if maxw is not None and maxw > 0 else None
    mx = p.get("xmaximum")
    if mx is not None:
        lim = min(lim or 1e9, _num(mx, maxw or W))
    lines = _wrap(s, size, lim)
    n.lines = lines
    lh = _vn3ds.line_height(size) + float(p.get("line_spacing") or 0)
    w = 0.0
    for ln in lines:
        w = max(w, _vn3ds.text_width(ln, size))
    n.line_h = lh
    return w, lh * len(lines)


def _disp_size(d, aw, ah):
    if isinstance(d, Null):
        return float(d.w or 0), float(d.h or 0)
    if isinstance(d, Solid):
        xs = d.xysize
        return (_num(xs[0], aw) if xs and xs[0] is not None else aw,
                _num(xs[1], ah) if xs and xs[1] is not None else ah)
    if isinstance(d, Transform):
        return _disp_size(d.child, aw, ah)
    if isinstance(d, Text):
        return _vn3ds.text_width(d.text, 22), _vn3ds.line_height(22)
    if isinstance(d, Movie):
        return aw, ah
    if isinstance(d, (list, tuple)) and d and not isinstance(d[0], str):
        return _disp_size(d[0], aw, ah)
    if _is_color(d):
        return aw, ah
    info = image_info(d)
    if info is None:
        return 0.0, 0.0
    return float(info[1]), float(info[2])


def _measure_image(n, aw, ah):
    d = n.pos[0] if n.pos else None
    w, h = _disp_size(d, aw, ah)
    p = n.sp
    z = p.get("zoom")
    xz = p.get("xzoom", 1.0) * (z if z is not None else 1.0)
    yz = p.get("yzoom", 1.0) * (z if z is not None else 1.0)
    return w * xz, h * yz


def _button_images(n):
    """imagebutton: the image for its state."""
    p = n.props
    st = n.state
    if p.get("auto"):
        name = _expand_auto(p["auto"], st)
        if name:
            return name
    for k in {"idle": ["idle"], "hover": ["hover", "idle"],
              "selected_idle": ["selected_idle", "idle"],
              "selected_hover": ["selected_hover", "hover", "selected_idle", "idle"],
              "insensitive": ["insensitive", "idle"],
              "selected_insensitive": ["selected_insensitive", "insensitive", "idle"]}.get(st, ["idle"]):
        if p.get(k) is not None:
            return p[k]
        if p.get(k + "_background") is not None:
            return p[k + "_background"]
    if n.pos:
        return n.pos[0]
    return None


def _measure_imagebutton(n):
    d = _button_images(n)
    n.image = d
    if d is None and n.props.get("auto"):
        d = _expand_auto(n.props["auto"], "idle")
    return _disp_size(d, W, H)


def _measure_box(n, aw, ah, vertical):
    p = n.sp
    spacing = float(p.get("spacing") or 0)
    first = p.get("first_spacing")
    kids = _children_box(n)
    total = 0.0
    cross = 0.0
    for i, c in enumerate(kids):
        cw, ch = measure(c, aw, ah if not vertical else ah)
        if vertical:
            total += ch
            cross = max(cross, cw)
        else:
            total += cw
            cross = max(cross, ch)
        if i < len(kids) - 1:
            total += float(first) if (i == 0 and first is not None) else spacing
    if p.get("box_wrap"):
        pass
    return (cross, total) if vertical else (total, cross)


def _measure_grid(n, aw, ah):
    p = n.sp
    kids = _children_box(n)
    if n.kind == "grid":
        cols = int(n.pos[0]) if n.pos else 1
        rows = int(n.pos[1]) if len(n.pos) > 1 else 1
    else:
        cols = int(p.get("cols") or 0)
        rows = int(p.get("rows") or 0)
        if not cols:
            cols = max(1, (len(kids) + max(rows, 1) - 1) // max(rows, 1))
        if not rows:
            rows = max(1, (len(kids) + cols - 1) // cols)
    xs = float(p.get("xspacing", p.get("spacing")) or 0)
    ys = float(p.get("yspacing", p.get("spacing")) or 0)
    cw = ch = 0.0
    for c in kids:
        w, h = measure(c, aw, ah)
        cw, ch = max(cw, w), max(ch, h)
    n.grid = (cols, rows, cw, ch, xs, ys)
    if n.kind == "vpgrid":
        rows = max(rows, (len(kids) + cols - 1) // cols)
    return cols * cw + (cols - 1) * xs, rows * ch + (rows - 1) * ys


def _imagemap_image(n, key):
    p = n.props
    if p.get(key) is not None:
        return p[key]
    if p.get("auto"):
        return _expand_auto(p["auto"], {"ground": "ground"}.get(key, key)) or \
            (p["auto"].replace("%s", key) if image_info(p["auto"].replace("%s", key)) else None)
    return None


def _measure_imagemap(n, aw, ah):
    g = _imagemap_image(n, "ground") or _imagemap_image(n, "idle")
    n.ground = g
    for c in n.children:
        if c.kind in ("hotspot", "hotbar"):
            measure(c, aw, ah)
        elif c.kind not in ("timer", "key", "on"):
            measure(c, aw, ah)
    w, h = _disp_size(g, aw, ah)
    return (w or aw), (h or ah)


# -- placing

def _place_axis(p, axis, avail, size):
    """Ren'Py's placement on one axis (props already canonical, see
    _canon_into): pos, anchor, offset."""
    pos = p.get(axis + "pos")
    anchor = p.get(axis + "anchor")
    off = float(p.get(axis + "offset") or 0)
    return (_num(pos, avail) or 0.0) - (_num(anchor, size) or 0.0) + off


def place(n, x, y, aw, ah, depth):
    """Positions n (measured) inside the area (x, y, aw, ah)."""
    p = n.sp
    ml, mt, mr, mb = n.mar
    w, h = n.mw, n.mh
    nx = x + _place_axis(p, "x", aw - ml - mr, w) + ml
    ny = y + _place_axis(p, "y", ah - mt - mb, h) + mt
    _set_rect(n, nx, ny, w, h, depth)


def _set_rect(n, nx, ny, w, h, depth):
    n.rect = (nx, ny, w, h)
    n.depth = depth
    p = n.sp
    pl, pt, pr, pb = n.pad
    ix, iy, iw, ih = nx + pl, ny + pt, w - pl - pr, h - pt - pb
    k = n.kind
    kids = _children_box(n)
    d = depth - 0.012
    if k in ("vbox", "hbox"):
        spacing = float(p.get("spacing") or 0)
        first = p.get("first_spacing")
        cur = iy if k == "vbox" else ix
        for i, c in enumerate(kids):
            cw, ch = c.mw, c.mh
            cp = c.sp
            if k == "vbox":
                cx = ix + _place_axis(cp, "x", iw, cw)
                cy = cur + float(cp.get("yoffset") or 0)
                _set_rect(c, cx, cy, cw, ch, d)
                cur += ch
            else:
                cy = iy + _place_axis(cp, "y", ih, ch)
                cx = cur + float(cp.get("xoffset") or 0)
                _set_rect(c, cx, cy, cw, ch, d)
                cur += cw
            if i < len(kids) - 1:
                cur += float(first) if (i == 0 and first is not None) else spacing
        return
    if k in ("grid", "vpgrid"):
        cols, rows, cw, ch, xs, ys = n.grid
        transpose = bool(p.get("transpose"))
        for i, c in enumerate(kids):
            if transpose:
                col, row = i // rows, i % rows
            else:
                col, row = i % cols, i // cols
            place(c, ix + col * (cw + xs), iy + row * (ch + ys), cw, ch, d)
        if k == "vpgrid":
            _scroll(n, iy)
        return
    if k == "imagemap":
        for c in n.children:
            if c.kind == "hotspot":
                r = c.pos[0] if c.pos else (0, 0, 0, 0)
                _set_rect(c, ix + r[0], iy + r[1], r[2], r[3], d)
            elif c.kind not in ("timer", "key", "on"):
                place(c, ix, iy, iw, ih, d)
        return
    for c in kids:
        place(c, ix, iy, iw, ih, d)
    if k == "viewport":
        _scroll(n, iy)


def _scroll(n, top):
    """A viewport's children move by its scroll position (d-pad / drag)."""
    off = _VIEWPORTS.get(n.key)
    p = n.sp
    content = 0.0
    for c in _children_box(n):
        if c.rect:
            content = max(content, c.rect[1] + c.rect[3] - top)
    vh = n.rect[3]
    rng = max(0.0, content - vh)
    if off is None:
        yi = p.get("yinitial")
        off = (float(yi) * rng if isinstance(yi, float) and yi <= 1.0 else float(yi or 0)) \
            if yi is not None else 0.0
    off = max(0.0, min(rng, off))
    _VIEWPORTS[n.key] = off
    n.scroll_range = rng
    if off:
        for c in _children_box(n):
            _shift(c, -off)


def _shift(n, dy):
    if n.rect:
        x, y, w, h = n.rect
        n.rect = (x, y + dy, w, h)
    for c in n.children:
        _shift(c, dy)


_VIEWPORTS = {}


# --------------------------------------------------------------------------
# buttons: state, focus, hits

_FOCUS = [None]     # key of the focused button
_FOCUSABLE = []     # (node, rect) this frame, in drawing order


def _actions_selected(a):
    if a is None:
        return False
    if isinstance(a, (list, tuple)):
        for x in a:
            if _selected(x):
                return True
        return False
    return _selected(a)


def _selected(a):
    if a is None:
        return False
    if isinstance(a, (list, tuple)):
        return _actions_selected(a)
    try:
        return bool(a.get_selected()) if hasattr(a, "get_selected") else False
    except Exception:
        return False


def _sensitive(a):
    if a is None:
        return False
    if isinstance(a, (list, tuple)):
        for x in a:
            if not _sensitive(x):
                return False
        return len(a) > 0
    try:
        return bool(a.get_sensitive()) if hasattr(a, "get_sensitive") else True
    except Exception:
        return True


def _button_state(n):
    p = n.props
    act = p.get("action", p.get("clicked"))
    sel = p.get("selected")
    selected = bool(sel) if sel is not None else _actions_selected(act)
    sens = p.get("sensitive")
    sensitive = bool(sens) if sens is not None else (act is not None and _sensitive(act))
    if n.kind == "hotspot" and act is None:
        sensitive = False
    n.sensitive = sensitive
    focused = sensitive and _FOCUS[0] == n.key
    if not sensitive:
        st = "insensitive"
    else:
        st = "hover" if focused else "idle"
    if selected:
        st = "selected_" + st
    n.state = st


def _run_action(a):
    if a is None:
        return None
    if isinstance(a, (list, tuple)):
        r = None
        for x in a:
            v = _run_action(x)
            if v is not None:
                r = v
        return r
    if callable(a):
        return a()
    return None


# --------------------------------------------------------------------------
# display list

_LIST = []


def _emit(*cmd):
    """("img", name, x, y, w, h, alpha, depth, sx, sy, sw, sh)  sx.. -1: whole
       ("rect", rgba, x, y, w, h, depth)
       ("text", s, x, y, size, rgba, depth, outline rgba (0: none))"""
    _LIST.append(cmd)


def _alpha_of(n):
    a = 1.0
    p = n.sp
    if p.get("alpha") is not None:
        a *= float(p["alpha"])
    return a


def _draw_disp(d, x, y, w, h, alpha, depth, crop=None):
    if d is None:
        return
    if isinstance(d, Transform):
        a = d.kw.get("alpha")
        _draw_disp(d.child, x, y, w, h, alpha * (float(a) if a is not None else 1.0), depth, crop)
        return
    if isinstance(d, Solid):
        _emit("rect", rgba(d.color), x, y, w, h, depth)
        return
    if isinstance(d, Null) or isinstance(d, Movie):
        return
    if isinstance(d, Frame):
        _draw_disp(d.image, x, y, w, h, alpha, depth, crop)
        return
    if isinstance(d, Text):
        _emit("text", d.text, x, y, 22.0, 0xFFFFFFFF, depth, 0)
        return
    if isinstance(d, (list, tuple)) and d and not isinstance(d[0], str):
        for e in d:
            _draw_disp(e, x, y, w, h, alpha, depth, crop)
        return
    if _is_color(d):
        _emit("rect", rgba(d), x, y, w, h, depth)
        return
    info = image_info(d)
    if info is None:
        return
    if crop is None:
        _emit("img", info[0], x, y, w, h, alpha, depth, -1, -1, -1, -1)
    else:   # the window as fractions of the image (crop is in its pixels)
        iw, ih = float(max(1, info[1])), float(max(1, info[2]))
        _emit("img", info[0], x, y, w, h, alpha, depth, crop[0] / iw, crop[1] / ih,
              crop[2] / iw, crop[3] / ih)


def _draw_bg(n, key, x, y, w, h):
    bg = n.sp.get(key)
    if bg is None:
        return
    _draw_disp(bg, x, y, w, h, _alpha_of(n), n.depth + 0.004)


def draw(n):
    if n.rect is None:
        return
    x, y, w, h = n.rect
    k = n.kind
    a = _alpha_of(n)
    if a <= 0:
        return
    if k in ("frame", "window", "button", "textbutton", "imagebutton", "input", "fixed",
             "vbox", "hbox", "grid", "vpgrid", "viewport", "side"):
        _draw_bg(n, "background", x, y, w, h)
    if k in ("text", "label", "textbutton", "input"):
        _draw_text(n)
    elif k in ("add", "image"):
        _draw_disp(n.pos[0] if n.pos else None, x, y, w, h, a, n.depth)
    elif k == "imagebutton":
        _draw_disp(n.image, x, y, w, h, a, n.depth - (0.03 if "hover" in n.state else 0))
    elif k == "imagemap":
        _draw_imagemap(n)
        return
    elif k in ("bar", "vbar"):
        _draw_bar(n)
    if k in ("button", "textbutton", "imagebutton", "hotspot"):
        if getattr(n, "sensitive", False):
            _FOCUSABLE.append(n)
    if k == "viewport" or k == "vpgrid":
        top, bot = y, y + h
        for c in _children_box(n):
            _draw_clipped(c, top, bot)
    else:
        for c in _children_box(n):
            draw(c)
    _draw_bg(n, "foreground", x, y, w, h)


def _draw_clipped(n, top, bot):
    if n.rect is None:
        return
    x, y, w, h = n.rect
    if y + h <= top or y >= bot:
        return
    mark = len(_LIST)
    draw(n)
    # crop what straddles the edge (images by their source rect, the rest
    # when it doesn't fit)
    k = mark
    while k < len(_LIST):
        c = _LIST[k]
        if c[0] == "img":
            cy, ch = c[3], c[5]
            if cy < top or cy + ch > bot:
                t0 = max(cy, top)
                t1 = min(cy + ch, bot)
                if t1 <= t0:
                    _LIST.pop(k)
                    continue
                sx, sy, sw, sh = (c[8], c[9], c[10], c[11]) if c[10] > 0 else (0.0, 0.0, 1.0, 1.0)
                f0 = (t0 - cy) / ch
                f1 = (t1 - cy) / ch
                _LIST[k] = ("img", c[1], c[2], t0, c[4], t1 - t0, c[6], c[7], sx,
                            sy + f0 * sh, sw, (f1 - f0) * sh)
        elif c[0] == "rect":
            cy, ch = c[3], c[5]
            t0 = max(cy, top)
            t1 = min(cy + ch, bot)
            if t1 <= t0:
                _LIST.pop(k)
                continue
            _LIST[k] = ("rect", c[1], c[2], t0, c[4], t1 - t0, c[6])
        elif c[0] == "text":
            if c[3] < top - 2 or c[3] + c[4] > bot + 2:
                _LIST.pop(k)
                continue
        k += 1
    # buttons out of view can't be focused
    for f in list(_FOCUSABLE):
        if f.rect and (f.rect[1] + f.rect[3] <= top or f.rect[1] >= bot):
            _FOCUSABLE.remove(f)


_BY_ENGINE = {}


def _info_by_engine(name):
    if not _BY_ENGINE:
        for k in _IMAGES:
            _BY_ENGINE[_IMAGES[k][0]] = _IMAGES[k]
    return _BY_ENGINE.get(name)


def _draw_text(n):
    p = getattr(n, "text_props", None) or n.sp
    size = getattr(n, "text_size", 22.0)
    color = rgba(p.get("color"), 0xFFFFFFFF)
    outl = 0
    o = p.get("outlines")
    if o and isinstance(o, (list, tuple)) and o and isinstance(o[0], (list, tuple)) and \
            len(o[0]) >= 2:
        outl = rgba(o[0][1], 0)
    x, y, w, h = n.rect
    pl, pt, pr, pb = _padding(n.sp) if n.kind in ("textbutton", "input") else (0, 0, 0, 0)
    lines = getattr(n, "lines", [])
    lh = getattr(n, "line_h", size)
    ta = p.get("text_align")
    tw_all = w - pl - pr
    if n.kind == "textbutton":
        # the button's text is placed in the button like a child
        tw = 0.0
        for ln in lines:
            tw = max(tw, _vn3ds.text_width(ln, size))
        th = lh * len(lines)
        tx = x + pl + _place_axis(p, "x", tw_all, tw)
        ty = y + pt + _place_axis(p, "y", h - pt - pb, th)
    else:
        tx, ty = x + pl, y + pt
    a = _alpha_of(n)
    if a < 1.0:
        color = (color & 0xFFFFFF00) | int((color & 0xFF) * a)
    for i, ln in enumerate(lines):
        lx = tx
        if ta is not None and ta:
            lw = _vn3ds.text_width(ln, size)
            box = tw if n.kind == "textbutton" else tw_all
            lx = tx + (box - lw) * float(ta)
        _emit("text", ln, lx, ty + i * lh, size, color, n.depth - 0.006, outl)


def _draw_imagemap(n):
    x, y, w, h = n.rect
    a = _alpha_of(n)
    _draw_disp(n.ground, x, y, w, h, a, n.depth)
    for c in n.children:
        if c.kind == "hotspot":
            if c.rect is None:
                continue
            st = c.state
            img = None
            if "hover" in st:
                img = _imagemap_image(n, "selected_hover" if "selected" in st else "hover")
            elif "selected" in st:
                img = _imagemap_image(n, "selected_idle")
            elif st == "insensitive":
                img = _imagemap_image(n, "insensitive")
            else:
                img = _imagemap_image(n, "idle")
            if img is not None and img != n.ground:
                hx, hy, hw, hh = c.rect
                _draw_disp(img, hx, hy, hw, hh, a, n.depth - (0.03 if "hover" in st else 0.0),
                           (hx - x, hy - y, hw, hh))
            if c.sensitive:
                _FOCUSABLE.append(c)
            for cc in _children_box(c):
                draw(cc)
        elif c.kind not in ("timer", "key", "on"):
            draw(c)


def _draw_bar(n):
    x, y, w, h = n.rect
    p = n.sp
    v = p.get("value")
    r = p.get("range")
    if isinstance(v, BarValue):
        r = v.get_range()
        v = v.get_value()
    frac = 0.0
    try:
        if isinstance(v, (int, float)) and r:
            frac = max(0.0, min(1.0, float(v) / float(r)))
    except Exception:
        frac = 0.0
    _emit("rect", 0x404048FF, x, y, w, h, n.depth)
    if n.kind == "bar":
        _emit("rect", 0xC8C8D0FF, x, y, w * frac, h, n.depth - 0.004)
    else:
        _emit("rect", 0xC8C8D0FF, x, y + h * (1 - frac), w, h * frac, n.depth - 0.004)


# --------------------------------------------------------------------------
# hit testing

def _mask_hit(info, px, py):
    """Is (px, py) (in the image's own pixels) on an opaque part?"""
    if info is None:
        return True
    bbox = info[3]
    if bbox is None:
        return True
    if not (bbox[0] <= px < bbox[0] + bbox[2] and bbox[1] <= py < bbox[1] + bbox[3]):
        return False
    m = info[4]
    if not m:
        return True
    mw, mh, bits = m
    cx = int(px * mw / max(1, info[1]))
    cy = int(py * mh / max(1, info[2]))
    if cx < 0 or cy < 0 or cx >= mw or cy >= mh:
        return False
    k = cy * mw + cx
    return (int(bits[k // 4], 16) >> (3 - k % 4)) & 1 == 1


def _mask_info(n):
    """The image whose shape a focus_mask button has: its current one, or
    (when that is fully transparent, e.g. an idle state that only shows on
    hover) its hover image."""
    info = image_info(getattr(n, "image", None) or _button_images(n))
    if (info is None or (info[3] is not None and info[3][2] == 0)) and n.props.get("auto"):
        alt = image_info(_expand_auto(n.props["auto"], "hover"))
        if alt is not None:
            return alt
    return info


def _hit(n, x, y):
    if n.rect is None:
        return False
    rx, ry, rw, rh = n.rect
    if not (rx <= x < rx + rw and ry <= y < ry + rh):
        return False
    fm = n.props.get("focus_mask", n.sp.get("focus_mask") if hasattr(n, "sp") else None)
    if fm is None or fm is False:
        return True
    if fm is True:
        info = _mask_info(n)
    else:
        info = image_info(fm)
        if info is None:
            return True
    if info is None:
        return True
    sx = (x - rx) * info[1] / max(1.0, rw)
    sy = (y - ry) * info[2] / max(1.0, rh)
    return _mask_hit(info, sx, sy)


def _focus_rect(n):
    """Where a button visibly is: its opaque part for focus_mask images."""
    rx, ry, rw, rh = n.rect
    fm = n.props.get("focus_mask")
    if fm is True or (fm is not None and fm is not False):
        info = _mask_info(n) if fm is True else image_info(fm)
        if info is not None and info[3] is not None:
            b = info[3]
            fx, fy = rw / max(1.0, info[1]), rh / max(1.0, info[2])
            return (rx + b[0] * fx, ry + b[1] * fy, b[2] * fx, b[3] * fy)
    return n.rect


def _navigable(n):
    """Buttons the d-pad lands on: not invisible click-catchers."""
    if n.kind == "imagebutton":
        img = getattr(n, "image", None)
        if img is None or isinstance(img, Null):
            return False
        info = image_info(img)
        if info is None and not isinstance(img, (Solid, Transform)):
            return False
    r = _focus_rect(n)
    if r[2] >= W * 0.95 and r[3] >= H * 0.95:
        return False
    return True


def _move_focus(direction):
    cands = [n for n in _FOCUSABLE if _navigable(n)]
    if not cands:
        return False
    cur = None
    for n in cands:
        if n.key == _FOCUS[0]:
            cur = n
    if cur is None:
        # start from the top-left most
        best = None
        for n in cands:
            r = _focus_rect(n)
            score = r[1] + r[0] * 0.25
            if best is None or score < best[0]:
                best = (score, n)
        _FOCUS[0] = best[1].key
        return True
    r = _focus_rect(cur)
    cx, cy = r[0] + r[2] / 2, r[1] + r[3] / 2
    best = None
    for n in cands:
        if n is cur:
            continue
        q = _focus_rect(n)
        qx, qy = q[0] + q[2] / 2, q[1] + q[3] / 2
        dx, dy = qx - cx, qy - cy
        if direction == "up":
            along, side = -dy, abs(dx)
        elif direction == "down":
            along, side = dy, abs(dx)
        elif direction == "left":
            along, side = -dx, abs(dy)
        else:
            along, side = dx, abs(dy)
        if along <= 1:
            continue
        score = along + side * 2.0
        if best is None or score < best[0]:
            best = (score, n)
    if best is not None:
        _FOCUS[0] = best[1].key
        _sound(best[1], "hover_sound")
        return True
    return False


def _sound(n, key):
    s = n.props.get(key) if n.props.get(key) is not None else n.sp.get(key)
    if s:
        renpy.play(s, "sound")


def _activate(n):
    p = n.props
    _sound(n, "activate_sound")
    hv = p.get("hovered")
    if hv is not None:
        _run_action(hv)
    return _run_action(p.get("action", p.get("clicked")))


# --------------------------------------------------------------------------
# keys

_DIR_KEYS = {"up": ("K_UP", "w", "K_w", "focus_up", "K_KP8"),
             "down": ("K_DOWN", "s", "K_s", "focus_down", "K_KP2"),
             "left": ("K_LEFT", "a", "K_a", "focus_left", "K_KP4"),
             "right": ("K_RIGHT", "d", "K_d", "focus_right", "K_KP6")}
_BUTTON_KEYS = {"a": ("K_RETURN", "K_SPACE", "K_KP_ENTER", "dismiss", "button_select"),
                "b": ("game_menu", "K_ESCAPE", "button_alternate", "mouseup_3", "hide_windows"),
                "x": ("K_TAB", "x", "K_x"), "y": ("y", "K_y", "rollback", "K_PAGEUP"),
                "l": ("rollback", "K_PAGEUP", "q", "K_q"), "r": ("rollforward", "K_PAGEDOWN", "e", "K_e")}


def _keynames(k):
    if isinstance(k, (list, tuple)):
        out = []
        for x in k:
            out += _keynames(x)
        return out
    k = str(k)
    if k in config.keymap:
        return list(config.keymap[k]) + [k]
    for pre in ("keydown_", "keyup_", "repeat_", "noshift_", "shift_", "ctrl_", "alt_"):
        if k.startswith(pre):
            k = k[len(pre):]
    return [k]


def _bound_keys(trees):
    """key statements and button keysyms in the frontmost modal group."""
    out = []
    for root in trees:
        _collect_keys(root, out)
    return out


def _collect_keys(n, out):
    if n.kind == "key" and n.pos:
        out.append((_keynames(n.pos[0]), n, "key"))
    if n.kind in ("button", "textbutton", "imagebutton", "hotspot"):
        ks = n.props.get("keysym")
        if ks is not None and getattr(n, "sensitive", True):
            out.append((_keynames(ks), n, "button"))
    for c in n.children:
        _collect_keys(c, out)


def _key_fire(keys, names):
    for ks, n, kind in keys:
        for nm in names:
            if nm in ks:
                if kind == "key":
                    _run_action(n.props.get("action"))
                else:
                    _activate(n)
                return True
    return False


# --------------------------------------------------------------------------
# a run (the engine's minigame mode) and the story's overlays

class _Run(object):
    def __init__(self):
        self.mode = None       # "call" | "overlay"
        self.screen = None
        self.menu = False
        self.changed = False
        self.overlays_changed = False
        self.result = ""
        self.clock = 0.0


_RUN = _Run()


def _encode_overlays():
    out = []
    for s in _SHOWN:
        if s.persistent:
            out.append(s.name + "\x1f" + "s" + s.scope.get("_vn3ds_args", "") + "\x1e")
    return "".join(out)


def _decode_overlays(v):
    out = []
    if not isinstance(v, str):
        return out
    for item in v.split("\x1e"):
        if "\x1f" not in item:
            continue
        k, val = item.split("\x1f", 1)
        out.append((k, val[1:] if val.startswith("s") else ""))
    return out


def _parse_args(src):
    if not src:
        return (), {}
    f = _ARGS.get(src)
    if f is None:
        return (), {}
    try:
        return f()
    except Exception as e:
        _err("screen arguments (" + src + ")", e)
        return (), {}


_SYNCED = [None]


def sync_overlays():
    """Shown overlays follow the story's _vn3ds_screens (the script's
    show screen / hide screen, kept in saves)."""
    try:
        v = _vn3ds.get("_vn3ds_screens") if _vn3ds.has("_vn3ds_screens") else ""
    except Exception:
        v = ""
    if v == _SYNCED[0]:
        return
    _SYNCED[0] = v
    want = _decode_overlays(v)
    names = [w[0] for w in want]
    for s in list(_SHOWN):
        if s.persistent and s.name not in names:
            _SHOWN.remove(s)
    for name, args in want:
        cur = get_screen(name)
        if cur is not None and cur.persistent and cur.scope.get("_vn3ds_args", "") == args:
            continue
        a, k = _parse_args(args)
        s = show_screen(name, a, k, persistent=True)
        if s is not None:
            s.scope["_vn3ds_args"] = args


def _write_overlays():
    if not _RUN.overlays_changed:
        return
    _RUN.overlays_changed = False
    v = _encode_overlays()
    _SYNCED[0] = v
    if _vn3ds.has("_vn3ds_screens"):
        _vn3ds.set("_vn3ds_screens", v)


def _frontmost():
    """Screens that take input: from the top down to the first modal one."""
    out = []
    for s in reversed(_SHOWN):
        out.append(s)
        if s.modal:
            break
    return out


_TREES = [None]     # the last render's trees (redrawn only when something changed)


def _render_all():
    del _LIST[:]
    del _FOCUSABLE[:]
    trees = []
    for s in list(_SHOWN):
        root = _render(s)
        measure(root, W, H)
        _set_rect(root, 0.0, 0.0, W, H, _BASE_DEPTH[0] - 0.02 * len(trees))
        trees.append(root)
    take = _frontmost()
    focusable_before = len(_FOCUSABLE)
    for root in trees:
        start = len(_FOCUSABLE)
        draw(root)
        if root.screen not in take:
            del _FOCUSABLE[start:]
    _TREES[0] = trees
    return trees


_BASE_DEPTH = [-0.05]


def _tick_timers(trees, dt):
    fired = False
    live = {}
    for root in trees:
        for n in _walk(root):
            if n.kind != "timer":
                continue
            delay = float(n.pos[0]) if n.pos else 1.0
            t = _TIMERS.get(n.key, 0.0) + dt
            if t >= delay and delay >= 0:
                _run_action(n.props.get("action"))
                fired = True
                t = t - delay if n.props.get("repeat") else -1e9
                if t > delay:
                    t = 0.0
            live[n.key] = t
    _TIMERS.clear()
    _TIMERS.update(live)
    return fired


def _walk(n):
    out = [n]
    k = 0
    while k < len(out):
        out += out[k].children
        k += 1
    return out


def _on_events(trees, event):
    for root in trees:
        for n in _walk(root):
            if n.kind == "on" and n.pos:
                ev = n.pos[0]
                evs = ev if isinstance(ev, (list, tuple)) else [ev]
                if event in evs:
                    _run_action(n.props.get("action"))


def _handle(trees, events):
    take = [s.root for s in _frontmost() if s.root is not None]
    keys = _bound_keys(take)
    bound = set()
    for ks, n, kind in keys:
        for k in ks:
            bound.add(k)
    for ev in events:
        if ev.startswith("tap:"):
            x, y = ev[4:].split(",")
            x, y = float(x), float(y)
            for n in reversed(_FOCUSABLE):
                if _hit(n, x, y):
                    _FOCUS[0] = n.key
                    _activate(n)
                    return True
            continue
        if ev.startswith("hover:"):
            x, y = ev[6:].split(",")
            x, y = float(x), float(y)
            for n in reversed(_FOCUSABLE):
                if _hit(n, x, y):
                    _FOCUS[0] = n.key
                    break
            continue
        if ev in _DIR_KEYS:
            names = _DIR_KEYS[ev]
            if any(k in bound for k in names) and _key_fire(keys, names):
                continue
            if _move_focus(ev):
                continue
            _scroll_viewports(trees, ev)
            continue
        if ev.startswith("pad_"):   # circle pad: always focus, then scroll
            d = ev[4:]
            if not _move_focus(d):
                _scroll_viewports(trees, d)
            continue
        if ev == "a":
            cur = None
            for n in _FOCUSABLE:
                if n.key == _FOCUS[0]:
                    cur = n
            if cur is not None:
                _activate(cur)
                return True
            if _key_fire(keys, _BUTTON_KEYS["a"]):
                return True
            if not _FOCUSABLE:
                continue
            _move_focus("down")
            continue
        if ev in _BUTTON_KEYS:
            if _key_fire(keys, _BUTTON_KEYS[ev]):
                return True
            if ev == "b":
                # leave the menu the way Ren'Py's game_menu key does
                if _RUN.mode == "overlay" or _RUN.menu:
                    raise _signal(_ReturnValue, None)
            continue
    return False


def _scroll_viewports(trees, d):
    if d not in ("up", "down"):
        return
    for root in trees:
        for n in _walk(root):
            if n.kind in ("viewport", "vpgrid") and getattr(n, "scroll_range", 0) > 0:
                cur = _VIEWPORTS.get(n.key, 0.0)
                _VIEWPORTS[n.key] = cur + (H * 0.12 if d == "down" else -H * 0.12)


def begin(mode, screen, args):
    """Starts a run: `call screen` (mode "call") or the story overlays'
    button (mode "overlay")."""
    _RUN.mode = mode
    _RUN.menu = False
    _RUN.result = ""
    _RUN.screen = screen
    _RUN.changed = True
    _FOCUS[0] = None
    sync_overlays()
    if mode == "call":
        a, k = _parse_args(args)
        show_screen(screen, a, k)
        return
    # the overlay button: an overlay with a single button is pressed for
    # the player (the phone's icon), else its buttons take input
    trees = _render_all()
    ov = [s for s in _SHOWN if s.persistent]
    btns = [n for n in _FOCUSABLE if n.screen in ov]
    if len(btns) == 1:
        try:
            _activate(btns[0])
        except (_Jump, _Call, _ReturnValue, _EndRun) as e:
            _finish(e)


def _finish(e):
    if isinstance(e, _Jump):
        _RUN.result = "jump:" + str(_SIG[0])
    elif isinstance(e, _Call):
        _RUN.result = "call:" + str(_SIG[0])
    elif isinstance(e, _ReturnValue):
        v = _SIG[0]
        if v is None or isinstance(v, (bool, int, float, str)):
            if _vn3ds.has("_return"):
                _vn3ds.set("_return", v)
        _RUN.result = "return"
    else:
        _RUN.result = "end"
    # what a run showed goes away with it; the script's overlays stay
    for s in list(_SHOWN):
        if not s.persistent:
            _SHOWN.remove(s)
    _write_overlays()
    try:   # the story's next frame draws what is left
        _render_all()
    except Exception as e2:
        _err("drawing the overlays", e2)


def frame(dt, events):
    """One frame of a run. events: space-separated "up down left right a b x
    y l r pad_up ... tap:x,y hover:x,y". Returns "" while running, else
    "return" / "jump:<label>" / "call:<label>" / "end"."""
    if _RUN.result:
        return _RUN.result
    _RUN.clock += dt
    evs = events.split() if events else []
    try:
        # redrawn only when something may have changed: an input (the focus
        # moves too), a timer that fired, a screen shown or hidden
        trees = _TREES[0]
        if trees is None or _RUN.changed:
            _RUN.changed = False
            trees = _render_all()
        changed = _tick_timers(trees, dt)
        if evs:
            _handle(trees, evs)
            changed = True
        if changed or _RUN.changed:
            _RUN.changed = False
            trees = _render_all()
        _write_overlays()
        if _RUN.mode == "call" and get_screen(_RUN.screen) is None:
            _finish(_signal(_ReturnValue, None))
        elif _RUN.mode == "overlay" and not [s for s in _SHOWN if not s.persistent]:
            # nothing the button opened is showing any more
            if _RUN.menu or [s for s in _SHOWN if not s.persistent] == []:
                if _RUN.clock > 0 and _opened[0]:
                    _finish(None)
        if [s for s in _SHOWN if not s.persistent]:
            _opened[0] = True
    except (_Jump, _Call, _ReturnValue, _EndRun) as e:
        _finish(e)
    return _RUN.result


_opened = [False]


def end_run():
    _opened[0] = False
    _RUN.mode = None
    _RUN.result = ""


def draw_list():
    return _LIST


_STORY = [None, 0.0]   # the story's line counter when last drawn, seconds since


def story_frame(dt, serial=0):
    """The story is on: draw the shown overlays (no input), run their timers.
    They are redrawn when they change, the story moves on (`serial`, the
    engine's line counter), a timer fires, or once a second."""
    before = _SYNCED[0]
    sync_overlays()
    if not _SHOWN:
        del _LIST[:]
        _TREES[0] = None
        return 0
    _STORY[1] += dt
    try:
        trees = _TREES[0]
        if trees is None or _RUN.changed or before != _SYNCED[0] or serial != _STORY[0] or \
                _STORY[1] >= 1.0:
            _RUN.changed = False
            _STORY[0] = serial
            _STORY[1] = 0.0
            trees = _render_all()
        if _tick_timers(trees, dt) or _RUN.changed:
            _RUN.changed = False
            _render_all()
        _write_overlays()
    except (_Jump, _Call, _ReturnValue, _EndRun):
        pass
    return len(_LIST)


def hud_label():
    """The overlay button's label ("" for none): shown overlays that have
    buttons."""
    for s in reversed(_SHOWN):
        if not s.persistent or s.root is None:
            continue
        for n in _walk(s.root):
            if n.kind in ("button", "textbutton", "imagebutton", "hotspot") and \
                    getattr(n, "sensitive", False):
                alt = n.props.get("alt") or n.props.get("tooltip")
                if isinstance(alt, str) and alt and len(alt) <= 24:
                    return alt
                return _HUD_NAMES.get(s.name) or _screen_title(s.name)
    return ""


_HUD_NAMES = {}


def _screen_title(name):
    """A button label from a screen's name: phoneUI_Mokia -> Phone."""
    words = []
    cur = ""
    for c in name:
        if c == "_" or c == " ":
            if cur:
                words.append(cur)
            cur = ""
        elif c in _UPPER and cur and cur[-1] not in _UPPER:
            words.append(cur)
            cur = c
        else:
            cur += c
    if cur:
        words.append(cur)
    skip = ("ui", "screen", "overlay", "hud", "icon", "button", "show", "sys")
    keep = [w for w in words if w.lower() not in skip]
    word = keep[0] if keep else (words[0] if words else "Open")
    return word[:1].upper() + word[1:]


def init(w, h):
    global W, H
    W = int(w)
    H = int(h)
    config.screen_width = W
    config.screen_height = H

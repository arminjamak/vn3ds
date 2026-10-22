"""Ren'Py screen language -> Python, for the screen runtime (vn3ds_rt.py).

A screen becomes a function that builds its displayables each time it is
drawn, the way Ren'Py re-evaluates a screen on every interaction:

    screen snake(g=snake_handler):          def _scr_snake(_ui, _sc):
        if g.alive:                             if _sc["g"].alive:
            timer .4 repeat True action ...  ->     _ui.timer(.4, repeat=True, action=..., _id=3)
        frame xysize 100,100:                   with _ui.frame(xysize=(100, 100), _id=4):
            text "Hi" align .5,.5                   _ui.text("Hi", align=(.5, .5), _id=5)
            action Return(1)                        _ui.props(action=Return(1))

Containers are `with` blocks; a property line inside a block applies to
the enclosing displayable (that's how Ren'Py reads it too). Every statement
gets an `_id`, so the runtime can keep a timer's clock, a button's focus or
a viewport's scroll position between redraws.

Names are resolved here, at pack time (resolve_names): the screen's
parameters, its `default`s and what it assigns live in the screen's scope
`_sc`; the story's variables (which the VM keeps, and saves) are read and
written through `_get` / `_set`; everything else is a Python global of the
game's own init python or the runtime (actions, classes, builtins).

Everything is deterministic: the same screens always give the same code.
"""

import ast
import io
import re
import tokenize

# ---------------------------------------------------------------------------
# properties

STYLE_PROPS = set("""
action alternate hovered unhovered selected sensitive keysym alternate_keysym focus_mask
auto idle hover insensitive selected_idle selected_hover selected_insensitive ground
xysize xsize ysize pos xpos ypos anchor xanchor yanchor align xalign yalign xycenter xcenter
ycenter offset xoffset yoffset area xfill yfill xmaximum ymaximum maximum xminimum yminimum
minimum spacing first_spacing box_reverse box_wrap padding xpadding ypadding left_padding
right_padding top_padding bottom_padding margin xmargin ymargin left_margin right_margin
top_margin bottom_margin background foreground color size font bold italic underline
strikethrough outlines outline_scaling text_align layout kerning line_spacing line_leading
min_width justify antialias black_color hinting slow_cps slow_cps_multiplier
at id style style_prefix style_suffix style_group alt tooltip modal zorder tag variant
mouse focus default_focus repeat xzoom yzoom zoom alpha rotate fit crop crop_relative
scrollbars draggable mousewheel edgescroll cols rows transpose child_size xinitial yinitial
value range changed adjustment copypaste mask length pixel_width allow exclude prefix suffix
caret caret_blink as arguments properties activate_sound hover_sound time_policy
thumb thumb_offset left_bar right_bar top_bar bottom_bar bar_vertical bar_invert
unscrollable gutter base_bar thumb_shadow xspacing yspacing order_reverse
subpixel transform_anchor nearest matrixcolor blur radius corner1 corner2
clicked hotspot_offset drag_name draggable droppable drag_raise dragged dropped
drag_handle drag_joined drag_offscreen focus_rect key_events capture
width height xfit yfit rest_indent first_indent newline_indent vertical emptyspace hyperlink_functions
shaper instance language ruby_style altruby_style textshader outline_scaling adjust_spacing
""".split())

PREFIXES = ("selected_hover_", "selected_idle_", "selected_insensitive_", "selected_",
            "hover_", "idle_", "insensitive_", "activate_", "text_", "side_",
            "viewport_", "scrollbar_", "vscrollbar_", "thumb_", "bar_")

# operator words that continue an expression after a value
EXPR_WORDS = {"and", "or", "not", "in", "is", "if", "else", "for", "lambda", "async", "await"}


def is_prop(name):
    while True:
        if name in STYLE_PROPS:
            return True
        for p in PREFIXES:
            if name.startswith(p) and len(name) > len(p):
                name = name[len(p):]
                break
        else:
            return False


def _tokens(src):
    try:
        return [t for t in tokenize.generate_tokens(io.StringIO(src).readline)
                if t.type not in (tokenize.NEWLINE, tokenize.NL, tokenize.ENDMARKER,
                                  tokenize.COMMENT, tokenize.INDENT, tokenize.DEDENT)]
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return None


def _ends_value(t):
    return (t.type in (tokenize.NUMBER, tokenize.STRING) or
            (t.type == tokenize.NAME and t.string not in EXPR_WORDS) or
            t.string in (")", "]", "}") or
            t.type == getattr(tokenize, "FSTRING_END", -1))


def _starts_value(t):
    return (t.type in (tokenize.NUMBER, tokenize.STRING, tokenize.NAME) or
            t.string in ("(", "[", "{", "-", "+", "~") or
            t.type == getattr(tokenize, "FSTRING_START", -1))


def split_props(src, first_prop=False):
    """'"x.png" focus_mask True action Show("a"), Hide("b")' ->
    (['"x.png"'], [("focus_mask", "True"), ("action", 'Show("a"), Hide("b")')]).
    Returns None if the line can't be tokenised. first_prop: the line
    starts with a property name, known or not (a property line in a block)."""
    toks = _tokens(src)
    if toks is None:
        return None
    lines = src.split("\n")
    offs = [0]
    for ln in lines:
        offs.append(offs[-1] + len(ln) + 1)

    def at(pos):
        return offs[pos[0] - 1] + pos[1]

    positional, props = [], []
    cur_name, cur_start = None, None   # cur_name None: positional
    depth = 0
    prev = None

    def close(end):
        if cur_start is None:
            return
        piece = src[cur_start:end].strip()
        if cur_name is None:
            if piece:
                positional.append(piece)
        else:
            props.append((cur_name, piece))

    want_value = False   # just after a property name: the next token is its value
    for i, t in enumerate(toks):
        s = t.string
        if i == 0 and first_prop and t.type == tokenize.NAME:
            cur_name, cur_start = s, at(t.end)
            prev = t
            want_value = True
            continue
        if depth == 0 and not want_value and t.type == tokenize.NAME and is_prop(s) and \
                (prev is None or _ends_value(prev)):
            close(at(t.start))
            cur_name, cur_start = s, at(t.end)
            prev = t
            want_value = True
            continue
        if depth == 0 and not want_value and prev is not None and _ends_value(prev) and \
                _starts_value(t) and t.type != tokenize.OP and cur_name is None and \
                not (prev.type == tokenize.STRING and t.type == tokenize.STRING) and \
                not (t.type == tokenize.NAME and s in EXPR_WORDS) and \
                not (prev.type == tokenize.NAME and prev.string in ("not", "lambda")):
            close(at(t.start))   # `grid 2 3`: a second positional
            cur_start = at(t.start)
        elif cur_start is None:
            cur_start = at(t.start)
        want_value = False
        if s in "([{":
            depth += 1
        elif s in ")]}":
            depth -= 1
        prev = t
    close(len(src))
    return positional, props


# ---------------------------------------------------------------------------
# statements

DISPLAYABLES = {
    "add", "image", "text", "label", "textbutton", "imagebutton", "button", "frame", "window",
    "fixed", "vbox", "hbox", "grid", "vpgrid", "side", "viewport", "imagemap", "hotspot",
    "hotbar", "bar", "vbar", "null", "input", "timer", "key", "mousearea", "drag", "draggroup",
    "nearrect", "dismiss", "transform", "areapicker",
}
# take one block of children
CONTAINERS = {"frame", "window", "fixed", "vbox", "hbox", "grid", "vpgrid", "side",
              "viewport", "imagemap", "button", "drag", "draggroup", "transform", "nearrect",
              "mousearea", "dismiss"}


class Unsupported(Exception):
    pass


class Out:
    def __init__(self):
        self.lines = []
        self.next_id = 1

    def emit(self, depth, text):
        self.lines.append("    " * depth + text)

    def new_id(self):
        n = self.next_id
        self.next_id += 1
        return n


NAME_PROPS = ("tag", "layer", "as")   # these take a name, not an expression


def _kwargs(props):
    props = [(n, repr(v) if n in NAME_PROPS and re.match(r"[A-Za-z_]\w*$", v or "") else v)
             for n, v in props]
    out = []
    last = {}
    for name, src in props:   # a property given twice: the last one counts
        last[name] = src
    props = [(n, last.pop(n)) for n, _s in props if n in last]
    for name, src in props:
        if name == "as":
            continue
        if name == "properties":
            out.append(f"**({src})")
        else:
            out.append(f"{name}=({src})" if src else f"{name}=True")
    return out


def _call(fn, positional, props, _id):
    args = [f"({p})" for p in positional] + _kwargs(props) + [f"_id={_id}"]
    return f"_ui.{fn}({', '.join(args)})"


def translate_block(lines, out, depth, warn):
    """Statements of a screen block (rpy.Line objects) -> out."""
    i = 0
    emitted = False
    while i < len(lines):
        ln = lines[i]
        text = ln.text
        word = re.match(r"[A-Za-z_]\w*|\$", text)
        word = word.group(0) if word else ""
        rest = text[len(word):].strip()
        has_colon = rest.endswith(":") and ln.block
        head = rest[:-1].strip() if has_colon else rest
        try:
            if word == "$":
                out.emit(depth, text[1:].strip())
                emitted = True
            elif word == "python":
                from .rpy import python_block_source
                for l in python_block_source(ln.block).split("\n"):
                    out.emit(depth, l)
                emitted = True
            elif word in ("if", "elif", "while") or (word == "else" and text.rstrip(":") == "else"):
                if word == "else":
                    out.emit(depth, "else:")
                else:
                    out.emit(depth, f"{word} {head}:")
                if not translate_block(ln.block, out, depth + 1, warn):
                    out.emit(depth + 1, "pass")
                emitted = True
            elif word == "showif":
                out.emit(depth, f"if {head}:")
                if not translate_block(ln.block, out, depth + 1, warn):
                    out.emit(depth + 1, "pass")
                emitted = True
            elif word == "for":
                out.emit(depth, f"for {head}:")
                if not translate_block(ln.block, out, depth + 1, warn):
                    out.emit(depth + 1, "pass")
                emitted = True
            elif word == "pass":
                out.emit(depth, "pass")
                emitted = True
            elif word == "default":
                m = re.match(r"([A-Za-z_]\w*)\s*=\s*(.+)$", rest, re.S)
                if not m:
                    raise Unsupported("default")
                out.emit(depth, f"if {m.group(1)!r} not in _sc: _sc[{m.group(1)!r}] = ({m.group(2)})")
                emitted = True
            elif word == "use":
                m = re.match(r"(expression\s+(.+?)\s+pass\s*|([A-Za-z_][\w.]*))\s*(\(.*\))?\s*(id\s+.*)?$",
                             head, re.S)
                if not m:
                    raise Unsupported("use")
                target = m.group(2) if m.group(2) else repr(m.group(3))
                args = m.group(4)[1:-1] if m.group(4) else ""
                _id = out.new_id()
                if has_colon:
                    out.emit(depth, f"def _tc{_id}():")
                    if not translate_block(ln.block, out, depth + 1, warn):
                        out.emit(depth + 1, "pass")
                    extra = f"_transclude=_tc{_id}, "
                else:
                    extra = ""
                out.emit(depth, f"_ui.use({target}, {extra}_args=_ui.pack({args}), _id={_id})")
                emitted = True
            elif word == "transclude":
                out.emit(depth, "_ui.transclude()")
                emitted = True
            elif word == "has":
                sp = split_props(head)
                if sp is None or not sp[0]:
                    raise Unsupported("has")
                kind = sp[0][0]
                # the remaining lines are this box's children
                _id = out.new_id()
                out.emit(depth, f"with {_call(kind, sp[0][1:], sp[1], _id)}:")
                if not translate_block(lines[i + 1:], out, depth + 1, warn):
                    out.emit(depth + 1, "pass")
                return True
            elif word == "on":
                sp = split_props(head)
                if sp is None or not sp[0]:
                    raise Unsupported("on")
                out.emit(depth, _call("on", sp[0], sp[1], out.new_id()))
                emitted = True
            elif word in DISPLAYABLES:
                sp = split_props(head)
                if sp is None:
                    raise Unsupported(f"{word} line")
                positional, props = sp
                if word == "text" and len(positional) > 1:   # `text "a" "b"`: one string
                    positional = [" ".join(positional)]
                _id = out.new_id()
                call = _call(word, positional, props, _id)
                if ln.block:
                    out.emit(depth, f"with {call}:")
                    if not translate_block(ln.block, out, depth + 1, warn):
                        out.emit(depth + 1, "pass")
                else:
                    out.emit(depth, call)
                emitted = True
            elif word == "at" and has_colon:
                pass   # `at transform:` with its own ATL: the runtime doesn't animate it
            elif word in ("predict", "pagekeys", "substitute", "nopredict", "variant",
                          "layer", "sensitive_if", "roll_forward"):
                pass   # no effect on the 3DS
            elif re.match(r"[A-Za-z_]\w*$", word):
                # anything else in a block is a property (Ren'Py has no other kind)
                sp = split_props(text, first_prop=True)
                if sp is None:
                    raise Unsupported("property line")
                props = sp[1]
                if props:
                    out.emit(depth, f"_ui.props({', '.join(_kwargs(props))})")
                if ln.block:
                    raise Unsupported(f"{word} block")
                emitted = True
            else:
                raise Unsupported(f"'{text[:20]}'")
        except Unsupported as e:
            warn(ln, f"screen language: {e.args[0]} is not supported; skipped")
        i += 1
    return emitted


def translate_screen(name, params, body, warn):
    """One screen -> (source of its function, its parameters' source)."""
    out = Out()
    out.emit(0, f"def _scr_{_ident(name)}(_ui, _sc):")
    if not translate_block(body, out, 1, warn):
        out.emit(1, "pass")
    return "\n".join(out.lines)


def _ident(name):
    return re.sub(r"\W", "_", name)


# ---------------------------------------------------------------------------
# style statements

def translate_style(line, warn):
    """`style a is b:` + property lines -> _style(...) calls."""
    m = re.match(r"style\s+([\w.]+)\s*(.*?):?\s*$", line.text, re.S)
    if not m:
        return []
    name, rest = m.group(1), m.group(2).strip()
    parent = None
    calls = []
    words = rest.split()
    k = 0
    while k < len(words):
        w = words[k]
        if w == "is" and k + 1 < len(words):
            parent = words[k + 1]
            k += 2
        elif w == "take" and k + 1 < len(words):
            calls.append(f"_style_take({name!r}, {words[k + 1]!r})")
            k += 2
        elif w == "clear":
            calls.append(f"_style_clear({name!r})")
            k += 1
        elif w == "variant":
            return []   # variants for other devices: the PC one is the base
        else:
            break
    props = []
    rest_src = " ".join(words[k:])
    for ln in [rest_src] + [l.text for l in line.block]:
        if not ln:
            continue
        sp = split_props(ln)
        if sp is None:
            warn(line, f"style {name}: cannot read '{ln[:40]}'")
            continue
        props += sp[1]
    # in order, the later ones winning (`properties` dicts and plain ones)
    parts = []
    for pname, src in props:
        if pname == "properties":
            parts.append(f"({src})")
        else:
            parts.append(f"{{{pname!r}: ({src or 'True'})}}")
    calls.insert(0, f"_style({name!r}, {parent!r}{''.join(', ' + a for a in parts)})")
    return calls


# ---------------------------------------------------------------------------
# names

class _Scope:
    def __init__(self, names, kind):
        self.names = set(names)
        self.kind = kind   # "local" | "screen"


def _assigned(node):
    """Names a statement list binds (assignment targets, for targets, defs)."""
    out = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store):
            out.add(n.id)
        elif isinstance(n, (ast.FunctionDef, ast.ClassDef)):
            out.add(n.name)
        elif isinstance(n, ast.alias):
            out.add((n.asname or n.name).split(".")[0])
    return out


class Resolver(ast.NodeTransformer):
    """Rewrites names: screen scope -> _sc["x"], story variables -> _get("x")
    / _set("x", v), the rest unchanged.

    `store_vars`: names the VM keeps. `screen_names`: the screen's scope
    (None outside screens). Locals of functions, lambdas and comprehensions,
    and a function's `global` declarations, are followed."""

    def __init__(self, store_vars, screen_names=None, module=False):
        self.store = store_vars
        self.screen = set(screen_names or ())
        self.stack = []          # local name sets of enclosing functions
        self.globals = []        # `global` names per function
        self.module = module     # module level of init python

    # -- scopes
    def _is_local(self, name):
        for s in reversed(self.stack):
            if name in s:
                return True
        return False

    def _kind(self, name):
        if self._is_local(name):
            if self.globals and name in self.globals[-1]:
                return "store" if name in self.store else "global"
            return "local"
        if name in self.screen:
            return "screen"
        if name in self.store:
            return "store"
        return "global"

    def _fn(self, node, args):
        local = set()
        for a in args.posonlyargs + args.args + args.kwonlyargs:
            local.add(a.arg)
        if args.vararg:
            local.add(args.vararg.arg)
        if args.kwarg:
            local.add(args.kwarg.arg)
        glob = set()
        body = node.body if isinstance(node.body, list) else [node.body]
        for st in body:
            for n in ast.walk(st):
                if isinstance(n, ast.Global):
                    glob |= set(n.names)
        for st in body:
            local |= _assigned(st)
        local -= glob
        if not self.stack and self.screen:   # the screen's own function: its scope isn't local
            local -= self.screen
        # defaults are evaluated outside
        args.defaults = [self.visit(d) for d in args.defaults]
        args.kw_defaults = [self.visit(d) if d is not None else None for d in args.kw_defaults]
        self.stack.append(local)
        self.globals.append(glob)
        if isinstance(node.body, list):
            node.body = [self._stmt(st) for st in node.body]
            node.body = [st for s in node.body for st in (s if isinstance(s, list) else [s])]
            # `global x` of a story variable: it is read and written through
            # _get/_set, so drop it from the declaration
            for st in node.body:
                if isinstance(st, ast.Global):
                    st.names = [n for n in st.names if n not in self.store] or ["_vn3ds_unused"]
        else:
            node.body = self.visit(node.body)
        self.stack.pop()
        self.globals.pop()
        node.decorator_list = [self.visit(d) for d in getattr(node, "decorator_list", [])]
        return node

    def visit_FunctionDef(self, node):
        return self._fn(node, node.args)

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Lambda(self, node):
        return self._fn(node, node.args)

    def visit_ClassDef(self, node):
        node.bases = [self.visit(b) for b in node.bases]
        node.keywords = [self.visit(k) for k in node.keywords]
        node.decorator_list = [self.visit(d) for d in node.decorator_list]
        local = set()
        for st in node.body:
            local |= _assigned(st)
        self.stack.append(local)
        self.globals.append(set())
        node.body = [self._stmt(st) for st in node.body]
        node.body = [st for s in node.body for st in (s if isinstance(s, list) else [s])]
        self.stack.pop()
        self.globals.pop()
        return node

    def _comp(self, node, elts):
        local = set()
        for g in node.generators:
            local |= {n.id for n in ast.walk(g.target) if isinstance(n, ast.Name)}
        # the first iterable is evaluated outside
        node.generators[0].iter = self.visit(node.generators[0].iter)
        self.stack.append(local)
        for k, g in enumerate(node.generators):
            if k:
                g.iter = self.visit(g.iter)
            g.ifs = [self.visit(c) for c in g.ifs]
        for e in elts:
            setattr(node, e, self.visit(getattr(node, e)))
        self.stack.pop()
        return node

    def visit_ListComp(self, node):
        return self._comp(node, ["elt"])

    visit_SetComp = visit_GeneratorExp = visit_ListComp

    def visit_DictComp(self, node):
        return self._comp(node, ["key", "value"])

    # -- names
    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            k = self._kind(node.id)
            if k == "screen":
                return ast.copy_location(ast.Subscript(
                    value=ast.Name("_sc", ast.Load()), slice=ast.Constant(node.id),
                    ctx=ast.Load()), node)
            if k == "store":
                return ast.copy_location(ast.Call(ast.Name("_get", ast.Load()),
                                                  [ast.Constant(node.id)], []), node)
        elif isinstance(node.ctx, ast.Store) and self._kind(node.id) == "screen":
            return ast.copy_location(ast.Subscript(
                value=ast.Name("_sc", ast.Load()), slice=ast.Constant(node.id),
                ctx=ast.Store()), node)
        return node

    def visit_Attribute(self, node):
        # persistent.x / store.x: story variables by their full name
        if isinstance(node.value, ast.Name) and node.value.id in ("persistent", "store") and \
                not self._is_local(node.value.id):
            full = node.attr if node.value.id == "store" else f"persistent.{node.attr}"
            if isinstance(node.ctx, ast.Load):
                if node.value.id == "persistent" or full in self.store:
                    return ast.copy_location(ast.Call(ast.Name("_get", ast.Load()),
                                                      [ast.Constant(full)], []), node)
        self.generic_visit(node)
        return node

    def _target_name(self, t):
        """The story variable an assignment target writes, or None."""
        if isinstance(t, ast.Name) and self._kind(t.id) == "store":
            return t.id
        if isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name) and \
                t.value.id in ("persistent", "store") and not self._is_local(t.value.id):
            full = t.attr if t.value.id == "store" else f"persistent.{t.attr}"
            if t.value.id == "persistent" or full in self.store:
                return full
        return None

    def _set(self, name, value, node):
        return ast.copy_location(ast.Expr(ast.Call(ast.Name("_set", ast.Load()),
                                                   [ast.Constant(name), value], [])), node)

    def _stmt(self, st):
        """A statement, possibly turned into several."""
        if isinstance(st, ast.Assign):
            names = [self._target_name(t) for t in st.targets]
            if any(names):
                if self.module and not self.stack:
                    return []   # init-time value of a story variable: the VM has it
                value = self.visit(st.value)
                out = []
                if len(st.targets) == 1:
                    return self._set(names[0], value, st)
                tmp = ast.Name("_vn3ds_tmp", ast.Store())
                out.append(ast.copy_location(ast.Assign([tmp], value), st))
                for t, n in zip(st.targets, names):
                    v = ast.Name("_vn3ds_tmp", ast.Load())
                    if n:
                        out.append(self._set(n, v, st))
                    else:
                        out.append(ast.copy_location(ast.Assign([self.visit(t)], v), st))
                return out
        if isinstance(st, ast.AugAssign):
            n = self._target_name(st.target)
            if n:
                if self.module and not self.stack:
                    return []
                cur = ast.Call(ast.Name("_get", ast.Load()), [ast.Constant(n)], [])
                return self._set(n, ast.BinOp(cur, st.op, self.visit(st.value)), st)
        if isinstance(st, ast.AnnAssign) and st.value is not None:
            n = self._target_name(st.target)
            if n:
                return [] if self.module and not self.stack else \
                    self._set(n, self.visit(st.value), st)
        for field in ("body", "orelse", "finalbody"):
            if hasattr(st, field) and isinstance(getattr(st, field), list) and \
                    not isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                new = [self._stmt(s) for s in getattr(st, field)]
                setattr(st, field, [x for s in new for x in (s if isinstance(s, list) else [s])]
                        or [ast.Pass()])
        if isinstance(st, ast.Try):
            for h in st.handlers:
                new = [self._stmt(s) for s in h.body]
                h.body = [x for s in new for x in (s if isinstance(s, list) else [s])] or [ast.Pass()]
                if h.type:
                    h.type = self.visit(h.type)
        # visit the statement's own expressions (not its already-done bodies)
        if isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            return self.visit(st)
        for field, value in ast.iter_fields(st):
            if field in ("body", "orelse", "finalbody", "handlers"):
                continue
            if isinstance(value, ast.AST):
                setattr(st, field, self.visit(value))
            elif isinstance(value, list):
                setattr(st, field, [self.visit(v) if isinstance(v, ast.AST) else v for v in value])
        if isinstance(st, ast.For):
            # a story variable as a loop target: loop over a local, then set it
            n = self._target_name(st.target) if isinstance(st.target, ast.Name) else None
            if n:
                st.target = ast.Name("_vn3ds_it", ast.Store())
                st.body.insert(0, self._set(n, ast.Name("_vn3ds_it", ast.Load()), st))
        return st

    def run(self, tree):
        if isinstance(tree, ast.Module):
            new = [self._stmt(st) for st in tree.body]
            tree.body = [x for s in new for x in (s if isinstance(s, list) else [s])]
            return tree
        return self.visit(tree)


def screen_scope_names(fn_tree):
    """A screen function's scope: what its `default`s and `$` lines bind
    (its parameters are added by the caller)."""
    out = set()
    for n in ast.walk(fn_tree):
        if isinstance(n, ast.If) and isinstance(n.test, ast.Compare) and \
                isinstance(n.test.left, ast.Constant) and \
                isinstance(n.test.comparators[0], ast.Name) and n.test.comparators[0].id == "_sc":
            out.add(n.test.left.value)
    fn = fn_tree.body[0]
    for st in ast.walk(fn):
        if isinstance(st, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
            targets = st.targets if isinstance(st, ast.Assign) else [st.target]
            for t in targets:
                for n in ast.walk(t):
                    if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store) and \
                            not n.id.startswith("_"):
                        out.add(n.id)
    return out

"""Parser for the subset of the Ren'Py script language that vn3ds supports.

The output is a list of plain node objects (see the `Node` subclasses below)
that `compiler.py` turns into bytecode. Anything outside the subset becomes
an `Unsupported` node so the compiler can warn about it once.
"""

import re


class ParseError(Exception):
    def __init__(self, filename, lineno, msg):
        super().__init__(f"{filename}:{lineno}: {msg}")
        self.filename = filename
        self.lineno = lineno


# --------------------------------------------------------------------------
# Logical lines and blocks
# --------------------------------------------------------------------------

class Line:
    __slots__ = ("filename", "lineno", "indent", "text", "block")

    def __init__(self, filename, lineno, indent, text):
        self.filename = filename
        self.lineno = lineno
        self.indent = indent
        self.text = text
        self.block = []

    def error(self, msg):
        return ParseError(self.filename, self.lineno, msg)


def logical_lines(src, filename):
    """Yield (lineno, indent, text) per logical line.

    Joins lines inside brackets and strings (Ren'Py strings may span lines),
    honours trailing backslashes and strips comments.
    """
    src = src.replace("\r\n", "\n").replace("\r", "\n")
    if src.startswith("﻿"):
        src = src[1:]
    i, n, lineno = 0, len(src), 1
    while i < n:
        start = lineno
        indent = 0
        while i < n and src[i] in " \t":
            indent = indent + 1 if src[i] == " " else (indent // 8 + 1) * 8
            i += 1
        buf = []
        depth = 0
        while i < n:
            c = src[i]
            if c == "\n":
                lineno += 1
                i += 1
                if depth == 0:
                    break
                buf.append(" ")
                continue
            if c == "#":
                while i < n and src[i] != "\n":
                    i += 1
                continue
            if c == "\\" and i + 1 < n and src[i + 1] == "\n":
                i += 2
                lineno += 1
                continue
            if c in "\"'`":
                q = c * 3 if src.startswith(c * 3, i) else c
                j = i + len(q)
                while True:
                    if j >= n:
                        raise ParseError(filename, start, "unterminated string")
                    if src[j] == "\\":
                        if j + 1 < n and src[j + 1] == "\n":
                            lineno += 1
                        j += 2
                        continue
                    if src[j] == "\n":
                        lineno += 1
                    if src.startswith(q, j):
                        j += len(q)
                        break
                    j += 1
                buf.append(src[i:j])
                i = j
                continue
            if c in "([{":
                depth += 1
            elif c in ")]}":
                depth = max(0, depth - 1)
            buf.append(c)
            i += 1
        text = "".join(buf).strip()
        if text:
            yield start, indent, text


def parse_blocks(src, filename):
    lines = [Line(filename, *t) for t in logical_lines(src, filename)]

    def gather(i, indent):
        block = []
        while i < len(lines):
            line = lines[i]
            if line.indent < indent:
                break
            if line.indent > indent:
                raise line.error("unexpected indentation")
            i += 1
            if i < len(lines) and lines[i].indent > indent:
                line.block, i = gather(i, lines[i].indent)
            block.append(line)
        return block, i

    if not lines:
        return []
    block, i = gather(0, lines[0].indent)
    if i != len(lines):
        raise lines[i].error("inconsistent indentation")
    return block


# --------------------------------------------------------------------------
# Per-line lexer
# --------------------------------------------------------------------------

KEYWORDS = {
    "at", "as", "behind", "call", "elif", "else", "expression", "hide", "if",
    "image", "init", "jump", "menu", "onlayer", "python", "return", "scene",
    "set", "show", "with", "while", "zorder", "transform", "label", "define",
    "default", "pass", "play", "stop", "queue", "voice", "pause", "window",
}

IMAGE_STOP_WORDS = {"at", "as", "behind", "onlayer", "with", "zorder", "expression", "if"}

WORD = r"[a-zA-Z_ -�][a-zA-Z0-9_ -�]*"
IMAGE_WORD = r"-?[a-zA-Z0-9_ -�][-a-zA-Z0-9_ -�]*"
STRING_START = re.compile(r"(?:[rRuUbBfF]{0,2})(\"\"\"|'''|\"|'|`)")
NUMBER = re.compile(r"[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?")


class Lexer:
    def __init__(self, line, text=None):
        self.line = line
        self.text = line.text if text is None else text
        self.pos = 0

    def error(self, msg):
        return self.line.error(msg)

    def ws(self):
        while self.pos < len(self.text) and self.text[self.pos] in " \t\n":
            self.pos += 1

    def eol(self):
        self.ws()
        return self.pos >= len(self.text)

    def peek(self, s):
        self.ws()
        return self.text.startswith(s, self.pos)

    def lit(self, s):
        if self.peek(s):
            self.pos += len(s)
            return True
        return False

    def match(self, regex):
        self.ws()
        m = re.compile(regex).match(self.text, self.pos)
        if not m:
            return None
        self.pos = m.end()
        return m.group(0)

    def word(self):
        return self.match(WORD)

    def keyword(self, kw):
        save = self.pos
        if self.word() == kw:
            return True
        self.pos = save
        return False

    def name(self):
        save = self.pos
        w = self.word()
        if w is None or w in KEYWORDS:
            self.pos = save
            return None
        return w

    def dotted_name(self):
        save = self.pos
        w = self.word()
        if w is None:
            return None
        parts = [w]
        while self.text.startswith(".", self.pos):
            self.pos += 1
            w = self.word()
            if w is None:
                self.pos = save
                return None
            parts.append(w)
        return ".".join(parts)

    def label_name(self):
        """A label name, possibly local (".foo") or qualified ("a.foo")."""
        self.ws()
        if self.text.startswith(".", self.pos):
            self.pos += 1
            w = self.word()
            return "." + w if w else None
        return self.dotted_name()

    def image_word(self):
        save = self.pos
        w = self.match(IMAGE_WORD)
        # Only the show/scene/hide clause words end an image name in Ren'Py;
        # "bg cafe window" is a perfectly good image.
        if w is None or w in IMAGE_STOP_WORDS:
            self.pos = save
            return None
        return w

    def string(self):
        """Return the source text of a string literal (quotes included)."""
        self.ws()
        m = STRING_START.match(self.text, self.pos)
        if not m:
            return None
        q = m.group(1)
        j = m.end()
        while j < len(self.text):
            if self.text[j] == "\\":
                j += 2
                continue
            if self.text.startswith(q, j):
                j += len(q)
                src = self.text[self.pos:j]
                self.pos = j
                return src
            j += 1
        raise self.error("unterminated string")

    def number(self):
        self.ws()
        m = NUMBER.match(self.text, self.pos)
        if not m:
            return None
        self.pos = m.end()
        return m.group(0)

    def balanced(self):
        """Consume a bracketed group starting at the current position."""
        self.ws()
        open_c = self.text[self.pos]
        close_c = {"(": ")", "[": "]", "{": "}"}[open_c]
        depth = 0
        j = self.pos
        while j < len(self.text):
            c = self.text[j]
            if c in "\"'`":
                sub = Lexer(self.line, self.text)
                sub.pos = j
                sub.string()
                j = sub.pos
                continue
            if c in "([{":
                depth += 1
            elif c in ")]}":
                depth -= 1
                if depth == 0:
                    j += 1
                    src = self.text[self.pos:j]
                    self.pos = j
                    return src
            j += 1
        raise self.error(f"unbalanced {open_c}")

    def simple_expression(self):
        """A Ren'Py "simple expression": an atom plus trailers, no operators."""
        self.ws()
        start = self.pos
        if self.lit("-") or self.lit("+"):
            pass
        if self.pos < len(self.text) and self.text[self.pos] in "([{":
            self.balanced()
        elif self.string() is not None:
            pass
        elif self.number() is not None:
            pass
        elif self.word() is not None:
            pass
        else:
            self.pos = start
            return None
        while self.pos < len(self.text):
            c = self.text[self.pos]
            if c == ".":
                self.pos += 1
                if self.word() is None:
                    raise self.error("expected name after '.'")
            elif c in "([":
                self.balanced()
            else:
                break
        return self.text[start:self.pos].strip()

    def rest(self):
        self.ws()
        r = self.text[self.pos:].strip()
        self.pos = len(self.text)
        return r

    def rest_before_colon(self):
        r = self.rest()
        if not r.endswith(":"):
            raise self.error("expected ':' at end of line")
        return r[:-1].strip()

    def expect_eol(self):
        if not self.eol():
            raise self.error(f"unexpected text: {self.text[self.pos:]!r}")


def string_value(src):
    """Evaluate a string literal's source as Python would (for file names etc.)."""
    import ast
    return ast.literal_eval(src)


def dialogue_text(src):
    """Turn a dialogue string literal into the text Ren'Py would display.

    Whitespace runs collapse to one space, escapes are processed and text tags
    are reduced to what the engine understands: {p} becomes a newline,
    {w}/{nw}/{fast}/style tags are dropped. Returns (text, flags) where flags
    has "nw" when the line should not wait for input.
    """
    m = STRING_START.match(src)
    q = m.group(1)
    raw = "r" in src[:m.start(1)].lower()
    body = src[m.end():-len(q)]
    body = re.sub(r"\s+", " ", body)
    if not raw:
        out = []
        i = 0
        while i < len(body):
            c = body[i]
            if c == "\\" and i + 1 < len(body):
                n = body[i + 1]
                out.append({"n": "\n", "t": "\t"}.get(n, n))
                i += 2
                continue
            out.append(c)
            i += 1
        body = "".join(out)
    flags = set()
    out = []
    i = 0
    while i < len(body):
        if body.startswith("{{", i):
            out.append("{")
            i += 2
            continue
        if body[i] == "{":
            j = body.find("}", i)
            if j < 0:
                out.append(body[i:])
                break
            tag = body[i + 1:j]
            name = tag.split("=")[0].strip().lstrip("/")
            if name == "p":
                out.append("\n")
            elif name == "nw":
                flags.add("nw")
            elif name == "space":
                try:
                    out.append(" " * max(1, int(tag.split("=")[1]) // 8))
                except (IndexError, ValueError):
                    out.append(" ")
            # every other tag ({w}, {b}, {color=...}, {size}, {fast}, ...) is
            # dropped; the system font cannot style spans.
            i = j + 1
            continue
        out.append(body[i])
        i += 1
    return "".join(out), flags


# --------------------------------------------------------------------------
# AST nodes
# --------------------------------------------------------------------------

class Node:
    def __init__(self, line, **kw):
        self.line = line
        self.__dict__.update(kw)

    def __repr__(self):
        fields = {k: v for k, v in self.__dict__.items() if k != "line"}
        return f"{type(self).__name__}({fields})"


class Label(Node): pass          # name, block
class Say(Node): pass            # who (str|None), who_is_string, attrs, what, flags, with_
class Show(Node): pass           # spec, expression, at, as_, behind, zorder, with_, atl
class Scene(Node): pass          # same as Show, spec may be None
class Hide(Node): pass           # tag, with_
class With(Node): pass           # expr
class Jump(Node): pass           # target, expression
class Call(Node): pass           # target, expression
class Return(Node): pass         # expr
class Menu(Node): pass           # label, caption (Say|None), items[(text, cond, block)]
class If(Node): pass             # branches[(cond, block)], else_
class While(Node): pass          # cond, block
class Python(Node): pass         # code, init
class Pause(Node): pass          # expr
class Play(Node): pass           # channel, expr, fadein, fadeout, loop, if_changed, queue
class Stop(Node): pass           # channel, fadeout
class Window(Node): pass         # mode
class Pass(Node): pass
class Define(Node): pass         # name, expr, priority
class Default(Node): pass        # name, expr
class Image(Node): pass          # name, expr, atl
class Transform(Node): pass      # name, params, block
class Init(Node): pass           # priority, block
class Unsupported(Node): pass    # what
class Screen(Node): pass         # name, items (see screen_items), background, body (lines)
class CallScreen(Node): pass     # name, with_, args (source of "(...)" or None)
class ShowScreen(Node): pass     # name, hide (show screen / hide screen)


# --------------------------------------------------------------------------
# Statement parser
# --------------------------------------------------------------------------

CHANNELS = {"music": 0, "sound": 1, "audio": 1, "voice": 2}


def channel_index(name, default=1):
    """Ren'Py games register extra channels (music2, soundlow, ...); fold them
    onto the engine's three by name."""
    if not name:
        return default
    if name in CHANNELS:
        return CHANNELS[name]
    n = name.lower()
    if "music" in n or "bgm" in n or "ambien" in n:
        return 0
    if "voice" in n:
        return 2
    return 1

SKIPPED_BLOCKS = {
    "screen": "screen language",
    "style": "style statements",
    "translate": "translations",
    "testcase": "test cases",
    "layeredimage": "layeredimage",
}


def parse_file(src, filename):
    return parse_block(parse_blocks(src, filename))


def parse_statement(line):
    lex = Lexer(line)
    text = line.text

    if text.startswith("$"):
        return Python(line, code=text[1:].strip(), init=False)

    save = lex.pos
    w = lex.word()

    if w == "label":
        name = lex.label_name()
        if name is None:
            raise line.error("expected label name")
        if lex.peek("("):
            lex.balanced()
        lex.keyword("hide")
        if not lex.lit(":"):
            raise line.error("expected ':' after label")
        lex.expect_eol()
        return Label(line, name=name, block=parse_block(line.block))

    if w == "init":
        priority = 0
        n = lex.number()
        if n is not None:
            priority = int(float(n))
        if lex.keyword("python"):
            lex.rest()
            return Python(line, code=python_block_source(line.block), init=True,
                          priority=priority)
        if lex.lit(":"):
            return Init(line, priority=priority, block=parse_block(line.block))
        # "init 5 image ..." / "init define ..." style one-liners
        sub = Line(line.filename, line.lineno, line.indent, lex.rest())
        sub.block = line.block
        node = parse_statement(sub)
        return Init(line, priority=priority, block=[node] if node else [])

    if w == "python":
        lex.rest()
        return Python(line, code=python_block_source(line.block), init=False)

    if w == "jump":
        if lex.keyword("expression"):
            return Jump(line, target=lex.rest(), expression=True)
        target = lex.label_name()
        lex.expect_eol()
        return Jump(line, target=target, expression=False)

    if w == "call":
        if lex.keyword("screen"):
            name = lex.word()
            args = None
            if lex.peek("("):
                args = lex.balanced()
            with_ = None
            while not lex.eol():
                if lex.keyword("with"):
                    with_ = lex.simple_expression()
                elif lex.keyword("nopredict") or lex.keyword("onlayer") or lex.keyword("zorder"):
                    lex.simple_expression()
                else:
                    lex.rest()
            return CallScreen(line, name=name, with_=with_, args=args)
        if lex.keyword("expression"):
            target = lex.simple_expression()
            expression = True
        else:
            target = lex.label_name()
            expression = False
        if lex.peek("("):
            lex.balanced()
        if lex.keyword("from"):
            lex.label_name()
        lex.expect_eol()
        return Call(line, target=target, expression=expression)

    if w == "return":
        r = lex.rest()
        return Return(line, expr=r or None)

    if w in ("scene", "show"):
        if w == "show" and (lex.keyword("screen")):
            name = lex.word()
            lex.rest()
            return ShowScreen(line, name=name, hide=False) if name else \
                Unsupported(line, what="show screen")
        if w == "show" and lex.keyword("layer"):
            return Unsupported(line, what="show layer")
        return parse_show(line, lex, scene=(w == "scene"))

    if w == "hide":
        if lex.keyword("screen"):
            name = lex.word()
            lex.rest()
            return ShowScreen(line, name=name, hide=True) if name else \
                Unsupported(line, what="hide screen")
        words = []
        while True:
            iw = lex.image_word()
            if iw is None:
                break
            words.append(iw)
        if not words:
            raise line.error("expected image tag after hide")
        with_ = None
        while not lex.eol():
            if lex.keyword("onlayer"):
                lex.word()
            elif lex.keyword("with"):
                with_ = lex.simple_expression()
            else:
                raise line.error(f"unexpected text: {lex.rest()!r}")
        return Hide(line, tag=words[0], with_=with_)

    if w == "with":
        return With(line, expr=lex.rest())

    if w == "menu":
        return parse_menu(line, lex)

    if w == "if":
        return _parse_block_with_if([line])[0]

    if w in ("elif", "else"):
        raise line.error(f"'{w}' without 'if'")

    if w == "while":
        cond = lex.rest_before_colon()
        return While(line, cond=cond, block=parse_block(line.block))

    if w == "pass":
        return Pass(line)

    if w == "pause":
        r = lex.rest()
        return Pause(line, expr=r or None)

    if w in ("play", "queue"):
        channel = lex.word()
        expr = lex.simple_expression()
        if expr is None:
            raise line.error("expected file after play/queue")
        node = Play(line, channel=channel_index(channel), channel_name=channel,
                    expr=expr, fadein=0.0, fadeout=None, loop=None,
                    if_changed=False, queue=(w == "queue"))
        while not lex.eol():
            if lex.keyword("fadein"):
                node.fadein = float(lex.simple_expression())
            elif lex.keyword("fadeout"):
                node.fadeout = float(lex.simple_expression())
            elif lex.keyword("loop"):
                node.loop = True
            elif lex.keyword("noloop"):
                node.loop = False
            elif lex.keyword("if_changed"):
                node.if_changed = True
            elif lex.keyword("volume"):
                lex.simple_expression()
            else:
                lex.rest()
        return node

    if w == "voice":
        if lex.keyword("sustain"):
            return Pass(line)
        expr = lex.simple_expression()
        return Play(line, channel=2, channel_name="voice", expr=expr, fadein=0.0,
                    fadeout=None, loop=False, if_changed=False, queue=False)

    if w == "stop":
        channel = lex.word()
        fadeout = None
        if lex.keyword("fadeout"):
            fadeout = float(lex.simple_expression())
        return Stop(line, channel=channel_index(channel), fadeout=fadeout)

    if w == "window":
        mode = lex.word()
        lex.rest()
        return Window(line, mode={"auto": 0, "show": 1, "hide": 2}.get(mode, 0))

    if w in ("nvl", "rpy"):
        return Pass(line)

    if w == "camera":
        # `camera [layer] [at t, ...] [:]` with an optional ATL block. It is
        # compiled like a show of a special "@camera" sprite.
        node = Show(line, spec="@camera", expression=None, at=[], as_="@camera", behind=[],
                    zorder=None, with_=None, atl=None, onlayer=None)
        save = lex.pos
        if not lex.eol() and not lex.peek(":") and lex.word() == "at":
            lex.pos = save   # no layer name given
        # (otherwise the word was a layer name: vn3ds has one camera)
        if lex.keyword("at"):
            while True:
                e = lex.simple_expression()
                if e is None:
                    raise line.error("expected transform after 'at'")
                node.at.append(e)
                if not lex.lit(","):
                    break
        if lex.lit(":"):
            node.atl = line.block
        lex.expect_eol()
        return node

    if w == "define":
        priority = 0
        n = lex.number()
        if n is not None:
            priority = int(float(n))
        name = lex.dotted_name()
        op = lex.match(r"\+=|\|=|=")
        if op is None:
            raise line.error("expected '=' in define")
        expr = lex.rest()
        return Define(line, name=name, expr=expr, op=op, priority=priority)

    if w == "default":
        name = lex.dotted_name()
        if not lex.lit("="):
            raise line.error("expected '=' in default")
        return Default(line, name=name, expr=lex.rest())

    if w == "image":
        words = []
        while True:
            iw = lex.image_word()
            if iw is None:
                break
            words.append(iw)
        name = " ".join(words)
        if lex.lit("="):
            return Image(line, name=name, expr=lex.rest(), atl=None)
        if lex.lit(":"):
            return Image(line, name=name, expr=None, atl=line.block)
        raise line.error("expected '=' or ':' in image statement")

    if w == "transform":
        name = lex.dotted_name()
        params = None
        if lex.peek("("):
            params = lex.balanced()
        if not lex.lit(":"):
            raise line.error("expected ':' after transform name")
        return Transform(line, name=name, params=params, block=line.block)

    if w == "screen":
        name = lex.word()
        return Screen(line, name=name, items=screen_items(line.block),
                      background=screen_background(line.block), body=line.block)

    if w in SKIPPED_BLOCKS:
        return Unsupported(line, what=SKIPPED_BLOCKS[w])

    # Anything else should be dialogue.
    lex.pos = save
    say = parse_say(line, lex)
    if say is not None:
        return say

    return Unsupported(line, what=f"statement '{text.split()[0]}'")


def python_block_source(block):
    """Reconstruct the source of a python: block from its logical lines."""
    out = []

    def walk(lines, depth):
        for l in lines:
            out.append("    " * depth + l.text)
            walk(l.block, depth + 1)

    walk(block, 0)
    return "\n".join(out)


def parse_show(line, lex, scene):
    node_cls = Scene if scene else Show
    spec_words = []
    expression = None
    if lex.keyword("expression"):
        expression = lex.simple_expression()
    else:
        while True:
            iw = lex.image_word()
            if iw is None:
                break
            spec_words.append(iw)
    node = node_cls(line, spec=" ".join(spec_words) or None, expression=expression,
                    at=[], as_=None, behind=[], zorder=None, with_=None, atl=None,
                    onlayer=None)
    while not lex.eol():
        if lex.keyword("at"):
            while True:
                e = lex.simple_expression()
                if e is None:
                    raise line.error("expected transform after 'at'")
                node.at.append(e)
                if not lex.lit(","):
                    break
        elif lex.keyword("as"):
            node.as_ = lex.image_word()
        elif lex.keyword("behind"):
            while True:
                node.behind.append(lex.image_word())
                if not lex.lit(","):
                    break
        elif lex.keyword("onlayer"):
            node.onlayer = lex.word()
        elif lex.keyword("zorder"):
            node.zorder = lex.simple_expression()
        elif lex.keyword("with"):
            node.with_ = lex.simple_expression()
        elif lex.lit(":"):
            node.atl = line.block
            lex.expect_eol()
        else:
            raise line.error(f"unexpected text in {'scene' if scene else 'show'}: "
                             f"{lex.rest()!r}")
    if scene and node.spec is None and node.expression is None and node.atl:
        raise line.error("scene with a block needs an image")
    return node


def parse_say(line, lex, allow_block=False):
    """Parse `[who] [attrs] "what" [with x]`. Returns None if not dialogue."""
    save = lex.pos
    who = None
    who_is_string = False
    attrs = []

    s = lex.string()
    if s is not None:
        s2_save = lex.pos
        s2 = lex.string()
        if s2 is not None:
            who, who_is_string, what = s, True, s2
        else:
            lex.pos = s2_save
            what = s
    else:
        who = lex.dotted_name()
        if who is None:
            lex.pos = save
            return None
        while True:
            a = lex.image_word()
            if a is None:
                break
            attrs.append(a)
        if lex.lit("@"):
            while True:
                a = lex.image_word()
                if a is None:
                    break
                attrs.append(a)
        what = lex.string()
        if what is None:
            lex.pos = save
            return None

    with_ = None
    while not lex.eol():
        if lex.keyword("with"):
            with_ = lex.simple_expression()
        elif lex.keyword("id"):
            lex.word()
        elif lex.peek("("):
            lex.balanced()
        elif allow_block and lex.peek(":"):
            break
        elif lex.peek("if") and allow_block:
            break
        else:
            lex.pos = save
            return None

    text, flags = dialogue_text(what)
    if who_is_string:
        who = dialogue_text(who)[0]
    return Say(line, who=who, who_is_string=who_is_string, attrs=attrs,
               what=text, flags=flags, with_=with_)


def parse_menu(line, lex):
    label = lex.label_name() if not lex.peek(":") and not lex.peek("(") else None
    if lex.peek("("):
        lex.balanced()
    if not lex.lit(":"):
        raise line.error("expected ':' after menu")
    caption = None
    items = []
    with_ = None
    for child in line.block:
        clex = Lexer(child)
        if clex.keyword("set"):
            continue
        if clex.keyword("with"):
            with_ = clex.rest()
            continue
        s = clex.string()
        if s is not None and not child.block:
            # caption / say statement without a block
            clex.pos = 0
            caption = parse_say(child, clex)
            if caption is None:
                raise child.error("bad menu caption")
            continue
        if s is None:
            # "e "What do I do?"" as caption
            clex.pos = 0
            say = parse_say(child, clex)
            if say is not None and not child.block:
                caption = say
                continue
            raise child.error("expected a menu choice")
        text, _ = dialogue_text(s)
        if clex.peek("("):
            clex.balanced()
        cond = None
        if clex.keyword("if"):
            cond = clex.rest_before_colon()
        else:
            if not clex.lit(":"):
                raise child.error("expected ':' after menu choice")
            clex.expect_eol()
        items.append((text, cond, parse_block(child.block)))
    return Menu(line, label=label, caption=caption, items=items, with_=with_)


def _parse_block_with_if(lines):
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        lex = Lexer(line)
        w = lex.word()
        if w == "if":
            cond = lex.rest_before_colon()
            node = If(line, branches=[(cond, parse_block_with_if(line.block))], else_=None)
            i += 1
            while i < len(lines):
                nl = Lexer(lines[i])
                nw = nl.word()
                if nw == "elif":
                    node.branches.append((nl.rest_before_colon(),
                                          parse_block_with_if(lines[i].block)))
                    i += 1
                elif nw == "else":
                    if not nl.lit(":"):
                        raise lines[i].error("expected ':' after else")
                    node.else_ = parse_block_with_if(lines[i].block)
                    i += 1
                    break
                else:
                    break
            out.append(node)
            continue
        try:
            node = parse_statement(line)
        except ParseError as e:
            # One odd statement shouldn't sink a 100k-line game.
            node = Unsupported(line, what=f"unparseable statement ({e.args[0].split(': ', 1)[-1]})")
        if node is not None:
            out.append(node)
        i += 1
    return out


parse_block_with_if = _parse_block_with_if
parse_block = _parse_block_with_if


def iter_nodes(nodes):
    """Walk every node, including nested blocks."""
    for n in nodes:
        yield n
        if isinstance(n, (Label, Init, While)):
            yield from iter_nodes(n.block)
        elif isinstance(n, If):
            for _, b in n.branches:
                yield from iter_nodes(b)
            if n.else_:
                yield from iter_nodes(n.else_)
        elif isinstance(n, Menu):
            if n.caption:
                yield n.caption
            for _, _, b in n.items:
                yield from iter_nodes(b)


# --------------------------------------------------------------------------
# Screens -> menus
# --------------------------------------------------------------------------
#
# vn3ds has no screen language, but a very common use of it is navigation:
# an imagemap or a set of buttons whose actions Jump()/Call() to labels.
# screen_items() extracts those buttons, with the screen-language if/elif/else
# conditions around them, so `call screen` can become a choice menu.

_ACTION = re.compile(r"\b(Jump|Call|Return)\(\s*(?:'([^']*)'|\"([^\"]*)\"|([^()]*))?\s*\)")
_BUTTONS = ("hotspot", "imagebutton", "textbutton", "button", "hotbar")


def _button_info(line):
    """(kind, target, text, position) for a button line, or None."""
    text_all = line.text
    children = list(_walk_lines(line.block))
    action_src = None
    m = re.search(r"\baction\b(.*)$", text_all)
    if m:
        action_src = m.group(1)
    props = {}
    for c in children:
        t = c.text.strip()
        if t.startswith("action ") or t.startswith("action["):
            action_src = action_src or t[6:]
        for key in ("xalign", "yalign", "xpos", "ypos", "idle", "auto", "alt", "tooltip"):
            mm = re.match(rf"{key}\s+(.+)$", t)
            if mm:
                props[key] = mm.group(1).strip()
    for key in ("xalign", "yalign", "xpos", "ypos", "alt", "tooltip"):
        mm = re.search(rf"\b{key}\s+(\S+)", text_all)
        if mm and key not in props:
            props[key] = mm.group(1)
    if not action_src:
        return None
    am = _ACTION.search(action_src)
    if not am:
        return None
    kind = am.group(1)
    target = am.group(2) if am.group(2) is not None else am.group(3)
    if target is None:
        target = (am.group(4) or "").strip() or None
    elif kind == "Return":
        target = repr(target)  # a quoted Return("x") value
    text = None
    word = text_all.split()[0].rstrip(":")
    if word == "textbutton":
        sm = STRING_START.search(text_all)
        if sm:
            lx = Lexer(line, text_all)
            lx.pos = sm.start()
            src = lx.string()
            if src:
                text = dialogue_text(src)[0]
    for key in ("alt", "tooltip"):
        if not text and key in props:
            v = props[key].strip()
            if v[:1] in "\"'":
                text = dialogue_text(v.split(" ")[0] if False else v)[0]
    pos = None
    hm = re.match(r"hotspot\s*\(([^)]*)\)", text_all)
    try:
        if hm:
            x, y, w, h = (float(v) for v in hm.group(1).split(",")[:4])
            pos = ("px", x + w / 2, y + h / 2)
        elif "xalign" in props or "yalign" in props:
            pos = ("frac", float(props.get("xalign", 0.5)), float(props.get("yalign", 0.5)))
        elif "xpos" in props and "ypos" in props:
            pos = ("pos", float(props["xpos"]), float(props["ypos"]))
    except ValueError:
        pos = None
    return kind, target, text, pos


def _walk_lines(lines):
    for l in lines:
        yield l
        yield from _walk_lines(l.block)


def screen_background(lines):
    """The picture a navigation screen shows: an imagemap's ground (or idle)
    image, or the first `add` of a displayable. Returns an image spec/file or None."""
    for line in _walk_lines(lines):
        t = line.text.strip()
        for key in ("ground", "idle", "add"):
            m = re.match(rf"{key}\s+(\"[^\"]+\"|'[^']+')", t)
            if m:
                return m.group(1)[1:-1]
    return None


def screen_items(lines, conds=()):
    """Buttons with Jump/Call/Return actions in a screen body: a list of
    (conditions, kind, target, text, position)."""
    out = []
    chain = []
    for line in lines:
        t = line.text.strip()
        first = t.split()[0].rstrip(":") if t.split() else ""
        if first in ("if", "showif") and t.endswith(":"):
            cond = t[len(first):-1].strip()
            chain = [cond]
            out += screen_items(line.block, conds + (cond,))
            continue
        if first == "elif" and t.endswith(":"):
            cond = t[4:-1].strip()
            out += screen_items(line.block, conds + tuple(f"not ({c})" for c in chain) + (cond,))
            chain.append(cond)
            continue
        if t == "else:":
            out += screen_items(line.block, conds + tuple(f"not ({c})" for c in chain))
            chain = []
            continue
        chain = [] if first not in ("elif", "else") else chain
        if first in _BUTTONS:
            info = _button_info(line)
            if info:
                out.append((conds,) + info)
            continue
        if line.block:
            out += screen_items(line.block, conds)
    return out

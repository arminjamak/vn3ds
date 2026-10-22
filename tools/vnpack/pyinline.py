"""The game's own Python functions, folded into one script expression.

vn3ds's script engine has numbers, strings and booleans, not Python. Many
games still decide what happens next with small functions of their own:

    def current_beat():
        for b in BEATS:                      # a constant table of objects
            if b.stage == store.key_task and b.level == store.robin_progression_level:
                return b
        return None

    def ready_beat():
        b = current_beat()
        if b is not None and not b.confirm and beat_stats_met(b):
            return b.label
        return None

When everything a function looks at is either a constant table from init
python (lists, dicts, objects built by a simple class) or a story variable,
it can be evaluated while converting, as far as the constants go, and what
depends on story variables becomes a conditional expression:

    ready_beat()  ->  ("story_beat1" if key_task == 0 and robin_progression_level
                       == 0 else ("story_beat2" if ... and trust >= 20 and ... else None))

Handled: parameters with defaults, local assignments, if/elif/else, for over
a constant table (unrolled), return, calls to other such functions, and/or/
not, comparisons, `is None`, getattr(store, "x"), all()/any() over a
constant table, len() of a constant. Anything else (changing a set, a loop
over a story variable, side effects) leaves the call unsupported, as before.
"""

import ast
import copy
import types

from . import rpy
from .freeroam import Tables, Unreadable

MAX_DEPTH = 8


class Unfoldable(Exception):
    pass


class C:   # a value known while converting
    def __init__(self, v):
        self.v = v


class S:   # a value the story computes: a script expression
    def __init__(self, expr):
        self.e = expr


class Ch:  # a known value that depends on a story condition
    def __init__(self, cond, a, b):
        self.c, self.a, self.b = cond, a, b


def _scalar(v):
    return v is None or isinstance(v, (bool, int, float, str))


def expr(v):
    """A value as script source."""
    if isinstance(v, C):
        if not _scalar(v.v):
            raise Unfoldable(f"{type(v.v).__name__} value")
        return repr(v.v)
    if isinstance(v, S):
        return v.e
    return f"({expr(v.a)} if {v.c} else {expr(v.b)})"


def choose(cond, a, b):
    if isinstance(a, C) and isinstance(b, C) and a.v is b.v and _scalar(a.v):
        return a
    if isinstance(a, C) and isinstance(b, C) and a.v is True and b.v is False:
        return S(f"({cond})")
    if isinstance(a, C) and isinstance(b, C) and a.v is False and b.v is True:
        return S(f"(not ({cond}))")
    return Ch(cond, a, b)


def lift(v, fn):
    """fn applied to a value, through any story conditions."""
    if isinstance(v, Ch):
        return choose(v.c, lift(v.a, fn), lift(v.b, fn))
    return fn(v)


def lift2(a, b, fn):
    return lift(a, lambda x: lift(b, lambda y: fn(x, y)))


_CMP = {ast.Eq: ("==", lambda a, b: a == b), ast.NotEq: ("!=", lambda a, b: a != b),
        ast.Lt: ("<", lambda a, b: a < b), ast.LtE: ("<=", lambda a, b: a <= b),
        ast.Gt: (">", lambda a, b: a > b), ast.GtE: (">=", lambda a, b: a >= b),
        ast.Is: ("==", lambda a, b: a is b), ast.IsNot: ("!=", lambda a, b: a is not b),
        ast.In: ("in", lambda a, b: a in b), ast.NotIn: ("not in", lambda a, b: a not in b)}


class Inliner:
    def __init__(self, files):
        self.t = Tables(files)
        self.t.make_object = self.make_object
        self.cache = {}
        # names the story itself changes ($ money += 25, default x = ...): story
        # variables even when init python also gives them a first value
        self.mutable = set()
        for nodes in files:
            for n in rpy.iter_nodes(nodes):
                if isinstance(n, rpy.Default):
                    self.mutable.add(n.name)
                if isinstance(n, rpy.Python) and not getattr(n, "init", False):
                    try:
                        tree = ast.parse(n.code)
                    except SyntaxError:
                        continue
                    for x in ast.walk(tree):
                        for t in (x.targets if isinstance(x, ast.Assign) else
                                  [x.target] if isinstance(x, ast.AugAssign) else []):
                            if isinstance(t, ast.Name):
                                self.mutable.add(t.id)

    @property
    def funcs(self):
        return self.t.funcs

    def make_object(self, cls, args, kwargs):
        """An object of a simple class: __init__ only stores its arguments."""
        init = next((s for s in cls.body if isinstance(s, ast.FunctionDef) and
                     s.name == "__init__"), None)
        if init is None:
            raise Unreadable(f"class {cls.name}")
        params = [a.arg for a in init.args.args[1:]]
        defaults = init.args.defaults
        env = dict(zip(params[len(params) - len(defaults):],
                       [self.t.ev(d, {}) for d in defaults]))
        env.update(zip(params, args))
        env.update(kwargs)
        obj = types.SimpleNamespace()
        env["self"] = obj   # (later fields can read earlier ones)
        for st in init.body:
            if isinstance(st, ast.Expr) and isinstance(st.value, ast.Constant):
                continue
            if isinstance(st, ast.Assign) and len(st.targets) == 1 and \
                    isinstance(st.targets[0], ast.Attribute) and \
                    isinstance(st.targets[0].value, ast.Name) and st.targets[0].value.id == "self":
                setattr(obj, st.targets[0].attr, self.t.ev(st.value, env))
            else:
                raise Unreadable(f"class {cls.name}: __init__ does more than store values")
        return obj

    def fold(self, node):
        """Script source for an expression of the story that reads the game's
        tables (GIFTS[gift_to_give].scene_label), or None."""
        try:
            return expr(self.val(node, {}, 0, site=True))
        except (Unfoldable, Unreadable, RecursionError, TypeError):
            return None

    def procedure(self, name, arg_nodes, kw_nodes):
        """A call statement of the game's function `name`: its body as
        statements to compile in its place (parameters replaced by the
        arguments, store.x by x, locals renamed), or None."""
        fd = self.t.funcs.get(name)
        if fd is None or fd.args.vararg or fd.args.kwarg or fd.args.kwonlyargs:
            return None
        params = [p.arg for p in fd.args.args]
        if len(arg_nodes) > len(params) or any(k not in params for k in kw_nodes):
            return None
        bind = dict(zip(params[len(params) - len(fd.args.defaults):], fd.args.defaults))
        bind.update(zip(params, arg_nodes))
        bind.update(kw_nodes)
        if any(p not in bind for p in params):
            return None
        body = [s for s in fd.body if not (isinstance(s, ast.Expr) and
                                           isinstance(s.value, ast.Constant))]
        if body and isinstance(body[-1], ast.Return) and body[-1].value is None:
            body = body[:-1]
        local = {t.id for s in body for x in ast.walk(s)
                 for t in (x.targets if isinstance(x, ast.Assign) else
                           [x.target] if isinstance(x, (ast.AugAssign, ast.For)) else [])
                 if isinstance(t, ast.Name)} - set(params)
        for s in body:
            for x in ast.walk(s):
                if isinstance(x, (ast.Return, ast.Global, ast.Nonlocal, ast.Yield, ast.Lambda)):
                    return None

        class Sub(ast.NodeTransformer):
            def visit_Name(self, node):
                if node.id in bind and isinstance(node.ctx, ast.Load):
                    return copy.deepcopy(bind[node.id])
                if node.id in local:
                    return ast.copy_location(ast.Name(id=f"_vn3ds_{name}_{node.id}",
                                                      ctx=node.ctx), node)
                return node

            def visit_Attribute(self, node):
                self.generic_visit(node)
                if isinstance(node.value, ast.Name) and node.value.id == "store":
                    return ast.copy_location(ast.Name(id=node.attr, ctx=node.ctx), node)
                return node
        return [ast.fix_missing_locations(Sub().visit(copy.deepcopy(s))) for s in body]

    def inline(self, name, arg_nodes):
        """Script source for name(args) at a call site, or None."""
        try:
            args = [self.val(a, {}, 0, site=True) for a in arg_nodes]
            return expr(self.call(name, args, {}, 0))
        except (Unfoldable, Unreadable, RecursionError):
            return None

    # -- functions -------------------------------------------------------

    def call(self, name, args, kwargs, depth):
        if depth > MAX_DEPTH:
            raise Unfoldable("too deep")
        fd = self.t.funcs[name]
        a = fd.args
        if a.vararg or a.kwarg or a.kwonlyargs:
            raise Unfoldable("*args")
        params = [p.arg for p in a.args]
        if len(args) > len(params):
            raise Unfoldable("arguments")
        env = {}
        for p, d in zip(params[len(params) - len(a.defaults):], a.defaults):
            env[p] = self.val(d, {}, depth)
        env.update(zip(params, args))
        for k, v in kwargs.items():
            if k not in params:
                raise Unfoldable("keyword")
            env[k] = v
        if any(p not in env for p in params):
            raise Unfoldable("missing argument")
        return self.run(list(fd.body), env, depth + 1)

    def run(self, stmts, env, depth):
        for i, st in enumerate(stmts):
            rest = stmts[i + 1:]
            if not isinstance(st, tuple):
                # a variable that is one of several known values (b = current_beat()):
                # go on once per case, so `b is not None and b.x` never reads None.x
                for name in {x.id for x in ast.walk(st) if isinstance(x, ast.Name)}:
                    v = env.get(name)
                    if isinstance(v, Ch):
                        return choose(v.c, self.run(stmts[i:], dict(env, **{name: v.a}), depth),
                                      self.run(stmts[i:], dict(env, **{name: v.b}), depth))
            if isinstance(st, tuple):   # ("bind", name, value): a for loop's variable
                env = dict(env, **{st[1]: st[2]})
            elif isinstance(st, ast.Pass) or (isinstance(st, ast.Expr) and
                                              isinstance(st.value, ast.Constant)):
                continue
            elif isinstance(st, ast.Assign) and len(st.targets) == 1 and \
                    isinstance(st.targets[0], ast.Name):
                env = dict(env, **{st.targets[0].id: self.val(st.value, env, depth)})
            elif isinstance(st, ast.Return):
                return self.val(st.value, env, depth) if st.value is not None else C(None)
            elif isinstance(st, ast.If):
                c = self.val(st.test, env, depth)
                if isinstance(c, C):
                    return self.run((st.body if c.v else st.orelse) + rest, env, depth)
                return lift(c, lambda cv: self.run((st.body if cv.v else st.orelse) + rest,
                                                   env, depth)) if isinstance(c, Ch) else \
                    choose(expr(c), self.run(st.body + rest, env, depth),
                           self.run(st.orelse + rest, env, depth))
            elif isinstance(st, ast.For) and isinstance(st.target, ast.Name) and not st.orelse:
                items = self.val(st.iter, env, depth)
                if not isinstance(items, C):
                    raise Unfoldable("a loop over a story variable")
                if any(isinstance(s, (ast.Break, ast.Continue)) for b in st.body
                       for s in ast.walk(b)):
                    raise Unfoldable("break/continue")
                vals = items.v.values() if isinstance(items.v, dict) else items.v
                unrolled = []
                for item in vals if not isinstance(items.v, dict) else items.v:
                    unrolled += [("bind", st.target.id, C(item))] + list(st.body)
                return self.run(unrolled + rest, env, depth)
            else:
                raise Unfoldable(type(st).__name__)
        return C(None)

    # -- expressions -------------------------------------------------------

    def val(self, n, env, depth, site=False):
        if isinstance(n, ast.Constant):
            return C(n.value)
        if isinstance(n, ast.Name):
            if n.id in env:
                return env[n.id]
            if n.id in ("True", "False", "None"):
                return C({"True": True, "False": False, "None": None}[n.id])
            if n.id not in self.mutable and (n.id in self.t.src or n.id in self.t.funcs):
                try:   # a table from init python
                    return C(self.t.get(n.id))
                except Unreadable:
                    raise Unfoldable(f"{n.id} can't be read")
            return S(n.id)   # a story variable
        if isinstance(n, ast.Attribute):
            if isinstance(n.value, ast.Name) and n.value.id == "store":
                return S(n.attr)
            base = self.val(n.value, env, depth)

            def get(b):
                if isinstance(b, C) and b.v is None:   # a table's missing key
                    return C(None)
                if not isinstance(b, C) or not hasattr(b.v, n.attr):
                    raise Unfoldable(f".{n.attr}")
                return C(getattr(b.v, n.attr))
            return lift(base, get)
        if isinstance(n, (ast.Tuple, ast.List)):
            vals = [self.val(e, env, depth) for e in n.elts]
            if all(isinstance(v, C) for v in vals):
                return C(tuple(v.v for v in vals))
            raise Unfoldable("a list with story values")
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.Not):
            return lift(self.val(n.operand, env, depth),
                        lambda v: C(not v.v) if isinstance(v, C) else S(f"(not {expr(v)})"))
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.USub):
            return lift(self.val(n.operand, env, depth),
                        lambda v: C(-v.v) if isinstance(v, C) else S(f"(-{expr(v)})"))
        if isinstance(n, ast.BoolOp):
            return self.boolop(isinstance(n.op, ast.And),
                               [lambda e=e: self.val(e, env, depth) for e in n.values])
        if isinstance(n, ast.Compare) and len(n.ops) == 1:
            sym, fn = _CMP.get(type(n.ops[0]), (None, None))
            if sym is None:
                raise Unfoldable("comparison")
            a, b = self.val(n.left, env, depth), self.val(n.comparators[0], env, depth)

            def cmp(x, y):
                if isinstance(x, C) and isinstance(y, C):
                    return C(fn(x.v, y.v))
                return S(f"({expr(x)} {sym} {expr(y)})")
            return lift2(a, b, cmp)
        if isinstance(n, ast.BinOp):
            ops = {ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/", ast.Mod: "%"}
            if type(n.op) not in ops:
                raise Unfoldable("operator")
            a, b = self.val(n.left, env, depth), self.val(n.right, env, depth)
            o = ops[type(n.op)]
            return lift2(a, b, lambda x, y: C(eval(f"x.v {o} y.v", {}, {"x": x, "y": y}))
                         if isinstance(x, C) and isinstance(y, C)
                         else S(f"({expr(x)} {o} {expr(y)})"))
        if isinstance(n, ast.IfExp):
            c = self.val(n.test, env, depth)
            if isinstance(c, C):
                return self.val(n.body if c.v else n.orelse, env, depth)
            return choose(expr(c), self.val(n.body, env, depth), self.val(n.orelse, env, depth))
        if isinstance(n, ast.Subscript):
            base, key = self.val(n.value, env, depth), self.val(n.slice, env, depth)
            if isinstance(key, C) and isinstance(base, (C, Ch)):
                def item(b):
                    if isinstance(b, C) and b.v is None:   # a table's missing key
                        return C(None)
                    try:
                        return C(b.v[key.v])
                    except (KeyError, IndexError, TypeError, AttributeError):
                        raise Unfoldable("subscript")
                return lift(base, item)
            if isinstance(base, C) and isinstance(base.v, dict) and isinstance(key, S) and \
                    0 < len(base.v) <= 64:
                # a table looked up by a story value: one case per key
                out = C(None)
                for k, v in reversed(list(base.v.items())):
                    if not _scalar(k):
                        raise Unfoldable("key")
                    out = choose(f"({key.e} == {k!r})", C(v), out)
                return out
            if isinstance(base, S):   # d[k] of a story set/dict: the compiler's
                return S(f"{base.e}[{expr(key)}]")
            raise Unfoldable("subscript of a story value")
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute):
            # a method of a story value (seen.get(k)): left to the compiler
            obj = self.val(n.func.value, env, depth)
            if isinstance(obj, S) and not n.keywords:
                args = [expr(self.val(a, env, depth)) for a in n.args]
                return S(f"{obj.e}.{n.func.attr}({', '.join(args)})")
            raise Unfoldable("method")
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name):
            fn = n.func.id
            if n.keywords and fn not in self.t.funcs:
                raise Unfoldable("keywords")
            if fn == "getattr" and len(n.args) >= 2:
                obj, attr = self.val(n.args[1 - 1], env, depth), self.val(n.args[1], env, depth)
                if isinstance(n.args[0], ast.Name) and n.args[0].id == "store" and \
                        isinstance(attr, C) and isinstance(attr.v, str):
                    return S(attr.v)
                return lift2(obj, attr, lambda o, a: C(getattr(o.v, a.v)) if isinstance(o, C)
                             and isinstance(a, C) and hasattr(o.v, a.v) else _no("getattr"))
            if fn in ("all", "any") and len(n.args) == 1 and \
                    isinstance(n.args[0], (ast.GeneratorExp, ast.ListComp)):
                g = n.args[0]
                if len(g.generators) != 1 or not isinstance(g.generators[0].target, ast.Name) \
                        or g.generators[0].ifs:
                    raise Unfoldable("comprehension")
                gen = g.generators[0]
                items = self.val(gen.iter, env, depth)
                if not isinstance(items, C):
                    raise Unfoldable("all() over a story value")
                parts = [lambda it=it: self.val(g.elt, dict(env, **{gen.target.id: C(it)}), depth)
                         for it in items.v]
                return self.boolop(fn == "all", parts, empty=fn == "all")
            if fn == "len" and len(n.args) == 1:
                v = self.val(n.args[0], env, depth)
                if isinstance(v, C):
                    return C(len(v.v))
                raise Unfoldable("len of a story value")
            if fn in self.t.funcs:
                args = [self.val(a, env, depth) for a in n.args]
                kw = {k.arg: self.val(k.value, env, depth) for k in n.keywords if k.arg}
                return self.call(fn, args, kw, depth)
        raise Unfoldable(type(n).__name__)

    def boolop(self, is_and, parts, empty=None):
        """and/or over lazily evaluated parts, folding the known ones."""
        out = []
        for p in parts:
            v = p()
            if isinstance(v, C):
                if bool(v.v) != is_and:   # False in an and, True in an or: decided here
                    if not out:
                        return C(v.v)
                    out.append(expr(v))
                    break
                continue
            out.append(expr(v))
        if not out:
            return C(True if is_and else False) if empty is None else C(empty)
        return S("(" + (" and " if is_and else " or ").join(out) + ")")


def _no(what):
    raise Unfoldable(what)

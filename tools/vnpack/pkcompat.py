"""CPython source -> the Python the engine's interpreter (pocketpy) runs.

pocketpy speaks a dialect of Python 3: most programs run unchanged, but
some constructs don't parse or don't work there. This pass rewrites them,
on the AST, into equivalents it does run, so a game's own Python and the
screen runtime (vn3ds_rt.py) need no hand edits. What it can't rewrite
fails one statement at a time when the program loads (pyscreens.py loads
it statement by statement), not the whole program.

Rewritten:
  - default values that aren't literals, defaults before *args, keyword-only
    parameters: the function gets plain parameters and _with_defaults()
    supplies the defaults, evaluated once at definition as in CPython
  - a generator expression as an argument (pocketpy wants brackets): a list
  - {**a, k: v}: _merge_dicts(a, {k: v}); dict(...) with keywords or an
    iterable of pairs: _dict(...)
  - keyword arguments to built-ins that only take them positionally
  - `with a, b:` -> nested withs; try/except/else -> a flag; finally ->
    run after the try and in a handler that re-raises (not on a return)
  - classes inside a class body: defined before it
  - super().__init__(...) where the base is object: allowed to fail
  - x **= y, x //= y, ... -> x = x ** y; `for x[k] in ...` -> a plain loop name
  - the name `match` (a keyword there)
  - a class with __eq__ but no __ne__ gets one
The runtime's prelude (vn3ds_rt.py) adds the missing methods and builtins
(str.isdigit, dict.setdefault, tuple +, % formatting, str.format(**kw), ...).
"""

import ast

RENAMED = {"match": "match_vn", "_": "_vn_tr"}   # names the interpreter reserves

# built-ins that take these keyword arguments only by position there
KW_TO_POS = {
    "enumerate": ("iterable", "start"),
    "int": ("x", "base"),
    "round": ("number", "ndigits"),
    "range": ("start", "stop", "step"),
    "sorted": None,       # key= / reverse= work
}
METHOD_KW_TO_POS = {
    "split": ("sep", "maxsplit"),
    "rsplit": ("sep", "maxsplit"),
    "replace": ("old", "new", "count"),
    "get": ("key", "default"),
    "pop": ("key", "default"),
    "encode": ("encoding", "errors"),
    "decode": ("encoding", "errors"),
}
EXPANDED_AUG = (ast.Pow, ast.FloorDiv, ast.Mod, ast.LShift, ast.RShift, ast.BitAnd, ast.BitOr,
                ast.BitXor, ast.MatMult)


def _literal(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (str, int, float, bool,
                                                                  type(None))):
        return True
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)) and \
            isinstance(node.operand, ast.Constant) and isinstance(node.operand.value, (int, float)):
        return True
    return False   # tuples aren't (not even ())


def _name(id, ctx=None):
    return ast.Name(id, ctx or ast.Load())


def _call(fn, args, keywords=()):
    return ast.Call(_name(fn) if isinstance(fn, str) else fn, list(args), list(keywords))


class Compat(ast.NodeTransformer):
    def __init__(self):
        self.n = 0

    def _tmp(self, base):
        self.n += 1
        return f"_vn_{base}{self.n}"

    # -- names
    def visit_Name(self, node):
        if node.id in RENAMED:
            node.id = RENAMED[node.id]
        return node

    def visit_arg(self, node):
        if node.arg in RENAMED:
            node.arg = RENAMED[node.arg]
        self.generic_visit(node)
        return node

    def visit_keyword(self, node):
        if node.arg in RENAMED:
            node.arg = RENAMED[node.arg]
        self.generic_visit(node)
        return node

    def visit_Attribute(self, node):
        self.generic_visit(node)
        if node.attr in RENAMED:
            if isinstance(node.ctx, ast.Load):
                return ast.copy_location(_call("getattr", [node.value, ast.Constant(node.attr)]),
                                         node)
            node.attr = RENAMED[node.attr]
        return node

    # -- functions
    def _needs_wrap(self, args):
        if args.kwonlyargs:
            return True
        if any(not _literal(d) for d in args.defaults):
            return True
        if args.defaults and args.vararg:
            return True
        return False

    def _wrap_info(self, args):
        """Strips defaults/kw-only from `args`; returns the wrapper's call
        pieces: (names, defaults dict node, star, kwonly names)."""
        pos = args.posonlyargs + args.args
        names = [a.arg for a in pos]
        dkeys, dvals = [], []
        for a, d in zip(pos[len(pos) - len(args.defaults):], args.defaults):
            dkeys.append(ast.Constant(a.arg))
            dvals.append(d)
        kwonly = [a.arg for a in args.kwonlyargs]
        for a, d in zip(args.kwonlyargs, args.kw_defaults):
            if d is not None:
                dkeys.append(ast.Constant(a.arg))
                dvals.append(d)
        args.defaults = []
        args.kw_defaults = []
        args.args = pos
        args.posonlyargs = []
        args.kwonlyargs = []
        kwname = None
        if kwonly:
            if args.kwarg is None:
                args.kwarg = ast.arg("_vn_kw")
            kwname = args.kwarg.arg
        return names, ast.Dict(dkeys, dvals), args.vararg is not None, kwonly, kwname

    def _wrapper(self, fn_expr, info):
        names, defaults, star, kwonly, _ = info
        return _call("_with_defaults", [
            fn_expr, ast.Tuple([ast.Constant(n) for n in names], ast.Load()), defaults,
            ast.Constant(star), ast.Tuple([ast.Constant(n) for n in kwonly], ast.Load())])

    def _kwonly_prologue(self, info):
        _, _, _, kwonly, kwname = info
        return [ast.Assign([_name(k, ast.Store())],
                           _call(ast.Attribute(_name(kwname), "pop", ast.Load()),
                                 [ast.Constant(k)]))
                for k in kwonly]

    def visit_FunctionDef(self, node):
        node.args.defaults = [self.visit(d) for d in node.args.defaults]
        node.args.kw_defaults = [self.visit(d) if d is not None else None
                                 for d in node.args.kw_defaults]
        for a in node.args.posonlyargs + node.args.args + node.args.kwonlyargs:
            self.visit_arg(a)
        node.body = self._stmts(node.body)
        if node.name in RENAMED:
            node.name = RENAMED[node.name]
        if not self._needs_wrap(node.args):
            node.decorator_list = [self.visit(d) for d in node.decorator_list]
            return node
        info = self._wrap_info(node.args)
        node.body = self._kwonly_prologue(info) + node.body
        decos = [self.visit(d) for d in node.decorator_list]
        node.decorator_list = []
        value = self._wrapper(_name(node.name), info)
        for d in reversed(decos):
            value = _call(d, [value])
        return [node, ast.copy_location(ast.Assign([_name(node.name, ast.Store())], value), node)]

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Lambda(self, node):
        node.args.defaults = [self.visit(d) for d in node.args.defaults]
        node.args.kw_defaults = [self.visit(d) if d is not None else None
                                 for d in node.args.kw_defaults]
        node.body = self.visit(node.body)
        if not self._needs_wrap(node.args):
            return node
        if node.args.kwonlyargs:
            return node   # rare; left as it is
        info = self._wrap_info(node.args)
        return ast.copy_location(self._wrapper(node, info), node)

    def visit_ClassDef(self, node):
        node.bases = [self.visit(b) for b in node.bases]
        node.keywords = [self.visit(k) for k in node.keywords]
        node.decorator_list = [self.visit(d) for d in node.decorator_list]
        node.body = self._class_comps(self._stmts(node.body))
        names = {st.name for st in node.body if isinstance(st, ast.FunctionDef)}
        if "__eq__" in names and "__ne__" not in names:
            node.body.append(ast.parse(
                "def __ne__(self, other):\n    return not self.__eq__(other)").body[0])
        # classes inside a class: defined before it, under a name of their own
        hoisted = []
        body = []
        for st in node.body:
            if isinstance(st, list):
                for x in st:
                    body.append(x)
                continue
            body.append(st)
        node.body = []
        renamed = {}
        for st in body:
            if isinstance(st, ast.ClassDef):
                inner = st.name
                st.name = f"_vn_{node.name}_{inner}"
                st.bases = [_name(renamed[b.id]) if isinstance(b, ast.Name) and b.id in renamed
                            else b for b in st.bases]
                renamed[inner] = st.name
                hoisted.append(st)
                node.body.append(ast.Assign([_name(inner, ast.Store())], _name(st.name)))
            else:
                node.body.append(st)
        node.body = node.body or [ast.Pass()]
        return hoisted + [node] if hoisted else node

    def _class_comps(self, body):
        """x = [f(t) for t in names] in a class body sees the class's names
        in Ren'Py's Python 2 (and not in Python 3): a loop does too."""
        out = []
        for st in body:
            v = getattr(st, "value", None)
            if isinstance(st, ast.Assign) and len(st.targets) == 1 and \
                    isinstance(st.targets[0], ast.Name) and isinstance(v, ast.ListComp) and \
                    len(v.generators) == 1 and not v.generators[0].is_async:
                g = v.generators[0]
                name = st.targets[0].id
                append = ast.Expr(_call(ast.Attribute(_name(name), "append", ast.Load()), [v.elt]))
                inner = append
                for cond in reversed(g.ifs):
                    inner = ast.If(cond, [inner], [])
                out.append(ast.Assign([_name(name, ast.Store())], ast.List([], ast.Load())))
                out.append(ast.For(g.target, g.iter, [inner], []))
                continue
            out.append(st)
        return out

    # -- expressions
    def visit_GeneratorExp(self, node):
        self.generic_visit(node)
        return ast.copy_location(ast.ListComp(node.elt, node.generators), node)

    def visit_Dict(self, node):
        self.generic_visit(node)
        if not any(k is None for k in node.keys):
            return node
        parts, cur_k, cur_v = [], [], []
        for k, v in zip(node.keys, node.values):
            if k is None:
                if cur_k:
                    parts.append(ast.Dict(cur_k, cur_v))
                    cur_k, cur_v = [], []
                parts.append(v)
            else:
                cur_k.append(k)
                cur_v.append(v)
        if cur_k:
            parts.append(ast.Dict(cur_k, cur_v))
        return ast.copy_location(_call("_merge_dicts", parts), node)

    def visit_Call(self, node):
        self.generic_visit(node)
        f = node.func
        if isinstance(f, ast.Name) and f.id == "dict" and (node.keywords or node.args):
            return ast.copy_location(_call("_dict", node.args, node.keywords), node)
        table = None
        if isinstance(f, ast.Name) and f.id in KW_TO_POS:
            table = KW_TO_POS[f.id]
        elif isinstance(f, ast.Attribute) and f.attr in METHOD_KW_TO_POS:
            table = METHOD_KW_TO_POS[f.attr]
        if table and node.keywords and not any(k.arg is None for k in node.keywords):
            names = list(table)
            kw = {k.arg: k.value for k in node.keywords}
            if set(kw) <= set(names):
                args = list(node.args)
                for nm in names[len(args):]:
                    if not kw:
                        break
                    if nm not in kw:
                        break
                    args.append(kw.pop(nm))
                if not kw:
                    node.args = args
                    node.keywords = []
        return node

    # -- statements
    def _stmts(self, body):
        out = []
        for st in body:
            r = self.visit(st)
            if r is None:
                continue
            out += r if isinstance(r, list) else [r]
        return out or [ast.Pass()]

    def generic_visit(self, node):
        for field, old in ast.iter_fields(node):
            if isinstance(old, list) and old and isinstance(old[0], ast.stmt):
                setattr(node, field, self._stmts(old))
            elif isinstance(old, list):
                new = []
                for v in old:
                    if isinstance(v, ast.AST):
                        v = self.visit(v)
                        if v is None:
                            continue
                        if isinstance(v, list):
                            new += v
                            continue
                    new.append(v)
                setattr(node, field, new)
            elif isinstance(old, ast.AST):
                setattr(node, field, self.visit(old))
        return node

    def visit_With(self, node):
        self.generic_visit(node)
        if len(node.items) <= 1:
            return node
        inner = ast.With(node.items[1:], node.body)
        inner = self.visit_With(inner)
        return ast.copy_location(ast.With(node.items[:1], [inner]), node)

    def visit_Try(self, node):
        self.generic_visit(node)
        out = self._try_else(node)
        if not node.finalbody:
            return out
        # finally: run on the way out, normally or by an exception
        fin = node.finalbody
        node.finalbody = []
        inner = out if isinstance(out, list) else [out]
        if not node.handlers:   # try/finally alone: the body itself
            inner = [st for x in inner for st in ([x] if x is not node else node.body)]
        e = self._tmp("e")
        guard = ast.Try(inner, [ast.ExceptHandler(_name("Exception"), e,
                                                  fin + [ast.Raise(_name(e), None)])], [], [])
        return [guard] + [ast.parse(ast.unparse(st)).body[0] for st in fin]

    def _try_else(self, node):
        if not node.orelse:
            return node
        flag = self._tmp("ok")
        set_true = ast.Assign([_name(flag, ast.Store())], ast.Constant(True))
        set_false = ast.Assign([_name(flag, ast.Store())], ast.Constant(False))
        node.body = node.body + [set_true]
        orelse = node.orelse
        node.orelse = []
        return [set_false, node, ast.If(_name(flag), orelse, [])]

    def visit_Expr(self, node):
        self.generic_visit(node)
        v = node.value
        if isinstance(v, ast.Call) and isinstance(v.func, ast.Attribute) and \
                v.func.attr == "__init__" and isinstance(v.func.value, ast.Call) and \
                isinstance(v.func.value.func, ast.Name) and v.func.value.func.id == "super":
            # object has no __init__ there: a base class's init may be missing
            return ast.Try([node], [ast.ExceptHandler(_name("AttributeError"), None,
                                                      [ast.Pass()])], [], [])
        return node

    def visit_For(self, node):
        self.generic_visit(node)
        simple = isinstance(node.target, ast.Name) or (
            isinstance(node.target, ast.Tuple) and all(isinstance(e, ast.Name) for e in node.target.elts))
        if simple:
            return node
        # for x[k] in ...: a plain name, then the assignment
        tmp = self._tmp("it")
        assign = ast.Assign([node.target], _name(tmp))
        node.target = _name(tmp, ast.Store())
        node.body = [assign] + node.body
        return node

    def visit_AugAssign(self, node):
        self.generic_visit(node)
        if not isinstance(node.op, EXPANDED_AUG):
            return node
        t = node.target
        load = ast.parse(ast.unparse(t), mode="eval").body
        return ast.copy_location(ast.Assign([t], ast.BinOp(load, node.op, node.value)), node)


def transform(tree):
    tree = Compat().visit(tree)
    return ast.fix_missing_locations(tree)


class _Unparser(ast._Unparser):
    """ast.unparse, with every `a if c else b` in parentheses (the
    interpreter refuses nested ones without) and *(...) around starred
    expressions."""

    def visit_IfExp(self, node):
        self.write("(")
        super().visit_IfExp(node)
        self.write(")")

    def visit_Starred(self, node):
        # *(a + b): the interpreter binds a bare * tighter than the operator
        self.write("*")
        if isinstance(node.value, (ast.Name, ast.Attribute, ast.Call, ast.Subscript)):
            self.traverse(node.value)
        else:
            self.write("(")
            self.traverse(node.value)
            self.write(")")


def unparse(tree):
    return _Unparser().visit(ast.fix_missing_locations(tree))


def convert_source(src):
    """Source text -> pocketpy-friendly source text."""
    return unparse(transform(ast.parse(src)))

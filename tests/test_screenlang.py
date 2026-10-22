"""The game's own screens and Python on vn3ds: the screen-language
translation (screenlang.py), the name resolution, the rewrites into the
engine interpreter's dialect (pkcompat.py), and the runtime (vn3ds_rt.py)
in CPython. The engine side is tests/pyscreens/ (run_tests.sh).
Run: python3 tests/test_screenlang.py"""

import ast
import os
import sys
import types

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
from vnpack import pkcompat, rpy   # noqa: E402
from vnpack.screenlang import Resolver, split_props, translate_screen   # noqa: E402

fail = 0


def check(ok, what):
    global fail
    print(("  ok: " if ok else "  FAIL: ") + what)
    fail |= not ok


def main():
    # -- property lines
    check(split_props('auto "x_%s.png" focus_mask True action Show("a"), Hide("b") at fade') ==
          ([], [("auto", '"x_%s.png"'), ("focus_mask", "True"),
                ("action", 'Show("a"), Hide("b")'), ("at", "fade")]),
          "imagebutton properties, an action list")
    check(split_props("(40-g.speed)*.01 repeat True action Function(g.tick)") ==
          (["(40-g.speed)*.01"], [("repeat", "True"), ("action", "Function(g.tick)")]),
          "timer: an expression, then properties")
    check(split_props("2 3")[0] == ["2", "3"], "grid 2 3: two values")
    check(split_props("action action", first_prop=True)[1] == [("action", "action")],
          "a property whose value is a name like a property")
    check(split_props("xalign 1.0 if x else 0.0 yalign 0", first_prop=True)[1] ==
          [("xalign", "1.0 if x else 0.0"), ("yalign", "0")], "a conditional value")

    # -- a screen
    src = '''screen s(g=handler):
    default n = 0
    timer .5 repeat True action Function(g.tick)
    frame xysize 100,100:
        for i in range(n):
            text "[i]"
        textbutton "Go" action [SetScreenVariable("n", n + 1), SetVariable("score", score + 1)]
    if flag:
        $ n += 1
'''
    node = rpy.parse_file(src, "t.rpy")[0]
    warned = []
    fn = translate_screen("s", "g=handler", node.body, lambda l, m: warned.append(m))
    tree = ast.parse(fn)
    from vnpack.screenlang import screen_scope_names
    scope = screen_scope_names(tree) | {"g"}
    code = ast.unparse(Resolver({"score", "flag"}, scope).run(tree))
    check(not warned, "the screen translates without warnings")
    check("_sc['n']" in code and "_sc['g'].tick" in code, "screen scope: defaults and parameters")
    check("_get('score')" in code and "_get('flag')" in code, "story variables through _get")
    check("for i in range(_sc['n'])" in code, "a loop variable stays local")
    check("_ui.timer(0.5, repeat=True" in code and "with _ui.frame(xysize=(100, 100)" in code,
          "displayables as calls, containers as with blocks")

    # -- story variables in init python functions
    tree = Resolver({"score"}, module=True).run(ast.parse(
        "score = 5\nclass A:\n    def win(self):\n        global score\n        score += 1\n"))
    code = ast.unparse(tree)
    check("score = 5" not in code, "an init-time story value is left to the story")
    check("_set('score', _get('score') + 1)" in code, "a function's global story variable")

    # -- the interpreter's dialect
    out = pkcompat.convert_source('''
class A(B):
    class Inner:
        pass
    def __init__(self, child=None, *a, k=Q, **kw):
        super(A, self).__init__(**kw)
    def __eq__(self, o):
        return True
x = {**a, "b": 1}
y = " ".join(n for n in z)
with p as q, r as s:
    try:
        pass
    except E:
        pass
    else:
        v = 2
    finally:
        w = 3
x **= 2
f = lambda d=d: d
match = c if a else b if c else d
for o[k] in t:
    pass
''')
    check("_with_defaults(__init__" in out and "def __init__(self, child, *a, **kw)" in out,
          "defaults go to _with_defaults")
    check("class _vn_A_Inner" in out and "Inner = _vn_A_Inner" in out, "nested class hoisted")
    check("def __ne__" in out, "__ne__ added")
    check("_merge_dicts(a, {'b': 1})" in out, "{**a} merged")
    check("' '.join([n for n in z])" in out, "a generator argument becomes a list")
    check("finally" not in out and "else:" not in out.split("with p as q")[1].split("x = ")[0],
          "try/else/finally rewritten")
    check("x = x ** 2" in out, "**= expanded")
    check("match_vn = " in out and "(b if c else d)" in out, "match renamed, nested ternary in ()")
    check("for _vn_it" in out, "a subscript loop target goes through a name")
    compile(out, "<compat>", "exec")
    check(True, "the rewritten source is valid Python")

    # -- the runtime itself, through the same rewrites, in CPython
    rt = open(os.path.join(os.path.dirname(pkcompat.__file__), "vn3ds_rt.py")).read()
    V = {"_vn3ds_screens": ""}
    m = types.ModuleType("_vn3ds")
    m.has = lambda n: n in V
    m.get = lambda n: V.get(n)
    m.set = lambda n, v: V.__setitem__(n, v)
    m.play = m.queue = m.stop = lambda *a: None
    m.playing = lambda ch: ""
    m.text_width = lambda s, size: len(s) * size * 0.5
    m.line_height = lambda size: size * 1.2
    m.log = print
    m.seen_label = lambda n: True
    sys.modules["_vn3ds"] = m
    g = {"__name__": "vn3ds_rt"}
    exec(compile(pkcompat.convert_source(rt), "vn3ds_rt", "exec"), g)
    check(g["_percent"]("%5.2f|%-3s|%03d", (1.5, "a", 7)) == " 1.50|a  |007", "% formatting")
    check(g["_format_kw"]("{a}-{0}-{b.real}", 1, a=2, b=3) == "2-1-3", "str.format with names")
    p = g["_canon_into"]({"xpos": 408, "xsize": 1220}, {"xalign": 1.0, "padding": (10, 4)})
    check(p["xpos"] == 1.0 and p["xanchor"] == 1.0 and p["left_padding"] == 10 and
          p["bottom_padding"] == 4, "a later xalign overrides an earlier xpos; padding expanded")
    print("screen language: " + ("FAIL" if fail else "all ok"))
    return fail


if __name__ == "__main__":
    sys.exit(main())

"""Free roam: a game's point-and-click house rebuilt as choice menus.

Some Ren'Py games let the player walk between rooms and click things in
them (a bed to nap in, a door to knock on), drawn by one screen from tables
in the game's Python: the rooms with a background per time of day, and the
hotspots in each room with the label they start. vn3ds can't run that
screen, but the tables say everything it does. An adapter entry names them:

    "minigames": {"room": {"mechanic": "free_roam",
        "rooms": "ROOMS",            {room: {"bg": {slot: name}, "hide_nav": (...)}}
        "hotspots": "HOTSPOTS",      {room: [dict(slots=(...), label="x_{slot}",
                                               cond=fn, tip="key")]}
        "nav_order": "NAV_ORDER",    the rooms the player can walk to
        "slots": "SLOTS",            the times of day, the first is the default
        "time": "time_of_day",       the variable holding the time of day
        "room": "current_room",      the variable holding the room
        "background": "images/backgrounds/{bg}.png",
        "room_tips": "ROOM_TIP",     {room: (title, "Go to ...")} (optional)
        "hotspot_tips": "HOTSPOT_TIP",   {tip: (title, caption)} (optional)
        "slot_tips": {"nap": "NAP_TIP"}, a tip whose text depends on the time
        "collectibles": {"table": "ARTIFACTS", "var": "artifact{n}",
                         "level": "robin_progression_level"}}}   (optional)

Every `call screen room(...)` (and every screen that is just `use room(...)`)
becomes: set the room variable, then a loop that shows the room's background
for the time of day and a menu of its hotspots (each starts its label) and
the rooms to walk to. A hotspot's `cond` (a function returning one
expression, or a function returning such a lambda) becomes the menu item's
condition. The tables are read from the game's Python without running it.
"""

import ast
import copy
import re

from . import rpy

LOOP = "_vn3ds_free_roam"


class _Func:
    """A reference to one of the game's functions (with arguments)."""

    def __init__(self, name, args=()):
        self.name, self.args = name, tuple(args)


class _Lambda:
    """A `lambda: <expression>` in a table (a condition)."""

    def __init__(self, body):
        self.body = body


class Unreadable(Exception):
    pass


class Tables:
    """The game's init-python names, evaluated on demand and only as far as
    plain data goes (literals, comprehensions, dict(), _(), constants)."""

    def __init__(self, files):
        self.src, self.funcs, self.vals, self.classes = {}, {}, {}, {}
        self.make_object = None   # pyinline.Inliner: objects of simple classes
        for nodes in files:
            for n in rpy.iter_nodes(nodes):
                if isinstance(n, rpy.Define) and "." not in n.name:   # define X = ...
                    try:
                        self.src[n.name] = ast.parse(n.expr.strip(), mode="eval").body
                    except SyntaxError:
                        pass
                if isinstance(n, rpy.Python) and getattr(n, "init", False):
                    try:
                        tree = ast.parse(n.code)
                    except SyntaxError:
                        continue
                    for st in tree.body:
                        if isinstance(st, ast.Assign) and len(st.targets) == 1 and \
                                isinstance(st.targets[0], ast.Name):
                            self.src[st.targets[0].id] = st.value
                        elif isinstance(st, ast.FunctionDef):
                            self.funcs[st.name] = st
                        elif isinstance(st, ast.ClassDef):
                            self.classes[st.name] = st

    def get(self, name):
        if name in self.vals:
            return self.vals[name]
        if name in self.funcs:
            return _Func(name)
        if name not in self.src:
            raise Unreadable(f"no table {name}")
        self.vals[name] = None   # (a cycle reads as None)
        v = self.vals[name] = self.ev(self.src[name], {})
        return v

    def ev(self, n, env):
        if isinstance(n, ast.Constant):
            return n.value
        if isinstance(n, ast.Name):
            return env[n.id] if n.id in env else self.get(n.id)
        if isinstance(n, ast.Dict):
            return {self.ev(k, env): self.ev(v, env) for k, v in zip(n.keys, n.values)}
        if isinstance(n, (ast.List, ast.Tuple, ast.Set)):
            return tuple(self.ev(e, env) for e in n.elts)
        if isinstance(n, (ast.DictComp, ast.ListComp)) and len(n.generators) == 1:
            g = n.generators[0]
            if not isinstance(g.target, ast.Name):
                raise Unreadable("comprehension target")
            out = {} if isinstance(n, ast.DictComp) else []
            for item in self.ev(g.iter, env):
                e = dict(env, **{g.target.id: item})
                if not all(self.ev(c, e) for c in g.ifs):
                    continue
                if isinstance(n, ast.DictComp):
                    out[self.ev(n.key, e)] = self.ev(n.value, e)
                else:
                    out.append(self.ev(n.elt, e))
            return out if isinstance(n, ast.DictComp) else tuple(out)
        if isinstance(n, ast.BinOp) and isinstance(n.op, (ast.Add, ast.Mod)):
            a, b = self.ev(n.left, env), self.ev(n.right, env)
            if isinstance(a, (str, int, float)) and isinstance(b, (str, int, float, tuple)):
                return a + b if isinstance(n.op, ast.Add) else a % b
        if isinstance(n, ast.Compare) and len(n.ops) == 1 and \
                isinstance(n.ops[0], (ast.Eq, ast.NotEq)):
            a, b = self.ev(n.left, env), self.ev(n.comparators[0], env)
            return (a == b) == isinstance(n.ops[0], ast.Eq)
        if isinstance(n, ast.Lambda) and not n.args.args:
            return _Lambda(n.body)
        if isinstance(n, ast.Attribute):   # a field of an object in a table
            base = self.ev(n.value, env)
            if base is not None and hasattr(base, n.attr) and not isinstance(base, _Func):
                return getattr(base, n.attr)
            raise Unreadable(ast.unparse(n)[:60])
        if isinstance(n, ast.IfExp):
            return self.ev(n.body if self.ev(n.test, env) else n.orelse, env)
        if isinstance(n, ast.BoolOp):
            v = None
            for e in n.values:
                v = self.ev(e, env)
                if bool(v) != isinstance(n.op, ast.And):
                    return v
            return v
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name):
            fn = n.func.id
            if fn in ("_", "__") and n.args:
                return self.ev(n.args[0], env)
            if fn == "dict" and not n.args:
                return {k.arg: self.ev(k.value, env) for k in n.keywords if k.arg}
            if fn in self.funcs:
                return _Func(fn, [self.ev(a, env) for a in n.args])
            if fn in self.classes and self.make_object:
                return self.make_object(self.classes[fn], [self.ev(a, env) for a in n.args],
                                        {k.arg: self.ev(k.value, env) for k in n.keywords if k.arg})
        raise Unreadable(ast.unparse(n)[:60])

    def call(self, name, args):
        """A function whose body is `return <data>` (with its parameters), or
        raises Unreadable."""
        fd = self.funcs.get(name)
        body = [s for s in (fd.body if fd else []) if not (isinstance(s, ast.Expr) and
                                                            isinstance(s.value, ast.Constant))]
        if not fd or len(body) != 1 or not isinstance(body[0], ast.Return):
            raise Unreadable(f"{name}() isn't plain data")
        return self.ev(body[0].value, dict(zip([a.arg for a in fd.args.args], args)))

    def condition(self, ref):
        """A function reference (or a lambda) as a script condition, or None."""
        if isinstance(ref, _Lambda):
            return _cond(ref.body, {})
        if not isinstance(ref, _Func) or not self.funcs.get(ref.name):
            return None
        fd = self.funcs[ref.name]
        body = [s for s in fd.body if not (isinstance(s, ast.Expr) and
                                           isinstance(getattr(s, "value", None), ast.Constant))]
        if len(body) != 1 or not isinstance(body[0], ast.Return) or body[0].value is None:
            return None
        if not ref.args and fd.args.args:
            return None
        expr = body[0].value
        if isinstance(expr, ast.Lambda):   # min_level(n) -> lambda: level >= n
            expr = expr.body
        return _cond(expr, {a.arg: v for a, v in zip(fd.args.args, ref.args)})


def _cond(expr, params):
    """An expression over story variables (store.x or x) as script source, or
    None when it calls or indexes anything."""
    expr = copy.deepcopy(expr)

    class Sub(ast.NodeTransformer):
        def visit_Name(self, node):
            if node.id in params:
                return ast.copy_location(ast.Constant(params[node.id]), node)
            return node

        def visit_Attribute(self, node):
            self.generic_visit(node)
            if isinstance(node.value, ast.Name) and node.value.id == "store":
                return ast.copy_location(ast.Name(id=node.attr, ctx=ast.Load()), node)
            return node
    expr = Sub().visit(expr)
    for sub in ast.walk(expr):   # only plain variables and constants
        if isinstance(sub, (ast.Call, ast.Attribute, ast.Lambda, ast.Subscript)):
            return None
    return ast.unparse(expr)

def _q(s):
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


def _plain(s):
    """Text without {tags} (the menu draws its own)."""
    return re.sub(r"\{[^{}]*\}", "", str(s)).strip()


def _tip(tips, key, i):
    t = tips.get(key) if isinstance(tips, dict) else None
    if isinstance(t, tuple) and len(t) > i and t[i]:
        return _plain(t[i])
    return None


def generate(cfg, tables, labels, warn, line):
    """The loop's script (Ren'Py source) for an adapter entry, or None."""
    try:
        rooms = tables.get(cfg["rooms"])
        hotspots = tables.get(cfg["hotspots"]) if cfg.get("hotspots") else {}
        slots = list(tables.get(cfg["slots"]))
        nav = list(tables.get(cfg["nav_order"])) if cfg.get("nav_order") else list(rooms)
    except (Unreadable, KeyError, TypeError) as e:
        warn(line, f"free roam: can't read the game's tables ({e})")
        return None
    get = lambda key: _soft(tables, cfg.get(key))   # noqa: E731
    room_tips, hot_tips = get("room_tips") or {}, get("hotspot_tips") or {}
    slot_tips = {k: _soft(tables, v) or {} for k, v in (cfg.get("slot_tips") or {}).items()}
    coll = cfg.get("collectibles") or {}
    coll_table = _soft(tables, coll.get("table")) or {}
    time_var, room_var = cfg.get("time", "time_of_day"), cfg.get("room", "current_room")
    bg_fmt = cfg.get("background", "{bg}")
    start = cfg.get("start") or (nav[0] if nav else next(iter(rooms)))
    out = [f"label {LOOP}:"]
    first_room = True
    for rid, room in rooms.items():
        if not isinstance(room, dict):
            continue
        out.append(f"    {'if' if first_room else 'elif'} {room_var} == {_q(rid)}:")
        first_room = False
        hidden = room.get("hide_nav") or ()
        title = _tip(room_tips, rid, 0) or rid.replace("_", " ").title()
        ordered = slots[1:] + slots[:1]   # the first slot is the fallback (else)
        for k, slot in enumerate(ordered):
            last = k == len(ordered) - 1
            out.append(f"        {'else' if last else ('if' if k == 0 else 'elif')}"
                       f"{'' if last else f' {time_var} == {_q(slot)}'}:")
            ind = " " * 12
            bg = (room.get("bg") or {}).get(slot)
            if bg:
                out.append(f"{ind}scene expression {_q(bg_fmt.format(bg=bg))} with dissolve")
            out.append(f"{ind}menu:")
            out.append(f"{ind}    {_q(title + ' · ' + slot.title())}")
            items = 0
            for h in (hotspots or {}).get(rid, ()):
                if not isinstance(h, dict) or slot not in (h.get("slots") or ()):
                    continue
                label = str(h.get("label", "")).replace("{slot}", slot)
                if label not in labels:
                    warn(line, f"free roam: hotspot label {label} isn't defined; left out")
                    continue
                tip = h.get("tip")
                text = (_tip(slot_tips.get(tip, {}), slot, 0) if tip in slot_tips else None) or \
                    _tip(hot_tips, tip, 1) or _tip(hot_tips, tip, 0) or \
                    (tip or label).replace("_", " ").capitalize()
                cond = ""
                if h.get("cond") is not None:
                    c = tables.condition(h["cond"])
                    if c:
                        cond = f" if {c}"
                    else:
                        warn(line, f"free roam: the condition of {label} can't be read; it is "
                                   "always offered")
                out += [f"{ind}    {_q(text)}{cond}:",
                        f"{ind}        jump {label}"]
                items += 1
            for n, entry in sorted((coll_table or {}).items()):
                if not (isinstance(entry, tuple) and len(entry) >= 2 and entry[0] == rid and
                        entry[1] == slot):
                    continue
                var = coll.get("var", "collectible{n}").format(n=n)
                cond = f"not {var}"
                if coll.get("level") and len(entry) > 3 and entry[3]:
                    cond += f" and {coll['level']} >= {entry[3]}"
                out += [f"{ind}    {_q(coll.get('text', 'Pick up the collectible'))} if {cond}:",
                        f"{ind}        $ {var} = True",
                        f"{ind}        jump {LOOP}"]
                items += 1
            for target in nav:
                if target == rid or target in hidden or target not in rooms:
                    continue
                text = _tip(room_tips, target, 1) or \
                    "Go to " + _plain((rooms[target] or {}).get("nav_label") or target)
                out += [f"{ind}    {_q(text)}:",
                        f"{ind}        $ {room_var} = {_q(target)}",
                        f"{ind}        jump {LOOP}"]
                items += 1
            if not items:
                out += [f"{ind}    \"Look around\":", f"{ind}        jump {LOOP}"]
    out += [f"    $ {room_var} = {_q(start)}", f"    jump {LOOP}"]
    return "\n".join(out) + "\n"


def topics_label(rid, slot, page=None):
    return f"_vn3ds_topics_{rid}_{slot}" + (f"_{page}" if page else "")


def generate_topics(cfg, roam, tables, labels, warn, line, rid, slot):
    """A character's talk menu in room rid at time slot (adapter mechanic
    "topics"): its pages from cfg["buttons"] (a function returning
    (key, title, icon, ("page", page)) rows), each page's topics from
    cfg["topics"][cfg["key"]] as (caption, label, lambda: condition).
    Script source, or None."""
    try:
        buttons = tables.call(cfg["buttons"], [rid, slot]) if cfg.get("buttons") else ()
        topics = tables.get(cfg["topics"])
    except (Unreadable, KeyError, TypeError) as e:
        warn(line, f"talk menu: can't read the game's tables ({e})")
        return None
    pages = []   # (page, title, [(caption, label, condition)])
    for b in buttons or ():
        if not (isinstance(b, tuple) and len(b) >= 4 and isinstance(b[3], tuple) and
                len(b[3]) == 2 and b[3][0] == "page"):
            continue
        page = b[3][1]
        rows = []
        for t in topics.get(cfg.get("key", "{page}_{slot}").format(page=page, slot=slot), ()):
            if not (isinstance(t, tuple) and len(t) >= 2) or t[1] not in labels:
                continue
            cond = tables.condition(t[2]) if len(t) > 2 and t[2] is not None else None
            if len(t) > 2 and t[2] is not None and cond is None:
                warn(line, f"talk menu: the condition of {t[1]} can't be read; it is always offered")
            rows.append((_plain(t[0]), t[1], cond))
        gifts = cfg.get("gifts")
        if page == (gifts or {}).get("page"):
            for g in _items(tables, gifts):
                rows.append((_plain(getattr(g, gifts.get("name", "name"), "")),
                             ("give", g), _owned_cond(g, gifts)))
        if rows:
            pages.append((page, _plain(b[1]), rows))
    room_var = roam.get("room", "current_room")
    bg = None
    try:
        bg = tables.get(roam["rooms"])[rid]["bg"][slot]
    except (Unreadable, KeyError, TypeError):
        pass
    head = []
    if bg:
        head.append(f"    scene expression {_q(roam.get('background', '{bg}').format(bg=bg))}")
    if cfg.get("show"):
        head.append(f"    show {cfg['show']}")
    title = _tip(_soft(tables, roam.get("room_tips")) or {}, rid, 0) or rid.replace("_", " ").title()
    main = topics_label(rid, slot)
    out = [f"label {main}:"] + head + ["    menu:", f"        {_q(title + ' · ' + slot.title())}"]
    for page, ptitle, rows in pages:
        any_cond = " or ".join(f"({c})" for _, _, c in rows if c) if all(c for _, _, c in rows) \
            else ""
        out += [f"        {_q(ptitle)}{' if ' + any_cond if any_cond else ''}:",
                f"            jump {topics_label(rid, slot, page)}"]
    out += ["        \"Go back\":", f"            $ {room_var} = {_q(rid)}", f"            jump {LOOP}"]
    for page, ptitle, rows in pages:
        out += [f"label {topics_label(rid, slot, page)}:"] + head + ["    menu:"]
        for caption, label, cond in rows:
            out.append(f"        {_q(caption)}{' if ' + cond if cond else ''}:")
            if isinstance(label, tuple):   # give a gift: the game's own label takes it
                g, gifts = label[1], cfg["gifts"]
                out += [f"            $ {gifts['var']} = {_q(getattr(g, gifts.get('id', 'id')))}",
                        f"            jump {gifts['label']}"]
            else:
                out.append(f"            jump {label}")
        out += ["        \"Go back\":", f"            jump {main}"]
    return "\n".join(out) + "\n"


def _items(tables, cfg):
    try:
        items = tables.get(cfg["items"])
    except (Unreadable, KeyError):
        return []
    return list(items.values() if isinstance(items, dict) else items or ())


def _owned_cond(g, cfg):
    """The story variable that says an item is owned (cfg["owned"] names the
    item field holding the variable's name), as a condition."""
    var = getattr(g, cfg.get("owned", ""), None)
    return var if isinstance(var, str) and var.isidentifier() else None


SHOP = "_vn3ds_shop_"


def generate_shop(cfg, tables, labels, warn, line, screen):
    """A shop screen (adapter mechanic "shop"): the items not owned yet and
    unlocked as menu choices, each jumping to its purchase label (which
    checks the money), then "Go back" (returns from the call)."""
    items = _items(tables, cfg)
    if not items:
        warn(line, f"shop: can't read {cfg.get('items')}")
        return None
    out = [f"label {SHOP}{screen}:", "    menu:"]
    for g in items:
        label = getattr(g, cfg.get("label", "purchase_label"), None)
        if not isinstance(label, str) or label not in labels:
            continue
        name = _plain(getattr(g, cfg.get("name", "name"), label))
        price = getattr(g, cfg.get("price", "price"), None)
        text = f"{name} (${price})" if isinstance(price, (int, float)) else name
        conds = []
        owned = _owned_cond(g, cfg)
        if owned:
            conds.append(f"not {owned}")
        lvl = cfg.get("level")
        if lvl and isinstance(getattr(g, lvl[0], None), (int, float)):
            conds.append(f"{lvl[1]} >= {getattr(g, lvl[0])}")
        out += [f"        {_q(text)}{' if ' + ' and '.join(conds) if conds else ''}:",
                f"            jump {label}"]
    back = cfg.get("back")   # where the shop's own back button jumps, if it does
    out += ["        \"Go back\":", f"            jump {back}" if back in labels else "            return"]
    return "\n".join(out) + "\n"


def _soft(tables, name):
    if not name:
        return None
    try:
        return tables.get(name)
    except Unreadable:
        return None


def wrappers(files, screens):
    """Screens whose whole body is `use <a free roam screen>(...)`:
    {name: (screen, args source)}."""
    out = {}
    for nodes in files:
        for n in rpy.iter_nodes(nodes):
            if not isinstance(n, rpy.Screen):
                continue
            lines = [l.text.strip() for l in (getattr(n, "body", None) or []) if l.text.strip()]
            if len(lines) == 1:
                m = re.match(r"use\s+(\w+)\s*(\(.*\))?\s*$", lines[0])
                if m and m.group(1) in screens:
                    out[n.name] = (m.group(1), m.group(2))
    return out


def room_arg(args):
    """The room argument of a call's "(...)" source: (source, is a literal)."""
    if not args:
        return None
    try:
        call = ast.parse("f" + args, mode="eval").body
    except SyntaxError:
        return None
    a = call.args[0] if call.args else next((k.value for k in call.keywords if k.arg == "rid"),
                                             None)
    return ast.unparse(a) if a is not None else None

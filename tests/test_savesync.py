"""Saves between Ren'Py on the Mac and vn3ds on the 3DS (tools/vnpack/savesync.py).

    python3 tests/test_savesync.py [engine/build-host/vn3ds-host]

A small game is ported, with compiled scripts (.rpyc) and Ren'Py saves made
up here the way Ren'Py writes them (the classes stood in for, as on any
computer without Ren'Py). Then:

1. Ren'Py -> vn3ds: a Ren'Py save made inside a called label converts, and
   the desktop build loads it: same line, variables, call stack (it returns
   to the right place), pictures and music.
2. vn3ds -> Ren'Py: a save the desktop build made converts into a Ren'Py
   save that names the same statement, call stack, variables and pictures.
3. Sync over Wi-Fi with `vn3ds-host --receive` standing in for the 3DS:
   saves go both ways; a change on one side is copied; when both changed
   the newer wins and the other is kept as a backup; deletions follow; the
   3DS nudges the computer when it opens; the background agent syncs a
   save made on the 3DS by itself.
4. The installed-games list finds a game folder and a Mac .app.
5. A real Ren'Py save on this Mac, if there is one, reads and writes back
   unchanged (the stand-in classes lose nothing).

Nothing here touches a real 3DS: everything runs on 127.0.0.1."""

import glob
import io
import json
import os
import shutil
import socket
import struct
import subprocess
import sys
import tempfile
import threading
import time
import wave
import zipfile
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(REPO, "tools"))

TMP = tempfile.mkdtemp(prefix="vn3ds-savesync-")
os.environ["VN3DS_SYNC_DIR"] = os.path.join(TMP, "sync")
os.environ["VN3DS_RENPY_HOME"] = os.path.join(TMP, "RenPy")
os.environ["VN3DS_SCAN_HOSTS"] = "127.0.0.1"
os.environ["VN3DS_NETLOADER_ADDRESS"] = "127.0.0.1"

from vnpack import library, renpysave, savesync, vn3dssave  # noqa: E402
from vnpack.savemap import SaveMap  # noqa: E402

HOST = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO, "engine", "build-host", "vn3ds-host")
SAVE_DIR = "SyncTest-1700000000"
fail = 0


def check(cond, what):
    global fail
    print(("  ok: " if cond else "  FAIL: ") + what)
    fail |= not cond


SCRIPT = '''define e = Character("Eileen")
default score = 0
default seen_intro = False
default player = "Kim"
default inventory = []
image bg room = "#334455"
image bg street = "#556677"
image eileen happy = "#ff8888"
image eileen sad = "#8888ff"

label start:
    scene bg room
    play music "audio/theme.wav"
    "Line one."
    $ score = 5
    $ player = "Ash"
    show eileen happy
    e "Line two."
    call side
    "Back from the call, score [score]."
    "The end."
    return

label side:
    scene bg street
    show eileen sad
    $ score += 10
    $ seen_intro = True
    e "Inside the call."
    e "Score [score], player [player], seen [seen_intro]."
    return
'''

OPTIONS = f'''define config.name = "Sync Test"
define config.version = "1.0"
define config.save_directory = "{SAVE_DIR}"
'''


def line_of(text):
    for i, l in enumerate(SCRIPT.split("\n")):
        if l.strip() == text:
            return i + 1
    raise KeyError(text)


# --------------------------------------------------------------------------
# Ren'Py's side, made up: compiled scripts and saves
# --------------------------------------------------------------------------

def stub(module, cls_name, **state):
    cls = renpysave._stub_class(module, cls_name)
    o = cls.__new__(cls)
    o._rp_state, o._rp_has_state = dict(state), True
    return o


def rlist(items):
    o = stub("renpy.python", "RevertableList")
    o._rp_has_state, o._rp_state = False, None
    o._rp_items = list(items)
    return o


FN = "game/script.rpy"
SERIAL = iter(range(1, 1000))


def node(kind, text, **extra):
    line = line_of(text)
    return stub("renpy.ast", kind, name=(FN, 1700000000, next(SERIAL)), filename=FN,
                linenumber=line, **extra)


def make_rpyc(path):
    """script.rpyc as Ren'Py compiles it: (data, statements) pickled, in a
    RENPY RPC2 container."""
    side_block = [node("Scene", "scene bg street"), node("Show", "show eileen sad"),
                  node("Python", "$ score += 10"), node("Python", "$ seen_intro = True"),
                  node("Say", 'e "Inside the call."'),
                  node("Say", 'e "Score [score], player [player], seen [seen_intro]."'),
                  node("Return", "return")]
    call = node("Call", "call side", label="side")
    after = node("Pass", "call side")
    start_block = [node("Scene", "scene bg room"),
                   node("UserStatement", 'play music "audio/theme.wav"'),
                   node("Say", '"Line one."'), node("Python", "$ score = 5"),
                   node("Python", '$ player = "Ash"'), node("Show", "show eileen happy"),
                   node("Say", 'e "Line two."'), call, after,
                   node("Say", '"Back from the call, score [score]."'),
                   node("Say", '"The end."'), node("Return", "return")]
    start = stub("renpy.ast", "Label", name="start", filename=FN, linenumber=line_of("label start:"),
                 block=start_block, parameters=None)
    side = stub("renpy.ast", "Label", name="side", filename=FN, linenumber=line_of("label side:"),
                block=side_block, parameters=None)
    blob = zlib.compress(renpysave.dumps(({"version": 5003000, "key": "unlocked"},
                                          [start, side]), False, 2))
    head = b"RENPY RPC2" + struct.pack("<III", 1, 34, len(blob)) + struct.pack("<III", 0, 0, 0)
    with open(path, "wb") as f:
        f.write(head + blob)
    return {"call": call, "after": after, "inside": side_block[4]}


def make_renpy_save(path, current, call_nodes, return_nodes, variables, images, music, say,
                    mtime):
    """A save the way Ren'Py writes one (zip with a pickled roots + log)."""
    entries = []
    for spec, tag in images:
        ref = stub("renpy.display.image", "ImageReference", name=tuple(spec.split()),
                   style=stub("renpy.styledata.styleclass", "Style", parent="image_placement"))
        tr = stub("renpy.display.transform", "Transform", child=ref, children=[ref],
                  state=stub("renpy.display.transform", "TransformState", xpos=0.5))
        entries.append(stub("renpy.display.core", "SceneListEntry", tag=tag,
                            name=tuple(spec.split()), zorder=0, show_time=1.0, animation_time=1.0,
                            displayable=tr))
    shown = stub("renpy.display.image", "ShownImageInfo",
                 attributes={("master", tag): tuple(spec.split()[1:]) for spec, tag in images},
                 shown={("master", tag) for _, tag in images})
    scene = stub("renpy.display.core", "SceneLists", layers={"master": entries, "screens": []},
                 at_list={"master": {tag: [] for _, tag in images}}, shown=shown)
    mc = stub("renpy.audio.audio", "MusicContext", last_filenames=[music] if music else [],
              last_tight=False)
    ctx = stub("renpy.execution", "Context", current=current.get("name"),
               return_stack=[n.get("name") for n in return_nodes],
               call_location_stack=[n.get("name") for n in call_nodes],
               dynamic_stack=[{} for _ in range(len(call_nodes) + 1)], scene_lists=scene,
               images=shown, music={"music": mc}, translate_identifier="script_abc", line_log=[],
               rollback=True)
    rb = stub("renpy.python", "Rollback", context=ctx,
              stores={"store": {"score": variables.get("score", 0)}}, objects=[],
              checkpoint=True, hard_checkpoint=True, forward=None)
    log = stub("renpy.python", "RollbackLog", log=rlist([stub("renpy.python", "Rollback",
                                                              context=ctx), rb]),
               current=rb, forward=[], rollback_limit=100)
    roots = {"store." + k: (rlist(v) if isinstance(v, list) else v) for k, v in variables.items()}
    roots.update({"store._last_say_who": say[0], "store._last_say_what": say[1],
                  "store._history_list": rlist(["old line"]),
                  "store._version": "1.0"})
    data = renpysave.dumps((roots, log), False, 2)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("screenshot.png", b"\x89PNG\r\n\x1a\n")
        z.writestr("extra_info", "")
        z.writestr("json", json.dumps({"_save_name": "", "_renpy_version": [8, 3, 0, 1],
                                       "_version": "1.0", "_ctime": mtime}))
        z.writestr("renpy_version", "Ren'Py 8.3.0.24082114")
        z.writestr("log", data)
    os.utime(path, (mtime, mtime))


# --------------------------------------------------------------------------

def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def port_game():
    src = os.path.join(TMP, "Sync Test")
    gd = os.path.join(src, "game")
    os.makedirs(os.path.join(gd, "audio"))
    os.makedirs(os.path.join(src, "renpy"))   # (so the installed-games list knows it)
    with open(os.path.join(gd, "script.rpy"), "w") as f:
        f.write(SCRIPT)
    with open(os.path.join(gd, "options.rpy"), "w") as f:
        f.write(OPTIONS)
    with wave.open(os.path.join(gd, "audio", "theme.wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(22050)
        w.writeframes(b"\0\0" * 22050)
    nodes = make_rpyc(os.path.join(gd, "script.rpyc"))
    r = run([os.path.join(REPO, "tools", "vnpack.sh"), src, "-o", os.path.join(TMP, "build"), "-q"])
    builds = glob.glob(os.path.join(TMP, "build", "*", "game.bin"))
    if r.returncode != 0 or not builds:
        print(r.stdout[-2000:], r.stderr[-2000:])
        sys.exit("FAIL: the test game didn't port")
    return src, os.path.dirname(builds[0]), nodes


def play(game_dir, root, *args):
    r = run([HOST, game_dir, "--root", root, "--max-lines", "8"] + list(args), timeout=120)
    return r.stdout + r.stderr


def main():
    src, game, nodes = port_game()
    smap = SaveMap(game)
    gid = smap.id
    check(os.path.exists(os.path.join(game, "savemap.json")), "savemap.json written with the port")
    check(smap.save_directory == SAVE_DIR, f"config.save_directory found ({smap.save_directory})")
    check(len(smap.nodes) >= 20, f"statement names read from script.rpyc ({len(smap.nodes)})")
    from vnpack import send
    check(not any(p.endswith("savemap.json") for p, _ in send.plan([game])),
          "savemap.json stays on the computer")

    print("1. Ren'Py -> vn3ds")
    renpy_dir = os.path.join(os.environ["VN3DS_RENPY_HOME"], SAVE_DIR)
    mac_save = os.path.join(renpy_dir, "1-1.save")
    make_renpy_save(mac_save, nodes["inside"], [nodes["call"]], [nodes["after"]],
                    dict(score=42, player="Mac", seen_intro=True, inventory=[1, 2]),
                    [("bg street", "bg"), ("eileen sad", "eileen")], "audio/theme.wav",
                    ("Eileen", "Inside the call."), time.time() - 3600)
    info = renpysave.read(mac_save)
    check(info.slot == "1-1" and info.call_nodes and info.images,
          f"the Ren'Py save reads back ({info.slot}, {len(info.variables)} variables)")
    data, notes = savesync.renpy_to_vn3ds(info, smap, time.time())
    check(any("inventory" in n for n in notes), "a list variable is reported as left at its default")
    root1 = os.path.join(TMP, "root1")
    os.makedirs(os.path.join(root1, "saves", gid))
    with open(os.path.join(root1, "saves", gid, "slot01.sav"), "wb") as f:
        f.write(data)
    out = play(game, root1, "--load", "1")
    check("[load] slot 1: ok" in out, "the desktop build loads the converted save")
    check("on screen: bg street, eileen sad" in out, "with the same pictures on screen")
    check(f"music: res {smap.music['audio/theme.wav']} " in out, "and the same music")
    check("Eileen: Score 42, player Mac, seen True." in out,
          "the variables came along (score 42, player Mac, seen True)")
    check("Back from the call, score 42." in out, "the call stack came along (it returns after the call)")

    print("2. vn3ds -> Ren'Py")
    root2 = os.path.join(TMP, "root2")
    out = play(game, root2, "--save-at", "3:2")
    check("[save] slot 2: ok" in out, "the desktop build saved inside the call")
    ds_path = os.path.join(root2, "saves", gid, "slot02.sav")
    s = vn3dssave.read(open(ds_path, "rb").read())
    check(s.get("sprite_size") == vn3dssave.SPRITE_SIZE,
          f"sizeof(Sprite) is {vn3dssave.SPRITE_SIZE} ({s.get('sprite_size')})")
    check([x[0] for x in s["specs"] or []] == ["bg street", "eileen sad"],
          f"the save names what is on screen ({s['specs']})")
    out_save = os.path.join(TMP, "from3ds.save")
    notes = savesync.vn3ds_to_renpy(open(ds_path, "rb").read(), smap, mac_save, out_save,
                                    time.time())
    back = renpysave.read(out_save)
    check(back.node == renpysave.node_key(nodes["inside"].get("name")),
          "the Ren'Py save names the same statement")
    check(back.call_nodes == [renpysave.node_key(nodes["call"].get("name"))] and
          back.return_nodes == [renpysave.node_key(nodes["after"].get("name"))],
          "and the same call stack (return to the statement after the call)")
    check(back.variables.get("score") == 15 and back.variables.get("player") == "Ash" and
          back.variables.get("seen_intro") is True,
          f"and the variables (score {back.variables.get('score')}, "
          f"player {back.variables.get('player')})")
    check([i[0] for i in back.images] == ["bg street", "eileen sad"], "and the pictures")
    check(back.music == "audio/theme.wav", "and the music")
    z = zipfile.ZipFile(out_save)
    check(z.read("screenshot.png").startswith(b"\x89PNG") and "json" in z.namelist(),
          "it keeps the parts Ren'Py lists saves with")

    print("3. sync over Wi-Fi with the desktop receiver")
    root3 = os.path.join(TMP, "root3")
    os.makedirs(os.path.join(root3, "saves", gid))
    shutil.copy(ds_path, os.path.join(root3, "saves", gid, "slot02.sav"))   # made on the 3DS
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp.bind(("127.0.0.1", 0))
    udp_port = udp.getsockname()[1]
    rx = subprocess.Popen([HOST, "--receive", "--serve", "90", "--root", root3],
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    try:
        t0 = time.time()
        while not savesync.detect.listening("127.0.0.1") and time.time() - t0 < 10:
            time.sleep(0.2)
        savesync.register(game)

        def sync(initial=False):
            link = savesync.WifiLink("127.0.0.1", agent_port=udp_port)
            try:
                return savesync.sync(link, savesync.game_maps(), initial=initial)[gid]
            finally:
                link.close()
        r = sync(initial=True)
        check([n for n, _ in r.to_3ds] == [1] and [n for n, _ in r.to_mac] == [2],
              f"first sync: slot 1 to the 3DS, slot 2 to the Mac ({r.summary()})")
        on3ds = os.path.join(root3, "saves", gid, "slot01.sav")
        check(os.path.exists(on3ds) and vn3dssave.read(open(on3ds, "rb").read())["pc"] > 0,
              "the 3DS has slot 1")
        mac2 = os.path.join(renpy_dir, "1-2.save")
        check(os.path.exists(mac2) and renpysave.read(mac2).variables.get("score") == 15,
              "the Mac has page 1 slot 2 (Ren'Py's 1-2.save)")
        time.sleep(0.3)   # (written by the main loop, a frame later)
        check(os.path.exists(os.path.join(root3, "sync.cfg")) and
              f"port = {udp_port}" in open(os.path.join(root3, "sync.cfg")).read(),
              "the 3DS remembers the computer (sync.cfg)")
        r = sync()
        check(r.summary() == "already in sync", f"nothing to do the second time ({r.summary()})")

        # a new save on the 3DS
        time.sleep(1.1)
        out = play(game, root3, "--save-at", "4:2")
        r = sync()
        check([n for n, _ in r.to_mac] == [2], f"a changed 3DS save goes to the Mac ({r.summary()})")
        check(renpysave.read(mac2).node == renpysave.node_key(
            next(k for k, v in smap.nodes.items() if v[1] == line_of(
                'e "Score [score], player [player], seen [seen_intro]."'))),
              "and resumes on the new line")
        backups = os.listdir(os.path.join(os.environ["VN3DS_SYNC_DIR"], "backups", gid))
        check(any("1-2" in b for b in backups), "the Mac's old 1-2 is kept as a backup")

        # a new save on the Mac
        make_renpy_save(mac_save, nodes["inside"], [nodes["call"]], [nodes["after"]],
                        dict(score=7, player="Mac2"), [("bg street", "bg")], None,
                        ("Eileen", "Inside the call."), time.time())
        r = sync()
        check([n for n, _ in r.to_3ds] == [1], f"a changed Mac save goes to the 3DS ({r.summary()})")
        check(os.path.exists(on3ds + ".bak"), "the 3DS keeps the one it replaced (slot01.sav.bak)")

        # both changed: the newer wins
        out = play(game, root3, "--save-at", "2:1")   # the 3DS saves slot 1 now...
        time.sleep(1.1)
        make_renpy_save(mac_save, nodes["inside"], [nodes["call"]], [nodes["after"]],
                        dict(score=99, player="Newest"), [("bg street", "bg")], None,
                        ("Eileen", "Inside the call."), time.time() + 5)   # ...the Mac after
        r = sync()
        check([n for n, _ in r.to_3ds] == [1], f"both changed: the newer (the Mac's) wins ({r.summary()})")
        bak = vn3dssave.read(open(on3ds + ".bak", "rb").read())
        check("Line two" in bak["preview"], "the 3DS's version is kept as slot01.sav.bak")
        root4 = os.path.join(TMP, "root4")
        os.makedirs(os.path.join(root4, "saves", gid))
        shutil.copy(on3ds, os.path.join(root4, "saves", gid, "slot01.sav"))
        out = play(game, root4, "--load", "1")
        check("Score 99, player Newest" in out, "the 3DS now plays the Mac's newest save")

        # deleting
        os.remove(mac2)
        r = sync()
        check([n for n, _ in r.deleted] == [2] and not os.path.exists(
            os.path.join(root3, "saves", gid, "slot02.sav")) and os.path.exists(
            os.path.join(root3, "saves", gid, "slot02.sav.bak")),
            f"a save deleted on the Mac is deleted on the 3DS, kept as .bak ({r.summary()})")

        # saves Ren'Py has that vn3ds has no slot for
        make_renpy_save(os.path.join(renpy_dir, "quick-1.save"), nodes["inside"], [nodes["call"]],
                        [nodes["after"]], dict(score=1), [], None, ("", ""), time.time())
        r = sync()
        check(any(s == "quick-1" and "quick" in why for s, why in r.kept_back),
              "a quick save is listed as not carried over, with the reason")
    finally:
        rx.terminate()
        rx.wait()

    # the 3DS nudges the computer when vn3ds opens
    rx = subprocess.Popen([HOST, "--receive", "--serve", "60", "--root", root3],
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    try:
        udp.settimeout(10)
        try:
            msg, _ = udp.recvfrom(128)
        except socket.timeout:
            msg = b""
        check(msg[:4] == b"VN3N" and struct.unpack_from("<I", msg, 4)[0] == 1,
              "vn3ds opening nudges the computer (UDP)")
        udp.close()

        # the agent, as at login: a save made on the 3DS reaches the Mac by itself
        stop = threading.Event()
        logs = []
        t = threading.Thread(target=savesync.run_agent,
                             kwargs=dict(port=udp_port, host="127.0.0.1", poll=1.0,
                                         say=logs.append, stop=stop.is_set), daemon=True)
        t.start()
        time.sleep(2.5)
        before = os.path.getmtime(mac_save)
        play(game, root3, "--save-at", "5:1")
        t0 = time.time()
        while time.time() - t0 < 20 and os.path.getmtime(mac_save) == before:
            time.sleep(0.5)
        stop.set()
        check(os.path.getmtime(mac_save) != before and
              renpysave.read(mac_save).variables.get("score") == 15,
              "the agent brought a new 3DS save to the Mac by itself")
        st = json.load(open(os.path.join(os.environ["VN3DS_SYNC_DIR"], "status.json")))
        check(st.get("host") == "127.0.0.1" and st.get("last_sync"), "it reports in status.json")
    finally:
        rx.terminate()
        rx.wait()

    print("4. installed games")
    apps = os.path.join(TMP, "Applications")
    app_game = os.path.join(apps, "Other Game.app", "Contents", "Resources", "autorun", "game")
    os.makedirs(app_game)
    shutil.copy(os.path.join(src, "game", "script.rpyc"), app_game)
    os.environ["VN3DS_LIBRARY_DIRS"] = os.pathsep.join([TMP, apps])
    found = {g.title: g for g in library.find()}
    check("Sync Test" in found and found["Sync Test"].saves >= 1 and found["Sync Test"].size > 0,
          f"a game folder: its title, size and saves ({sorted(found)})")
    check("Other Game" in found, "a Mac .app")

    print("5. a real Ren'Py save, read and written back")
    real = sorted(glob.glob(os.path.expanduser("~/Library/RenPy/*/*.save")))[:1]
    if not real:
        print("  (none on this Mac: skipped)")
    for p in real:
        raw = zipfile.ZipFile(p).read("log")
        roots, log, py2, proto = renpysave.loads(raw)
        again = renpysave.loads(renpysave.dumps((roots, log), py2, proto))
        check(canon(roots) == canon(again[0]) and canon(log) == canon(again[1]),
              f"{os.path.basename(p)} (Ren'Py {'7' if py2 else '8'}) round-trips")
        others = sorted(glob.glob(os.path.join(os.path.dirname(p), "*.save")))
        a, b = renpysave.read(p), renpysave.read(others[-1])
        flag = next((k for k, v in a.variables.items() if isinstance(v, bool)), None)
        out = os.path.join(TMP, "real.save")
        renpysave.write_from(p, out, b.node, b.return_nodes, b.call_nodes,
                             {"vn3ds_test": "hi", **({flag: not a.variables[flag]} if flag else {})},
                             images=b.images, music=b.music, say=("who", "A line."), mtime=1.7e9)
        c = renpysave.read(out)
        check(c.node == b.node and c.images == b.images and c.music == b.music and
              c.variables.get("vn3ds_test") == "hi" and
              (not flag or c.variables[flag] == (not a.variables[flag])),
              "written with another position, pictures, music and variables, it reads back so")


def canon(o, seen=None, depth=0):
    """A comparable picture of a pickled object graph."""
    seen = seen if seen is not None else {}
    if depth > 60:
        return "..."
    if isinstance(o, renpysave.Stub):
        if id(o) in seen:
            return ("ref", seen[id(o)])
        seen[id(o)] = len(seen)
        return (type(o).__module__, type(o).__name__, o._rp_reduce, canon(o._rp_args, seen, depth + 1),
                canon(o._rp_state, seen, depth + 1), canon(o._rp_items, seen, depth + 1),
                canon(sorted(o._rp_dict.items(), key=repr), seen, depth + 1))
    if isinstance(o, dict):
        return ("d", tuple(sorted(((repr(k), canon(v, seen, depth + 1)) for k, v in o.items()),
                                  key=lambda kv: kv[0])))
    if isinstance(o, (list, tuple)):
        return (type(o).__name__, tuple(canon(x, seen, depth + 1) for x in o))
    if isinstance(o, (set, frozenset)):
        return ("s", tuple(sorted(repr(x) for x in o)))
    if isinstance(o, type):
        return ("type", o.__module__, o.__name__)
    return repr(o)


try:
    main()
finally:
    shutil.rmtree(TMP, ignore_errors=True)
print("all save sync tests passed" if not fail else "FAILED")
sys.exit(1 if fail else 0)

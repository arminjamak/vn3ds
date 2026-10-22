"""Saves on the Mac and on the 3DS, kept in step.

A game sent to the 3DS takes the player's Ren'Py saves with it, and from
then on a save made on either side appears on the other:

  Ren'Py (this Mac)                              vn3ds (the 3DS)
  ~/Library/RenPy/<save_directory>/1-1.save  <->  saves/<id>/slot01.sav
  (and the game's own game/saves/)               ...
  page P, slot S                             <->  slot (P-1)*6+S (1-30)
  auto-1 (the newest autosave)               <->  slot 0 (where Continue goes)

Each save is converted (renpysave.py, vn3dssave.py, savemap.py): the story
position (statement and call stack), the variables vn3ds keeps (numbers,
true/false, text), the pictures on screen and the music. A save that can't
be converted stays where it is and is listed with the reason.

Which side changed is decided against the last sync (sync/<id>.json): one
side changed, it is copied over; both changed, the newer wins and the other
is kept as a backup (on the Mac in sync/backups/<id>/, on the 3DS as
slotNN.sav.bak). A save deleted on one side is deleted on the other (also
kept as a backup), unless it changed there meanwhile.

When it happens: right after a game is sent (its existing saves go with
it); whenever vn3ds opens, a game is closed, vn3ds exits or a save is made
(the 3DS nudges the computer over UDP, engine/source/savesync.c); and every
POLL seconds while vn3ds is open. 3DS homebrew can't run while it's closed,
so saves made in between wait on the SD card; the agent (run_agent, started
at login by the Mac app's login item) takes them the next time vn3ds is open,
even briefly.

    python3 -m vnpack.savesync sync [--host IP | --sd PATH] [GAME_DIR...]
    python3 -m vnpack.savesync agent [--port 5556]
    python3 -m vnpack.savesync convert SAVE GAME_DIR [-o OUT]   (one save, either way)
"""

import argparse
import json
import os
import re
import shutil
import socket
import struct
import sys
import threading
import time

from . import detect, renpysave, vn3dssave
from .savemap import NAME as SAVEMAP, SaveMap

VN3DS_PORT = 5555
AGENT_PORT = 5556        # UDP: the 3DS's nudges
POLL = 20                # seconds between looks while vn3ds is open
SEARCH_EVERY = 600       # seconds between network searches when the 3DS isn't where it was
SLOTS_PER_PAGE = 6
MAX_SLOT = 30

REASONS = {1: "vn3ds opened", 2: "a save on the 3DS", 3: "a game was closed", 4: "vn3ds is closing"}


class Unconvertible(Exception):
    """A save that can't be carried over (the message says why)."""


NO_TEMPLATE = ("there's no Ren'Py save of this game on this Mac to build it on: save once "
               "in the game on the Mac (the 3DS's save is kept meanwhile)")


# --------------------------------------------------------------------------
# where things are
# --------------------------------------------------------------------------

def data_dir():
    from .port import user_data_dir
    d = os.environ.get("VN3DS_SYNC_DIR") or os.path.join(user_data_dir(), "sync")
    os.makedirs(d, exist_ok=True)
    return d


def renpy_home():
    """Where Ren'Py keeps saves for every game on this computer."""
    if os.environ.get("VN3DS_RENPY_HOME"):
        return os.environ["VN3DS_RENPY_HOME"]
    if sys.platform == "darwin":
        return os.path.expanduser("~/Library/RenPy")
    if os.name == "nt":
        return os.path.join(os.environ.get("APPDATA", ""), "RenPy")
    return os.path.expanduser("~/.renpy")


def renpy_dirs(smap):
    """Ren'Py's save folders for this game: its own under ~/Library/RenPy
    and the game's game/saves/ (Ren'Py writes to both and loads the newest)."""
    dirs = []
    if smap.save_directory:
        dirs.append(os.path.join(renpy_home(), smap.save_directory))
    src = smap.source
    # (not inside a Mac .app: Ren'Py doesn't save there, and the app's signature would break)
    if src and os.path.isdir(src) and os.path.basename(src.rstrip("/")) == "game" and \
            ".app/Contents/" not in src:
        dirs.append(os.path.join(src, "saves"))
    return dirs


def registry_path():
    return os.path.join(data_dir(), "games.json")


def load_registry():
    try:
        with open(registry_path(), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def register(game_dir):
    """Remembers a ported game for the agent (its folder holds savemap.json)."""
    if not os.path.exists(os.path.join(game_dir, SAVEMAP)):
        return False
    reg = load_registry()
    gid = os.path.basename(os.path.abspath(game_dir).rstrip("/"))
    reg[gid] = {"build": os.path.abspath(game_dir)}
    _write_json(registry_path(), reg)
    return True


def _write_json(path, obj):
    tmp = path + ".part"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1)
    os.replace(tmp, path)


# --------------------------------------------------------------------------
# slots
# --------------------------------------------------------------------------

def renpy_slot_to_vn3ds(name):
    m = re.match(r"^(\d+)-(\d+)$", name or "")
    if m:
        page, slot = int(m.group(1)), int(m.group(2))
        if 1 <= slot <= SLOTS_PER_PAGE and 1 <= page:
            n = (page - 1) * SLOTS_PER_PAGE + slot
            return n if n <= MAX_SLOT else None
        return None
    return 0 if name == "auto-1" else None


def vn3ds_slot_to_renpy(n):
    if n == 0:
        return "auto-1"
    return f"{(n - 1) // SLOTS_PER_PAGE + 1}-{(n - 1) % SLOTS_PER_PAGE + 1}"


def unmapped_reason(name):
    if name.startswith("quick-"):
        return "a quick save (vn3ds has no quick-save slot)"
    if name.startswith("auto-"):
        return "an older autosave (only the newest one goes to vn3ds's Continue)"
    m = re.match(r"^(\d+)-(\d+)$", name)
    if m:
        return (f"page {m.group(1)}, slot {m.group(2)} is past vn3ds's "
                f"{MAX_SLOT // SLOTS_PER_PAGE} pages of {SLOTS_PER_PAGE}")
    return "not a slot vn3ds has"


def renpy_saves(smap):
    """{renpy slot name: (path, mtime, size)}, the newest of each across
    Ren'Py's save folders."""
    out = {}
    for d in renpy_dirs(smap):
        try:
            names = os.listdir(d)
        except OSError:
            continue
        for fn in names:
            m = renpysave.SLOT_RE.match(fn)
            if not m:
                continue
            slot = f"{m.group(1)}-{m.group(2)}" if m.group(1) else f"{m.group(3)}-{m.group(4)}"
            p = os.path.join(d, fn)
            st = os.stat(p)
            if slot not in out or st.st_mtime > out[slot][1]:
                out[slot] = (p, st.st_mtime, st.st_size)
    return out


def _suffix(d):
    """Ren'Py 7.4+ on Python 2 names saves 1-1-LT1.save."""
    try:
        return "-LT1" if any(f.endswith("-LT1.save") for f in os.listdir(d)) else ""
    except OSError:
        return ""


# --------------------------------------------------------------------------
# converting
# --------------------------------------------------------------------------

def renpy_to_vn3ds(info, smap, ds_time):
    """vn3ds save bytes for a Ren'Py save (renpysave.SaveInfo). Returns
    (data, notes)."""
    notes = []
    if smap.stale:
        raise Unconvertible("the game was ported again; send it to the 3DS first")
    pc, exact = smap.node_pc(info.node)
    if pc is None:
        where = smap.nodes.get(info.node)
        raise Unconvertible(
            f"its place in the story ({where[0]}:{where[1]}) is in a part vn3ds leaves out"
            if where else "its place in the story isn't in the scripts this port was made from "
                          "(another version of the game?)")
    if not exact:
        notes.append("it starts at the nearest line vn3ds has")
    calls = []
    for i, call in enumerate(info.call_nodes):
        ret, _ = smap.node_pc(call, after=True)
        if ret is None and i < len(info.return_nodes):
            ret, _ = smap.node_pc(info.return_nodes[i])
        if ret is None:
            raise Unconvertible("it is inside a called label vn3ds can't return from")
        calls.append(ret)
    values, kept, dropped = [], 0, []
    for name in smap.vars:
        v = info.variables.get(name, vn3dssave.Default)
        if v is vn3dssave.Default or v is None or isinstance(v, (bool, int, float, str)):
            if v is not vn3dssave.Default:
                kept += 1
            values.append(v)
        else:
            values.append(vn3dssave.Default)
            dropped.append(name)
    if dropped:
        notes.append(f"{len(dropped)} variables vn3ds can't hold start at the game's defaults "
                     f"({', '.join(dropped[:3])}{'...' if len(dropped) > 3 else ''})")
    music = smap.music.get(info.music, -1) if info.music else -1
    if info.music and music < 0:
        notes.append("its music isn't in the vn3ds port")
    preview = f"{info.say_who}: {info.say_what}" if info.say_who else info.say_what
    data = vn3dssave.write(smap.crc, ds_time, preview.replace("\n", " "), pc, calls, values,
                           last_text=info.say_what, music=music, specs=info.images)
    return data, notes


def vn3ds_to_renpy(data, smap, template, out, mtime):
    """Writes a Ren'Py save for vn3ds save bytes, built on `template` (a
    Ren'Py save of the game). Returns notes."""
    s = vn3dssave.read(data)
    if s["crc"] != smap.crc:
        raise Unconvertible("it was made with another port of the game")
    at = smap.statement_at(s["pc"])
    node = smap.node_at(at[0], at[1], kinds={"Say", "Menu", "UserStatement"}) if at else None
    if node is None:
        raise Unconvertible("its place in the story has no statement Ren'Py knows "
                            "(the game's .rpyc files couldn't be read)")
    call_nodes, return_nodes = [], []
    for ret in s["calls"]:
        c = smap.statement_ending(ret)
        call = smap.node_at(c[0], c[1], kinds={"Call"}) if c else None
        nxt = smap.next.get(call) if call else None
        if not nxt:
            raise Unconvertible("it is inside a called label Ren'Py couldn't return from")
        call_nodes.append(call)
        return_nodes.append(nxt)
    variables = {name: v for name, v in zip(smap.vars, s["vars"]) if v is not vn3dssave.Default}
    who, _, what = s["preview"].partition(": ") if ": " in s["preview"] else ("", "", s["preview"])
    notes = renpysave.write_from(
        template, out, node, return_nodes, call_nodes, variables,
        images=s["specs"], music=smap.music_name.get(s["music"]) if s["music"] >= 0 else None,
        say=(who, s["last_text"] or what), mtime=mtime, extra_info=s["preview"][:80])
    return notes


def template_for(mac, prefer=None):
    """The Ren'Py save to build a converted one on: the slot's own, else the
    newest. Writing over a template keeps a copy of it, so this is safe."""
    if prefer and prefer in mac:
        return mac[prefer][0]
    best = max(mac.values(), key=lambda v: v[1], default=None)
    return best[0] if best else None


# --------------------------------------------------------------------------
# the 3DS end: over Wi-Fi ("VN3S", engine/source/savesync.c) or a folder
# --------------------------------------------------------------------------

class LinkError(OSError):
    pass


class WifiLink:
    def __init__(self, host, port=VN3DS_PORT, agent_port=AGENT_PORT, timeout=12):
        self.host = host
        self.sock = socket.create_connection((host, port), timeout=timeout)
        self.sock.settimeout(timeout)
        self.sock.sendall(b"VN3S" + struct.pack("<IIQ", 1, agent_port, 0))
        head = self._recv(16)
        if head[:4] != b"VN3S":
            raise LinkError("vn3ds didn't answer the save sync (update vn3ds?)")
        _, self.now, count = struct.unpack_from("<III", head, 4)
        self.saves = {}
        for _ in range(count):
            n = struct.unpack("<H", self._recv(2))[0]
            path = self._recv(n).decode("utf-8", "replace")
            size, t = struct.unpack("<II", self._recv(8))
            self.saves[path] = (t, size)
        self.offset = self.now - time.time()

    def _recv(self, n):
        b = bytearray()
        while len(b) < n:
            chunk = self.sock.recv(n - len(b))
            if not chunk:
                raise LinkError("the 3DS closed the connection")
            b += chunk
        return bytes(b)

    def _path(self, cmd, path):
        p = path.encode("utf-8")
        self.sock.sendall(cmd + struct.pack("<H", len(p)) + p)

    def get(self, path):
        self._path(b"G", path)
        n = struct.unpack("<I", self._recv(4))[0]
        return None if n == 0xFFFFFFFF else self._recv(n)

    def put(self, path, data):
        p = path.encode("utf-8")
        self.sock.sendall(b"P" + struct.pack("<H", len(p)) + p + struct.pack("<I", len(data)) + data)
        if self._recv(1) != b"\0":
            raise LinkError(f"the 3DS couldn't write {path}")

    def delete(self, path):
        self._path(b"D", path)
        self._recv(1)

    def close(self):
        try:
            self.sock.sendall(b"Q")
            self._recv(4)
        except OSError:
            pass
        self.sock.close()


class FolderLink:
    """The 3DS's SD card in this computer (or a test's vn3ds root)."""

    def __init__(self, root):
        self.root = root
        self.host = None
        # the 3DS clock is local time counted as if it were UTC
        self.offset = -time.timezone if not time.localtime().tm_isdst else -time.altzone
        self.now = time.time() + self.offset
        self.saves = {}
        base = os.path.join(root, "saves")
        for gid in (os.listdir(base) if os.path.isdir(base) else []):
            for slot in range(MAX_SLOT + 1):
                rel = f"saves/{gid}/slot{slot:02d}.sav"
                p = os.path.join(root, rel)
                if os.path.exists(p):
                    with open(p, "rb") as f:
                        head = vn3dssave.peek(f.read(16 + vn3dssave.PREVIEW))
                    self.saves[rel] = (head[0] if head else 0, os.path.getsize(p))

    def get(self, path):
        try:
            with open(os.path.join(self.root, path), "rb") as f:
                return f.read()
        except OSError:
            return None

    def put(self, path, data):
        p = os.path.join(self.root, path)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        if os.path.exists(p):
            os.replace(p, p + ".bak")
        with open(p + ".part", "wb") as f:
            f.write(data)
        os.replace(p + ".part", p)

    def delete(self, path):
        p = os.path.join(self.root, path)
        if os.path.exists(p):
            os.replace(p, p + ".bak")

    def close(self):
        pass


# --------------------------------------------------------------------------
# syncing one game
# --------------------------------------------------------------------------

class Report:
    def __init__(self, say=None):
        self.say = say or (lambda text: None)
        self.to_3ds, self.to_mac, self.deleted, self.kept_back, self.notes = [], [], [], [], []

    def add(self, kind, slot, detail=""):
        getattr(self, kind).append((slot, detail))
        self.say(_describe(kind, slot, detail))

    def summary(self):
        parts = []
        if self.to_3ds:
            parts.append(f"{len(self.to_3ds)} to the 3DS")
        if self.to_mac:
            parts.append(f"{len(self.to_mac)} to this Mac")
        if self.deleted:
            parts.append(f"{len(self.deleted)} deleted")
        if self.kept_back:
            parts.append(f"{len(self.kept_back)} couldn't be carried over")
        return ", ".join(parts) or "already in sync"

    def as_dict(self):
        return {k: [list(x) for x in getattr(self, k)]
                for k in ("to_3ds", "to_mac", "deleted", "kept_back", "notes")}


def _describe(kind, slot, detail):
    what = {"to_3ds": "-> 3DS", "to_mac": "-> Mac", "deleted": "deleted",
            "kept_back": "not carried over", "notes": "note"}[kind]
    return f"{slot_name(slot)}: {what}" + (f" ({detail})" if detail else "")


def slot_name(slot):
    if isinstance(slot, int):
        return "Continue (autosave)" if slot == 0 else \
            f"slot {slot} (page {(slot - 1) // SLOTS_PER_PAGE + 1})"
    return f"Ren'Py {slot}"


def _backup(gid, path, why):
    d = os.path.join(data_dir(), "backups", gid)
    os.makedirs(d, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    dest = os.path.join(d, f"{stamp}-{why}-{os.path.basename(path)}")
    shutil.copy2(path, dest)
    return dest


def sync_game(link, smap, report, initial=False):
    """Brings one game's saves in step between link (the 3DS) and this Mac."""
    gid = smap.id
    state_path = os.path.join(data_dir(), f"{gid}.json")
    try:
        with open(state_path, encoding="utf-8") as f:
            state = json.load(f)
    except (OSError, ValueError):
        state = {}
    slots = state.setdefault("slots", {})
    mac_all = renpy_saves(smap)
    mac = {}
    for name, v in mac_all.items():
        n = renpy_slot_to_vn3ds(name)
        if n is None:
            told = state.setdefault("unmapped_told", [])
            if initial or name not in told:
                report.add("kept_back", name, unmapped_reason(name))
                if name not in told:
                    told.append(name)
            continue
        mac[n] = (name,) + v
    ds = {}
    for path, (t, size) in link.saves.items():
        m = re.match(rf"^saves/{re.escape(gid)}/slot(\d\d)\.sav$", path)
        if m:
            ds[int(m.group(1))] = (path, t, size)
    write_dirs = [d for d in renpy_dirs(smap) if os.path.isdir(d)] or renpy_dirs(smap)[:1]
    mirror = os.path.join(data_dir(), gid, "3ds")

    def push(n):
        name, path, mtime, size = mac[n]
        info = renpysave.read(path)
        data, notes = renpy_to_vn3ds(info, smap, mtime + link.offset)
        link.put(f"saves/{gid}/slot{n:02d}.sav", data)
        slots[str(n)] = {"ds": [int(mtime + link.offset) & 0xFFFFFFFF, len(data)],
                         "mac": [mtime, size]}
        report.add("to_3ds", n, "; ".join(notes))

    def pull(n):
        path, t, size = ds[n]
        data = link.get(path)
        if data is None:
            raise Unconvertible("the 3DS couldn't read it")
        os.makedirs(mirror, exist_ok=True)   # the 3DS's save as it was, always kept
        with open(os.path.join(mirror, f"slot{n:02d}.sav"), "wb") as f:
            f.write(data)
        name = vn3ds_slot_to_renpy(n)
        mtime = t - link.offset
        template = template_for(mac_all, prefer=name)
        if template is None:
            raise Unconvertible(NO_TEMPLATE)
        held = os.path.join(data_dir(), f".{gid}-template.save")
        shutil.copy2(template, held)   # (the template may be the file being replaced)
        template = held
        if n in mac:
            _backup(gid, mac[n][1], "replaced")
        notes, written = [], None
        for d in write_dirs:
            os.makedirs(d, exist_ok=True)
            out = os.path.join(d, name + _suffix(d) + ".save")
            stage = os.path.join(data_dir(), f".{gid}-{n}.save")
            notes = vn3ds_to_renpy(data, smap, template, stage, mtime)
            for old in (os.path.join(d, name + sfx + ".save") for sfx in ("", "-LT1")):
                if old != out and os.path.exists(old):
                    os.remove(old)
            os.replace(stage, out)
            written = out
        st = os.stat(written)
        slots[str(n)] = {"ds": [t, size], "mac": [st.st_mtime, st.st_size]}
        report.add("to_mac", n, "; ".join(notes))

    for n in sorted(set(mac) | set(ds)):
        prev = slots.get(str(n))
        if prev and prev.get("why") == NO_TEMPLATE and mac_all:
            prev = None   # it can be built now
        m_now = [mac[n][2], mac[n][3]] if n in mac else None
        d_now = [ds[n][1], ds[n][2]] if n in ds else None
        m_changed = m_now is not None and (prev is None or not _same(prev.get("mac"), m_now))
        d_changed = d_now is not None and (prev is None or prev.get("ds") != d_now)
        try:
            if m_now and d_now:
                if m_changed and d_changed:   # both: the newer wins
                    if mac[n][2] >= ds[n][1] - link.offset:
                        push(n)
                    else:
                        pull(n)
                elif m_changed:
                    push(n)
                elif d_changed:
                    pull(n)
            elif m_now:
                if prev and prev.get("ds") and not m_changed:   # deleted on the 3DS
                    _backup(gid, mac[n][1], "deleted-on-3ds")
                    for d in renpy_dirs(smap):
                        p = os.path.join(d, os.path.basename(mac[n][1]))
                        if os.path.exists(p):
                            os.remove(p)
                    slots.pop(str(n), None)
                    report.add("deleted", n, "deleted on the 3DS")
                elif m_changed:
                    push(n)
            elif d_now:
                if prev and prev.get("mac") and not d_changed:   # deleted on the Mac
                    link.delete(ds[n][0])
                    slots.pop(str(n), None)
                    report.add("deleted", n, "deleted on this Mac (kept on the 3DS as a .bak)")
                elif d_changed:
                    pull(n)
        except (Unconvertible, vn3dssave.SaveError, ValueError, KeyError, EOFError,
                AttributeError, TypeError, IndexError) as e:
            # a save that can't go across: keep both as they are, say why once
            why = str(e) if isinstance(e, Unconvertible) else f"it couldn't be read ({e})"
            if (prev or {}).get("why") != why or initial:
                report.add("kept_back", n, why)
            slots[str(n)] = {"ds": d_now or (prev or {}).get("ds"),
                             "mac": m_now or (prev or {}).get("mac"), "why": why}
    _write_json(state_path, state)


def _same(a, b):
    return a is not None and abs(a[0] - b[0]) < 1 and a[1] == b[1]


def game_maps(game_dirs=None):
    """SaveMaps of the given ported games, or of every registered one."""
    dirs = list(game_dirs or [])
    if not dirs:
        dirs = [v["build"] for v in load_registry().values()]
    out = []
    for d in dirs:
        try:
            out.append(SaveMap(d))
        except (OSError, ValueError, KeyError):
            continue
    return out


def sync(link, maps, say=None, initial=False):
    """Every game: {id: Report}."""
    out = {}
    for smap in maps:
        r = Report(say)
        try:
            sync_game(link, smap, r, initial=initial)
        except (OSError, LinkError) as e:
            r.add("notes", "-", f"stopped: {e}")
            out[smap.id] = r
            raise
        out[smap.id] = r
    return out


# --------------------------------------------------------------------------
# the agent: in the background, at login
# --------------------------------------------------------------------------

def status_path():
    return os.path.join(data_dir(), "status.json")


def _status(**kw):
    try:
        with open(status_path(), encoding="utf-8") as f:
            st = json.load(f)
    except (OSError, ValueError):
        st = {}
    st.update(kw)
    _write_json(status_path(), st)


def sync_once(host, maps, say=print, initial=False, agent_port=AGENT_PORT):
    link = WifiLink(host, agent_port=agent_port)
    try:
        reports = sync(link, maps, say=say, initial=initial)
    finally:
        link.close()
    _status(last_sync=time.time(), host=host,
            games={gid: dict(summary=r.summary(), **r.as_dict()) for gid, r in reports.items()})
    return reports


def run_agent(port=AGENT_PORT, host=None, poll=POLL, say=print, stop=None):
    """Waits for vn3ds on the Wi-Fi and syncs every registered game whenever
    it is there: when nudged (the 3DS says it opened, saved, closed a game
    or is exiting) and every `poll` seconds while it answers."""
    nudged = threading.Event()
    nudge = {}

    def listen():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("", port))
        while not (stop and stop()):
            s.settimeout(1.0)
            try:
                data, (ip, _) = s.recvfrom(128)
            except socket.timeout:
                continue
            if data[:4] == b"VN3N":
                reason = struct.unpack_from("<I", data, 4)[0]
                nudge.update(ip=ip, reason=reason)
                nudged.set()
    threading.Thread(target=listen, daemon=True).start()
    host = host or _last_host()
    last_search = 0.0
    say(f"vn3ds save sync: waiting for the 3DS (UDP {port})")
    _status(agent=os.getpid(), agent_started=time.time())
    while not (stop and stop()):
        woke = nudged.wait(poll)
        if woke:
            nudged.clear()
            host = nudge.get("ip") or host
            say(f"nudge from {host}: {REASONS.get(nudge.get('reason'), 'sync')}")
            time.sleep(1.0)   # (the save it just made is still being written)
        if not host or not detect.listening(host, VN3DS_PORT, timeout=1.5):
            # where else it might be: Nintendo network cards this Mac has seen
            # (no packets), then now and then the whole network
            found = [ip for ip in detect.nintendo_hosts() if ip != host and
                     detect.listening(ip, VN3DS_PORT, timeout=1.0)]
            if not found and (woke or time.time() - last_search >= SEARCH_EVERY):
                last_search = time.time()
                found = detect.scan_lan(ports=(VN3DS_PORT,)).get(VN3DS_PORT) or []
            if not found:
                continue
            host = found[0]
        maps = game_maps()
        if not maps:
            continue
        try:
            reports = sync_once(host, maps, say=say, agent_port=port)
            changed = sum(len(r.to_3ds) + len(r.to_mac) + len(r.deleted) for r in reports.values())
            if changed:
                say(f"synced with {host}: " + "; ".join(f"{g}: {r.summary()}"
                                                       for g, r in reports.items()))
        except (OSError, LinkError) as e:
            say(f"sync with {host} stopped: {e}")


def _last_host():
    try:
        with open(status_path(), encoding="utf-8") as f:
            return json.load(f).get("host")
    except (OSError, ValueError):
        return None


# --------------------------------------------------------------------------
# after a game is sent
# --------------------------------------------------------------------------

def after_delivery(game_dirs, kind, where, ui, later=False):
    """The player's Ren'Py saves go with a game that was just delivered
    (later=True: vn3ds was updated with it and the running one can't sync
    yet; the agent or the next send takes them)."""
    maps = []
    for d in game_dirs:
        if register(d):
            maps += game_maps([d])
    if not maps:
        return None
    if later:
        ui.step("saves", "skip", "your saves go once vn3ds is restarted (it was just updated)",
                label="Saves")
        return None
    ui.step("saves", "active", "looking for your saves", label="Saves")
    try:
        if kind == "sd":
            link = FolderLink(os.path.join(where, "3ds", "vn3ds"))
        else:
            ip = where.split(":")[0]
            if not detect.listening(ip, VN3DS_PORT):   # (it moved during the transfer)
                found, at = detect.locate(ip)
                ip = at if found == "vn3ds" else ip
            link = WifiLink(ip)
        try:
            reports = sync(link, maps, say=ui.log, initial=True)
        finally:
            link.close()
    except (OSError, LinkError) as e:
        ui.step("saves", "fail", f"saves weren't sent ({e}); they go at the next sync",
                label="Saves")
        return None
    r = next(iter(reports.values())) if len(reports) == 1 else None
    total = sum(len(x.to_3ds) for x in reports.values())
    back = [(slot_name(s), why) for x in reports.values() for s, why in x.kept_back]
    detail = (f"{total} save{'s' if total != 1 else ''} sent" if total else
              "no Ren'Py saves of this game on this Mac" if not back else "none could be sent")
    if back:
        detail += f"; {len(back)} couldn't be"
    ui.step("saves", "done", detail, label="Saves")
    _status(host=where.split(":")[0] if kind != "sd" else _last_host())
    return dict(sent=total, kept_back=back, reports={g: x.as_dict() for g, x in reports.items()},
                summary=r.summary() if r else None)


# --------------------------------------------------------------------------
# the command line
# --------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(prog="vnpack.savesync", description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sync", help="sync saves once")
    s.add_argument("--host", help="the 3DS's IP (default: where it was last, else search)")
    s.add_argument("--sd", help="a 3DS SD card (or a vn3ds root folder) instead of Wi-Fi")
    s.add_argument("--port", type=int, default=VN3DS_PORT)
    s.add_argument("games", nargs="*", help="ported game folders (default: every one sent)")
    a = sub.add_parser("agent", help="keep saves in sync in the background")
    a.add_argument("--port", type=int, default=AGENT_PORT)
    a.add_argument("--host")
    a.add_argument("--poll", type=float, default=POLL)
    c = sub.add_parser("convert", help="convert one save (Ren'Py <-> vn3ds)")
    c.add_argument("save")
    c.add_argument("game", help="the ported game folder (with savemap.json)")
    c.add_argument("-o", "--output")
    c.add_argument("--template", help="a Ren'Py save to build on (vn3ds -> Ren'Py)")
    args = ap.parse_args(argv)
    if args.cmd == "agent":
        run_agent(args.port, args.host, args.poll)
        return
    if args.cmd == "convert":
        smap = SaveMap(args.game)
        if args.save.endswith(".sav"):
            out = args.output or os.path.splitext(args.save)[0] + ".save"
            tmpl = args.template or template_for(renpy_saves(smap))
            if not tmpl:
                sys.exit("give --template: a Ren'Py save of this game to build on")
            data = open(args.save, "rb").read()
            notes = vn3ds_to_renpy(data, smap, tmpl, out, os.path.getmtime(args.save))
        else:
            info = renpysave.read(args.save)
            data, notes = renpy_to_vn3ds(info, smap, info.mtime)
            out = args.output or os.path.splitext(args.save)[0] + ".sav"
            with open(out, "wb") as f:
                f.write(data)
        print(f"wrote {out}" + "".join(f"\n  {n}" for n in notes))
        return
    for g in args.games:
        register(g)
    maps = game_maps(args.games)
    if not maps:
        sys.exit("no ported games with a savemap.json (port the game again to sync its saves)")
    if args.sd:
        link = FolderLink(args.sd if os.path.isdir(os.path.join(args.sd, "saves"))
                          else os.path.join(args.sd, "3ds", "vn3ds"))
    else:
        host = args.host or _last_host()
        if not host or not detect.listening(host, args.port):
            kind, host = detect.locate(host)
            if kind != "vn3ds":
                sys.exit("vn3ds isn't open on the 3DS (or the 3DS isn't on the Wi-Fi)")
        link = WifiLink(host, args.port)
    try:
        reports = sync(link, maps, say=lambda t: print("  " + t))
    finally:
        link.close()
    for gid, r in reports.items():
        print(f"{gid}: {r.summary()}")


if __name__ == "__main__":
    main()

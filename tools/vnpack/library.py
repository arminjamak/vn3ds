"""Ren'Py games installed on this computer, for the Mac app's list.

Looks in /Applications and ~/Applications (Ren'Py's Mac builds keep the game
in X.app/Contents/Resources/autorun/game/), the usual download folders and
Steam's library. A folder counts as a Ren'Py game when it has a game/ folder
with scripts or archives in it and Ren'Py itself (renpy/) or a Mac app
layout next to it.

    games = find()          # [Game(path, game_dir, title, size, saves, where, cover)]
    cover(game)             # a small PNG of its menu art or icon (cached), or None
"""

import hashlib
import io
import os
import re
import sys
import threading
import time
import zlib
from collections import namedtuple

GAME_EXTS = (".rpy", ".rpyc", ".rpa")
SKIP = {"renpy", "lib", "__pycache__", "cache", "saves", "node_modules", ".git", "Library",
        "Photos Library.photoslibrary", "Music", "Movies", "Pictures"}

Game = namedtuple("Game", "path game_dir title version size saves save_directory where cover")


def home(*p):
    return os.path.join(os.path.expanduser("~"), *p)


def search_roots():
    """[(folder, how deep to look, label)]"""
    extra = [p for p in os.environ.get("VN3DS_LIBRARY_DIRS", "").split(os.pathsep) if p]
    if extra:   # (tests)
        return [(p, 3, "folder") for p in extra]
    roots = [("/Applications", 2, "Applications"), (home("Applications"), 2, "Applications"),
             (home("Downloads"), 3, "Downloads"), (home("Desktop"), 2, "Desktop"),
             (home("Documents"), 2, "Documents"), (home("Games"), 3, "Games"),
             (home("Library", "Application Support", "Steam", "steamapps", "common"), 3, "Steam")]
    if sys.platform.startswith("win"):
        roots += [(os.path.join(os.environ.get("ProgramFiles(x86)", ""), "Steam", "steamapps",
                                "common"), 3, "Steam")]
    elif not sys.platform == "darwin":
        roots += [(home(".local", "share", "Steam", "steamapps", "common"), 3, "Steam")]
    return roots


def _has_game_files(d):
    try:
        return any(f.lower().endswith(GAME_EXTS) for f in os.listdir(d))
    except OSError:
        return False


def game_dir_of(path):
    """The game/ folder if `path` is a Ren'Py game (folder or .app), else None."""
    if path.endswith(".app"):
        g = os.path.join(path, "Contents", "Resources", "autorun", "game")
        return g if _has_game_files(g) else None
    g = os.path.join(path, "game")
    if not os.path.isdir(g) or not _has_game_files(g):
        return None
    try:
        names = set(os.listdir(path))
    except OSError:
        return None
    # Ren'Py itself beside it: a build (renpy/, lib/, the launch scripts) or a project
    if "renpy" in names or "lib" in names or any(n.endswith((".sh", ".exe", ".py")) for n in names):
        return g
    return None


def _walk(root, depth, deadline=None):
    if deadline and time.monotonic() > deadline:
        return   # (an iCloud-synced folder can take minutes to list in full)
    try:
        entries = sorted(os.scandir(root), key=lambda e: e.name.lower())
    except OSError:
        return
    for e in entries:
        if e.name.startswith(".") or e.name in SKIP:
            continue
        try:
            is_dir = e.is_dir(follow_symlinks=False)
        except OSError:
            continue
        if not is_dir:
            continue
        g = game_dir_of(e.path)
        if g:
            yield e.path, g
        elif depth > 1 and not e.name.endswith(".app"):
            yield from _walk(e.path, depth - 1, deadline)


def _size(path):
    total = 0
    for root, _, files in os.walk(path):
        for f in files:
            try:
                total += os.lstat(os.path.join(root, f)).st_size
            except OSError:
                pass
    return total


SAVE_DIR_RE = re.compile(rb"""save_directory\s*=\s*u?r?["']([^"'\\\n]{1,120})["']""")
NAME_RE = re.compile(r"""config\.name\s*=\s*_?\(?\s*u?["']([^"'\n]{1,120})["']""")
VERSION_RE = re.compile(r"""config\.version\s*=\s*u?["']([^"'\n]{1,40})["']""")


def _about(game_dir):
    """(title, version, save_directory) from options.rpy / options.rpyc."""
    title = version = save_dir = None
    for name in ("options.rpy", "options.rpyc"):
        p = os.path.join(game_dir, name)
        if not os.path.exists(p):
            continue
        try:
            raw = open(p, "rb").read()
        except OSError:
            continue
        if name.endswith(".rpyc"):
            raw = _rpyc_text(raw)
        m = SAVE_DIR_RE.search(raw)
        save_dir = save_dir or (m and m.group(1).decode("utf-8", "replace"))
        text = raw.decode("utf-8", "replace")
        m = NAME_RE.search(text)
        title = title or (m and m.group(1))
        m = VERSION_RE.search(text)
        version = version or (m and m.group(1))
        if not save_dir and name.endswith(".rpyc"):
            # `define config.save_directory = "X"`: the name and the value are
            # apart in the compiled script
            i = raw.find(b"save_directory")
            m = re.search(rb"""["']([A-Za-z0-9 _.\-]{3,80}-\d{6,})["']""", raw[i:i + 600]) \
                if i >= 0 else None
            save_dir = m and m.group(1).decode()
    return title, version, save_dir


def _rpyc_text(raw):
    try:
        if raw.startswith(b"RENPY RPC2"):
            import struct
            slot, start, length = struct.unpack_from("<III", raw, 10)
            return zlib.decompress(raw[start:start + length])
        return zlib.decompress(raw)
    except (zlib.error, ValueError):
        return b""


def renpy_home():
    from .savesync import renpy_home as h
    return h()


def _count_saves(game_dir, save_dir):
    n = 0
    for d in ([os.path.join(renpy_home(), save_dir)] if save_dir else []) + \
             [os.path.join(game_dir, "saves")]:
        try:
            n = max(n, sum(1 for f in os.listdir(d) if f.endswith(".save")))
        except OSError:
            pass
    return n


def _guess_save_dir(title, game_dir):
    """Ren'Py's folder for a game whose options we couldn't read: the one
    named after it (save directories are "<Name>-<number>")."""
    try:
        dirs = os.listdir(renpy_home())
    except OSError:
        return None
    key = re.sub(r"[^a-z0-9]", "", (title or "").lower())
    for d in dirs:
        base = re.sub(r"-\d+$", "", d)
        if key and re.sub(r"[^a-z0-9]", "", base.lower()) == key:
            return d
    return None


def _title_from_path(path):
    name = os.path.basename(path.rstrip("/"))
    name = re.sub(r"\.app$", "", name)
    name = re.sub(r"[-_ ](v?\d+(\.\d+)+[a-z]?)?[-_ ]?(pc|mac|market|linux|win|all)?$", "", name,
                  flags=re.I) or name
    return name.replace("_", " ").strip()


def find(say=None, budget=10.0):
    """Every installed game; each folder is searched for at most `budget`
    seconds (all at once), so a huge or cloud-synced one can't hold the
    list up."""
    roots = [r for r in search_roots() if os.path.isdir(r[0])]
    found = [[] for _ in roots]
    deadline = time.monotonic() + budget

    def search(i, root, depth, label):
        for path, gd in _walk(root, depth, deadline):
            found[i].append((path, gd, label))
    threads = [threading.Thread(target=search, args=(i,) + r, daemon=True)
               for i, r in enumerate(roots)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(budget + 2)
    seen, out = set(), []
    for path, gd, label in (x for f in found for x in list(f)):
        real = os.path.realpath(path)
        if real in seen:
            continue
        seen.add(real)
        title, version, save_dir = _about(gd)
        title = title or _title_from_path(path)
        save_dir = save_dir or _guess_save_dir(title, gd)
        g = Game(path=path, game_dir=gd, title=title, version=version, size=_size(path),
                 saves=_count_saves(gd, save_dir), save_directory=save_dir, where=label,
                 cover=None)
        out.append(g)
        if say:
            say(g)
    return out


# --------------------------------------------------------------------------
# covers
# --------------------------------------------------------------------------

COVER_NAMES = ("gui/main_menu.png", "gui/main_menu.jpg", "gui/main_menu.webp",
               "images/main_menu.png", "gui/game_menu.png", "gui/window_icon.png")


def cover(game, cache_dir):
    """A small PNG of the game's main menu art (else its window icon),
    cached by path. None if there is none (the app shows the .app's icon)."""
    os.makedirs(cache_dir, exist_ok=True)
    key = hashlib.sha1(os.path.realpath(game.path).encode()).hexdigest()[:16]
    out = os.path.join(cache_dir, key + ".png")
    if os.path.exists(out):
        return out
    try:
        from PIL import Image
        from .assets import AssetFS
    except ImportError:
        return None
    data = None
    for n in COVER_NAMES:   # loose first: no archive to open
        p = os.path.join(game.game_dir, n)
        if os.path.exists(p):
            data = open(p, "rb").read()
            break
    if data is None:
        try:
            fs = AssetFS(game.game_dir, lambda *a: None)
            for n in COVER_NAMES:
                k = fs.find(n, dirs=("",))
                if k:
                    data = fs.read(k)
                    break
        except Exception:
            data = None
    if data is None:
        return None
    try:
        img = Image.open(io.BytesIO(data)).convert("RGB")
        img.thumbnail((400, 400))
        img.save(out + ".part", "PNG")
        os.replace(out + ".part", out)
        return out
    except Exception:
        return None

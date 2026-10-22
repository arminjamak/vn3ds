"""Free roam, talk menus, the game's own functions, sets and dicts, label
arguments and computed jumps (tools/vnpack/freeroam.py, pyinline.py,
compiler.py; JMP_NAME and the collection builtins in engine/source/vm.c).

    python3 tests/test_freeroam.py

Builds a small game the way point-and-click Ren'Py games are written (a
ROOMS / HOTSPOTS table drawn by one screen, a talk screen fed by a topics
table, story beats picked by a function over a table of objects, `jump
expression`), converts it with an adapter in its vn3ds.json and plays it in
the desktop build, checking the menus and where the story goes.
"""

import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOST = os.path.join(ROOT, "engine", "build-host", "vn3ds-host")
failed = False

SCRIPT = '''
init python:
    SLOTS = ("day", "night")
    NAV = ("bedroom", "kitchen")
    ROOMS = {
        "bedroom": {"bg": {s: "bedroom" for s in SLOTS}},
        "kitchen": {"bg": {"day": "kitchen", "night": "kitchen"}},
    }

    def late():
        """The fridge is open from day 2."""
        return store.day >= 2

    HOTSPOTS = {
        "bedroom": [dict(slots=SLOTS, label="sleep_{slot}", tip="sleep")],
        "kitchen": [dict(slots=("day",), label="cook", tip="cook"),
                    dict(slots=("night",), label="snack", tip="snack", cond=late)],
    }
    TIPS = {"sleep": (_("Bed"), _("Go to bed")), "cook": (_("Stove"), _("Cook dinner")),
            "snack": (_("Fridge"), _("Late snack"))}
    ROOM_TIP = {"bedroom": (_("Bedroom"), _("Go to the bedroom")),
                "kitchen": (_("Kitchen"), _("Go to the kitchen"))}

    class Beat(object):
        def __init__(self, day, label, quiet=False):
            self.day = day
            self.label = label
            self.quiet = quiet

    BEATS = [Beat(1, "beat_one"), Beat(2, "beat_two"), Beat(3, "beat_three", quiet=True)]

    def ready_beat():
        for b in BEATS:
            if b.day == store.day and not b.quiet:
                return b.label
        return None

    def buttons(rid, slot):
        return [("chat", _("Talk"), None, ("page", "chat")), ("back", _("Leave"), None, ("room", rid))]

    TOPICS = {"chat_day": ((_("Say hi"), "hi", lambda: day >= 1),
                           (_("Tell a secret"), "secret", lambda: day >= 5))}

    EVENTS = {"cake": ((("joy", 10),), _("We baked a cake.")),
              "walk": ((("joy", 5),), _("We went for a walk."))}

    def first_time(eid):
        return eid not in store.seen_events

    def done_today(eid):
        return store.event_last_day.get(eid) == store.day

    def mark_seen(eid):
        store.seen_events.add(eid)

    def event_done(eid):
        """Seen, and done for today."""
        mark_seen(eid)
        store.event_last_day[eid] = store.day

define STAT_NAME = {"joy": "Joy", "calm": "Calm"}

screen room(rid):
    text "rooms"

screen talk(rid, slot):
    text "talk"

screen kitchen_now():
    use room("kitchen")

image bedroom = "#334455"
image kitchen = "#554433"

default time_of_day = "day"
default current_room = "bedroom"
default day = 1
default joy = 0
default seen_events = set()
default event_last_day = {}
default event = None

label gain(stat, amount, message=True):
    $ setattr(store, stat, getattr(store, stat) + amount)
    if message:
        $ gain_name = STAT_NAME[stat]
        "[gain_name] up by [amount], now [joy]."
    return

label do_event(eid):
    if done_today(eid):
        "Not again today."
        return
    if first_time(eid):
        $ event = EVENTS[eid][1]
        "[event]"
        call gain("joy", 10)
    else:
        "Seen it, a little joy."
        call gain("joy", 2, message=False)
    $ event_done(eid)
    return

label start:
    "Morning."
    $ next_beat = ready_beat()
    jump expression next_beat

label beat_one:
    "Beat one."
    call screen room(current_room)

label sleep_day:
    $ time_of_day = "night"
    "Night falls."
    call screen kitchen_now

label sleep_night:
    $ day += 1
    $ time_of_day = "day"
    "Day [day]."
    $ next_beat = ready_beat()
    if next_beat:
        jump expression next_beat
    call screen room(current_room)

label beat_two:
    "Beat two."
    call screen talk("kitchen", "day")

label cook:
    "Cooking."
    call do_event("cake")
    call do_event("cake")
    $ day += 1
    call do_event("cake")
    $ n_seen = len(seen_events)
    "Joy [joy], [n_seen] seen."
    call screen room(current_room)

label snack:
    "Snack."
    return

label hi:
    "Hi."
    return

label secret:
    "Secret."
    return
'''

ADAPTER = {
    "room": {"mechanic": "free_roam", "rooms": "ROOMS", "hotspots": "HOTSPOTS",
             "nav_order": "NAV", "slots": "SLOTS", "time": "time_of_day",
             "room": "current_room", "background": "{bg}", "room_tips": "ROOM_TIP",
             "hotspot_tips": "TIPS"},
    "talk": {"mechanic": "topics", "buttons": "buttons", "topics": "TOPICS",
             "key": "{page}_{slot}"},
}


def check(ok, msg):
    global failed
    print(("  ok: " if ok else "  FAIL: ") + msg)
    failed |= not ok


def main():
    tmp = tempfile.mkdtemp(prefix="vn3ds-freeroam-")
    game = os.path.join(tmp, "roam", "game")
    os.makedirs(game)
    with open(os.path.join(game, "script.rpy"), "w") as f:
        f.write(SCRIPT)
    with open(os.path.join(game, "vn3ds.json"), "w") as f:
        json.dump({"minigames": ADAPTER}, f)
    env = dict(os.environ, PYTHONPATH=os.path.join(ROOT, "tools"))
    r = subprocess.run([sys.executable, "-m", "vnpack", os.path.dirname(game), "-o",
                        os.path.join(tmp, "out"), "-q"], capture_output=True, text=True, env=env)
    out = os.path.join(tmp, "out", "roam")
    check(r.returncode == 0 and os.path.exists(os.path.join(out, "game.bin")),
          "converts" + ("" if r.returncode == 0 else ": " + (r.stderr or r.stdout)[-400:]))
    if failed:
        sys.exit(1)
    # bed at day, then at night the kitchen (no snack yet), back to the bedroom,
    # bed; day 2 starts beat two and its talk menu: Talk, then Say hi
    choices = "0,0,1,0,0,0"
    p = subprocess.run([HOST, out, "--root", os.path.join(tmp, "root"), "--sdmc",
                        os.path.join(tmp, "sd"), "--choices", choices],
                       capture_output=True, text=True, timeout=120)
    lines = [l for l in p.stdout.splitlines() if not l.lstrip().startswith("[")]
    text = "\n".join(lines)
    said = [l for l in lines if not l.startswith((" ", "=="))]
    want = ["Morning.", "Beat one.", "Bedroom · Day", "Night falls.", "Kitchen · Night",
            "Bedroom · Night", "Day 2.", "Beat two.", "Kitchen · Day", "Hi."]
    check([w for w in want if w in said] == want,
          f"the story goes: {' / '.join(want)}  (got: {' / '.join(said)[:300]})")
    check("Go to bed" in text and "Go to the kitchen" in text,
          "hotspots and the way to other rooms are choices, with the game's own tips")
    check("Late snack" not in text, "a hotspot's condition (late(): day >= 2) hides it on day 1")
    check("Tell a secret" not in text and "Say hi" in text,
          "talk topics are offered under their lambda conditions")
    check("ERROR" not in p.stdout and "no label" not in p.stdout,
          "jump expression finds the beat from ready_beat() (folded from the BEATS table)")
    # events: a set of seen ones and a dict of the day each was last done
    p = subprocess.run([HOST, out, "--root", os.path.join(tmp, "root2"), "--sdmc",
                        os.path.join(tmp, "sd"), "--label", "cook", "--choices", "0"],
                       capture_output=True, text=True, timeout=120)
    said = [l for l in p.stdout.splitlines() if not l.startswith((" ", "=="))]
    want = ["Cooking.", "We baked a cake.", "Joy up by 10, now 10.", "Not again today.",
            "Seen it, a little joy.", "Joy 12, 1 seen."]
    check(said[:len(want)] == want,
          "first time / done today / seen before, from set() and {} story variables, "
          f"event_done() inlined, call gain(...) with setattr  (got: {' / '.join(said[:8])})")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()

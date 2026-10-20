#!/usr/bin/env python3
"""Starts leaderboard.py on a random localhost port and exercises the API.

    python3 server/leaderboard/test_leaderboard.py
"""

import os
import re
import secrets
import subprocess
import sys
import tempfile
import unittest
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import leaderboard  # noqa: E402

KEY = "test-key-123"
POST_LIMIT = 40


class LeaderboardTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.db = os.path.join(cls.tmp.name, "lb.db")
        env = dict(os.environ, LEADERBOARD_KEY=KEY, LEADERBOARD_POST_LIMIT=str(POST_LIMIT),
                   LEADERBOARD_GET_LIMIT="1000")
        cls.proc = subprocess.Popen(
            [sys.executable, os.path.join(HERE, "leaderboard.py"), "--host", "127.0.0.1",
             "--port", "0", "--db", cls.db],
            env=env, stderr=subprocess.PIPE, text=True)
        line = cls.proc.stderr.readline()
        m = re.search(r"serving on [\d.]+:(\d+)", line)
        if not m:
            cls.proc.kill()
            raise RuntimeError(f"server did not start: {line!r}")
        cls.base = f"http://127.0.0.1:{m.group(1)}"

    @classmethod
    def tearDownClass(cls):
        cls.proc.terminate()
        cls.proc.wait(5)
        cls.proc.stderr.close()
        cls.tmp.cleanup()

    # ---- helpers ----
    def request(self, path, body=None, headers=None):
        req = urllib.request.Request(self.base + path, data=body, headers=headers or {})
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                return r.status, r.read().decode()
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode()

    def post(self, game="quiz", name="Ann", score=50, player="aaaa1111", nonce=None, sig=None,
             key=KEY):
        nonce = nonce or secrets.token_hex(8)
        score = str(score)
        if sig is None:
            sig = leaderboard.sign(key, game, name, score, nonce)
        form = urllib.parse.urlencode(dict(game=game, name=name, score=score, player=player,
                                           nonce=nonce, sig=sig))
        return self.request("/v1/score", form.encode())

    def top(self, game, n=10):
        status, body = self.request(f"/v1/top?game={game}&n={n}")
        self.assertEqual(status, 200, body)
        return [tuple(line.split("\t")) for line in body.splitlines()]

    # ---- tests (run in name order; the rate limit test runs last) ----
    def test_1_submit_and_top(self):
        self.assertEqual(self.post("snake", "Ann", 40), (200, "ok\t1\t1\n"))
        self.assertEqual(self.post("snake", "Bob", 70, player="bbbb2222"), (200, "ok\t1\t2\n"))
        # a lower score keeps the best; the reply gives the best's rank
        self.assertEqual(self.post("snake", "Bob", 10, player="bbbb2222"), (200, "ok\t1\t2\n"))
        # same name on another console is a different player
        self.assertEqual(self.post("snake", "Ann", 70, player="cccc3333"), (200, "ok\t1\t3\n"))
        # an improvement replaces the old best
        self.assertEqual(self.post("snake", "Ann", 90), (200, "ok\t1\t3\n"))
        self.assertEqual(self.top("snake"),
                         [("1", "Ann", "90"), ("2", "Bob", "70"), ("2", "Ann", "70")])
        self.assertEqual(self.top("snake", n=1), [("1", "Ann", "90")])
        self.assertEqual(self.top("tower"), [])

    def test_2_name_cleanup(self):
        status, body = self.post("tower", "  Zoë \t  X  ", 33)
        self.assertEqual(status, 200, body)
        self.assertEqual(self.top("tower"), [("1", "Zo X", "33")])

    def test_3_validation(self):
        cases = [
            (dict(game="chess"), 400, "unknown game"),
            (dict(score=101), 400, "score"),
            (dict(score=-1), 400, "score"),
            (dict(score="5x"), 400, "score"),
            (dict(name=""), 400, "name"),
            (dict(name="éé"), 400, "name"),
            (dict(name="A" * 17), 400, "name"),
            (dict(player=""), 400, "player"),
            (dict(player="no spaces!"), 400, "player"),
            (dict(nonce="short"), 400, "nonce"),
            (dict(sig="00" * 32), 403, "signature"),
            (dict(key="wrong-key"), 403, "signature"),
        ]
        for kw, status, word in cases:
            got_status, body = self.post(**kw)
            self.assertEqual(got_status, status, (kw, body))
            self.assertTrue(body.startswith("error\t") and word in body, (kw, body))
        # a nonce works once
        self.assertEqual(self.post("miso", nonce="nonce12345")[0], 200)
        status, body = self.post("miso", nonce="nonce12345")
        self.assertEqual(status, 409, body)
        # unknown game, missing route, oversized body
        self.assertEqual(self.request("/v1/top?game=chess")[0], 400)
        self.assertEqual(self.request("/nope")[0], 404)
        self.assertEqual(self.request("/v1/score", b"x" * 5000)[0], 413)
        self.assertEqual(self.request("/v1/top?game=quiz&x=" + "a" * 600)[0], 414)
        self.assertEqual(self.request("/v1/health"), (200, "ok\n"))

    def test_4_admin_cli(self):
        out = subprocess.run([sys.executable, os.path.join(HERE, "leaderboard.py"), "--db", self.db,
                              "--list", "--game", "snake"], capture_output=True, text=True, check=True)
        rows = out.stdout.splitlines()[1:]
        self.assertEqual(len(rows), 3)
        bob = next(r for r in rows if "\tBob\t" in r)
        subprocess.run([sys.executable, os.path.join(HERE, "leaderboard.py"), "--db", self.db,
                        "--delete", bob.split("\t")[0]], capture_output=True, check=True)
        self.assertEqual(self.top("snake"), [("1", "Ann", "90"), ("2", "Ann", "70")])

    def test_9_rate_limit(self):
        # every POST so far counted against 127.0.0.1's budget
        statuses = [self.post("draw", "Rate", 1)[0] for _ in range(POST_LIMIT + 1)]
        self.assertEqual(statuses[0], 200)
        self.assertEqual(statuses[-1], 429)
        status, body = self.post("draw", "Rate", 1)
        self.assertEqual(status, 429)
        self.assertIn("too many requests", body)
        # reading has its own budget
        self.assertEqual(self.top("draw"), [("1", "Rate", "1")])


if __name__ == "__main__":
    unittest.main(verbosity=2)

# vn3ds link: games from a browser, and vn3ds's own updates

Open vn3ds on the 3DS and press Y. The receive screen shows a QR code and
`vn3ds.com · code ABCD 2345`. On a phone or computer, vn3ds.com converts the
game in the browser and sends it to the 3DS. On the same Wi-Fi it finds the
3DS by itself, and anywhere else the code says which one.

## The route

A web page can't open a connection into a home network, and nothing outside
can connect to a 3DS behind its router. So both connect out to the link, a
Cloudflare Worker (`worker.js`), which passes the bytes along:

```
browser ──wss──▶ Cloudflare edge ──▶ Durable Object "Link" (one per 3DS code) ◀── ws (plain HTTP) ── 3DS
                                      └─ "Room" (one per public address): which 3DSes are behind it
```

- **The 3DS** (`engine/source/relay.c`): once the receive screen has been
  opened, vn3ds keeps one outbound WebSocket to `link.vn3ds.com` whenever it
  listens for games. It reconnects after a drop, sends `ping` every 15 s
  (answered without waking the object), and hands the socket to the ordinary
  receiver (`net.c`, `net_adopt`). The bytes inside are the same VN3D
  protocol that `vn3ds-port --3ds` speaks, so the 3DS gets the same things:
  - only the files it doesn't have are sent;
  - an open game's files are staged;
  - a transfer resumes after a drop.
- **The page** (`web/vn3ds-send.js`): the same transfer as `send.py`
  (protocol 4: the manifest, the 3DS's bitmap, then the needed files,
  deflated when that saves 3 %). It keeps at most 4 MB beyond what the 3DS
  has acknowledged (`ack <bytes>` every 256 KB), so nothing piles up in the
  relay. After a drop it retries until it works, and each retry skips what
  already arrived.
- **Speed**: the 3DS has no TCP window scaling, so one connection carries at
  most 61 KB per round trip. With the 3DS's Wi-Fi the round trip is about
  1 ms on a LAN, and 10–40 ms to a Cloudflare edge in the same region. That
  keeps the 3DS (about 1–1.7 MB/s) the limit, as on a LAN, as long as the
  page's upload is faster. A single relay server in one region would put
  far-away users at 100+ ms, which is about 0.5 MB/s.
- **Same network**: the Room is keyed by the public address the 3DS
  connects from. A phone on IPv6 also sends its IPv4 address (from an
  IPv4-only lookup), because the 3DS has IPv4 only.

`devrelay.py` is the same link in Python (standard library only). The tests
use it, and it also works as a link on your own computer.

## Conversion in the browser (`web/`)

`web/index.html` is the page; vn3ds.com's home page carries the same section.
- **The converter**: `web/convert/worker.js` runs vnpack (the same Python as
  `vn3ds-port`) on Pyodide, with ffmpeg.wasm for sound and movies.
  `convert/vn3ds_browser.py` stands in for subprocess and threads.
- **What it accepts**: a dropped or picked `.zip`, `.apk` or `.rpa`, read in
  place without being copied into memory. It also takes an itch.io page or
  download link, which comes through the link's `/fetch` because browsers
  can't read other sites' files.
- **First visit**: Python, numpy, Pillow and ffmpeg (about 50 MB, from
  jsDelivr) load once, and the browser keeps them.
- **Quality**: always `--quality balanced`. Movies are 2D, since the depth
  model for 3D movies stays on the computer.
- **Keep the page open**: the converting happens on that device, so the page
  must stay open until it says Done (it holds a screen wake lock). Sending
  retries by itself.

After changing vnpack, rebuild the bundle the page loads:

```sh
python3 server/link/web/convert/build_bundle.py      # web/convert/vnpack.zip
```

## Installing vn3ds with FBI, and its updates

The release workflow (`.github/workflows/release.yml`, on a `v*` tag) builds
`vn3ds.3dsx` and `vn3ds.cia` with the tag as the version and attaches them
to the release. The link serves the newest release's files over plain HTTP:

- `http://link.vn3ds.com/vn3ds.cia` is for FBI: *Remote Install → Scan QR
  Code* and a QR code of this address on vn3ds.com installs vn3ds as a HOME
  Menu app. The address never changes and always serves the newest version.
- `/latest`, `/vn3ds.3dsx` and `/vn3ds.cia` are for vn3ds itself
  (`engine/source/update.c`). It checks a few seconds after it starts, at
  most every 6 hours, and downloads with resume. It checks the SHA-256
  against the release's own digest, then installs:
  - the `.3dsx` replaces itself;
  - the HOME Menu app installs the `.cia` over itself through the AM
    service, as FBI does.

  The new version runs from the next start. `update.cfg` with `auto = off`
  stops this. Builds without a tag (`dev`) never update.

## Deploying (Cloudflare, free plan)

```sh
cd server/link && npx wrangler deploy
```

1. `wrangler.toml` claims `link.vn3ds.com` as the Worker's custom domain.
2. The 3DS speaks plain HTTP (it has no usable TLS). In the vn3ds.com
   zone, add a Configuration Rule for the hostname `link.vn3ds.com` that
   turns off "Always Use HTTPS" and "Automatic HTTPS Rewrites". The page
   still uses `https://` and `wss://`.
3. Durable Objects with SQLite storage are on the free plan. A transfer is
   a few thousand WebSocket messages; idle 3DS links hibernate.

Local test of the real Worker: `npx wrangler dev --port 8799` (without
the `routes` line), then
`VN3DS_TEST_LINK=http://127.0.0.1:8799 python3 tests/test_link.py`.

## Tests

- `tests/test_link.py` (in `run_tests.sh`). The host build stands in for the
  3DS, devrelay for the Worker, and Node runs the page's sender. It checks:
  - linking up, the same-network listing, and a byte-for-byte transfer;
  - flow control, and skipping files the 3DS already has;
  - resume after a cut link;
  - the QR code module for module;
  - self-update.
- `tests/browser_convert.mjs` drives the page in headless Chrome (when
  Chrome is installed): it drops a game on it and waits for Done.

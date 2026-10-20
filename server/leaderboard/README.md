# vn3ds online leaderboard

A small HTTP server that keeps the best minigame scores (quiz, miso, draw,
lantern, snake, tower, invaders; each 0-100) and shows a top 10 per game.
It is one Python file using only the standard library, and it keeps its data
in SQLite. The engine's client is `engine/source/leaderboard.c`.

## API

The API is plain text, so the 3DS can parse it easily.

| Request | Reply (200) |
| --- | --- |
| `GET /v1/top?game=<id>&n=10` | one line per entry: `rank<TAB>name<TAB>score` (an empty body means no scores yet) |
| `POST /v1/score` form: `game, name, score, player, nonce, sig` | `ok<TAB>rank<TAB>total` (rank of the player's best, number of entries) |
| `GET /v1/health` | `ok` |

Errors come back as a 4xx or 5xx status with the body `error<TAB>message`.
The codes are 400 (validation), 403 (bad signature), 409 (reused nonce),
411, 413 and 414 (request size), and 429 (rate limit).

- `sig` is the hex HMAC-SHA256 over `game|name|score|nonce`, made with the
  shared key.
- `player` is a random id that each console makes once and keeps in
  `leaderboard.cfg`. It tells apart players who share a name. An entry is
  the triple (game, player, name), and only its best score is kept.
- Validation checks that the game id is known, the score is between 0 and
  100, and the name is 1-16 printable ASCII characters after cleanup (other
  characters are dropped and runs of spaces are collapsed). The player id
  must be 1-32 letters or digits, and the nonce 8-64 letters or digits,
  never used before. The POST body may be at most 1 KB and the URL at most
  512 bytes.
- Each client IP may make 20 posts and 120 reads a minute
  (`LEADERBOARD_POST_LIMIT` and `LEADERBOARD_GET_LIMIT`).
- Ties share a rank (scores 100, 90, 90, 80 get ranks 1, 2, 2, 4). Within a
  tie, whoever got the score first is listed first.

## Running it locally

```sh
python3 server/leaderboard/leaderboard.py --port 8080 --db /tmp/lb.db
python3 server/leaderboard/test_leaderboard.py      # the tests
```

The server reads the key from `$LEADERBOARD_KEY`, then from the file named
by `$LEADERBOARD_KEY_FILE`, then from `$CREDENTIALS_DIRECTORY/key` (systemd).
If none of those is set, it uses the public development key
`vn3ds-dev-key-change-me`, which matches the engine's default, and prints a
warning.

### Admin

```sh
python3 leaderboard.py --db lb.db --list [--game quiz]   # ids, scores, names, players
python3 leaderboard.py --db lb.db --delete 12 --delete 13
```

On the VM:

```sh
gcloud compute ssh vn3ds-leaderboard --zone=us-central1-a
sudo -u vn3ds python3 /opt/vn3ds-leaderboard/leaderboard.py \
    --db /var/lib/vn3ds-leaderboard/leaderboard.db --list
journalctl -u vn3ds-leaderboard -f        # request log
```

## Deploying to Google Cloud (free-tier e2-micro)

1. Make a real key and compile it into the game. Put the key in
   `engine/source/leaderboard_config.h` as `LEADERBOARD_KEY`:

   ```sh
   openssl rand -hex 32
   ```

2. Deploy. This uses the project that `gcloud` is configured for, unless you
   set `PROJECT=...`:

   ```sh
   server/leaderboard/deploy_gce.sh
   ```

   The script reads the key from `leaderboard_config.h`, unless you set
   `LEADERBOARD_KEY=...`. It refuses to deploy the development key unless you
   also set `ALLOW_DEV_KEY=1`. It makes these changes, each only when it is
   missing:
   - It enables the Compute Engine API.
   - It reserves the static IP `vn3ds-leaderboard-ip` in us-central1.
   - It creates the firewall rule `vn3ds-leaderboard-http`, which opens
     tcp:80 only for VMs tagged `vn3ds-leaderboard`.
   - It creates the VM `vn3ds-leaderboard`: an e2-micro in us-central1-a,
     running Debian 12 on a 10 GB standard persistent disk.

   The server code and the key reach the VM as instance metadata. `startup.sh`
   installs them on every boot and runs the server as the systemd service
   `vn3ds-leaderboard` on port 80, as an unprivileged user. Running the
   script again ships the current `leaderboard.py` and key, then restarts the
   VM. The scores and the IP stay. At the end the script waits for the server
   and prints its address.

3. Point the game at the server. Set `LEADERBOARD_URL` in
   `leaderboard_config.h` to `"http://<ip>"` and rebuild. Players can also
   override the URL in `leaderboard.cfg` in the vn3ds folder (`sdmc:/3ds/vn3ds/`
   on the console):

   ```
   url = http://203.0.113.7
   name = Armin          # optional; the default is the console's nickname
   ```

   The game adds `player = <id>` to that file by itself. A line `url =` with
   no address turns the leaderboard off. If no URL is set anywhere, the game
   stays offline and says so.

To remove everything (the VM, its disk with the scores, the firewall rule
and the IP), run `server/leaderboard/teardown_gce.sh`.

## What it costs

This information is from Google's free-tier page in October 2026. Check the
current terms before you rely on it.

- **Free:** one e2-micro VM a month in us-west1, us-central1 or us-east1,
  30 GB-months of standard persistent disk, and 1 GB of outbound traffic a
  month from North America. A request to this server is a few hundred bytes,
  so 1 GB covers millions of requests.
- The script picks the free options: e2-micro, us-central1, and a
  `pd-standard` disk. The default disk type would be `pd-balanced`, which is
  not free.
- **Possibly not free: the external IPv4 address.** Google has billed
  external IPv4 addresses separately since 2024. That is roughly
  $0.005/hour, about $3.60 a month, while the address is in use, and more
  for a reserved address that is not attached to a VM. The free-tier page
  does not say whether the e2-micro's address is covered. Check the current
  pricing at <https://cloud.google.com/vpc/network-pricing> and set a budget
  alert in the billing console. The script reserves a static address so that
  the IP compiled into the game does not change when the VM restarts. If you
  run teardown, it releases the address so it is not billed while unused.
- Traffic beyond 1 GB a month, or to China or Australia, is billed.

## Security caveats

- **The key is inside the game binary.** Anyone who wants to can extract it
  and post any score from 0 to 100. The signature, nonce and validation only
  stop casual tampering, such as replaying or editing a captured request. Use
  `--list` and `--delete` to clean up the board. To lock out a leaked key,
  change it, rebuild the game, and redeploy (old builds will then get "bad
  signature").
- **The traffic is plain HTTP.** Names and scores travel unencrypted, and the
  connection can be read or changed in transit. Nothing secret is sent: the
  signature never includes the key.
- **Names are not moderated.** Delete entries by hand if needed.
- The per-IP rate limit and the size limits keep a single client from
  flooding the server. They are not DDoS protection, but the e2-micro and
  SQLite can handle far more traffic than a 3DS game will produce.
- The service runs as the unprivileged user `vn3ds` with
  `ProtectSystem=strict`. The only open port is 80 (and 22, through the
  default network's SSH rule). The key is in `/etc/vn3ds-leaderboard/key`
  (mode 600) and in the instance metadata, so anyone with access to the
  project can read it.

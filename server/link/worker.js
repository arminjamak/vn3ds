// vn3ds link: a Cloudflare Worker that joins a browser (vn3ds.com) to a 3DS.
//
// A web page can't open a connection into someone's home network, and the
// 3DS is behind the home router, so both connect out to here and this
// passes the bytes along. The edge is close to both, so the round trip is
// short and the 3DS (64 KB receive window, no window scaling) still gets
// its full speed.
//
//   GET /3ds   WebSocket from vn3ds (engine/source/relay.c), with headers
//              X-VN3DS-Key (32 hex digits), X-VN3DS-Name, X-VN3DS-Version
//   GET /send?code=ABCD2345   WebSocket from the page (web/vn3ds-send.js)
//   GET /near[?ip4=a.b.c.d]   the 3DSes behind the caller's router (same
//              public address), as JSON [{code, name, online}]
//   GET /fetch?url=...        a game download for the page: itch.io game
//              pages are resolved to their file; the bytes are passed on
//              with CORS headers (browsers can't read other sites' files)
//   GET /latest               the newest release, for vn3ds's self-update
//              (engine/source/update.h): "vn3ds-latest 1", the tag, then
//              "3dsx <size> <sha256>" and "cia <size> <sha256>"
//   GET /vn3ds.cia, /vn3ds.3dsx   that release's files over plain HTTP:
//              FBI's "Scan QR Code" installs vn3ds from the first, and it is
//              always the newest one
//
// Through the pipe: binary messages are the vn3ds receiver protocol (VN3D
// 4, engine/source/net.c) in both directions, untouched. Text messages are
// the link's: from the 3DS "ping" (answered "pong" here without waking the
// object) and "ack <bytes>" (passed to the page: flow control); from the
// page {"t":"end"} (the transfer is over: the 3DS link is closed and the
// 3DS connects again for the next one); to the page
// {"t":"state","online":bool,"name":...} whenever the 3DS comes or goes.
//
// One Durable Object per 3DS code (Link) holds both sockets; one per public
// address (Room) remembers which 3DSes are there.

const CODE_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ";
const CODE_RE = /^[2-9A-HJ-NP-Z]{8}$/;
const KEY_RE = /^[0-9a-f]{32}$/;
const GAME_EXT = /\.(zip|apk|rpa|tar|gz|tgz|bz2)$/i;
const MAX_FETCH = 8 * 1024 ** 3;

export async function deviceCode(key) {
  const d = new Uint8Array(await crypto.subtle.digest("SHA-256", new TextEncoder().encode("vn3ds-relay-code:" + key)));
  let bits = 0n;
  for (let i = 0; i < 5; i++) bits = (bits << 8n) | BigInt(d[i]);
  let out = "";
  for (let i = 0; i < 8; i++) out += CODE_ALPHABET[Number((bits >> BigInt(35 - 5 * i)) & 31n)];
  return out;
}

const cleanCode = s => {
  const c = (s || "").replace(/[\s-]/g, "").toUpperCase();
  return CODE_RE.test(c) ? c : null;
};

function cors(resp, req, env) {
  const origin = req.headers.get("Origin") || "";
  const allowed = (env.ORIGINS || "https://vn3ds.com,https://www.vn3ds.com").split(",");
  const h = new Headers(resp.headers);
  if (allowed.includes(origin) || /^http:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/.test(origin)) {
    h.set("Access-Control-Allow-Origin", origin);
    h.set("Vary", "Origin");
    h.set("Access-Control-Expose-Headers", "Content-Length, X-File-Name");
  }
  return new Response(resp.body, { status: resp.status, headers: h, webSocket: resp.webSocket });
}

const json = (v, status = 200) =>
  new Response(JSON.stringify(v), { status, headers: { "Content-Type": "application/json", "Cache-Control": "no-store" } });

export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    const ip = req.headers.get("CF-Connecting-IP") || "";
    if (req.method === "OPTIONS") return cors(new Response(null, { status: 204 }), req, env);
    const upgrade = (req.headers.get("Upgrade") || "").toLowerCase() === "websocket";

    if (url.pathname === "/3ds") {
      if (!upgrade) return new Response("vn3ds link: WebSocket only\n", { status: 426 });
      const key = req.headers.get("X-VN3DS-Key") || "";
      if (!KEY_RE.test(key)) return new Response("bad key\n", { status: 400 });
      const code = await deviceCode(key);
      const name = (req.headers.get("X-VN3DS-Name") || "3DS").replace(/[^A-Za-z0-9 ]/g, "").slice(0, 20) || "3DS";
      const h = new Headers(req.headers);
      h.set("X-Link-Role", "3ds");
      h.set("X-Link-Code", code);
      h.set("X-Link-Name", name);
      h.set("X-Link-IP", ip);
      return env.LINK.get(env.LINK.idFromName(code)).fetch(new Request(req, { headers: h }));
    }

    if (url.pathname === "/send") {
      const code = cleanCode(url.searchParams.get("code"));
      if (!code) return cors(json({ error: "That code doesn't look right" }, 404), req, env);
      if (!upgrade) return cors(json({ error: "WebSocket only" }, 426), req, env);
      const h = new Headers(req.headers);
      h.set("X-Link-Role", "web");
      h.set("X-Link-Code", code);
      return env.LINK.get(env.LINK.idFromName(code)).fetch(new Request(req, { headers: h }));
    }

    if (url.pathname === "/near") {
      // A phone often reaches us over IPv6 while the 3DS (IPv4 only) can't:
      // then the page also says its IPv4 address, from an IPv4-only lookup.
      const ips = [ip];
      const ip4 = url.searchParams.get("ip4");
      if (ip.includes(":") && ip4 && /^\d{1,3}(\.\d{1,3}){3}$/.test(ip4)) ips.push(ip4);
      const seen = new Map();
      for (const a of ips) {
        if (!a) continue;
        const r = await env.ROOM.get(env.ROOM.idFromName(a)).fetch("https://room/list");
        for (const d of await r.json()) seen.set(d.code, d);
      }
      return cors(json([...seen.values()]), req, env);
    }

    if (url.pathname === "/fetch") return cors(await proxyDownload(url.searchParams.get("url") || ""), req, env);
    if (url.pathname === "/latest") return latestText(env);
    if (url.pathname === "/vn3ds.cia" || url.pathname === "/vn3ds.3dsx") return releaseFile(env, url.pathname.slice(1), req.headers.get("Range"));
    if (url.pathname === "/health") return cors(json({ ok: true }), req, env);
    return new Response("vn3ds link\n", { status: 404 });
  },
};

export class Link {
  constructor(state, env) {
    this.state = state;
    this.env = env;
    state.setWebSocketAutoResponse(new WebSocketRequestResponsePair("ping", "pong"));
  }

  role(ws) {
    return this.state.getTags(ws)[0];
  }

  device() {
    const s = this.state.getWebSockets("3ds")[0];
    return s ? s.deserializeAttachment() : null;
  }

  tellWeb() {
    const d = this.device();
    const msg = JSON.stringify({ t: "state", online: !!d, name: d ? d.name : "" });
    for (const w of this.state.getWebSockets("web")) try { w.send(msg); } catch (e) {}
  }

  async room(d, op) {
    if (!d || !d.ip) return;
    await this.env.ROOM.get(this.env.ROOM.idFromName(d.ip)).fetch(`https://room/${op}`, {
      method: "POST",
      body: JSON.stringify({ code: d.code, name: d.name }),
    });
  }

  async fetch(req) {
    const role = req.headers.get("X-Link-Role");
    const pair = new WebSocketPair();
    const [client, server] = Object.values(pair);
    for (const old of this.state.getWebSockets(role)) {
      try { old.close(4000, "replaced by a newer connection"); } catch (e) {}
    }
    this.state.acceptWebSocket(server, [role]);
    if (role === "3ds") {
      const d = { code: req.headers.get("X-Link-Code"), name: req.headers.get("X-Link-Name"), ip: req.headers.get("X-Link-IP") };
      server.serializeAttachment(d);
      await this.room(d, "add");
    }
    this.tellWeb();
    return new Response(null, { status: 101, webSocket: client });
  }

  async webSocketMessage(ws, msg) {
    const from = this.role(ws);
    if (from === "web" && typeof msg === "string") {
      let m = {};
      try { m = JSON.parse(msg); } catch (e) {}
      if (m.t === "end") for (const s of this.state.getWebSockets("3ds")) try { s.close(1000, "transfer over"); } catch (e) {}
      return;
    }
    const to = this.state.getWebSockets(from === "3ds" ? "web" : "3ds");
    for (const o of to) try { o.send(msg); } catch (e) {}
    if (!to.length && from === "web") ws.send(JSON.stringify({ t: "state", online: false, name: "" }));
  }

  async webSocketClose(ws, code, reason) {
    await this.gone(ws);
  }

  async webSocketError(ws) {
    await this.gone(ws);
  }

  async gone(ws) {
    const from = this.role(ws);
    try { ws.close(1000, "bye"); } catch (e) {}
    if (from === "3ds") {
      const d = ws.deserializeAttachment();
      if (!this.state.getWebSockets("3ds").some(s => s !== ws)) await this.room(d, "offline");
      this.tellWeb();
    } else {
      // the page went away: the 3DS's receiver starts afresh on a new link
      for (const s of this.state.getWebSockets("3ds")) try { s.close(1000, "sender left"); } catch (e) {}
    }
  }
}

// The 3DSes seen behind one public address. Kept a week after they were
// last online, so the page can say "your 3DS: open vn3ds on it".
export class Room {
  constructor(state) {
    this.state = state;
  }

  async fetch(req) {
    const op = new URL(req.url).pathname.slice(1);
    const all = (await this.state.storage.get("devices")) || {};
    const now = Date.now();
    if (op === "list") {
      for (const [c, d] of Object.entries(all)) if (now - d.seen > 7 * 86400e3) delete all[c];
      await this.state.storage.put("devices", all);
      return json(Object.values(all).map(d => ({ code: d.code, name: d.name, online: d.online })));
    }
    const { code, name } = await req.json();
    if (op === "add") all[code] = { code, name, online: true, seen: now };
    else if (op === "offline" && all[code]) Object.assign(all[code], { online: false, seen: now });
    await this.state.storage.put("devices", all);
    return json({ ok: true });
  }
}

// ---- downloads for the page ---------------------------------------------------

function publicHost(u) {
  const h = u.hostname;
  return !(h === "localhost" || h.endsWith(".local") || /^(10|127|169\.254|192\.168)\./.test(h) ||
    /^172\.(1[6-9]|2\d|3[01])\./.test(h) || h.startsWith("[") || /^\d+$/.test(h));
}

async function resolveItch(pageUrl) {
  const base = pageUrl.split("?")[0].replace(/\/$/, "");
  const jar = [];
  const keep = r => {
    const sc = r.headers.getSetCookie ? r.headers.getSetCookie() : [];
    for (const c of sc) jar.push(c.split(";")[0]);
    return r;
  };
  const get = (u, init = {}) =>
    fetch(u, { ...init, headers: { ...(init.headers || {}), Cookie: jar.join("; "), "User-Agent": "vn3ds-link/1" } }).then(keep);
  const page = await (await get(base)).text();
  let csrf = (page.match(/name="csrf_token"\s+value="([^"]+)"/) || [])[1];
  if (!csrf) throw new Error("That itch.io page doesn't look like a game page");
  const form = t => ({ method: "POST", body: new URLSearchParams({ csrf_token: t }),
    headers: { "Content-Type": "application/x-www-form-urlencoded" } });
  let uploads = itchUploads(page);
  let source = "view_game", extra = {}, html = page;
  if (!uploads.length) {
    const r = await (await get(base + "/download_url", form(csrf))).json();
    if (!r.url) throw new Error("This game isn't free on itch.io. Buy it there, then paste the download link from your itch.io library");
    html = await (await get(r.url)).text();
    uploads = itchUploads(html);
    source = "game_download";
    csrf = (html.match(/name="csrf_token"\s+value="([^"]+)"/) || [])[1] || csrf;
    const opts = (html.match(/init_GameDownload\([^,]+,\s*(\{.*?\})\);/) || [])[1] || "";
    if (opts.includes('"show_download_lightbox":true')) extra = { after_download_lightbox: "1", as_props: "1" };
    try { const k = JSON.parse(opts).key; if (k) extra.key = k; } catch (e) {}
  }
  const best = pickUpload(uploads);
  if (!best) throw new Error("No download found on that itch.io page");
  const q = new URLSearchParams({ source, ...extra });
  const r = await (await get(`${base}/file/${best.id}?${q}`, form(csrf))).json();
  if (!r.url) throw new Error("itch.io didn't hand out the download");
  return r.url;
}

function itchUploads(html) {
  return html.split(/<div class="upload(?=[ "])/).slice(1).map(b => {
    const id = (b.match(/data-upload_id="(\d+)"/) || [])[1];
    const name = (b.match(/class="name"[^>]*title="([^"]+)"/) || [])[1];
    const platforms = [...b.matchAll(/title="Download for ([^"]+)"/g)].map(m => m[1].toLowerCase()).join(" ");
    return id && name ? { id, name, platforms } : null;
  }).filter(Boolean);
}

// The upload most likely to hold the whole Ren'Py game: the PC/Linux build,
// then Mac or Android; never a soundtrack or a patch.
export function pickUpload(ups) {
  const score = u => {
    const n = u.name.toLowerCase();
    let s = 0;
    if (/(soundtrack|\bost\b|artbook|wallpaper|guide|walkthrough|patch|\.pdf$|\.mp3$)/.test(n)) s -= 100;
    const ext = (n.match(/\.([a-z0-9]{2,4})$/) || [])[1];
    if (ext && !["zip", "apk", "bz2", "gz", "tgz", "rpa"].includes(ext)) s -= 50;
    if (/(-pc|-linux|windows|win|-market)/.test(n) || /windows|linux/.test(u.platforms)) s += 30;
    if (/-mac|osx/.test(n) || /mac/.test(u.platforms)) s += 10;
    if (n.endsWith(".apk")) s += 5;
    if (n.includes("-all")) s += 20;
    return s;
  };
  return ups.length ? ups.reduce((a, b) => (score(b) > score(a) ? b : a)) : null;
}

async function proxyDownload(raw) {
  let u;
  try { u = new URL(/^https?:\/\//i.test(raw) ? raw : "https://" + raw); } catch (e) { return json({ error: "That is not a web link" }, 400); }
  if (!/^https?:$/.test(u.protocol) || !publicHost(u)) return json({ error: "That link can't be fetched" }, 400);
  try {
    let target = u.href;
    const parts = u.pathname.split("/").filter(Boolean);
    if (u.hostname.endsWith(".itch.io") && u.hostname !== "itch.io" && parts.length === 1) target = await resolveItch(u.href);
    const r = await fetch(target, { headers: { "User-Agent": "vn3ds-link/1" }, redirect: "follow" });
    if (!r.ok) return json({ error: `The download answered ${r.status}` }, 502);
    if ((r.headers.get("Content-Type") || "").includes("text/html"))
      return json({ error: "That link opens a web page, not a file. Paste the itch.io game page, or the link of the download itself" }, 400);
    const len = Number(r.headers.get("Content-Length") || 0);
    if (len > MAX_FETCH) return json({ error: "That file is too big" }, 413);
    const cd = r.headers.get("Content-Disposition") || "";
    let name = decodeURIComponent((cd.match(/filename\*=UTF-8''([^;]+)/) || cd.match(/filename="?([^";]+)"?/) || [])[1] ||
      new URL(r.url).pathname.split("/").pop() || "game.zip");
    if (!GAME_EXT.test(name)) return json({ error: `${name} isn't a game vn3ds can convert (a .zip, .apk or .rpa)` }, 400);
    const h = new Headers({ "Content-Type": "application/octet-stream", "X-File-Name": encodeURIComponent(name) });
    if (len) h.set("Content-Length", String(len));
    return new Response(r.body, { status: 200, headers: h });
  } catch (e) {
    return json({ error: e.message || "The download failed" }, 502);
  }
}

// ---- the newest release ---------------------------------------------------------

async function latestRelease(env) {
  const repo = env.REPO || "arminjamak/vn3ds";
  const r = await fetch(`https://api.github.com/repos/${repo}/releases/latest`, {
    headers: { "User-Agent": "vn3ds-link/1", Accept: "application/vnd.github+json" },
    cf: { cacheTtl: 300, cacheEverything: true },   // (GitHub allows 60 unsigned requests an hour)
  });
  if (!r.ok) throw new Error(`GitHub answered ${r.status}`);
  return r.json();
}

async function latestText(env) {
  try {
    const rel = await latestRelease(env);
    const lines = ["vn3ds-latest 1", rel.tag_name];
    for (const [kind, name] of [["3dsx", "vn3ds.3dsx"], ["cia", "vn3ds.cia"]]) {
      const a = rel.assets.find(x => x.name === name);
      const sha = a && (a.digest || "").replace(/^sha256:/, "");
      if (a && sha) lines.push(`${kind} ${a.size} ${sha}`);
    }
    return new Response(lines.join("\n") + "\n", { headers: { "Content-Type": "text/plain", "Cache-Control": "max-age=300" } });
  } catch (e) {
    return new Response("unavailable\n", { status: 503 });
  }
}

async function releaseFile(env, name, range) {
  try {
    const a = (await latestRelease(env)).assets.find(x => x.name === name);
    if (!a) return new Response("not in the newest release\n", { status: 404 });
    // a Range request (a resumed download) is passed on as it is
    const h = { "User-Agent": "vn3ds-link/1" };
    if (range) h.Range = range;
    const r = await fetch(a.browser_download_url, { headers: h, redirect: "follow" });
    const out = new Headers({ "Content-Type": "application/octet-stream" });
    for (const k of ["Content-Length", "Content-Range", "Accept-Ranges"]) if (r.headers.get(k)) out.set(k, r.headers.get(k));
    out.set("Content-Disposition", `attachment; filename="${name}"`);
    return new Response(r.body, { status: r.status, headers: out });
  } catch (e) {
    return new Response("unavailable\n", { status: 503 });
  }
}

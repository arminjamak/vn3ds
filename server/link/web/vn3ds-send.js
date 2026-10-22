// Sends a converted game from a web page to a 3DS running vn3ds, through
// the vn3ds link (server/link/worker.js). The same transfer as
// `vn3ds-port --3ds` (tools/vnpack/send.py, protocol 4): the manifest goes
// first, the 3DS answers with the files it still needs, those follow
// back to back (deflated when that saves something). A dropped connection
// is retried until it works; every retry skips what already arrived.
//
//   import { findNearby, sendGame } from "./vn3ds-send.js";
//   const near = await findNearby();            // [{code, name, online}]
//   await sendGame({ code, files, onProgress }); // files: [{path, size, data}]
//
// `path` is relative to the vn3ds folder ("games/<id>/game.bin"); `data` is
// a Blob/File, an ArrayBuffer/Uint8Array, or an async function returning
// one. Works in browsers and in Node 22+ (global WebSocket).

export const LINK = "https://link.vn3ds.com";

const WINDOW = 4 << 20;        // bytes on their way to the card at most
const MSG = 256 << 10;         // one WebSocket message (the relay takes up to 1 MiB)
const COMPRESS_MIN_GAIN = 0.97;
const PROBE_ABOVE = 8 << 20;
const PROBE_BYTES = 1 << 20;

// ---- small helpers --------------------------------------------------------------

const CRC_TABLE = (() => {
  const t = new Uint32Array(256);
  for (let n = 0; n < 256; n++) {
    let c = n;
    for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    t[n] = c >>> 0;
  }
  return t;
})();

export function crc32(bytes, crc = 0) {
  let c = ~crc >>> 0;
  for (let i = 0; i < bytes.length; i++) c = CRC_TABLE[(c ^ bytes[i]) & 0xff] ^ (c >>> 8);
  return ~c >>> 0;
}

async function bytesOf(file) {
  let d = typeof file.data === "function" ? await file.data() : file.data;
  if (d instanceof Uint8Array) return d;
  if (d instanceof ArrayBuffer) return new Uint8Array(d);
  if (d && typeof d.arrayBuffer === "function") return new Uint8Array(await d.arrayBuffer());
  throw new Error(`no data for ${file.path}`);
}

async function deflateRaw(bytes) {
  const cs = new CompressionStream("deflate-raw");
  const out = new Response(new Blob([bytes]).stream().pipeThrough(cs)).arrayBuffer();
  return new Uint8Array(await out);
}

// (method, payload): deflate only when it saves at least 3%; big media that
// doesn't shrink is tested on its first megabyte, as send.py does.
async function pack(bytes) {
  if (bytes.length > PROBE_ABOVE) {
    const head = bytes.subarray(0, PROBE_BYTES);
    if ((await deflateRaw(head)).length >= head.length * COMPRESS_MIN_GAIN) return [0, bytes];
  }
  const z = await deflateRaw(bytes);
  return z.length < bytes.length * COMPRESS_MIN_GAIN ? [1, z] : [0, bytes];
}

const sleep = ms => new Promise(r => setTimeout(r, ms));
const wsUrl = (base, path) => base.replace(/^http/, "ws") + path;

export class Cancelled extends Error {}

// ---- finding the 3DS -------------------------------------------------------------

// The 3DSes behind the same router as this page (the relay sees the same
// public address). A phone on IPv6 also says its IPv4 address, which is
// what the 3DS (IPv4 only) shows up under.
export async function findNearby(link = LINK) {
  let q = "";
  try {
    const r = await fetch("https://api.ipify.org?format=json", { signal: AbortSignal.timeout(3000) });
    const j = await r.json();
    if (/^\d{1,3}(\.\d{1,3}){3}$/.test(j.ip)) q = "?ip4=" + j.ip;
  } catch (e) { /* the relay's own view is enough */ }
  const r = await fetch(link + "/near" + q, { cache: "no-store" });
  if (!r.ok) throw new Error("The vn3ds link isn't answering");
  return r.json();
}

// ---- one connection to the relay ----------------------------------------------------

class Pipe {
  constructor(link, code, onState) {
    this.ws = new WebSocket(wsUrl(link, "/send?code=" + encodeURIComponent(code)));
    this.ws.binaryType = "arraybuffer";
    this.chunks = [];       // binary bytes from the 3DS not yet read
    this.have = 0;
    this.acked = 0;         // stream bytes the 3DS has taken in
    this.online = false;
    this.name = "";
    this.closed = false;
    this.waiters = new Set();
    this.onState = onState;
    this.ws.onmessage = ev => {
      if (typeof ev.data === "string") {
        if (ev.data.startsWith("ack ")) this.acked = Number(ev.data.slice(4));
        else {
          try {
            const m = JSON.parse(ev.data);
            if (m.t === "state") {
              this.online = m.online;
              this.name = m.name || this.name;
              if (onState) onState(m);
            }
          } catch (e) {}
        }
      } else {
        const b = new Uint8Array(ev.data);
        this.chunks.push(b);
        this.have += b.length;
      }
      this.wake();
    };
    this.ws.onclose = () => { this.closed = true; this.wake(); };
    this.ws.onerror = () => { this.closed = true; this.wake(); };
  }

  wake() {
    for (const w of this.waiters) w();
    this.waiters.clear();
  }

  // waits until cond() holds; throws if the link breaks or stop() says so
  async until(cond, stop, ms = 0, what = "the 3DS") {
    const t0 = Date.now();
    for (;;) {
      if (cond()) return;
      if (stop && stop()) throw new Cancelled("cancelled");
      if (this.closed) throw new Error("The connection to the vn3ds link dropped");
      if (ms && Date.now() - t0 > ms) throw new Error(`No answer from ${what}`);
      await new Promise(r => { this.waiters.add(r); setTimeout(r, 250); });
    }
  }

  async read(n, stop, ms) {
    await this.until(() => this.have >= n || !this.online, stop, ms);
    if (this.have < n) throw new Error("The 3DS went offline");
    const out = new Uint8Array(n);
    let at = 0;
    while (at < n) {
      const c = this.chunks[0];
      const take = Math.min(c.length, n - at);
      out.set(c.subarray(0, take), at);
      at += take;
      if (take === c.length) this.chunks.shift();
      else this.chunks[0] = c.subarray(take);
    }
    this.have -= n;
    return out;
  }

  send(bytes) {
    if (this.closed || this.ws.readyState !== 1) throw new Error("The connection to the vn3ds link dropped");
    this.ws.send(bytes);
  }

  close(end) {
    try {
      if (end && this.ws.readyState === 1) this.ws.send(JSON.stringify({ t: "end" }));
      this.ws.close(1000);
    } catch (e) {}
  }
}

// ---- the transfer -------------------------------------------------------------------

async function attempt(link, code, files, crcs, report, stop, onState) {
  const pipe = new Pipe(link, code, onState);
  let sent = 0;   // stream bytes written to the pipe
  try {
    await pipe.until(() => pipe.ws.readyState === 1, stop, 15000, "the vn3ds link");
    report("waiting", { name: pipe.name });
    await pipe.until(() => pipe.online, stop);   // (forever: the 3DS may be off for now)
    report("checking", { files: files.length, name: pipe.name });

    const enc = new TextEncoder();
    const total = files.reduce((a, f) => a + f.size, 0);
    const parts = [];
    const head = new DataView(new ArrayBuffer(20));
    head.setUint32(0, 0x4433_4e56, true);   // "VN3D"
    head.setUint32(4, 4, true);
    head.setUint32(8, files.length, true);
    head.setBigUint64(12, BigInt(total), true);
    parts.push(new Uint8Array(head.buffer));
    files.forEach((f, i) => {
      const name = enc.encode(f.path);
      const e = new DataView(new ArrayBuffer(2 + name.length + 12));
      e.setUint16(0, name.length, true);
      new Uint8Array(e.buffer).set(name, 2);
      e.setBigUint64(2 + name.length, BigInt(f.size), true);
      e.setUint32(10 + name.length, crcs[i], true);
      parts.push(new Uint8Array(e.buffer));
    });
    const manifest = new Uint8Array(await new Blob(parts).arrayBuffer());
    for (let k = 0; k < manifest.length; k += MSG) pipe.send(manifest.subarray(k, k + MSG));
    sent += manifest.length;

    // the 3DS compares the list with its card (this can take a while)
    const bits = await pipe.read((files.length + 7) >> 3, stop, 30 * 60e3);
    const need = files.map((_, i) => i).filter(i => (bits[i >> 3] >> (i & 7)) & 1);
    const skipped = files.length - need.length;
    if (skipped) report("skipped", { skipped, need: need.length });
    const want = need.reduce((a, i) => a + files[i].size, 0);

    let done = 0, wire = 0, last = 0;
    const t0 = Date.now();
    const tick = (force = false) => {
      if (stop && stop()) throw new Cancelled("cancelled");
      if (!force && Date.now() - last < 250) return;
      last = Date.now();
      const rate = done / Math.max(0.001, (Date.now() - t0) / 1000);
      report("bytes", { done, total: want, rate, left: (want - done) / Math.max(rate, 1), wire });
    };
    tick(true);
    // the next file is read and compressed while this one goes out
    let next = need.length ? (async i => pack(await bytesOf(files[i])))(need[0]) : null;
    for (let n = 0; n < need.length; n++) {
      const i = need[n];
      const [method, payload] = await next;
      next = n + 1 < need.length ? (async j => pack(await bytesOf(files[j])))(need[n + 1]) : null;
      if (method === 0 && payload.length !== files[i].size) throw new Error(`${files[i].path} changed size`);
      const h = new DataView(new ArrayBuffer(13));
      h.setUint32(0, i, true);
      h.setUint8(4, method);
      h.setBigUint64(5, BigInt(payload.length), true);
      pipe.send(new Uint8Array(h.buffer));
      sent += 13;
      const base = done;
      for (let k = 0; k < payload.length; k += MSG) {
        const piece = payload.subarray(k, k + MSG);
        // flow control: the 3DS says how much it has taken in
        await pipe.until(() => sent - pipe.acked < WINDOW && pipe.ws.bufferedAmount < WINDOW || !pipe.online, stop);
        if (!pipe.online) throw new Error("The 3DS went offline");
        pipe.send(piece);
        sent += piece.length;
        wire += piece.length;
        done = base + Math.floor(files[i].size * (k + piece.length) / Math.max(1, payload.length));
        tick();
      }
      done = base + files[i].size;
    }
    if (need.length) tick(true);
    report("sent", { need: need.length, wire, unpacked: want });
    const doneMark = await pipe.read(8, stop, 10 * 60e3);
    if (new TextDecoder().decode(doneMark.subarray(0, 4)) !== "DONE") throw new Error("The transfer did not finish cleanly");
    const failed = new DataView(doneMark.buffer, doneMark.byteOffset + 4, 4).getUint32(0, true);
    pipe.close(true);
    return { sent: need.length - failed, skipped, failed };
  } catch (e) {
    pipe.close(false);
    throw e;
  }
}

// Sends files to the 3DS with this code; keeps trying until it works,
// stop() returns true (Cancelled), or `retries` reconnects failed.
// onProgress(event, info): "waiting", "checking", "skipped", "bytes"
// {done, total, rate, left, wire}, "sent", "retry" {attempt, wait, text}.
export async function sendGame({ code, files, link = LINK, onProgress, onState, stop, retries = Infinity }) {
  const report = onProgress || (() => {});
  report("preparing", { files: files.length });
  const crcs = [];
  for (const f of files) {   // once: retries reuse them
    const b = await bytesOf(f);
    f.size = b.length;
    crcs.push(crc32(b));
    if (stop && stop()) throw new Cancelled("cancelled");
  }
  for (let n = 0; ; n++) {
    try {
      return await attempt(link, code, files, crcs, report, stop, onState);
    } catch (e) {
      if (e instanceof Cancelled || n >= retries) throw e;
      const wait = Math.min(60, 2 + 3 * n);
      report("retry", { attempt: n + 1, wait, text: `${e.message}: trying again in ${wait} s` });
      for (let t = 0; t < wait * 4; t++) {
        if (stop && stop()) throw new Cancelled("cancelled");
        await sleep(250);
      }
    }
  }
}

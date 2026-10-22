// Movies for the 3DS in a web page: the clip is demuxed here and decoded
// by the browser (WebCodecs VideoDecoder, on the graphics chip where there
// is one); a few helper workers (movie-worker.js) scale the frames and
// encode them with x264 (ffmpeg.wasm), each a GOP-long stretch at a time,
// side by side. ffmpeg.wasm alone does all of it in one thread at a few
// frames a second; a game with hours of movies (Ripples: 1,197 clips at
// 1080p) needs this.
//
//   const r = await vn3dsEncodeMovie(bytes, ".webm", 400, 240, 30, 240, 4, null, "main", "3.0", "slower");
//   r = {annexb: Uint8Array, first: Uint8Array (w*h RGB), fpsNum, fpsDen} or null
//
// null: this clip or browser can't be done here (not WebM/Matroska, a codec
// the browser can't decode, no workers); the caller uses ffmpeg then. What
// comes out is what vnpack's .cvh needs (tools/vnpack/assets.py,
// encode_cvh), made with its x264 settings: Annex B, no B-frames, an IDR
// frame at frame 0 and at the start of every GOP, two passes at `kbps`, the
// frame rate the clip's own up to fpsCap. Each GOP is coded on its own
// (two-pass rate control per 4 s stretch: the same size and quality as the
// whole clip at once, VMAF 92.7 against 92.9 on a test clip).
//
// Why not the browser's own encoder (VideoEncoder): at 400x240 it needs
// twice x264's bitrate for the same quality. Why the scaling isn't the
// browser's (drawImage): see "scaling" below.
//
// A classic script: convert/worker.js and movie-worker.js importScripts it.

(function () {
  "use strict";

  // ---- Matroska / WebM -------------------------------------------------

  const ID = {
    EBML: 0x1a45dfa3, Segment: 0x18538067, Info: 0x1549a966, TimecodeScale: 0x2ad7b1,
    Tracks: 0x1654ae6b, TrackEntry: 0xae, TrackNumber: 0xd7, TrackType: 0x83, CodecID: 0x86,
    CodecPrivate: 0x63a2, DefaultDuration: 0x23e383, Video: 0xe0, PixelWidth: 0xb0, PixelHeight: 0xba,
    Cluster: 0x1f43b675, Timecode: 0xe7, SimpleBlock: 0xa3, BlockGroup: 0xa0, Block: 0xa1,
    ReferenceBlock: 0xfb,
  };
  // elements whose children are read; everything else is skipped by size
  const MASTER = new Set([ID.Segment, ID.Info, ID.Tracks, ID.TrackEntry, ID.Video, ID.Cluster, ID.BlockGroup]);

  function vint(b, p, keepMarker) {
    const first = b[p];
    if (first === undefined) return null;
    let len = 1, mask = 0x80;
    while (len <= 8 && !(first & mask)) { len++; mask >>= 1; }
    if (len > 8 || p + len > b.length) return null;
    let v = keepMarker ? first : first & (mask - 1);
    let allOnes = (first & (mask - 1)) === mask - 1;
    for (let i = 1; i < len; i++) {
      v = v * 256 + b[p + i];
      if (b[p + i] !== 0xff) allOnes = false;
    }
    return { v, len, unknown: !keepMarker && allOnes };
  }

  const uint = (b, p, n) => { let v = 0; for (let i = 0; i < n; i++) v = v * 256 + b[p + i]; return v; };
  const sint16 = (b, p) => { const v = (b[p] << 8) | b[p + 1]; return v & 0x8000 ? v - 0x10000 : v; };

  // -> {codec, width, height, defaultDuration (ns) or 0, codecPrivate, frames: [{t (s), key, data}]}
  function demuxWebM(b) {
    let scale = 1e6;
    const tracks = [];
    let track = null;
    const blocks = [];   // [track number, cluster time, block bytes, keyframe or null]
    let clusterTime = 0;
    let group = null;    // the BlockGroup being read: {data, ref}

    function walk(p, end) {
      while (p < end) {
        const id = vint(b, p, true);
        if (!id) return;
        const size = vint(b, p + id.len, false);
        if (!size) return;
        const at = p + id.len + size.len;
        const stop = size.unknown ? end : Math.min(end, at + size.v);
        const e = id.v;
        if (e === ID.TrackEntry) {
          track = { number: 0, type: 0, codec: "", width: 0, height: 0, dur: 0, priv: null };
          walk(at, stop);
          tracks.push(track);
          track = null;
        } else if (e === ID.BlockGroup) {
          group = { data: null, ref: false };
          walk(at, stop);
          if (group.data) blocks.push([group.data[0], clusterTime, group.data[1], !group.ref]);
          group = null;
        } else if (MASTER.has(e)) {
          walk(at, stop);
        } else if (e === ID.TimecodeScale) scale = uint(b, at, stop - at);
        else if (e === ID.Timecode) clusterTime = uint(b, at, stop - at);
        else if (track && e === ID.TrackNumber) track.number = uint(b, at, stop - at);
        else if (track && e === ID.TrackType) track.type = uint(b, at, stop - at);
        else if (track && e === ID.CodecID) track.codec = new TextDecoder().decode(b.subarray(at, stop)).replace(/\0+$/, "");
        else if (track && e === ID.CodecPrivate) track.priv = b.slice(at, stop);
        else if (track && e === ID.DefaultDuration) track.dur = uint(b, at, stop - at);
        else if (track && e === ID.PixelWidth) track.width = uint(b, at, stop - at);
        else if (track && e === ID.PixelHeight) track.height = uint(b, at, stop - at);
        else if (e === ID.SimpleBlock) {
          const n = vint(b, at, false);
          blocks.push([n.v, clusterTime, b.subarray(at, stop), null]);
        } else if (group && e === ID.Block) {
          const n = vint(b, at, false);
          group.data = [n.v, b.subarray(at, stop)];
        } else if (group && e === ID.ReferenceBlock) group.ref = true;
        p = stop;
      }
    }
    walk(0, b.length);

    const v = tracks.find(t => t.type === 1 || /^V_/.test(t.codec));
    if (!v) return null;
    const frames = [];
    for (const [num, ct, blk, keyFromGroup] of blocks) {
      if (num !== v.number) continue;
      const n = vint(blk, 0, false);
      const rel = sint16(blk, n.len);
      const flags = blk[n.len + 2];
      if (flags & 0x06) return null;   // laced video frames: not seen in practice; ffmpeg can
      const key = keyFromGroup === null ? !!(flags & 0x80) : keyFromGroup;
      frames.push({ t: (ct + rel) * scale / 1e9, key, data: blk.subarray(n.len + 3) });
    }
    return { codec: v.codec, width: v.width, height: v.height, defaultDuration: v.dur, codecPrivate: v.priv, frames };
  }

  // ---- MP4 (H.264) -------------------------------------------------------

  // -> the same as demuxWebM (frames in decode order, t the presentation
  // time), codec "mp4-avc" with the avcC record as codecPrivate; null for
  // anything else (HEVC, fragmented files: ffmpeg does those).
  function demuxMP4(b) {
    const dv = new DataView(b.buffer, b.byteOffset, b.byteLength);
    const u32 = p => dv.getUint32(p);
    const type = p => String.fromCharCode(b[p], b[p + 1], b[p + 2], b[p + 3]);
    function boxes(p, end) {
      const out = [];
      while (p + 8 <= end) {
        let size = u32(p), head = 8;
        if (size === 1) { size = dv.getUint32(p + 8) * 4294967296 + dv.getUint32(p + 12); head = 16; }
        else if (size === 0) size = end - p;
        if (size < head || p + size > end) break;
        out.push({ type: type(p + 4), start: p + head, end: p + size });
        p += size;
      }
      return out;
    }
    const child = (box, t) => box && boxes(box.start, box.end).find(x => x.type === t);
    const top = boxes(0, b.length);
    if (top.some(x => x.type === "moof")) return null;
    const moov = top.find(x => x.type === "moov");
    if (!moov) return null;
    for (const trak of boxes(moov.start, moov.end).filter(x => x.type === "trak")) {
      const mdia = child(trak, "mdia");
      const hdlr = child(mdia, "hdlr");
      if (!hdlr || type(hdlr.start + 8) !== "vide") continue;
      const mdhd = child(mdia, "mdhd");
      const timescale = b[mdhd.start] === 1 ? u32(mdhd.start + 20) : u32(mdhd.start + 12);
      const stbl = child(child(mdia, "minf"), "stbl");
      const stsd = child(stbl, "stsd");
      const entry = boxes(stsd.start + 8, stsd.end)[0];
      if (!entry || (entry.type !== "avc1" && entry.type !== "avc3")) return null;
      const avcC = boxes(entry.start + 78, entry.end).find(x => x.type === "avcC");
      if (!avcC) return null;
      const width = dv.getUint16(entry.start + 24), height = dv.getUint16(entry.start + 26);
      // sample sizes, times, sync samples, chunk offsets
      const stsz = child(stbl, "stsz");
      const fixed = u32(stsz.start + 4), count = u32(stsz.start + 8);
      const size = i => fixed || u32(stsz.start + 12 + 4 * i);
      const dts = new Float64Array(count);
      const stts = child(stbl, "stts");
      for (let e = 0, n = u32(stts.start + 4), i = 0, t = 0; e < n; e++) {
        const c = u32(stts.start + 8 + 8 * e), d = u32(stts.start + 12 + 8 * e);
        for (let k = 0; k < c && i < count; k++, i++, t += d) dts[i] = t;
      }
      const cts = new Float64Array(count);
      const ctts = child(stbl, "ctts");
      if (ctts) {
        const v1 = b[ctts.start] === 1;
        for (let e = 0, n = u32(ctts.start + 4), i = 0; e < n; e++) {
          const c = u32(ctts.start + 8 + 8 * e);
          const o = v1 ? dv.getInt32(ctts.start + 12 + 8 * e) : u32(ctts.start + 12 + 8 * e);
          for (let k = 0; k < c && i < count; k++, i++) cts[i] = o;
        }
      }
      const stss = child(stbl, "stss");
      const sync = stss ? new Set(Array.from({ length: u32(stss.start + 4) }, (_, k) => u32(stss.start + 8 + 4 * k) - 1)) : null;
      const stco = child(stbl, "stco"), co64 = child(stbl, "co64");
      const nChunks = u32((stco || co64).start + 4);
      const chunkAt = c => stco ? u32(stco.start + 8 + 4 * c) : dv.getUint32(co64.start + 8 + 8 * c) * 4294967296 + dv.getUint32(co64.start + 12 + 8 * c);
      const stsc = child(stbl, "stsc");
      const runs = Array.from({ length: u32(stsc.start + 4) }, (_, e) => [u32(stsc.start + 8 + 12 * e) - 1, u32(stsc.start + 12 + 12 * e)]);
      const frames = [];
      let i = 0;
      for (let c = 0, r = 0; c < nChunks && i < count; c++) {
        while (r + 1 < runs.length && runs[r + 1][0] <= c) r++;
        let at = chunkAt(c);
        for (let k = 0; k < runs[r][1] && i < count; k++, i++) {
          const n = size(i);
          if (at + n > b.length) return null;
          frames.push({ t: (dts[i] + cts[i]) / timescale, key: sync ? sync.has(i) : true, data: b.subarray(at, at + n) });
          at += n;
        }
      }
      const tmin = Math.min(...frames.map(f => f.t));
      for (const f of frames) f.t -= tmin;
      return { codec: "mp4-avc", width, height, defaultDuration: 0, codecPrivate: b.slice(avcC.start, avcC.end), frames };
    }
    return null;
  }

  function decoderConfig(m) {
    if (m.codec === "mp4-avc") {
      const c = m.codecPrivate, hex = x => x.toString(16).padStart(2, "0");
      return { codec: "avc1." + hex(c[1]) + hex(c[2]) + hex(c[3]), description: c };
    }
    if (m.codec === "V_VP8") return { codec: "vp8" };
    if (m.codec === "V_VP9") return { codec: "vp09.00.41.08" };
    if (m.codec === "V_AV1") {
      const c = { codec: "av01.0.08M.08" };
      if (m.codecPrivate && m.codecPrivate.length > 4) c.description = m.codecPrivate.subarray(4);
      return c;
    }
    return null;
  }

  // ---- H.264 with x264 ---------------------------------------------------

  const FFCORE = "https://cdn.jsdelivr.net/npm/@ffmpeg/core@0.12.10/dist/umd/";

  // The clip's frame rate as a fraction: whole numbers and the NTSC rates
  // as they are, anything else to a thousandth.
  function fraction(fps) {
    for (const base of [24, 30, 48, 60]) {
      if (Math.abs(fps - base * 1000 / 1001) < 0.005) return [base * 1000, 1001];
    }
    if (Math.abs(fps - Math.round(fps)) < 0.01) return [Math.round(fps), 1];
    return [Math.round(fps * 1000), 1000];
  }

  function clipRate(m) {
    if (m.defaultDuration > 0) return 1e9 / m.defaultDuration;
    const d = [];
    const ts = m.frames.map(f => f.t).sort((a, c) => a - c);
    for (let i = 1; i < ts.length; i++) {
      const s = ts[i] - ts[i - 1];
      if (s > 0) d.push(s);
    }
    if (!d.length) return 30;
    d.sort((a, c) => a - c);
    return 1 / d[d.length >> 1];
  }

  // The helper workers, made once: as many as the computer has cores to
  // spare, each with its own ffmpeg.
  let pool = null;
  function getPool() {
    if (pool) return pool;
    const n = Math.max(1, Math.min(8, (self.navigator && navigator.hardwareConcurrency || 4) - 1));
    const url = new URL("movie-worker.js", self.location.href);
    const workers = [];
    let seq = 0;
    const waiting = new Map();
    for (let i = 0; i < n; i++) {
      const w = new Worker(url);
      w.load = 0;
      w.onmessage = ({ data }) => {
        const job = waiting.get(data.id);
        if (!job) return;
        waiting.delete(data.id);
        w.load -= job.weight;
        if (data.error) job.reject(new Error(data.error));
        else job.resolve(data.out);
      };
      w.onerror = e => {
        for (const [id, job] of waiting) if (job.worker === w) { waiting.delete(id); job.reject(new Error(e.message || "a movie helper stopped")); }
      };
      workers.push(w);
    }
    // a job goes to the least busy helper; an encode weighs as much as
    // scaling a GOP's worth of frames
    const run = (msg, transfer, weight = 1) => new Promise((resolve, reject) => {
      let w = workers[0];
      for (const x of workers) if (x.load < w.load) w = x;
      const id = ++seq;
      w.load += weight;
      waiting.set(id, { resolve, reject, weight, worker: w });
      w.postMessage({ ...msg, id }, transfer);
    });
    const ready = Promise.all(workers.map(w => new Promise((resolve, reject) => {
      const id = ++seq;
      waiting.set(id, { resolve, reject, weight: 0, worker: w });
      w.postMessage({ t: "init", id, ffUrl: self.VN3DS_FFCORE || FFCORE });
    })));
    pool = { n, run, ready, busy: () => waiting.size };
    return pool;
  }

  function y4m(frames, w, h, fpsNum, fpsDen) {
    const head = new TextEncoder().encode(`YUV4MPEG2 W${w} H${h} F${fpsNum}:${fpsDen} Ip A1:1 C420jpeg\n`);
    const tag = new TextEncoder().encode("FRAME\n");
    const size = w * h * 3 / 2;
    const out = new Uint8Array(head.length + frames.length * (tag.length + size));
    out.set(head, 0);
    let at = head.length;
    for (const f of frames) {
      out.set(tag, at); at += tag.length;
      out.set(f, at); at += size;
    }
    return out;
  }

  async function encodeMovie(bytes, ext, w, h, fpsCap, kbps, gopSeconds, maxSeconds, profile, level, preset) {
    if (typeof VideoDecoder === "undefined" || typeof Worker === "undefined") return null;
    const b = bytes instanceof Uint8Array ? bytes : new Uint8Array(bytes);
    let m;
    try {
      if (/^\.(webm|mkv)$/i.test(ext || "")) m = demuxWebM(b);
      else if (/^\.(mp4|m4v|mov)$/i.test(ext || "")) m = demuxMP4(b);
      else return null;
    } catch (e) { return null; }
    if (!m || !m.frames.length || !m.frames[0].key) return null;
    const dcfg = decoderConfig(m);
    if (!dcfg) return null;
    // decoded in software where possible: a hardware decoder's frames live
    // on the graphics chip, and copying them out isn't always possible
    try {
      const soft = { ...dcfg, hardwareAcceleration: "prefer-software" };
      if ((await VideoDecoder.isConfigSupported(soft)).supported) Object.assign(dcfg, soft);
      else if (!(await VideoDecoder.isConfigSupported(dcfg)).supported) return null;
    } catch (e) { return null; }
    let P;
    try { P = getPool(); await P.ready; } catch (e) { return null; }

    let fps = clipRate(m);
    if (fps > fpsCap) fps = fpsCap;
    const [fpsNum, fpsDen] = fraction(fps);
    fps = fpsNum / fpsDen;
    const gop = Math.max(1, Math.round(fps * (gopSeconds || 4)));
    let t0 = Infinity, tLast = -Infinity;
    for (const f of m.frames) { t0 = Math.min(t0, f.t); tLast = Math.max(tLast, f.t); }
    let end = tLast - t0 + (m.defaultDuration > 0 ? m.defaultDuration / 1e9 : 1 / clipRate(m));
    if (maxSeconds) end = Math.min(end, maxSeconds);
    const total = Math.max(1, Math.round(end * fps));
    // vnpack's x264 settings (assets.py, encode_cvh)
    const x264 = `bframes=0:ref=3:keyint=${gop}:min-keyint=${Math.max(1, gop >> 2)}:scenecut=40:` +
      "open-gop=0:slices=1:sliced-threads=0:aud=0:annexb=1:nal-hrd=none:force-cfr=1";
    const args = ["-c:v", "libx264", "-profile:v", profile || "main", "-level:v", level || "3.0",
                  "-preset", preset || "slower", "-b:v", Math.round(kbps) + "k", "-x264-params", x264];
    const kernel = self.VN3DS_SCALER || "lanczos3";

    let failed = null;
    const slots = new Array(total);      // promise of each output frame (I420 w x h)
    const segments = [];                 // promise of each GOP's Annex B
    let slot = 0;
    let held = null;                     // the newest decoded frame
    let scaling = 0;

    function closeSegment(s) {
      const from = s * gop, to = Math.min(total, from + gop);
      segments[s] = Promise.all(slots.slice(from, to)).then(frames => {
        for (let i = from; i < to; i++) slots[i] = null;   // (memory)
        const data = y4m(frames, w, h, fpsNum, fpsDen);
        return P.run({ t: "encode", y4m: data, args }, [data.buffer], to - from);
      });
      segments[s].catch(e => { failed = failed || e; });
    }

    // Output frames are every 1/fps from the start; each takes the source
    // frame shown at that moment (as ffmpeg's fps filter: drops at a lower
    // rate, repeats across gaps). A source frame no output frame uses
    // isn't scaled.
    async function emitUpTo(tEnd, frame) {
      let small = null;
      while (slot < total && (slot + 0.5) / fps <= tEnd) {
        if (!small && !frame.format) {
          // a frame only the graphics chip holds: scaled by the browser
          small = Promise.resolve(onCanvas(frame, w, h));
        }
        if (!small) {
          const r = frame.visibleRect;
          const buf = new Uint8Array(frame.allocationSize({ rect: r }));
          const layout = (await frame.copyTo(buf, { rect: r })).map(p => ({ offset: p.offset, stride: p.stride }));
          scaling++;
          small = P.run({ t: "scale", buf, layout, format: frame.format, fw: r.width, fh: r.height, w, h, kernel }, [buf.buffer])
            .finally(() => { scaling--; });
          small.catch(() => {});   // (the GOP's encode reports it)
        }
        slots[slot] = small;
        slot++;
        if (slot % gop === 0 || slot === total) closeSegment((slot - 1) / gop | 0);
      }
    }

    let chain = Promise.resolve();
    let queued = 0;
    const decoder = new VideoDecoder({
      output: frame => {
        queued++;
        chain = chain.then(async () => {
          const t = frame.timestamp / 1e6;
          if (held && !failed) await emitUpTo(t, held);
          if (held) held.close();
          held = frame;
          queued--;
        }).catch(e => { failed = failed || e; queued--; });
      },
      error: e => { failed = failed || e; },
    });
    decoder.configure(dcfg);
    const settle = () => new Promise(r => setTimeout(r, 1));
    for (const f of m.frames) {
      if (failed) break;
      decoder.decode(new EncodedVideoChunk({ type: f.key ? "key" : "delta", timestamp: Math.round((f.t - t0) * 1e6), data: f.data }));
      // a few frames ahead of the helpers, and at most a few GOPs waiting
      // for x264: the memory stays small for clips of any length
      while (!failed && (decoder.decodeQueueSize > 4 || queued > 4 || scaling > 2 * P.n ||
             segments.length - (slot / gop | 0) > 0 && P.busy() > 3 * P.n)) await settle();
    }
    try { await decoder.flush(); } catch (e) { failed = failed || e; }
    await chain;
    if (held) {
      if (!failed) {
        try { await emitUpTo(Infinity, held); } catch (e) { failed = failed || e; }
      }
      held.close();
    }
    decoder.close();
    if (!failed && slot < total) failed = new Error("the movie ended early");
    let parts;
    try { parts = await Promise.all(segments); } catch (e) { failed = failed || e; }
    if (failed) throw failed;

    let size = 0;
    for (const p of parts) size += p.length;
    const annexb = new Uint8Array(size);
    let at = 0;
    for (const p of parts) { annexb.set(p, at); at += p.length; }
    const first = await decodeFirst(annexb, w, h);
    return { annexb, first, fpsNum, fpsDen };
  }

  // A frame scaled by the browser (drawImage), I420: for frames that can't
  // be copied out (format null). RGB to YUV as ffmpeg does by default
  // (BT.601, limited range).
  let fallback = null;
  function onCanvas(frame, w, h) {
    if (!fallback || fallback.canvas.width !== w || fallback.canvas.height !== h) {
      const canvas = new OffscreenCanvas(w, h);
      fallback = { canvas, ctx: canvas.getContext("2d", { willReadFrequently: true }) };
      fallback.ctx.imageSmoothingQuality = "high";
    }
    fallback.ctx.drawImage(frame, 0, 0, w, h);
    const px = fallback.ctx.getImageData(0, 0, w, h).data;
    const out = new Uint8Array(w * h * 3 / 2);
    const cw = w >> 1, uAt = w * h, vAt = uAt + cw * (h >> 1);
    for (let y = 0; y < h; y++) {
      for (let x = 0; x < w; x++) {
        const i = (y * w + x) * 4;
        out[y * w + x] = Math.round(16 + (65.738 * px[i] + 129.057 * px[i + 1] + 25.064 * px[i + 2]) / 256);
      }
    }
    for (let y = 0; y < h >> 1; y++) {
      for (let x = 0; x < cw; x++) {
        let r = 0, g = 0, b = 0;
        for (const [dx, dy] of [[0, 0], [1, 0], [0, 1], [1, 1]]) {
          const i = ((2 * y + dy) * w + 2 * x + dx) * 4;
          r += px[i]; g += px[i + 1]; b += px[i + 2];
        }
        r /= 4; g /= 4; b /= 4;
        out[uAt + y * cw + x] = Math.round(128 + (-37.945 * r - 74.494 * g + 112.439 * b) / 256);
        out[vAt + y * cw + x] = Math.round(128 + (112.439 * r - 94.154 * g - 18.285 * b) / 256);
      }
    }
    return out;
  }

  // The first frame as the 3DS's decoder will show it, RGB: decoded with
  // VideoDecoder (null when this browser can't, and vnpack decodes it).
  async function decodeFirst(annexb, w, h) {
    try {
      let sps = null, endOfFirst = annexb.length;
      let seenSlice = false;
      for (let i = 0; i + 3 < annexb.length; i++) {
        if (annexb[i] === 0 && annexb[i + 1] === 0 && annexb[i + 2] === 1) {
          const t = annexb[i + 3] & 31;
          if (t === 7 && !sps) sps = annexb.subarray(i + 4, i + 7);
          if (t === 1 || t === 5) {
            if (seenSlice && (annexb[i + 4] & 0x80)) { endOfFirst = i; break; }
            seenSlice = true;
          }
        }
      }
      if (!sps) return null;
      const hex = x => x.toString(16).padStart(2, "0");
      const codec = "avc1." + hex(sps[0]) + hex(sps[1]) + hex(sps[2]);
      let got = null;
      const d = new VideoDecoder({ output: f => { if (got) f.close(); else got = f; }, error: () => {} });
      d.configure({ codec, codedWidth: w, codedHeight: h, optimizeForLatency: true });
      d.decode(new EncodedVideoChunk({ type: "key", timestamp: 0, data: annexb.subarray(0, endOfFirst) }));
      await d.flush();
      d.close();
      if (!got) return null;
      const canvas = new OffscreenCanvas(w, h);
      const ctx = canvas.getContext("2d");
      ctx.drawImage(got, 0, 0, w, h);
      got.close();
      const px = ctx.getImageData(0, 0, w, h).data;
      const rgb = new Uint8Array(w * h * 3);
      for (let i = 0, j = 0; i < px.length; i += 4, j += 3) {
        rgb[j] = px[i]; rgb[j + 1] = px[i + 1]; rgb[j + 2] = px[i + 2];
      }
      return rgb;
    } catch (e) {
      return null;
    }
  }

  // ---- scaling --------------------------------------------------------
  //
  // A browser's own scaling (drawImage, createImageBitmap) is close to
  // bilinear: from 1080p down to 240 lines it loses detail that ffmpeg's
  // Lanczos keeps (VMAF 92.7 at any bitrate, against x264's 92.9 at 240 kbps).
  // So the decoded YUV planes are resampled here, separably, with the
  // kernel below; the frame never goes through RGB.

  const KERNELS = {
    box: { support: 0.5, f: x => (Math.abs(x) < 0.5 ? 1 : Math.abs(x) === 0.5 ? 0.5 : 0) },
    triangle: { support: 1, f: x => Math.max(0, 1 - Math.abs(x)) },
    lanczos2: { support: 2, f: x => lanczos(x, 2) },
    lanczos3: { support: 3, f: x => lanczos(x, 3) },
  };
  function lanczos(x, a) {
    if (x === 0) return 1;
    if (Math.abs(x) >= a) return 0;
    const p = Math.PI * x;
    return a * Math.sin(p) * Math.sin(p / a) / (p * p);
  }

  const tables = new Map();
  // Weights for inN -> outN samples: {start[o], count[o], w (count[o] each, flat)}.
  function weights(inN, outN, kname) {
    const key = inN + ":" + outN + ":" + kname;
    if (tables.has(key)) return tables.get(key);
    const k = KERNELS[kname];
    const scale = inN / outN, stretch = Math.max(1, scale);
    const support = k.support * stretch;
    const start = new Int32Array(outN), count = new Int32Array(outN), at = new Int32Array(outN);
    const all = [];
    for (let o = 0; o < outN; o++) {
      const c = (o + 0.5) * scale;
      const lo = Math.max(0, Math.floor(c - support)), hi = Math.min(inN - 1, Math.ceil(c + support));
      const ws = [];
      let sum = 0;
      for (let i = lo; i <= hi; i++) {
        const v = k.f((i + 0.5 - c) / stretch);
        ws.push(v);
        sum += v;
      }
      start[o] = lo; count[o] = ws.length; at[o] = all.length;
      for (const v of ws) all.push(sum ? v / sum : 0);
    }
    const t = { start, count, at, w: new Float32Array(all) };
    tables.set(key, t);
    return t;
  }

  // One plane: src (stride sStride, sw x sh, step 1 or 2 for interleaved
  // chroma) -> dst (dw x dh, packed). While the plane is more than twice
  // the size wanted it is first halved by averaging 2x2 blocks (cheap, and
  // the kernel then spans fewer samples: half the time, no visible change).
  function resample(src, sOff, sStride, step, sw, sh, dst, dOff, dw, dh, kname) {
    while (kname !== "box" && sw >= dw * 4 && sh >= dh * 4) {
      const hw = sw >> 1, hh = sh >> 1, half = new Uint8Array(hw * hh);
      for (let y = 0; y < hh; y++) {
        let p = sOff + 2 * y * sStride, q = p + sStride, d = y * hw;
        for (let x = 0; x < hw; x++, p += 2 * step, q += 2 * step) {
          half[d++] = (src[p] + src[p + step] + src[q] + src[q + step] + 2) >> 2;
        }
      }
      src = half; sOff = 0; sStride = hw; step = 1; sw = hw; sh = hh;
    }
    const H = weights(sw, dw, kname), V = weights(sh, dh, kname);
    // rows first, only those some output row uses
    const mid = new Float32Array(dw * sh);
    const rowLo = V.start[0], rowHi = V.start[dh - 1] + V.count[dh - 1];
    const Hs = H.start, Hc = H.count, Ha = H.at, Hw = H.w;
    for (let y = rowLo; y < rowHi; y++) {
      const row = sOff + y * sStride, mrow = y * dw;
      for (let o = 0; o < dw; o++) {
        let acc = 0, p = row + Hs[o] * step, wi = Ha[o];
        for (let n = Hc[o]; n > 0; n--, p += step) acc += src[p] * Hw[wi++];
        mid[mrow + o] = acc;
      }
    }
    const acc = new Float32Array(dw);
    for (let o = 0; o < dh; o++) {
      acc.fill(0);
      const s0 = V.start[o], n = V.count[o], w0 = V.at[o], drow = dOff + o * dw;
      for (let k = 0; k < n; k++) {
        const wk = V.w[w0 + k], m0 = (s0 + k) * dw;
        for (let x = 0; x < dw; x++) acc[x] += mid[m0 + x] * wk;
      }
      for (let x = 0; x < dw; x++) {
        const v = acc[x];
        dst[drow + x] = v <= 0 ? 0 : v >= 255 ? 255 : (v + 0.5) | 0;
      }
    }
  }

  // A frame's planes (as VideoFrame.copyTo wrote them) at w x h, I420.
  // 4:2:0, 4:2:2 and 4:4:4, 8 to 12 bits, planar or NV12.
  function scalePlanes(buf, layout, format, fw, fh, w, h, kname) {
    const out = new Uint8Array(w * h * 3 / 2);
    const m = /^I4(20|22|44)A?(P(10|12))?$/.exec(format || "");
    if (format !== "NV12" && !m) throw new Error("frames in " + format + " can't be scaled here");
    const sub = format === "NV12" || m[1] === "20" ? [2, 2] : m[1] === "22" ? [2, 1] : [1, 1];
    const cw = Math.ceil(fw / sub[0]), ch = Math.ceil(fh / sub[1]);
    const bits = m && m[3] ? +m[3] : 8;
    // high bit depths: to 8 bits first (the 3DS shows 8)
    function plane(i, pw, ph) {
      if (bits === 8) return [buf, layout[i].offset, layout[i].stride];
      const shift = bits - 8, half = 1 << (shift - 1);
      const src = new Uint16Array(buf.buffer, buf.byteOffset + layout[i].offset);
      const step = layout[i].stride >> 1;
      const p8 = new Uint8Array(pw * ph);
      for (let y = 0; y < ph; y++) {
        for (let x = 0, a = y * step, d = y * pw; x < pw; x++) {
          const v = (src[a + x] + half) >> shift;
          p8[d + x] = v > 255 ? 255 : v;
        }
      }
      return [p8, 0, pw];
    }
    const [yb, yo, ys] = plane(0, fw, fh);
    resample(yb, yo, ys, 1, fw, fh, out, 0, w, h, kname);
    if (format === "NV12") {
      resample(buf, layout[1].offset, layout[1].stride, 2, cw, ch, out, w * h, w >> 1, h >> 1, kname);
      resample(buf, layout[1].offset + 1, layout[1].stride, 2, cw, ch, out, w * h * 5 / 4, w >> 1, h >> 1, kname);
    } else {
      const [ub, uo, us] = plane(1, cw, ch), [vb, vo, vs] = plane(2, cw, ch);
      resample(ub, uo, us, 1, cw, ch, out, w * h, w >> 1, h >> 1, kname);
      resample(vb, vo, vs, 1, cw, ch, out, w * h * 5 / 4, w >> 1, h >> 1, kname);
    }
    return out;
  }

  // For vnpack (tools/vnpack/webmovies.py): movies started ahead of their
  // turn run side by side; the call with wait=true collects one (a promise
  // of encodeMovie's result, or null: ffmpeg does it).
  const started = new Map();
  function movie(key, bytes, ext, w, h, fpsCap, kbps, gopSeconds, maxSeconds, profile, level, preset, wait) {
    if (self.VN3DS_DEBUG_MOVIES) console.info(`movie ${key} wait=${wait} bytes=${bytes ? bytes.length : 0}`);
    let p = started.get(key);
    if (!p) {
      if (!bytes) return wait ? Promise.resolve(null) : undefined;
      const T = performance.now();
      const enc = () => encodeMovie(bytes, ext, w, h, fpsCap, kbps, gopSeconds, maxSeconds, profile, level, preset);
      // tried twice: a helper's ffmpeg can fail on its own (it is replaced)
      p = enc().catch(e => {
        console.warn(`movie ${key}: ${e && e.message || e}; trying again`);
        return enc();
      })
        .then(r => {
          if (self.VN3DS_DEBUG_MOVIES) console.info(`movie ${key}: ${r ? r.annexb.length + " bytes" : "left to ffmpeg"} in ${Math.round(performance.now() - T)} ms`);
          return r;
        })
        .catch(e => { console.warn(`movie ${key}: ${e && e.message || e}`); return null; });
      started.set(key, p);
    }
    if (!wait) return undefined;
    started.delete(key);
    return p;
  }

  self.vn3dsMovie = movie;
  self.vn3dsEncodeMovie = encodeMovie;
  self.vn3dsScalePlanes = scalePlanes;
  self.vn3dsDemuxWebM = demuxWebM;
})();

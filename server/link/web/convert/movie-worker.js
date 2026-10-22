// One of h264.js's helpers: scales decoded frames and encodes stretches of
// a movie with x264 (ffmpeg.wasm), several of these side by side.
//
//   in:  {t:"scale", id, buf, layout, format, fw, fh, w, h, kernel}  (a frame's YUV planes)
//        {t:"encode", id, y4m, args}                                (a GOP-long stretch)
//   out: {id, out: Uint8Array}  I420 w x h, or the Annex B stream
//        {id, error}

importScripts("h264.js");

let ffUrl = null, ffModule = null;

function newCore() {
  const m = {
    mainScriptUrlOrBlob: ffUrl + "ffmpeg-core.js#" + btoa(JSON.stringify({ wasmURL: ffUrl + "ffmpeg-core.wasm" })),
    instantiateWasm(imports, receive) {
      const inst = new WebAssembly.Instance(ffModule, imports);
      receive(inst, ffModule);
      return inst.exports;
    },
  };
  createFFmpegCore(m);
  return m;
}

// x264's two passes. One ffmpeg instance is kept and reset between runs
// (a new one per run runs out of memory over a long game: thousands of
// GOPs), and replaced every RECYCLE encodes: it slowly fills up, until x264
// fails with "memory access out of bounds". A run that crashes is tried
// once more on a fresh instance.
const RECYCLE = 20;
let core = null, uses = 0;

function run(args) {
  if (!core) core = newCore();
  const err = [];
  core.setLogger(({ type, message }) => { if (type !== "stdout") err.push(message); });
  let rc;
  try {
    rc = core.exec(...args);
    core.reset();
  } catch (e) {
    core = null;
    throw e;
  }
  if (rc !== 0) throw new Error("x264: " + err.join(" ").slice(-200));
}

function clean(names) {
  for (const n of names) try { core && core.FS.unlink(n); } catch (e) { /* not there */ }
}

function encode(y4m, args) {
  if (++uses > RECYCLE) { core = null; uses = 1; }
  try {
    return encodeOnce(y4m, args);
  } catch (e) {
    if (!(e instanceof WebAssembly.RuntimeError)) throw e;
    core = null; uses = 1;
    return encodeOnce(y4m, args);
  }
}

function encodeOnce(y4m, args) {
  try {
    if (!core) core = newCore();
    core.FS.writeFile("/in.y4m", y4m);
    const base = ["-v", "error", "-y", "-f", "yuv4mpegpipe", "-i", "/in.y4m", "-an", ...args, "-passlogfile", "/x264"];
    run([...base, "-pass", "1", "-f", "null", "/dev/null"]);
    run([...base, "-pass", "2", "-f", "h264", "/out.h264"]);
    return core.FS.readFile("/out.h264");
  } finally {
    if (core) clean(["/in.y4m", "/out.h264", ...core.FS.readdir("/").filter(n => n.startsWith("x264")).map(n => "/" + n)]);
  }
}

onmessage = async ({ data: m }) => {
  try {
    if (m.t === "init") {
      ffUrl = m.ffUrl;
      importScripts(ffUrl + "ffmpeg-core.js");
      ffModule = await WebAssembly.compileStreaming(fetch(ffUrl + "ffmpeg-core.wasm"));
      postMessage({ id: m.id, out: null });
    } else if (m.t === "scale") {
      const out = self.vn3dsScalePlanes(m.buf, m.layout, m.format, m.fw, m.fh, m.w, m.h, m.kernel);
      postMessage({ id: m.id, out }, [out.buffer]);
    } else if (m.t === "encode") {
      const out = encode(m.y4m, m.args);
      postMessage({ id: m.id, out }, [out.buffer]);
    }
  } catch (e) {
    postMessage({ id: m.id, error: String(e && e.message || e) });
  }
};

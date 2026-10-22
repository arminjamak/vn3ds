// Converts a Ren'Py game for the 3DS inside the browser: vnpack (the same
// Python as vn3ds-port) on Pyodide, with ffmpeg.wasm for sound and movies.
// See vn3ds_browser.py for what stands in for what. Driven by
// ../vn3ds-convert.js:
//
//   in:  {file: File}                      the game (.zip, .apk, .rpa, ...)
//   out: {t:"progress", kind, data}        as the conversion goes
//        {t:"loading", what}               the first time: downloading the tools
//        {t:"done", id, files:[{path, size}]}   (the files stay here)
//        {t:"error", message}
//   in:  {t:"read", path, req}  ->  out: {t:"file", req, data:ArrayBuffer}
//
// A classic worker: Pyodide and the ffmpeg core both load with importScripts.

const PYODIDE = "https://cdn.jsdelivr.net/pyodide/v0.27.7/full/";
const FFCORE = "https://cdn.jsdelivr.net/npm/@ffmpeg/core@0.12.10/dist/umd/";

let ready = null;
let py = null, core = null;

function mkdirs(fs, path) {
  let cur = "";
  for (const part of path.split("/").slice(0, -1)) {
    if (!part) continue;
    cur += "/" + part;
    try { fs.mkdir(cur); } catch (e) { /* there */ }
  }
}

const isFile = (fs, p) => {
  try { return fs.isFile(fs.stat(p).mode); } catch (e) { return false; }
};

// subprocess.run(["ffmpeg", ...]) from Python lands here (synchronously):
// inputs are copied into ffmpeg's file system, outputs back afterwards;
// "-" as the input (with stdin bytes) or as the last argument (stdout)
// becomes a file.
function ffExec(probe, argsProxy, stdinProxy) {
  const args = argsProxy.toJs();
  argsProxy.destroy();
  const stdin = stdinProxy ? stdinProxy.toJs() : null;
  if (stdinProxy && stdinProxy.destroy) stdinProxy.destroy();
  // libopus in ffmpeg.wasm overruns its stack on much stereo music at
  // complexity 5 and up (every release so far): 4 here, a little less
  // efficient at the same bitrate than the computer's 10
  const at = args.indexOf("libopus");
  if (at >= 0) {
    const cl = args.indexOf("-compression_level");
    if (cl >= 0) args.splice(cl, 2);
    args.splice(at + 1, 0, "-compression_level", "4");
  }
  // a fresh instance every so often: a long-lived one slowly fills up
  if (!core || ++coreRuns > 40) newCoreSync();
  try {
    return ffOnce(probe, args.slice(), stdin);
  } catch (e) {
    // a crash leaves the instance unusable: a fresh one, and one more try
    if (!(e instanceof WebAssembly.RuntimeError)) throw e;
    newCoreSync();
    try {
      return ffOnce(probe, args.slice(), stdin);
    } catch (e2) {
      core = null;
      if (!(e2 instanceof WebAssembly.RuntimeError)) throw e2;
      // a failed run, as ffmpeg on a computer would end: vnpack skips
      // this one file with a warning instead of losing the whole game
      return { rc: 1, stdout: new Uint8Array(), stderr: "ffmpeg crashed: " + e2.message };
    }
  }
}

function ffOnce(probe, args, stdin) {
  // This ffmpeg.wasm build crashes when told to resample stereo (-ar);
  // libopus codes at 48 kHz whatever it is given, so for it -ar can go.
  const ar = args.indexOf("-ar");
  if (ar >= 0 && args.includes("libopus")) args.splice(ar, 2);
  const P = py.FS, C = core.FS;
  const copied = [], outs = [];
  let passlog = null;
  for (let i = 0; i < args.length; i++) {
    const a = args[i];
    const afterI = args[i - 1] === "-i";
    if (afterI && (a === "-" || a.startsWith("pipe:"))) {
      C.writeFile("/tmp/stdin.bin", stdin || new Uint8Array());
      args[i] = "/tmp/stdin.bin";
      copied.push("/tmp/stdin.bin");
    } else if (i === args.length - 1 && !probe && (a === "-" || a === "pipe:1" || a === "pipe:")) {
      args[i] = "/tmp/stdout.bin";
      outs.push(["-", "/tmp/stdout.bin"]);
    } else if (args[i - 1] === "-passlogfile") {
      // x264's two passes are two runs: its statistics files go across
      passlog = a;
      const dir = a.slice(0, a.lastIndexOf("/")) || "/";
      mkdirs(C, a);
      for (const n of P.readdir(dir)) {
        const p = dir + "/" + n;
        if (p.startsWith(a) && isFile(P, p)) { C.writeFile(p, P.readFile(p)); copied.push(p); }
      }
    } else if (a.startsWith("/")) {
      if (isFile(P, a)) {
        mkdirs(C, a);
        C.writeFile(a, P.readFile(a));
        copied.push(a);
      } else if (!afterI && i === args.length - 1) {
        mkdirs(C, a);
        outs.push([a, a]);
      }
    }
  }
  const out = [], err = [];
  core.setLogger(({ type, message }) => (type === "stdout" ? out : err).push(message));
  let rc;
  if (self.VN3DS_DEBUG) console.info((probe ? "ffprobe " : "ffmpeg ") + args.join(" "));
  try {
    rc = probe ? core.ffprobe(...args) : core.exec(...args);
    core.reset();   // (ready for the next run)
  } catch (e) {
    if (self.VN3DS_DEBUG) console.info("ffmpeg crashed: " + e);
    throw e;
  }
  let stdout = new TextEncoder().encode(out.join("\n") + (out.length ? "\n" : ""));
  for (const [dst, src] of outs) {
    if (!isFile(C, src)) continue;
    const data = C.readFile(src);
    C.unlink(src);
    if (dst === "-") stdout = data;
    else {
      mkdirs(P, dst);
      P.writeFile(dst, data);
    }
  }
  if (passlog) {
    const dir = passlog.slice(0, passlog.lastIndexOf("/")) || "/";
    for (const n of C.readdir(dir)) {
      const p = dir + "/" + n;
      if (p.startsWith(passlog) && isFile(C, p)) P.writeFile(p, C.readFile(p));
    }
  }
  for (const p of copied) try { C.unlink(p); } catch (e) {}
  return { rc, stdout, stderr: err.join("\n") };
}

// A new ffmpeg instance, made synchronously from the compiled code (the
// conversion calls ffmpeg synchronously, so a replacement can't be waited for).
let ffModule = null, coreRuns = 0;
function newCoreSync() {
  coreRuns = 0;
  const m = {
    // (the core reads where its .wasm is from its script URL's fragment)
    mainScriptUrlOrBlob: FFCORE + "ffmpeg-core.js#" + btoa(JSON.stringify({ wasmURL: FFCORE + "ffmpeg-core.wasm" })),
    instantiateWasm(imports, receive) {
      const inst = new WebAssembly.Instance(ffModule, imports);
      receive(inst, ffModule);
      return inst.exports;
    },
  };
  createFFmpegCore(m);
  if (typeof m.exec !== "function") throw new Error("ffmpeg didn't start");
  core = m;
}

async function load() {
  postMessage({ t: "loading", what: "Python" });
  importScripts(PYODIDE + "pyodide.js");
  py = await loadPyodide({ indexURL: PYODIDE });
  postMessage({ t: "loading", what: "image tools" });
  await py.loadPackage(["numpy", "pillow"]);
  postMessage({ t: "loading", what: "the converter" });
  const bundle = await (await fetch(new URL("vnpack.zip", self.location.href))).arrayBuffer();
  py.unpackArchive(bundle, "zip", { extractDir: "/vn" });
  postMessage({ t: "loading", what: "sound and movie tools" });
  importScripts(FFCORE + "ffmpeg-core.js");
  ffModule = await WebAssembly.compileStreaming(fetch(FFCORE + "ffmpeg-core.wasm"));
  py.runPython(`
import sys
sys.path[:0] = ["/vn", "/vn/tools", "/vn/tools/third_party/unrpyc"]
import vn3ds_browser
`);
  py.globals.get("vn3ds_browser").ff_exec = ffExec;
  importScripts("h264.js");   // movies: WebCodecs decoding + a pool of x264 workers (vnpack/webmovies.py)
}

let outFiles = new Map();

onmessage = async (ev) => {
  if (ev.data.t === "read") {   // one converted file, for the sender
    try {
      const bytes = py.FS.readFile(outFiles.get(ev.data.path));
      postMessage({ t: "file", req: ev.data.req, data: bytes.buffer }, [bytes.buffer]);
    } catch (e) {
      postMessage({ t: "file", req: ev.data.req, error: String(e) });
    }
    return;
  }
  const { file, debug } = ev.data;
  self.VN3DS_DEBUG = debug;
  try {
    if (!ready) ready = load();
    await ready;
    // the game is read where it is (WORKERFS): nothing is copied into memory first
    try { py.FS.unmount("/in"); } catch (e) {}
    try { py.FS.mkdir("/in"); } catch (e) {}
    py.FS.mount(py.FS.filesystems.WORKERFS, { files: [file] }, "/in");
    const report = (kind, data) => {
      postMessage({ t: "progress", kind, data: data.toJs ? data.toJs({ dict_converter: Object.fromEntries }) : data });
      if (data.destroy) data.destroy();
    };
    const vb = py.globals.get("vn3ds_browser");
    outFiles = new Map();
    py.runPython(`import shutil; shutil.rmtree("/out", ignore_errors=True); shutil.rmtree("/tmp/work", ignore_errors=True)`);
    // With JSPI (Chrome) Python can wait for the movie pool's promises;
    // without it (Safari for now) ffmpeg.wasm makes the movies in line.
    const game = typeof WebAssembly.Suspending === "function" && vb.convert.callPromising
      ? await vb.convert.callPromising("/in/" + file.name, "/out", report)
      : vb.convert("/in/" + file.name, "/out", report);
    if (self.VN3DS_DEBUG) try { console.info(new TextDecoder().decode(py.FS.readFile(game + "/port-report.txt"))); } catch (e) {}
    // the files stay here; the page reads them one at a time while sending,
    // so a big game is never all in the page's memory at once
    outFiles = new Map(vb.files_of(game).toJs().map(([remote, local]) => [remote, local]));
    const files = [...outFiles].map(([path, local]) => ({ path, size: py.FS.stat(local).size }));
    postMessage({ t: "done", id: game.split("/").pop(), files });
  } catch (e) {
    const msg = String(e && e.message || e);
    // a Python error's last line says what went wrong
    const last = msg.trim().split("\n").filter(Boolean).pop() || msg;
    postMessage({ t: "error", message: last.replace(/^\w+Error: /, "") });
  }
};

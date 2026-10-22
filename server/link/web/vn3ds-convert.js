// Converts a game in the browser (convert/worker.js) and hands back the
// files for vn3ds-send.js.
//
//   const { id, files } = await convertGame(file, (kind, data) => ...);
//
// kind: "loading" {what} (the first time: Python, ffmpeg and the converter
// are downloaded, ~50 MB, then cached), "phase" {title}, "step" {id, state,
// detail, done, total}, "log" {text}.

let worker = null;
const reqs = new Map();
let nextReq = 0;

// The converted files stay in the worker; data() fetches one when the
// sender needs it, so a big game is never all in the page's memory.
function readOut(path) {
  return new Promise((resolve, reject) => {
    const req = ++nextReq;
    reqs.set(req, { resolve, reject });
    worker.postMessage({ t: "read", path, req });
  });
}

export function convertGame(file, onProgress = () => {}, base = import.meta.url) {
  if (!worker) worker = new Worker(new URL("convert/worker.js", base));
  return new Promise((resolve, reject) => {
    worker.onmessage = ({ data: m }) => {
      if (m.t === "loading") onProgress("loading", { what: m.what });
      else if (m.t === "progress") onProgress(m.kind, m.data);
      else if (m.t === "done") resolve({ id: m.id, files: m.files.map(f => ({ path: f.path, size: f.size, data: () => readOut(f.path) })) });
      else if (m.t === "error") reject(new Error(m.message));
      else if (m.t === "file") {
        const r = reqs.get(m.req);
        reqs.delete(m.req);
        if (r) m.error ? r.reject(new Error(m.error)) : r.resolve(new Uint8Array(m.data));
      }
    };
    worker.onerror = e => {
      worker = null;
      reject(new Error(e.message || "The converter stopped"));
    };
    worker.postMessage({ file, debug: !!globalThis.VN3DS_DEBUG });
  });
}

// A download through the vn3ds link (itch.io pages are resolved there):
// the browser can't read another site's files by itself.
export async function fetchGame(url, link, onProgress = () => {}) {
  const r = await fetch(link + "/fetch?url=" + encodeURIComponent(url));
  if (!r.ok) {
    let msg = `The download failed (${r.status})`;
    try { msg = (await r.json()).error || msg; } catch (e) {}
    throw new Error(msg);
  }
  const name = decodeURIComponent(r.headers.get("X-File-Name") || "game.zip");
  const total = Number(r.headers.get("Content-Length") || 0);
  // to the browser's own disk (OPFS) where it can, so a game of several GB
  // never has to fit in memory; in memory otherwise
  let sink = null, handle = null;
  try {
    const dir = await navigator.storage.getDirectory();
    try { await dir.removeEntry("download"); } catch (e) {}
    handle = await dir.getFileHandle("download", { create: true });
    sink = await handle.createWritable();
  } catch (e) { sink = null; }
  const reader = r.body.getReader();
  const parts = [];
  let done = 0;
  const t0 = Date.now();
  for (;;) {
    const { done: end, value } = await reader.read();
    if (end) break;
    if (sink) await sink.write(value); else parts.push(value);
    done += value.length;
    onProgress({ done, total, rate: done / Math.max(0.001, (Date.now() - t0) / 1000) });
  }
  if (sink) {
    await sink.close();
    return new File([await handle.getFile()], name);
  }
  return new File(parts, name);
}

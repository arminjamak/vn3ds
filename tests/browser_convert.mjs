// Runs the page (server/link/web/index.html) in headless Chrome: drops a
// game file on it and waits until it says Done, printing what it showed
// along the way, with timings. Driven over the DevTools protocol (Node's
// own WebSocket), so nothing needs installing.
//
//   node tests/browser_convert.mjs http://127.0.0.1:8787 <file served by the relay, e.g. _test_game.zip> [seconds]
//
// The page must be served with ?link= pointing at a relay that a receiver
// (vn3ds-host --receive) is linked to. Exit code 0 when the page says Done.
import { spawn } from "node:child_process";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const [base, file, secs = "1800"] = process.argv.slice(2);
const CHROME = process.env.CHROME || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const profile = mkdtempSync(join(tmpdir(), "vn3ds-chrome-"));
const port = 9300 + Math.floor(Math.random() * 500);
const chrome = spawn(CHROME, ["--headless=new", `--remote-debugging-port=${port}`, `--user-data-dir=${profile}`,
  "--no-first-run", "--disable-background-timer-throttling", "--disable-renderer-backgrounding", "about:blank"],
  { stdio: "ignore" });
const quit = code => { chrome.kill(); try { rmSync(profile, { recursive: true, force: true }); } catch (e) {} process.exit(code); };

let target;
for (let i = 0; i < 100 && !target; i++) {
  try { target = (await (await fetch(`http://127.0.0.1:${port}/json`)).json()).find(t => t.type === "page"); }
  catch (e) { await new Promise(r => setTimeout(r, 100)); }
}
if (!target) { console.log("no Chrome"); quit(2); }
const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise(r => (ws.onopen = r));
let id = 0;
const pending = new Map();
ws.onmessage = ev => {
  const m = JSON.parse(ev.data);
  if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); }
  if (m.method === "Target.attachedToTarget")   // the converter's worker: its console too
    ws.send(JSON.stringify({ id: ++id, method: "Runtime.enable", sessionId: m.params.sessionId }));
  if (m.method === "Runtime.consoleAPICalled" && (m.params.type === "error" || process.env.DEBUG))
    console.log("console:", m.params.args.map(a => a.value ?? a.description).join(" "));
};
const cdp = (method, params = {}) => new Promise(r => { pending.set(++id, r); ws.send(JSON.stringify({ id, method, params })); });
const evaluate = async expr => (await cdp("Runtime.evaluate", { expression: expr, awaitPromise: true, returnByValue: true })).result?.result?.value;

await cdp("Runtime.enable");
await cdp("Target.setAutoAttach", { autoAttach: true, waitForDebuggerOnStart: false, flatten: true });
await cdp("Page.enable");
await cdp("Page.navigate", { url: `${base}/?link=${encodeURIComponent(base)}` });
await new Promise(r => setTimeout(r, 2500));
const t0 = Date.now();
if (process.env.DEBUG) await evaluate("globalThis.VN3DS_DEBUG = true");
const size = await evaluate(`(async () => {
  const b = await (await fetch(${JSON.stringify("/" + file)})).blob();
  const f = new File([b], ${JSON.stringify(file.replace(/^_test_/, ""))});
  const dt = new DataTransfer(); dt.items.add(f);
  window.dispatchEvent(new DragEvent("drop", { dataTransfer: dt, bubbles: true, cancelable: true }));
  return f.size;
})()`);
console.log(`dropped ${file} (${(size / 1e6).toFixed(1)} MB)`);
let last = "";
for (;;) {
  const s = await evaluate(`[document.getElementById("detail").textContent,
    document.getElementById("err").hidden ? "" : document.getElementById("err").textContent]`);
  const t = ((Date.now() - t0) / 1000).toFixed(0);
  if (s && s[0] !== last) { console.log(`${t.padStart(5)} s  ${s[0]}`); last = s[0]; }
  if (s && s[1]) { console.log(`${t.padStart(5)} s  ERROR: ${s[1]}`); quit(1); }
  if (s && s[0].startsWith("Done")) quit(0);
  if (Date.now() - t0 > Number(secs) * 1000) { console.log("timed out"); quit(1); }
  await new Promise(r => setTimeout(r, 500));
}

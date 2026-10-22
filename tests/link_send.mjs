// Sends a ported game folder through a vn3ds link with the page's own
// sender (server/link/web/vn3ds-send.js), for tests/test_link.py.
//
//   node tests/link_send.mjs http://127.0.0.1:8787 ABCD2345 build/syntax-test [near]
//
// Prints one JSON line per event, then {"result": ...} or {"error": ...}.
import { readdirSync, readFileSync, statSync } from "node:fs";
import { basename, join, relative } from "node:path";
import { findNearby, sendGame } from "../server/link/web/vn3ds-send.js";

const [link, code, game, mode] = process.argv.slice(2);
const out = o => console.log(JSON.stringify(o));

function walk(dir) {
  return readdirSync(dir).sort().flatMap(n => {
    const full = join(dir, n);
    return statSync(full).isDirectory() ? walk(full) : [full];
  });
}

// the same files send.py sends (tools/vnpack/send.py: _files_of)
const files = walk(game)
  .filter(f => !((f.endsWith(".part") || f.endsWith(".txt")) && basename(f) !== "port-report.txt") && basename(f) !== "savemap.json")
  .map(f => ({ path: "games/" + basename(game) + "/" + relative(game, f).split("\\").join("/"), size: statSync(f).size, data: () => readFileSync(f) }));

// "engine": also try to replace vn3ds itself (the 3DS must refuse it over the link)
if (mode === "engine") files.push({ path: "vn3ds.3dsx", size: 5, data: () => new TextEncoder().encode("evil!") });

try {
  if (mode === "near") {
    // findNearby asks an outside service for the IPv4 address; locally the relay's own view is used
    globalThis.fetch = (orig => (u, o) => (String(u).includes("ipify") ? Promise.reject(new Error("offline")) : orig(u, o)))(globalThis.fetch);
    out({ near: await findNearby(link) });
    process.exit(0);
  }
  let last = 0;
  const result = await sendGame({
    code, files, link,
    onProgress: (event, info) => {
      if (event !== "bytes" || Date.now() - last > 500) out({ event, ...info });
      if (event === "bytes") last = Date.now();
    },
  });
  out({ result });
  process.exit(0);
} catch (e) {
  out({ error: e.message });
  process.exit(1);
}

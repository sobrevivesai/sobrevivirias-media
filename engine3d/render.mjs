import { chromium } from "playwright";
import http from "http"; import fs from "fs"; import path from "path";
const root = path.resolve("web");
const srv = http.createServer((q, r) => { const f = path.join(root, decodeURIComponent(q.url.split("?")[0])); fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); r.end(); return; } r.writeHead(200); r.end(d); }); }).listen(8124);
const [W, a, b, out] = [+(process.env.W || 810), +process.argv[2], +process.argv[3], process.argv[4] || "frames"];
fs.mkdirSync(out, { recursive: true });
const br = await chromium.launch({ executablePath: "/usr/bin/google-chrome", args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
const p = await br.newPage({ viewport: { width: W, height: Math.round(W * 16 / 9) } });
p.on("pageerror", e => console.log("ERR:", e.message));
await p.goto(`http://localhost:8124/ep.html?w=${W}&${process.env.QS || ""}`); await p.waitForFunction("window.ready", null, { timeout: 120000 });
const t0 = Date.now();
for (let f = a; f <= b; f++) { const fn = `${out}/f${String(f).padStart(4, "0")}.jpg`; if (fs.existsSync(fn)) continue;
  await p.evaluate(f => window.renderFrame(f), f);
  const d = await p.evaluate(() => document.querySelector("canvas").toDataURL("image/jpeg", .94));
  fs.writeFileSync(fn, Buffer.from(d.split(",")[1], "base64"));
  if (f % 50 === 0) console.log("frame", f, ((Date.now() - t0) / 1000).toFixed(0) + "s"); }
console.log("DONE"); await br.close(); srv.close();

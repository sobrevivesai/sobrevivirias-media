import { chromium } from "playwright";
import http from "http"; import fs from "fs"; import path from "path";
const root = path.resolve("web");
const srv = http.createServer((q, r) => { const f = path.join(root, decodeURIComponent(q.url.split("?")[0])); fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); r.end(); return; } r.writeHead(200, { "content-type": f.endsWith(".js") ? "text/javascript" : f.endsWith(".html")?"text/html":"application/octet-stream" }); r.end(d); }); }).listen(8123);
const W = process.argv[2] || 1080, page = process.argv[3] || "proto.html", frames=(process.argv[4]||"0,30").split(",").map(Number), out=process.argv[5]||"test";
const b = await chromium.launch({ executablePath: "/usr/bin/google-chrome", args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
const p = await b.newPage({ viewport: { width: +W, height: Math.round(W * 16 / 9) } });
p.on("console", m => console.log("C:", m.text())); p.on("pageerror", e => console.log("ERR:", e.message));
await p.goto(`http://localhost:8123/${page}?w=${W}&${process.env.QS||""}`); await p.waitForFunction("window.ready", null, { timeout: 120000 });
fs.mkdirSync(out,{recursive:true});
for (const f of frames) { const t = Date.now(); await p.evaluate(f => window.renderFrame(f), f);
  const d = await p.evaluate(() => document.querySelector("canvas").toDataURL("image/jpeg", .92));
  fs.writeFileSync(`${out}/f${String(f).padStart(4,"0")}.jpg`, Buffer.from(d.split(",")[1], "base64")); console.log("frame", f, (Date.now() - t) / 1000, "s"); }
await b.close(); srv.close();

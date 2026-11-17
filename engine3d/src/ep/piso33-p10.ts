// PISO 33 · Parte 10 "EL LABORATORIO" — mundo 3D + tarjetas 2D, cada cuadro es función pura del número de cuadro.
import * as THREE from "three";
import { EffectComposer, RenderPass, EffectPass, ToneMappingEffect, ToneMappingMode, SMAAEffect, SMAAPreset } from "postprocessing";
import { InkPass, NOINK } from "../kit/ink";
import { LensBlur } from "../kit/lensblur";
import { GradeEffect, GRADES } from "../kit/grade";
import { TONE, CHAR, twoTone, untone } from "../kit/shade";
import { cardShade, CARD_K, blobMaterial } from "../kit/cardshade";
import { ctex, rng, jit } from "../kit/paint";
import { Pen, bodyFront, bodySide, FrontOpts, Outfit, INK } from "../toon33";
import { TU, LUCIA, SOLDADO, IBARRA, ZOMBIE } from "../castdefs";

const Q = new URLSearchParams(location.search);
const W = +(Q.get("w") || 720), H = Math.round(W * 16 / 9), FPS = 30;
const renderer = new THREE.WebGLRenderer({ antialias: false, stencil: false, preserveDrawingBuffer: true });
renderer.setSize(W, H); renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
document.body.appendChild(renderer.domElement);
const scene = new THREE.Scene();
const cam = new THREE.PerspectiveCamera(40, W / H, 0.1, 1500);

// ---------- helpers ----------
const clamp = (x: number, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const sst = (x: number) => { x = clamp(x); return x * x * x * (x * (6 * x - 15) + 10); };
const eOut = (x: number) => 1 - Math.pow(1 - clamp(x), 3);
const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
const V = (x: number, y: number, z: number) => new THREE.Vector3(x, y, z);
const nz = (t: number, s: number) => Math.sin(t * 1.7 + s) * 0.6 + Math.sin(t * 0.63 + s * 2.1) * 0.4;
const hash = (n: number) => { const x = Math.sin(n * 91.345) * 47453.5453; return x - Math.floor(x); };
const lam = (o: THREE.MeshLambertMaterialParameters) => twoTone(new THREE.MeshLambertMaterial(o));
const add = (g: THREE.Object3D, m: THREE.Mesh, x: number, y: number, z: number, cast = true) => {
  m.position.set(x, y, z); m.castShadow = cast; m.receiveShadow = true; g.add(m); return m;
};
const box = (w: number, h: number, d: number, mat: THREE.Material | THREE.Material[]) => new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat);
const cyl = (r: number, h: number, mat: THREE.Material, n = 16) => new THREE.Mesh(new THREE.CylinderGeometry(r, r, h, n), mat);
const plane = (w: number, h: number, mat: THREE.Material) => new THREE.Mesh(new THREE.PlaneGeometry(w, h), mat);
const repT = (t: THREE.Texture, x: number, y: number) => { const c = t.clone(); c.repeat.set(x, y); c.wrapS = c.wrapT = THREE.RepeatWrapping; c.needsUpdate = true; return c; };

// ---------- painted textures ----------
const snowT = ctex("snow33", 512, 512, (g, r) => {
  g.fillStyle = "#eef2f8"; g.fillRect(0, 0, 512, 512);
  for (let i = 0; i < 260; i++) { g.fillStyle = r() < 0.5 ? "rgba(170,190,225,0.35)" : "rgba(255,255,255,0.8)"; const x = r() * 512, y = r() * 512; g.beginPath(); g.ellipse(x, y, 6 + r() * 22, 2 + r() * 5, 0, 0, 7); g.fill(); }
});
const tileT = ctex("tile33", 512, 512, (g, r) => {
  for (let i = 0; i < 4; i++) for (let j = 0; j < 4; j++) { g.fillStyle = jit(r, (i + j) % 2 ? "#c9cfd2" : "#d6dbdc", 0.04); g.fillRect(i * 128, j * 128, 128, 128); }
  g.strokeStyle = "rgba(60,60,70,0.7)"; g.lineWidth = 4; for (let i = 0; i <= 4; i++) { g.beginPath(); g.moveTo(i * 128, 0); g.lineTo(i * 128, 512); g.stroke(); g.beginPath(); g.moveTo(0, i * 128); g.lineTo(512, i * 128); g.stroke(); }
  for (let i = 0; i < 30; i++) { g.fillStyle = "rgba(90,80,70,0.12)"; g.beginPath(); g.ellipse(r() * 512, r() * 512, 10 + r() * 30, 5 + r() * 12, r() * 3, 0, 7); g.fill(); }
});
const wallT = ctex("wall33", 512, 512, (g, r) => {
  g.fillStyle = "#b9c7c4"; g.fillRect(0, 0, 512, 512);
  g.fillStyle = "#93a5a3"; g.fillRect(0, 380, 512, 132);
  g.strokeStyle = "rgba(50,60,60,0.75)"; g.lineWidth = 4; g.beginPath(); g.moveTo(0, 380); g.lineTo(512, 380); g.stroke();
  for (let x = 0; x <= 512; x += 256) { g.lineWidth = 3; g.beginPath(); g.moveTo(x, 0); g.lineTo(x, 512); g.stroke(); }
  for (let i = 0; i < 40; i++) { g.fillStyle = "rgba(70,70,60,0.08)"; g.beginPath(); g.ellipse(r() * 512, r() * 512, 8 + r() * 40, 4 + r() * 20, 0, 0, 7); g.fill(); }
});
const extWallT = ctex("extwall33", 512, 512, (g, r) => {
  g.fillStyle = "#c8c3b8"; g.fillRect(0, 0, 512, 512);
  g.strokeStyle = "rgba(60,55,50,0.6)"; g.lineWidth = 3;
  for (let y = 0; y < 512; y += 64) { g.beginPath(); g.moveTo(0, y); g.lineTo(512, y); g.stroke(); }
  for (let i = 0; i < 50; i++) { g.fillStyle = "rgba(80,70,60,0.1)"; g.fillRect(r() * 512, r() * 512, 10 + r() * 50, 4 + r() * 10); }
  g.fillStyle = "rgba(255,255,255,0.85)"; g.fillRect(0, 0, 512, 18);
});
const doorT = ctex("door33", 256, 512, (g) => {
  g.fillStyle = "#6f7a82"; g.fillRect(0, 0, 256, 512);
  g.strokeStyle = "rgba(30,30,40,0.8)"; g.lineWidth = 6; g.strokeRect(22, 22, 212, 468);
  g.fillStyle = "#ffd98a"; g.fillRect(80, 70, 96, 70); g.lineWidth = 5; g.strokeRect(80, 70, 96, 70);
  g.fillStyle = "#3a3f46"; g.fillRect(200, 260, 22, 60);
  g.fillStyle = "rgba(255,255,255,0.12)"; g.fillRect(30, 160, 30, 300);
});
const metalT = ctex("metal33", 256, 256, (g, r) => {
  g.fillStyle = "#7e8890"; g.fillRect(0, 0, 256, 256);
  for (let i = 0; i < 30; i++) { g.strokeStyle = "rgba(255,255,255,0.08)"; g.beginPath(); const y = r() * 256; g.moveTo(0, y); g.lineTo(256, y + 4); g.stroke(); }
  g.strokeStyle = "rgba(30,30,40,0.7)"; g.lineWidth = 6; g.strokeRect(8, 8, 240, 240);
  g.fillStyle = "#3a3f46"; for (const [x, y] of [[20, 20], [236, 20], [20, 236], [236, 236]]) { g.beginPath(); g.arc(x, y, 6, 0, 7); g.fill(); }
});
const woodT = ctex("wood33", 256, 256, (g, r) => {
  g.fillStyle = "#8b6a4a"; g.fillRect(0, 0, 256, 256);
  for (let i = 0; i < 12; i++) { g.strokeStyle = "rgba(60,40,25,0.35)"; g.lineWidth = 2; g.beginPath(); const y = r() * 256; g.moveTo(0, y); g.bezierCurveTo(80, y + 6, 170, y - 6, 256, y + 2); g.stroke(); }
});
const tapeT = ctex("tape33", 128, 32, (g) => { g.fillStyle = "#d8322e"; g.fillRect(0, 0, 128, 32); g.fillStyle = "#f2d5d0"; g.font = "bold 18px sans-serif"; g.fillText("PELIGRO", 22, 23); });
const genT = ctex("gen33", 256, 256, (g) => {
  g.fillStyle = "#e6b52c"; g.fillRect(0, 0, 256, 256);
  g.fillStyle = "#2b2b2b"; for (let i = 0; i < 8; i++) g.fillRect(30 + i * 24, 40, 12, 90);
  g.fillStyle = "#222"; g.fillRect(150, 170, 70, 40); g.fillStyle = "#ff3b2f"; g.beginPath(); g.arc(60, 190, 16, 0, 7); g.fill();
  g.strokeStyle = "rgba(40,30,10,0.8)"; g.lineWidth = 6; g.strokeRect(6, 6, 244, 244);
});
const ventT = ctex("vent33", 256, 160, (g) => {
  g.fillStyle = "#9aa3aa"; g.fillRect(0, 0, 256, 160); g.fillStyle = "#1b1f24";
  for (let i = 0; i < 7; i++) g.fillRect(18, 16 + i * 19, 220, 10);
  g.strokeStyle = "#2a2e33"; g.lineWidth = 6; g.strokeRect(3, 3, 250, 154);
});
const speakerT = ctex("spk33", 256, 256, (g) => {
  g.fillStyle = "#4a4f57"; g.fillRect(0, 0, 256, 256); g.fillStyle = "#1c1f24";
  for (let y = 40; y < 220; y += 22) for (let x = 40; x < 220; x += 22) { if (Math.hypot(x - 128, y - 128) < 92) { g.beginPath(); g.arc(x, y, 6, 0, 7); g.fill(); } }
  g.strokeStyle = "#1c1f24"; g.lineWidth = 8; g.strokeRect(6, 6, 244, 244);
});
const FONT = "Patrick";
const drawBoard = (g: CanvasRenderingContext2D) => {
  g.fillStyle = "#f7f8f6"; g.fillRect(0, 0, 1024, 576);
  const names = ["1. RAMÍREZ", "2. SOSA", "3. PEREYRA", "4. VIDAL", "5. ACOSTA", "6. MÉNDEZ", "7. FARÍAS", "8. LUNA", "9. ROJAS", "10. CABRAL", "11. QUIROGA"];
  g.font = `44px ${FONT}`; g.fillStyle = "#1d3c8a"; g.lineCap = "round";
  names.forEach((n, i) => {
    const x = i < 6 ? 60 : 420, y = 80 + (i % 6) * 66; g.fillText(n, x, y);
    g.strokeStyle = "#202020"; g.lineWidth = 6; g.beginPath(); g.moveTo(x - 10, y - 14); g.lineTo(x + g.measureText(n).width + 14, y - 18); g.stroke();
  });
  g.fillStyle = "#c62020"; g.font = `bold 58px ${FONT}`; g.fillText("12. LUCÍA", 420, 470); g.font = `bold 50px ${FONT}`; g.fillText("SUJETO INMUNE", 420, 530);
  g.strokeStyle = "#c62020"; g.lineWidth = 6; g.beginPath(); g.ellipse(560, 495, 190, 72, -0.03, 0, 7); g.stroke();
  // goteo de tinta fresca
  g.fillStyle = "#c62020"; g.beginPath(); g.moveTo(731, 538); g.quadraticCurveTo(736, 560, 733, 575); g.lineTo(728, 575); g.quadraticCurveTo(726, 556, 731, 538); g.fill();
  g.strokeStyle = "#5a5f66"; g.lineWidth = 14; g.strokeRect(7, 7, 1010, 562);
};
const boardT = () => ctex("board33", 1024, 576, drawBoard);
const drawNote = (g: CanvasRenderingContext2D) => {
  g.fillStyle = "#fbf3c8"; g.fillRect(0, 0, 512, 384);
  g.strokeStyle = "rgba(120,140,200,0.4)"; g.lineWidth = 2; for (let y = 70; y < 384; y += 52) { g.beginPath(); g.moveTo(0, y); g.lineTo(512, y); g.stroke(); }
  g.fillStyle = "#1c1c2a"; g.font = `50px ${FONT}`;
  g.fillText("Los acompañantes", 34, 115); g.fillText("NO son necesarios.", 34, 220); g.font = `40px ${FONT}`; g.fillText("— Dr. I.", 300, 318);
  g.strokeStyle = "#1c1c2a"; g.lineWidth = 4; g.beginPath(); g.moveTo(34, 232); g.lineTo(108, 232); g.stroke();
};
const noteT = () => ctex("note33", 512, 384, drawNote);
const signT = ctex("sign33", 512, 128, (g) => { g.fillStyle = "#1f5f8f"; g.fillRect(0, 0, 512, 128); g.fillStyle = "#fff"; g.font = "bold 64px sans-serif"; g.fillText("LABORATORIO", 40, 88); });
const skyT = ctex("sky33", 64, 512, (g) => { const gr = g.createLinearGradient(0, 0, 0, 512); gr.addColorStop(0, "#5f7fa8"); gr.addColorStop(0.5, "#aebfd6"); gr.addColorStop(1, "#d9e1ea"); g.fillStyle = gr; g.fillRect(0, 0, 64, 512); });
const blobT = ctex("blob33", 128, 128, (g) => { const gr = g.createRadialGradient(64, 64, 4, 64, 64, 62); gr.addColorStop(0, "#7a7480"); gr.addColorStop(0.6, "#bdb8c0"); gr.addColorStop(1, "#ffffff"); g.fillStyle = gr; g.fillRect(0, 0, 128, 128); });

// ---------- sets ----------
const SETS: Record<string, THREE.Group> = {};
const mkSet = (k: string, x: number) => { const g = new THREE.Group(); g.position.set(x, 0, 0); scene.add(g); SETS[k] = g; return g; };
const lights = { panels: [] as THREE.Mesh[], corPanels: [] as THREE.Mesh[] };
const panelMat = new THREE.MeshBasicMaterial({ color: 0xf4fbff });
const panelMatC = new THREE.MeshBasicMaterial({ color: 0xf4fbff });
const red = new THREE.MeshBasicMaterial({ color: 0x551010 });

// EXTERIOR (snowy yard in front of the lab)
const EXT = mkSet("ext", 0);
{
  const g = add(EXT, plane(120, 120, lam({ map: repT(snowT, 30, 30) })), 0, 0, 0, false); g.rotation.x = -Math.PI / 2;
  const sky = new THREE.Mesh(new THREE.SphereGeometry(600, 24, 16), new THREE.MeshBasicMaterial({ map: skyT, side: THREE.BackSide, fog: false, toneMapped: false })); EXT.add(sky);
  const bw = lam({ map: repT(extWallT, 4, 1.2) });
  add(EXT, box(16, 5, 9, bw), 0, 2.5, -4.6);
  add(EXT, box(6, 2.2, 5, bw), -3, 6.1, -5.5);
  add(EXT, box(16.4, 0.35, 9.4, lam({ color: "#f1f4f8" })), 0, 5.15, -4.6);
  const door = add(EXT, plane(1.3, 2.3, lam({ map: doorT })), 1.2, 1.15, -0.09, false);
  add(EXT, box(1.5, 0.12, 0.12, lam({ color: "#4a4f57" })), 1.2, 2.36, -0.05);
  add(EXT, plane(2.6, 0.62, lam({ map: signT })), 1.2, 3.2, -0.08, false);
  const bulb = add(EXT, new THREE.Mesh(new THREE.SphereGeometry(0.14, 12, 8), new THREE.MeshBasicMaterial({ color: 0xffe2a0 })), 1.2, 2.75, 0.1, false);
  for (let i = 0; i < 6; i++) { const w = add(EXT, plane(1.1, 0.8, lam({ color: i === 2 ? "#ffd98a" : "#2c3440" })), -6.5 + i * 2.2 + (i > 2 ? 2.2 : 0), 3.3, -0.08, false); }
  // reja + postes
  for (let i = -10; i <= 10; i++) add(EXT, cyl(0.05, 2.2, lam({ color: "#3d434b" }), 6), i * 1.2, 1.1, 13);
  add(EXT, box(25, 0.08, 0.08, lam({ color: "#3d434b" })), 0, 2.0, 13);
  // montañas y pinos
  const snowCap = lam({ color: "#f6f8fb" }), rock = lam({ color: "#7d8aa0" }), pine = lam({ color: "#2f5a4a" });
  for (let i = 0; i < 7; i++) { const r = 30 + hash(i) * 30, h = 40 + hash(i + 9) * 40, x = -150 + i * 50, z = -170 - hash(i + 3) * 60;
    const m = new THREE.Mesh(new THREE.ConeGeometry(r * 1.6, h, 7), rock); m.position.set(x, h / 2 - 2, z); EXT.add(m);
    const c = new THREE.Mesh(new THREE.ConeGeometry(r * 0.62, h * 0.39, 7), snowCap); c.position.set(x, h - h * 0.39 / 2 - 2 + 0.3, z); EXT.add(c); }
  for (let i = 0; i < 26; i++) { const x = -40 + hash(i * 3) * 80, z = -14 - hash(i * 5) * 40; if (Math.abs(x) < 9 && z > -16) continue; const s = 1.5 + hash(i) * 2;
    const t = new THREE.Mesh(new THREE.ConeGeometry(s, s * 3.4, 7), pine); t.position.set(x, s * 1.7, z); t.castShadow = true; EXT.add(t);
    const c = new THREE.Mesh(new THREE.ConeGeometry(s * 0.55, s * 1.1, 7), snowCap); c.position.set(x, s * 2.85, z); EXT.add(c); }
  void door; void bulb;
}

// room builder: floor, walls, ceiling (inward faces)
const room = (G: THREE.Group, w: number, d: number, h: number, wall: THREE.Material, floor: THREE.Material, ceil: THREE.Material) => {
  const f = add(G, plane(w, d, floor), 0, 0, 0, false); f.rotation.x = -Math.PI / 2;
  const c = add(G, plane(w, d, ceil), 0, h, 0, false); c.rotation.x = Math.PI / 2;
  const b = add(G, plane(w, h, wall), 0, h / 2, -d / 2, false);
  const fr = add(G, plane(w, h, wall), 0, h / 2, d / 2, false); fr.rotation.y = Math.PI;
  const l = add(G, plane(d, h, wall), -w / 2, h / 2, 0, false); l.rotation.y = Math.PI / 2;
  const r = add(G, plane(d, h, wall), w / 2, h / 2, 0, false); r.rotation.y = -Math.PI / 2;
  return { f, c, b, fr, l, r };
};
const ceilMat = lam({ color: "#cfd6d8" });
const bench = (G: THREE.Group, x: number, z: number, w: number, d = 0.7) => {
  add(G, box(w, 0.08, d, lam({ color: "#e8ecee" })), x, 0.92, z);
  add(G, box(w - 0.06, 0.88, d - 0.06, lam({ map: repT(metalT, w / 0.8, 1) })), x, 0.44, z);
};
const tubes = (G: THREE.Group, x: number, z: number, n = 6) => {
  add(G, box(0.5, 0.06, 0.14, lam({ color: "#4a4f57" })), x, 0.99, z);
  for (let i = 0; i < n; i++) add(G, cyl(0.025, 0.2, lam({ color: ["#e85d5d", "#6ac0e8", "#9be86a", "#f2c94c"][i % 4] }), 8), x - 0.2 + i * 0.08, 1.08, z);
};
const microscope = (G: THREE.Group, x: number, z: number) => {
  const m = lam({ color: "#eef1f3" }), k = lam({ color: "#2e3238" });
  add(G, box(0.26, 0.05, 0.3, m), x, 0.985, z); add(G, box(0.06, 0.36, 0.06, m), x, 1.16, z - 0.1);
  const t = add(G, cyl(0.045, 0.32, k, 10), x, 1.28, z - 0.02); t.rotation.x = 0.5; add(G, box(0.18, 0.03, 0.14, k), x, 1.08, z + 0.02);
};

// LAB room (Ibarra + Lucía)
const LAB = mkSet("lab", 200);
{
  room(LAB, 8, 7, 3.1, lam({ map: repT(wallT, 3, 1) }), lam({ map: repT(tileT, 4, 3.5) }), ceilMat);
  bench(LAB, 0, -3.1, 6); microscope(LAB, -0.6, -3.1); tubes(LAB, 1.2, -3.15); tubes(LAB, -2.2, -3.2, 4);
  add(LAB, plane(2.4, 0.58, lam({ map: signT })), 0.8, 2.45, -3.48, false);
  add(LAB, box(0.5, 0.5, 0.4, lam({ color: "#d9dfe3" })), 2.4, 1.2, -3.1);
  // stool
  add(LAB, cyl(0.25, 0.06, lam({ color: "#2e3238" })), 0.7, 0.62, -1.3); add(LAB, cyl(0.04, 0.6, lam({ color: "#9aa3aa" }), 8), 0.7, 0.3, -1.3);
  // console with gooseneck mic (right)
  bench(LAB, 3.3, -1.2, 1.2, 1.4); add(LAB, box(0.6, 0.35, 0.05, lam({ color: "#20252b" })), 3.3, 1.15, -1.7);
  for (let i = 0; i < 5; i++) add(LAB, box(0.06, 0.02, 0.06, new THREE.MeshBasicMaterial({ color: i % 2 ? 0x55ff88 : 0xff5544 })), 3.05 + i * 0.12, 0.97, -1.3, false);
  const mic = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3([V(0, 0, 0), V(0, 0.25, 0), V(-0.08, 0.4, 0.06), V(-0.2, 0.46, 0.12)]), 16, 0.012, 6), lam({ color: "#2e3238" }));
  add(LAB, mic, 3.15, 0.96, -1.0); add(LAB, new THREE.Mesh(new THREE.SphereGeometry(0.05, 10, 8), lam({ color: "#444a52" })), 2.95, 1.42, -0.88);
  // corridor doorway (left wall): dark opening
  const dw = add(LAB, plane(1.2, 2.2, new THREE.MeshBasicMaterial({ color: 0x0b0d12 })), -3.98, 1.1, 0.4, false); dw.rotation.y = Math.PI / 2;
  const fr = lam({ color: "#5c666e" }); add(LAB, box(0.1, 2.3, 0.1, fr), -3.95, 1.15, -0.25); add(LAB, box(0.1, 2.3, 0.1, fr), -3.95, 1.15, 1.05); add(LAB, box(0.1, 0.1, 1.4, fr), -3.95, 2.3, 0.4);
  for (const [x, z] of [[-2, -1.5], [2, -1.5], [-2, 1.8], [2, 1.8]]) { const p = add(LAB, plane(1.2, 0.5, panelMat), x, 3.09, z, false); p.rotation.x = Math.PI / 2; lights.panels.push(p); }
}

// CORRIDOR (along z), doors with red tape
const COR = mkSet("cor", 400);
{
  const Gc = new THREE.Group(); Gc.position.set(0, 0, -8); COR.add(Gc);
  room(Gc, 2.6, 24, 2.9, lam({ map: repT(wallT, 8, 1) }), lam({ map: repT(tileT, 1.3, 12) }), ceilMat);
  const dm = lam({ map: doorT }), tm = lam({ map: tapeT });
  for (let i = 0; i < 7; i++) for (const s of [-1, 1]) {
    const z = -10 + i * 3.2 + (s > 0 ? 1.2 : 0);
    const d = add(Gc, plane(1.0, 2.1, dm), s * 1.29, 1.05, z, false); d.rotation.y = -s * Math.PI / 2;
    for (const a of [-1, 1]) { const t = add(Gc, plane(1.35, 0.13, tm), s * 1.27, 1.1, z, false); t.rotation.set(0, -s * Math.PI / 2, 0); t.rotateZ(a * 0.98); }
  }
  for (let i = 0; i < 8; i++) { const p = add(Gc, plane(0.6, 1.2, panelMatC), 0, 2.89, -11 + i * 3, false); p.rotation.x = Math.PI / 2; lights.corPanels.push(p); }
  const end = add(Gc, plane(2.6, 2.9, new THREE.MeshBasicMaterial({ color: 0x07080b })), 0, 1.45, -11.95, false); void end;
}

// CAGE room (whiteboard, drawer, door, speaker, vent, generator)
const CAGE = mkSet("cage", 600);
const cageParts: { door?: THREE.Group; drawer?: THREE.Group; redLamp?: THREE.Mesh; spk?: THREE.Mesh } = {};
{
  const G = CAGE;
  room(G, 10, 8.5, 3.2, lam({ map: repT(wallT, 4, 1) }), lam({ map: repT(tileT, 5, 4.25) }), ceilMat);
  // whiteboard on back wall
  add(G, plane(2.6, 1.46, lam({ map: boardT() })), -1.2, 1.65, -4.23, false);
  add(G, box(2.6, 0.05, 0.1, lam({ color: "#9aa3aa" })), -1.2, 0.9, -4.18);
  const mk = add(G, cyl(0.022, 0.15, lam({ color: "#c62020" }), 8), -0.35, 0.95, -4.15); mk.rotation.z = Math.PI / 2;
  const cap = add(G, cyl(0.026, 0.05, lam({ color: "#c62020" }), 8), -0.72, 0.95, -4.15); cap.rotation.z = Math.PI / 2;
  // cages (right side)
  const bar = lam({ color: "#4d5560" });
  for (let c = 0; c < 3; c++) {
    const cx = 1.6 + c * 1.35, cz = -3.2;
    add(G, box(1.25, 0.06, 1.3, bar), cx, 2.0, cz); add(G, box(1.25, 0.06, 1.3, bar), cx, 0.03, cz);
    for (let i = 0; i < 9; i++) { const x = cx - 0.56 + i * 0.14;
      if (c === 1 && i >= 2 && i <= 6) { // doblados hacia afuera
        const k = [0.35, 0.6, 0.7, 0.55, 0.3][i - 2], sx = (i - 4) * 0.09;
        const crv = new THREE.CatmullRomCurve3([V(x, 0.06, cz + 0.62), V(x + sx * 0.5, 0.7, cz + 0.62 + k * 0.6), V(x + sx, 1.05, cz + 0.62 + k), V(x + sx * 0.5, 1.45, cz + 0.62 + k * 0.55), V(x, 1.97, cz + 0.62)]);
        const t = new THREE.Mesh(new THREE.TubeGeometry(crv, 24, 0.018, 6), bar); t.castShadow = true; G.add(t);
      } else add(G, cyl(0.018, 1.94, bar, 6), x, 1.0, cz + 0.62);
      add(G, cyl(0.018, 1.94, bar, 6), x, 1.0, cz - 0.62); }
    for (let i = 0; i < 9; i++) for (const s of [-1, 1]) add(G, cyl(0.018, 1.94, bar, 6), cx + s * 0.6, 1.0, cz - 0.56 + i * 0.14);
  }
  // scratches on the floor of the bent cage
  add(G, plane(0.9, 0.5, lam({ color: "#9a8f86" })), 2.95, 0.07, -3.2, false).rotation.x = -Math.PI / 2;
  // desk with drawer (left)
  const desk = lam({ map: repT(woodT, 2, 1) });
  add(G, box(1.8, 0.07, 0.8, desk), -3.6, 0.85, -1.4); add(G, box(0.07, 0.82, 0.75, desk), -4.45, 0.41, -1.4); add(G, box(0.07, 0.82, 0.75, desk), -2.75, 0.41, -1.4);
  const dr = new THREE.Group(); dr.position.set(-3.4, 0.68, -1.4); G.add(dr); cageParts.drawer = dr;
  add(dr, box(0.9, 0.03, 0.62, desk), 0, -0.1, 0); add(dr, box(0.9, 0.22, 0.03, desk), 0, 0, 0.31); add(dr, box(0.9, 0.22, 0.03, desk), 0, 0, -0.31);
  add(dr, box(0.03, 0.22, 0.62, desk), -0.45, 0, 0); add(dr, box(0.03, 0.22, 0.62, desk), 0.45, 0, 0);
  add(dr, box(0.12, 0.04, 0.03, lam({ color: "#d9c27a" })), 0.47, 0.02, 0).rotation.y = Math.PI / 2;
  const nt = add(dr, plane(0.4, 0.3, lam({ map: noteT() })), 0.18, -0.07, 0.05, false); nt.rotation.x = -Math.PI / 2; nt.rotation.z = 0.12;
  for (let i = 0; i < 3; i++) { const s = add(dr, cyl(0.016, 0.2, lam({ color: "#e6f4ff" }), 8), -0.05 + i * 0.05, -0.065, -0.12); s.rotation.x = Math.PI / 2; add(dr, cyl(0.004, 0.06, lam({ color: "#8a9099" }), 4), -0.05 + i * 0.05, -0.065, -0.25).rotation.x = Math.PI / 2; }
  for (let i = 0; i < 4; i++) add(dr, cyl(0.03, 0.08, lam({ color: i % 2 ? "#7fd0e8" : "#f29a5c" }), 10), 0.32 + (i % 2) * 0.06, -0.045, 0.12 + Math.floor(i / 2) * 0.08);
  // entrance door (left wall, hinge at z=+2.6)
  const dg = new THREE.Group(); dg.position.set(-4.97, 0, 2.6); G.add(dg); cageParts.door = dg;
  const dd = add(dg, box(0.08, 2.2, 1.2, lam({ map: doorT })), 0.05, 1.1, -0.6);
  const fr = lam({ color: "#5c666e" }); add(G, box(0.12, 2.3, 0.1, fr), -4.95, 1.15, 2.65); add(G, box(0.12, 2.3, 0.1, fr), -4.95, 1.15, 1.35); add(G, box(0.12, 0.1, 1.4, fr), -4.95, 2.3, 2.0);
  const hole = add(G, plane(1.2, 2.2, new THREE.MeshBasicMaterial({ color: 0x0b0d12 })), -4.99, 1.1, 2.0, false); hole.rotation.y = Math.PI / 2; void dd;
  // speaker above the door + red alarm lamp
  const spk = add(G, box(0.08, 0.62, 0.62, [lam({ map: speakerT }), lam({ map: speakerT }), lam({ color: "#3a3f46" }), lam({ color: "#3a3f46" }), lam({ color: "#3a3f46" }), lam({ color: "#3a3f46" })]), -4.94, 2.72, 0.8); cageParts.spk = spk;
  const lamp = add(G, new THREE.Mesh(new THREE.SphereGeometry(0.11, 12, 8, 0, Math.PI * 2, 0, Math.PI / 2), red), -4.92, 2.72, 2.0, false); lamp.rotation.z = Math.PI / 2; cageParts.redLamp = lamp;
  // vent on ceiling + generator below (back-left corner)
  const v = add(G, plane(0.9, 0.56, lam({ map: ventT })), -3.7, 3.19, -3.2, false); v.rotation.x = Math.PI / 2;
  add(G, box(1.0, 0.8, 0.6, [lam({ color: "#c99a1e" }), lam({ color: "#c99a1e" }), lam({ color: "#d9a925" }), lam({ color: "#c99a1e" }), lam({ map: genT }), lam({ color: "#c99a1e" })]), -4.2, 0.4, -3.75);
  const cable = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3([V(-3.7, 0.3, -3.45), V(-3.3, 0.04, -3.0), V(-2.6, 0.04, -3.3), V(-2.0, 0.04, -3.9), V(-1.9, 0.3, -4.2)]), 40, 0.035, 8), lam({ color: "#1d1d1f" }));
  cable.castShadow = true; G.add(cable);
  for (const [x, z] of [[-2.5, -2], [2.5, -2], [-2.5, 2], [2.5, 2]]) { const p = add(G, plane(1.2, 0.5, panelMat), x, 3.19, z, false); p.rotation.x = Math.PI / 2; lights.panels.push(p); }
}

// ---------- cards ----------
const SU = 0.00216;
class Card {
  cv = document.createElement("canvas"); tex: THREE.CanvasTexture; mesh: THREE.Mesh; blob: THREE.Mesh; key = "";
  constructor() {
    this.cv.width = 900; this.cv.height = 1500; this.tex = new THREE.CanvasTexture(this.cv); this.tex.colorSpace = THREE.SRGBColorSpace; this.tex.anisotropy = 8;
    const geo = new THREE.PlaneGeometry(600 * SU, 1000 * SU); geo.translate(0, 475 * SU, 0);
    this.mesh = new THREE.Mesh(geo, cardShade(new THREE.MeshLambertMaterial({ map: this.tex, alphaTest: 0.5, side: THREE.DoubleSide })));
    this.mesh.layers.set(NOINK); this.mesh.renderOrder = 2; this.mesh.onBeforeRender = () => { CARD_K.uPx.value = H / 1920; };
    this.blob = new THREE.Mesh(new THREE.PlaneGeometry(0.9, 0.42), blobMaterial(blobT)); this.blob.rotation.x = -Math.PI / 2; this.blob.renderOrder = 1;
    scene.add(this.mesh, this.blob);
  }
  hide() { this.mesh.visible = this.blob.visible = false; }
  put(set: string, x: number, y: number, z: number, s = 1) {
    const o = SETS[set].position; this.mesh.visible = this.blob.visible = true;
    this.mesh.position.set(o.x + x, y, o.z + z); this.mesh.scale.setScalar(s);
    this.blob.position.set(o.x + x, 0.012 + y, o.z + z + 0.02); this.blob.scale.setScalar(s); this.blob.visible = y < 0.05;
    this.mesh.rotation.y = Math.atan2(cam.position.x - this.mesh.position.x, cam.position.z - this.mesh.position.z);
  }
  draw(key: string, fn: (p: Pen) => void, flip = false) {
    if (key === this.key) return; this.key = key;
    const g = this.cv.getContext("2d")!; g.setTransform(1, 0, 0, 1, 0, 0); g.clearRect(0, 0, 900, 1500);
    g.setTransform(flip ? -1.5 : 1.5, 0, 0, 1.5, flip ? 900 : 0, 0); fn(new Pen(g)); this.tex.needsUpdate = true;
  }
}
const q = (x: number, k = 40) => Math.round(x * k) / k;
const front = (c: Card, o: Outfit, op: FrontOpts, tag: string) => c.draw(tag + JSON.stringify(op, (_k, v) => typeof v === "number" ? q(v) : v), (p) => bodyFront(p, o, op));
const cards = Array.from({ length: 6 }, () => new Card());

// ---------- light presets ----------
type Lt = { lit: number[]; shade: number[]; lift: number[]; tint: number[]; bg: string; fog: string; near: number; far: number; sun: number[] };
const LT: Record<string, Lt> = {
  ext: { lit: [1.38, 1.42, 1.5], shade: [0.4, 0.45, 0.62], lift: [0.06, 0.07, 0.12], tint: [0.97, 0.97, 1.02], bg: "#c3cfdf", fog: "#c3cfdf", near: 25, far: 220, sun: [-6, 9, 8] },
  lab: { lit: [1.36, 1.42, 1.4], shade: [0.38, 0.43, 0.52], lift: [0.05, 0.06, 0.08], tint: [1, 0.98, 0.97], bg: "#141820", fog: "#1a2028", near: 10, far: 60, sun: [2, 8, 4] },
  red: { lit: [1.6, 0.5, 0.4], shade: [0.26, 0.07, 0.07], lift: [0.04, 0.0, 0.0], tint: [1.0, 0.6, 0.55], bg: "#200608", fog: "#2a0a0c", near: 8, far: 50, sun: [-3, 7, 3] },
};
const sun = new THREE.DirectionalLight(0xffffff, 2.6); sun.castShadow = true; sun.shadow.mapSize.set(+(Q.get("sm") || 2048), +(Q.get("sm") || 2048));
Object.assign(sun.shadow.camera, { left: -9, right: 9, top: 9, bottom: -9, near: 0.5, far: 60 }); sun.shadow.bias = -0.0004; sun.shadow.normalBias = 0.02;
scene.add(sun, sun.target, new THREE.HemisphereLight(0xdcecff, 0x9a8a78, 0.45));
scene.fog = new THREE.Fog(0xffffff, 10, 100);
const mixA = (a: number[], b: number[], t: number) => a.map((v, i) => lerp(v, b[i], t));
const applyLight = (set: string, a: Lt, b: Lt | null, t: number, dim = 1) => {
  const L = (k: keyof Lt) => (b ? mixA(a[k] as number[], b[k] as number[], t) : (a[k] as number[]));
  const lit = L("lit").map((v) => v * dim);
  TONE.uLitCol.value.set(lit[0], lit[1], lit[2]); TONE.uShadeCol.value.set(...(L("shade") as [number, number, number]).map((v) => v * (0.6 + 0.4 * dim)) as [number, number, number]);
  TONE.uShadeLift.value.set(...(L("lift") as [number, number, number])); TONE.uLambert.value = 0.35; TONE.uSideK.value = 0.84; TONE.uTerm.value = 0.2;
  const tn = L("tint"); CHAR.uCharTint.value.set(tn[0] * (0.55 + 0.45 * dim), tn[1] * (0.55 + 0.45 * dim), tn[2] * (0.55 + 0.45 * dim));
  const bg = new THREE.Color(a.bg); if (b) bg.lerp(new THREE.Color(b.bg), t);
  scene.background = untone(bg); (scene.fog as THREE.Fog).color.copy(untone(b ? new THREE.Color(a.fog).lerp(new THREE.Color(b.fog), t) : new THREE.Color(a.fog)));
  (scene.fog as THREE.Fog).near = a.near; (scene.fog as THREE.Fog).far = a.far;
  const o = SETS[set].position, s = a.sun; sun.position.set(o.x + s[0], s[1], o.z + s[2]); sun.target.position.set(o.x, 0, o.z - 1);
};

// ---------- post ----------
const composer = new EffectComposer(renderer, { frameBufferType: THREE.HalfFloatType, multisampling: +(Q.get("ms") ?? 4) });
composer.addPass(new RenderPass(scene, cam));
composer.addPass(new InkPass(scene, cam, { widthNear: 4.2, widthFar: 3.0, distNear: 3, distFar: 60 }));
const lens = new LensBlur({ maxCoC: 24, nearScale: 1.2 });
const lp1 = new EffectPass(cam, lens.pre), lp2 = new EffectPass(cam, lens.main); composer.addPass(lp1); composer.addPass(lp2);
const grade = new GradeEffect(GRADES.day, 1);
composer.addPass(new EffectPass(cam, new ToneMappingEffect({ mode: ToneMappingMode.NEUTRAL }), grade));
if (Q.get("aa") === "smaa") composer.addPass(new EffectPass(cam, new SMAAEffect({ preset: SMAAPreset.ULTRA })));

// ---------- story ----------
// shot starts in seconds (aligned to the voice phrases)
const TIM = (window as any).TIM; const S: number[] = TIM.S;
const shotAt = (t: number) => { let i = 0; while (t >= S[i + 1]) i++; return i; };
type CamK = { p0: number[]; p1: number[]; l0: number[]; l1: number[]; fov?: number; fov1?: number; e?: (x: number) => number; dof?: number; foc?: number[] };
const walk = (t: number, speed = 1.0) => ({ d: t * speed, ph: t * 1.6 });
const idle = (t: number, seed: number) => ({ tilt: 1.6 * nz(t * 1.3, seed), headTilt: 2.5 * nz(t * 0.9, seed + 3) });
const blinkAt = (t: number, seed: number) => { const p = (t + hash(seed) * 3) % 3.1; return p < 0.12 ? 1 : 0; };
const DOOR_CLOSE = TIM.door; const RED_ON = TIM.red;

(window as any).renderFrame = (f: number) => {
  const t = f / FPS, sh = shotAt(t), st = t - S[sh], sl = S[sh + 1] - S[sh], u = st / sl;
  for (const k in SETS) SETS[k].visible = false; cards.forEach((c) => c.hide());
  let set = "lab", lt: Lt = LT.lab, lt2: Lt | null = null, lmix = 0, dim = 1;
  let K: CamK = { p0: [0, 1.6, 4], p1: [0, 1.6, 4], l0: [0, 1.4, 0], l1: [0, 1.4, 0] };
  const [cTU, cLU, cSO, cIB, cZ1, cZ2] = cards;
  const flick = (seed: number) => { const n = hash(Math.floor(t * 12) + seed); return n < 0.12 ? 0.35 : n < 0.2 ? 0.7 : 1; };
  const redOn = t >= RED_ON && sh >= 10;
  if (sh === 0) { // exterior: zombies pounding the lab door
    set = "ext"; lt = LT.ext;
    K = { p0: [4.2, 1.9, 9.5], p1: [2.6, 1.7, 5.6], l0: [0.9, 1.6, 0], l1: [1.1, 1.5, 0], e: sst, dof: 4 };
    const zs = [[0.6, 0.55], [1.25, 0.45], [1.9, 0.6], [0.95, 1.05]];
    zs.slice(0, 2).forEach(([x, z], i) => { const c = i ? cZ2 : cZ1; const k = 0.5 + 0.5 * Math.sin(t * 7 + i * 2);
      front(c, ZOMBIE(i), { mode: "stand", back: true, arms: "up", armK: 0.7 + 0.3 * k, tilt: 3 * Math.sin(t * 3.5 + i), seed: 20 + i }, "z" + i);
      c.put("ext", x + 0.3, 0, z + 0.35 + 0.05 * k); });
    front(cIB, ZOMBIE(2), { mode: "stand", back: true, arms: "up", armK: 0.85 + 0.15 * Math.sin(t * 6), tilt: -3 + 2 * Math.sin(t * 3), seed: 22 }, "z2"); cIB.put("ext", 2.15, 0, 0.75);
    front(cSO, ZOMBIE(1), { mode: "stand", back: true, arms: "reach", tilt: 4 * Math.sin(t * 2.4), seed: 23 }, "z3"); cSO.put("ext", 0.25, 0, 1.55);
  } else if (sh === 1) { // Lucía stays with Ibarra
    K = { p0: [0.35, 1.3, 2.3], p1: [0.2, 1.3, 1.9], l0: [0.12, 1.05, -1.1], l1: [0.12, 1.08, -1.1], e: sst, dof: 9 };
    front(cLU, LUCIA, { mode: "sit", expr: "worried", blink: blinkAt(t, 1), look: -0.6, ...idle(t, 1), seed: 5 }, "lu"); cLU.put("lab", 0.7, 0.02, -1.05);
    front(cIB, IBARRA, { mode: "stand", expr: "fake", arms: "syringe", armK: sst((st - 0.3) / 0.5), blink: blinkAt(t, 2), look: 0.5, ...idle(t, 2), seed: 9 }, "ib"); cIB.put("lab", -0.45, 0, -1.35);
  } else if (sh === 2) { // you + soldier leave through the left doorway
    K = { p0: [1.3, 1.65, 4.2], p1: [0.2, 1.6, 4.0], l0: [-0.6, 1.2, -0.6], l1: [-2.4, 1.2, 0.2], e: sst };
    const w = walk(Math.max(0, st - 0.2), 1.05);
    front(cTU, TU, { mode: w.d > 0 ? "stroll" : "stand", phase: w.ph, expr: "nervous", facing: -1, look: -1, seed: 3 }, "tu"); cTU.put("lab", -0.6 - w.d, 0, 0.6);
    front(cSO, SOLDADO, { mode: w.d > 0 ? "stroll" : "stand", phase: w.ph + 0.3, expr: "stern", facing: -1, look: -1, seed: 4 }, "so"); cSO.put("lab", 0.4 - w.d, 0, 0.1);
    front(cLU, LUCIA, { mode: "sit", expr: "worried", blink: blinkAt(t, 1), look: -1, ...idle(t, 1), seed: 5 }, "lu"); cLU.put("lab", 0.7, 0.02, -1.05);
    front(cIB, IBARRA, { mode: "stand", expr: "neutral", arms: "syringe", look: -1, blink: blinkAt(t, 2), ...idle(t, 2), seed: 9 }, "ib"); cIB.put("lab", -0.45, 0, -1.35);
  } else if (sh === 3) { // corridor: flicker + red tape; dolly back as they advance
    set = "cor"; dim = flick(1);
    const z = -14 + st * 1.0;
    K = { p0: [0.35, 1.55, z + 3.4], p1: [0.35, 1.55, z + 3.4 + sl * 1.0 * 0], l0: [-0.1, 1.35, z - 3], l1: [0, 1.35, z - 3], dof: 6 };
    K.p1 = [0.25, 1.55, z + 3.4]; K.p0 = K.p1;
    const w = walk(st, 1.0);
    front(cTU, TU, { mode: "stroll", phase: w.ph, expr: "nervous", look: Math.sin(st * 1.4), seed: 3 }, "tu"); cTU.put("cor", -0.38, 0, z);
    front(cSO, SOLDADO, { mode: "stroll", phase: w.ph + 0.5, expr: "stern", look: -Math.sin(st * 1.1), seed: 4 }, "so"); cSO.put("cor", 0.42, 0, z - 0.5);
    lights.corPanels.forEach((p, i) => ((p.material as THREE.MeshBasicMaterial).color.setScalar(flick(i * 7) < 1 && i % 2 ? 0.25 : 1)));
  } else if (sh >= 4 && sh <= 11 || sh === 14 || sh === 15) { // cage room
    set = "cage";
    if (redOn) { lt = LT.red; } if (sh === 10 && t >= RED_ON - 0.1) { lt = LT.lab; lt2 = LT.red; lmix = clamp((t - RED_ON + 0.1) / 0.25); }
    if (redOn) dim = 0.75 + 0.25 * (0.5 + 0.5 * Math.sin(t * 6.5));
    const tuOp: FrontOpts = { mode: "stand", expr: "nervous", blink: blinkAt(t, 3), ...idle(t, 3), seed: 3 };
    const soOp: FrontOpts = { mode: "stand", expr: "stern", blink: blinkAt(t, 4), ...idle(t, 4), seed: 4 };
    let tuP = [-0.6, 0, 0.8], soP = [0.5, 0, 1.2];
    if (sh === 4) { const w = walk(st, 0.9); K = { p0: [-1.0, 1.75, 4.0], p1: [-0.5, 1.7, 3.7], l0: [-0.4, 1.2, -1.0], l1: [0.9, 1.2, -2.2], e: sst };
      tuOp.mode = "stroll"; tuOp.phase = w.ph; soOp.mode = "stroll"; soOp.phase = w.ph + 0.5; tuOp.look = 1; soOp.look = 1;
      tuP = [-1.2, 0, 1.5 - Math.min(w.d, 1.5)]; soP = [-0.3, 0, 1.8 - Math.min(w.d, 1.5)]; }
    if (sh === 5) { K = { p0: [2.6, 1.25, -0.6], p1: [2.85, 1.15, -1.25], l0: [2.95, 1.0, -2.6], l1: [2.95, 1.0, -2.6], e: sst, dof: 9, fov: 40, fov1: 34 }; }
    if (sh === 6) { K = { p0: [-0.2, 1.65, -1.3], p1: [-1.9, 1.65, -1.4], l0: [-0.6, 1.75, -4.2], l1: [-1.75, 1.6, -4.2], e: sst }; }
    if (sh === 7) { K = { p0: [-1.05, 1.2, -1.5], p1: [-1.0, 1.15, -2.35], l0: [-1.0, 1.15, -4.2], l1: [-1.0, 1.12, -4.2], e: sst }; }
    if (sh === 8) { const op = sst(st / 0.7); cageParts.drawer!.position.x = -3.4 + 0.75 * op;
      K = { p0: [-1.6, 1.7, 0.2], p1: [-2.35, 1.38, -1.05], l0: [-2.9, 0.8, -1.4], l1: [-2.5, 0.6, -1.42], e: sst, dof: 5 }; }
    else cageParts.drawer!.position.x = -3.4 + (sh > 8 ? 0.75 : 0);
    if (sh === 9) { K = { p0: [-2.2, 1.5, 2.8], p1: [-2.25, 1.48, 2.35], l0: [-2.3, 1.42, 0.2], l1: [-2.3, 1.45, 0.2], e: eOut, dof: 10 };
      tuP = [-2.75, 0, 0.35]; soP = [-1.85, 0, 0.05]; tuOp.expr = "shock"; soOp.expr = "shock"; tuOp.arms = "cover"; tuOp.armK = sst(st / 0.35); soOp.look = -1; }
    if (sh === 10) { const whip = sst((t - TIM.whip) / 0.45);
      K = { p0: [-2.2, 1.55, -0.6], p1: [-2.2, 1.55, -0.6], l0: [-2.3, 1.4, 0.4], l1: [-4.9, 1.4, 2.0], e: (x) => x, dof: whip > 0.9 ? 0 : 8 };
      const lt0 = V(-2.3, 1.4, 0.4), lt1 = V(-4.9, 1.4, 2.0); const L = lt0.lerp(lt1, whip); K.l0 = K.l1 = [L.x, L.y, L.z];
      tuP = [-2.75, 0, 0.35]; soP = [-1.85, 0, 0.05]; tuOp.expr = t > DOOR_CLOSE ? "shock" : "nervous"; soOp.expr = t > DOOR_CLOSE ? "shock" : "stern"; tuOp.look = -1; soOp.look = -1; }
    const dclose = clamp((t - (DOOR_CLOSE - 0.35)) / 0.35); cageParts.door!.rotation.y = sh < 10 ? -1.35 : -1.35 * (1 - dclose * dclose);
    if (sh === 11) { K = { p0: [-2.6, 2.1, -0.2], p1: [-3.3, 2.3, 0.2], l0: [-4.9, 2.6, 1.3], l1: [-4.9, 2.65, 1.2], e: sst, dof: 6 };
      cageParts.spk!.scale.setScalar(1 + (t > TIM.spk ? 0.04 * Math.sin(t * 50) : 0)); }
    if (sh === 14) { const up = sst((t - TIM.up) / 1.4), down = sst((t - TIM.down) / 1.5);
      const look = V(-3.7, 3.1, -3.2).lerp(V(-3.4, 0.35, -3.5), down), pos = V(-2.2, 1.6, -0.9).lerp(V(-2.5, 1.2, -1.4), down);
      K = { p0: [pos.x, pos.y, pos.z], p1: [pos.x, pos.y, pos.z], l0: [lerp(-3.0, look.x, up), lerp(1.4, look.y, up), lerp(-3.0, look.z, up)], l1: [0, 0, 0], e: (x) => x };
      K.l1 = K.l0; }
    if (sh === 15) { K = { p0: [-1.0, 1.5, 2.6], p1: [-1.15, 1.48, 2.05], l0: [-1.35, 1.35, 0.3], l1: [-1.35, 1.4, 0.3], e: sst, dof: 10 };
      tuP = [-1.7, 0, 0.35]; soP = [-0.75, 0, 0.0]; tuOp.expr = "nervous"; tuOp.look = Math.sin(st * 0.9) > 0 ? 0.8 : -0.8; tuOp.headTilt = 6 * Math.sin(st * 0.9); soOp.expr = "stern"; soOp.look = -1; }
    if (sh !== 5 && sh !== 7 && sh !== 8 && sh !== 11 && sh !== 14) {
      front(cTU, TU, tuOp, "tu"); cTU.put("cage", tuP[0], 0, tuP[2]);
      front(cSO, SOLDADO, soOp, "so"); cSO.put("cage", soP[0], 0, soP[2]);
    }
    (cageParts.redLamp!.material as THREE.MeshBasicMaterial).color.set(redOn ? (Math.sin(t * 6.5) > 0 ? 0xff2a1a : 0x8a1510) : 0x551010);
  } else if (sh === 12 || sh === 13) { // Ibarra on the mic, Lucía sedated
    set = "lab"; lt = LT.red; dim = 0.8 + 0.2 * (0.5 + 0.5 * Math.sin(t * 6.5));
    if (sh === 12) {
      K = { p0: [2.2, 1.55, 1.3], p1: [2.45, 1.52, 0.85], l0: [3.0, 1.4, -1.0], l1: [3.0, 1.42, -1.0], e: sst, dof: 9 };
      const talk = Math.floor(t * 9) % 2 === 0 && t < TIM.talkEnd;
      front(cIB, IBARRA, { mode: "stand", expr: talk ? "stern" : "neutral", look: -0.4, blink: blinkAt(t, 2), ...idle(t, 2), facing: -1, seed: 9 }, "ib"); cIB.put("lab", 2.75, 0, -0.65);
      front(cLU, LUCIA, { mode: "sit", expr: "dazed", blink: 0.5, headTilt: 10, seed: 5 }, "lu"); cLU.put("lab", 0.7, 0.02, -1.05);
    } else {
      K = { p0: [0.85, 1.3, 0.7], p1: [0.78, 1.27, 0.35], l0: [0.7, 1.2, -1.05], l1: [0.7, 1.2, -1.05], e: sst, dof: 12 };
      const sl2 = sst((t - TIM.sleep) / 1.2);
      front(cLU, LUCIA, { mode: "sit", expr: sl2 > 0.6 ? "dazed" : "worried", blink: sl2 > 0.6 ? 0.5 + 0.5 * sl2 : blinkAt(t, 1), headTilt: 14 * sl2, tilt: 4 * sl2, seed: 5 }, "lu"); cLU.put("lab", 0.7, 0.02, -1.05);
      front(cIB, IBARRA, { mode: "stand", expr: "fake", arms: "syringe", look: 1, seed: 9 }, "ib"); cIB.put("lab", 1.9, 0, -1.7);
    }
  }
  if (sh === 1 || sh === 2) lights.panels.forEach((p) => (p.material as THREE.MeshBasicMaterial).color.setScalar(1));
  panelMat.color.setScalar(set === "cage" && redOn ? 0.15 : set === "lab" && (sh === 12 || sh === 13) ? 0.15 : 1);
  SETS[set].visible = true;
  applyLight(set, lt, lt2, lmix, dim);
  // camera
  const e = K.e ?? sst, k = e(u), o = SETS[set].position;
  const P = V(lerp(K.p0[0], K.p1[0], k), lerp(K.p0[1], K.p1[1], k), lerp(K.p0[2], K.p1[2], k));
  const L = V(lerp(K.l0[0], K.l1[0], k), lerp(K.l0[1], K.l1[1], k), lerp(K.l0[2], K.l1[2], k));
  P.x += 0.02 * nz(t * 0.8, 1); P.y += 0.015 * nz(t * 0.7, 2); // handheld creep
  let roll = 0;
  if (sh === 10 && t > DOOR_CLOSE) { const a = Math.max(0, 1 - (t - DOOR_CLOSE) / 0.3); P.x += 0.05 * a * Math.sin(t * 90); P.y += 0.04 * a * Math.cos(t * 77); }
  if (sh === 5) roll = 0.05 * sst(u); if (sh === 9) roll = -0.06 * eOut(u * 3); if (sh === 15) roll = 0.03 * Math.sin(st * 0.7);
  cam.position.set(o.x + P.x, P.y, o.z + P.z); cam.up.set(0, 1, 0); cam.lookAt(o.x + L.x, L.y, o.z + L.z); cam.rotateZ(roll);
  cam.fov = K.fov !== undefined ? lerp(K.fov, K.fov1 ?? K.fov, k) : 40; cam.updateProjectionMatrix();
  // re-billboard cards toward the final camera
  cards.forEach((c) => { if (c.mesh.visible) c.mesh.rotation.y = Math.atan2(cam.position.x - c.mesh.position.x, cam.position.z - c.mesh.position.z); });
  lens.focus = cam.position.distanceTo(V(o.x + L.x, L.y, o.z + L.z)); lens.cInf = (K.dof ?? 0) * (H / 1920) * 1.0; lp1.enabled = lp2.enabled = !!K.dof || Q.get("dofall") === "1";
  composer.render();
  return true;
};
(async () => {
  try { const ff = new FontFace("Patrick", "url(Patrick.ttf)"); await ff.load(); (document as any).fonts.add(ff); } catch (e) { console.log("font fail " + e); }
  await (document as any).fonts.ready;
  for (const [t, fn] of [[boardT(), drawBoard], [noteT(), drawNote]] as const) { const cv = t.image as HTMLCanvasElement; fn(cv.getContext("2d")!); t.needsUpdate = true; }
  (window as any).ready = true;
})();
void bodySide; void INK; void rng; void eOut;

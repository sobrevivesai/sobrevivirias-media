// EL BÚNKER · Parte 1 "LA ESCOTILLA" — mundo 3D + tarjetas 2D, cada cuadro es función pura del número de cuadro.
import * as THREE from "three";
import { EffectComposer, RenderPass, EffectPass, ToneMappingEffect, ToneMappingMode, SMAAEffect, SMAAPreset } from "postprocessing";
import { InkPass, NOINK } from "../kit/ink";
import { LensBlur } from "../kit/lensblur";
import { GradeEffect, GRADES } from "../kit/grade";
import { TONE, CHAR, twoTone, untone } from "../kit/shade";
import { cardShade, CARD_K, blobMaterial } from "../kit/cardshade";
import { ctex, rng, jit } from "../kit/paint";
import { Pen, bodyFront, bodySide, FrontOpts, Outfit, INK } from "../toon33";
import { BU } from "../castdefs";

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
const concT = ctex("conc", 512, 512, (g, r) => {
  g.fillStyle = "#8d9094"; g.fillRect(0, 0, 512, 512);
  for (let i = 0; i < 90; i++) { g.fillStyle = r() < 0.5 ? "rgba(60,60,66,0.10)" : "rgba(210,210,215,0.10)"; g.beginPath(); g.ellipse(r() * 512, r() * 512, 8 + r() * 50, 4 + r() * 24, r() * 3, 0, 7); g.fill(); }
  g.strokeStyle = "rgba(40,40,46,0.55)"; g.lineWidth = 4; for (let x = 0; x <= 512; x += 256) { g.beginPath(); g.moveTo(x, 0); g.lineTo(x, 512); g.stroke(); } for (let y = 0; y <= 512; y += 170) { g.beginPath(); g.moveTo(0, y); g.lineTo(512, y); g.stroke(); }
});
const floorT = ctex("bfloor", 512, 512, (g, r) => {
  g.fillStyle = "#5d646b"; g.fillRect(0, 0, 512, 512);
  g.strokeStyle = "rgba(20,22,28,0.6)"; g.lineWidth = 5; for (let i = 0; i <= 4; i++) { g.beginPath(); g.moveTo(i * 128, 0); g.lineTo(i * 128, 512); g.stroke(); g.beginPath(); g.moveTo(0, i * 128); g.lineTo(512, i * 128); g.stroke(); }
  for (let i = 0; i < 40; i++) { g.fillStyle = "rgba(255,255,255,0.05)"; g.fillRect(r() * 512, r() * 512, 30 + r() * 60, 3); }
});
const metalT = ctex("metalb", 256, 256, (g, r) => {
  g.fillStyle = "#7e8890"; g.fillRect(0, 0, 256, 256);
  for (let i = 0; i < 30; i++) { g.strokeStyle = "rgba(255,255,255,0.08)"; g.beginPath(); const y = r() * 256; g.moveTo(0, y); g.lineTo(256, y + 4); g.stroke(); }
  g.strokeStyle = "rgba(30,30,40,0.7)"; g.lineWidth = 6; g.strokeRect(8, 8, 240, 240);
  g.fillStyle = "#3a3f46"; for (const [x, y] of [[20, 20], [236, 20], [20, 236], [236, 236]]) { g.beginPath(); g.arc(x, y, 6, 0, 7); g.fill(); }
});
const canT = ctex("cans", 256, 256, (g) => { for (let i = 0; i < 4; i++) { g.fillStyle = ["#c0392b", "#d6a82a", "#3f7a3a", "#2f6fa8"][i]; g.fillRect(i * 64, 0, 64, 256); g.fillStyle = "#f4efe0"; g.fillRect(i * 64 + 8, 90, 48, 70); } });
const barT = ctex("barrel", 256, 256, (g) => { g.fillStyle = "#2f6fb8"; g.fillRect(0, 0, 256, 256); g.fillStyle = "rgba(255,255,255,0.18)"; g.fillRect(20, 0, 24, 256); g.strokeStyle = "rgba(10,20,50,0.7)"; g.lineWidth = 6; for (const y of [60, 196]) { g.beginPath(); g.moveTo(0, y); g.lineTo(256, y); g.stroke(); } g.fillStyle = "#e8f1fb"; g.font = "bold 40px sans-serif"; g.fillText("AGUA", 90, 140); });
const hatchT = ctex("hatch", 256, 256, (g, r) => {
  g.fillStyle = "#59616a"; g.fillRect(0, 0, 256, 256);
  g.strokeStyle = "rgba(15,18,24,0.8)"; g.lineWidth = 8; g.beginPath(); g.arc(128, 128, 118, 0, 7); g.stroke(); g.beginPath(); g.arc(128, 128, 60, 0, 7); g.stroke();
  g.fillStyle = "#c8a02a"; for (let i = 0; i < 8; i++) { const a = i * Math.PI / 4; g.beginPath(); g.arc(128 + Math.cos(a) * 92, 128 + Math.sin(a) * 92, 8, 0, 7); g.fill(); }
  for (let i = 0; i < 30; i++) { g.fillStyle = "rgba(120,60,30,0.15)"; g.beginPath(); g.ellipse(r() * 256, r() * 256, 6 + r() * 20, 3 + r() * 8, 0, 0, 7); g.fill(); }
});
const FONT = "Patrick";
const monT = () => ctex("monitor", 512, 384, (g) => {
  g.fillStyle = "#0e2a16"; g.fillRect(0, 0, 512, 384);
  const gr = g.createRadialGradient(256, 150, 20, 256, 190, 300); gr.addColorStop(0, "#3f8a58"); gr.addColorStop(1, "#0b1f10"); g.fillStyle = gr; g.fillRect(0, 0, 512, 384);
  g.fillStyle = "#0a160c"; g.beginPath(); g.ellipse(180, 250, 52, 38, 0, 0, 7); g.fill(); g.fillRect(138, 250, 84, 140); g.beginPath(); g.moveTo(138, 380); g.lineTo(138, 275); g.quadraticCurveTo(180, 225, 222, 275); g.lineTo(222, 380); g.fill();   // mujer
  g.beginPath(); g.arc(180, 205, 34, 0, 7); g.fill(); g.fillRect(150, 215, 60, 30); g.beginPath(); g.moveTo(148, 190); g.quadraticCurveTo(120, 280, 140, 330); g.lineTo(156, 330); g.fill();
  g.fillStyle = "#0a160c"; g.beginPath(); g.ellipse(390, 330, 80, 28, -0.1, 0, 7); g.fill(); g.beginPath(); g.arc(440, 305, 26, 0, 7); g.fill(); g.fillRect(300, 322, 80, 14);   // algo que se arrastra
  g.fillStyle = "#d8ff9a"; g.beginPath(); g.arc(434, 300, 4, 0, 7); g.arc(448, 300, 4, 0, 7); g.fill();
  g.fillStyle = "rgba(0,0,0,0.25)"; for (let y = 0; y < 384; y += 4) g.fillRect(0, y, 512, 2);
  g.fillStyle = "#9fe0b0"; g.font = "bold 22px monospace"; g.fillText("CAM 1 · ESCOTILLA", 16, 30); g.fillStyle = "#ff4a3a"; g.beginPath(); g.arc(484, 24, 8, 0, 7); g.fill();
});
const lblT = ctex("lbl", 256, 128, (g) => { g.fillStyle = "#f2e9c8"; g.fillRect(0, 0, 256, 128); g.fillStyle = "#222"; g.font = "bold 30px sans-serif"; g.fillText("AIRE · 14 DÍAS", 14, 56); g.fillStyle = "#c62020"; g.fillRect(14, 74, 228, 10); });
const blobT = ctex("blobb", 128, 128, (g) => { const gr = g.createRadialGradient(64, 64, 4, 64, 64, 62); gr.addColorStop(0, "#7a7480"); gr.addColorStop(0.6, "#bdb8c0"); gr.addColorStop(1, "#ffffff"); g.fillStyle = gr; g.fillRect(0, 0, 128, 128); });

// ---------- sets ----------
const SETS: Record<string, THREE.Group> = {};
const mkSet = (k: string, x: number) => { const g = new THREE.Group(); g.position.set(x, 0, 0); scene.add(g); SETS[k] = g; return g; };
const lights = { panels: [] as THREE.Mesh[] };
const room = (G: THREE.Group, w: number, d: number, h: number, wall: THREE.Material, floor: THREE.Material, ceil: THREE.Material) => {
  const f = add(G, plane(w, d, floor), 0, 0, 0, false); f.rotation.x = -Math.PI / 2;
  const c = add(G, plane(w, d, ceil), 0, h, 0, false); c.rotation.x = Math.PI / 2;
  add(G, plane(w, h, wall), 0, h / 2, -d / 2, false);
  const fr = add(G, plane(w, h, wall), 0, h / 2, d / 2, false); fr.rotation.y = Math.PI;
  const l = add(G, plane(d, h, wall), -w / 2, h / 2, 0, false); l.rotation.y = Math.PI / 2;
  const r = add(G, plane(d, h, wall), w / 2, h / 2, 0, false); r.rotation.y = -Math.PI / 2;
};
const BK = mkSet("bunk", 0);
const parts = { hatch: new THREE.Group(), fan: new THREE.Group(), lamp: null as THREE.Mesh | null, mon: null as THREE.Mesh | null, dust: [] as THREE.Mesh[] };
{
  const G = BK, W_ = 5.5, D_ = 6, H_ = 2.6;
  room(G, W_, D_, H_, lam({ map: repT(concT, 3, 1.2) }), lam({ map: repT(floorT, 3, 3.2) }), lam({ map: repT(concT, 3, 3) }));
  const steel = lam({ map: repT(metalT, 1, 1) }), dark = lam({ color: "#2e3238" });
  // escotilla en el techo, sobre la escalera (pared del fondo)
  parts.hatch.position.set(1.2, H_ - 0.02, -2.3); G.add(parts.hatch);
  { const h = add(parts.hatch, cyl(0.52, 0.1, lam({ map: hatchT }), 24), 0, -0.05, 0); h.castShadow = false;
    add(parts.hatch, cyl(0.08, 0.2, dark, 8), 0, -0.2, 0); const wh = add(parts.hatch, box(0.8, 0.07, 0.07, dark), 0, -0.3, 0); wh.rotation.y = 0.4; add(parts.hatch, box(0.07, 0.07, 0.8, dark), 0, -0.3, 0).rotation.y = 0.4; }
  // escalera
  for (const s of [-0.22, 0.22]) add(G, box(0.05, 2.6, 0.05, steel), 1.2 + s, 1.3, -2.92);
  for (let i = 0; i < 8; i++) add(G, box(0.44, 0.04, 0.05, steel), 1.2, 0.3 + i * 0.3, -2.92);
  // barriles de agua (izquierda del fondo)
  const bm = lam({ map: repT(barT, 1, 1) });
  for (let i = 0; i < 4; i++) add(G, cyl(0.28, 0.9, bm, 16), -2.2 + (i % 2) * 0.6, 0.45 + Math.floor(i / 2) * 0.9, -2.55);
  // estante con latas (pared izquierda)
  const cm = lam({ map: repT(canT, 2, 1) }), wood = lam({ color: "#7a5a3a" });
  for (let r = 0; r < 3; r++) { add(G, box(0.5, 0.05, 2.2, wood), -2.5, 0.5 + r * 0.55, 0.2); for (let i = 0; i < 9; i++) add(G, cyl(0.07, 0.2, cm, 10), -2.5 + (i % 2) * 0.08, 0.63 + r * 0.55, -0.8 + i * 0.25); }
  // litera (pared derecha)
  const bed = lam({ color: "#4a6a4f" }); for (const y of [0.45, 1.3]) { add(G, box(1.0, 0.12, 2.2, bed), 2.15, y, 0.9); }
  for (const [x, z] of [[1.65, -0.15], [2.65, -0.15], [1.65, 1.95], [2.65, 1.95]]) add(G, box(0.06, 1.6, 0.06, steel), x, 0.8, z);
  // filtro de aire (frente-derecha del fondo): caja con ventilador
  add(G, box(0.9, 0.9, 0.5, steel), 2.2, 1.0, -2.65); add(G, plane(0.6, 0.3, lam({ map: lblT })), 2.2, 1.45, -2.39, false);
  parts.fan.position.set(2.2, 0.85, -2.39); G.add(parts.fan); add(parts.fan, cyl(0.22, 0.03, dark, 20), 0, 0, 0).rotation.x = Math.PI / 2;
  for (let i = 0; i < 4; i++) { const b = add(parts.fan, box(0.4, 0.07, 0.02, lam({ color: "#aab2ba" })), 0, 0, 0.03); b.rotation.z = i * Math.PI / 4; }
  // mesa con monitor (pared izquierda frente)
  add(G, box(1.1, 0.07, 0.7, wood), -2.2, 0.8, 2.0); for (const [x, z] of [[-2.7, 1.7], [-1.7, 1.7], [-2.7, 2.3], [-1.7, 2.3]]) add(G, box(0.06, 0.78, 0.06, steel), x, 0.4, z);
  add(G, box(0.62, 0.48, 0.1, dark), -2.2, 1.1, 1.8); parts.mon = add(G, plane(0.54, 0.4, new THREE.MeshBasicMaterial({ map: monT() })), -2.2, 1.1, 1.855, false);
  // lámpara colgante con foco
  add(G, cyl(0.01, 0.35, dark, 6), 0, H_ - 0.18, 0.2); parts.lamp = add(G, new THREE.Mesh(new THREE.SphereGeometry(0.1, 12, 8), new THREE.MeshBasicMaterial({ color: 0xffe2a0 })), 0, H_ - 0.4, 0.2, false);
  for (let i = 0; i < 10; i++) { const d = add(G, plane(0.05, 0.05, new THREE.MeshBasicMaterial({ color: 0xcfc8bd, transparent: true, opacity: 0.8 })), 0, 0, 0, false); d.visible = false; parts.dust.push(d); }
}
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
const cards = Array.from({ length: 4 }, () => new Card());

// ---------- light presets ----------
type Lt = { lit: number[]; shade: number[]; lift: number[]; tint: number[]; bg: string; fog: string; near: number; far: number; sun: number[] };
const LT: Record<string, Lt> = {
  bunk: { lit: [1.4, 1.25, 1.0], shade: [0.34, 0.33, 0.42], lift: [0.05, 0.05, 0.08], tint: [1, 0.95, 0.9], bg: "#0a0b0e", fog: "#0f1115", near: 8, far: 40, sun: [1.5, 8, 3] },
  low: { lit: [1.1, 0.95, 0.85], shade: [0.26, 0.25, 0.34], lift: [0.04, 0.04, 0.07], tint: [0.95, 0.9, 0.9], bg: "#08090c", fog: "#0c0d11", near: 8, far: 40, sun: [1.5, 8, 3] },
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
const TIM = (window as any).TIM; const S: number[] = TIM.S;
const shotAt = (t: number) => { let i = 0; while (t >= S[i + 1]) i++; return i; };
type CamK = { p0: number[]; p1: number[]; l0: number[]; l1: number[]; fov?: number; e?: (x: number) => number; dof?: number };
const idle = (t: number, seed: number) => ({ tilt: 1.6 * nz(t * 1.3, seed), headTilt: 2.5 * nz(t * 0.9, seed + 3) });
const blinkAt = (t: number, seed: number) => { const p = (t + hash(seed) * 3) % 3.1; return p < 0.12 ? 1 : 0; };
const KN = [TIM.k1, TIM.k2, TIM.k3, TIM.k4, TIM.k5, TIM.k5 + 0.25];

(window as any).renderFrame = (f: number) => {
  const tr = f / FPS, hook = TIM.hookSrc != null && tr < S[1];
  const t = hook ? TIM.hookSrc + tr * (TIM.hookRate ?? 0.8) : tr, sh0 = shotAt(t), st = t - S[sh0], sl = S[sh0 + 1] - S[sh0], u = st / sl;
  const sh = sh0 === 0 ? 1 : sh0;
  for (const k in SETS) SETS[k].visible = false; cards.forEach((c) => c.hide());
  let K: CamK = { p0: [0, 1.6, 2.5], p1: [0, 1.6, 2.5], l0: [0, 1.4, 0], l1: [0, 1.4, 0] };
  const [cTU] = cards;
  const tuO = (o: FrontOpts = {}): FrontOpts => ({ mode: "stand", expr: "nervous", blink: blinkAt(t, 3), ...idle(t, 3), seed: 3, ...o });
  const tu = (x: number, z: number, o: FrontOpts = {}, y = 0, sc = 1) => { front(cTU, BU, tuO(o), "bu"); cTU.put("bunk", x, y, z, sc); };
  // golpes: choque que decae
  let kn = 0; for (const k of KN) if (t > k) kn += Math.exp(-(t - k) * 11) * (1 - Math.exp(-(t - k) * 120));
  const shake = Math.min(1, kn);
  parts.hatch.position.y = 2.58 - 0.035 * shake * Math.sin(t * 90); parts.hatch.rotation.z = 0.02 * shake * Math.sin(t * 70);
  parts.lamp!.position.x = 0.04 * Math.sin(t * 2.2) + 0.12 * shake * Math.sin(t * 40); parts.fan.rotation.z = t * 22;
  parts.dust.forEach((d, i) => { const a = (t - (KN.filter((k) => k <= t).slice(-1)[0] ?? 99)); const on = a >= 0 && a < 1.2; d.visible = on; if (on) { d.position.set(1.2 + (hash(i) - 0.5) * 0.9, 2.5 - a * (0.5 + hash(i + 4)), -2.3 + (hash(i + 8) - 0.5) * 0.9); d.rotation.y = hash(i) * 6; d.lookAt(cam.position); } });
  if (sh === 1) { // contexto
    K = { p0: [0.4, 1.55, 2.9], p1: [0.5, 1.5, 2.3], l0: [0.7, 1.2, -1.5], l1: [0.8, 1.3, -1.5], e: sst, dof: 4 };
    tu(0.6, -0.9, { expr: "worried" });
  } else if (sh === 2) { // votos
    K = { p0: [-1.0, 1.4, 2.6], p1: [-0.4, 1.4, 2.4], l0: [-0.5, 1.1, -1.2], l1: [-0.2, 1.1, -1.4], e: sst, dof: 4 };
    tu(-0.3, -1.1, { expr: "neutral", look: 0 });
  } else if (sh === 3) { // bajaste y sellaste
    K = { p0: [0.5, 0.9, 1.2], p1: [0.9, 1.2, 0.8], l0: [1.2, 2.2, -2.4], l1: [1.2, 2.3, -2.4], e: sst, dof: 3 };
    tu(1.2, -1.9, { back: true, arms: "up", armK: 0.9 + 0.1 * Math.sin(t * 3) });
  } else if (sh === 4) { // agua y comida
    K = { p0: [0.2, 1.1, 2.2], p1: [-0.2, 1.15, 1.8], l0: [-1.5, 1.0, -1.8], l1: [-1.6, 1.0, -1.5], e: sst, dof: 3 };
    tu(-0.6, -0.8, { expr: "relief", arms: "hold" as any, look: -1 });
  } else if (sh === 5) { // filtro de aire
    K = { p0: [1.0, 1.25, 1.0], p1: [1.6, 1.2, 0.2], l0: [2.2, 1.0, -2.5], l1: [2.2, 1.0, -2.5], e: sst, dof: 3 };
    tu(1.7, -1.6, { expr: "neutral", look: 1 });
  } else if (sh === 6) { // silencio
    K = { p0: [0.8, 0.5, 0.6], p1: [1.0, 0.6, 0.1], l0: [1.2, 2.3, -2.3], l1: [1.2, 2.4, -2.3], e: sst, dof: 4 };
    tu(0.5, -1.0, { expr: "worried", look: 0 });
  } else if (sh === 7) { // GOLPES
    K = { p0: [0.9, 0.9, 1.7], p1: [1.0, 1.0, 1.3], l0: [1.15, 1.7, -2.3], l1: [1.15, 1.8, -2.3], e: sst, dof: 3 };
    tu(1.0, -0.6, { expr: "shock", look: 0, arms: "cover" as any, tilt: 3 * shake * Math.sin(t * 50) });
  } else if (sh === 8) { // no esperabas a nadie
    K = { p0: [0.2, 1.45, 1.8], p1: [0.35, 1.5, 1.4], l0: [0.4, 1.4, -0.5], l1: [0.4, 1.45, -0.5], e: sst, dof: 3 };
    tu(0.4, -0.5, { expr: "worried" });
  } else if (sh === 9) { // voz
    K = { p0: [1.0, 0.7, 0.4], p1: [1.15, 1.1, -0.6], l0: [1.2, 2.3, -2.3], l1: [1.2, 2.45, -2.3], e: sst, dof: 3 };
    tu(0.6, -1.3, { expr: "shock", look: 1 });
  } else if (sh === 10) { // monitor
    K = { p0: [-1.2, 1.25, 3.0], p1: [-1.7, 1.2, 2.5], l0: [-2.2, 1.1, 1.8], l1: [-2.2, 1.1, 1.8], e: sst, dof: 0 };
    tu(-1.6, 2.4, { back: true, expr: "shock" }, 0, 0.001);
  } else if (sh === 11) { // dos opciones
    K = { p0: [-0.2, 1.5, 2.6], p1: [0.2, 1.5, 2.2], l0: [0.7, 1.3, -1.5], l1: [0.8, 1.3, -1.5], e: sst, dof: 4 };
    tu(0.9, -1.3, { expr: "nervous", look: 0, arms: "hip" as any });
  } else { // pregunta
    K = { p0: [0.6, 0.7, 1.4], p1: [0.9, 0.95, 1.0], l0: [1.2, 1.9, -2.3], l1: [1.2, 2.0, -2.3], e: sst, dof: 4 };
    tu(1.0, -1.4, { back: true, expr: "nervous" });
  }
  const set = "bunk"; SETS[set].visible = true;
  applyLight(set, LT.bunk, LT.low, sst((t - TIM.k1) / 3) * 0.4 + (sh >= 6 ? 0.3 : 0), 0.85 + 0.15 * Math.sin(t * 5) * 0 + 0.15 - 0.3 * shake);
  const e = K.e ?? sst, k = e(u), o = SETS[set].position;
  const P = V(lerp(K.p0[0], K.p1[0], k), lerp(K.p0[1], K.p1[1], k), lerp(K.p0[2], K.p1[2], k));
  const L = V(lerp(K.l0[0], K.l1[0], k), lerp(K.l0[1], K.l1[1], k), lerp(K.l0[2], K.l1[2], k));
  P.x += 0.02 * nz(t * 0.8, 1); P.y += 0.015 * nz(t * 0.7, 2);
  P.x += 0.05 * shake * Math.sin(t * 83); P.y += 0.04 * shake * Math.cos(t * 71);
  cam.position.set(o.x + P.x, P.y, o.z + P.z); cam.up.set(0, 1, 0); cam.lookAt(o.x + L.x, L.y, o.z + L.z);
  cam.fov = K.fov ?? 40; if (hook) cam.fov *= 0.94 - 0.08 * sst(tr / S[1]); cam.updateProjectionMatrix(); cam.updateMatrixWorld();
  cards.forEach((c) => { if (c.mesh.visible) c.mesh.rotation.y = Math.atan2(cam.position.x - c.mesh.position.x, cam.position.z - c.mesh.position.z); });
  lens.focus = cam.position.distanceTo(V(o.x + L.x, L.y, o.z + L.z)); lens.cInf = (K.dof ?? 0) * (H / 1920); lp1.enabled = lp2.enabled = !!K.dof;
  composer.render();
  return true;
};
(async () => {
  try { const ff = new FontFace("Patrick", "url(Patrick.ttf)"); await ff.load(); (document as any).fonts.add(ff); } catch (e) { console.log("font fail " + e); }
  await (document as any).fonts.ready;
  (window as any).ready = true;
})();
void bodySide; void INK; void rng; void eOut; void jit; void FONT; void lights;

import { Pen, bodyFront } from "./toon33";
import { TU, LUCIA, SOLDADO, IBARRA, ZOMBIE } from "./castdefs";
const c = document.createElement("canvas"); c.width = 1800; c.height = 2000; document.body.appendChild(c);
const g = c.getContext("2d")!; g.fillStyle = "#cfd8e0"; g.fillRect(0, 0, 1800, 2000);
const items: any[] = [[TU, { expr: "nervous", arms: "point" }], [LUCIA, { expr: "worried", arms: "hold" }], [SOLDADO, { expr: "stern", arms: "hip" }],
  [IBARRA, { expr: "fake", arms: "syringe" }], [ZOMBIE(0), { expr: "zombie", arms: "reach" }], [TU, { expr: "shock", arms: "up" }],
  [IBARRA, { expr: "stern", arms: "mic", facing: 1 }], [LUCIA, { expr: "dazed", mode: "sit" }], [SOLDADO, { expr: "shock", arms: "cover" }]];
items.forEach(([o, op], i) => { g.save(); g.translate((i % 3) * 600, Math.floor(i / 3) * 660 - 330); bodyFront(new Pen(g), o, { mode: "stand", seed: i + 3, ...op }); g.restore(); });
(window as any).renderFrame = () => true; (window as any).ready = true;

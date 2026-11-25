import { INK, Outfit } from "./toon33";
export const TU: Outfit = { jacket: "#6b7a3a", pants: "#3b3f52", boots: "#4a3426", hat: "hair", hair: "#3a2a20", bandana: "#d23a33", pack: "#3f7a3a", skin: "#f5c9a0" };
export const LUCIA: Outfit = { jacket: "#7b5ac9", pants: "#3b3f52", boots: "#5a3b2a", hat: "hair", hair: "#6a4026", longHair: "#6a4026", bitten: true, skin: "#ffe2c2" };
export const SOLDADO: Outfit = { jacket: "#566640", pants: "#4a5238", boots: INK, hat: "helmet", cap: "#5d6b3f", belt: "#3a3a2a", rifle: true, skin: "#ecd0b6", build: "stout" };
export const IBARRA: Outfit = { jacket: "#e9edf0", coat: "#eef1f3", pants: "#4a4e5a", boots: "#2a2a30", hat: "hair", hair: "#a3a3aa", glasses: true, skin: "#ffe2c2", buttons: "#9aa3ad" };
export const ZOMBIE = (v = 0): Outfit => ({ jacket: ["#5a6a8a", "#7a5a4a", "#4a6a5a"][v % 3], pants: "#3b3f52", boots: "#3a2a20", hat: "hair", hair: ["#3a3a3a", "#6a4a2a", "#2a2a2a"][v % 3], zombie: true });
export const BU: Outfit = { jacket: "#d9822b", pants: "#3b3f52", boots: "#3a2a20", hat: "hair", hair: "#2a2320", bandana: "#2f7fd6", pack: "#5a5f66", skin: "#f5c9a0" };
export const ELLA: Outfit = { jacket: "#7d8794", pants: "#3b3f52", boots: "#3a2a20", hat: "hair", hair: "#1d171c", longHair: "#1d171c", skin: "#e9d3c4" };

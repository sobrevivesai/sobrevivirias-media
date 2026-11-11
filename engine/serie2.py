#!/usr/bin/env python3
"""Serie interactiva de supervivencia v2 — con voz, subtítulos karaoke y pantalla dividida.
Uso:  python3 serie2.py episodios/ep1.json salida.mp4
      python3 serie2.py preview episodios/ep1.json <beat> <t> out.png
"""
import hashlib, json, math, os, random, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS, SR = 1080, 1920, 30, 24000
HERE = os.path.dirname(os.path.abspath(__file__))
FONT_D = os.path.join(HERE, "..", "fonts", "Anton.ttf")
FONT_B = os.path.join(HERE, "..", "fonts", "ArchivoBlack.ttf")
CACHE = os.path.join(HERE, "cache"); os.makedirs(CACHE, exist_ok=True)
YEL = (255, 222, 40); RED = (255, 64, 64); BLUE = (40, 140, 255); ORA = (255, 128, 20); NAVY = (22, 24, 44)
_fc = {}
def font(p, s):
    if (p, s) not in _fc: _fc[(p, s)] = ImageFont.truetype(p, s)
    return _fc[(p, s)]
def ease(x): x = max(0.0, min(1.0, x)); return 1 - (1 - x) ** 3
def back(x):
    x = max(0.0, min(1.0, x)); c = 1.9; return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2
def lerp(a, b, t): return a + (b - a) * t

class SD:
    """ImageDraw con escala (para dibujar a 2x y suavizar bordes)."""
    def __init__(self, img, k=2, ox=0, oy=0):
        self.d = ImageDraw.Draw(img, "RGBA"); self.k = k; self.ox = ox; self.oy = oy
    def P(self, pts): return [((x + self.ox) * self.k, (y + self.oy) * self.k) for x, y in pts]
    def B(self, b): return [(b[0] + self.ox) * self.k, (b[1] + self.oy) * self.k, (b[2] + self.ox) * self.k, (b[3] + self.oy) * self.k]
    def ellipse(self, b, fill=None, outline=None, width=0): self.d.ellipse(self.B(b), fill=fill, outline=outline, width=int(width * self.k))
    def rect(self, b, r=0, fill=None, outline=None, width=0):
        bb = self.B(b)
        if bb[2] - bb[0] < 1 or bb[3] - bb[1] < 1: return
        self.d.rounded_rectangle(bb, int(r * self.k), fill=fill, outline=outline, width=int(width * self.k))
    def poly(self, pts, fill=None, outline=None, width=0): self.d.polygon(self.P(pts), fill=fill, outline=outline, width=int(width * self.k) if outline else 0)
    def line(self, pts, fill, width): self.d.line(self.P(pts), fill=fill, width=int(width * self.k), joint="curve")
    def chord(self, b, a0, a1, fill): self.d.chord(self.B(b), a0, a1, fill=fill)

# ================================================================ FONDOS
BW, BH = int(W * 1.15), int(H * 1.15)
def gradient(stops, w, h):
    ys = np.linspace(0, 1, h); out = np.zeros((h, 3))
    for i in range(len(stops) - 1):
        (p0, c0), (p1, c1) = stops[i], stops[i + 1]
        m = (ys >= p0) & (ys <= p1); f = ((ys[m] - p0) / max(1e-6, p1 - p0))[:, None]
        out[m] = np.array(c0) * (1 - f) + np.array(c1) * f
    return Image.fromarray(np.repeat(out[:, None, :], w, 1).astype(np.uint8), "RGB")

def add_light(img, x, y, rad, col, s=1.0, blur=None):
    g = Image.new("RGB", img.size, 0); d = ImageDraw.Draw(g)
    for i in range(10, 0, -1):
        rr = rad * i / 10; a = s * (1 - i / 11) ** 1.6
        d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=tuple(int(c * a) for c in col))
    g = g.filter(ImageFilter.GaussianBlur(blur or rad / 4))
    return Image.fromarray(np.clip(np.asarray(img, np.int16) + np.asarray(g, np.int16), 0, 255).astype(np.uint8))

def aurora(img, seed=2, strength=0.55):
    g = Image.new("RGB", img.size, 0); d = ImageDraw.Draw(g); r = random.Random(seed)
    for band in range(3):
        y0 = 350 + band * 160; ph = r.random() * 6
        col = [(40, 255, 160), (60, 220, 255), (170, 90, 255)][band]
        for k in range(0, 12):
            pts = [(x, y0 + 120 * math.sin(x / 260 + ph) + 60 * math.sin(x / 90 + ph * 2) + k * 9) for x in range(-50, img.width + 60, 30)]
            d.line(pts, fill=tuple(int(c * (0.35 - k * 0.025)) for c in col), width=26)
    g = g.filter(ImageFilter.GaussianBlur(38))
    return Image.fromarray(np.clip(np.asarray(img, np.int16) + (np.asarray(g, np.float32) * strength).astype(np.int16), 0, 255).astype(np.uint8))

def stars(img, n, maxy, seed=1):
    r = random.Random(seed); d = ImageDraw.Draw(img)
    for _ in range(n):
        x, y = r.randint(0, img.width), r.randint(0, maxy); s = r.choice([1, 1, 2, 2, 3]); c = r.randint(150, 255)
        d.ellipse([x, y, x + s, y + s], fill=(c, c, min(255, c + 20)))

def ridge(sd, yb, amp, col, seed, cap=None, step=(70, 170)):
    r = random.Random(seed); pts = [(-60, BH)]; x = -60; peaks = []
    while x < BW + 120:
        y = yb - r.randint(int(amp * 0.25), amp); pts.append((x, y)); peaks.append((x, y)); x += r.randint(*step)
        pts.append((x, yb - r.randint(0, int(amp * 0.35)))); x += r.randint(*step)
    pts.append((BW + 60, BH)); sd.poly(pts, fill=col)
    if cap:
        for (px, py) in peaks:
            sd.poly([(px, py), (px - 55, py + 70), (px - 20, py + 55), (px + 5, py + 80), (px + 40, py + 60)], fill=cap)

def fog(img, y, h, col, a=0.6):
    m = np.zeros((img.height, 1), np.float32); ys = np.arange(img.height)
    m[:, 0] = np.exp(-((ys - y) / h) ** 2) * a
    arr = np.asarray(img, np.float32); arr = arr * (1 - m[..., None]) + np.array(col, np.float32) * m[..., None]
    return Image.fromarray(arr.clip(0, 255).astype(np.uint8))

def pine(sd, x, y, h, col, snow=(225, 235, 250)):
    sd.rect([x - h * 0.04, y - h * 0.15, x + h * 0.04, y + 4], fill=(30, 22, 20))
    for i in range(4):
        ty = y - h * 0.15 - i * h * 0.2; wdt = h * (0.36 - i * 0.075)
        sd.poly([(x - wdt, ty), (x, ty - h * 0.38), (x + wdt, ty)], fill=col)
        sd.poly([(x - wdt * 0.55, ty - h * 0.15), (x, ty - h * 0.38), (x + wdt * 0.3, ty - h * 0.2)], fill=snow)

def ground(img, sd, y0, col=(214, 226, 245), shade=(120, 140, 190), seed=9):
    r = random.Random(seed)
    pts = [(-40, BH)] + [(x, y0 + 40 * math.sin(x / 210 + 1) + 15 * math.sin(x / 70)) for x in range(-40, BW + 60, 30)] + [(BW + 40, BH)]
    sd.poly(pts, fill=col)
    # sombras azules en la nieve
    for i in range(7):
        x = r.randint(0, BW); y = r.randint(int(y0 + 100), BH); w_ = r.randint(200, 420)
        sd.ellipse([x - w_, y - 22, x + w_, y + 22], fill=shade + (70,))
    return img

BG_CACHE = {}
def build_bg(kind):
    if kind in BG_CACHE: return BG_CACHE[kind]
    K = 2
    if kind in ("wreck", "crash"):
        sky = [(0, (26, 20, 58)), (0.45, (92, 52, 110)), (0.68, (230, 120, 110)), (1, (240, 170, 140))]
    elif kind == "sunset":
        sky = [(0, (34, 28, 86)), (0.4, (150, 60, 120)), (0.62, (255, 130, 70)), (1, (255, 190, 120))]
    elif kind == "cabin":
        sky = [(0, (6, 8, 26)), (0.5, (18, 30, 70)), (1, (40, 60, 110))]
    else:
        sky = [(0, (4, 6, 22)), (0.5, (14, 26, 64)), (1, (34, 56, 108))]
    img = gradient(sky, BW, BH)
    stars(img, 260 if kind not in ("sunset",) else 60, 1100)
    if kind in ("light", "night", "walk", "cabin"): img = aurora(img, seed={"light": 2, "night": 5, "walk": 3, "cabin": 7}[kind])
    if kind in ("light", "night", "cabin", "walk"):
        img = add_light(img, int(BW * 0.22), 420, 120, (200, 220, 255), 0.9)
        ImageDraw.Draw(img).ellipse([BW * 0.22 - 52, 368, BW * 0.22 + 52, 472], fill=(240, 244, 255))
    if kind == "sunset":
        img = add_light(img, BW // 2, 1240, 420, (255, 170, 80), 1.0)
        ImageDraw.Draw(img).ellipse([BW // 2 - 130, 1110, BW // 2 + 130, 1370], fill=(255, 226, 150))
    big = img.resize((BW * K, BH * K)); sd = SD(big, K)
    hot = kind in ("wreck", "crash", "sunset")
    far = (70, 50, 100) if hot else (34, 46, 92); mid = (48, 34, 74) if hot else (24, 32, 66); near = (30, 22, 50) if hot else (16, 20, 44)
    capc = (235, 200, 220) if hot else (190, 205, 240)
    ridge(sd, 1180, 420, far, 3, cap=capc)
    img = big.resize((BW, BH), Image.LANCZOS); img = fog(img, 1200, 140, (150, 110, 150) if hot else (60, 80, 140), 0.45)
    big = img.resize((BW * K, BH * K)); sd = SD(big, K)
    ridge(sd, 1330, 280, mid, 4, cap=capc, step=(90, 200))
    img = big.resize((BW, BH), Image.LANCZOS); img = fog(img, 1380, 110, (170, 120, 150) if hot else (70, 90, 150), 0.4)
    big = img.resize((BW * K, BH * K)); sd = SD(big, K)
    r = random.Random(11)
    if kind in ("walk", "night", "light", "cabin"):
        for i in range(14):
            x = r.randint(-40, BW + 40); pine(sd, x, 1470 + r.randint(-20, 20), r.randint(160, 260), near)
    gy = 1520 if kind != "light" else 1560
    ground(img, sd, gy, (226, 214, 232) if hot else (214, 226, 245), (180, 140, 190) if hot else (120, 140, 200))
    if kind in ("walk", "night"):
        for i in range(5):
            x = r.choice([r.randint(-60, 160), r.randint(BW - 160, BW + 60)]); pine(sd, x, BH - r.randint(80, 300), r.randint(520, 760), (12, 16, 34))
    if kind in ("wreck", "crash"): wreck(sd, BW // 2 + 120, 1560)
    if kind == "cabin": cabin(sd, BW // 2, 1500)
    img = big.resize((BW, BH), Image.LANCZOS)
    if kind in ("wreck", "crash"): img = add_light(img, BW // 2 + 110, 1520, 260, (255, 120, 40), 0.85)
    if kind == "light": img = add_light(img, int(BW * 0.7), 1330, 150, (255, 180, 80), 1.0)
    if kind == "cabin":
        img = add_light(img, BW // 2 - 150, 1420, 200, (255, 160, 60), 0.75)
        img = add_light(img, BW // 2 + 115, 1500, 260, (255, 140, 50), 0.8)
    BG_CACHE[kind] = img
    return img

def wreck(sd, cx, cy):
    body = (178, 186, 200); dark = (110, 116, 130)
    sd.poly([(cx - 200, cy + 30), (cx - 560, cy + 150), (cx - 540, cy + 182), (cx - 170, cy + 75)], fill=(150, 156, 170), outline=NAVY, width=4)
    sd.poly([(cx - 420, cy), (cx - 40, cy - 170), (cx + 15, cy - 60), (cx - 360, cy + 95)], fill=dark, outline=NAVY, width=5)
    sd.poly([(cx - 420, cy), (cx - 40, cy - 170), (cx - 25, cy - 130), (cx - 400, cy + 25)], fill=body)
    sd.poly([(cx - 410, cy + 40), (cx - 20, cy - 115), (cx - 15, cy - 100), (cx - 405, cy + 55)], fill=(200, 40, 50))
    for i in range(6):
        wx = cx - 350 + i * 54; wy = cy - 6 - i * 24; sd.ellipse([wx, wy, wx + 24, wy + 30], fill=(40, 60, 90))
    sd.poly([(cx - 40, cy - 170), (cx + 15, cy - 60), (cx + 70, cy - 40), (cx + 45, cy + 70), (cx - 25, cy + 50)], fill=(36, 28, 30))
    sd.poly([(cx + 70, cy - 40), (cx + 400, cy - 10), (cx + 370, cy + 100), (cx + 45, cy + 70)], fill=dark, outline=NAVY, width=5)
    sd.poly([(cx + 280, cy - 15), (cx + 365, cy - 250), (cx + 410, cy - 238), (cx + 370, cy - 5)], fill=(200, 40, 50), outline=NAVY, width=5)
    # nieve encima
    sd.poly([(cx - 410, cy - 2), (cx - 40, cy - 172), (cx - 60, cy - 150), (cx - 400, cy + 8)], fill=(240, 244, 255))

def cabin(sd, cx, cy):
    wood = (92, 56, 38); dk = (60, 36, 24)
    sd.rect([cx - 280, cy - 230, cx + 280, cy + 110], fill=wood, outline=NAVY, width=5)
    for y in range(cy - 220, cy + 110, 38): sd.line([(cx - 280, y), (cx + 280, y)], fill=dk, width=5)
    sd.rect([cx + 130, cy - 420, cx + 190, cy - 280], fill=(70, 50, 44), outline=NAVY, width=4)
    sd.poly([(cx - 340, cy - 220), (cx, cy - 470), (cx + 340, cy - 220)], fill=(46, 34, 34), outline=NAVY, width=5)
    sd.poly([(cx - 352, cy - 214), (cx, cy - 482), (cx + 352, cy - 214), (cx + 330, cy - 200), (cx, cy - 440), (cx - 330, cy - 200)], fill=(240, 245, 255))
    sd.rect([cx - 220, cy - 150, cx - 80, cy - 30], 6, fill=(255, 196, 90), outline=NAVY, width=5)
    sd.line([(cx - 150, cy - 150), (cx - 150, cy - 30)], fill=dk, width=8); sd.line([(cx - 220, cy - 90), (cx - 80, cy - 90)], fill=dk, width=8)
    sd.rect([cx + 50, cy - 130, cx + 180, cy + 110], fill=(255, 176, 70), outline=NAVY, width=5)
    sd.poly([(cx + 50, cy - 130), (cx + 105, cy - 108), (cx + 105, cy + 130), (cx + 50, cy + 110)], fill=(110, 70, 46), outline=NAVY, width=4)
    sd.poly([(cx + 60, cy + 112), (cx + 300, cy + 220), (cx + 140, cy + 230), (cx + 175, cy + 112)], fill=(255, 210, 140, 110))

# ================================================================ PERSONAJE (Pancho, original)
def pancho_layer(s, t, mouth=0.0, walk=False, shiver=True, look=0.0):
    K = 2; lw, lh = int(340 * s), int(480 * s)
    img = Image.new("RGBA", (lw * K, lh * K)); ox, oy = lw / 2 / s, 300
    sd = SD(img, K * s, ox, oy)
    O = NAVY; ow = 5
    bob = (-abs(math.sin(t * 7)) * 12) if walk else (math.sin(t * 38) * 1.5 if shiver else 0)
    sw = math.sin(t * 7) * 22 if walk else 0
    sd.ellipse([-115, 150, 115, 178], fill=(20, 30, 60, 70))
    # botas
    sd.rect([-62 - sw, 95, -14 - sw, 160], 16, fill=(52, 40, 46), outline=O, width=ow)
    sd.rect([14 + sw, 95, 62 + sw, 160], 16, fill=(52, 40, 46), outline=O, width=ow)
    oy2 = bob
    def Y(v): return v + oy2
    # mochila
    sd.rect([62, Y(-60), 122, Y(70)], 22, fill=(70, 110, 70), outline=O, width=ow)
    # cuerpo
    sd.ellipse([-108, Y(-80), 108, Y(130)], fill=(250, 124, 32), outline=O, width=ow)
    sd.line([(0, Y(-40)), (0, Y(120))], fill=(200, 90, 20), width=5)
    sd.rect([-70, Y(40), -30, Y(70)], 8, fill=(220, 100, 20))
    # brazos + mitones
    a = math.sin(t * 7) * 14 if walk else 0
    sd.ellipse([-138, Y(-20 + a), -78, Y(70 + a)], fill=(240, 114, 28), outline=O, width=ow)
    sd.ellipse([-140, Y(50 + a), -96, Y(94 + a)], fill=(214, 40, 50), outline=O, width=ow)
    sd.ellipse([78, Y(-20 - a), 138, Y(70 - a)], fill=(240, 114, 28), outline=O, width=ow)
    sd.ellipse([96, Y(50 - a), 140, Y(94 - a)], fill=(214, 40, 50), outline=O, width=ow)
    # capucha + piel
    sd.ellipse([-126, Y(-292), 126, Y(-40)], fill=(240, 114, 28), outline=O, width=ow)
    sd.ellipse([-108, Y(-272), 108, Y(-56)], fill=(236, 230, 220))
    for i in range(16):
        ang = i / 16 * 2 * math.pi; px, py = 104 * math.cos(ang), Y(-164) + 104 * math.sin(ang)
        sd.ellipse([px - 14, py - 14, px + 14, py + 14], fill=(236, 230, 220))
    sd.ellipse([-84, Y(-246), 84, Y(-80)], fill=(255, 214, 182), outline=(200, 150, 120), width=3)
    # cejas preocupadas, ojos, mejillas, boca
    lx = look * 6
    for side in (-1, 1):
        ex = side * 34
        blink = (t % 3.3) < 0.1
        if blink: sd.line([(ex - 15, Y(-170)), (ex + 15, Y(-170))], fill=O, width=6)
        else:
            sd.ellipse([ex - 19, Y(-196), ex + 19, Y(-148)], fill=(255, 255, 255), outline=O, width=3)
            sd.ellipse([ex - 11 + lx, Y(-184), ex + 11 + lx, Y(-158)], fill=(20, 22, 40))
            sd.ellipse([ex - 6 + lx, Y(-181), ex + 1 + lx, Y(-174)], fill=(255, 255, 255))
        sd.line([(ex - side * 22, Y(-214)), (ex + side * 18, Y(-206 - 6))], fill=(90, 50, 30), width=7)
        sd.ellipse([ex + side * 10 - 18, Y(-140), ex + side * 10 + 18, Y(-122)], fill=(255, 140, 140, 150))
    mo = max(0.0, min(1.0, mouth))
    if mo > 0.08: sd.ellipse([-16 - 4 * mo, Y(-128), 16 + 4 * mo, Y(-118 + 26 * mo)], fill=(90, 20, 30), outline=O, width=3)
    else: sd.line([(-14, Y(-118)), (0, Y(-122)), (14, Y(-118))], fill=O, width=5)
    # bufanda
    sd.rect([-82, Y(-84), 82, Y(-52)], 16, fill=(220, 34, 50), outline=O, width=4)
    fl = math.sin(t * 4) * 10
    sd.poly([(34, Y(-58)), (70 + fl, Y(20)), (40 + fl, Y(26)), (12, Y(-54))], fill=(200, 28, 44), outline=O, width=4)
    # vapor de aliento
    ph = (t * 0.7) % 1
    if ph < 0.6:
        al = int(150 * (1 - ph / 0.6)); rr = 14 + ph * 48
        bx, by = -95 - ph * 80, Y(-120) - ph * 40
        sd.ellipse([bx - rr, by - rr, bx + rr, by + rr], fill=(240, 245, 255, al))
    img = img.resize((lw, lh), Image.LANCZOS)
    return img, (int(lw / 2), int(oy * s))

# ================================================================ TEXTO
def text_img(txt, size, fill, stroke=10, fpath=None, shadow=True):
    f = font(fpath or FONT_D, size); bb = f.getbbox(txt, stroke_width=stroke); pad = 16
    im = Image.new("RGBA", (bb[2] - bb[0] + pad * 2, bb[3] - bb[1] + pad * 2))
    d = ImageDraw.Draw(im)
    if shadow:
        sh = Image.new("RGBA", im.size); ImageDraw.Draw(sh).text((-bb[0] + pad + 6, -bb[1] + pad + 8), txt, font=f, fill=(0, 0, 0, 160), stroke_width=stroke, stroke_fill=(0, 0, 0, 160))
        im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(5))); d = ImageDraw.Draw(im)
    d.text((-bb[0] + pad, -bb[1] + pad), txt, font=f, fill=fill, stroke_width=stroke, stroke_fill=(0, 0, 0))
    return im

class Karaoke:
    """Subtítulos de 1-3 palabras, la palabra que se dice va en amarillo."""
    def __init__(self, words, times, y=1180, size=124):
        self.y = y; self.size = size; self.chunks = []
        cur = []
        for i, w in enumerate(words):
            cur.append(i)
            brk = w.endswith((".", ",", "?", "!", "…", ":")) or w.endswith("...")
            if len(cur) == 3 or brk or sum(len(words[j]) for j in cur) > 13:
                self.chunks.append(cur); cur = []
        if cur: self.chunks.append(cur)
        self.words = words; self.times = times; self.cache = {}
    def img(self, i, active):
        k = (i, active)
        if k not in self.cache:
            w = self.words[i].upper().strip("*")
            hl = self.words[i].strip(".,?!…:¿¡").startswith("*")
            w = w.replace("*", "")
            self.cache[k] = text_img(w, self.size, YEL if active else ((255, 90, 90) if hl else (255, 255, 255)))
        return self.cache[k]
    def draw(self, frame, t):
        ci = None
        for n, ch in enumerate(self.chunks):
            if t >= self.times[ch[0]][0] - 0.05: ci = n
        if ci is None: return
        ch = self.chunks[ci]
        if t > self.times[ch[-1]][1] + 0.6 and ci == len(self.chunks) - 1: return
        t0 = self.times[ch[0]][0] - 0.05
        pop = back((t - t0) / 0.18); sp = int(self.size * 0.05)
        ims = []
        for i in ch:
            act = self.times[i][0] - 0.03 <= t < (self.times[i][1] if i != ch[-1] else 99)
            if i == ch[-1] and t >= self.times[i][1] and ci < len(self.chunks) - 1: act = False
            ims.append(self.img(i, act))
        # partir en 2 líneas si es muy ancho
        lines = [ims]
        if sum(im.width for im in ims) > 1000 and len(ims) > 1: lines = [ims[:-1], ims[-1:]] if len(ims) == 2 else [ims[:2], ims[2:]]
        lh = int(self.size * 1.05); y0 = self.y - (len(lines) * lh) // 2
        sc = 0.6 + 0.4 * pop
        for li, ln in enumerate(lines):
            tw = sum(im.width for im in ln) - sp * (len(ln) - 1); x = (W - tw) // 2
            for im in ln:
                if abs(sc - 1) > 0.01:
                    im2 = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))))
                    frame.paste(im2, (int(x + (im.width - im2.width) / 2), int(y0 + li * lh + (im.height - im2.height) / 2)), im2)
                else: frame.paste(im, (x, y0 + li * lh), im)
                x += im.width - sp

def pill(sd, x, y, txt, bg, fg=(255, 255, 255), size=38, anchor="l", icon=None):
    f = font(FONT_B, size); bb = f.getbbox(txt); tw = bb[2] - bb[0]; iw = 44 if icon else 0
    w_ = tw + 52 + iw; h_ = size + 34
    if anchor == "r": x -= w_
    if anchor == "c": x -= w_ / 2
    sd.rect([x, y, x + w_, y + h_], h_ / 2, fill=bg)
    if icon == "temp":
        sd.rect([x + 26, y + 14, x + 38, y + h_ - 22], 6, fill=(255, 255, 255)); sd.ellipse([x + 20, y + h_ - 32, x + 44, y + h_ - 10], fill=(255, 255, 255))
    if icon == "bat":
        sd.rect([x + 22, y + 22, x + 54, y + h_ - 22], 5, outline=(255, 255, 255), width=3); sd.rect([x + 54, y + 30, x + 58, y + h_ - 30], 1, fill=(255, 255, 255))
        sd.rect([x + 26, y + 26, x + 31, y + h_ - 26], 1, fill=(255, 255, 255))
    sd.d.text(((x + 26 + iw) * sd.k, (y + 17 - bb[1]) * sd.k), txt, font=font(FONT_B, size * sd.k), fill=fg)
    return x, x + w_

def hud_img(ep, h, blink):
    im = Image.new("RGBA", (W * 2, 150 * 2)); sd = SD(im, 2)
    pill(sd, 50, 20, f"PARTE {ep['parte']}", (255, 255, 255, 240), (10, 10, 20), 38)
    x = W - 50
    if "bat" in h:
        x0, _ = pill(sd, x, 20, f"{h['bat']}%", (RED + (245,)) if blink else (20, 20, 30, 190), size=38, anchor="r", icon="bat"); x = x0 - 14
    if "temp" in h: pill(sd, x, 20, f"{h['temp']}°C", (BLUE + (240,)), size=38, anchor="r", icon="temp")
    return im.resize((W, 150), Image.LANCZOS)

# ================================================================ VOZ
def tts(text, voice, speed):
    key = hashlib.md5(f"{text}|{voice}|{speed}".encode()).hexdigest()[:16]; p = os.path.join(CACHE, key + ".npy")
    if not os.path.exists(p):
        global _KOK
        if "_KOK" not in globals():
            from kokoro_onnx import Kokoro
            _KOK = Kokoro(os.environ.get("TTS_DIR", "/home/claude/tts") + "/kokoro.onnx", os.environ.get("TTS_DIR", "/home/claude/tts") + "/voices.bin")
        a, sr = _KOK.create(text.replace("*", ""), voice=voice, speed=speed, lang="es")
        assert sr == SR; np.save(p, a.astype(np.float32))
    a = np.load(p)
    env = np.abs(a); thr = 0.02 * env.max(); idx = np.where(env > thr)[0]
    a = a[max(0, idx[0] - 600): idx[-1] + 2400] if len(idx) else a
    return a / (np.abs(a).max() + 1e-6) * 0.9

def word_times(words, dur, lead):
    wts = []
    for w in words:
        base = len(w.strip("*.,?!¿¡…")) + 2
        if w.endswith(("...", "…")): base += 7
        elif w.endswith((".", "?", "!")): base += 4
        elif w.endswith(","): base += 3
        wts.append(base)
    tot = sum(wts); t = lead; out = []
    for x in wts:
        d = dur * x / tot; out.append((t, t + d)); t += d
    return out

# ================================================================ ESCENAS
SNOW = [(random.random() * W, random.random() * H, random.uniform(2, 8), random.uniform(0.5, 1.5)) for _ in range(320)]
def snowfall(d, t, wind=60, speed=1.0, n=220):
    for i, (x0, y0, r, v) in enumerate(SNOW[:n]):
        y = (y0 + t * 170 * v * speed) % (H + 40) - 20
        x = (x0 + t * wind * v + math.sin(t * 1.3 + i) * 18) % (W + 40) - 20
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, int(110 + 140 * r / 8)))

def cam(bg, t, dur, zoom=(1.0, 1.08), shake=0.0, pan=(0, 0), aspect=(W, H), center=(0.5, 0.5), rng=None):
    z = lerp(zoom[0], zoom[1], ease(t / dur) * 0.6 + (t / dur) * 0.4)
    base = min(bg.width / aspect[0], bg.height / aspect[1])
    cw, ch = aspect[0] * base / z, aspect[1] * base / z
    sx = (rng.uniform(-1, 1) if rng else 0) * shake; sy = (rng.uniform(-1, 1) if rng else 0) * shake
    cx = bg.width * center[0] + pan[0] * (t / dur - 0.5) + sx; cy = bg.height * center[1] + pan[1] * (t / dur - 0.5) + sy
    cx = min(max(cx, cw / 2), bg.width - cw / 2); cy = min(max(cy, ch / 2), bg.height - ch / 2)
    return bg.crop((int(cx - cw / 2), int(cy - ch / 2), int(cx + cw / 2), int(cy + ch / 2))).resize(aspect, Image.BILINEAR)

def make_vig():
    y, x = np.ogrid[:H, :W]; r = np.sqrt(((x - W / 2) / (W * 0.72)) ** 2 + ((y - H / 2) / (H * 0.66)) ** 2)
    v = np.zeros((H, W, 4), np.uint8); v[..., 3] = (np.clip(r - 0.5, 0, 1) * 380).clip(0, 200).astype(np.uint8); return Image.fromarray(v, "RGBA")
VIG = None; GRAIN = None

def finish(frame, f):
    global GRAIN
    if GRAIN is None:
        g = np.random.default_rng(3).normal(0, 7, (4, H // 2, W // 2)).astype(np.int16); GRAIN = [np.repeat(np.repeat(x, 2, 0), 2, 1)[..., None] for x in g]
    a = np.asarray(frame, np.int16) + GRAIN[f % 4]
    return np.clip(a, 0, 255).astype(np.uint8)

def panel_overlay(letter, text, col, pct=None):
    """Tarjeta de opción sobre una mitad de pantalla (1080x960), dibujada a 2x."""
    K = 2; im = Image.new("RGBA", (W * K, 960 * K)); sd = SD(im, K)
    # degradado inferior
    grad = np.zeros((960 * K, W * K, 4), np.uint8); ys = np.linspace(0, 1, 960 * K)
    grad[..., :3] = np.array(col) // 3; grad[..., 3] = (np.clip((ys - 0.35) / 0.65, 0, 1) ** 1.4 * 235)[:, None]
    im = Image.alpha_composite(im, Image.fromarray(grad, "RGBA")); sd = SD(im, K)
    top = 250 if letter == "A" else 60
    sd.ellipse([56, top, 236, top + 180], fill=col, outline=(255, 255, 255), width=7)
    fl = font(FONT_D, 130 * K); bb = fl.getbbox(letter)
    sd.d.text(((146) * K - (bb[0] + bb[2]) / 2, (top + 90) * K - (bb[1] + bb[3]) / 2), letter, font=fl, fill=(255, 255, 255))
    ft = font(FONT_D, 92 * K); words = text.upper().split(); lines = [""]
    for w_ in words:
        if ft.getlength((lines[-1] + " " + w_).strip()) > (W - 140) * K: lines.append(w_)
        else: lines[-1] = (lines[-1] + " " + w_).strip()
    lh = 100; y0 = 960 - 70 - len(lines) * lh
    for i, ln in enumerate(lines):
        sd.d.text((70 * K, (y0 + i * lh) * K), ln, font=ft, fill=(255, 255, 255), stroke_width=5 * K, stroke_fill=(0, 0, 0))
    sd.rect([70, y0 - 30, 250, y0 - 16], 7, fill=col)
    return im.resize((W, 960), Image.LANCZOS)

def make_beat(ep, b, T0):
    global VIG
    if VIG is None: VIG = make_vig()
    kind = b["scene"]; dur = b["dur"]
    bg = build_bg(kind) if kind not in ("choice", "results") else None
    if kind == "phone": bg = build_bg("wreck").filter(ImageFilter.GaussianBlur(14))
    kar = Karaoke(b["_words"], b["_times"], y=b.get("y", 1180), size=b.get("size", 124)) if b.get("_words") and not b.get("no_caps") else None
    huds = {}
    panels = {}
    if kind in ("choice", "results"):
        for L, col in (("A", BLUE), ("B", ORA)):
            v = b[L + "_view"]; panels[L] = (build_bg(v[0]), v, panel_overlay(L, b[L] if kind == "choice" else b[L][0], col))
    env = b.get("_env")
    def frame_at(t):
        f = int(round((T0 + t) * FPS)); rng = random.Random(f); T = T0 + t
        shake = b.get("shake", 0) * max(0, 1 - t / 0.8)
        punch = 1 + 0.06 * (1 - ease(t / 0.25))
        if kind in ("choice", "results"):
            frame = Image.new("RGB", (W, H))
            for i, L in enumerate("AB"):
                pbg, v, ov = panels[L]
                half = cam(pbg, t, dur, (v[3] * punch, v[3] * 1.08), 0, (0, 0), (W, 960), (v[1], v[2]))
                if kind == "results":
                    win = b["A"][1] > b["B"][1]; is_w = (L == "A") == win
                    if not is_w and t > 1.6:
                        k = ease((t - 1.6) / 0.4); g = half.convert("L").convert("RGB")
                        half = Image.blend(half, Image.blend(g, Image.new("RGB", g.size), 0.45), k)
                hd = ImageDraw.Draw(half, "RGBA"); snowfall(hd, T + i * 3, 50, 0.8, 90)
                slide = int((1 - ease((t - i * 0.12) / 0.35)) * W) * (-1 if L == "A" else 1)
                half.paste(ov, (slide, 0), ov)
                if kind == "results":
                    pct = b[L][1]; prog = ease((t - 0.3) / 1.2); s = f"{round(pct * prog)}%"
                    win = (b["A"][1] > b["B"][1]) == (L == "A")
                    sz = 260 if not (win and t > 1.6) else int(260 * (1 + 0.25 * back((t - 1.6) / 0.3)))
                    ti = text_img(s, sz, YEL if (win and t > 1.6) else (255, 255, 255), 12)
                    half.paste(ti, ((W - ti.width) // 2, 400 - ti.height // 2 + (60 if L == "A" else -60)), ti)
                frame.paste(half, (0, i * 960))
            d = ImageDraw.Draw(frame, "RGBA")
            # divisor + barra de tiempo
            d.rectangle([0, 952, W, 968], fill=(10, 10, 16))
            if kind == "choice":
                cd0 = b.get("_cd0", dur - 3); prog = min(1, max(0, (t - cd0) / (dur - cd0 - 0.1)))
                if t > 0.5: d.rectangle([0, 953, int(W * (1 - prog)), 967], fill=YEL if prog < 0.7 else RED)
            else:
                ti = hud_title(f"RESULTADO PARTE {ep['parte'] - 1}")
                frame.paste(ti, ((W - ti.width) // 2, 175), ti)
            frame = frame.convert("RGBA")
        else:
            if kind == "phone":
                frame = cam(bg, t, dur, (1.05, 1.1), shake, (0, 0), rng=rng).convert("RGBA")
            else:
                z = b.get("zoom", (1.0, 1.08)); frame = cam(bg, t, dur, (z[0] * punch, z[1]), shake, tuple(b.get("pan", (0, 0))), center=tuple(b.get("center", (0.5, 0.5))), rng=rng).convert("RGBA")
            d = ImageDraw.Draw(frame, "RGBA")
            if kind in ("wreck", "crash"):
                for i in range(16):
                    ph = (T * 0.22 + i / 16) % 1
                    sx = W / 2 + 140 + math.sin(i * 2 + T) * 30 + ph * 200; sy = 1440 - ph * 900; r = 26 + ph * 95
                    d.ellipse([sx - r, sy - r, sx + r, sy + r], fill=(120, 110, 135, int(26 * (1 - ph) * min(1, ph * 5))))
                for i in range(14):
                    ph = (T * 0.8 + i / 14) % 1; fx = W / 2 + 100 + math.sin(i * 5.1 + T) * 70; fy = 1480 - ph * 340
                    d.ellipse([fx - 6, fy - 6, fx + 6, fy + 6], fill=(255, 190, 80, int(255 * (1 - ph))))
            if b.get("pancho"):
                pc = b["pancho"]; m = 0
                if env is not None and b.get("talk", True):
                    fi = int(t * FPS); m = env[fi] if fi < len(env) else 0
                lay, (ax, ay) = pancho_layer(pc[2], T, m, b.get("walk", False), not b.get("walk"), b.get("look", 0))
                x = pc[0] + b.get("walk_dx", 0) * t / dur
                frame.paste(lay, (int(x - ax), int(pc[1] - ay)), lay)
            if kind == "phone": draw_phone(frame, t, b)
            if kind == "sunset": draw_thermo(frame, t, dur, b)
            d = ImageDraw.Draw(frame, "RGBA")
            snowfall(d, T, b.get("wind", 60), b.get("snow", 1.0), b.get("snow_n", 200))
            frame.paste(VIG, (0, 0), VIG)
            if b.get("hud"):
                blink = int(t * 2.5) % 2 == 0 and b["hud"].get("bat", 99) <= 5
                k = blink
                if k not in huds: huds[k] = hud_img(ep, b["hud"], blink)
                frame.paste(huds[k], (0, 175), huds[k])
        if kar: kar.draw(frame, t)
        fl = b.get("flash", 0) * max(0, 1 - t / 0.35)
        if fl > 0: frame = Image.blend(frame, Image.new("RGBA", (W, H), (255, 255, 255, 255)), fl)
        return Image.fromarray(finish(frame.convert("RGB"), f))
    return frame_at

_ht = {}
def hud_title(s):
    if s not in _ht:
        im = Image.new("RGBA", (W * 2, 180)); sd = SD(im, 2); pill(sd, W / 2, 4, s, (255, 255, 255, 240), (10, 10, 20), 38, anchor="c"); _ht[s] = im.resize((W, 90), Image.LANCZOS)
    return _ht[s]

_phone = {}
def draw_phone(frame, t, b):
    if "img" not in _phone:
        K = 2; im = Image.new("RGBA", (W * K, H * K)); sd = SD(im, K)
        x0, y0, x1, y1 = 300, 380, 780, 1380
        sd.rect([x0 - 18, y0 - 18, x1 + 18, y1 + 18], 74, fill=(18, 18, 24), outline=(90, 90, 110), width=4)
        g = gradient([(0, (30, 40, 90)), (1, (8, 10, 24))], (x1 - x0) * K, (y1 - y0) * K)
        mask = Image.new("L", g.size, 0); ImageDraw.Draw(mask).rounded_rectangle([0, 0, g.width, g.height], 56 * K, fill=255)
        im.paste(g, (x0 * K, y0 * K), mask); sd = SD(im, K)
        sd.rect([x0 + 180, y0 + 22, x1 - 180, y0 + 56], 17, fill=(0, 0, 0))
        f = font(FONT_B, 30 * K); sd.d.text(((x0 + 44) * K, (y0 + 78) * K), "SIN SERVICIO", font=f, fill=(255, 255, 255, 220))
        for i in range(4): sd.rect([x1 - 130 + i * 20, y0 + 108 - i * 13, x1 - 117 + i * 20, y0 + 110], 2, fill=(90, 90, 110))
        sd.line([(x1 - 140, y0 + 66), (x1 - 46, y0 + 116)], fill=RED, width=7)
        f2 = font(FONT_D, 110 * K); sd.d.text(((x0 + 120) * K, (y0 + 200) * K), "17:42", font=f2, fill=(255, 255, 255, 235))
        bx, by = 390, 760
        sd.rect([bx, by, bx + 300, by + 150], 26, outline=(255, 255, 255), width=10); sd.rect([bx + 300, by + 45, bx + 324, by + 105], 8, fill=(255, 255, 255))
        _phone["img"] = im.resize((W, H), Image.LANCZOS)
        _phone["pct"] = text_img(f"{b.get('bat', 3)}%", 190, RED, 0, shadow=False)
    frame.paste(_phone["img"], (0, 0), _phone["img"])
    d = ImageDraw.Draw(frame, "RGBA")
    if int(t * 2.5) % 2 == 0: d.rounded_rectangle([408, 778, 426, 892], 6, fill=RED)
    p = _phone["pct"]; frame.paste(p, ((W - p.width) // 2, 960), p)

def draw_thermo(frame, t, dur, b):
    a, z = b.get("temp_from", -18), b.get("temp_to", -30); v = lerp(a, z, ease((t - 0.6) / (dur * 0.7)))
    im = Image.new("RGBA", (300 * 2, 620 * 2)); sd = SD(im, 2); x = 120
    sd.rect([x, 20, x + 64, 500], 32, fill=(255, 255, 255, 235), outline=NAVY, width=5)
    lvl = (v + 40) / 50; sd.rect([x + 16, 40 + 420 * (1 - lvl), x + 48, 510], 16, fill=BLUE)
    sd.ellipse([x - 28, 450, x + 92, 570], fill=BLUE, outline=NAVY, width=5)
    im = im.resize((300, 620), Image.LANCZOS); frame.paste(im, (720, 330), im)
    ti = text_img(f"{round(v)}°C", 150, (255, 255, 255) if v > -25 else (140, 200, 255), 9); frame.paste(ti, (790 - ti.width, 520), ti)

# ================================================================ AUDIO
def build_audio(ep, total, voice_tracks):
    n = int(total * SR) + SR; out = np.zeros(n); tt = np.arange(n) / SR; rng = np.random.default_rng(1)
    def add(t0, sig, g=1.0):
        i = int(t0 * SR); j = min(n, i + len(sig))
        if 0 <= i < n: out[i:j] += sig[: j - i] * g
    # música: pulso tenso en La menor
    bpm = 104; step = 60 / bpm / 2; notes = [45, 45, 52, 45, 48, 45, 52, 50, 45, 45, 52, 45, 53, 52, 48, 47]
    mus = np.zeros(n)
    k = 0; t = 0
    while t < total:
        f0 = 440 * 2 ** ((notes[k % 16] - 69) / 12); L = int(step * SR * 0.95); x = np.arange(L) / SR
        s = (np.sin(2 * np.pi * f0 * x) + 0.35 * np.sign(np.sin(2 * np.pi * f0 * x)) * 0.5) * np.exp(-x * 7)
        i = int(t * SR); mus[i:i + L] += s[: max(0, min(L, n - i))] * 0.22
        if k % 4 == 0:
            kx = np.arange(int(0.18 * SR)) / SR; mus[i:i + len(kx)] += 0.5 * np.sin(2 * np.pi * 55 * kx * (1 - kx * 2)) * np.exp(-kx * 20)
        if k % 2 == 1:
            hx = rng.standard_normal(int(0.03 * SR)) * np.exp(-np.arange(int(0.03 * SR)) / SR * 150); mus[i:i + len(hx)] += np.diff(np.r_[0, hx]) * 0.12
        k += 1; t += step
    pad = 0.05 * (np.sin(2 * np.pi * 110 * tt) + np.sin(2 * np.pi * 130.8 * tt) + np.sin(2 * np.pi * 164.8 * tt)) * (0.6 + 0.4 * np.sin(tt * 0.4))
    wind = np.convolve(rng.standard_normal(n), np.ones(300) / 300, "same") * 1.2
    vo = np.zeros(n)
    for t0, a in voice_tracks:
        i = int(t0 * SR); j = min(n, i + len(a)); vo[i:j] += a[: j - i]
    # ducking
    e = np.convolve(np.abs(vo), np.ones(2400) / 2400, "same"); duck = 1 - 0.55 * np.clip(e * 12, 0, 1)
    out += (mus + pad) * duck * 0.8 + wind * duck
    def boom(L=1.2, f=46):
        x = np.arange(int(L * SR)) / SR; return 0.9 * np.sin(2 * np.pi * f * x * (1 - x * 0.3)) * np.exp(-x * 3.5) + 0.25 * rng.standard_normal(len(x)) * np.exp(-x * 16)
    def whoosh(L=0.45):
        x = np.arange(int(L * SR)) / SR; s = np.convolve(rng.standard_normal(len(x)), np.ones(30) / 30, "same"); return 1.4 * s * np.sin(np.pi * x / L) ** 2
    def tick():
        x = np.arange(int(0.05 * SR)) / SR; return 0.35 * np.sin(2 * np.pi * 1600 * x) * np.exp(-x * 90)
    def riser(L):
        x = np.arange(int(L * SR)) / SR; return 0.16 * np.sin(2 * np.pi * (200 + 700 * (x / L) ** 2) * x) * (x / L)
    def ding():
        x = np.arange(int(0.9 * SR)) / SR; return 0.28 * (np.sin(2 * np.pi * 880 * x) + 0.5 * np.sin(2 * np.pi * 1320 * x)) * np.exp(-x * 5)
    t0 = 0
    for b in ep["beats"]:
        if t0 > 0: add(t0 - 0.18, whoosh())
        if b.get("sfx") == "boom": add(t0, boom())
        if b.get("sfx") == "hit": add(t0, boom(0.7, 70), 0.8)
        if b["scene"] == "results": add(t0 + 0.3, riser(1.3)); add(t0 + 1.6, boom(0.6, 90), 0.7); add(t0 + 1.6, ding())
        if b["scene"] == "choice":
            cd0 = b["_cd0"]
            for k in range(int((b["dur"] - cd0) * 2)): add(t0 + cd0 + k * 0.5, tick())
        t0 += b["dur"]
    out += vo * 1.0
    out = np.tanh(out * 1.1) * 0.92
    out = out[: int(total * SR)]; fade = int(0.35 * SR); out[-fade:] *= np.linspace(1, 0, fade)
    return (out * 32767).astype(np.int16)

# ================================================================ MAIN
def prepare(ep):
    voice = ep.get("voz", "em_alex"); speed = ep.get("velocidad", 1.08)
    T = 0; tracks = []
    for b in ep["beats"]:
        say = b.get("say")
        if say:
            a = tts(say, b.get("voz", voice), b.get("velocidad", speed)); vd = len(a) / SR; lead = 0.12
            cap = b.get("cap", say); words = cap.split()
            b["_words"] = words; b["_times"] = word_times(words, vd, lead)
            env = np.array([np.sqrt(np.mean(a[int(i / FPS * SR): int((i + 1) / FPS * SR)] ** 2) + 1e-9) for i in range(int(vd * FPS) + 2)])
            b["_env"] = np.clip(np.nan_to_num(np.r_[np.zeros(int(lead * FPS)), env]) * 6, 0, 1)
            extra = 3.2 if b["scene"] == "choice" else b.get("pausa", 0.35)
            b["dur"] = max(b.get("min", 0), round(lead + vd + extra, 2))
            if b["scene"] == "choice": b["_cd0"] = lead + vd + 0.1
            tracks.append((T + lead, a))
        else:
            b.setdefault("dur", 3.0)
            if b["scene"] == "choice": b["_cd0"] = 0.6
        T += b["dur"]
    return T, tracks

def main(cfg, out):
    ep = json.load(open(cfg)); total, tracks = prepare(ep)
    tmp = out + "_parts"; os.makedirs(tmp, exist_ok=True); parts = []; T0 = 0
    only = os.environ.get("ONLY")
    for i, b in enumerate(ep["beats"]):
        pth = os.path.join(tmp, f"b{i:02d}.mp4"); parts.append(pth)
        if only is None or str(i) in only.split(","):
            fa = make_beat(ep, b, T0); n = int(round(b["dur"] * FPS)); print(f"escena {i} {b['scene']} {b['dur']}s", flush=True)
            p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                                  "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", pth + ".tmp.mp4"], stdin=subprocess.PIPE)
            for f in range(n): p.stdin.write(fa(f / FPS).tobytes())
            p.stdin.close(); assert p.wait() == 0; os.replace(pth + ".tmp.mp4", pth)
        T0 += b["dur"]
    with open(os.path.join(tmp, "list.txt"), "w") as f:
        for p in parts: f.write(f"file '{os.path.abspath(p)}'\n")
    real = sum(int(round(b["dur"] * FPS)) for b in ep["beats"]) / FPS
    wav = os.path.join(tmp, "audio.wav")
    with wave.open(wav, "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(build_audio(ep, real, tracks).tobytes())
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", os.path.join(tmp, "list.txt"), "-i", wav, "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest", "-movflags", "+faststart", out + ".tmp.mp4"], check=True)
    os.replace(out + ".tmp.mp4", out); print("listo", out, round(real, 1), "s")

if __name__ == "__main__":
    if sys.argv[1] == "preview":
        ep = json.load(open(sys.argv[2])); prepare(ep); bi = int(sys.argv[3])
        T0 = sum(x["dur"] for x in ep["beats"][:bi]); make_beat(ep, ep["beats"][bi], T0)(float(sys.argv[4])).save(sys.argv[5])
    else: main(sys.argv[1], sys.argv[2])

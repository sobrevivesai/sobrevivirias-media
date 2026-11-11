#!/usr/bin/env python3
"""PISO 33 v5 — estilo ilustrado a mano (contornos temblorosos, paleta apagada, subtítulo de una palabra,
fichas de datos de supervivencia). Uso: python3 beanie.py eps5/p1.json out.mp4 | preview eps5/p1.json <beat> <t> out.png"""
import json, math, os, random, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import serie2 as S
import piso as P
from serie2 import W, H, FPS, SR, SD, font, FONT_D, FONT_B, ease, back, lerp, cam

BW, BH = S.BW, S.BH; K = 2
HAND = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fonts", "Patrick.ttf")
# ---------------------------------------------------------------- PALETA (apagada, cálida)
OUT = (44, 34, 34); HEAD = (246, 241, 230); LEG = (52, 46, 50)
CREAM = (252, 229, 198); CREAM_D = (226, 200, 168); TXT = (40, 30, 30); GREY = (140, 120, 110)
NSKY0 = (52, 48, 78); NSKY1 = (120, 96, 120); NB1 = (78, 72, 104); NB2 = (62, 58, 86); NB3 = (48, 46, 68)
LIT = (246, 210, 150); FIRE = (236, 128, 70)
WARM_WALL = (196, 176, 152); WARM_FLOOR = (150, 128, 110); WARM_D = (164, 144, 122)
DARK_WALL = (88, 84, 108); DARK_FLOOR = (62, 58, 78); DARK_D = (72, 68, 92)
WOOD = (150, 108, 78); WOOD_D = (116, 82, 58); STEEL = (170, 172, 176)
JACKET = (112, 126, 76); BAG = (82, 96, 58); BAND = (196, 62, 52)
LJACKET = (150, 102, 136); HAIR = (92, 58, 44)
ZHEAD = (178, 188, 162); ZCLOTH = (112, 112, 104); ZEYE = (48, 36, 36)
TEALC = (78, 146, 140); MUST = (214, 150, 66); REDC = (190, 64, 54)

# ================================================================ dibujo "a mano"
class SK(SD):
    """Igual que SD pero con contorno tembloroso."""
    def __init__(self, img, k=K, seed=1):
        super().__init__(img, k); self.r = random.Random(seed)
    def wob(self, pts, closed=True, amp=1.4, step=24):
        out = []; n = len(pts); segs = n if closed else n - 1
        for i in range(segs):
            a, b = pts[i], pts[(i + 1) % n]; L = math.dist(a, b); m = max(1, int(L / step))
            for j in range(m):
                t = j / m; out.append((lerp(a[0], b[0], t) + self.r.uniform(-amp, amp), lerp(a[1], b[1], t) + self.r.uniform(-amp, amp)))
        if not closed: out.append(pts[-1])
        else: out.append(out[0])
        return out
    def sline(self, pts, w=4.5, col=OUT, closed=False):
        self.line(self.wob(pts, closed), fill=col, width=w)
    def srect(self, b, fill=None, w=4.5, col=OUT, line=True):
        if fill: self.rect(b, 0, fill=fill)
        if line and (b[2] - b[0]) > 24: self.sline([(b[0], b[1]), (b[2], b[1]), (b[2], b[3]), (b[0], b[3])], w, col, True)
    def spoly(self, pts, fill=None, w=4.5, col=OUT, line=True):
        if fill: self.poly(pts, fill=fill)
        if line: self.sline(pts, w, col, True)
    def sell(self, b, fill=None, w=4.5, col=OUT, line=True):
        if fill: self.ellipse(b, fill=fill)
        if line:
            cx, cy, rx, ry = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2, (b[2] - b[0]) / 2, (b[3] - b[1]) / 2
            n = max(16, int((rx + ry) / 6)); pts = [(cx + rx * math.cos(2 * math.pi * i / n), cy + ry * math.sin(2 * math.pi * i / n)) for i in range(n)]
            self.line(self.wob(pts, True, 1.0, 999), fill=col, width=w)

def grad(c0, c1, w, h):
    a = np.linspace(0, 1, h)[:, None, None]; g = np.array(c0)[None, None] * (1 - a) + np.array(c1)[None, None] * a
    return Image.fromarray(np.repeat(g, w, 1).astype(np.uint8), "RGB")

def glow(img, x, y, r, col, s=1.0):
    g = Image.new("RGB", img.size, 0); ImageDraw.Draw(g).ellipse([x - r, y - r, x + r, y + r], fill=tuple(int(c * s) for c in col))
    g = g.filter(ImageFilter.GaussianBlur(r / 2.2)); return Image.fromarray(np.clip(np.asarray(img, np.int16) + np.asarray(g, np.int16), 0, 255).astype(np.uint8))

def shade(img, col, a):
    return Image.blend(img, Image.new("RGB", img.size, col), a)

# ================================================================ PERSONAJES
def figure(sd, x, y, s=1.0, pose="stand", t=0.0, who="you", look=0.0, face=True, bag=None, tears=False, bitten=False):
    z = who == "zombie"; br = math.sin(t * 2.2) * 2 * s
    lean = 22 * s if z else 0
    hip = (x, y - 150 * s); neck = (x + lean, y - 258 * s + br); head = (neck[0] + (10 * s if z else 0), neck[1] - 50 * s)
    if pose == "sit":
        hip = (x, y - 40 * s); neck = (x + 8 * s, y - 150 * s + br); head = (neck[0], neck[1] - 50 * s)
    shL = (neck[0] - 24 * s, neck[1] + 12 * s); shR = (neck[0] + 24 * s, neck[1] + 12 * s)
    hpL = (hip[0] - 20 * s, hip[1]); hpR = (hip[0] + 20 * s, hip[1])
    lw = 10 * s
    # piernas
    if pose == "sit":
        legs = [((hip[0] - 8 * s, hip[1]), (x + 70 * s, y - 104 * s), (x + 108 * s, y)), ((hip[0] + 8 * s, hip[1]), (x + 62 * s, y - 96 * s), (x + 96 * s, y))]
    elif pose == "walk" or z:
        ph = t * (5 if not z else 2.2); a = math.sin(ph) * 28 * s
        legs = [((hip[0] - 8 * s, hip[1]), (x - 6 * s + a * 0.6, y - 74 * s), (x - 10 * s + a, y)), ((hip[0] + 8 * s, hip[1]), (x + 6 * s - a * 0.6, y - 74 * s), (x + 10 * s - a, y))]
    else:
        legs = [((hip[0] - 10 * s, hip[1]), (x - 14 * s, y - 74 * s), (x - 22 * s, y)), ((hip[0] + 10 * s, hip[1]), (x + 14 * s, y - 74 * s), (x + 22 * s, y))]
    for a_, b_, c_ in legs: sd.line([a_, b_, c_], fill=LEG, width=lw)
    for _, _, c_ in legs: sd.ellipse([c_[0] - 12 * s, c_[1] - 6 * s, c_[0] + 16 * s, c_[1] + 4 * s], fill=LEG)
    # mochila
    hasbag = bag if bag is not None else (who == "you")
    if hasbag and pose != "sit":
        bc = BAG if who == "you" else (96, 70, 96)
        sd.spoly([(neck[0] - 66 * s, neck[1] + 16 * s), (neck[0] - 18 * s, neck[1] + 14 * s), (hip[0] - 18 * s, hip[1] - 14 * s), (hip[0] - 66 * s, hip[1] - 10 * s)], fill=bc, w=4 * s)
    # torso (campera)
    tc = ZCLOTH if z else (LJACKET if who == "lucia" else (JACKET if who == "you" else (90, 96, 84)))
    tor = [shL, shR, hpR, hpL] if not z else [shL, shR, (hpR[0] + 6 * s, hpR[1]), (hip[0] + 6 * s, hip[1] + 14 * s), (hpL[0] + 4 * s, hpR[1] + 2 * s)]
    sd.spoly(tor, fill=tc, w=4.5 * s)
    # brazos
    A = []
    if z:
        sw = math.sin(t * 2.4) * 8 * s
        A = [(shR, (shR[0] + 56 * s, shR[1] + 8 * s + sw), (shR[0] + 108 * s, shR[1] + 4 * s + sw)), (shL, (shL[0] + 58 * s, shL[1] + 22 * s - sw), (shL[0] + 112 * s, shL[1] + 24 * s - sw))]
    elif pose == "flash":
        A = [(shR, (shR[0] + 48 * s, shR[1] + 28 * s), (shR[0] + 98 * s, shR[1] + 18 * s)), (shL, (shL[0] - 10 * s, shL[1] + 54 * s), (shL[0] - 12 * s, shL[1] + 104 * s))]
    elif pose == "hold":
        A = [(shL, (shL[0] - 6 * s, shL[1] + 60 * s), (shR[0] + 6 * s, shR[1] + 66 * s)), (shR, (shR[0] + 12 * s, shR[1] + 56 * s), (shL[0] + 10 * s, shL[1] + 70 * s))]
    elif pose == "sit":
        A = [(shR, (shR[0] + 40 * s, shR[1] + 46 * s), (shR[0] + 84 * s, shR[1] + 58 * s)), (shL, (shL[0] + 44 * s, shL[1] + 52 * s), (shL[0] + 90 * s, shL[1] + 64 * s))]
    elif pose == "walk":
        a = math.sin(t * 5) * 22 * s
        A = [(shL, (shL[0] - a * 0.5, shL[1] + 54 * s), (shL[0] - a, shL[1] + 104 * s)), (shR, (shR[0] + a * 0.5, shR[1] + 54 * s), (shR[0] + a, shR[1] + 104 * s))]
    elif pose == "point":
        A = [(shR, (shR[0] + 52 * s, shR[1] - 24 * s), (shR[0] + 104 * s, shR[1] - 52 * s)), (shL, (shL[0] - 8 * s, shL[1] + 54 * s), (shL[0] - 10 * s, shL[1] + 104 * s))]
    elif pose == "wall":
        A = [(shL, (shL[0] - 30 * s, shL[1] + 40 * s), (shL[0] - 44 * s, shL[1] + 90 * s)), (shR, (shR[0] + 30 * s, shR[1] + 40 * s), (shR[0] + 44 * s, shR[1] + 90 * s))]
    else:
        A = [(shL, (shL[0] - 8 * s, shL[1] + 54 * s), (shL[0] - 12 * s, shL[1] + 104 * s)), (shR, (shR[0] + 8 * s, shR[1] + 54 * s), (shR[0] + 12 * s, shR[1] + 104 * s))]
    for a_, b_, c_ in A: sd.line([a_, b_, c_], fill=OUT, width=lw * 0.9)
    hand = A[0][2]
    if pose == "flash":
        e = hand; sd.spoly([(e[0] - 6 * s, e[1] - 12 * s), (e[0] + 34 * s, e[1] - 14 * s), (e[0] + 34 * s, e[1] + 8 * s), (e[0] - 6 * s, e[1] + 10 * s)], fill=(70, 70, 76), w=3 * s)
    if pose == "hold" and who == "lucia":
        e = A[0][1]
        if bitten:
            sd.ellipse([e[0] - 20 * s, e[1] - 14 * s, e[0] + 20 * s, e[1] + 14 * s], fill=(214, 170, 150))
            for i in range(6):
                ang = i / 6 * 2 * math.pi; sd.ellipse([e[0] + 13 * s * math.cos(ang) - 3 * s, e[1] + 9 * s * math.sin(ang) - 3 * s, e[0] + 13 * s * math.cos(ang) + 3 * s, e[1] + 9 * s * math.sin(ang) + 3 * s], fill=(130, 30, 36))
        else:
            sd.sell([e[0] - 18 * s, e[1] - 14 * s, e[0] + 18 * s, e[1] + 14 * s], fill=(244, 240, 230), w=3 * s)
            sd.ellipse([e[0] - 6 * s, e[1] - 5 * s, e[0] + 6 * s, e[1] + 5 * s], fill=(176, 50, 48))
    # cabeza
    hx, hy = head; r = 46 * s
    if who == "lucia":
        sd.ellipse([hx - r - 9 * s, hy - r - 7 * s, hx + r + 9 * s, hy + r * 0.6], fill=HAIR)
        for sx in (-1, 1): sd.poly([(hx + sx * (r + 7 * s), hy - 4 * s), (hx + sx * (r + 5 * s), hy + 66 * s), (hx + sx * (r - 22 * s), hy + 54 * s), (hx + sx * (r - 20 * s), hy)], fill=HAIR)
    sd.sell([hx - r, hy - r, hx + r, hy + r], fill=ZHEAD if z else HEAD, w=4.5 * s)
    if who == "lucia": sd.chord([hx - r - 2 * s, hy - r - 5 * s, hx + r + 2 * s, hy + r * 0.3], 180, 360, fill=HAIR)
    if who == "you":
        sd.line([(hx - r * 0.97, hy - 15 * s), (hx + r * 0.97, hy - 15 * s)], fill=BAND, width=13 * s)
        fl = math.sin(t * 6) * 5 * s
        sd.poly([(hx - r + 3 * s, hy - 20 * s), (hx - r - 32 * s, hy - 30 * s + fl), (hx - r - 28 * s, hy - 12 * s + fl)], fill=BAND)
        sd.poly([(hx - r + 3 * s, hy - 14 * s), (hx - r - 24 * s, hy + 2 * s - fl), (hx - r - 12 * s, hy + 9 * s - fl)], fill=BAND)
    if who == "soldier":
        sd.chord([hx - r - 6 * s, hy - r - 8 * s, hx + r + 6 * s, hy + r * 0.5], 180, 360, fill=(80, 92, 64))
    if face:
        blink = (t % 3.7) < 0.12
        for sx in (-1, 1):
            ex = hx + sx * 16 * s + look * 9 * s; ey = hy + 4 * s
            if z: sd.ellipse([ex - 8 * s, ey - 7 * s, ex + 8 * s, ey + 7 * s], fill=ZEYE)
            elif blink: sd.line([(ex - 6 * s, ey), (ex + 6 * s, ey)], fill=OUT, width=4 * s)
            else: sd.ellipse([ex - 5.5 * s, ey - 5.5 * s, ex + 5.5 * s, ey + 5.5 * s], fill=OUT)
        if tears:
            ph = (t * 0.8) % 1
            for sx in (-1, 1):
                ex = hx + sx * 16 * s; ty = hy + 14 * s + ph * 30 * s
                sd.ellipse([ex - 4 * s, ty - 6 * s, ex + 4 * s, ty + 6 * s], fill=(150, 196, 230, int(255 * (1 - ph))))
        if z: sd.line([(hx - 12 * s, hy + 24 * s), (hx + 12 * s, hy + 20 * s)], fill=ZEYE, width=4 * s)
    return hand

# ================================================================ ESCENARIOS (estáticos)
def skyline(sk, rng, base, hmin, hmax, col, lit=0.08, wmin=110, wmax=230, line=True):
    x = -40
    while x < BW + 40:
        w_ = rng.randint(wmin, wmax); h_ = rng.randint(hmin, hmax)
        sk.srect([x, base - h_, x + w_, base + 700], fill=col, w=3.5, line=line)
        for wy in range(int(base - h_ + 26), int(base + 600), 46):
            for wx in range(int(x + 18), int(x + w_ - 26), 36):
                if rng.random() < lit: sk.rect([wx, wy, wx + 16, wy + 22], 0, fill=LIT)
        x += w_ + rng.randint(8, 26)

def city(img, x0, y0, x1, y1, day=False, fire=True, seed=3):
    sky = grad((150, 146, 140) if day else NSKY0, (206, 192, 172) if day else NSKY1, int((x1 - x0) * K), int((y1 - y0) * K))
    img.paste(sky, (int(x0 * K), int(y0 * K)))
    sub = Image.new("RGBA", img.size); sk = SK(sub, K, seed); r = random.Random(seed)
    if not day: sk.ellipse([x0 + 140, y0 + 120, x0 + 230, y0 + 210], fill=(238, 232, 214))
    skyline(sk, r, y1 - 300, 200, 520, (150, 144, 140) if day else NB1, 0 if day else 0.03)
    if fire and not day:
        for fx in (0.28, 0.72):
            for i in range(7):
                k = i / 7; rr = 50 + k * 110; cx = x0 + (x1 - x0) * fx + k * 120; cy = y1 - 380 - k * 520
                sk.ellipse([cx - rr, cy - rr * 0.8, cx + rr, cy + rr * 0.8], fill=(96, 84, 100, 120))
    skyline(sk, r, y1 - 90, 160, 460, (128, 122, 122) if day else NB2, 0 if day else 0.06)
    skyline(sk, r, y1 + 70, 120, 380, (108, 102, 104) if day else NB3, 0 if day else 0.09, 170, 300)
    m = np.zeros((img.height, img.width), np.uint8); m[int(y0 * K):int(y1 * K), int(x0 * K):int(x1 * K)] = 255
    a = (np.asarray(sub)[..., 3].astype(np.uint16) * m // 255).astype(np.uint8); img.paste(sub, (0, 0), Image.fromarray(a))

def room(sk, wall, floor, fy=1640):
    sk.rect([0, 0, BW, fy], 0, fill=wall); sk.rect([0, fy, BW, BH], 0, fill=floor)
    sk.sline([(0, fy), (BW, fy)], 5)
    sk.rect([0, fy - 26, BW, fy], 0, fill=tuple(int(c * 0.85) for c in wall)); sk.sline([(0, fy - 26), (BW, fy - 26)], 3.5)

def window(sk, x0, y0, x1, y1, frame=(70, 64, 80)):
    sk.rect([x0 - 26, y0 - 26, x1 + 26, y0], 0, fill=frame); sk.rect([x0 - 26, y1, x1 + 26, y1 + 26], 0, fill=frame)
    sk.rect([x0 - 26, y0, x0, y1], 0, fill=frame); sk.rect([x1, y0, x1 + 26, y1], 0, fill=frame)
    sk.rect([(x0 + x1) / 2 - 10, y0, (x0 + x1) / 2 + 10, y1], 0, fill=frame)
    sk.srect([x0 - 26, y0 - 26, x1 + 26, y1 + 26], line=True); sk.srect([x0, y0, x1, y1], line=True)
    sk.srect([x0 - 46, y1 + 26, x1 + 46, y1 + 56], fill=tuple(int(c * 1.2) for c in frame))

def door(sk, cx, top, bot, w=440):
    sk.srect([cx - w / 2 - 28, top - 28, cx + w / 2 + 28, bot], fill=(84, 76, 96))
    sk.srect([cx - w / 2, top, cx + w / 2, bot], fill=WOOD)
    sk.srect([cx - w / 2 + 54, top + 64, cx + w / 2 - 54, top + (bot - top) * 0.45], fill=WOOD_D)
    sk.srect([cx - w / 2 + 54, top + (bot - top) * 0.52, cx + w / 2 - 54, bot - 64], fill=WOOD_D)
    sk.sell([cx + w / 2 - 80, top + (bot - top) * 0.5 - 18, cx + w / 2 - 44, top + (bot - top) * 0.5 + 18], fill=STEEL)
    sk.sell([cx - 13, top + 170, cx + 13, top + 196], fill=STEEL)
    sk.sline([(cx + w / 2 - 120, top + 260), (cx + w / 2 - 70, top + 320), (cx + w / 2 - 120, top + 380)], 7, STEEL)

BG = {}
def bg(kind):
    if kind in BG: return BG[kind]
    img = Image.new("RGB", (BW * K, BH * K), DARK_WALL); sk = SK(img, K, hash(kind) % 997)
    if kind in ("hook", "window_night", "signal", "heli", "window_day"):
        day = kind == "window_day"
        room(sk, (122, 114, 120) if day else DARK_WALL, (100, 92, 98) if day else DARK_FLOOR, 1700)
        x0, y0, x1, y1 = 110, 270, BW - 110, 1500
        city(img, x0, y0, x1, y1, day=day, seed={"hook": 3, "window_night": 3, "window_day": 5, "signal": 7, "heli": 9}[kind]); sk = SK(img, K, 5)
        if kind == "signal":
            sk.srect([x0 + 430, 930, x1, y1], fill=(44, 42, 60)); sk.srect([x0 + 410, 905, x1, 935], fill=(70, 66, 88))
        window(sk, x0, y0, x1, y1, (84, 78, 92) if day else (64, 58, 76))
    elif kind == "tv":
        room(sk, WARM_WALL, WARM_FLOOR, 1640)
        for x in range(0, BW, 160): sk.line([(x, 0), (x, 1614)], fill=WARM_D, width=3)
        sk.srect([BW / 2 - 470, 480, BW / 2 + 470, 1040], fill=(36, 32, 36))
        sk.srect([BW / 2 - 24, 1040, BW / 2 + 24, 1110], fill=(60, 54, 56)); sk.srect([BW / 2 - 300, 1108, BW / 2 + 300, 1140], fill=WOOD_D)
        sk.srect([BW / 2 - 330, 1140, BW / 2 + 330, 1420], fill=WOOD); sk.srect([BW / 2 - 300, 1180, BW / 2 - 20, 1390], fill=WOOD_D); sk.srect([BW / 2 + 20, 1180, BW / 2 + 300, 1390], fill=WOOD_D)
        sk.srect([BW - 230, 300, BW - 120, 400], fill=(230, 220, 190)); sk.sline([(BW - 175, 0), (BW - 175, 300)], 3)
    elif kind == "street":
        img = grad((92, 88, 96), (110, 104, 108), BW * K, BH * K); sk = SK(img, K, 4)
        sk.srect([210, -10, BW - 210, BH + 10], fill=(118, 114, 118))
        sk.srect([-10, -10, 210, BH + 10], fill=(150, 140, 136)); sk.srect([BW - 210, -10, BW + 10, BH + 10], fill=(150, 140, 136))
        for y in range(0, BH, 170): sk.rect([BW / 2 - 8, y, BW / 2 + 8, y + 90], 0, fill=(226, 206, 140))
        for (cx, cy, c) in ((430, 700, REDC), (820, 1120, (90, 112, 140)), (470, 1560, (176, 174, 170))):
            sk.srect([cx - 70, cy - 140, cx + 70, cy + 140], fill=c); sk.srect([cx - 54, cy - 70, cx + 54, cy + 10], fill=(60, 62, 72))
        sk.srect([-10, BH - 240, BW + 10, BH + 10], fill=(96, 88, 96))
        sk.rect([-10, BH - 248, BW + 10, BH - 232], 0, fill=STEEL); sk.sline([(0, BH - 248), (BW, BH - 248)], 4)
        for x in range(30, BW, 90): sk.rect([x - 5, BH - 240, x + 5, BH], 0, fill=STEEL)
    elif kind == "bath":
        room(sk, (176, 196, 190), (134, 140, 140), 1700)
        for y in range(0, 1674, 120):
            for x in range(0, BW, 120): sk.rect([x + 3, y + 3, x + 117, y + 117], 6, outline=(156, 178, 172), width=4)
        sk.srect([BW * 0.47, 940, BW * 0.5, 1060], fill=STEEL); sk.srect([BW * 0.4, 920, BW * 0.52, 956], fill=STEEL)
        # bañera en corte (paredes gruesas, interior visible)
        sk.spoly([(110, 1150), (BW - 110, 1150), (BW - 140, 1600), (140, 1600)], fill=(240, 238, 232))
        sk.spoly([(150, 1180), (BW - 150, 1180), (BW - 176, 1560), (176, 1560)], fill=(206, 214, 216))
        for xx in (210, BW - 230): sk.srect([xx, 1600, xx + 40, 1660], fill=STEEL)
    elif kind in ("dark", "kitchen", "lucia", "door", "door_bang", "radio", "bite", "stairs"):
        room(sk, DARK_WALL, DARK_FLOOR, 1680)
        if kind in ("dark", "lucia"):
            x0, y0, x1, y1 = 150, 340, 580, 1000
            img.paste(grad(NSKY0, NSKY1, (x1 - x0) * K, (y1 - y0) * K), (x0 * K, y0 * K)); sk = SK(img, K, 6)
            sk.sell([x0 + 260, y0 + 80, x0 + 350, y0 + 170], fill=(238, 232, 214)); window(sk, x0, y0, x1, y1)
            sk.poly([(x0, 1680), (x1, 1680), (x1 + 360, BH), (x0 + 160, BH)], fill=(80, 78, 104))
            sk.srect([BW - 380, 760, BW - 120, 1680], fill=(110, 92, 86)); sk.srect([BW - 360, 800, BW - 140, 1200], fill=(96, 80, 74)); sk.srect([BW - 360, 1240, BW - 140, 1640], fill=(96, 80, 74))
        if kind == "kitchen":
            sk.srect([BW * 0.14, 420, BW * 0.86, 1330], fill=WOOD_D); sk.srect([BW * 0.17, 450, BW * 0.83, 1300], fill=(64, 52, 52))
            for sy in (760, 1040): sk.srect([BW * 0.17, sy - 16, BW * 0.83, sy], fill=WOOD)
            for cx, cy in ((0.27, 744), (0.36, 744), (0.66, 744), (0.32, 1024), (0.72, 1024), (0.6, 1284)):
                x = BW * cx; sk.srect([x - 40, cy - 126, x + 40, cy], fill=REDC); sk.srect([x - 40, cy - 90, x + 40, cy - 44], fill=CREAM); sk.sell([x - 40, cy - 138, x + 40, cy - 114], fill=STEEL, w=3)
        if kind in ("door", "door_bang"):
            door(sk, BW / 2 + 120, 400, 1680); sk.rect([BW / 2 + 120 - 220, 1676, BW / 2 + 120 + 220, 1690], 0, fill=(255, 220, 150))
        if kind == "radio":
            sk.srect([-20, 1300, BW + 20, 1350], fill=WOOD); sk.srect([60, 1350, 100, 1680], fill=WOOD_D); sk.srect([BW - 100, 1350, BW - 60, 1680], fill=WOOD_D)
            cx = BW / 2; sk.srect([cx - 300, 1010, cx + 300, 1300], fill=(140, 120, 100))
            for i in range(9): sk.sell([cx - 260 + (i % 3) * 60, 1066 + (i // 3) * 66, cx - 226 + (i % 3) * 60, 1100 + (i // 3) * 66], fill=OUT, w=2)
            sk.srect([cx - 40, 1060, cx + 260, 1170], fill=(110, 150, 110)); sk.sell([cx + 160, 1200, cx + 240, 1280], fill=OUT, w=2); sk.sline([(cx + 250, 1010), (cx + 360, 650)], 7, STEEL)
        if kind == "bite": sk.rect([0, 0, BW, 1680], 0, fill=(150, 120, 104))
        if kind == "stairs":
            sk.rect([0, 0, BW, BH], 0, fill=(80, 84, 92))
            for i, y in enumerate((620, 1180, 1740)):
                d = 1 if i % 2 == 0 else -1; xa, xb = (140, BW - 200) if d > 0 else (BW - 140, 200)
                sk.spoly([(xa, y), (xb, y + 420), (xb, y + 470), (xa, y + 50)], fill=(108, 108, 116))
                n = 12
                for j in range(n):
                    px = lerp(xa, xb, j / n); py = lerp(y, y + 420, j / n); sk.line([(px, py), (px, py - 150)], fill=STEEL, width=4)
                sk.sline([(xa, y - 150), (xb, y + 270)], 6, STEEL)
                sk.srect([min(xa, xb) - 140 if d < 0 else max(xa, xb) - 20, y + 420, (min(xa, xb) + 20) if d < 0 else max(xa, xb) + 140, y + 470], fill=(108, 108, 116))
            sk.srect([BW / 2 - 110, 240, BW / 2 + 110, 320], fill=(70, 150, 90)); sk.d.text(((BW / 2 - 70) * K, 248 * K), "SALIDA", font=font(FONT_B, 40 * K), fill=(240, 250, 240))
    elif kind == "peephole":
        img = grad((116, 130, 112), (86, 98, 86), BW * K, BH * K); sk = SK(img, K, 8)
        vx, vy = BW / 2, 900
        sk.spoly([(0, 0), (vx - 120, vy - 160), (vx - 120, vy + 180), (0, BH)], fill=(132, 142, 120)); sk.spoly([(BW, 0), (vx + 120, vy - 160), (vx + 120, vy + 180), (BW, BH)], fill=(122, 132, 112))
        sk.spoly([(0, BH), (vx - 120, vy + 180), (vx + 120, vy + 180), (BW, BH)], fill=(98, 92, 86)); sk.spoly([(0, 0), (vx - 120, vy - 160), (vx + 120, vy - 160), (BW, 0)], fill=(150, 156, 140))
        sk.srect([vx - 120, vy - 160, vx + 120, vy + 180], fill=(48, 52, 50)); sk.srect([vx - 50, vy - 150, vx + 50, vy - 128], fill=(150, 236, 170))
        for k in (0.3, 0.62):
            for sd_ in (-1, 1):
                xa = vx + sd_ * (120 + (1 - k) * (BW / 2 - 120)); xb = xa + sd_ * 70 * (1 - k)
                sk.spoly([(xa, (vy - 160) * k + 40), (xb, (vy - 160) * k + 30), (xb, vy + 180 + (BH - vy - 180) * (1 - k) * 0.85), (xa, vy + 180 + (BH - vy - 180) * (1 - k) * 0.82)], fill=WOOD_D)
    elif kind in ("card", "map"):
        img = Image.new("RGB", (BW * K, BH * K), CREAM); sk = SK(img, K, 9)
        if kind == "map":
            for x in range(60, BW, 170): sk.rect([x, 0, x + 34, BH], 0, fill=CREAM_D)
            for y in range(80, BH, 170): sk.rect([0, y, BW, y + 34], 0, fill=CREAM_D)
            sk.srect([170, 1560, 330, 1700], fill=(60, 56, 70)); sk.srect([830, 480, 1050, 660], fill=(250, 246, 240))
            sk.d.text((902 * K, 492 * K), "H", font=font(FONT_B, 120 * K), fill=REDC)
    elif kind == "street_side":
        img = grad((168, 160, 166), (216, 196, 176), BW * K, BH * K); sk = SK(img, K, 10)
        r = random.Random(11); skyline(sk, r, 1250, 380, 900, (128, 120, 126), 0, 200, 340)
        sk.srect([-10, 1250, BW + 10, 1330], fill=(150, 144, 140)); sk.srect([-10, 1330, BW + 10, BH + 10], fill=(112, 108, 112))
        for x in range(0, BW, 200): sk.rect([x + 40, 1760, x + 140, 1776], 0, fill=(220, 210, 160))
        for (cx, c) in ((260, REDC), (900, (90, 112, 140))):
            sk.spoly([(cx - 190, 1560), (cx - 150, 1470), (cx - 60, 1440), (cx + 90, 1440), (cx + 170, 1500), (cx + 190, 1560)], fill=c)
            sk.srect([cx - 190, 1540, cx + 190, 1600], fill=c); sk.spoly([(cx - 120, 1490), (cx - 50, 1456), (cx + 70, 1456), (cx + 120, 1490)], fill=(70, 74, 86))
            for wx in (-110, 110): sk.sell([cx + wx - 40, 1570, cx + wx + 40, 1650], fill=(50, 46, 50))
    elif kind == "hospital":
        img = grad((176, 168, 180), (226, 200, 170), BW * K, BH * K); sk = SK(img, K, 12)
        sk.srect([140, 380, BW - 140, 1400], fill=(214, 206, 196))
        for wy in range(470, 1360, 130):
            for wx in range(200, BW - 200, 140): sk.srect([wx, wy, wx + 80, wy + 80], fill=(140, 150, 160), w=3)
        sk.srect([BW / 2 - 90, 250, BW / 2 + 90, 380], fill=(250, 246, 240)); sk.d.text(((BW / 2 - 40) * K, 252 * K), "H", font=font(FONT_B, 110 * K), fill=REDC)
        sk.srect([300, 200, 700, 230], fill=(90, 96, 80)); sk.sline([(500, 230), (500, 250)], 6)
        sk.srect([-10, 1400, BW + 10, BH + 10], fill=(120, 116, 118))
        for x in range(0, BW + 40, 46): sk.rect([x, 1180, x + 8, 1560], 0, fill=(86, 86, 92))
        sk.rect([0, 1196, BW, 1210], 0, fill=(86, 86, 92)); sk.rect([0, 1500, BW, 1514], 0, fill=(86, 86, 92))
        sk.srect([BW / 2 - 150, 1170, BW / 2 + 150, 1570], fill=(150, 150, 156))
    else:
        raise ValueError(kind)
    out = img.resize((BW, BH), Image.LANCZOS)
    if kind in ("hook", "window_night", "signal", "heli"):
        out = glow(out, 360, 1400, 260, (110, 50, 30), 0.9); out = glow(out, 900, 1440, 220, (110, 50, 30), 0.8)
    if kind == "tv": out = glow(out, BW // 2, 760, 600, (90, 30, 30), 0.6); out = glow(out, BW - 175, 340, 300, (90, 70, 40), 0.7)
    if kind in ("door", "door_bang"): out = glow(out, BW // 2 + 120, 1700, 260, (110, 90, 60), 0.8)
    if kind == "radio": out = glow(out, BW // 2 + 110, 1115, 220, (50, 120, 60), 0.9)
    if kind == "bite": out = glow(out, BW // 2, 900, 700, (90, 60, 30), 0.6)
    if kind == "stairs": out = glow(out, BW // 2, 280, 300, (40, 110, 60), 0.8)
    if kind == "bath": out = glow(out, BW // 2, 300, 600, (70, 70, 60), 0.5)
    # textura de papel
    n = np.random.default_rng(hash(kind) % 1000).normal(0, 5, (BH, BW, 1))
    out = Image.fromarray(np.clip(np.asarray(out, np.float32) + n, 0, 255).astype(np.uint8))
    BG[kind] = out; return out

# ================================================================ capa animada
def dynamic(kind, sd, t, T, dur, b):
    if kind == "street":
        rng = random.Random(4)
        for i in range(b.get("crowd", 90)):
            x = rng.uniform(230, BW - 230) + math.sin(T * 1.3 + i) * 8; y = rng.uniform(60, BH - 280); r = rng.uniform(16, 22)
            sd.line([(x - r * 1.4, y + 4 + math.sin(T * 2 + i) * 4), (x - r * 1.1, y + r * 2.2)], fill=ZCLOTH, width=7)
            sd.line([(x + r * 1.4, y + 4 - math.sin(T * 2 + i) * 4), (x + r * 1.1, y + r * 2.2)], fill=ZCLOTH, width=7)
            sd.ellipse([x - r * 1.3, y - r * 0.5, x + r * 1.3, y + r * 0.9], fill=ZCLOTH, outline=OUT, width=3)
            sd.ellipse([x - r, y - r, x + r, y + r], fill=ZHEAD, outline=OUT, width=3)
        for hx in (430, 810): sd.ellipse([hx - 34, BH - 272, hx + 34, BH - 224], fill=HEAD, outline=OUT, width=5)
    if kind == "tv":
        cx, cy, w, h = BW / 2, 760, 900, 520; on = int(t * 3) % 2 == 0
        sd.rect([cx - w / 2 + 10, cy - h / 2 + 10, cx + w / 2 - 10, cy + h / 2 - 10], 0, fill=(70, 30, 36))
        sd.rect([cx - w / 2 + 10, cy - h / 2 + 50, cx + w / 2 - 10, cy - h / 2 + 160], 0, fill=(196, 60, 54) if on else (160, 50, 46))
        sd.d.text(((cx - w / 2 + 44) * K, (cy - h / 2 + 62) * K), "ALERTA DE EMERGENCIA", font=font(FONT_B, 58 * K), fill=(250, 240, 230))
        sd.d.text(((cx - w / 2 + 44) * K, (cy - 50) * K), "NO SALGA DE SU CASA", font=font(HAND, 76 * K), fill=(250, 240, 230))
        sd.d.text(((cx - w / 2 + 44) * K, (cy + 40) * K), "NO ABRA LA PUERTA", font=font(HAND, 76 * K), fill=(250, 220, 140))
    if kind == "bath":
        f0, f1 = b.get("fill", [0.0, 1.0]); lv = ease(min(1, max(0, (t / max(0.1, dur) - f0) / (f1 - f0))))
        running = f0 * dur <= t <= f1 * dur + 0.2
        top = 1560 - 330 * lv
        if lv > 0.002:
            # agua dentro de la bañera (trapecio interior)
            xl = lerp(176, 150, (1560 - top) / 380); xr = BW - xl
            sd.poly([(xl, top), (xr, top), (BW - 176, 1560), (176, 1560)], fill=(110, 162, 196))
            sd.line([(xl, top), (xr, top)], fill=(170, 210, 230), width=6)
        if running:
            sd.rect([BW * 0.47 + 8, 1060, BW * 0.5 - 8, top], 0, fill=(150, 196, 226, 220))
    if kind == "door_bang":
        for i in range(3):
            xx = BW / 2 + 120 - 160 + i * 140 + math.sin(T * 3 + i) * 26; sd.rect([xx - 40, 1676, xx + 40, 1690], 0, fill=(30, 26, 30))
    if kind == "peephole":
        if b.get("far_zombie"): figure(sd, BW / 2 + math.sin(T * 0.6) * 18, 1076, 0.3 + t * 0.012, "walk", T, "zombie")
        figure(sd, BW / 2, 2080, 3.4, "stand", T, "lucia", look=0)
    if kind == "radio":
        for k_ in range(4):
            ph = (t * 0.8 + k_ / 4) % 1; rr = 60 + ph * 420; cx, cy = BW / 2 + 360, 650
            sd.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=(150, 230, 150, int(170 * (1 - ph))), width=6)
    if kind == "signal":
        figure(sd, BW * 0.66 - 40, 905, 0.42, "point", T, "other", face=False)
        if (int(t * 4) % 3) != 2:
            sd.ellipse([BW * 0.66 - 70, 770, BW * 0.66 + 70, 900], fill=(255, 250, 210, 110)); sd.ellipse([BW * 0.66 - 16, 820, BW * 0.66 + 16, 852], fill=(255, 255, 240))
    if kind == "heli":
        hx = BW * (1.15 - t / max(1, dur) * 1.5); hy = 540 + math.sin(t) * 16
        sd.poly([(hx, hy + 30), (hx - 300, 1500), (hx + 100, 1500)], fill=(255, 250, 220, 50))
        sd.ellipse([hx - 80, hy - 34, hx + 80, hy + 34], fill=(40, 36, 44)); sd.rect([hx + 60, hy - 10, hx + 230, hy + 6], 0, fill=(40, 36, 44)); sd.rect([hx + 220, hy - 30, hx + 236, hy + 6], 0, fill=(40, 36, 44))
        bl = 180 * abs(math.sin(T * 30)); sd.line([(hx - bl, hy - 48), (hx + bl, hy - 48)], fill=(40, 36, 44), width=8)
        if int(t * 6) % 2 == 0: sd.ellipse([hx - 9, hy + 26, hx + 9, hy + 44], fill=REDC)
    if kind == "map":
        pts = [(250, 1560), (250, 1180), (620, 1180), (620, 570), (830, 570)]
        L = sum(math.dist(pts[i], pts[i + 1]) for i in range(4)); target = L * ease(t / max(1, dur * 0.8)); acc = 0
        for i in range(4):
            sl = math.dist(pts[i], pts[i + 1]); e = min(1, max(0, (target - acc) / sl)); n = int(sl * e / 44)
            for j in range(n + 1):
                x = lerp(pts[i][0], pts[i + 1][0], j * 44 / sl); y = lerp(pts[i][1], pts[i + 1][1], j * 44 / sl); sd.ellipse([x - 11, y - 11, x + 11, y + 11], fill=OUT)
            acc += sl
        r = random.Random(9)
        for i in range(80):
            x = r.uniform(60, BW - 60) + math.sin(T + i) * 8; y = r.uniform(500, 1600); a = int(255 * ease((t - 0.3 - i * 0.015) / 0.3))
            sd.ellipse([x - 13, y - 13, x + 13, y + 13], fill=ZHEAD + (a,), outline=OUT + (a,), width=3)
        sd.d.text((150 * K, 1716 * K), "TÚ", font=font(HAND, 90 * K), fill=TXT)
        sd.d.text((700 * K, 670 * K), "HOSPITAL", font=font(HAND, 90 * K), fill=REDC)
    if kind == "card": draw_card(sd, t, dur, b["card"])
    if kind == "bite": figure(sd, BW / 2 - 40, 2060, 3.2, "hold", T, "lucia", bitten=b.get("bitten", False), tears=b.get("tears", False))
    if kind == "stairs" and b.get("zombie_up"):
        figure(sd, lerp(980, 820, t / max(1, dur)), lerp(1700 + 420, 1700 + 300, t / max(1, dur)) - 120, 0.75, "walk", T, "zombie")
    if kind == "street_side":
        r = random.Random(5)
        for i in range(b.get("zombies", 6)):
            x = r.uniform(80, BW - 80); y = r.uniform(1380, 1460); figure(sd, x + math.sin(T * 0.4 + i) * 6, y, r.uniform(0.45, 0.6), "stand", T + i, "zombie")
    if kind == "hospital":
        for i, x in enumerate((420, 820)):
            figure(sd, x, 1640, 0.8, "stand", T + i, "soldier", look=0)
        if b.get("searchlight"):
            ang = math.sin(T * 0.6) * 0.5; sx, sy = 980, 1100
            sd.poly([(sx, sy), (sx - 600 + ang * 300, 1900), (sx - 200 + ang * 300, 1900)], fill=(255, 250, 220, 50))
    for c in b.get("cast", []):
        x = c["x"] + c.get("dx", 0) * t / max(1, dur)
        hand = figure(sd, x, c["y"], c["s"], c.get("pose", "stand"), T + c.get("ph", 0), c.get("who", "you"), c.get("look", 0), c.get("face", True), c.get("bag"), c.get("tears", False))
        if c.get("pose") == "flash":
            fx, fy = hand[0] + 30 * c["s"], hand[1]; tx, ty = b.get("flash_to", (fx + 600, fy - 200)); jit = math.sin(T * 1.7) * 26
            ang = math.atan2(ty - fy, tx - fx); px, py = -math.sin(ang), math.cos(ang)
            for wd, al in ((300, 46), (170, 40)): sd.poly([(fx, fy), (tx + px * wd + jit, ty + py * wd), (tx - px * wd + jit, ty - py * wd)], fill=(255, 244, 210, al))
    if b.get("candle"):
        cx, cy = b["candle"]; sd.rect([cx - 12, cy - 60, cx + 12, cy], 4, fill=(240, 230, 210), outline=OUT, width=3)
        fl = math.sin(T * 13) * 3; sd.ellipse([cx - 9 + fl, cy - 92, cx + 9 + fl, cy - 62], fill=(250, 180, 90))

def draw_card(sd, t, dur, c):
    """Ficha de datos estilo infografía."""
    y = 600
    if c.get("icon") == "drop":
        sd.poly([(BW / 2, 330), (BW / 2 - 60, 440), (BW / 2 + 60, 440)], fill=(100, 160, 200)); sd.ellipse([BW / 2 - 62, 390, BW / 2 + 62, 500], fill=(100, 160, 200), outline=OUT, width=5)
    elif c.get("icon") == "can":
        sd.rect([BW / 2 - 50, 340, BW / 2 + 50, 490], 10, fill=REDC, outline=OUT, width=5); sd.rect([BW / 2 - 50, 380, BW / 2 + 50, 440], 0, fill=CREAM)
    elif c.get("icon") == "stairs":
        for i in range(5): sd.rect([BW / 2 - 100 + i * 40, 480 - i * 30, BW / 2 - 60 + i * 40, 490], 0, fill=OUT)
    elif c.get("icon") == "walk":
        figure(sd, BW / 2, 500, 0.6, "walk", t * 3, "you")
    def ctext(txt, yy, f, col, a=255):
        bb = f.getbbox(txt); sd.d.text(((BW / 2) * K - (bb[2] - bb[0]) / 2, yy * K), txt, font=f, fill=col + (a,))
    ctext(c.get("kicker", ""), y + 20, font(FONT_B, 52 * K), GREY)
    ctext(c["title"], y + 96, font(FONT_B, 124 * K), TXT)
    yy = y + 320
    for i, (lab, val) in enumerate(c.get("rows", [])):
        a = int(255 * ease((t - 0.6 - i * 0.5) / 0.3))
        if a <= 0: continue
        sd.d.text((110 * K, yy * K), lab, font=font(FONT_B, 54 * K), fill=TXT + (a,))
        f = font(FONT_B, 66 * K); bb = f.getbbox(val); sd.d.text(((BW - 110) * K - bb[2], (yy - 8) * K), val, font=f, fill=TXT + (a,))
        sd.line([(110, yy + 90), (BW - 110, yy + 90)], fill=CREAM_D + (a,), width=4); yy += 140
    if c.get("units"):
        u = c["units"]; n = u["n"]; cols = u.get("cols", 10); kind_ = u["kind"]; cross = u.get("cross", 0); cross_t = u.get("cross_t", 0.6)
        for i in range(n):
            a = int(255 * ease((t - 0.4 - i * 0.04) / 0.2))
            if a <= 0: continue
            x = BW / 2 - (min(n, cols) - 1) * 50 + (i % cols) * 100; yv = yy + 60 + (i // cols) * 130
            if kind_ == "can":
                sd.rect([x - 32, yv - 50, x + 32, yv + 50], 8, fill=REDC + (a,), outline=OUT + (a,), width=4); sd.rect([x - 32, yv - 20, x + 32, yv + 16], 0, fill=CREAM + (a,))
            else:
                sd.poly([(x, yv - 50), (x - 30, yv + 4), (x + 30, yv + 4)], fill=(100, 160, 200, a)); sd.ellipse([x - 31, yv - 20, x + 31, yv + 42], fill=(100, 160, 200, a), outline=OUT + (a,), width=4)
            if i >= n - cross and t > cross_t * dur:
                sd.line([(x - 40, yv - 56), (x + 40, yv + 56)], fill=REDC, width=10); sd.line([(x + 40, yv - 56), (x - 40, yv + 56)], fill=REDC, width=10)
        yy += 60 + ((n - 1) // cols + 1) * 130
    if c.get("big"):
        a = int(255 * ease((t - c.get("big_t", 1.2)) / 0.3))
        if a > 0:
            f = font(FONT_B, 96 * K); bb = f.getbbox(c["big"]); bw = (bb[2] - bb[0]) / K
            sd.rect([BW / 2 - bw / 2 - 40, yy + 30, BW / 2 + bw / 2 + 40, yy + 170], 26, fill=(255, 255, 255, int(a * 0.6)), outline=OUT + (a,), width=5)
            ctext(c["big"], yy + 46, f, TXT, a)
        yy += 200
    if c.get("foot"):
        a = int(255 * ease((t - c.get("foot_t", 1.6)) / 0.3))
        if a > 0: ctext(c["foot"], yy + 20, font(FONT_B, 42 * K), GREY, a)

# ================================================================ subtítulo de una palabra (estilo Beanie)
_cap = {}
def word_img(w):
    if w in _cap: return _cap[w]
    f = ImageFont.truetype(HAND, 150); asc, desc = f.getmetrics()
    tw = int(f.getlength(w)) + 80; hh = asc + desc + 80
    im = Image.new("RGBA", (tw, hh)); d = ImageDraw.Draw(im)
    m = Image.new("L", im.size, 0); ImageDraw.Draw(m).text((tw / 2, 40 + asc), w, font=f, anchor="ms", fill=255, stroke_width=16, stroke_fill=255)
    m = np.clip(np.asarray(m.filter(ImageFilter.GaussianBlur(9)), np.float32) * 1.6, 0, 235).astype(np.uint8)
    a = np.zeros((im.height, im.width, 4), np.uint8); a[..., 0] = 255; a[..., 1] = 246; a[..., 2] = 236; a[..., 3] = m
    im = Image.alpha_composite(im, Image.fromarray(a)); d = ImageDraw.Draw(im)
    d.text((tw / 2, 40 + asc), w, font=f, anchor="ms", fill=(36, 26, 28), stroke_width=3, stroke_fill=(36, 26, 28))
    _cap[w] = (im, 40 + asc); return _cap[w]

class OneWord:
    def __init__(self, words, times, y=1400):
        self.w = [x.strip("*").replace("*", "").upper() for x in words]; self.t = times; self.y = y
    def draw(self, frame, t):
        cur = None
        for i, (a, b) in enumerate(self.t):
            if a - 0.02 <= t: cur = i
        if cur is None or t > self.t[-1][1] + 0.5: return
        w = self.w[cur].strip(",;")
        if not w: return
        im, base = word_img(w)
        al = ease((t - self.t[cur][0] + 0.02) / 0.06)
        if al < 1:
            im = im.copy(); a = np.asarray(im).copy(); a[..., 3] = (a[..., 3] * al).astype(np.uint8); im = Image.fromarray(a)
        frame.paste(im, (int(W / 2 - im.width / 2), int(self.y - base)), im)

# ================================================================ HUD
_hud = {}
def hud_img(ep, h):
    key = json.dumps(h, sort_keys=True)
    if key in _hud: return _hud[key]
    im = Image.new("RGBA", (W * K, 200 * K)); sk = SK(im, K, 3)
    f = font(HAND, 64 * K); txt = f"DÍA {h.get('dia', 1)}"; tw = f.getlength(txt) / K
    sk.srect([40, 20, 40 + tw + 56, 120], fill=CREAM + (240,), w=4); sk.d.text(((40 + 28) * K, 70 * K), txt, font=f, fill=TXT, anchor="lm")
    f2 = font(FONT_B, 26 * K); sk.d.text((48 * K, 136 * K), f"PISO 33 · PARTE {ep['parte']}", font=f2, fill=(250, 244, 236), stroke_width=4 * K, stroke_fill=(40, 30, 30))
    x = W - 40
    items = []
    if "comida" in h and h["comida"] >= 0: items.append(("can", str(h["comida"]), REDC if h["comida"] <= 2 else TXT))
    if "agua" in h and h["agua"] >= 0: items.append(("drop", f"{h['agua']} L", TXT))
    for ic, val, col in items:
        tw = f.getlength(val) / K; x0 = x - tw - 110
        sk.srect([x0, 20, x, 120], fill=CREAM + (240,), w=4); sk.d.text(((x0 + 84) * K, 70 * K), val, font=f, fill=col, anchor="lm")
        cx, cy = x0 + 44, 70
        if ic == "drop":
            sk.poly([(cx, cy - 32), (cx - 20, cy + 2), (cx + 20, cy + 2)], fill=(100, 160, 200)); sk.ellipse([cx - 21, cy - 12, cx + 21, cy + 28], fill=(100, 160, 200))
        else:
            sk.rect([cx - 18, cy - 28, cx + 18, cy + 28], 5, fill=REDC); sk.rect([cx - 18, cy - 8, cx + 18, cy + 10], 0, fill=CREAM)
        x = x0 - 16
    im = im.resize((W, 200), Image.LANCZOS); _hud[key] = im; return im

def hud_at(b, t):
    h = dict(b.get("hud", {}))
    for k_, (a, z, f0, f1) in b.get("hud_anim", {}).items():
        p = min(1, max(0, (t / b["dur"] - f0) / max(1e-3, f1 - f0)))
        h[k_] = (round(lerp(a, z, ease(p)) / 5) * 5 if k_ == "agua" else (z if p >= 1 else a)) if a >= 0 else (z if p > 0 else -1)
    return h

# ================================================================ pantallas de elección
def panel(letter, text, col):
    im = Image.new("RGBA", (W * K, 960 * K)); sk = SK(im, K, ord(letter))
    top = 250 if letter == "A" else 70
    sk.sell([56, top, 216, top + 160], fill=col, w=5)
    f = font(HAND, 130 * K); sk.d.text((136 * K, (top + 84) * K), letter, font=f, fill=(255, 250, 240), anchor="mm")
    ft = font(HAND, 84 * K); words = text.upper().split(); lines = [""]
    for w_ in words:
        if ft.getlength((lines[-1] + " " + w_).strip()) > (W - 200) * K: lines.append(w_)
        else: lines[-1] = (lines[-1] + " " + w_).strip()
    lh = 92; y0 = 960 - 70 - len(lines) * lh
    sk.srect([50, y0 - 30, W - 50, 960 - 50], fill=CREAM + (240,), w=5)
    for i, ln in enumerate(lines): sk.d.text((86 * K, (y0 + i * lh + 46) * K), ln, font=ft, fill=TXT, anchor="lm")
    sk.rect([50, y0 - 30, 66, 960 - 50], 0, fill=col)
    return im.resize((W, 960), Image.LANCZOS)

_title = {}
def title_pill(s):
    if s not in _title:
        im = Image.new("RGBA", (W * K, 120 * K)); sk = SK(im, K, 2); f = font(HAND, 52 * K); tw = f.getlength(s) / K
        sk.srect([W / 2 - tw / 2 - 30, 10, W / 2 + tw / 2 + 30, 100], fill=CREAM + (245,), w=4); sk.d.text((W / 2 * K, 56 * K), s, font=f, fill=TXT, anchor="mm")
        _title[s] = im.resize((W, 120), Image.LANCZOS)
    return _title[s]

def pct_img(s, win):
    f = ImageFont.truetype(HAND, 250); tw = int(f.getlength(s)) + 80; asc, desc = f.getmetrics()
    im = Image.new("RGBA", (tw, asc + desc + 60)); d = ImageDraw.Draw(im)
    d.text((tw / 2, 30 + asc), s, font=f, anchor="ms", fill=(255, 246, 236) if not win else (255, 214, 90), stroke_width=12, stroke_fill=(40, 30, 30))
    return im

# ================================================================ cuadro
VIG = None
def make_beat(ep, b, T0):
    global VIG
    if VIG is None: VIG = S.make_vig()
    kind = b["scene"]; dur = b["dur"]
    cap = OneWord(b["_words"], b["_times"], b.get("y", 1420)) if b.get("_words") and not b.get("no_caps") else None
    if kind in ("choice", "results"):
        ovs = {L: panel(L, b[L] if kind == "choice" else b[L][0], TEALC if L == "A" else MUST) for L in "AB"}
    def frame_at(t):
        f = int(round((T0 + t) * FPS)); rng = random.Random(f); T = T0 + t
        punch = 1 + 0.05 * (1 - ease(t / 0.3))
        if kind in ("choice", "results"):
            frame = Image.new("RGB", (W, H))
            for i, L in enumerate("AB"):
                vb = dict(b[L + "_beat"]); vb.setdefault("dur", 4)
                full = render_scene(vb, t, T); v = b[L + "_view"]
                half = cam(full, t, dur, (v[2] * punch, v[2] * 1.06), 0, (0, 0), (W, 960), (v[0], v[1]))
                if kind == "results":
                    win = (b["A"][1] > b["B"][1]) == (L == "A")
                    if not win and t > 1.6:
                        k_ = ease((t - 1.6) / 0.4); g = half.convert("L").convert("RGB"); half = Image.blend(half, Image.blend(g, Image.new("RGB", g.size), 0.4), k_)
                slide = int((1 - ease((t - i * 0.12) / 0.35)) * W) * (-1 if L == "A" else 1); half.paste(ovs[L], (slide, 0), ovs[L])
                if kind == "results":
                    pct = b[L][1]; prog = ease((t - 0.3) / 1.2); win = (b["A"][1] > b["B"][1]) == (L == "A")
                    pi = pct_img(f"{round(pct * prog)}%", win and t > 1.6); half.paste(pi, ((W - pi.width) // 2, 420 - pi.height // 2 + (60 if L == "A" else -60)), pi)
                frame.paste(half, (0, i * 960))
            d = ImageDraw.Draw(frame, "RGBA"); d.rectangle([0, 950, W, 970], fill=OUT)
            if kind == "choice":
                cd0 = b["_cd0"]; prog = min(1, max(0, (t - cd0) / (dur - cd0 - 0.1)))
                if t > 0.5: d.rectangle([0, 953, int(W * (1 - prog)), 967], fill=(250, 220, 140) if prog < 0.7 else REDC)
            else:
                ti = title_pill(f"RESULTADO PARTE {ep['parte'] - 1}"); frame.paste(ti, (0, 170), ti)
            frame = frame.convert("RGBA")
        else:
            full = render_scene(b, t, T)
            shake = b.get("shake", 0) * max(0, 1 - t / 0.8)
            for kt in b.get("knocks", []):
                if 0 <= t - kt < 0.25: shake = max(shake, 20 * (1 - (t - kt) / 0.25))
            z = b.get("zoom", (1.0, 1.05))
            frame = cam(full, t, dur, (z[0] * punch, z[1]), shake, tuple(b.get("pan", (0, 0))), center=tuple(b.get("center", (0.5, 0.5))), rng=rng).convert("RGBA")
            if b.get("flicker") and t < 1.4 and rng.random() < 0.4: frame = Image.blend(frame, Image.new("RGBA", (W, H), (10, 8, 16, 255)), 0.7)
            if kind == "peephole":
                m = Image.new("L", (W, H), 255); ImageDraw.Draw(m).ellipse([W / 2 - 480, 820 - 480, W / 2 + 480, 820 + 480], fill=0)
                frame.paste((22, 18, 22), (0, 0), m.filter(ImageFilter.GaussianBlur(36)))
            if kind != "card": frame.paste(VIG, (0, 0), VIG)
            if b.get("hud"): hi = hud_img(ep, hud_at(b, t)); frame.paste(hi, (0, 150), hi)
        if cap: cap.draw(frame, t)
        fl = b.get("flashw", 0) * max(0, 1 - t / 0.35)
        if fl > 0: frame = Image.blend(frame, Image.new("RGBA", (W, H), (255, 250, 240, 255)), fl)
        if b.get("red"): frame = Image.blend(frame, Image.new("RGBA", (W, H), (130, 20, 20, 255)), 0.12 + 0.06 * math.sin(t * 5))
        return frame.convert("RGB")
    return frame_at

def render_scene(b, t, T):
    kind = b["scene"]; base = bg(kind)
    lay = Image.new("RGBA", (BW * K, BH * K)); sd = SK(lay, K, int(T * 6))
    dynamic(kind, sd, t, T, b.get("dur", 4), b)
    lay = lay.reduce(K); img = base.copy(); img.paste(lay, (0, 0), lay)
    if b.get("candle"):
        cx, cy = b["candle"]; img = glow(img, cx, cy - 76, 320 + math.sin(T * 9) * 10, (130, 80, 36), 0.9)
    if kind == "dark" and b.get("moon", True): img = glow(img, 360, 700, 380, (40, 40, 70), 0.6)
    if kind in ("hook", "window_night", "signal", "heli", "street", "street_side"):
        d = ImageDraw.Draw(img, "RGBA")
        for i, (x0, y0, r, v) in enumerate(P.PART[:80]):
            y = (y0 * 1.15 + T * 55 * v) % BH; x = (x0 * 1.15 + T * 18 * v + math.sin(T + i) * 20) % BW
            d.ellipse([x - r * 0.6, y - r * 0.6, x + r * 0.6, y + r * 0.6], fill=(255, 160, 90, 190) if i % 6 == 0 else (220, 214, 210, 100))
    return img

# ================================================================ main
def main(cfg, out):
    ep = json.load(open(cfg)); total, tracks = P.prepare(ep); print("duración", round(total, 1), flush=True)
    tmp = out + "_parts"; os.makedirs(tmp, exist_ok=True); parts = []; T0 = 0
    for i, b in enumerate(ep["beats"]):
        pth = os.path.join(tmp, f"b{i:02d}.mp4"); parts.append(pth)
        fa = make_beat(ep, b, T0); n = int(round(b["dur"] * FPS))
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                              "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p", pth + ".tmp.mp4"], stdin=subprocess.PIPE)
        for k_ in range(n): p.stdin.write(fa(k_ / FPS).tobytes())
        p.stdin.close(); assert p.wait() == 0; os.replace(pth + ".tmp.mp4", pth); T0 += b["dur"]
    with open(os.path.join(tmp, "list.txt"), "w") as f:
        for p_ in parts: f.write(f"file '{os.path.abspath(p_)}'\n")
    real = sum(int(round(b["dur"] * FPS)) for b in ep["beats"]) / FPS; wav = os.path.join(tmp, "audio.wav")
    with wave.open(wav, "wb") as w_: w_.setnchannels(1); w_.setsampwidth(2); w_.setframerate(SR); w_.writeframes(P.build_audio(ep, real, tracks).tobytes())
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", os.path.join(tmp, "list.txt"), "-i", wav, "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest", "-movflags", "+faststart", out + ".tmp.mp4"], check=True)
    os.replace(out + ".tmp.mp4", out); print("listo", out, round(real, 1), "s")

if __name__ == "__main__":
    if sys.argv[1] == "preview":
        ep = json.load(open(sys.argv[2])); P.prepare(ep); bi = int(sys.argv[3]); T0 = sum(x["dur"] for x in ep["beats"][:bi])
        make_beat(ep, ep["beats"][bi], T0)(float(sys.argv[4])).save(sys.argv[5])
    elif sys.argv[1] == "dur":
        ep = json.load(open(sys.argv[2])); print(round(P.prepare(ep)[0], 1))
    elif sys.argv[1] not in ("v6", "p6"): main(sys.argv[1], sys.argv[2])

# ================================================================ v6: voz mejorada, audio limpio, portada
import hashlib, inspect, tempfile
LANG = "es-419"
def tts2(text, voice="em_alex", speed=0.97):
    key = hashlib.md5(f"v6|{text}|{voice}|{speed}|{LANG}".encode()).hexdigest()[:16]; p = os.path.join(S.CACHE, key + ".npy")
    if not os.path.exists(p):
        global _K2
        if "_K2" not in globals():
            from kokoro_onnx import Kokoro
            _K2 = Kokoro(os.environ.get("TTS_DIR", "/home/claude/tts") + "/kokoro.onnx", os.environ.get("TTS_DIR", "/home/claude/tts") + "/voices.bin")
        a, sr = _K2.create(text.replace("*", ""), voice=voice, speed=speed, lang=LANG)
        raw = tempfile.mktemp(suffix=".f32"); out = tempfile.mktemp(suffix=".f32")
        a.astype(np.float32).tofile(raw)
        filt = ("highpass=f=85,lowpass=f=11000,equalizer=f=160:t=q:w=1:g=2,equalizer=f=350:t=q:w=1:g=-2,"
                "equalizer=f=3000:t=q:w=1.4:g=3,equalizer=f=7000:t=q:w=2:g=-2,"
                "acompressor=threshold=-22dB:ratio=3:attack=5:release=70:makeup=3,aecho=0.85:0.6:28|52:0.07|0.04")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "f32le", "-ar", str(sr), "-ac", "1", "-i", raw, "-af", filt, "-f", "f32le", "-ar", str(SR), "-ac", "1", out], check=True)
        a = np.fromfile(out, np.float32); os.remove(raw); os.remove(out); np.save(p, a)
    a = np.load(p); env = np.abs(a); idx = np.where(env > 0.02 * env.max())[0]
    a = a[max(0, idx[0] - 600): idx[-1] + 3000] if len(idx) else a
    return a / (np.abs(a).max() + 1e-6) * 0.92

def prepare2(ep):
    voice = ep.get("voz", "em_alex"); speed = ep.get("velocidad2", 0.97); T = 0; tracks = []
    for b in ep["beats"]:
        if b["scene"] == "cover" or not b.get("say"):
            b.setdefault("dur", 0.8); T += b["dur"]; continue
        a = tts2(b["say"], b.get("voz", voice), speed); vd = len(a) / SR; lead = 0.12
        words = b.get("cap", b["say"]).split(); b["_words"] = words; b["_times"] = S.word_times(words, vd, lead)
        extra = 3.4 if b["scene"] == "choice" else b.get("pausa", 0.35)
        b["dur"] = max(b.get("min", 0), round(lead + vd + extra, 2))
        if b["scene"] == "choice": b["_cd0"] = lead + vd + 0.1
        tracks.append((T + lead, a)); T += b["dur"]
    return T, tracks

_src = inspect.getsource(P.build_audio)
_src = _src.replace('wind = np.convolve(rng.standard_normal(n), np.ones(500) / 500, "same") * 1.0',
                    'wind = np.convolve(np.convolve(rng.standard_normal(n), np.ones(1200) / 1200, "same"), np.ones(600) / 600, "same") * 0.9')
_src = _src.replace('return 0.12 * s', 'return 0.035 * np.convolve(s, np.ones(20) / 20, "same")')
_src = _src.replace('add(t0, static(dd), 0.6)', 'add(t0, static(dd), 0.15)')
_src = _src.replace('out = np.tanh(out * 1.1) * 0.92', 'out = out / max(1e-6, np.abs(out).max()) * 0.9')
_src = _src.replace('def build_audio(', 'def build_audio2(')
exec(_src, P.__dict__); build_audio2 = P.build_audio2

def cover_frame(ep, b):
    vb = dict(b["bg_beat"]); vb.setdefault("dur", 4)
    full = render_scene(vb, 1.0, 1.0)
    img = cam(full, 0, 1, (b.get("zoom", 1.15), 1.15), 0, (0, 0), (W, H), tuple(b.get("center", (0.5, 0.5))))
    img = Image.blend(img, Image.new("RGB", (W, H), (20, 16, 26)), 0.45).convert("RGBA")
    img.paste(VIG, (0, 0), VIG)
    d = ImageDraw.Draw(img)
    def t(txt, y, size, fill, stroke):
        d.text((W / 2, y), txt, font=ImageFont.truetype(HAND, size), anchor="ms", fill=fill, stroke_width=stroke, stroke_fill=(36, 26, 28))
    t(ep.get("serie", "PISO 33"), 860, 270, (255, 246, 236), 14)
    p = title_pill(f"PARTE {ep['parte']}"); big = p.resize((int(p.width * 1.6), int(p.height * 1.6)), Image.LANCZOS)
    img.paste(big, ((W - big.width) // 2, 900), big)
    if ep.get("titulo"): t(ep["titulo"].upper(), 1220, 110, (255, 214, 120), 9)
    return img.convert("RGB")

def main2(cfg, out):
    global VIG
    if VIG is None: VIG = S.make_vig()
    ep = json.load(open(cfg))
    if ep.get("cover"): ep["beats"].insert(0, {"scene": "cover", "dur": 0.7, **ep["cover"]})
    total, tracks = prepare2(ep); print("duración", round(total, 1), flush=True)
    tmp = out + "_parts"; os.makedirs(tmp, exist_ok=True); parts = []; T0 = 0
    for i, b in enumerate(ep["beats"]):
        pth = os.path.join(tmp, f"b{i:02d}.mp4"); parts.append(pth); n = int(round(b["dur"] * FPS))
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                              "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p", pth + ".tmp.mp4"], stdin=subprocess.PIPE)
        if b["scene"] == "cover":
            fr = cover_frame(ep, b).tobytes()
            for k_ in range(n): p.stdin.write(fr)
        else:
            fa = make_beat(ep, b, T0)
            for k_ in range(n): p.stdin.write(fa(k_ / FPS).tobytes())
        p.stdin.close(); assert p.wait() == 0; os.replace(pth + ".tmp.mp4", pth); T0 += b["dur"]
    with open(os.path.join(tmp, "list.txt"), "w") as f:
        for p_ in parts: f.write(f"file '{os.path.abspath(p_)}'\n")
    real = sum(int(round(b["dur"] * FPS)) for b in ep["beats"]) / FPS; wav = os.path.join(tmp, "audio.wav")
    with wave.open(wav, "wb") as w_: w_.setnchannels(1); w_.setsampwidth(2); w_.setframerate(SR); w_.writeframes(build_audio2(ep, real, tracks).tobytes())
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", os.path.join(tmp, "list.txt"), "-i", wav, "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-af", "highpass=f=35,loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest", "-movflags", "+faststart", out + ".tmp.mp4"], check=True)
    os.replace(out + ".tmp.mp4", out); print("listo", out, round(real, 1), "s")

if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "v6":
    main2(sys.argv[2], sys.argv[3])

if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "p6":
    # vista previa con la voz v6: python3 beanie.py p6 episodio.json <beat> <t> salida.png
    if VIG is None: VIG = S.make_vig()
    _ep = json.load(open(sys.argv[2]))
    if _ep.get("cover"): _ep["beats"].insert(0, {"scene": "cover", "dur": 0.7, **_ep["cover"]})
    prepare2(_ep); _bi = int(sys.argv[3]); _b = _ep["beats"][_bi]; _T0 = sum(x["dur"] for x in _ep["beats"][:_bi])
    (cover_frame(_ep, _b) if _b["scene"] == "cover" else make_beat(_ep, _b, _T0)(float(sys.argv[4]))).save(sys.argv[5])

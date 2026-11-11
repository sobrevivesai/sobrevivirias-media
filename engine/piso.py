#!/usr/bin/env python3
"""PISO 33 — serie interactiva de zombis (voz en 2ª persona, subtítulos karaoke, elección final).
Uso:  python3 piso.py eps/p1.json out.mp4
      python3 piso.py preview eps/p1.json <beat> <t> out.png
"""
import json, math, os, random, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import serie2 as S
from serie2 import (W, H, FPS, SR, SD, gradient, add_light, stars, text_img, Karaoke, pill, tts, word_times,
                    make_vig, finish, cam, font, FONT_D, FONT_B, ease, back, lerp, YEL, RED, BLUE, ORA, NAVY, panel_overlay)
BW, BH = S.BW, S.BH
ZG = (78, 98, 72); ZD = (40, 52, 40); EYE = (230, 255, 120)

# ================================================================ personas
def person(sd, x, y, h, col, kind="human", sway=0.0, hair=None, arm="down"):
    """Silueta estilizada. (x,y)=pies. kind: human|zombie"""
    u = h / 100.0; tilt = sway * 6 * u
    hx = x + tilt * (2 if kind == "zombie" else 0.5)
    # piernas
    sd.poly([(x - 12 * u, y - 46 * u), (x - 14 * u + sway * 4 * u, y), (x - 5 * u + sway * 4 * u, y), (x - 1 * u, y - 46 * u)], fill=col)
    sd.poly([(x + 1 * u, y - 46 * u), (x + 6 * u - sway * 4 * u, y), (x + 14 * u - sway * 4 * u, y), (x + 12 * u, y - 46 * u)], fill=col)
    # torso
    sd.poly([(x - 16 * u, y - 46 * u), (x - 18 * u + tilt, y - 80 * u), (x + 18 * u + tilt, y - 80 * u), (x + 16 * u, y - 46 * u)], fill=col)
    sd.ellipse([x - 19 * u + tilt, y - 86 * u, x + 19 * u + tilt, y - 74 * u], fill=col)
    # cabeza
    hy = y - 92 * u + (4 * u if kind == "zombie" else 0)
    sd.ellipse([hx - 10 * u, hy - 11 * u, hx + 10 * u, hy + 11 * u], fill=col)
    if hair: sd.ellipse([hx - 12 * u, hy - 13 * u, hx + 12 * u, hy + 4 * u], fill=hair); sd.poly([(hx - 12 * u, hy - 2 * u), (hx - 15 * u, hy + 22 * u), (hx - 4 * u, hy + 10 * u)], fill=hair)
    # brazos
    if kind == "zombie" or arm == "forward":
        for s, dy in ((-1, 0), (1, 5)):
            sd.line([(x + s * 15 * u + tilt, y - 78 * u), (x + s * 8 * u + 34 * u + tilt, y - 70 * u + dy * u + sway * 5 * u)], fill=col, width=7 * u)
    elif arm == "hold":
        sd.line([(x - 17 * u + tilt, y - 78 * u), (x - 8 * u, y - 58 * u), (x + 8 * u, y - 62 * u)], fill=col, width=7 * u)
        sd.line([(x + 17 * u + tilt, y - 78 * u), (x + 20 * u, y - 56 * u)], fill=col, width=7 * u)
    else:
        sd.line([(x - 18 * u + tilt, y - 78 * u), (x - 22 * u, y - 46 * u)], fill=col, width=7 * u)
        sd.line([(x + 18 * u + tilt, y - 78 * u), (x + 22 * u, y - 46 * u)], fill=col, width=7 * u)
    if kind == "zombie":
        for s in (-1, 1): sd.ellipse([hx + s * 4.5 * u - 2.4 * u, hy - 2.5 * u, hx + s * 4.5 * u + 2.4 * u, hy + 1.5 * u], fill=EYE)

def zombie_small(d, x, y, h, t, i, col=(30, 36, 30)):
    """Zombi pequeño animado, dibujo directo (1x)."""
    sw = math.sin(t * 2.2 + i * 1.7); u = h / 100
    d.ellipse([x - 14 * u, y - 3 * u, x + 14 * u, y + 3 * u], fill=(0, 0, 0, 90))
    d.polygon([(x - 13 * u, y - 45 * u), (x - 10 * u + sw * 5 * u, y), (x + 10 * u - sw * 5 * u, y), (x + 13 * u, y - 45 * u)], fill=col)
    d.polygon([(x - 15 * u, y - 45 * u), (x - 15 * u + sw * 4 * u, y - 82 * u), (x + 15 * u + sw * 4 * u, y - 82 * u), (x + 15 * u, y - 45 * u)], fill=col)
    hx = x + sw * 7 * u; d.ellipse([hx - 10 * u, y - 100 * u, hx + 10 * u, y - 78 * u], fill=col)
    d.line([(x + sw * 4 * u - 12 * u, y - 76 * u), (x + 30 * u, y - 70 * u + sw * 4 * u)], fill=col, width=max(1, int(6 * u)))
    if h > 22:
        d.ellipse([hx - 6 * u, y - 92 * u, hx - 2 * u, y - 88 * u], fill=EYE); d.ellipse([hx + 2 * u, y - 92 * u, hx + 6 * u, y - 88 * u], fill=EYE)

# ================================================================ fondos
def skyline(sd, rng, base, n, hmin, hmax, col, win_col, lit=0.12, wmin=90, wmax=210):
    x = -60
    while x < BW + 60:
        w_ = rng.randint(wmin, wmax); h_ = rng.randint(hmin, hmax)
        sd.rect([x, base - h_, x + w_, base + 400], fill=col)
        if rng.random() < 0.3: sd.rect([x + w_ * 0.4, base - h_ - rng.randint(30, 90), x + w_ * 0.44, base - h_], fill=col)
        for wy in range(int(base - h_ + 20), int(base + 300), 36):
            for wx in range(int(x + 12), int(x + w_ - 20), 30):
                if rng.random() < lit: sd.rect([wx, wy, wx + 14, wy + 18], fill=win_col)
        x += w_ + rng.randint(4, 30)

def smoke_plume(img, x, y, h, col=(30, 22, 28), a=0.8):
    g = Image.new("RGBA", img.size); d = ImageDraw.Draw(g)
    for i in range(14):
        k = i / 14; r = 40 + k * 160
        d.ellipse([x + k * 120 - r + math.sin(i) * 30, y - k * h - r, x + k * 120 + r + math.sin(i) * 30, y - k * h + r], fill=col + (int(255 * a * (1 - k * 0.6)),))
    g = g.filter(ImageFilter.GaussianBlur(30)); img.paste(g, (0, 0), g); return img

BG = {}
def bg(kind):
    if kind in BG: return BG[kind]
    K = 2; r = random.Random(hash(kind) % 1000)
    if kind in ("city", "window", "signal", "heli", "city_day"):
        day = kind == "city_day"
        sky = [(0, (10, 8, 22)), (0.45, (60, 20, 40)), (0.7, (170, 60, 40)), (1, (60, 20, 24))] if not day else [(0, (60, 70, 90)), (0.5, (120, 110, 120)), (0.75, (190, 140, 110)), (1, (80, 70, 80))]
        img = gradient(sky, BW, BH); stars(img, 80 if not day else 0, 700)
        for fx in (0.2, 0.62, 0.85): img = add_light(img, int(BW * fx), 1350, 260, (255, 110, 30), 0.8 if not day else 0.3)
        for fx in (0.18, 0.6): img = smoke_plume(img, int(BW * fx), 1250, 900, (25, 18, 24) if not day else (70, 66, 72), 0.7)
        big = img.resize((BW * K, BH * K)); sd = SD(big, K)
        skyline(sd, r, 1350, 0, 250, 650, (34, 22, 40) if not day else (90, 86, 100), (120, 70, 60), 0.05)
        skyline(sd, r, 1520, 0, 200, 700, (16, 12, 22) if not day else (52, 50, 62), (255, 190, 100), 0.08, 140, 300)
        if kind == "signal":
            sd.rect([BW * 0.48, 1080, BW * 0.98, BH], fill=(12, 10, 18)); sd.rect([BW * 0.47, 1060, BW * 0.99, 1085], fill=(24, 20, 30))
            sd.rect([BW * 0.86, 960, BW * 0.92, 1062], fill=(24, 20, 30))
            person(sd, BW * 0.66, 1062, 120, (8, 6, 12), arm="forward")
        img = big.resize((BW, BH), Image.LANCZOS)
        if kind == "city": img = add_light(img, BW // 2, BH - 200, 700, (255, 90, 30), 0.85)
        if kind == "window": img = window_frame(img)
        BG[kind] = img; return img
    if kind == "street":
        img = gradient([(0, (20, 18, 26)), (1, (40, 34, 40))], BW, BH); big = img.resize((BW * K, BH * K)); sd = SD(big, K)
        # mirando hacia abajo desde el piso 33: dos fachadas que convergen, calle abajo
        sd.poly([(0, 0), (BW * 0.27, BH * 0.58), (BW * 0.27, BH), (0, BH)], fill=(28, 24, 34))
        sd.poly([(BW, 0), (BW * 0.73, BH * 0.58), (BW * 0.73, BH), (BW, BH)], fill=(24, 20, 30))
        for i in range(14):
            k = i / 14
            for side in (0, 1):
                xa = (k * BW * 0.27) if side == 0 else (BW - k * BW * 0.27); ya = k * BH * 0.58
                sd.rect([xa - 18 * (1 - k * 0.7) - (0 if side == 0 else 0), ya - 10, xa + 18 * (1 - k * 0.7), ya + 10 * (1 - k * 0.6)], fill=(255, 190, 110) if r.random() < 0.25 else (46, 40, 52))
        sd.rect([BW * 0.27, BH * 0.58, BW * 0.73, BH], fill=(52, 48, 54))
        for y in range(int(BH * 0.6), BH, 120): sd.rect([BW * 0.495, y, BW * 0.505, y + 60], fill=(200, 190, 120))
        for (cx, cy, c) in ((0.43, 0.7, (120, 30, 30)), (0.56, 0.82, (40, 60, 90)), (0.46, 0.9, (90, 90, 96))):
            sd.rect([BW * cx - 36, BH * cy - 70, BW * cx + 36, BH * cy + 70], 14, fill=c); sd.rect([BW * cx - 28, BH * cy - 40, BW * cx + 28, BH * cy + 10], 6, fill=(20, 24, 30))
        img = big.resize((BW, BH), Image.LANCZOS)
        img = add_light(img, int(BW * 0.43), int(BH * 0.7), 160, (255, 120, 40), 0.9)
        img = add_light(img, int(BW * 0.58), int(BH * 0.64), 120, (255, 200, 120), 0.35)
        BG[kind] = img; return img
    if kind == "tv":
        img = gradient([(0, (6, 8, 16)), (1, (14, 16, 30))], BW, BH); img = add_light(img, BW // 2, 900, 700, (120, 30, 40), 0.6)
        big = img.resize((BW * K, BH * K)); sd = SD(big, K)
        cx = BW / 2
        sd.rect([-100, 1520, BW + 100, BH], 80, fill=(14, 12, 20)); sd.rect([-60, 1460, BW * 0.42, 1640], 60, fill=(20, 18, 28)); sd.rect([BW * 0.58, 1460, BW + 60, 1640], 60, fill=(20, 18, 28))
        BG[kind] = big.resize((BW, BH), Image.LANCZOS); return BG[kind]
    if kind == "bath":
        img = gradient([(0, (30, 50, 70)), (1, (14, 24, 40))], BW, BH); big = img.resize((BW * K, BH * K)); sd = SD(big, K)
        for y in range(0, 1450, 120):
            for x in range((y // 120 % 2) * -60, BW, 120): sd.rect([x + 4, y + 4, x + 116, y + 116], 6, fill=(44, 70, 92))
        sd.rect([0, 1450, BW, BH], fill=(24, 30, 40))
        sd.rect([BW * 0.62, 820, BW * 0.66, 990], 8, fill=(190, 196, 210)); sd.rect([BW * 0.56, 800, BW * 0.68, 840], 18, fill=(210, 216, 230))
        img = big.resize((BW, BH), Image.LANCZOS); img = add_light(img, BW // 2, 300, 500, (140, 180, 220), 0.3)
        BG[kind] = img; return img
    if kind in ("dark", "lucia"):
        img = gradient([(0, (14, 18, 36)), (1, (24, 26, 44))], BW, BH); big = img.resize((BW * K, BH * K)); sd = SD(big, K)
        sd.rect([BW * 0.08, 300, BW * 0.5, 1150], fill=(40, 50, 90)); sd.rect([BW * 0.08, 300, BW * 0.5, 1150], outline=(20, 20, 30), width=26)
        sd.line([(BW * 0.29, 300), (BW * 0.29, 1150)], fill=(20, 20, 30), width=16); sd.line([(BW * 0.08, 720), (BW * 0.5, 720)], fill=(20, 20, 30), width=16)
        sd.ellipse([BW * 0.33, 400, BW * 0.43, 500], fill=(230, 235, 255))
        sd.poly([(BW * 0.08, 1150), (BW * 0.5, 1150), (BW * 0.75, 1700), (BW * 0.2, 1700)], fill=(30, 36, 66))
        if kind == "lucia":
            sd.rect([BW * 0.45, 1250, BW * 1.05, 1560], 50, fill=(26, 22, 34)); sd.rect([BW * 0.42, 1180, BW * 0.55, 1560], 40, fill=(30, 26, 40))
            neighbor(sd, BW * 0.66, 1900)
            sd.line([(BW * 0.66 - 200, 1640), (BW * 0.66 + 40, 1560)], fill=(236, 232, 222), width=50)
            sd.rect([BW * 0.25, 1470, BW * 0.27, 1520], fill=(240, 230, 210))
        else:
            person(sd, BW * 0.27, 1560, 420, (6, 6, 12), arm="down")
        img = big.resize((BW, BH), Image.LANCZOS)
        img = add_light(img, int(BW * 0.29), 720, 520, (90, 120, 200), 0.6)
        if kind == "lucia": img = add_light(img, int(BW * 0.26), 1450, 300, (255, 150, 60), 0.75); img = add_light(img, int(BW * 0.5), 1300, 500, (255, 140, 60), 0.35)
        BG[kind] = img; return img
    if kind == "kitchen":
        img = gradient([(0, (30, 26, 30)), (1, (44, 38, 40))], BW, BH); big = img.resize((BW * K, BH * K)); sd = SD(big, K)
        sd.rect([BW * 0.12, 420, BW * 0.88, 1300], 10, fill=(40, 32, 30)); sd.rect([BW * 0.15, 450, BW * 0.85, 1270], 6, fill=(22, 18, 18))
        for sy in (720, 1000, 1270): sd.rect([BW * 0.15, sy - 14, BW * 0.85, sy], fill=(60, 48, 44))
        cans = [(0.25, 706), (0.33, 706), (0.62, 706), (0.3, 986), (0.7, 986), (0.78, 986)]
        for cx, cy in cans:
            x = BW * cx; sd.rect([x - 40, cy - 130, x + 40, cy], 10, fill=(170, 40, 40)); sd.rect([x - 40, cy - 95, x + 40, cy - 40], fill=(230, 220, 200)); sd.ellipse([x - 40, cy - 142, x + 40, cy - 118], fill=(190, 190, 200))
        sd.rect([BW * 0.5, 1150, BW * 0.6, 1256], 8, fill=(40, 90, 160))
        img = big.resize((BW, BH), Image.LANCZOS); img = add_light(img, BW // 2, 900, 520, (255, 230, 170), 0.45)
        BG[kind] = img; return img
    if kind in ("door", "door_bang"):
        img = gradient([(0, (16, 14, 20)), (1, (30, 26, 32))], BW, BH); big = img.resize((BW * K, BH * K)); sd = SD(big, K)
        cx = BW / 2
        sd.rect([cx - 330, 280, cx + 330, 1720], fill=(36, 30, 34)); sd.rect([cx - 290, 320, cx + 290, 1700], 6, fill=(96, 62, 44))
        for (a, b_) in ((380, 900), (960, 1640)): sd.rect([cx - 230, a, cx + 230, b_], 6, outline=(70, 44, 30), width=10)
        sd.ellipse([cx - 22, 640, cx + 22, 684], fill=(200, 190, 150)); sd.ellipse([cx - 12, 650, cx + 12, 674], fill=(20, 20, 20))
        sd.ellipse([cx + 190, 1010, cx + 240, 1060], fill=(200, 180, 120)); sd.rect([cx + 150, 1020, cx + 250, 1050], 10, fill=(200, 180, 120))
        sd.line([(cx + 200, 820), (cx + 160, 900), (cx + 200, 960)], fill=(170, 170, 180), width=8)
        sd.rect([cx - 290, 1700, cx + 290, 1716], fill=(255, 220, 140))
        sd.rect([-50, 1716, BW + 50, BH], fill=(22, 18, 22))
        img = big.resize((BW, BH), Image.LANCZOS); img = add_light(img, int(cx), 1740, 260, (255, 200, 120), 0.5)
        BG[kind] = img; return img
    if kind in ("peephole", "peephole_far"):
        img = gradient([(0, (20, 30, 24)), (1, (40, 50, 40))], BW, BH); big = img.resize((BW * K, BH * K)); sd = SD(big, K)
        vx, vy = BW / 2, BH * 0.46
        sd.poly([(0, 0), (vx - 90, vy - 120), (vx - 90, vy + 130), (0, BH)], fill=(52, 60, 50)); sd.poly([(BW, 0), (vx + 90, vy - 120), (vx + 90, vy + 130), (BW, BH)], fill=(46, 54, 44))
        sd.poly([(0, BH), (vx - 90, vy + 130), (vx + 90, vy + 130), (BW, BH)], fill=(34, 32, 30)); sd.poly([(0, 0), (vx - 90, vy - 120), (vx + 90, vy - 120), (BW, 0)], fill=(60, 66, 58))
        sd.rect([vx - 90, vy - 120, vx + 90, vy + 130], fill=(14, 18, 14))
        for k in (0.25, 0.55, 0.8):
            for side in (-1, 1):
                x0 = vx + side * (90 + (1 - k) * (BW / 2 - 90)); ytop = vy - 120 - (1 - k) * (vy - 120); ybot = vy + 130 + (1 - k) * (BH - vy - 130)
                sd.poly([(x0, ytop + (ybot - ytop) * 0.2), (x0 + side * 60 * (1 - k), ytop + (ybot - ytop) * 0.18), (x0 + side * 60 * (1 - k), ytop + (ybot - ytop) * 0.9), (x0, ytop + (ybot - ytop) * 0.88)], fill=(70, 50, 36))
        sd.rect([vx - 40, vy - 118, vx + 40, vy - 104], fill=(120, 255, 160))
        if kind == "peephole":
            neighbor(sd, vx, BH * 0.98)
        img = big.resize((BW, BH), Image.LANCZOS); img = add_light(img, int(vx), int(vy - 110), 220, (80, 255, 140), 0.4)
        BG[kind] = img; return img
    if kind in ("arm", "arm_bite"):
        img = gradient([(0, (18, 14, 20)), (1, (30, 22, 26))], BW, BH); img = add_light(img, BW // 2, 960, 600, (255, 150, 70), 0.45)
        big = img.resize((BW * K, BH * K)); sd = SD(big, K)
        sd.poly([(-50, 820), (BW + 50, 760), (BW + 50, 1140), (-50, 1180)], fill=(214, 160, 128))
        sd.poly([(-50, 1180), (BW + 50, 1140), (BW + 50, 1180), (-50, 1220)], fill=(170, 120, 96))
        if kind == "arm":
            for i in range(8):
                x = 240 + i * 70; sd.poly([(x, 790), (x + 90, 785), (x + 80, 1170), (x - 10, 1175)], fill=(236, 232, 222) if i % 2 else (222, 218, 206))
            sd.ellipse([470, 930, 610, 1030], fill=(150, 30, 34, 170))
        else:
            for i, (ax, ay) in enumerate([(430, 920), (470, 905), (510, 900), (550, 905), (590, 920), (440, 1050), (480, 1062), (520, 1066), (560, 1062), (600, 1050)]):
                sd.ellipse([ax - 13, ay - 16, ax + 13, ay + 16], fill=(90, 30, 40))
            sd.ellipse([400, 880, 640, 1090], outline=(150, 70, 80, 120), width=14)
        img = big.resize((BW, BH), Image.LANCZOS); BG[kind] = img; return img
    if kind == "radio":
        img = gradient([(0, (10, 10, 14)), (1, (24, 20, 22))], BW, BH); img = add_light(img, BW // 2, 1100, 400, (255, 140, 50), 0.4)
        big = img.resize((BW * K, BH * K)); sd = SD(big, K)
        sd.rect([-50, 1350, BW + 50, BH], fill=(46, 32, 26))
        cx = BW / 2; sd.rect([cx - 380, 900, cx + 380, 1360], 50, fill=(60, 54, 50), outline=(20, 20, 20), width=6)
        for i in range(9): sd.ellipse([cx - 340 + (i % 3) * 70, 1000 + (i // 3) * 90, cx - 300 + (i % 3) * 70, 1040 + (i // 3) * 90], fill=(28, 26, 26))
        sd.rect([cx - 50, 990, cx + 340, 1130], 16, fill=(30, 50, 30)); sd.ellipse([cx + 150, 1180, cx + 260, 1290], fill=(30, 28, 28))
        sd.line([(cx + 300, 900), (cx + 420, 520)], fill=(150, 150, 160), width=8)
        img = big.resize((BW, BH), Image.LANCZOS); img = add_light(img, int(cx + 145), 1060, 220, (120, 255, 120), 0.6)
        BG[kind] = img; return img
    if kind == "map":
        img = gradient([(0, (220, 210, 186)), (1, (196, 182, 156))], BW, BH); big = img.resize((BW * K, BH * K)); sd = SD(big, K)
        for x in range(0, BW, 150): sd.rect([x, 0, x + 26, BH], fill=(168, 156, 132))
        for y in range(0, BH, 150): sd.rect([0, y, BW, y + 26], fill=(168, 156, 132))
        sd.rect([BW * 0.15, BH * 0.72, BW * 0.27, BH * 0.8], 10, fill=(40, 40, 60)); sd.rect([BW * 0.68, BH * 0.22, BW * 0.86, BH * 0.32], 10, fill=(240, 240, 240), outline=(200, 40, 40), width=10)
        f = S.font(FONT_D, 110 * K); sd.d.text(((BW * 0.77 - 34) * K, (BH * 0.27 - 70) * K), "H", font=f, fill=(200, 30, 30))
        img = big.resize((BW, BH), Image.LANCZOS); BG[kind] = img; return img
    raise ValueError(kind)

def neighbor(sd, cx, by):
    sd.poly([(cx - 420, by), (cx - 300, by - 520), (cx + 300, by - 520), (cx + 420, by)], fill=(110, 40, 50))
    sd.poly([(cx - 300, by - 520), (cx - 200, by - 600), (cx + 200, by - 600), (cx + 300, by - 520)], fill=(110, 40, 50))
    sd.rect([cx - 70, by - 700, cx + 70, by - 560], fill=(200, 150, 120))
    sd.ellipse([cx - 250, by - 1180, cx + 250, by - 560], fill=(46, 28, 22))
    sd.poly([(cx - 250, by - 860), (cx - 290, by - 480), (cx - 150, by - 600)], fill=(46, 28, 22)); sd.poly([(cx + 250, by - 860), (cx + 290, by - 480), (cx + 150, by - 600)], fill=(46, 28, 22))
    sd.ellipse([cx - 175, by - 1080, cx + 175, by - 640], fill=(214, 164, 132))
    sd.chord([cx - 210, by - 1150, cx + 210, by - 820], 180, 360, fill=(46, 28, 22))
    for s_ in (-1, 1):
        ex = cx + s_ * 70; sd.ellipse([ex - 34, by - 900, ex + 34, by - 852], fill=(250, 250, 250)); sd.ellipse([ex - 16, by - 894, ex + 16, by - 860], fill=(30, 20, 20))
        sd.line([(ex - s_ * 40, by - 962), (ex + s_ * 34, by - 938)], fill=(46, 28, 22), width=12)
    sd.ellipse([cx - 40, by - 760, cx + 40, by - 720], fill=(120, 40, 40))
    sd.line([(cx + 120, by - 800), (cx + 140, by - 760)], fill=(150, 60, 50), width=8)

def window_frame(img):
    fr = Image.new("RGBA", img.size); sd = SD(fr, 1); x0, y0, x1, y1 = 60, 260, BW - 60, 1720
    sd.rect([0, 0, BW, y0], fill=(10, 10, 14)); sd.rect([0, y1, BW, BH], fill=(10, 10, 14)); sd.rect([0, 0, x0, BH], fill=(10, 10, 14)); sd.rect([x1, 0, BW, BH], fill=(10, 10, 14))
    sd.rect([x0, y0, x1, y1], outline=(30, 28, 34), width=30); sd.line([((x0 + x1) / 2, y0), ((x0 + x1) / 2, y1)], fill=(30, 28, 34), width=24)
    sd.rect([x0 - 30, y1 - 10, x1 + 30, y1 + 50], fill=(40, 36, 42))
    img = img.copy(); img.paste(fr, (0, 0), fr); return img

# ================================================================ HUD
_hud = {}
def hud_img(ep, h):
    key = json.dumps(h, sort_keys=True)
    if key in _hud: return _hud[key]
    K = 2; im = Image.new("RGBA", (W * K, 170 * K)); sd = SD(im, K)
    _, x = pill(sd, 44, 10, f"DÍA {h.get('dia', 1)}", (220, 30, 40, 245), size=40)
    pill(sd, x + 12, 10, f"PISO 33 · PARTE {ep['parte']}", (255, 255, 255, 235), (10, 10, 20), size=30)
    x = W - 44
    if "comida" in h:
        c = h["comida"]; x0, _ = pill(sd, x, 92, f"COMIDA {c} DÍA{'S' if c != 1 else ''}", ((200, 40, 40, 240) if c <= 2 else (230, 120, 20, 240)), size=30, anchor="r"); x = x0 - 10
    if "agua" in h:
        x0, _ = pill(sd, x, 92, f"AGUA {h['agua']} L", (30, 110, 220, 240), size=30, anchor="r")
    im = im.resize((W, 170), Image.LANCZOS); _hud[key] = im; return im

def hud_with_icons(ep, h):
    """pill sin iconos en texto: añadimos gotita/lata como prefijo visual."""
    return hud_img(ep, h)

# ================================================================ partículas
PART = [(random.random() * W, random.random() * H, random.uniform(1.5, 5), random.uniform(0.4, 1.4)) for _ in range(260)]
def ash(d, t, n=120, ember=True, speed=1.0):
    for i, (x0, y0, r, v) in enumerate(PART[:n]):
        y = (y0 + t * 70 * v * speed) % (H + 40) - 20; x = (x0 + t * 25 * v + math.sin(t * 0.9 + i) * 25) % (W + 40) - 20
        if ember and i % 7 == 0: d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 150, 60, 220))
        else: d.ellipse([x - r * 0.8, y - r * 0.8, x + r * 0.8, y + r * 0.8], fill=(180, 170, 170, 120))
def dust(d, t, n=35):
    for i, (x0, y0, r, v) in enumerate(PART[:n]):
        y = (y0 + math.sin(t * 0.3 + i) * 40) % H; x = (x0 + t * 8 * v) % W
        d.ellipse([x - 1.2, y - 1.2, x + 1.2, y + 1.2], fill=(255, 240, 220, 28))

# ================================================================ escena por cuadro
VIG = None
def make_beat(ep, b, T0):
    global VIG
    if VIG is None: VIG = make_vig()
    kind = b["scene"]; dur = b["dur"]
    kar = Karaoke(b["_words"], b["_times"], y=b.get("y", 1180), size=b.get("size", 118)) if b.get("_words") and not b.get("no_caps") else None
    env = b.get("_env"); panels = {}
    if kind in ("choice", "results"):
        for L, col in (("A", BLUE), ("B", ORA)):
            v = b[L + "_view"]; panels[L] = (bg(v[0]), v, panel_overlay(L, b[L] if kind == "choice" else b[L][0], col))
    else: base = bg(kind)
    zr = random.Random(5); crowd = [(zr.uniform(0.29, 0.71), zr.uniform(0.58, 1.02), zr.uniform(0.7, 1.25)) for _ in range(b.get("crowd", 70))]
    knocks = b.get("knocks", [])
    def frame_at(t):
        f = int(round((T0 + t) * FPS)); rng = random.Random(f); T = T0 + t
        shake = b.get("shake", 0) * max(0, 1 - t / 0.8)
        for kt in knocks:
            if 0 <= t - kt < 0.25: shake = max(shake, 22 * (1 - (t - kt) / 0.25))
        punch = 1 + 0.07 * (1 - ease(t / 0.3))
        if kind in ("choice", "results"):
            frame = Image.new("RGB", (W, H))
            for i, L in enumerate("AB"):
                pbg, v, ov = panels[L]
                half = cam(pbg, t, dur, (v[3] * punch, v[3] * 1.1), 0, (0, 0), (W, 960), (v[1], v[2]))
                if kind == "results":
                    win = (b["A"][1] > b["B"][1]) == (L == "A")
                    if not win and t > 1.6:
                        k = ease((t - 1.6) / 0.4); g = half.convert("L").convert("RGB"); half = Image.blend(half, Image.blend(g, Image.new("RGB", g.size), 0.45), k)
                hd = ImageDraw.Draw(half, "RGBA"); ash(hd, T + i * 3, 50)
                slide = int((1 - ease((t - i * 0.12) / 0.35)) * W) * (-1 if L == "A" else 1); half.paste(ov, (slide, 0), ov)
                if kind == "results":
                    pct = b[L][1]; prog = ease((t - 0.3) / 1.2); s = f"{round(pct * prog)}%"; win = (b["A"][1] > b["B"][1]) == (L == "A")
                    sz = 260 if not (win and t > 1.6) else int(260 * (1 + 0.25 * back((t - 1.6) / 0.3)))
                    ti = text_img(s, sz, YEL if (win and t > 1.6) else (255, 255, 255), 12); half.paste(ti, ((W - ti.width) // 2, 400 - ti.height // 2 + (60 if L == "A" else -60)), ti)
                frame.paste(half, (0, i * 960))
            d = ImageDraw.Draw(frame, "RGBA"); d.rectangle([0, 952, W, 968], fill=(10, 10, 16))
            if kind == "choice":
                cd0 = b.get("_cd0", dur - 3); prog = min(1, max(0, (t - cd0) / (dur - cd0 - 0.1)))
                if t > 0.5: d.rectangle([0, 953, int(W * (1 - prog)), 967], fill=YEL if prog < 0.7 else RED)
            else:
                ti = S.hud_title(f"RESULTADO PARTE {ep['parte'] - 1}"); frame.paste(ti, ((W - ti.width) // 2, 175), ti)
            frame = frame.convert("RGBA")
        else:
            z = b.get("zoom", (1.0, 1.08))
            frame = cam(base, t, dur, (z[0] * punch, z[1]), shake, tuple(b.get("pan", (0, 0))), center=tuple(b.get("center", (0.5, 0.5))), rng=rng).convert("RGBA")
            d = ImageDraw.Draw(frame, "RGBA")
            zf = lerp(z[0], z[1], t / dur)
            if kind == "street":
                for i, (zx, zy, zs) in enumerate(crowd):
                    yy = zy * H + math.sin(T * 0.4 + i) * 6; xx = zx * W + (W * 0.5 - zx * W) * 0.0 + math.sin(T * 0.3 + i * 2) * 10
                    xx = W / 2 + (xx - W / 2) * zf; yy = H / 2 + (yy - H / 2) * zf
                    zombie_small(d, xx, yy, 52 * zs * (0.5 + 0.6 * (yy / H)) * zf, T, i, (34, 44, 34))
            if kind == "city" and b.get("horde", True):
                hr = random.Random(4)
                for i in range(16):
                    x = hr.uniform(-60, W + 60); y = H - hr.uniform(0, 260); hh = hr.uniform(330, 560)
                    zombie_small(d, x + math.sin(T * 0.8 + i) * 12, y + 20, hh, T, i, (20, 12, 18))
            if kind == "tv":
                cx = W / 2; zz = lerp(1.0, 1.08, t / dur); sy0 = 470
                def Z(x, y): return (W / 2 + (x - W / 2) * zz, H / 2 + (y - H / 2) * zz)
                (a0, b0), (a1, b1) = Z(30, sy0 - 30), Z(W - 30, sy0 + 690); d.rounded_rectangle([a0, b0, a1, b1], 26, fill=(8, 8, 10))
                (a0, b0), (a1, b1) = Z(60, sy0), Z(W - 60, sy0 + 630); d.rectangle([a0, b0, a1, b1], fill=(40, 6, 12))
                (a0, b0), (a1, b1) = Z(60, sy0 + 70), Z(W - 60, sy0 + 190); d.rectangle([a0, b0, a1, b1], fill=(225, 20, 30, 255 if int(t * 3) % 2 == 0 else 190))
                fA = font(FONT_D, int(86 * zz)); d.text(Z(100, sy0 + 82), "ALERTA DE EMERGENCIA", font=fA, fill=(255, 255, 255))
                f2 = font(FONT_D, int(78 * zz)); d.text(Z(100, sy0 + 250), "NO SALGA DE SU CASA", font=f2, fill=(255, 255, 255)); d.text(Z(100, sy0 + 350), "NO ABRA LA PUERTA", font=f2, fill=(255, 230, 120))
                f3 = font(FONT_B, int(34 * zz)); off = (t * 260) % 1700
                (a0, b0), (a1, b1) = Z(60, sy0 + 540), Z(W - 60, sy0 + 610); d.rectangle([a0, b0, a1, b1], fill=(0, 0, 0, 200))
                d.text(Z(W - 60 - off, sy0 + 552), "BROTE CONFIRMADO EN TODA LA CIUDAD · EVITE EL CONTACTO", font=f3, fill=(255, 220, 120))
                (a0, b0), (a1, b1) = Z(0, sy0 + 540), Z(60, sy0 + 610); d.rectangle([a0, b0, a1, b1], fill=(8, 8, 10))
                for yy in range(int(Z(0, sy0)[1]), int(Z(0, sy0 + 630)[1]), 6): d.line([(Z(60, 0)[0], yy), (Z(W - 60, 0)[0], yy)], fill=(0, 0, 0, 45))
            if kind == "bath":
                lvl = ease(t / dur); top = 1300 - 260 * lvl
                d.rectangle([W * 0.6, 990, W * 0.62, top], fill=(150, 200, 255, 200))
                d.rounded_rectangle([110, 1150, W - 110, 1460], 80, fill=(232, 236, 244)); d.rectangle([150, top, W - 150, 1300], fill=(70, 140, 220, 230))
                for i in range(6): xx = 180 + ((T * 140 + i * 130) % (W - 360)); d.ellipse([xx - 30, top - 4, xx + 30, top + 6], fill=(170, 210, 255, 160))
                d.rounded_rectangle([110, 1300, W - 110, 1460], 60, fill=(232, 236, 244)); d.rounded_rectangle([110, 1150, W - 110, 1190], 20, fill=(246, 248, 252))
            if kind == "signal":
                on = (int(t * 4) % 3) != 2
                if on:
                    lx, ly = (W * 0.62, 1030)
                    frame = Image.fromarray(np.asarray(add_light(frame.convert("RGB"), int(W * 0.62), 1000, 160, (255, 250, 200), 1.0))).convert("RGBA"); d = ImageDraw.Draw(frame, "RGBA")
            if kind == "heli":
                hx = W * (1.2 - t / dur * 1.6); hy = 520 + math.sin(t) * 20
                d.polygon([(hx, hy), (hx - 340, 1700), (hx + 120, 1700)], fill=(255, 255, 220, 40))
                d.ellipse([hx - 70, hy - 30, hx + 70, hy + 30], fill=(8, 8, 12)); d.rectangle([hx + 50, hy - 8, hx + 210, hy + 6], fill=(8, 8, 12))
                bl = 160 * abs(math.sin(T * 40)); d.line([(hx - bl, hy - 42), (hx + bl, hy - 42)], fill=(8, 8, 12), width=6)
                if int(t * 6) % 2 == 0: d.ellipse([hx - 8, hy + 22, hx + 8, hy + 38], fill=(255, 40, 40))
            if kind == "radio":
                for k in range(4):
                    ph = (t * 0.8 + k / 4) % 1; rr = 80 + ph * 520
                    d.ellipse([W / 2 + 360 - rr, 520 - rr, W / 2 + 360 + rr, 520 + rr], outline=(120, 255, 120, int(160 * (1 - ph))), width=6)
            if kind == "map":
                p0 = (W * 0.21, H * 0.74); p1 = (W * 0.77, H * 0.29); pts = [p0, (W * 0.21, H * 0.52), (W * 0.5, H * 0.52), (W * 0.5, H * 0.29), p1]
                prog = ease(t / (dur * 0.8)); segs = []
                L = sum(math.dist(pts[i], pts[i + 1]) for i in range(4)); acc = 0; target = L * prog
                for i in range(4):
                    sl = math.dist(pts[i], pts[i + 1])
                    if acc + sl <= target: segs.append((pts[i], pts[i + 1]))
                    else:
                        k = (target - acc) / sl; segs.append((pts[i], (lerp(pts[i][0], pts[i + 1][0], k), lerp(pts[i][1], pts[i + 1][1], k)))); break
                    acc += sl
                for a, c in segs:
                    n = int(math.dist(a, c) / 40)
                    for j in range(n): x = lerp(a[0], c[0], j / max(1, n)); y = lerp(a[1], c[1], j / max(1, n)); d.ellipse([x - 9, y - 9, x + 9, y + 9], fill=(40, 40, 60))
                zr2 = random.Random(9)
                for i in range(70):
                    x = zr2.uniform(80, W - 80); y = zr2.uniform(H * 0.3, H * 0.75); x += math.sin(T + i) * 8
                    a = int(255 * ease((t - 0.4 - i * 0.02) / 0.3)); d.ellipse([x - 11, y - 11, x + 11, y + 11], fill=(210, 30, 30, a))
                fA = font(FONT_D, 64); d.text((W * 0.13, H * 0.65), "TÚ", font=fA, fill=(40, 40, 60)); d.text((W * 0.66, H * 0.33), "HOSPITAL", font=fA, fill=(200, 30, 30))
            if kind == "door_bang":
                for i in range(2):
                    xx = W / 2 - 120 + i * 200 + math.sin(T * 3 + i) * 30; d.rectangle([xx - 50, 1700, xx + 50, 1716], fill=(10, 8, 10))
            if kind in ("peephole", "peephole_far"):
                show = b.get("zombie_far", kind == "peephole_far")
                if show:
                    zx = W / 2 + math.sin(T * 0.7) * 30; zy = H * 0.46 + 125; zh = 150 + t * 12
                    zombie_small(d, zx, zy, zh, T, 1, (20, 26, 20))
            if b.get("people"):
                pass
            if kind in ("city", "window", "city_day", "heli", "signal", "street"): ash(d, T, b.get("ash", 120), kind != "city_day")
            else: dust(d, T)
            if kind in ("peephole", "peephole_far"):
                m = Image.new("L", (W, H), 255); ImageDraw.Draw(m).ellipse([W / 2 - 470, H * 0.45 - 470, W / 2 + 470, H * 0.45 + 470], fill=0)
                m = m.filter(ImageFilter.GaussianBlur(40)); frame.paste((0, 0, 0), (0, 0), m)
            if b.get("flicker"):
                if (t < 1.2 and rng.random() < 0.35) or t >= 1.2: frame = Image.blend(frame, Image.new("RGBA", (W, H), (0, 0, 0, 255)), 0.75 if t >= 1.2 else 0.5)
            frame.paste(VIG, (0, 0), VIG)
            if b.get("hud"):
                hi = hud_img(ep, b["hud"]); frame.paste(hi, (0, 170), hi)
        if kar: kar.draw(frame, t)
        fl = b.get("flash", 0) * max(0, 1 - t / 0.35)
        if fl > 0: frame = Image.blend(frame, Image.new("RGBA", (W, H), (255, 255, 255, 255)), fl)
        if b.get("red"):
            a = 0.18 + 0.12 * math.sin(t * 5); frame = Image.blend(frame, Image.new("RGBA", (W, H), (180, 0, 0, 255)), a)
        return Image.fromarray(finish(frame.convert("RGB"), f))
    return frame_at

# ================================================================ audio
def build_audio(ep, total, tracks):
    n = int(total * SR) + SR; tt = np.arange(n) / SR; rng = np.random.default_rng(2); out = np.zeros(n)
    def add(t0, sig, g=1.0):
        i = int(t0 * SR); j = min(n, i + len(sig))
        if 0 <= i < n: out[i:j] += sig[: j - i] * g
    # música: drone + pulso grave + campana menor
    mus = 0.07 * (np.sin(2 * np.pi * 55 * tt) + 0.6 * np.sin(2 * np.pi * 82.4 * tt) + 0.4 * np.sin(2 * np.pi * 65.4 * tt * (1 + 0.002 * np.sin(tt))))
    bpm = 92; beat = 60 / bpm
    for k in range(int(total / beat) + 1):
        i = int(k * beat * SR); L = int(0.22 * SR); x = np.arange(L) / SR
        s = 0.55 * np.sin(2 * np.pi * 50 * x * (1 - x * 1.5)) * np.exp(-x * 16)
        if k % 2 == 1: s *= 0.55
        j = min(n, i + L); mus[i:j] += s[: j - i]
        if k % 8 == 0:
            L2 = int(2.5 * SR); x2 = np.arange(L2) / SR; nt = [220, 207.65, 196, 174.6][(k // 8) % 4]
            s2 = 0.06 * (np.sin(2 * np.pi * nt * x2) + 0.4 * np.sin(2 * np.pi * nt * 2.01 * x2)) * np.exp(-x2 * 1.4); j = min(n, i + L2); mus[i:j] += s2[: j - i]
    wind = np.convolve(rng.standard_normal(n), np.ones(500) / 500, "same") * 1.0
    vo = np.zeros(n)
    for t0, a in tracks:
        i = int(t0 * SR); j = min(n, i + len(a)); vo[i:j] += a[: j - i]
    e = np.convolve(np.abs(vo), np.ones(2400) / 2400, "same"); duck = 1 - 0.5 * np.clip(e * 12, 0, 1)
    out += (mus + wind) * duck
    def boom(L=1.3, f=44):
        x = np.arange(int(L * SR)) / SR; return 0.9 * np.sin(2 * np.pi * f * x * (1 - x * 0.3)) * np.exp(-x * 3) + 0.25 * rng.standard_normal(len(x)) * np.exp(-x * 14)
    def whoosh(L=0.45):
        x = np.arange(int(L * SR)) / SR; s = np.convolve(rng.standard_normal(len(x)), np.ones(30) / 30, "same"); return 1.3 * s * np.sin(np.pi * x / L) ** 2
    def knock():
        x = np.arange(int(0.18 * SR)) / SR; return 0.9 * (np.sin(2 * np.pi * 95 * x) + 0.5 * np.sin(2 * np.pi * 180 * x)) * np.exp(-x * 30) + 0.3 * rng.standard_normal(len(x)) * np.exp(-x * 80)
    def bang():
        x = np.arange(int(0.5 * SR)) / SR; return 1.0 * np.sin(2 * np.pi * 60 * x) * np.exp(-x * 12) + 0.5 * rng.standard_normal(len(x)) * np.exp(-x * 30)
    def groan(L=1.6):
        x = np.arange(int(L * SR)) / SR; f0 = 85 + 15 * np.sin(2 * np.pi * 3 * x); ph = np.cumsum(2 * np.pi * f0 / SR)
        s = (np.sign(np.sin(ph)) * 0.3 + np.sin(ph)) * np.sin(np.pi * x / L) ** 2; s = np.convolve(s, np.ones(18) / 18, "same"); return 0.35 * s
    def siren(L):
        x = np.arange(int(L * SR)) / SR; f0 = 700 + 200 * np.sin(2 * np.pi * 0.4 * x); return 0.05 * np.sin(np.cumsum(2 * np.pi * f0 / SR))
    def rotor(L):
        x = np.arange(int(L * SR)) / SR; return 0.45 * np.sin(2 * np.pi * 55 * x) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 14 * x))) * np.sin(np.pi * x / L)
    def static(L):
        return 0.12 * rng.standard_normal(int(L * SR)) * (0.6 + 0.4 * np.sin(np.arange(int(L * SR)) / SR * 30))
    def tick():
        x = np.arange(int(0.05 * SR)) / SR; return 0.35 * np.sin(2 * np.pi * 1600 * x) * np.exp(-x * 90)
    def hb():
        x = np.arange(int(0.22 * SR)) / SR; return 0.9 * np.sin(2 * np.pi * 55 * x) * np.exp(-x * 20)
    def riser(L):
        x = np.arange(int(L * SR)) / SR; return 0.15 * np.sin(2 * np.pi * (180 + 700 * (x / L) ** 2) * x) * (x / L)
    def ding():
        x = np.arange(int(0.9 * SR)) / SR; return 0.26 * (np.sin(2 * np.pi * 660 * x) + 0.5 * np.sin(2 * np.pi * 990 * x)) * np.exp(-x * 5)
    def water(L):
        s = np.convolve(rng.standard_normal(int(L * SR)), np.ones(6) / 6, "same"); return 0.12 * s
    t0 = 0
    for b in ep["beats"]:
        dd = b["dur"]
        if t0 > 0: add(t0 - 0.18, whoosh())
        for s in b.get("sfx", "").split(","):
            if s == "boom": add(t0, boom())
            if s == "hit": add(t0, boom(0.7, 70), 0.7)
            if s == "groan": add(t0 + 0.6, groan(), 0.9)
            if s == "siren": add(t0, siren(dd))
            if s == "rotor": add(t0, rotor(dd))
            if s == "static": add(t0, static(dd), 0.6)
            if s == "water": add(t0, water(dd))
            if s == "heart":
                for k in range(int(dd / 0.75)): add(t0 + k * 0.75, hb()); add(t0 + k * 0.75 + 0.22, hb() * 0.6)
            if s == "power": add(t0 + 1.2, boom(0.9, 38))
        for kt in b.get("knocks", []): add(t0 + kt, bang() if b["scene"] == "door_bang" else knock())
        if b["scene"] == "results": add(t0 + 0.3, riser(1.3)); add(t0 + 1.6, boom(0.6, 90), 0.7); add(t0 + 1.6, ding())
        if b["scene"] == "choice":
            for k in range(int((dd - b["_cd0"]) * 2)): add(t0 + b["_cd0"] + k * 0.5, tick()); add(t0 + b["_cd0"] + k * 0.5, hb() * 0.7)
        t0 += dd
    out += vo
    out = np.tanh(out * 1.1) * 0.92; out = out[: int(total * SR)]; fd = int(0.35 * SR); out[-fd:] *= np.linspace(1, 0, fd)
    return (out * 32767).astype(np.int16)

# ================================================================ main
def prepare(ep):
    voice = ep.get("voz", "em_alex"); speed = ep.get("velocidad", 1.1); T = 0; tracks = []
    for b in ep["beats"]:
        a = tts(b["say"], b.get("voz", voice), b.get("velocidad", speed)); vd = len(a) / SR; lead = 0.12
        words = b.get("cap", b["say"]).split(); b["_words"] = words; b["_times"] = word_times(words, vd, lead)
        env = np.array([np.sqrt(np.mean(a[int(i / FPS * SR): int((i + 1) / FPS * SR)] ** 2) + 1e-9) if int(i / FPS * SR) < len(a) else 0 for i in range(int(vd * FPS) + 2)])
        b["_env"] = env
        extra = 3.4 if b["scene"] == "choice" else b.get("pausa", 0.3)
        b["dur"] = max(b.get("min", 0), round(lead + vd + extra, 2))
        if b["scene"] == "choice": b["_cd0"] = lead + vd + 0.1
        tracks.append((T + lead, a)); T += b["dur"]
    return T, tracks

def main(cfg, out):
    ep = json.load(open(cfg)); total, tracks = prepare(ep); print("duración", round(total, 1), flush=True)
    tmp = out + "_parts"; os.makedirs(tmp, exist_ok=True); parts = []; T0 = 0
    for i, b in enumerate(ep["beats"]):
        pth = os.path.join(tmp, f"b{i:02d}.mp4"); parts.append(pth)
        fa = make_beat(ep, b, T0); n = int(round(b["dur"] * FPS))
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                              "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", pth + ".tmp.mp4"], stdin=subprocess.PIPE)
        for k in range(n): p.stdin.write(fa(k / FPS).tobytes())
        p.stdin.close(); assert p.wait() == 0; os.replace(pth + ".tmp.mp4", pth); T0 += b["dur"]
    with open(os.path.join(tmp, "list.txt"), "w") as f:
        for p in parts: f.write(f"file '{os.path.abspath(p)}'\n")
    real = sum(int(round(b["dur"] * FPS)) for b in ep["beats"]) / FPS; wav = os.path.join(tmp, "audio.wav")
    with wave.open(wav, "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(build_audio(ep, real, tracks).tobytes())
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", os.path.join(tmp, "list.txt"), "-i", wav, "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest", "-movflags", "+faststart", out + ".tmp.mp4"], check=True)
    os.replace(out + ".tmp.mp4", out); print("listo", out, round(real, 1), "s")

if __name__ == "__main__":
    if sys.argv[1] == "preview":
        ep = json.load(open(sys.argv[2])); prepare(ep); bi = int(sys.argv[3]); T0 = sum(x["dur"] for x in ep["beats"][:bi])
        make_beat(ep, ep["beats"][bi], T0)(float(sys.argv[4])).save(sys.argv[5])
    elif sys.argv[1] == "dur":
        ep = json.load(open(sys.argv[2])); print(round(prepare(ep)[0], 1))
    else: main(sys.argv[1], sys.argv[2])

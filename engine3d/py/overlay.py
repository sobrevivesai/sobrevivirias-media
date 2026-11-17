# Overlays a 1080x1920: portada, resultado de la votación, subtítulos abajo (palabra activa en amarillo), opciones A/B, flash.
import sys, os, glob, json
from PIL import Image, ImageDraw, ImageFont
F = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "web") + "/"; W, H = 1080, 1920; FPS = 30
A = lambda s: ImageFont.truetype(F + "Anton.ttf", s); B = lambda s: ImageFont.truetype(F + "ArchivoBlack.ttf", s)
INK = (36, 23, 38); YEL = (255, 214, 64)
EP = json.load(open(os.environ.get("EP", "episode.json")))     # parte, titulo, votos, opciones
PH = json.load(open("work/phrases.json"))["phrases"]; AN = json.load(open("work/anchors.json"))
def sst(x): x = max(0, min(1, x)); return x * x * x * (x * (6 * x - 15) + 10)
def text(d, xy, s, f, fill, sw=8, anchor="ms"): d.text(xy, s, font=f, fill=fill, stroke_width=sw, stroke_fill=INK, anchor=anchor)
def pill(d, box, fill, r=40): d.rounded_rectangle(box, r, fill=fill, outline=INK, width=9)
def fade(L, a): L.putalpha(L.getchannel("A").point(lambda v: int(v * a))); return L
# subtitle chunks: up to 3 words / 18 chars, never across phrases; ellipses split chunks
CH = []
for p in PH:
    cur = []
    for w in p["words"]:
        cur.append(w)
        if len(cur) >= 3 or sum(len(x[0]) for x in cur) >= 16 or w[0].endswith(("...", ".", ":", "?", ",")):
            CH.append(cur); cur = []
    if cur: CH.append(cur)
SUBF = B(66); SUBY = 1530
def subs(d, t):
    for c in CH:
        t0, t1 = c[0][1] - 0.05, c[-1][2] + 0.12
        if t0 <= t < t1:
            words = [w[0].upper().replace("...", "…") for w in c]
            widths = [d.textlength(x + " ", font=SUBF) for x in words]; x = W / 2 - (sum(widths) - d.textlength(" ", font=SUBF)) / 2
            pop = sst((t - t0) / 0.08)
            for (w, a, b), s, wd in zip(c, words, widths):
                on = a <= t < b or (t >= b and w is c[-1][0] and False)
                text(d, (x, SUBY + int(10 * (1 - pop))), s, SUBF, YEL if a <= t < b + 0.02 else (255, 255, 255), 10, "ls"); x += wd
            return
def frame(f, im):
    t = f / FPS; im = im.resize((W, H), Image.LANCZOS).convert("RGBA")
    if f <= 22: im = Image.alpha_composite(im, Image.new("RGBA", im.size, (18, 14, 24, 125)))
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    if f <= 22:
        text(d, (W / 2, 840), EP["serie"], A(255), (255, 246, 236), 15)
        pill(d, (W / 2 - 225, 900, W / 2 + 225, 1035), (214, 58, 51)); text(d, (W / 2, 998), f"PARTE {EP['parte']}", A(93), (255, 255, 255), 0)
        text(d, (W / 2, 1185), EP["titulo"], A(117), YEL, 10)
    else:
        S1 = AN["S"][1]
        a = sst((t - 0.8) / 0.35) * (1 - sst((t - (S1 - 0.35)) / 0.3)); g = sst((t - 1.0) / 0.9)
        if a > 0:
            L = Image.new("RGBA", im.size, (0, 0, 0, 0)); dd = ImageDraw.Draw(L)
            for i, (p, lab) in enumerate(EP["votos"]):
                y = 220 + i * 180; col = (110, 200, 90) if i == 0 else (150, 150, 165)
                pill(dd, (60, y, W - 60, y + 144), (250, 247, 240)); bw = (W - 150) * p / 100 * g
                dd.rounded_rectangle((75, y + 15, 75 + max(30, bw), y + 129), 30, fill=col)
                text(dd, (99, y + 99), f"{round(p * g)}%", A(81), (255, 255, 255), 7, "ls")
                text(dd, (290, y + 93), lab, B(38 if len(lab) < 24 else 34), (255, 255, 255), 6, "ls")
            ov = Image.alpha_composite(ov, fade(L, a)); d = ImageDraw.Draw(ov)
        subs(d, t)
        for i, (k, lab, col, ta) in enumerate([("A", EP["opciones"][0], (64, 140, 230), AN["optA"] - 0.2), ("B", EP["opciones"][1], (230, 90, 60), AN["optB"] - 0.2)]):
            al = sst((t - ta) / 0.3)
            if al <= 0: continue
            L = Image.new("RGBA", im.size, (0, 0, 0, 0)); dd = ImageDraw.Draw(L); y = 1060 + i * 205 + int(40 * (1 - al))
            pill(dd, (54, y, W - 54, y + 175), (250, 247, 240), 45); dd.ellipse((78, y + 24, 210, y + 156), fill=col, outline=INK, width=9)
            text(dd, (144, y + 123), k, A(93), (255, 255, 255), 0)
            ws = lab.split(); l1 = " ".join(ws[:3]); l2 = " ".join(ws[3:])
            text(dd, (240, y + 78 if l2 else y + 108), l1, B(46), INK, 0, "ls")
            if l2: text(dd, (240, y + 140), l2, B(46), INK, 0, "ls")
            ov = Image.alpha_composite(ov, fade(L, al))
    im = Image.alpha_composite(im, ov)
    fd = round(AN["door"] * FPS)
    if fd <= f <= fd + 4: im = Image.blend(im, Image.new("RGBA", im.size, (255, 255, 255, 255)), 0.55 * (1 - (f - fd) / 5))
    return im.convert("RGB")
if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]; os.makedirs(dst, exist_ok=True)
    fl = [int(x) for x in sys.argv[3].split(",")] if len(sys.argv) > 3 else None
    for p in sorted(glob.glob(src + "/f*.jpg")):
        f = int(p[-8:-4])
        if fl and f not in fl: continue
        o = f"{dst}/f{f:04d}.jpg"
        if not fl and os.path.exists(o): continue
        frame(f, Image.open(p)).save(o, quality=93)

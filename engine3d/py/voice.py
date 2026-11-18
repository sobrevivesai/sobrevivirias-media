# Voz con Piper (gratis, local). Genera voice.wav + work/phrases.json con tiempos por palabra estimados.
import json, numpy as np, subprocess, tempfile, os, re, wave, sys, soundfile as sf
sys.path.insert(0, "/usr/local/lib/python3.13/site-packages")
from piper import PiperVoice, SynthesisConfig
VD = os.environ.get("PIPER_DIR", "/home/claude/piper")
NARR = os.environ.get("NARR", "es_MX-claude-high"); OTHER = os.environ.get("OTHER", "es_MX-ald-medium")
_V = {}
def voice(m):
    if m not in _V: _V[m] = PiperVoice.load(f"{VD}/vits-piper-{m}/{m}.onnx")
    return _V[m]
SR = 48000
# Cadena de "narrador de tráiler": voz más grave y cálida, presencia, de-esser, sala muy sutil.
FILT = ("highpass=f=70,equalizer=f=140:t=q:w=0.9:g=2.5,equalizer=f=420:t=q:w=1.2:g=-2.5,equalizer=f=3000:t=q:w=1.3:g=2.5,"
        "deesser=i=0.35,acompressor=threshold=-20dB:ratio=2.2:attack=6:release=90:makeup=2,aecho=0.85:0.6:28|47:0.07|0.04,lowpass=f=11500")
SPK = ",highpass=f=380,lowpass=f=3300,acrusher=bits=10:mix=0.2"
ACCION = ("corre", "salta", "golpe", "grita", "rápido", "ya", "¡")
def plan(text, i, n):
    """Divide la frase en trozos (en '...' y entre oraciones) y les da velocidad, tono y pausa distintos para que no suene plano."""
    parts = []; buf = ""
    for tok in text.replace("...", "…").split(" "):
        buf += (" " if buf else "") + tok
        if tok.endswith("…") or (tok.endswith((".", "?", "!")) and len(buf.split()) >= 3): parts.append(buf.strip()); buf = ""
    if buf: parts.append(buf.strip())
    out = []
    for j, ptxt in enumerate(parts):
        w = len(ptxt.split()); low = ptxt.lower()
        ls = 0.9
        if w <= 5: ls = 1.0                                   # frases cortas = golpe dramático, más lentas
        if any(k in low for k in ACCION): ls = 0.84           # acción = más rápido
        if i == 0: ls = 0.98                                  # gancho: claro y con peso
        if i == n - 1: ls = 1.0                               # pregunta final
        st = -1.0 + (0.35 if j % 2 else -0.15)                # voz más grave + variación entre oraciones
        if ptxt.endswith("?"): st += 0.7
        if i == 0: st -= 0.5
        pause = 0.42 if ptxt.endswith("…") else 0.16
        out.append((ptxt.replace("…", "."), ls, st, pause))
    return out
def tts(text, m, ls_mul, extra="", i=0, n=1):
    chunks = []
    for ptxt, ls, st, pause in plan(text, i, n):
        p = tempfile.mktemp(suffix=".wav")
        with wave.open(p, "wb") as w: voice(m).synthesize_wav(ptxt, w, syn_config=SynthesisConfig(length_scale=ls * ls_mul, noise_scale=0.72, noise_w_scale=0.95))
        o = tempfile.mktemp(suffix=".f32")
        pf = f"rubberband=pitch={2 ** (st / 12):.4f}:formant=preserved,"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", p, "-af", pf + FILT + extra, "-f", "f32le", "-ar", str(SR), "-ac", "1", o], check=True)
        a = np.fromfile(o, np.float32); os.remove(p); os.remove(o)
        env = np.abs(a); idx = np.where(env > 0.02 * env.max())[0]; a = a[max(0, idx[0] - 600): idx[-1] + 2400]
        chunks += [a / np.abs(a).max(), np.zeros(int(pause * SR), np.float32)]
    a = np.concatenate(chunks[:-1]); return a / np.abs(a).max() * 0.9
def wtimes(text, t0, t1):
    ws = text.split(); vw = lambda w: max(1, len(re.findall(r"[aeiouáéíóúü]+", w.lower())))
    wt = [vw(w) + (1.6 if w.endswith("...") else 0.9 if w[-1] in ".,:;?!" else 0) for w in ws]
    tot = sum(wt); out = []; t = t0
    for w, k in zip(ws, wt): d = (t1 - t0) * k / tot; out.append([w, round(t, 3), round(t + d, 3)]); t += d
    return out
if __name__ == "__main__":
    lines = json.load(open("script.json")); cfg = json.load(open("voices.json")) if os.path.exists("voices.json") else {}
    LS = float(os.environ.get("LS", "1.0")); PAUSE = {int(k): v for k, v in cfg.get("pausas", {}).items()}
    T = float(cfg.get("inicio", 0.12)); phr = []; out = []  # sin portada: la voz arranca en el cuadro 4
    for i, t in enumerate(lines):
        other = str(i) in cfg.get("otra_voz", [])
        a = tts(t, OTHER if other else NARR, LS, SPK if str(i) in cfg.get("parlante", []) else "", i, len(lines))
        t1 = T + len(a) / SR
        phr.append({"i": i, "text": t, "t0": round(T, 3), "t1": round(t1, 3), "words": wtimes(t, T + 0.05, t1 - 0.05)})
        out.append((T, a)); T = t1 + PAUSE.get(i, 0.32)
    T += 3.2
    buf = np.zeros(int(T * SR) + 1, np.float32)
    for t0, a in out: s = int(t0 * SR); buf[s:s + len(a)] += a
    sf.write("voice.wav", buf, SR)
    json.dump({"dur": T, "frames": round(T * 30), "phrases": phr}, open("work/phrases.json", "w"), indent=1, ensure_ascii=False)
    print(T, round(T * 30))

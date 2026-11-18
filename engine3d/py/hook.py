# Gancho: agrega a anchors.json / tim.js el "flash-forward" del plano 0 y genera el golpe sonoro del cuadro 0.
# episode.json: "gancho_de": índice de la frase cuyo momento se muestra en el gancho (el clímax del capítulo),
#               "gancho_desfase": segundos dentro de esa frase (opcional), "gancho_texto": 2-4 palabras en MAYÚSCULAS.
import json, sys, numpy as np, soundfile as sf
A = json.load(open("work/anchors.json")); E = json.load(open("episode.json")); P = json.load(open("work/phrases.json"))["phrases"]
if "gancho_de" in E:
    A["hookSrc"] = round(P[E["gancho_de"]]["t0"] + E.get("gancho_desfase", 0.3), 3); A["hookRate"] = E.get("gancho_velocidad", 0.8)
json.dump(A, open("work/anchors.json", "w"), indent=1)
open(sys.argv[1], "w").write("window.TIM=" + json.dumps(A) + ";")
SR = 48000; n = int(1.6 * SR); t = np.arange(n) / SR; rng = np.random.default_rng(7)
boom = np.sin(2 * np.pi * (70 * np.exp(-t * 3) + 32) * t) * np.exp(-t * 2.6)
hiss = np.convolve(rng.standard_normal(n), np.ones(6) / 6, "same") * np.exp(-t * 9) * 0.35
sf.write("work/hit.wav", ((boom + hiss) * 0.5).astype(np.float32), SR)
print("gancho:", A.get("hookSrc"))

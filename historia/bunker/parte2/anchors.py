import json, sys
d = json.load(open("work/phrases.json")); P = d["phrases"]
def w(i, word):
    for x in P[i]["words"]:
        if x[0].lower().strip(".,:;?!¿¡").startswith(word): return x[1]
    raise SystemExit(f"no {word} in {i}")
S = [0] + [round(P[i]["t0"] - 0.14, 3) for i in range(1, len(P))] + [99]
A = dict(S=S, dur=d["dur"], frames=d["frames"], off=w(3, "luz"), k1=w(4, "golpea"), smile=w(6, "sonríe"), name=w(7, "nombre"),
         key=w(9, "llave"), clic=w(10, "clic"), spin=w(10, "volante"), optA=w(11, "trabas"), optB=w(11, "dejas"))
json.dump(A, open("work/anchors.json", "w"), indent=1)
open(sys.argv[1], "w").write("window.TIM=" + json.dumps(A) + ";")
print(A)

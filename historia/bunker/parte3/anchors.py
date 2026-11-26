import json, sys
d = json.load(open("work/phrases.json")); P = d["phrases"]
def w(i, word):
    for x in P[i]["words"]:
        if x[0].lower().strip(".,:;?!¿¡").startswith(word): return x[1]
    raise SystemExit(f"no {word} in {i}")
S = [0] + [round(P[i]["t0"] - 0.14, 3) for i in range(1, len(P))] + [99]
A = dict(S=S, dur=d["dur"], frames=d["frames"], bar=w(4, "barra"), hit=w(5, "golpea"), smile=w(6, "sonríe"), point=w(8, "señala"),
         gone=w(9, "desaparece"), onyou=w(9, "está"), turn=w(10, "gira"), bend=w(10, "dobla"), optA=w(12, "pides"), optB=w(12, "cortas"))
json.dump(A, open("work/anchors.json", "w"), indent=1)
open(sys.argv[1], "w").write("window.TIM=" + json.dumps(A) + ";")
print(A)

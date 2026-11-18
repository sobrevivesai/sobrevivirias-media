import json, sys
d = json.load(open("work/phrases.json")); P = d["phrases"]
def w(i, word):
    for x in P[i]["words"]:
        if x[0].lower().strip(".,:;?!¿¡").startswith(word): return x[1]
    raise SystemExit(f"no {word} in {i}")
S = [0] + [round(P[i]["t0"] - 0.14, 3) for i in range(1, len(P))] + [99]
fall = w(8, "cae")
A = dict(S=S, dur=d["dur"], frames=d["frames"], drop=w(3, "caes"), kick=w(3, "pateas"), turn=P[5]["t0"], aim=w(6, "apunta"), creak=w(7, "cruje"),
         fall=fall, flash=[fall + 0.25], num=w(9, "número"), roar=P[10]["t0"], hand=w(10, "levanta"), still=w(10, "queda"), bring=w(11, "tráeme"),
         optA=w(12, "cargas"), optB=w(12, "tomas"))
json.dump(A, open("work/anchors.json", "w"), indent=1)
open(sys.argv[1], "w").write("window.TIM=" + json.dumps(A) + ";")
print(A)

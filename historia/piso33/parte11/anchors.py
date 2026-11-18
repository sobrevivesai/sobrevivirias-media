import json, sys
d = json.load(open("work/phrases.json")); P = d["phrases"]
def w(i, word):
    for x in P[i]["words"]:
        if x[0].lower().strip(".,:;?!¿¡").startswith(word): return x[1]
    raise SystemExit(f"no {word} in {i}")
S = [0] + [round(P[i]["t0"] - 0.14, 3) for i in range(1, 16)] + [99]
A = dict(S=S, dur=d["dur"], frames=d["frames"], door=999, open=w(2, "chirrido"), boost=round(P[1]["t0"] + 0.3, 3), scratch=w(7, "raspa"), scr8=P[8]["t0"],
         light=w(9, "enciende"), eyes=w(10, "brillan"), breathe=w(12, "respira"), lookL=P[14]["t0"], lookF=w(14, "frente"),
         optA=w(15, "bajas"), optB=w(15, "escapas"), ojos=w(10, "ojos"), jaulas=w(11, "jaulas"))
json.dump(A, open("work/anchors.json", "w"), indent=1)
open(sys.argv[1], "w").write("window.TIM=" + json.dumps(A) + ";")
print(A)

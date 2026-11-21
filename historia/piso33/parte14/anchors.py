import json, sys
d = json.load(open("work/phrases.json")); P = d["phrases"]
def w(i, word):
    for x in P[i]["words"]:
        if x[0].lower().strip(".,:;?!¿¡").startswith(word): return x[1]
    raise SystemExit(f"no {word} in {i}")
S = [0] + [round(P[i]["t0"] - 0.14, 3) for i in range(1, len(P))] + [99]
A = dict(S=S, dur=d["dur"], frames=d["frames"], carry=w(3, "cargas"), shout=P[4]["t0"], drop=w(5, "tira"), grab=w(6, "agarras"),
         door=w(7, "abre"), roar=w(7, "ruge"), smash=w(8, "golpea"), wake=w(10, "abre"), burst=w(11, "rompe"), optA=w(12, "cruzas"), optB=w(12, "encierras"))
json.dump(A, open("work/anchors.json", "w"), indent=1)
open(sys.argv[1], "w").write("window.TIM=" + json.dumps(A) + ";")
print(A)

import json, sys
d = json.load(open("work/phrases.json")); P = d["phrases"]
def w(i, word):
    for x in P[i]["words"]:
        if x[0].lower().strip(".,:;?!¿¡").startswith(word): return x[1]
    raise SystemExit(f"no {word} in {i}")
S = [0] + [round(P[i]["t0"] - 0.14, 3) for i in range(1, len(P))] + [99]
A = dict(S=S, dur=d["dur"], frames=d["frames"], apartan=w(5, "apartan"), drop=w(5, "apartan"), door=w(3, "abre"), roar=w(8, "ruge"), smash=w(9, "aparta"),
         wake=w(4, "avanzan"), burst=w(8, "rompe"), chain=w(10, "tira"), optA=w(12, "trepas"), optB=w(12, "dejas"))
json.dump(A, open("work/anchors.json", "w"), indent=1)
open(sys.argv[1], "w").write("window.TIM=" + json.dumps(A) + ";")
print(A)

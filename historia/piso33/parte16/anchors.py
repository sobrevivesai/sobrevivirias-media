import json, sys
d = json.load(open("work/phrases.json")); P = d["phrases"]
def w(i, word):
    for x in P[i]["words"]:
        if x[0].lower().strip(".,:;?!¿¡").startswith(word): return x[1]
    raise SystemExit(f"no {word} in {i}")
S = [0] + [round(P[i]["t0"] - 0.14, 3) for i in range(1, len(P))] + [99]
A = dict(S=S, dur=d["dur"], frames=d["frames"], grab=w(5, "agarra"), drop=w(5, "agarra"), up=w(3, "sube"), climb=w(4, "trepas"), free=w(8, "suelta"),
         roar=w(9, "ruge"), heli=w(12, "despegan"), optA=w(13, "búnker"), optB=w(13, "isla"))
json.dump(A, open("work/anchors.json", "w"), indent=1)
open(sys.argv[1], "w").write("window.TIM=" + json.dumps(A) + ";")
print(A)

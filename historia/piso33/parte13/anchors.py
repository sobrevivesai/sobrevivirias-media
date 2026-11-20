import json, sys
d = json.load(open("work/phrases.json")); P = d["phrases"]
def w(i, word):
    for x in P[i]["words"]:
        if x[0].lower().strip(".,:;?!¿¡").startswith(word): return x[1]
    raise SystemExit(f"no {word} in {i}")
S = [0] + [round(P[i]["t0"] - 0.14, 3) for i in range(1, len(P))] + [99]
A = dict(S=S, dur=d["dur"], frames=d["frames"], jump=w(3, "saltas"), shout=P[4]["t0"], taunt=P[5]["t0"], step=w(6, "paso"), shot=w(7, "dispara"),
         look=w(8, "pero"), turn=P[9]["t0"], yank=w(10, "arranca"), lift=w(10, "levanta"), kick=w(11, "patalea"), eyes=w(12, "abre"),
         optA=w(13, "salvas"), optB=w(13, "escapas"))
json.dump(A, open("work/anchors.json", "w"), indent=1)
open(sys.argv[1], "w").write("window.TIM=" + json.dumps(A) + ";")
print(A)

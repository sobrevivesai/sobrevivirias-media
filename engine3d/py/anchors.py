import json, sys
d = json.load(open("work/phrases.json")); P = d["phrases"]
def w(i, word):
    for x in P[i]["words"]:
        if x[0].lower().strip(".,:;?!¿¡").startswith(word): return x[1]
    raise SystemExit(f"no {word} in {i}")
S = [0] + [round(P[i]["t0"] - 0.14, 3) for i in range(1, 16)] + [99]
door = w(10, "cierra")
A = dict(S=S, dur=d["dur"], frames=d["frames"], door=door, red=round(door + 0.4, 3), whip=round(door - 0.6, 3),
         spk=w(11, "voz"), talkEnd=P[12]["t1"], sleep=round(P[13]["t0"] + 0.4, 3), up=P[14]["t0"] + 0.15, down=w(14, "abajo") - 0.1,
         afuera=w(5, "afuera"), ustedes=w(9, "son"), ibar0=P[12]["t0"], ibar1=P[12]["t1"], optA=w(15, "ventilación"), optB=w(15, "cortas"))
json.dump(A, open("work/anchors.json", "w"), indent=1)
open(sys.argv[1], "w").write("window.TIM=" + json.dumps(A) + ";")
print(A)

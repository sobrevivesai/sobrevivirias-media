import numpy as np, soundfile as sf, json
A=json.load(open("work/anchors.json")); S=A["S"]
SR=48000; v,_=sf.read("voice.wav"); N=len(v); t=np.arange(N)/SR; rng=np.random.default_rng(15)
def noise(d): return rng.standard_normal(int(d*SR))
def lp(x,k): return np.convolve(x,np.ones(k)/k,"same")
def thud(d=0.3,f=60):
    tt=np.arange(int(d*SR))/SR; return np.sin(2*np.pi*f*tt)*np.exp(-tt*14)+0.4*lp(noise(d),25)*np.exp(-tt*25)
def sting(d=2.0):
    tt=np.arange(int(d*SR))/SR; return (np.sin(2*np.pi*38*tt)+0.5*np.sin(2*np.pi*57*tt)+0.3*lp(noise(d),60))*np.exp(-tt*1.6)
mus=np.zeros(N); DROP=A["drop"]
s=S[1]
while s<N/SR-0.3 and s<A["optA"]:
    i=int(s*SR); n=int(0.4*SR); tt=np.arange(n)/SR
    if i+n<N: mus[i:i+n]+=0.6*np.sin(2*np.pi*49*tt)*np.exp(-tt*7)
    s+=max(0.3,0.7-0.012*(s-S[1]))
pad=sum(np.sin(2*np.pi*f*t+0.3*np.sin(2*np.pi*0.2*t)) for f in [196,233.1,293.7])*0.06*(t>S[1]-0.3)
hook=(0.3*np.sin(2*np.pi*41*t)+0.15*np.sin(2*np.pi*55*t))*(t<S[1])
mus=mus+pad+hook
for s in np.arange(A["optA"]+0.1,N/SR-0.3,0.8):
    for o,a in [(0,1),(0.18,0.7)]:
        i=int((s+o)*SR); n=int(0.12*SR); tt=np.arange(n)/SR
        if i+n<N: mus[i:i+n]+=0.9*a*np.sin(2*np.pi*50*tt)*np.exp(-tt*30)
fx=np.zeros(N)
def put(s,a,g=1):
    i=int(s*SR)
    if i<0 or i>=N: return
    a=a[:N-i]; fx[i:i+len(a)]+=a*g
put(0.02,thud(1.0,40)*1.4)
put(A["drop"],thud(0.4,45)*1.3); put(A["drop"]+0.1,lp(noise(0.5),20)*np.exp(-np.arange(int(.5*SR))/SR*8)*0.4)
put(A["door"],thud(0.3,70)); put(A["roar"],sting(1.5),0.7)
for k in range(5): put(A["smash"]+0.25*k,thud(0.25,55),0.9)
put(A["wake"],sting(1.2),0.4); put(A["burst"],thud(0.5,35)*1.5); put(A["burst"]+0.1,lp(noise(0.6),8)*np.exp(-np.arange(int(.6*SR))/SR*7)*0.6)
sf.write("music.wav",mus.astype(np.float32),SR); sf.write("sfx.wav",fx.astype(np.float32),SR)
def grms(x):
    w=int(0.4*SR); b=x[:len(x)//w*w].reshape(-1,w); r=np.sqrt((b**2).mean(1)); r=r[r>0.1*r.max()]; return np.sqrt((r**2).mean())
vr=grms(v); mus*=0.5*vr/grms(mus); fx*=0.5*vr/grms(fx); pk=0.7*np.abs(v).max()
if np.abs(fx).max()>pk: fx*=pk/np.abs(fx).max()
print("music %.1f dB, sfx %.1f dB vs voice"%(20*np.log10(grms(mus)/vr),20*np.log10(grms(fx)/vr)))
mix=v+mus+fx; sf.write("mix.wav",(mix/np.abs(mix).max()*0.89).astype(np.float32),SR)

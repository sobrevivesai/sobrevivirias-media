import numpy as np, soundfile as sf, json
A=json.load(open("work/anchors.json")); S=A["S"]
SR=48000; v,_=sf.read("voice.wav"); N=len(v); t=np.arange(N)/SR; rng=np.random.default_rng(12)
def env(a,r,n): e=np.ones(n); a=int(a*SR); r=int(r*SR); e[:a]=np.linspace(0,1,a) if a else 1; e[-r:]*=np.linspace(1,0,r); return e
def noise(d): return rng.standard_normal(int(d*SR))
def lp(x,k): return np.convolve(x,np.ones(k)/k,"same")
def thud(d=0.3,f=60):
    tt=np.arange(int(d*SR))/SR; return np.sin(2*np.pi*f*tt)*np.exp(-tt*14)+0.4*lp(noise(d),25)*np.exp(-tt*25)
def sting(d=2.0):
    tt=np.arange(int(d*SR))/SR; return (np.sin(2*np.pi*38*tt)+0.5*np.sin(2*np.pi*57*tt)+0.3*lp(noise(d),60))*np.exp(-tt*1.6)
# music: tense pulse that speeds up toward the creature, drops out at the fall, drone after; heartbeat at the choice
mus=np.zeros(N); FALL=A["fall"]
k=0.0; s=S[1]
while s<FALL-0.2:
    i=int(s*SR); n=int(0.4*SR); tt=np.arange(n)/SR
    if i+n<N: mus[i:i+n]+=0.6*np.sin(2*np.pi*49*tt)*np.exp(-tt*7)
    s+=max(0.42,0.75-0.012*(s-S[1]))
pad=sum(np.sin(2*np.pi*f*t+0.3*np.sin(2*np.pi*0.2*t)) for f in [196,233.1,293.7])*0.07*(t<FALL)*(t>S[1]-0.3)
dr=(0.35*np.sin(2*np.pi*41*t)+0.2*np.sin(2*np.pi*61.5*t))*np.clip((t-FALL-0.3)/1.5,0,1)
hook=(0.3*np.sin(2*np.pi*41*t)+0.15*np.sin(2*np.pi*55*t))*(t<S[1])
mus=mus+pad+dr+hook
for s in np.arange(S[12]+0.1,N/SR-0.3,0.8):
    for o,a in [(0,1),(0.18,0.7)]:
        i=int((s+o)*SR); n=int(0.12*SR); tt=np.arange(n)/SR
        if i+n<N: mus[i:i+n]+=0.9*a*np.sin(2*np.pi*50*tt)*np.exp(-tt*30)
fx=np.zeros(N)
def put(s,a,g=1):
    i=int(s*SR)
    if i<0 or i>=N: return
    a=a[:N-i]; fx[i:i+len(a)]+=a*g
# hook: creature landing (slow-mo time)
hl=(A["fall"]+0.32-A["hookSrc"])/A["hookRate"]; put(hl,thud(1.0,40)*1.6); put(hl,lp(noise(0.8),6)*np.exp(-np.arange(int(.8*SR))/SR*8)*0.5)
put(A["kick"],thud(0.25,90)); put(A["kick"]+0.25,lp(noise(0.5),5)*0.3*env(0.01,0.4,int(.5*SR)))  # grille clang
put(A["kick"]+0.62,np.sin(2*np.pi*900*np.arange(int(.5*SR))/SR)*np.exp(-np.arange(int(.5*SR))/SR*10)*0.35)
put(A["drop"]+0.32,thud(0.35,70)); put(A["drop"]+1.02,thud(0.35,65))
put(A["turn"]+0.3,lp(noise(0.3),10)*0.3*env(0.05,0.2,int(.3*SR)))
put(A["aim"]-0.1,lp(noise(0.08),2)*0.8); put(A["aim"]+0.05,lp(noise(0.06),2)*0.6)  # rifle click
tt=np.arange(int(1.6*SR))/SR; put(A["creak"]-0.1,np.sign(np.sin(2*np.pi*np.cumsum(120+40*np.sin(2*np.pi*2.5*tt))/SR))*0.12*lp(np.abs(noise(1.6)),40)*3)
put(A["fall"]+0.32,thud(1.0,40)*1.6); put(A["fall"]+0.32,lp(noise(0.8),6)*np.exp(-np.arange(int(.8*SR))/SR*8)*0.5)
put(A["num"]-0.05,sting(),0.6)
rr=lp(noise(1.6),12)*env(0.1,0.5,int(1.6*SR))*(0.8+0.2*np.sin(2*np.pi*30*np.arange(int(1.6*SR))/SR)); put(A["roar"],rr*1.2)
put(A["still"]-0.05,sting(1.5),0.7)
sf.write("music.wav",mus.astype(np.float32),SR); sf.write("sfx.wav",fx.astype(np.float32),SR)
def grms(x):
    w=int(0.4*SR); b=x[:len(x)//w*w].reshape(-1,w); r=np.sqrt((b**2).mean(1)); r=r[r>0.1*r.max()]; return np.sqrt((r**2).mean())
vr=grms(v); mus*=0.5*vr/grms(mus); fx*=0.5*vr/grms(fx); pk=0.7*np.abs(v).max()
if np.abs(fx).max()>pk: fx*=pk/np.abs(fx).max()
print("music %.1f dB, sfx %.1f dB vs voice"%(20*np.log10(grms(mus)/vr),20*np.log10(grms(fx)/vr)))
mix=v+mus+fx; sf.write("mix.wav",(mix/np.abs(mix).max()*0.89).astype(np.float32),SR)

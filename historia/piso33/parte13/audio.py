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
# music: tense pulse until the lift, drone after, heartbeat at the choice
mus=np.zeros(N); LIFT=A["lift"]
s=S[1]
while s<LIFT-0.2:
    i=int(s*SR); n=int(0.4*SR); tt=np.arange(n)/SR
    if i+n<N: mus[i:i+n]+=0.6*np.sin(2*np.pi*49*tt)*np.exp(-tt*7)
    s+=max(0.42,0.75-0.012*(s-S[1]))
pad=sum(np.sin(2*np.pi*f*t+0.3*np.sin(2*np.pi*0.2*t)) for f in [196,233.1,293.7])*0.07*(t<LIFT)*(t>S[1]-0.3)
dr=(0.35*np.sin(2*np.pi*41*t)+0.2*np.sin(2*np.pi*61.5*t))*np.clip((t-LIFT)/1.2,0,1)
hook=(0.3*np.sin(2*np.pi*41*t)+0.15*np.sin(2*np.pi*55*t))*(t<S[1])
mus=mus+pad+dr+hook
for s in np.arange(S[13]+0.1,N/SR-0.3,0.8):
    for o,a in [(0,1),(0.18,0.7)]:
        i=int((s+o)*SR); n=int(0.12*SR); tt=np.arange(n)/SR
        if i+n<N: mus[i:i+n]+=0.9*a*np.sin(2*np.pi*50*tt)*np.exp(-tt*30)
fx=np.zeros(N)
def put(s,a,g=1):
    i=int(s*SR)
    if i<0 or i>=N: return
    a=a[:N-i]; fx[i:i+len(a)]+=a*g
put(0.02,thud(1.0,40)*1.4); put(0.02,lp(noise(0.8),6)*np.exp(-np.arange(int(.8*SR))/SR*8)*0.5)
put(A["jump"]+0.3,thud(0.3,80)); put(A["step"]+0.1,thud(0.5,38)*1.3); put(A["step"]+0.75,thud(0.5,36)*1.4); put(A["step"]+1.4,thud(0.5,34)*1.5)
put(A["shot"]+0.05,lp(noise(0.25),3)*np.exp(-np.arange(int(.25*SR))/SR*25)*1.5)
put(A["shot"]+0.25,np.sin(2*np.pi*1400*np.arange(int(.4*SR))/SR)*np.exp(-np.arange(int(.4*SR))/SR*12)*0.3)
put(A["look"]+0.2,sting(1.5),0.6)
put(A["yank"],thud(0.3,60)); put(A["lift"],lp(noise(0.9),20)*env(0.05,0.5,int(.9*SR))*0.35)
put(A["kick"],thud(0.2,90),0.6); put(A["kick"]+0.5,thud(0.2,90),0.6)
put(A["eyes"]-0.05,sting(1.5),0.7)
sf.write("music.wav",mus.astype(np.float32),SR); sf.write("sfx.wav",fx.astype(np.float32),SR)
def grms(x):
    w=int(0.4*SR); b=x[:len(x)//w*w].reshape(-1,w); r=np.sqrt((b**2).mean(1)); r=r[r>0.1*r.max()]; return np.sqrt((r**2).mean())
vr=grms(v); mus*=0.5*vr/grms(mus); fx*=0.5*vr/grms(fx); pk=0.7*np.abs(v).max()
if np.abs(fx).max()>pk: fx*=pk/np.abs(fx).max()
print("music %.1f dB, sfx %.1f dB vs voice"%(20*np.log10(grms(mus)/vr),20*np.log10(grms(fx)/vr)))
mix=v+mus+fx; sf.write("mix.wav",(mix/np.abs(mix).max()*0.89).astype(np.float32),SR)

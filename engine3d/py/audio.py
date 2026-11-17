import numpy as np, soundfile as sf, json
A=json.load(open("work/anchors.json")); S=A["S"]
SR=48000; v,_=sf.read("voice.wav"); N=len(v); t=np.arange(N)/SR; rng=np.random.default_rng(3)
def env(a,r,n): e=np.ones(n); a=int(a*SR); r=int(r*SR); e[:a]=np.linspace(0,1,a) if a else 1; e[-r:]*=np.linspace(1,0,r); return e
# ---- music: low pulse + minor pad, stops at the door slam, then drone
mus=np.zeros(N); bpm=84; beat=60/bpm; SLAM=A["door"]
notes=[55,55,52,53]  # A1 A1 E1(approx) F1 in Hz-ish roots
for k in range(int(SLAM/beat)):
    s=k*beat; i=int(s*SR); n=int(0.5*SR)
    if i+n>N: break
    f=[55,55,49,51.9][(k//4)%4]; tt=np.arange(n)/SR
    mus[i:i+n]+=0.6*np.sin(2*np.pi*f*tt)*np.exp(-tt*6)
    if k%2==1: mus[i:i+n]+=0.25*np.sin(2*np.pi*f*2*tt)*np.exp(-tt*9)
pad=np.zeros(N); m=t<SLAM
for f in [220,261.6,329.6]: pad+=np.sin(2*np.pi*f*t+0.3*np.sin(2*np.pi*0.2*t))
pad*=0.08*(0.6+0.4*np.sin(2*np.pi*t/8)); pad[~m]=0
fade=np.clip((t-0.2)/1.5,0,1); mus=(mus+pad)*fade
dr=0.35*np.sin(2*np.pi*41*t)+0.2*np.sin(2*np.pi*61.5*t); dr*=np.clip((t-SLAM-0.4)/2,0,1)*(t>SLAM)
mus+=dr*(1+0.3*np.sin(2*np.pi*0.5*t))
# heartbeat in the choice
for s in np.arange(S[15]+0.15,N/SR-0.3,0.85):
    for o,a in [(0,1),(0.18,0.7)]:
        i=int((s+o)*SR); n=int(0.12*SR); tt=np.arange(n)/SR
        if i+n<N: mus[i:i+n]+=0.9*a*np.sin(2*np.pi*50*tt)*np.exp(-tt*30)
# ---- sfx
fx=np.zeros(N)
def put(s,a,g=1):
    i=int(s*SR); a=a[:max(0,N-i)]; fx[i:i+len(a)]+=a*g
def noise(d): return rng.standard_normal(int(d*SR))
def lp(x,k): return np.convolve(x,np.ones(k)/k,"same")
def thud(d=0.25,f=70):
    tt=np.arange(int(d*SR))/SR; return (np.sin(2*np.pi*f*tt)*np.exp(-tt*18)+0.4*lp(noise(d),30)*np.exp(-tt*30))
for s in np.arange(0.3,S[1]-0.2,0.42): put(s+0.07*rng.random(),thud(),0.7+0.3*rng.random())  # pounding door
put(0,lp(noise(S[1]),200)*0.6*env(0.5,1,int(S[1]*SR)))  # wind
buzz=(np.sign(np.sin(2*np.pi*120*t[:int((S[4]-S[3])*SR)]))*0.05); put(S[3],buzz*env(0.2,0.3,len(buzz)))
for s in np.arange(S[3]+0.1,S[4]-0.1,0.33):
    if rng.random()<0.45: put(s,lp(noise(0.06),4)*0.4)
def creak(d,f0):
    tt=np.arange(int(d*SR))/SR; f=f0+30*np.sin(2*np.pi*3*tt); return np.sign(np.sin(2*np.pi*np.cumsum(f)/SR))*0.15*np.exp(-tt*2)*lp(np.abs(noise(d)),40)*3
put(S[5]+0.15,creak(1.0,140),0.7)
def sting(d=2.0):
    tt=np.arange(int(d*SR))/SR; return (np.sin(2*np.pi*38*tt)+0.5*np.sin(2*np.pi*57*tt)+0.3*lp(noise(d),60))*np.exp(-tt*1.6)
put(A["afuera"]-0.05,sting(),0.8); put(A["ustedes"]-0.05,sting(),0.8)
put(S[7]+0.2,lp(noise(0.5),6)*0.25*env(0.05,0.2,int(0.5*SR)))  # marker squeak-ish
put(S[8]+0.05,lp(noise(0.55),25)*0.6*env(0.05,0.2,int(0.55*SR)))  # drawer slide
put(S[8]+1.35,np.sin(2*np.pi*1800*np.arange(int(.3*SR))/SR)*np.exp(-np.arange(int(.3*SR))/SR*14)*0.4)  # glass ting
put(SLAM-0.65,lp(noise(0.65),15)*0.4*env(0.4,0.05,int(0.65*SR)))  # door swing whoosh
put(SLAM,thud(0.9,48)*1.6+lp(noise(0.9),8)*np.exp(-np.arange(int(.9*SR))/SR*12)*0.8)
for s in np.arange(A["red"],N/SR,1.0):  # alarm
    n=int(0.45*SR); tt=np.arange(n)/SR; put(s,np.sin(2*np.pi*(700+250*tt/0.45)*tt)*0.12*env(0.02,0.1,n))
dd=A["ibar1"]-A["ibar0"]+0.5; st=lp(noise(dd),3)*0.08*env(0.1,0.3,int(dd*SR)); put(A["ibar0"]-0.2,st)  # speaker static
sf.write("music.wav",mus.astype(np.float32),SR); sf.write("sfx.wav",fx.astype(np.float32),SR)
# ---- mix: music at 50 % of voice gated RMS, sfx at 50 % with peaks <= 0.7 * voice peak
def grms(x):
    w=int(0.4*SR); b=x[:len(x)//w*w].reshape(-1,w); r=np.sqrt((b**2).mean(1)); r=r[r>0.1*r.max()]; return np.sqrt((r**2).mean())
vr=grms(v); mus*=0.5*vr/grms(mus); fx*=0.5*vr/grms(fx); pk=0.7*np.abs(v).max()
if np.abs(fx).max()>pk: fx*=pk/np.abs(fx).max()
db=lambda x:20*np.log10(grms(x)/vr)
print("music %.1f dB, sfx %.1f dB vs voice"%(db(mus),db(fx)))
mix=v+mus+fx; mix=mix/np.abs(mix).max()*0.89
sf.write("mix.wav",mix.astype(np.float32),SR)

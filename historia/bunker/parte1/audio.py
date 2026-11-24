import numpy as np, soundfile as sf, json
A=json.load(open("work/anchors.json")); S=A["S"]
SR=48000; v,_=sf.read("voice.wav"); N=len(v); t=np.arange(N)/SR; rng=np.random.default_rng(101)
def noise(d): return rng.standard_normal(int(d*SR))
def lp(x,k): return np.convolve(x,np.ones(k)/k,"same")
def thud(d=0.3,f=60):
    tt=np.arange(int(d*SR))/SR; return np.sin(2*np.pi*f*tt)*np.exp(-tt*14)+0.4*lp(noise(d),25)*np.exp(-tt*25)
def clang(d=0.7):
    tt=np.arange(int(d*SR))/SR; return (np.sin(2*np.pi*180*tt)+0.6*np.sin(2*np.pi*317*tt)+0.4*np.sin(2*np.pi*512*tt))*np.exp(-tt*7)+0.3*lp(noise(d),8)*np.exp(-tt*40)
# music: low drone + fan hum, tension grows after the knocks
fan=0.12*np.sin(2*np.pi*95*t)*(0.7+0.3*np.sin(2*np.pi*7*t))
drone=(0.25*np.sin(2*np.pi*43*t)+0.12*np.sin(2*np.pi*64.5*t+np.sin(2*np.pi*0.1*t)))*(0.6+0.4*np.clip((t-S[1])/8,0,1))
pad=sum(np.sin(2*np.pi*f*t) for f in [146.8,174.6,220.0])*0.04*(t>A["k1"])
hook=(0.3*np.sin(2*np.pi*41*t)+0.15*np.sin(2*np.pi*55*t))*(t<S[1])
mus=fan+drone+pad+hook
fx=np.zeros(N)
def put(s,a,g=1):
    i=int(s*SR)
    if i<0 or i>=N: return
    a=a[:N-i]; fx[i:i+len(a)]+=a*g
put(0.02,thud(1.0,40)*1.4); put(0.05,clang(),0.8)
for k in ("k1","k2","k3"): put(A[k],clang(),1.0); put(A[k],thud(0.4,50),1.1)
put(A["k4"],clang(),0.8); put(A["k5"]+0.1,clang(),0.9); put(A["k5"]+0.35,clang(),0.9)
sf.write("music.wav",mus.astype(np.float32),SR); sf.write("sfx.wav",fx.astype(np.float32),SR)
def grms(x):
    w=int(0.4*SR); b=x[:len(x)//w*w].reshape(-1,w); r=np.sqrt((b**2).mean(1)); r=r[r>0.1*r.max()]; return np.sqrt((r**2).mean())
vr=grms(v); mus*=0.5*vr/grms(mus); fx*=0.5*vr/grms(fx); pk=0.7*np.abs(v).max()
if np.abs(fx).max()>pk: fx*=pk/np.abs(fx).max()
mix=v+mus+fx; sf.write("mix.wav",(mix/np.abs(mix).max()*0.89).astype(np.float32),SR)

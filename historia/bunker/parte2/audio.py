import numpy as np, soundfile as sf, json
A=json.load(open("work/anchors.json")); S=A["S"]
SR=48000; v,_=sf.read("voice.wav"); N=len(v); t=np.arange(N)/SR; rng=np.random.default_rng(101)
def noise(d): return rng.standard_normal(int(d*SR))
def lp(x,k): return np.convolve(x,np.ones(k)/k,"same")
def thud(d=0.3,f=60):
    tt=np.arange(int(d*SR))/SR; return np.sin(2*np.pi*f*tt)*np.exp(-tt*14)+0.4*lp(noise(d),25)*np.exp(-tt*25)
def clang(d=0.7):
    tt=np.arange(int(d*SR))/SR; return (np.sin(2*np.pi*180*tt)+0.6*np.sin(2*np.pi*317*tt)+0.4*np.sin(2*np.pi*512*tt))*np.exp(-tt*7)+0.3*lp(noise(d),8)*np.exp(-tt*40)
# music: low drone + fan hum; silence-tension after lights go off, pad from the smile on
fan=0.12*np.sin(2*np.pi*95*t)*(0.7+0.3*np.sin(2*np.pi*7*t))
drone=(0.25*np.sin(2*np.pi*43*t)+0.12*np.sin(2*np.pi*64.5*t+np.sin(2*np.pi*0.1*t)))*(0.6+0.4*np.clip((t-S[1])/8,0,1))
pad=sum(np.sin(2*np.pi*f*t) for f in [146.8,155.6,220.0])*0.04*(t>A["smile"])
hook=(0.3*np.sin(2*np.pi*41*t)+0.15*np.sin(2*np.pi*55*t))*(t<S[1])
mus=fan+drone+pad+hook
fx=np.zeros(N)
def put(s,a,g=1):
    i=int(s*SR)
    if i<0 or i>=N: return
    a=a[:N-i]; fx[i:i+len(a)]+=a*g
def static(d=0.5):
    tt=np.arange(int(d*SR))/SR; return (noise(d)-lp(noise(d),12))*0.35*np.exp(-tt*4)
def tick(): 
    tt=np.arange(int(0.09*SR))/SR; return (np.sin(2*np.pi*1400*tt)+0.6*noise(0.09))*np.exp(-tt*60)
put(0.02,thud(1.0,40)*1.4); put(0.05,static(0.7),1.0)
put(A["off"],tick(),0.9); put(A["k1"],clang(),1.0); put(A["k1"]+0.35,clang(),0.9)
put(A["smile"],thud(0.9,36),1.0); put(A["name"]-0.05,static(0.6),0.9); put(A["name"],thud(0.8,40),1.1)
put(S[8]-0.05,static(0.35),0.7); put(A["key"],clang(0.35),0.4)
put(A["clic"],tick(),1.3); put(A["clic"]+0.15,thud(0.3,70),0.8)
for j in range(30):
    s=A["spin"]+j*0.22
    put(s,tick(),0.55); put(s,clang(0.2),0.25)
sf.write("music.wav",mus.astype(np.float32),SR); sf.write("sfx.wav",fx.astype(np.float32),SR)
def grms(x):
    w=int(0.4*SR); b=x[:len(x)//w*w].reshape(-1,w); r=np.sqrt((b**2).mean(1)); r=r[r>0.1*r.max()]; return np.sqrt((r**2).mean())
vr=grms(v); mus*=0.5*vr/grms(mus); fx*=0.5*vr/grms(fx); pk=0.7*np.abs(v).max()
if np.abs(fx).max()>pk: fx*=pk/np.abs(fx).max()
mix=v+mus+fx; sf.write("mix.wav",(mix/np.abs(mix).max()*0.89).astype(np.float32),SR)

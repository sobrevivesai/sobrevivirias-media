import numpy as np, soundfile as sf, json
A=json.load(open("work/anchors.json")); S=A["S"]
SR=48000; v,_=sf.read("voice.wav"); N=len(v); t=np.arange(N)/SR; rng=np.random.default_rng(101)
def noise(d): return rng.standard_normal(int(d*SR))
def lp(x,k): return np.convolve(x,np.ones(k)/k,"same")
def thud(d=0.3,f=60):
    tt=np.arange(int(d*SR))/SR; return np.sin(2*np.pi*f*tt)*np.exp(-tt*14)+0.4*lp(noise(d),25)*np.exp(-tt*25)
def clang(d=0.7):
    tt=np.arange(int(d*SR))/SR; return (np.sin(2*np.pi*180*tt)+0.6*np.sin(2*np.pi*317*tt)+0.4*np.sin(2*np.pi*512*tt))*np.exp(-tt*7)+0.3*lp(noise(d),8)*np.exp(-tt*40)
# music: drone + fan hum; pad desde la sonrisa; pulso creciente con la barra
fan=0.12*np.sin(2*np.pi*95*t)*(0.7+0.3*np.sin(2*np.pi*7*t))
drone=(0.25*np.sin(2*np.pi*43*t)+0.12*np.sin(2*np.pi*64.5*t+np.sin(2*np.pi*0.1*t)))*(0.6+0.4*np.clip((t-S[1])/8,0,1))
pad=sum(np.sin(2*np.pi*f*t) for f in [146.8,155.6,220.0])*0.04*(t>A["smile"])
pulse=0.35*np.sin(2*np.pi*55*t)*np.exp(-((t*2.2)%1)*5)*(t>S[9])
hook=(0.3*np.sin(2*np.pi*41*t)+0.15*np.sin(2*np.pi*55*t))*(t<S[1])
mus=fan+drone+pad+pulse+hook
fx=np.zeros(N)
def put(s,a,g=1):
    i=int(s*SR)
    if i<0 or i>=N: return
    a=a[:N-i]; fx[i:i+len(a)]+=a*g
def static(d=0.5):
    tt=np.arange(int(d*SR))/SR; return (noise(d)-lp(noise(d),12))*0.35*np.exp(-tt*4)
def tick(): 
    tt=np.arange(int(0.09*SR))/SR; return (np.sin(2*np.pi*1400*tt)+0.6*noise(0.09))*np.exp(-tt*60)
def creak(d=1.2,f=300):
    tt=np.arange(int(d*SR))/SR; ph=2*np.pi*np.cumsum(f*(1+0.25*np.sin(2*np.pi*9*tt))*(1-0.3*tt/d))/SR
    return (np.sign(np.sin(ph))*0.25+0.5*lp(noise(d),6))*np.sin(np.pi*tt/d)
put(0.02,thud(1.0,40)*1.4); put(0.05,creak(1.8,260),0.9); put(0.9,clang(),0.7)
put(S[3]+0.2,creak(0.8,420),0.35); put(A["bar"],clang(0.6),0.8)
put(A["hit"],clang(),1.2); put(A["hit"],thud(0.4,60),1.0)
put(A["smile"],thud(0.9,36),1.0); put(S[7]-0.05,static(0.5),0.8); put(A["point"],thud(0.7,45),0.9)
put(A["gone"],static(0.6),0.9)
for k in range(3): put(A["onyou"]+k*0.28,clang(),0.9); put(A["onyou"]+k*0.28,thud(0.35,55),1.0)
put(A["turn"],creak(1.0,380),0.8); put(A["bend"],creak(1.8,220),1.2); put(A["bend"]+0.2,clang(),0.8)
put(S[11]-0.05,static(0.45),0.8)
sf.write("music.wav",mus.astype(np.float32),SR); sf.write("sfx.wav",fx.astype(np.float32),SR)
def grms(x):
    w=int(0.4*SR); b=x[:len(x)//w*w].reshape(-1,w); r=np.sqrt((b**2).mean(1)); r=r[r>0.1*r.max()]; return np.sqrt((r**2).mean())
vr=grms(v); mus*=0.5*vr/grms(mus); fx*=0.5*vr/grms(fx); pk=0.7*np.abs(v).max()
if np.abs(fx).max()>pk: fx*=pk/np.abs(fx).max()
mix=v+mus+fx; sf.write("mix.wav",(mix/np.abs(mix).max()*0.89).astype(np.float32),SR)

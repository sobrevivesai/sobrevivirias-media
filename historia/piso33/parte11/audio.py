import numpy as np, soundfile as sf, json
A=json.load(open("work/anchors.json")); S=A["S"]
SR=48000; v,_=sf.read("voice.wav"); N=len(v); t=np.arange(N)/SR; rng=np.random.default_rng(5)
def env(a,r,n): e=np.ones(n); a=int(a*SR); r=int(r*SR); e[:a]=np.linspace(0,1,a) if a else 1; e[-r:]*=np.linspace(1,0,r); return e
def noise(d): return rng.standard_normal(int(d*SR))
def lp(x,k): return np.convolve(x,np.ones(k)/k,"same")
# music: low drone + slow pulse, grows toward the eyes
mus=(0.35*np.sin(2*np.pi*41*t)+0.2*np.sin(2*np.pi*61.5*t)+0.06*np.sin(2*np.pi*246.9*t+0.3*np.sin(2*np.pi*0.2*t)))*(1+0.3*np.sin(2*np.pi*0.4*t))
mus*=np.clip(t/1.5,0,1)*(0.6+0.8*np.clip((t-A["eyes"]+2)/6,0,1))
for s in np.arange(0.5,N/SR-0.3,0.95):
    i=int(s*SR); n=int(0.12*SR); tt=np.arange(n)/SR
    if i+n<N: mus[i:i+n]+=0.5*np.sin(2*np.pi*50*tt)*np.exp(-tt*30)
fx=np.zeros(N)
def put(s,a,g=1):
    i=int(s*SR); a=a[:max(0,N-i)]; fx[i:i+len(a)]+=a*g
def thud(d=0.25,f=70):
    tt=np.arange(int(d*SR))/SR; return (np.sin(2*np.pi*f*tt)*np.exp(-tt*18)+0.4*lp(noise(d),30)*np.exp(-tt*30))
def creak(d,f0):
    tt=np.arange(int(d*SR))/SR; f=f0+30*np.sin(2*np.pi*3*tt); return np.sign(np.sin(2*np.pi*np.cumsum(f)/SR))*0.15*np.exp(-tt*2)*lp(np.abs(noise(d)),40)*3
def sting(d=2.0):
    tt=np.arange(int(d*SR))/SR; return (np.sin(2*np.pi*38*tt)+0.5*np.sin(2*np.pi*57*tt)+0.3*lp(noise(d),60))*np.exp(-tt*1.6)
def scratch(d=0.35):
    return lp(noise(d),3)*np.abs(np.sin(2*np.pi*14*np.arange(int(d*SR))/SR))*0.5*env(0.02,0.15,int(d*SR))
# alarm in the cage room
for s in np.arange(0.2,S[3],1.0):
    n=int(0.45*SR); tt=np.arange(n)/SR; put(s,np.sin(2*np.pi*(700+250*tt/0.45)*tt)*0.12*env(0.02,0.1,n))
put(A["boost"],thud(0.3,60),0.9)
put(A["open"]-0.1,creak(1.2,260),0.9)
for s in np.arange(S[3]+0.3,S[6]-0.2,0.9): put(s,thud(0.12,150),0.3); put(s+0.45,thud(0.12,130),0.25)  # crouched steps
put(S[3],lp(noise(S[4]-S[3]),120)*0.25)
put(A["scratch"],scratch(),1.0)
x=A["scr8"]
while x<A["eyes"]: put(x,scratch(0.3),0.9); x+=max(0.45,1.1-0.12*(x-A["scr8"]))
put(A["light"]-0.1,thud(0.08,900),0.5)
put(A["eyes"]-0.05,sting(),0.9)
x=A["breathe"]
while x<S[13]: put(x,lp(noise(0.7),20)*0.5*env(0.25,0.3,int(0.7*SR)),0.9); x+=1.0
put(A["lookL"]-0.1,lp(noise(0.5),40)*0.3*env(0.1,0.3,int(0.5*SR)))
sf.write("music.wav",mus.astype(np.float32),SR); sf.write("sfx.wav",fx.astype(np.float32),SR)
def grms(x):
    w=int(0.4*SR); b=x[:len(x)//w*w].reshape(-1,w); r=np.sqrt((b**2).mean(1)); r=r[r>0.1*r.max()]; return np.sqrt((r**2).mean())
vr=grms(v); mus*=0.5*vr/grms(mus); fx*=0.5*vr/grms(fx); pk=0.7*np.abs(v).max()
if np.abs(fx).max()>pk: fx*=pk/np.abs(fx).max()
mix=v+mus+fx; mix=mix/np.abs(mix).max()*0.89
sf.write("mix.wav",mix.astype(np.float32),SR)

#!/bin/bash
# Uso: bash engine3d/make.sh historia/piso33/parte10 src/ep/piso33-p10.ts [stills|full]
# La carpeta de la parte tiene: script.json (frases), voices.json, episode.json. Salida: <carpeta>/out.mp4
set -e; D=$(cd "$(dirname "$0")" && pwd); P=$(cd "$1" && pwd); EP=$2; MODE=${3:-full}
cd "$P"; mkdir -p work
[ -f voice.wav ] && [ work/phrases.json -nt script.json ] || python3 -I "$D/py/voice.py"
AN="$D/py/anchors.py"; [ -f anchors.py ] && AN="$P/anchors.py"; python3 -I "$AN" "$D/web/tim.js"
cd "$D" && npx esbuild "$EP" --bundle --outfile=web/ep.js --format=iife --log-level=error
N=$(python3 -c "import json;print(json.load(open('$P/work/anchors.json'))['frames'])")
if [ "$MODE" = stills ]; then
  F=$(python3 -c "import json;S=json.load(open('$P/work/anchors.json'))['S'];S[-1]=$N/30;print(','.join(str(round((S[i]+S[i+1])/2*30)) for i in range(len(S)-1)))")
  rm -rf "$P/stills"; QS="ms=0&sm=1024&aa=smaa" node rtest.mjs 540 ep.html $F "$P/stills" | grep -E "ERR|rror" || true
  python3 -c "
from PIL import Image;import glob
fs=sorted(glob.glob('$P/stills/f*.jpg'));w,h=270,480;n=8
s=Image.new('RGB',(w*n,h*((len(fs)+n-1)//n)))
[s.paste(Image.open(f).resize((w,h)),((i%n)*w,(i//n)*h)) for i,f in enumerate(fs)];s.save('$P/stills/sheet.jpg',quality=88)"
  echo "hoja: $P/stills/sheet.jpg"; exit 0; fi
W=810 QS="ms=0&sm=1024&aa=smaa" node render.mjs 0 $((N-1)) "$P/frames"
cd "$P" && AU="$D/py/audio.py"; [ -f "$P/audio.py" ] && AU="$P/audio.py"; python3 -I "$AU" && EP=episode.json python3 -I "$D/py/overlay.py" frames ofr
ffmpeg -loglevel error -y -framerate 30 -i ofr/f%04d.jpg -i mix.wav -c:v libx264 -preset veryfast -crf 18 -pix_fmt yuv420p -c:a aac -b:a 192k -af loudnorm=I=-14:TP=-1 -shortest out.mp4
ffprobe -v error -show_entries format=duration -of csv=p=0 out.mp4

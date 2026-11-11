#!/usr/bin/env bash
# Instala todo lo necesario para renderizar en un entorno nuevo (solo usa npm y PyPI).
set -euo pipefail
TTS_DIR="${TTS_DIR:-/home/claude/tts}"
mkdir -p "$TTS_DIR" && cd "$TTS_DIR"
which ffmpeg >/dev/null || { echo "Falta ffmpeg"; exit 1; }
pip install -q --break-system-packages kokoro-onnx fonttools pillow numpy soundfile >/dev/null 2>&1 || pip install -q kokoro-onnx fonttools pillow numpy
if [ ! -f kokoro.onnx ]; then
  mkdir -p dl && cd dl
  for p in kokoro-fp32a-shards kokoro-fp32b-shards kokoro-fp32c-shards kokoro-js; do npm pack -q "$p" >/dev/null 2>&1; done
  for f in *.tgz; do mkdir -p "x_${f%.tgz}"; tar xzf "$f" -C "x_${f%.tgz}"; done
  for i in $(seq 0 18); do cat x_kokoro-fp32*/package/kokoro-fp32.part$i.bin; done > "$TTS_DIR/kokoro.onnx"
  python3 -I - "$TTS_DIR" <<'EOF'
import sys, glob, numpy as np
out = sys.argv[1]; d = {}
for v in ["em_alex", "ef_dora", "em_santa"]:
    f = glob.glob(f"x_kokoro-js-*/package/voices/{v}.bin")[0]
    d[v] = np.fromfile(f, dtype=np.float32).reshape(-1, 1, 256)
np.savez(out + "/voices.npz", **d)
EOF
  mv "$TTS_DIR/voices.npz" "$TTS_DIR/voices.bin"
  cd "$TTS_DIR" && rm -rf dl
fi
ls -la "$TTS_DIR"
echo "setup ok"

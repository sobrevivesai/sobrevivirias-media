#!/bin/bash
# Instala el motor 3D (three.js + postprocessing + esbuild), Playwright/Chrome y las voces Piper (gratis, desde GitHub releases).
set -e; D=$(cd "$(dirname "$0")" && pwd); cd "$D"
[ -d node_modules/three ] || npm i --silent
G=$(npm root -g); [ -d "$G/playwright" ] || npm i -g playwright >/dev/null
[ -e node_modules/playwright ] || ln -s "$G/playwright" node_modules/playwright
python3 -c "import piper" 2>/dev/null || pip install --break-system-packages -q piper-tts soundfile numpy pillow
P=${PIPER_DIR:-/home/claude/piper}; mkdir -p "$P"
for m in es_MX-claude-high es_MX-ald-medium; do
  [ -f "$P/vits-piper-$m/$m.onnx" ] || (cd "$P" && curl -sL -o $m.tar.bz2 https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-piper-$m.tar.bz2 && tar xjf $m.tar.bz2 && rm $m.tar.bz2)
done
CH=$(ls /usr/bin/google-chrome 2>/dev/null || true); [ -n "$CH" ] || npx playwright install chromium
echo "engine3d listo"

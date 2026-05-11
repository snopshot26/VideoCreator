#!/usr/bin/env bash
set -e

mkdir -p /workspace/logs 2>/dev/null || true

if [ -d /workspace ]; then
  export COMFYUI_DIR="${COMFYUI_DIR:-/workspace/ComfyUI}"
else
  SCRIPT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
  export COMFYUI_DIR="${COMFYUI_DIR:-$SCRIPT_ROOT/ComfyUI}"
fi

echo "ComfyUI target: $COMFYUI_DIR"

if [ ! -d "$COMFYUI_DIR" ]; then
  git clone https://github.com/comfyanonymous/ComfyUI.git "$COMFYUI_DIR"
fi

cd "$COMFYUI_DIR"

if [ ! -d venv ]; then
  python3 -m venv venv
fi
source venv/bin/activate

pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

mkdir -p \
  models/checkpoints \
  models/diffusion_models \
  models/text_encoders \
  models/vae \
  models/clip_vision \
  models/upscale_models \
  models/controlnet \
  models/loras \
  output \
  input

echo "ComfyUI installed/updated at $COMFYUI_DIR"

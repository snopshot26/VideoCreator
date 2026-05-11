#!/usr/bin/env bash
set -e

if [ -d /workspace ]; then
  export COMFYUI_DIR="${COMFYUI_DIR:-/workspace/ComfyUI}"
else
  SCRIPT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
  export COMFYUI_DIR="${COMFYUI_DIR:-$SCRIPT_ROOT/ComfyUI}"
fi

export COMFYUI_PORT="${COMFYUI_PORT:-8188}"

cd "$COMFYUI_DIR"
# shellcheck source=/dev/null
source venv/bin/activate || source .venv/bin/activate || true
exec python main.py --listen 0.0.0.0 --port "$COMFYUI_PORT"

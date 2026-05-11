#!/usr/bin/env bash
set -e

export COMFYUI_PORT="${COMFYUI_PORT:-8188}"
if curl -fsS -m 5 "http://127.0.0.1:${COMFYUI_PORT}/system_stats" >/dev/null; then
  echo "ComfyUI is reachable at http://127.0.0.1:${COMFYUI_PORT}"
else
  echo "ComfyUI not reachable at http://127.0.0.1:${COMFYUI_PORT}" >&2
  exit 1
fi

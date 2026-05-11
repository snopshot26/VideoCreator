#!/usr/bin/env bash
set +e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
export APP_PORT="${APP_PORT:-7860}"
export COMFYUI_PORT="${COMFYUI_PORT:-8188}"
export COMFYUI_PORT_SECOND="${COMFYUI_PORT_SECOND:-8189}"

if [ -d /workspace/logs ]; then
  LOG_DIR="${LOG_DIR:-/workspace/logs}"
else
  LOG_DIR="${LOG_DIR:-$PROJECT_DIR/logs}"
fi

multi_on=false
case "${COMFYUI_MULTI_GPU:-false}" in
  1|true|TRUE|yes|Yes|YES) multi_on=true ;;
esac

GPU_COUNT=0
if command -v nvidia-smi >/dev/null 2>&1; then
  GPU_COUNT=$(nvidia-smi -L 2>/dev/null | grep -c '^GPU' || true)
fi

echo "=== nvidia-smi -L (GPU count lines) ==="
nvidia-smi -L 2>/dev/null || echo "(nvidia-smi not available)"
echo "Detected GPU line count: ${GPU_COUNT:-0}"

echo ""
echo "=== COMFYUI_MULTI_GPU ==="
echo "COMFYUI_MULTI_GPU=${COMFYUI_MULTI_GPU:-false} (effective multi flag: $multi_on)"

echo ""
echo "=== Disk ==="
df -h /workspace 2>/dev/null || df -h "$PROJECT_DIR" 2>/dev/null || true

echo ""
echo "=== PID files ($LOG_DIR) ==="
ls -la "$LOG_DIR"/*.pid 2>/dev/null || echo "(no pid files)"

echo ""
echo "=== Processes (ComfyUI / webui) ==="
ps aux | grep -E "ComfyUI|webui.py|uvicorn" | grep -v grep || true

echo ""
echo "=== Ports ${APP_PORT} / ${COMFYUI_PORT} / ${COMFYUI_PORT_SECOND} ==="
command -v ss >/dev/null && ss -tlnp 2>/dev/null | grep -E ":${APP_PORT}|:${COMFYUI_PORT}|:${COMFYUI_PORT_SECOND}" || true

echo ""
echo "=== ComfyUI :${COMFYUI_PORT} /system_stats ==="
curl -sS -m 3 "http://127.0.0.1:${COMFYUI_PORT}/system_stats" | head -c 200 || echo "(no response)"
echo ""
echo "=== ComfyUI :${COMFYUI_PORT_SECOND} /system_stats ==="
curl -sS -m 3 "http://127.0.0.1:${COMFYUI_PORT_SECOND}/system_stats" | head -c 200 || echo "(no response)"

echo ""
echo "=== App /health ==="
curl -sS -m 3 "http://127.0.0.1:${APP_PORT}/health" || echo "(no response)"

echo ""
echo "=== Recent logs (last 25 lines each) ==="
for f in comfyui.log comfyui_gpu0.log comfyui_gpu1.log ai-shorts-factory.log; do
  if [ -f "$LOG_DIR/$f" ]; then
    echo "--- $f ---"
    tail -n 25 "$LOG_DIR/$f"
  fi
done

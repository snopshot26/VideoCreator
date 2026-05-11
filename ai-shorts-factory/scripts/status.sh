#!/usr/bin/env bash
set +e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
export APP_PORT="${APP_PORT:-7860}"
export COMFYUI_PORT="${COMFYUI_PORT:-8188}"

if [ -d /workspace/logs ]; then
  LOG_DIR="${LOG_DIR:-/workspace/logs}"
else
  LOG_DIR="${LOG_DIR:-$PROJECT_DIR/logs}"
fi

echo "=== GPU ==="
nvidia-smi || true

echo ""
echo "=== Disk (workspace or cwd) ==="
df -h /workspace 2>/dev/null || df -h "$PROJECT_DIR" 2>/dev/null || true

echo ""
echo "=== PID files ($LOG_DIR) ==="
ls -la "$LOG_DIR"/*.pid 2>/dev/null || echo "(no pid files)"

echo ""
echo "=== Processes (ComfyUI / webui) ==="
ps aux | grep -E "ComfyUI|webui.py|uvicorn" | grep -v grep || true

echo ""
echo "=== Ports ${APP_PORT} / ${COMFYUI_PORT} ==="
command -v ss >/dev/null && ss -tlnp 2>/dev/null | grep -E ":${APP_PORT}|:${COMFYUI_PORT}" || true

echo ""
echo "=== ComfyUI /system_stats ==="
curl -sS -m 3 "http://127.0.0.1:${COMFYUI_PORT}/system_stats" | head -c 300 || echo "(no response)"

echo ""
echo "=== App /health ==="
curl -sS -m 3 "http://127.0.0.1:${APP_PORT}/health" || echo "(no response)"

echo ""
echo "=== Recent logs (last 40 lines) ==="
tail -n 40 "$LOG_DIR/comfyui.log" 2>/dev/null || echo "(no comfyui.log)"
echo "---"
tail -n 40 "$LOG_DIR/ai-shorts-factory.log" 2>/dev/null || echo "(no ai-shorts-factory.log)"

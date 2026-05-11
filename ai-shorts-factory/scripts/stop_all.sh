#!/usr/bin/env bash
set +e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"

if [ -d /workspace/logs ]; then
  LOG_DIR="${LOG_DIR:-/workspace/logs}"
else
  LOG_DIR="${LOG_DIR:-$PROJECT_DIR/logs}"
fi

stop_pidfile() {
  local f="$1"
  local name="$2"
  if [ -f "$f" ]; then
    pid="$(cat "$f" 2>/dev/null || true)"
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
      echo "Stopping $name (pid $pid)..."
      kill "$pid" 2>/dev/null || true
      sleep 1
      kill -9 "$pid" 2>/dev/null || true
    fi
    rm -f "$f"
  fi
}

stop_pidfile "$LOG_DIR/ai-shorts-factory.pid" "AI Shorts Factory"
stop_pidfile "$LOG_DIR/comfyui.pid" "ComfyUI (single)"
stop_pidfile "$LOG_DIR/comfyui_gpu0.pid" "ComfyUI GPU0"
stop_pidfile "$LOG_DIR/comfyui_gpu1.pid" "ComfyUI GPU1"

if pgrep -f "python app/webui.py" >/dev/null 2>&1; then
  pkill -f "python app/webui.py" 2>/dev/null || true
fi
if pgrep -f "uvicorn.*app.webui:app" >/dev/null 2>&1; then
  pkill -f "uvicorn.*app.webui:app" 2>/dev/null || true
fi
if pgrep -f "ComfyUI.*main.py" >/dev/null 2>&1; then
  pkill -f "ComfyUI.*main.py" 2>/dev/null || true
fi

echo "Stopped AI Shorts Factory and ComfyUI workers (if they were running)."

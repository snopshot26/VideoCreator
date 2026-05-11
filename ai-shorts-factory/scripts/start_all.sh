#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
if [ -d /workspace ]; then
  export COMFYUI_DIR="${COMFYUI_DIR:-/workspace/ComfyUI}"
else
  export COMFYUI_DIR="${COMFYUI_DIR:-$PROJECT_DIR/ComfyUI}"
fi
export APP_PORT="${APP_PORT:-7860}"
export COMFYUI_PORT="${COMFYUI_PORT:-8188}"
export COMFYUI_URL="${COMFYUI_URL:-http://127.0.0.1:${COMFYUI_PORT}}"
export APP_HOST="${APP_HOST:-0.0.0.0}"

# Logs + PID files: prefer /workspace/logs on Vast; else project logs/.
if [ -d /workspace ] && mkdir -p /workspace/logs 2>/dev/null; then
  LOG_DIR="${LOG_DIR:-/workspace/logs}"
else
  LOG_DIR="${LOG_DIR:-$PROJECT_DIR/logs}"
fi
mkdir -p "$LOG_DIR"

COMFYUI_PID_FILE="$LOG_DIR/comfyui.pid"
APP_PID_FILE="$LOG_DIR/ai-shorts-factory.pid"

is_alive() {
  local pid="$1"
  [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null
}

need_comfy=1
if [ -f "$COMFYUI_PID_FILE" ]; then
  old="$(cat "$COMFYUI_PID_FILE" 2>/dev/null || true)"
  if is_alive "$old"; then
    echo "ComfyUI already running (pid $old)."
    need_comfy=0
  else
    rm -f "$COMFYUI_PID_FILE"
  fi
fi

if [ "$need_comfy" = 1 ]; then
  if [ ! -d "$COMFYUI_DIR" ]; then
    echo "ERROR: COMFYUI_DIR not found: $COMFYUI_DIR (run scripts/install_comfyui.sh first)" >&2
    exit 1
  fi
  echo "Starting ComfyUI on port $COMFYUI_PORT..."
  cd "$COMFYUI_DIR"
  # shellcheck source=/dev/null
  source venv/bin/activate
  nohup python main.py --listen 0.0.0.0 --port "$COMFYUI_PORT" >>"$LOG_DIR/comfyui.log" 2>&1 &
  echo $! >"$COMFYUI_PID_FILE"
fi

sleep 3

if [ -f "$APP_PID_FILE" ]; then
  old="$(cat "$APP_PID_FILE" 2>/dev/null || true)"
  if is_alive "$old"; then
    echo "AI Shorts Factory already running (pid $old)."
    exit 0
  fi
  rm -f "$APP_PID_FILE"
fi

if [ ! -d "$PROJECT_DIR/.venv" ]; then
  echo "ERROR: Project venv missing at $PROJECT_DIR/.venv" >&2
  exit 1
fi

echo "Starting AI Shorts Factory on port $APP_PORT..."
cd "$PROJECT_DIR"
# shellcheck source=/dev/null
source .venv/bin/activate
export COMFYUI_URL
export VIDEO_BACKEND="${VIDEO_BACKEND:-placeholder}"
nohup python app/webui.py --host "$APP_HOST" --port "$APP_PORT" >>"$LOG_DIR/ai-shorts-factory.log" 2>&1 &
echo $! >"$APP_PID_FILE"

sleep 2

echo "Started."
echo "AI Shorts Factory: http://127.0.0.1:${APP_PORT}/ui"
echo "ComfyUI: http://127.0.0.1:${COMFYUI_PORT}"
echo "Health: http://127.0.0.1:${APP_PORT}/health"
echo "Logs + PID files: $LOG_DIR"
echo "Use Vast.ai IP Port Info for public URLs."

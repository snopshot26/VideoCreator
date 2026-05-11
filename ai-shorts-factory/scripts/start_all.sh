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
export COMFYUI_PORT_SECOND="${COMFYUI_PORT_SECOND:-8189}"
export COMFYUI_URL="${COMFYUI_URL:-http://127.0.0.1:${COMFYUI_PORT}}"
export APP_HOST="${APP_HOST:-0.0.0.0}"

if [ -d /workspace ] && mkdir -p /workspace/logs 2>/dev/null; then
  LOG_DIR="${LOG_DIR:-/workspace/logs}"
else
  LOG_DIR="${LOG_DIR:-$PROJECT_DIR/logs}"
fi
mkdir -p "$LOG_DIR"

COMFYUI_PID_FILE="$LOG_DIR/comfyui.pid"
COMFYUI_PID_GPU0="$LOG_DIR/comfyui_gpu0.pid"
COMFYUI_PID_GPU1="$LOG_DIR/comfyui_gpu1.pid"
APP_PID_FILE="$LOG_DIR/ai-shorts-factory.pid"

is_alive() {
  local pid="$1"
  [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null
}

GPU_COUNT=0
if command -v nvidia-smi >/dev/null 2>&1; then
  GPU_COUNT=$(nvidia-smi -L 2>/dev/null | grep -c '^GPU' || true)
fi

multi_on=false
case "${COMFYUI_MULTI_GPU:-false}" in
  1|true|TRUE|yes|Yes|YES) multi_on=true ;;
esac

if [ "$multi_on" = true ] && [ "${GPU_COUNT:-0}" -lt 2 ]; then
  echo "WARN: COMFYUI_MULTI_GPU=true but fewer than 2 GPUs detected (nvidia-smi count=$GPU_COUNT). Using single ComfyUI." >&2
  multi_on=false
fi

start_comfy_single() {
  local need=1
  if [ -f "$COMFYUI_PID_FILE" ]; then
    local old
    old="$(cat "$COMFYUI_PID_FILE" 2>/dev/null || true)"
    if is_alive "$old"; then
      echo "ComfyUI already running (pid $old)."
      need=0
    else
      rm -f "$COMFYUI_PID_FILE"
    fi
  fi
  if [ "$need" = 1 ]; then
    if [ ! -d "$COMFYUI_DIR" ]; then
      echo "ERROR: COMFYUI_DIR not found: $COMFYUI_DIR" >&2
      exit 1
    fi
    echo "Starting ComfyUI on port $COMFYUI_PORT..."
    cd "$COMFYUI_DIR"
    # shellcheck source=/dev/null
    source venv/bin/activate
    nohup python main.py --listen 0.0.0.0 --port "$COMFYUI_PORT" >>"$LOG_DIR/comfyui.log" 2>&1 &
    echo $! >"$COMFYUI_PID_FILE"
  fi
  unset COMFYUI_URLS 2>/dev/null || true
  export COMFYUI_URL="http://127.0.0.1:${COMFYUI_PORT}"
}

start_comfy_worker() {
  local gpu_id="$1" port="$2" logf="$3" pidf="$4"
  local need=1
  if [ -f "$pidf" ]; then
    local old
    old="$(cat "$pidf" 2>/dev/null || true)"
    if is_alive "$old"; then
      echo "ComfyUI GPU${gpu_id} already running (pid $old) on port ${port}."
      need=0
    else
      rm -f "$pidf"
    fi
  fi
  if [ "$need" = 1 ]; then
    if [ ! -d "$COMFYUI_DIR" ]; then
      echo "ERROR: COMFYUI_DIR not found: $COMFYUI_DIR" >&2
      exit 1
    fi
    echo "Starting ComfyUI worker GPU${gpu_id} on port ${port} (CUDA_VISIBLE_DEVICES=${gpu_id})..."
    cd "$COMFYUI_DIR"
    # shellcheck source=/dev/null
    source venv/bin/activate
    CUDA_VISIBLE_DEVICES="$gpu_id" nohup python main.py --listen 0.0.0.0 --port "$port" >>"$LOG_DIR/$logf" 2>&1 &
    echo $! >"$pidf"
  fi
}

if [ "$multi_on" = true ]; then
  rm -f "$COMFYUI_PID_FILE" 2>/dev/null || true
  start_comfy_worker 0 "$COMFYUI_PORT" "comfyui_gpu0.log" "$COMFYUI_PID_GPU0"
  start_comfy_worker 1 "$COMFYUI_PORT_SECOND" "comfyui_gpu1.log" "$COMFYUI_PID_GPU1"
  export COMFYUI_URLS="http://127.0.0.1:${COMFYUI_PORT},http://127.0.0.1:${COMFYUI_PORT_SECOND}"
  export COMFYUI_WORKERS="${COMFYUI_WORKERS:-2}"
  unset COMFYUI_URL 2>/dev/null || true
else
  rm -f "$COMFYUI_PID_GPU0" "$COMFYUI_PID_GPU1" 2>/dev/null || true
  start_comfy_single
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
export VIDEO_BACKEND="${VIDEO_BACKEND:-placeholder}"
if [ "$multi_on" = true ]; then
  export COMFYUI_URLS
  export COMFYUI_WORKERS
else
  export COMFYUI_URL
fi
nohup python app/webui.py --host "$APP_HOST" --port "$APP_PORT" >>"$LOG_DIR/ai-shorts-factory.log" 2>&1 &
echo $! >"$APP_PID_FILE"

sleep 2

echo "Started."
echo "AI Shorts Factory: http://127.0.0.1:${APP_PORT}/ui"
if [ "$multi_on" = true ]; then
  echo "ComfyUI workers: http://127.0.0.1:${COMFYUI_PORT} (GPU0), http://127.0.0.1:${COMFYUI_PORT_SECOND} (GPU1)"
  echo "COMFYUI_URLS=$COMFYUI_URLS"
else
  echo "ComfyUI: http://127.0.0.1:${COMFYUI_PORT}"
fi
echo "Health: http://127.0.0.1:${APP_PORT}/health"
echo "Logs + PID files: $LOG_DIR"
echo "Note: Multi-GPU runs separate ComfyUI processes in parallel; VRAM is NOT pooled for one model."

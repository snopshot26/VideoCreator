#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"

if [ -d /workspace/logs ]; then
  LOG_DIR="${LOG_DIR:-/workspace/logs}"
else
  LOG_DIR="${LOG_DIR:-$PROJECT_DIR/logs}"
fi
mkdir -p "$LOG_DIR"

files=()
for f in setup_vast.log comfyui.log comfyui_gpu0.log comfyui_gpu1.log ai-shorts-factory.log; do
  if [ -f "$LOG_DIR/$f" ]; then
    files+=("$LOG_DIR/$f")
  fi
done

if [ ${#files[@]} -eq 0 ]; then
  echo "No log files found in $LOG_DIR yet."
  exit 0
fi

echo "Tailing: ${files[*]}"
tail -f "${files[@]}"

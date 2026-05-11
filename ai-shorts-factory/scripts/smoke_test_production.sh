#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
cd "$PROJECT_DIR"

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "FFmpeg is missing. On Ubuntu run: sudo apt install -y ffmpeg" >&2
  exit 1
fi
if ! command -v ffprobe >/dev/null 2>&1; then
  echo "ffprobe is missing (install the ffmpeg package). On Ubuntu run: sudo apt install -y ffmpeg" >&2
  exit 1
fi

if [ ! -d .venv ]; then
  echo "ERROR: .venv not found. Run: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt" >&2
  exit 1
fi

# shellcheck source=/dev/null
source .venv/bin/activate

export VIDEO_BACKEND=placeholder

exec python scripts/smoke_test_production.py

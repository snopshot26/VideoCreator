#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."
source .venv/bin/activate
export APP_PORT="${APP_PORT:-7860}"
export APP_HOST="${APP_HOST:-0.0.0.0}"
python app/webui.py --host "$APP_HOST" --port "$APP_PORT"

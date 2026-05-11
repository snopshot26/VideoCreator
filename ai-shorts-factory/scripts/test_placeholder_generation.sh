#!/usr/bin/env bash
set -e

export APP_PORT="${APP_PORT:-7860}"
URL="http://127.0.0.1:${APP_PORT}/health"

echo "Waiting for app at $URL ..."
for i in $(seq 1 60); do
  if curl -fsS -m 2 "$URL" >/dev/null 2>&1; then
    echo "App is up."
    break
  fi
  sleep 1
  if [ "$i" -eq 60 ]; then
    echo "Timeout waiting for app. Start with: bash scripts/start_all.sh" >&2
    exit 1
  fi
done

RESP=$(curl -sS -X POST "http://127.0.0.1:${APP_PORT}/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "idea": "A 15-second fake commercial for a programmer energy drink, funny meme style, vertical video.",
    "duration_seconds": 15,
    "style": "funny meme",
    "language": "en",
    "voice_mode": "narrator",
    "music": "light background"
  }')

echo "$RESP"
JOB_ID=$(echo "$RESP" | python3 -c "import sys, json; print(json.load(sys.stdin).get('job_id',''))" 2>/dev/null || true)
if [ -n "$JOB_ID" ]; then
  echo "Job ID: $JOB_ID — check GET /jobs/$JOB_ID or the Web UI output folder."
fi

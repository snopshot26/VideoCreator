#!/usr/bin/env bash
set -e

echo "=== nvidia-smi -L ==="
nvidia-smi -L

echo ""
echo "=== ComfyUI :8188 /system_stats ==="
curl -fsS -m 5 "http://127.0.0.1:8188/system_stats" >/dev/null
echo "OK: 8188"

echo ""
echo "=== ComfyUI :8189 /system_stats ==="
curl -fsS -m 5 "http://127.0.0.1:8189/system_stats" >/dev/null
echo "OK: 8189"

echo ""
echo "PASSED: both ComfyUI worker ports respond."

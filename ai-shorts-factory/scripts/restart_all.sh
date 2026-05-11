#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

bash "$SCRIPT_DIR/stop_all.sh"
sleep 2
bash "$SCRIPT_DIR/start_all.sh"

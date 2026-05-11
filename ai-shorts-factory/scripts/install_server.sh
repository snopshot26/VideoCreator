#!/usr/bin/env bash
set -e

sudo apt update
sudo apt install -y python3 python3-venv python3-pip git ffmpeg curl wget

python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

chmod +x scripts/*.sh 2>/dev/null || true

echo "Installation complete."
echo "Run: bash scripts/start_app.sh"
echo "On Linux/macOS, if scripts are not executable: chmod +x scripts/*.sh"

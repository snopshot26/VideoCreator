#!/usr/bin/env bash
set -e

mkdir -p /workspace/logs
LOG_FILE="/workspace/logs/setup_vast.log"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "Starting Vast.ai setup at $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "NOTE: This script is non-destructive: it does not rm -rf ComfyUI, models, outputs, or your repo."
echo "      It only installs packages, ensures venvs exist, and optionally starts services."

export PROJECT_DIR="${PROJECT_DIR:-/workspace/ai-shorts-factory}"
export COMFYUI_DIR="${COMFYUI_DIR:-/workspace/ComfyUI}"
export APP_PORT="${APP_PORT:-7860}"
export COMFYUI_PORT="${COMFYUI_PORT:-8188}"
export AUTO_START="${AUTO_START:-true}"
export DOWNLOAD_MODELS="${DOWNLOAD_MODELS:-false}"
export VIDEO_BACKEND="${VIDEO_BACKEND:-placeholder}"
export COMFYUI_URL="${COMFYUI_URL:-http://127.0.0.1:${COMFYUI_PORT}}"

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y \
  git wget curl ffmpeg python3 python3-venv python3-pip \
  build-essential tmux nano htop unzip rsync ca-certificates

mkdir -p /workspace/logs /workspace/models_cache

# Clone project when missing (typical Vast on-start provisioning).
if [ ! -d "$PROJECT_DIR" ]; then
  if [ -n "${GITHUB_REPO_URL:-}" ]; then
    git clone "$GITHUB_REPO_URL" "$PROJECT_DIR"
  else
    echo "NOTE: PROJECT_DIR does not exist and GITHUB_REPO_URL is empty."
    echo "If the repo is bind-mounted or copied into $PROJECT_DIR, continue."
  fi
fi

if [ -d "$PROJECT_DIR" ]; then
  cd "$PROJECT_DIR"
  if [ ! -d .venv ]; then
    python3 -m venv .venv
  fi
  # shellcheck source=/dev/null
  source .venv/bin/activate
  pip install --upgrade pip setuptools wheel
  pip install -r requirements.txt
  if [ -f .env.vast.example ]; then
    cp -n .env.vast.example .env || true
  fi
  chmod +x scripts/*.sh 2>/dev/null || true

  bash "$PROJECT_DIR/scripts/install_comfyui.sh"
  bash "$PROJECT_DIR/scripts/install_comfyui_custom_nodes.sh" || true

  if [ "$DOWNLOAD_MODELS" = "true" ]; then
    bash "$PROJECT_DIR/scripts/download_models.sh" || true
  else
    echo "Skipping model download. Set DOWNLOAD_MODELS=true to enable."
  fi

  if [ "$AUTO_START" = "true" ]; then
    bash "$PROJECT_DIR/scripts/start_all.sh"
  fi
else
  echo "ERROR: PROJECT_DIR not found at $PROJECT_DIR — cannot install app."
  exit 1
fi

echo ""
echo "Setup complete."
echo "AI Shorts Factory (internal): http://127.0.0.1:${APP_PORT}/ui"
echo "ComfyUI (internal): http://127.0.0.1:${COMFYUI_PORT}"
echo "On Vast.ai, map public ports to 7860 (app) and 8188 (ComfyUI)."
echo "Full log: $LOG_FILE"

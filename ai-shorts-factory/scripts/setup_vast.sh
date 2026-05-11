#!/usr/bin/env bash
set -e

mkdir -p /workspace/logs
LOG_FILE="/workspace/logs/setup_vast.log"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "Starting Vast.ai setup at $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "NOTE: This script is non-destructive: it does not rm -rf ComfyUI, models, outputs, or your repo."
echo "      It only installs packages, ensures venvs exist, and optionally starts services."

DEFAULT_PROJECT_DIR="/workspace/ai-shorts-factory"
PROJECT_DIR_FROM_USER="${PROJECT_DIR:-}"
if [ -n "$PROJECT_DIR_FROM_USER" ]; then
  export PROJECT_DIR="$PROJECT_DIR_FROM_USER"
else
  export PROJECT_DIR="$DEFAULT_PROJECT_DIR"
fi
export COMFYUI_DIR="${COMFYUI_DIR:-/workspace/ComfyUI}"
export APP_PORT="${APP_PORT:-7860}"
export COMFYUI_PORT="${COMFYUI_PORT:-8188}"
export COMFYUI_MULTI_GPU="${COMFYUI_MULTI_GPU:-false}"
export COMFYUI_WORKERS="${COMFYUI_WORKERS:-1}"
export COMFYUI_URLS="${COMFYUI_URLS:-http://127.0.0.1:${COMFYUI_PORT}}"
export AUTO_START="${AUTO_START:-true}"
export DOWNLOAD_MODELS="${DOWNLOAD_MODELS:-false}"
export VIDEO_BACKEND="${VIDEO_BACKEND:-placeholder}"
export COMFYUI_URL="${COMFYUI_URL:-http://127.0.0.1:${COMFYUI_PORT}}"
export SKIP_GIT_CLONE="${SKIP_GIT_CLONE:-false}"

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y \
  git wget curl ffmpeg python3 python3-venv python3-pip \
  build-essential tmux nano htop unzip rsync ca-certificates

mkdir -p /workspace/logs /workspace/models_cache

# Detect repo root when script runs from an existing project checkout:
# scripts/setup_vast.sh -> parent directory must contain requirements.txt, app/, pipeline/.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DETECTED_REPO_ROOT="$(dirname "$SCRIPT_DIR")"
if [ -z "$PROJECT_DIR_FROM_USER" ] && [ -f "$DETECTED_REPO_ROOT/requirements.txt" ] && [ -d "$DETECTED_REPO_ROOT/app" ] && [ -d "$DETECTED_REPO_ROOT/pipeline" ]; then
  export PROJECT_DIR="$DETECTED_REPO_ROOT"
  echo "Detected existing project repo at: $PROJECT_DIR"
fi

if [ "$SKIP_GIT_CLONE" = "true" ] || [ "$SKIP_GIT_CLONE" = "1" ] || [ "$SKIP_GIT_CLONE" = "yes" ]; then
  if [ ! -d "$PROJECT_DIR" ]; then
    echo "SKIP_GIT_CLONE=true but PROJECT_DIR does not exist."
    exit 1
  fi
elif [ ! -d "$PROJECT_DIR" ]; then
  if [ -n "${GITHUB_REPO_URL:-}" ]; then
    export GIT_TERMINAL_PROMPT=0
    if ! git clone "$GITHUB_REPO_URL" "$PROJECT_DIR"; then
      echo "Git clone failed. If the repository is private, make it public or use a GitHub token. You can also upload/copy the repo manually and rerun with SKIP_GIT_CLONE=true PROJECT_DIR=/path/to/repo."
      exit 1
    fi
  else
    echo "ERROR: PROJECT_DIR does not exist and GITHUB_REPO_URL is empty."
    exit 1
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

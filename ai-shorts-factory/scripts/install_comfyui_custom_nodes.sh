#!/usr/bin/env bash
set -e

if [ -d /workspace ]; then
  export COMFYUI_DIR="${COMFYUI_DIR:-/workspace/ComfyUI}"
else
  SCRIPT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
  export COMFYUI_DIR="${COMFYUI_DIR:-$SCRIPT_ROOT/ComfyUI}"
fi

CUSTOM_NODES_DIR="$COMFYUI_DIR/custom_nodes"
mkdir -p "$CUSTOM_NODES_DIR"
cd "$CUSTOM_NODES_DIR"

clone_or_update() {
  local repo_url="$1"
  local dir_name="$2"

  if [ -d "$dir_name" ]; then
    echo "Updating $dir_name"
    (cd "$dir_name" && git pull || true) || echo "WARN: git pull failed for $dir_name" >&2
  else
    echo "Cloning $dir_name"
    git clone "$repo_url" "$dir_name" || echo "WARN: clone failed for $dir_name" >&2
  fi
}

clone_or_update "https://github.com/ltdrdata/ComfyUI-Manager.git" "ComfyUI-Manager"
clone_or_update "https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git" "ComfyUI-VideoHelperSuite"

echo "Custom nodes installation complete."

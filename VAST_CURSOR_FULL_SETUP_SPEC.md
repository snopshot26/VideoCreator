# Vast.ai Full Auto Setup Specification for Cursor

## 0. Purpose

Modify the existing `ai-shorts-factory` project so it can be deployed on Vast.ai with minimal manual work.

Target flow:

```text
Cursor builds project
→ user pushes project to GitHub
→ user creates Vast.ai template
→ Vast.ai runs setup script automatically
→ ComfyUI starts
→ AI Shorts Factory starts
→ user opens web UI
→ user writes prompt
→ final publish-ready vertical video is generated
```

This file is a build instruction for Cursor. Cursor must create all scripts, config files, docs, and startup logic required for Vast.ai deployment.

---

## 1. Final User Experience

After setup, the user should be able to do this:

```text
1. Rent Vast.ai GPU instance.
2. Use the custom template.
3. Wait until setup finishes.
4. Open the external Vast.ai URL for port 7860.
5. Enter prompt.
6. Click Generate.
7. Download final.mp4 and publish package.
```

The system must generate:

```text
outputs/{job_id}/
  final.mp4
  thumbnail.png
  title.txt
  description.txt
  hashtags.txt
  subtitles.srt
  publish_package.json
  metadata.json
  logs.txt
```

---

## 2. Important Deployment Rule

Do not bake huge model weights directly into the GitHub repo or Docker image.

Correct behavior:

```text
Code lives in GitHub.
ComfyUI is installed on /workspace.
Models are stored on /workspace/ComfyUI/models.
If files already exist, scripts must not download them again.
```

Every setup script must be idempotent.

Meaning:

```text
Running setup_vast.sh twice should not destroy or duplicate the installation.
```

---

## 3. Vast.ai Recommended Template Settings

The user will create a Vast.ai template with:

```text
Launch Mode:
Jupyter-python notebook + SSH

Ports:
7860 TCP
8188 TCP

Recommended GPU:
RTX 4090 24GB or better

Recommended disk:
150–250 GB minimum

Recommended OS/container:
PyTorch + CUDA + Ubuntu
```

Required environment variables in Vast template:

```env
APP_PORT=7860
COMFYUI_PORT=8188
COMFYUI_URL=http://127.0.0.1:8188
PROJECT_DIR=/workspace/ai-shorts-factory
COMFYUI_DIR=/workspace/ComfyUI
```

Optional environment variables:

```env
GITHUB_REPO_URL=https://github.com/YOUR_USERNAME/ai-shorts-factory.git
PROVISIONING_SCRIPT=https://raw.githubusercontent.com/YOUR_USERNAME/ai-shorts-factory/main/scripts/setup_vast.sh
AUTO_START=true
DOWNLOAD_MODELS=false
VIDEO_BACKEND=placeholder
```

If `DOWNLOAD_MODELS=false`, setup should install the system but not download huge model files.

If `DOWNLOAD_MODELS=true`, setup may call `scripts/download_models.sh`.

---

## 4. Files Cursor Must Create

Create or update these files:

```text
scripts/
  setup_vast.sh
  start_all.sh
  stop_all.sh
  restart_all.sh
  status.sh
  check_gpu.py
  install_comfyui.sh
  install_comfyui_custom_nodes.sh
  download_models.sh
  test_placeholder_generation.sh
  test_comfyui_connection.sh
  tail_logs.sh

docs/
  VAST_SETUP.md
  VAST_TEMPLATE.md
  MODEL_DOWNLOADS.md
  PRODUCTION_RUNBOOK.md

config/
  vast.yaml
  models.yaml

.env.vast.example
```

Also update:

```text
README.md
```

with a Vast.ai deployment section.

---

## 5. Required Directory Layout on Vast.ai

The installation must use:

```text
/workspace/
  ai-shorts-factory/
  ComfyUI/
  models_cache/
  logs/
```

Project path:

```text
/workspace/ai-shorts-factory
```

ComfyUI path:

```text
/workspace/ComfyUI
```

Logs:

```text
/workspace/logs/
  comfyui.log
  ai-shorts-factory.log
  setup_vast.log
```

---

## 6. `scripts/setup_vast.sh`

Create a robust setup script.

Requirements:

- Bash script.
- Must use `set -e`.
- Must log to `/workspace/logs/setup_vast.log`.
- Must install system packages.
- Must install Python venv for the project.
- Must install ComfyUI.
- Must optionally install ComfyUI custom nodes.
- Must optionally download models.
- Must optionally auto-start services.
- Must be safe to run multiple times.
- Must print final access instructions.

Script must support environment variables:

```env
PROJECT_DIR=/workspace/ai-shorts-factory
COMFYUI_DIR=/workspace/ComfyUI
APP_PORT=7860
COMFYUI_PORT=8188
AUTO_START=true
DOWNLOAD_MODELS=false
GITHUB_REPO_URL=
VIDEO_BACKEND=placeholder
```

Implementation logic:

```bash
#!/usr/bin/env bash
set -e

mkdir -p /workspace/logs
LOG_FILE="/workspace/logs/setup_vast.log"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "Starting Vast.ai setup..."

export PROJECT_DIR="${PROJECT_DIR:-/workspace/ai-shorts-factory}"
export COMFYUI_DIR="${COMFYUI_DIR:-/workspace/ComfyUI}"
export APP_PORT="${APP_PORT:-7860}"
export COMFYUI_PORT="${COMFYUI_PORT:-8188}"
export AUTO_START="${AUTO_START:-true}"
export DOWNLOAD_MODELS="${DOWNLOAD_MODELS:-false}"
export VIDEO_BACKEND="${VIDEO_BACKEND:-placeholder}"

apt update
DEBIAN_FRONTEND=noninteractive apt install -y \
  git wget curl ffmpeg python3 python3-venv python3-pip \
  build-essential tmux nano htop unzip rsync ca-certificates

mkdir -p /workspace/logs /workspace/models_cache

# Clone project only if not already present and GITHUB_REPO_URL is provided.
if [ ! -d "$PROJECT_DIR" ]; then
  if [ -n "$GITHUB_REPO_URL" ]; then
    git clone "$GITHUB_REPO_URL" "$PROJECT_DIR"
  else
    echo "PROJECT_DIR does not exist and GITHUB_REPO_URL is empty."
    echo "If this script is running from inside the repo, this is okay."
  fi
fi

# Install project dependencies.
if [ -d "$PROJECT_DIR" ]; then
  cd "$PROJECT_DIR"
  python3 -m venv .venv
  source .venv/bin/activate
  pip install --upgrade pip setuptools wheel
  pip install -r requirements.txt
  cp -n .env.vast.example .env || true

  # Make scripts executable.
  chmod +x scripts/*.sh || true
fi

# Install ComfyUI.
if [ -d "$PROJECT_DIR" ]; then
  bash "$PROJECT_DIR/scripts/install_comfyui.sh"
fi

# Install custom nodes.
if [ -d "$PROJECT_DIR" ]; then
  bash "$PROJECT_DIR/scripts/install_comfyui_custom_nodes.sh" || true
fi

# Optional model download.
if [ "$DOWNLOAD_MODELS" = "true" ] && [ -d "$PROJECT_DIR" ]; then
  bash "$PROJECT_DIR/scripts/download_models.sh"
else
  echo "Skipping model download. Set DOWNLOAD_MODELS=true to enable."
fi

# Auto-start.
if [ "$AUTO_START" = "true" ] && [ -d "$PROJECT_DIR" ]; then
  bash "$PROJECT_DIR/scripts/start_all.sh"
fi

echo "Setup complete."
echo "AI Shorts Factory internal URL: http://127.0.0.1:${APP_PORT}"
echo "ComfyUI internal URL: http://127.0.0.1:${COMFYUI_PORT}"
echo "On Vast.ai, use the external mapped URLs from IP Port Info."
```

Cursor must write the final script, not only this example.

---

## 7. `scripts/install_comfyui.sh`

Create this script.

Requirements:

- Install ComfyUI into `/workspace/ComfyUI`.
- Use Python venv inside ComfyUI.
- Do not reinstall if already installed.
- Update requirements if already present.
- Do not delete existing models.

Expected behavior:

```bash
#!/usr/bin/env bash
set -e

export COMFYUI_DIR="${COMFYUI_DIR:-/workspace/ComfyUI}"
mkdir -p /workspace/logs

if [ ! -d "$COMFYUI_DIR" ]; then
  git clone https://github.com/comfyanonymous/ComfyUI.git "$COMFYUI_DIR"
fi

cd "$COMFYUI_DIR"

python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

mkdir -p \
  models/checkpoints \
  models/diffusion_models \
  models/text_encoders \
  models/vae \
  models/clip_vision \
  models/upscale_models \
  models/controlnet \
  models/loras \
  output \
  input

echo "ComfyUI installed/updated at $COMFYUI_DIR"
```

---

## 8. `scripts/install_comfyui_custom_nodes.sh`

Create this script.

Requirements:

- Install ComfyUI Manager.
- Create a safe place for future video custom nodes.
- Do not crash if one node fails.
- Log warnings.

Suggested nodes:

```text
ComfyUI-Manager
ComfyUI-VideoHelperSuite
```

Script behavior:

```bash
#!/usr/bin/env bash
set -e

export COMFYUI_DIR="${COMFYUI_DIR:-/workspace/ComfyUI}"
CUSTOM_NODES_DIR="$COMFYUI_DIR/custom_nodes"

mkdir -p "$CUSTOM_NODES_DIR"
cd "$CUSTOM_NODES_DIR"

clone_or_update() {
  local repo_url="$1"
  local dir_name="$2"

  if [ -d "$dir_name" ]; then
    echo "Updating $dir_name"
    cd "$dir_name"
    git pull || true
    cd ..
  else
    echo "Cloning $dir_name"
    git clone "$repo_url" "$dir_name" || true
  fi
}

clone_or_update "https://github.com/ltdrdata/ComfyUI-Manager.git" "ComfyUI-Manager"
clone_or_update "https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git" "ComfyUI-VideoHelperSuite"

echo "Custom nodes installation complete."
```

Cursor may add more video nodes, but must avoid unstable random dependencies unless documented.

---

## 9. `scripts/start_all.sh`

Create this script.

Requirements:

- Start ComfyUI on port 8188.
- Start AI Shorts Factory on port 7860.
- Use `nohup` or `tmux`.
- Save logs.
- Avoid starting duplicates.
- Print URLs.

Behavior:

```bash
#!/usr/bin/env bash
set -e

export PROJECT_DIR="${PROJECT_DIR:-/workspace/ai-shorts-factory}"
export COMFYUI_DIR="${COMFYUI_DIR:-/workspace/ComfyUI}"
export APP_PORT="${APP_PORT:-7860}"
export COMFYUI_PORT="${COMFYUI_PORT:-8188}"
export COMFYUI_URL="${COMFYUI_URL:-http://127.0.0.1:${COMFYUI_PORT}}"

mkdir -p /workspace/logs

# Start ComfyUI if not already running.
if pgrep -f "ComfyUI.*main.py" > /dev/null; then
  echo "ComfyUI already running."
else
  echo "Starting ComfyUI..."
  cd "$COMFYUI_DIR"
  source venv/bin/activate
  nohup python main.py --listen 0.0.0.0 --port "$COMFYUI_PORT" > /workspace/logs/comfyui.log 2>&1 &
fi

sleep 3

# Start AI Shorts Factory if not already running.
if pgrep -f "app/webui.py" > /dev/null; then
  echo "AI Shorts Factory already running."
else
  echo "Starting AI Shorts Factory..."
  cd "$PROJECT_DIR"
  source .venv/bin/activate
  nohup python app/webui.py --host 0.0.0.0 --port "$APP_PORT" > /workspace/logs/ai-shorts-factory.log 2>&1 &
fi

sleep 2

echo "Started."
echo "AI Shorts Factory: http://127.0.0.1:${APP_PORT}"
echo "ComfyUI: http://127.0.0.1:${COMFYUI_PORT}"
echo "Use Vast.ai IP Port Info for public URLs."
```

If the actual app does not support CLI args yet, Cursor must add support to `app/webui.py`.

---

## 10. `scripts/stop_all.sh`

Create script to stop both services.

Requirements:

- Stop app.
- Stop ComfyUI.
- Do not kill unrelated Python processes if avoidable.
- Print status.

Example:

```bash
#!/usr/bin/env bash
set +e

pkill -f "app/webui.py"
pkill -f "ComfyUI.*main.py"

echo "Stopped AI Shorts Factory and ComfyUI if they were running."
```

Cursor may improve with PID files.

---

## 11. `scripts/restart_all.sh`

Create:

```bash
#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

bash "$SCRIPT_DIR/stop_all.sh"
sleep 2
bash "$SCRIPT_DIR/start_all.sh"
```

---

## 12. `scripts/status.sh`

Create a status script.

It must print:

- GPU info
- disk usage
- running processes
- port status
- ComfyUI health
- AI app health
- recent log tail

Example commands:

```bash
nvidia-smi || true
df -h /workspace || true
ps aux | grep -E "ComfyUI|webui.py" | grep -v grep || true
curl -s http://127.0.0.1:8188 || true
curl -s http://127.0.0.1:7860/health || true
tail -n 40 /workspace/logs/comfyui.log || true
tail -n 40 /workspace/logs/ai-shorts-factory.log || true
```

---

## 13. `scripts/tail_logs.sh`

Create:

```bash
#!/usr/bin/env bash
set -e

tail -f \
  /workspace/logs/setup_vast.log \
  /workspace/logs/comfyui.log \
  /workspace/logs/ai-shorts-factory.log
```

---

## 14. `scripts/download_models.sh`

Create a model download script.

Important:

Do not hardcode unstable or fake model URLs.

The script should support a manifest file:

```text
config/model_manifest.yaml
```

Create that manifest with placeholders.

Example:

```yaml
models:
  - name: "wan_or_ltx_model_placeholder"
    enabled: false
    url: ""
    target_path: "/workspace/ComfyUI/models/diffusion_models/model.safetensors"
    sha256: ""
    notes: "Fill official model URL manually."
```

Behavior:

- Read manifest.
- For enabled models with URL, download to target path.
- If file exists, skip.
- If sha256 exists, verify.
- If URL empty, print clear message.
- Do not fail whole setup just because model URL is empty.

Cursor can implement this in Bash or Python.

Preferred: create `scripts/download_models.py` and make `download_models.sh` call it.

---

## 15. `config/vast.yaml`

Create:

```yaml
vast:
  workspace_dir: "/workspace"
  project_dir: "/workspace/ai-shorts-factory"
  comfyui_dir: "/workspace/ComfyUI"
  logs_dir: "/workspace/logs"

server:
  app_host: "0.0.0.0"
  app_port: 7860
  comfyui_host: "0.0.0.0"
  comfyui_port: 8188

startup:
  auto_start: true
  download_models: false
  install_custom_nodes: true

runtime:
  default_video_backend: "placeholder"
  production_video_backend: "comfyui"
```

---

## 16. `.env.vast.example`

Create:

```env
APP_PORT=7860
COMFYUI_PORT=8188
COMFYUI_URL=http://127.0.0.1:8188

PROJECT_DIR=/workspace/ai-shorts-factory
COMFYUI_DIR=/workspace/ComfyUI

AUTO_START=true
DOWNLOAD_MODELS=false
VIDEO_BACKEND=placeholder

# Fill this after pushing the project to GitHub
GITHUB_REPO_URL=https://github.com/YOUR_USERNAME/ai-shorts-factory.git

# Optional future API keys
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
ELEVENLABS_API_KEY=
```

---

## 17. App Must Support CLI Args

Update `app/webui.py` so it supports:

```bash
python app/webui.py --host 0.0.0.0 --port 7860
```

Also use environment variables as fallback:

```text
APP_PORT
APP_HOST
```

Expected order:

```text
CLI args > environment variables > config/default.yaml > hardcoded fallback
```

---

## 18. Health Endpoint

Ensure the app has:

```text
GET /health
```

It should return:

```json
{
  "status": "ok",
  "app": "ai-shorts-factory",
  "version": "0.1.0",
  "video_backend": "placeholder",
  "comfyui_url": "http://127.0.0.1:8188",
  "comfyui_reachable": true
}
```

If Gradio is used, Cursor should still expose a small FastAPI health endpoint or mount Gradio onto FastAPI.

---

## 19. ComfyUI Health Check

Create `scripts/test_comfyui_connection.sh`:

```bash
#!/usr/bin/env bash
set -e

COMFYUI_PORT="${COMFYUI_PORT:-8188}"
curl -s "http://127.0.0.1:${COMFYUI_PORT}" > /dev/null

echo "ComfyUI is reachable at http://127.0.0.1:${COMFYUI_PORT}"
```

Also the app should show ComfyUI status in UI:

```text
ComfyUI: connected / disconnected
```

---

## 20. Placeholder Mode Must Work First

The project must work even without real AI video models.

Required:

```text
VIDEO_BACKEND=placeholder
```

must generate a complete final video with:

- 9:16 vertical MP4
- generated script
- generated subtitles
- generated silent or synthetic voice/audio
- generated ambience/music placeholder
- thumbnail
- title
- description
- hashtags
- publish package

This is not optional.

---

## 21. Production ComfyUI Mode

When real ComfyUI workflow is configured:

```text
VIDEO_BACKEND=comfyui
```

the project must:

1. Load workflow JSON from `workflows/`.
2. Inject the generated prompt.
3. Queue prompt through ComfyUI API.
4. Wait for completion.
5. Copy/download video output.
6. Render final video with audio/subtitles.
7. Save publish package.

If workflow node IDs are not configured, show this error:

```text
ComfyUI workflow is present, but prompt_node_id is not configured in config/models.yaml.
Open your workflow API JSON, find the text prompt node ID, and set it in config/models.yaml.
```

---

## 22. Vast.ai Template Documentation

Create `docs/VAST_TEMPLATE.md`.

It must explain exactly what the user should enter in Vast.ai.

### Ports

```text
7860 TCP
8188 TCP
```

### Environment variables

```env
APP_PORT=7860
COMFYUI_PORT=8188
COMFYUI_URL=http://127.0.0.1:8188
PROJECT_DIR=/workspace/ai-shorts-factory
COMFYUI_DIR=/workspace/ComfyUI
AUTO_START=true
DOWNLOAD_MODELS=false
VIDEO_BACKEND=placeholder
GITHUB_REPO_URL=https://github.com/YOUR_USERNAME/ai-shorts-factory.git
PROVISIONING_SCRIPT=https://raw.githubusercontent.com/YOUR_USERNAME/ai-shorts-factory/main/scripts/setup_vast.sh
```

### Launch Mode

```text
Jupyter-python notebook + SSH
```

### After Launch

```bash
cd /workspace/ai-shorts-factory
bash scripts/status.sh
bash scripts/tail_logs.sh
```

### Open UI

Use Vast.ai IP Port Info.

Find the external mapped port for internal port:

```text
7860
```

Open it in browser.

---

## 23. `docs/VAST_SETUP.md`

Create a clear full guide:

```text
1. Push project to GitHub.
2. Open Vast.ai.
3. Create/Edit template.
4. Add ports 7860 and 8188.
5. Add environment variables.
6. Set launch mode to Jupyter + SSH.
7. Rent RTX 4090 24GB or better.
8. Wait for setup.
9. Open terminal.
10. Run status script.
11. Open public URL for port 7860.
12. Generate placeholder test video.
13. Configure ComfyUI real workflow.
14. Switch VIDEO_BACKEND=comfyui.
15. Generate production video.
```

Include troubleshooting.

---

## 24. `docs/MODEL_DOWNLOADS.md`

Create a guide explaining:

- Models are large.
- Do not store them in Git.
- Put models under `/workspace/ComfyUI/models/...`.
- Use `config/model_manifest.yaml` for automatic downloads.
- If Hugging Face token is needed, add it as env var.
- If model license requires acceptance, user must accept it manually.
- If disk is small, use 200GB+ disk.

Include recommended folders:

```text
/workspace/ComfyUI/models/diffusion_models
/workspace/ComfyUI/models/text_encoders
/workspace/ComfyUI/models/vae
/workspace/ComfyUI/models/checkpoints
/workspace/ComfyUI/models/loras
```

---

## 25. `docs/PRODUCTION_RUNBOOK.md`

Create a runbook:

```text
Start:
bash scripts/start_all.sh

Stop:
bash scripts/stop_all.sh

Restart:
bash scripts/restart_all.sh

Status:
bash scripts/status.sh

Logs:
bash scripts/tail_logs.sh

Test placeholder:
bash scripts/test_placeholder_generation.sh

Test ComfyUI:
bash scripts/test_comfyui_connection.sh
```

Also include:

```text
Do not keep GPU running when not generating videos.
After generation, download outputs and stop/destroy instance if not needed.
```

---

## 26. `scripts/test_placeholder_generation.sh`

Create script:

```bash
#!/usr/bin/env bash
set -e

APP_PORT="${APP_PORT:-7860}"

curl -X POST "http://127.0.0.1:${APP_PORT}/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "idea": "A 15-second fake commercial for a programmer energy drink, funny meme style, vertical video.",
    "duration_seconds": 15,
    "style": "funny meme",
    "language": "en",
    "voice_mode": "narrator",
    "music": "light background"
  }'
```

If the app uses async jobs, the script should print returned job ID and then instruct user to check UI or job endpoint.

---

## 27. Batch Generation on Vast

Ensure batch mode works on Vast.

Command:

```bash
cd /workspace/ai-shorts-factory
source .venv/bin/activate
python app/main.py --batch batch_prompts.txt
```

For each line, generate full publish package.

---

## 28. Readiness Indicator

The web UI should show a clear readiness box:

```text
System Status
- App: running
- ComfyUI: connected/disconnected
- Video backend: placeholder/comfyui
- GPU: detected/not detected
- Output directory: /workspace/ai-shorts-factory/outputs
- Production ready: yes/no
```

Production ready is `yes` only if:

```text
ComfyUI is connected
workflow file exists
prompt node ID is configured
models likely exist
FFmpeg is installed
```

---

## 29. Do Not Use Browser Scraping

Do not implement browser-based uploading to TikTok, YouTube, or Instagram.

The system should generate a publish package for manual upload.

Allowed:

```text
Manual upload instructions
Future official API integration stubs
```

Not allowed:

```text
selenium login automation
cookie stealing
platform scraping
copyrighted music downloader
real-person voice cloning
```

---

## 30. Update README

Update `README.md` with:

```text
Quick Local Test
Vast.ai Deployment
Ports
Environment Variables
How to Create Vast Template
How to Start/Stop
How to Generate First Placeholder Video
How to Configure ComfyUI Real Video Generation
Where Outputs Are Saved
Troubleshooting
Cost Control
```

Cost control section:

```text
Do not leave the GPU server running 24/7 unless needed.
Generate videos, download outputs, then stop/destroy the instance.
```

---

## 31. Cursor Implementation Order

Cursor must implement in this order:

### Step 1

Create all Vast scripts.

### Step 2

Make app support CLI host/port and `/health`.

### Step 3

Make placeholder mode generate full publish package.

### Step 4

Create status/log/test scripts.

### Step 5

Create Vast docs.

### Step 6

Update README.

### Step 7

Run a local smoke test if possible.

---

## 32. Acceptance Criteria

The deployment task is complete only when:

1. `scripts/setup_vast.sh` exists and is executable.
2. `scripts/start_all.sh` starts both ComfyUI and AI Shorts Factory.
3. `scripts/stop_all.sh` stops both.
4. `scripts/status.sh` prints useful diagnostic information.
5. `app/webui.py --host 0.0.0.0 --port 7860` works.
6. `/health` returns JSON.
7. Placeholder generation works without models.
8. ComfyUI connection test script exists.
9. Vast template documentation exists.
10. README contains Vast setup instructions.
11. The project can be launched from Vast.ai with `PROVISIONING_SCRIPT`.
12. The user can generate a ready-to-publish MP4 from one prompt.

---

## 33. Final Message Cursor Should Print

After completing implementation, Cursor should print:

```text
Vast.ai deployment support is ready.

Next steps:

1. Push this repo to GitHub.
2. In Vast.ai template, add:
   - ports: 7860 TCP, 8188 TCP
   - PROVISIONING_SCRIPT=https://raw.githubusercontent.com/YOUR_USERNAME/ai-shorts-factory/main/scripts/setup_vast.sh
   - GITHUB_REPO_URL=https://github.com/YOUR_USERNAME/ai-shorts-factory.git
3. Launch RTX 4090 24GB instance.
4. Wait for setup.
5. Open the public URL mapped to internal port 7860.
6. Generate a test video in placeholder mode.
7. Configure ComfyUI workflow for production mode.
```

---

# End of Specification

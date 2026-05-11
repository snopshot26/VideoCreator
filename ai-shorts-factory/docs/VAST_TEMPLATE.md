# Vast.ai template (recommended)

Use this checklist when creating or editing an instance template on [Vast.ai](https://vast.ai).

## Launch mode

```text
Jupyter-python notebook + SSH
```

## Ports (TCP)

| Internal port | Purpose        |
|---------------|----------------|
| 7860          | AI Shorts Factory (FastAPI + Gradio UI at `/ui`) |
| 8188          | ComfyUI          |

## Environment variables

```env
APP_PORT=7860
COMFYUI_PORT=8188
COMFYUI_URL=http://127.0.0.1:8188
APP_HOST=0.0.0.0

PROJECT_DIR=/workspace/ai-shorts-factory
COMFYUI_DIR=/workspace/ComfyUI

AUTO_START=true
DOWNLOAD_MODELS=false
VIDEO_BACKEND=placeholder

GITHUB_REPO_URL=https://github.com/YOUR_USERNAME/ai-shorts-factory.git
PROVISIONING_SCRIPT=https://raw.githubusercontent.com/YOUR_USERNAME/ai-shorts-factory/main/scripts/setup_vast.sh
```

- Set `GITHUB_REPO_URL` and `PROVISIONING_SCRIPT` to **your** fork.
- Keep `DOWNLOAD_MODELS=false` until you deliberately add verified URLs to `config/model_manifest.yaml`.
- Use `VIDEO_BACKEND=placeholder` until ComfyUI workflows and weights are configured; then switch to `VIDEO_BACKEND=comfyui`.

## On-disk layout (target)

```text
/workspace/
  ai-shorts-factory/   # this app
  ComfyUI/             # ComfyUI install
  models_cache/        # optional cache
  logs/                # setup + service logs
```

## After the instance boots

```bash
cd /workspace/ai-shorts-factory
bash scripts/status.sh
bash scripts/tail_logs.sh
```

## Open the UI

In Vast **IP & Port** info, find the **public** URL mapped to internal port **7860**.

- Web UI: `https://...` → path `/` redirects to `/ui`
- Health JSON: same host, path `/health`

Internal checks:

```text
http://127.0.0.1:7860/health
http://127.0.0.1:8188/system_stats
```

## GPU and disk

- Prefer **RTX 4090 24GB** or better.
- Use **150–250 GB+** disk if you plan to store diffusion checkpoints locally.

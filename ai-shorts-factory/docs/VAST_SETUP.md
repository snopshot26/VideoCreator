# Vast.ai full setup guide

## 1. Push to GitHub

Push this repository (or your fork) to GitHub. Do **not** commit large model weights.

## 2. Create a Vast template

Follow `docs/VAST_TEMPLATE.md` for ports, environment variables, and launch mode.

## 3. Point provisioning at `setup_vast.sh`

Set `PROVISIONING_SCRIPT` to the **raw** URL of `scripts/setup_vast.sh` on your default branch, for example:

```text
https://raw.githubusercontent.com/YOUR_USERNAME/ai-shorts-factory/main/scripts/setup_vast.sh
```

Set `GITHUB_REPO_URL` to your clone URL.

`setup_vast.sh` supports both provisioning modes:

- **Automatic provisioning**: if `PROJECT_DIR` is missing and `GITHUB_REPO_URL` is set, it clones into `PROJECT_DIR`.
- **Manual existing-repo**: if running from `scripts/setup_vast.sh` inside an existing checkout, it auto-detects the repo root (`requirements.txt`, `app/`, `pipeline/`) and uses it as `PROJECT_DIR` unless user provided `PROJECT_DIR`.
- **Skip clone**: with `SKIP_GIT_CLONE=true`, clone is disabled and `PROJECT_DIR` must already exist.

## 4. Rent a suitable GPU

Prefer RTX 4090 24GB+ and enough disk for ComfyUI models you plan to install.

## 5. Wait for setup

`setup_vast.sh` logs to `/workspace/logs/setup_vast.log` and mirrors output to stdout.

Idempotent behavior:

- Re-running setup should not wipe existing `ComfyUI/models` weights.
- Python venvs are created only if missing.

## 6. SSH / Jupyter terminal

```bash
cd /workspace/ai-shorts-factory
bash scripts/status.sh
```

### Manual existing-repo setup example

```bash
cd /workspace/VideoCreator/ai-shorts-factory
export SKIP_GIT_CLONE=true
export PROJECT_DIR=/workspace/VideoCreator/ai-shorts-factory
export COMFYUI_DIR=/workspace/ComfyUI
export APP_PORT=7860
export COMFYUI_PORT=8188
export COMFYUI_URL=http://127.0.0.1:8188
export APP_HOST=0.0.0.0
export AUTO_START=true
export DOWNLOAD_MODELS=false
export VIDEO_BACKEND=placeholder
export COMFYUI_MULTI_GPU=false
export COMFYUI_WORKERS=1
export COMFYUI_URLS=http://127.0.0.1:8188
bash scripts/setup_vast.sh
```

## 7. Open the public URL for port 7860

Use Vast’s mapped external URL. Paths:

- `/` → redirects to `/ui`
- `/ui` — Gradio
- `/health` — JSON status

## 8. First placeholder video

With `VIDEO_BACKEND=placeholder` (default on Vast), generate from the UI or run:

```bash
bash scripts/test_placeholder_generation.sh
```

One-shot **production smoke** (Python pipeline + `ffprobe` 1080×1920 + publish JSON checks, no ComfyUI, no HTTP):

```bash
bash scripts/smoke_test_production.sh
```

Confirm `outputs/<job_id>/` contains `final.mp4`, subtitles, publish package, etc.

## 9. Configure ComfyUI for production

1. Install weights under `/workspace/ComfyUI/models/...` (manual or `DOWNLOAD_MODELS=true` with a filled `config/model_manifest.yaml`).
2. Export a working API workflow JSON into `workflows/wan_t2v_vertical.json`.
3. Set `prompt_node_id` in `config/models.yaml`.
4. Set `VIDEO_BACKEND=comfyui` in the template (or `.env`), restart:

```bash
bash scripts/restart_all.sh
```

## 10. Troubleshooting

- **App not listening**: `tail -n 80 /workspace/logs/ai-shorts-factory.log`
- **ComfyUI not listening**: `tail -n 80 /workspace/logs/comfyui.log`
- **FFmpeg missing**: `apt-get install -y ffmpeg` (should already be installed by `setup_vast.sh`)
- **CUDA / driver issues**: run `nvidia-smi` inside the instance; pick a CUDA-capable template.

## Cost control

Do not leave a GPU instance running 24/7 unless you need it. Generate videos, **download** `outputs/`, then stop or destroy the instance when idle.

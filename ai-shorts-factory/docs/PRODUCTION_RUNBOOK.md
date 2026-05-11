# Production runbook (Vast / GPU server)

## Provisioning (`setup_vast.sh`)

`scripts/setup_vast.sh` is idempotent and supports:

- **Automatic provisioning**: clone from `GITHUB_REPO_URL` when `PROJECT_DIR` is missing.
- **Manual existing-repo mode**: detects repo root automatically when run from `scripts/setup_vast.sh`.
- **No-clone mode**: `SKIP_GIT_CLONE=true` requires an existing `PROJECT_DIR`.

Manual existing-repo example:

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

## Start

```bash
cd /workspace/ai-shorts-factory
bash scripts/start_all.sh
```

Starts ComfyUI (8188) and the app (7860) under `nohup`, logs to `/workspace/logs/`.

## Stop

```bash
bash scripts/stop_all.sh
```

## Restart

```bash
bash scripts/restart_all.sh
```

## Status

```bash
bash scripts/status.sh
```

## Logs (follow)

```bash
bash scripts/tail_logs.sh
```

## Tests

### Full production smoke (placeholder — no ComfyUI, no HTTP)

After Vast setup (or any host with FFmpeg + `.venv`):

```bash
cd /workspace/ai-shorts-factory
bash scripts/smoke_test_production.sh
```

This runs one complete generation (`VIDEO_BACKEND=placeholder`), checks **1080×1920** `final.mp4` with **ffprobe**, and verifies the publish package files and `publish_package.json` keys. Exits non-zero on any failure; prints **PASSED** only when everything succeeds.

Expected:

```text
PASSED: generated playable vertical final.mp4 and complete publish package.
```

### With HTTP server (`start_all` running)

```bash
bash scripts/test_placeholder_generation.sh
bash scripts/test_comfyui_connection.sh
```

### Multi-GPU ComfyUI workers (after `COMFYUI_MULTI_GPU=true`)

```bash
bash scripts/test_multigpu_comfyui.sh
```

For other one-off checks, see `docs/USAGE.md`.

## Batch

```bash
cd /workspace/ai-shorts-factory
source .venv/bin/activate
python app/main.py --batch batch_prompts.txt
```

## Production checklist

- [ ] `VIDEO_BACKEND=comfyui`
- [ ] ComfyUI reachable (`/system_stats`)
- [ ] Valid workflow JSON in `workflows/`
- [ ] `prompt_node_id` set in `config/models.yaml`
- [ ] Weights present under `/workspace/ComfyUI/models/...`
- [ ] FFmpeg available (`ffmpeg -version`)

## Cost and safety

- Stop instances when idle; download outputs before destroying disk.
- No browser scraping uploads — use the generated publish package and upload manually (or future official APIs only).

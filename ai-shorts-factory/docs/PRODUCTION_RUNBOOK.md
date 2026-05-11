# Production runbook (Vast / GPU server)

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

# AI Shorts Factory (`ai-shorts-factory`)

Self-hosted pipeline for **vertical 9:16** short videos (TikTok / YouTube Shorts / Instagram Reels): script → prompts → TTS → music bed → video (ComfyUI or placeholder) → subtitles → FFmpeg final export → thumbnail + publish pack.

## What it does today

- Full **placeholder mode** end-to-end (black/slate video + audio mux + burned-in subtitles) without any ML weights.
- **ComfyUI integration** when reachable and `config/models.yaml` has valid `prompt_node_id` + a real exported workflow.
- **Local TTS** via `pyttsx3` by default (falls back to silent WAV on failure).
- **Synthetic / assets music** (no copyrighted downloads).
- **Batch mode** and **JSONL history** (`outputs/history.jsonl`).
- **Publish package**: `title.txt`, `description.txt`, `hashtags.txt`, `publish_package.json`, `thumbnail.png`, `captions.srt` (copy of subtitles), `captions_burned_in.mp4` (copy of final when burn-in enabled).
- **Vast.ai** provisioning scripts, runbooks, and `VIDEO_BACKEND` switch (`placeholder` vs `comfyui`).

## What it does not do yet

- No automatic platform uploads (manual upload only; see `platforms/README.md`).
- No cloud-only paid dependencies in the core path.
- No voice cloning of real people.

## Quick local test

```bash
cd ai-shorts-factory
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
# FFmpeg must be on PATH (full placeholder + mux requires it)
python app/webui.py --host 127.0.0.1 --port 7860
```

Structure-only check (no FFmpeg needed):

```bash
python scripts/verify_structure.py
```

### Production smoke test (after Vast setup, placeholder mode)

Requires **ffmpeg** + **ffprobe** and project **`.venv`**. Does **not** use ComfyUI.

```bash
cd /workspace/ai-shorts-factory
bash scripts/smoke_test_production.sh
```

Expected final line:

```text
PASSED: generated playable vertical final.mp4 and complete publish package.
```

On **Windows**, if `ffmpeg` is missing: install FFmpeg and add it to `PATH` (e.g. `winget install FFmpeg` or a static build), then reopen the terminal.

- UI: `http://127.0.0.1:7860/ui` (or `/` → redirects to `/ui`)
- Health: `http://127.0.0.1:7860/health`

CLI overrides env overrides `config/default.yaml` for `--host` / `--port`. Env vars: `APP_HOST`, `APP_PORT`, `COMFYUI_URL`, `COMFYUI_PORT`, `VIDEO_BACKEND`.

## Quick start (Ubuntu desktop / server)

```bash
cd ai-shorts-factory
bash scripts/install_server.sh
bash scripts/start_app.sh
```

Open **`http://SERVER_IP:7860/ui`**. Health: `http://SERVER_IP:7860/health`.

## Quick start (Windows dev)

```powershell
cd ai-shorts-factory
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
# Install FFmpeg and ensure `ffmpeg` is on PATH
python app/webui.py
```

## Vast.ai deployment

High-level flow:

```text
Push repo → create Vast template (ports + env) → PROVISIONING_SCRIPT runs setup_vast.sh
→ ComfyUI + app start → open public URL for 7860 → generate
```

### Ports

| TCP | Service |
|-----|---------|
| 7860 | AI Shorts Factory (API + Gradio `/ui`) |
| 8188 | ComfyUI |

### Environment variables (template)

See `.env.vast.example` and `docs/VAST_TEMPLATE.md`. Typical:

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

### How to create the Vast template

1. Read **`docs/VAST_TEMPLATE.md`** (launch mode, ports, env block).
2. Paste `PROVISIONING_SCRIPT` raw URL to `scripts/setup_vast.sh` on your branch.
3. Use Jupyter + SSH image with CUDA drivers.

### How to start / stop on the instance

```bash
cd /workspace/ai-shorts-factory
bash scripts/start_all.sh
bash scripts/status.sh
bash scripts/stop_all.sh
bash scripts/restart_all.sh
bash scripts/tail_logs.sh
```

Logs on Vast: `/workspace/logs/setup_vast.log`, `comfyui.log` (single-GPU) or `comfyui_gpu0.log` / `comfyui_gpu1.log` (multi-GPU), `ai-shorts-factory.log`.

### First placeholder video on Vast

1. Keep `VIDEO_BACKEND=placeholder` until workflows + weights are ready.
2. Run `bash scripts/start_all.sh`, then `bash scripts/test_placeholder_generation.sh` **or** use the web UI.
3. Artifacts live under `/workspace/ai-shorts-factory/outputs/<job_id>/`.

### ComfyUI production video

1. Install weights under `/workspace/ComfyUI/models/...` (see `docs/MODEL_DOWNLOADS.md`).
2. Export API workflow JSON to `workflows/wan_t2v_vertical.json` and set `prompt_node_id` in `config/models.yaml`.
3. Set `VIDEO_BACKEND=comfyui`, `bash scripts/restart_all.sh`.

### Where outputs are saved

- Per job: `outputs/<job_id>/` (under project root; on Vast that is `/workspace/ai-shorts-factory/outputs/...`).
- Last good export copy: `outputs/latest/final.mp4`.
- History: `outputs/history.jsonl`.

### Troubleshooting (Vast)

See **`docs/VAST_SETUP.md`** and **`docs/TROUBLESHOOTING.md`**. Quick checks: `bash scripts/status.sh`, `tail` logs in `/workspace/logs/`.

### Cost control

Do **not** leave a rented GPU running 24/7 unless you need it. Generate, **download** outputs from `outputs/`, then stop or destroy the instance.

### Multi-GPU ComfyUI (parallel workers, not pooled VRAM)

With **`COMFYUI_MULTI_GPU=true`** and **≥2 GPUs** (`nvidia-smi -L`), `scripts/start_all.sh` starts:

- GPU **0**: `CUDA_VISIBLE_DEVICES=0` → port **8188** → log `comfyui_gpu0.log`, PID `comfyui_gpu0.pid`
- GPU **1**: `CUDA_VISIBLE_DEVICES=1` → port **8189** → log `comfyui_gpu1.log`, PID `comfyui_gpu1.pid`

The app uses **`COMFYUI_URLS`** (comma-separated) and **round-robin** across healthy workers. **Two 24GB GPUs do not become 48GB for one model** — you get **two independent ComfyUI servers** for **parallel** jobs.

**2× RTX 4090 example (Vast):** open TCP **7860**, **8188**, **8189** and set:

```env
COMFYUI_MULTI_GPU=true
COMFYUI_WORKERS=2
COMFYUI_URLS=http://127.0.0.1:8188,http://127.0.0.1:8189
COMFYUI_PORT=8188
COMFYUI_PORT_SECOND=8189
```

Verify workers: `bash scripts/test_multigpu_comfyui.sh`. Batch mode limits parallel jobs to **`COMFYUI_WORKERS`** and, for ComfyUI video, to the number of **reachable** worker URLs.

## First placeholder video (no ComfyUI)

1. Set `VIDEO_BACKEND=placeholder` **or** keep `prompt_node_id` unset / ComfyUI stopped — you still get `final.mp4`.
2. Use the Web UI or (with server running) `bash scripts/test_placeholder_generation.sh`.
3. Inspect `outputs/<job_id>/` for the full artifact set.

## Connect ComfyUI (local generation)

1. Start ComfyUI (`bash scripts/start_comfyui.sh` — uses `COMFYUI_DIR`, default `/workspace/ComfyUI` or `./ComfyUI` off-repo).
2. Export your Wan/LTX **API** workflow JSON into `workflows/wan_t2v_vertical.json`.
3. Set `prompt_node_id` in `config/models.yaml`.
4. Set `VIDEO_BACKEND=comfyui` and restart the app.

See `docs/MODEL_SETUP.md` and `workflows/README.md`.

## API example

```bash
curl -X POST http://127.0.0.1:7860/generate \
  -H "Content-Type: application/json" \
  -d '{
    "idea": "A funny vertical video about a fictional politician-style taxi driver arguing about oil prices",
    "duration_seconds": 15,
    "style": "realistic cinematic",
    "language": "en",
    "voice_mode": "dialogue",
    "music": "city ambience"
  }'
```

## Batch

```bash
python app/main.py --batch batch_prompts.txt
```

## Example prompts

```text
A 15-second vertical realistic cinematic video of a fictional politician-style taxi driver arguing with a passenger about oil prices, neon city at night, funny dialogue, subtitles, meme ending.
```

```text
A 12-second TikTok-style fake commercial for an energy drink for programmers, fast cuts, dramatic voiceover, glowing laptop, cyberpunk office, bold captions.
```

```text
A 20-second documentary-style short about why people procrastinate, cinematic b-roll, narrator voice, subtitles, calm background music.
```

## Docs

- `docs/SERVER_SETUP.md`
- `docs/USAGE.md`
- `docs/TROUBLESHOOTING.md`
- `docs/MODEL_SETUP.md`
- `docs/VAST_SETUP.md`
- `docs/VAST_TEMPLATE.md`
- `docs/MODEL_DOWNLOADS.md`
- `docs/PRODUCTION_RUNBOOK.md`

---

AI Shorts Factory is ready.

Run locally:

```bash
bash scripts/install_server.sh
bash scripts/start_app.sh
```

Then open:

```text
http://SERVER_IP:7860/ui
```

On **Vast.ai**, use `scripts/setup_vast.sh` + the template described in `docs/VAST_TEMPLATE.md`.

First test **placeholder** mode. After that, configure ComfyUI workflow in `workflows/` and `config/models.yaml`, then set `VIDEO_BACKEND=comfyui`.

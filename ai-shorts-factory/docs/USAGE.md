# Usage

## Web UI

```bash
bash scripts/start_app.sh
# or
python app/webui.py
```

Open `http://127.0.0.1:7860/ui` (Gradio UI). API routes live on the same port (for example `GET /health`).

## API

- `GET /health` — liveness + ComfyUI reachability flag
- `POST /generate` — JSON body per README example
- `GET /jobs/{job_id}` — job summary + logs tail
- `GET /outputs/{job_id}/final` — download `final.mp4`
- `GET /outputs/{job_id}/metadata` — `metadata.json`
- `GET /history/recent` — last lines from `outputs/history.jsonl`

## Batch

Create `batch_prompts.txt` (one idea per line), then:

```bash
python app/main.py --batch batch_prompts.txt
```

Outputs go to `outputs/batch_{timestamp}/job_001/`, plus `batch_summary.csv` and `batch_summary.json`.

## Stages

- **Placeholder** — ComfyUI not reachable, node IDs not configured, or generation fell back to FFmpeg slate.
- **Local ComfyUI** — ComfyUI produced `raw_video.mp4` but TTS may still be simple.
- **Production** — ComfyUI video + non-placeholder TTS provider (for example `pyttsx3`).

Tune `config/default.yaml` and `config/models.yaml` to move between stages.

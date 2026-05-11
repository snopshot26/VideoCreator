# Troubleshooting

## ComfyUI not running

Message:

```text
ComfyUI is not reachable at http://127.0.0.1:8188.
Start it with: bash scripts/start_comfyui.sh
Or switch video backend to placeholder in config/default.yaml.
```

Fix: start ComfyUI, confirm `COMFYUI_URL` in `.env`, or set `comfyui.enabled: false` to force placeholder video.

## Workflow missing

Message:

```text
Workflow file not found. Add your exported ComfyUI API workflow to workflows/wan_t2v_vertical.json.
```

Fix: export API JSON from ComfyUI into that path (see `workflows/README.md`).

## Prompt node ID missing

Message:

```text
Prompt node ID is not configured. Open config/models.yaml and set prompt_node_id for your workflow.
```

Fix: open your workflow JSON, find the node id for the positive prompt input, set `prompt_node_id` accordingly.

## FFmpeg missing

Message:

```text
FFmpeg is not installed. Run: sudo apt install ffmpeg
```

Fix: install FFmpeg and ensure it is on `PATH`.

## pyttsx3 errors

On headless Linux servers, pyttsx3 may require additional packages. Set `tts.provider: placeholder` in `config/default.yaml` to force silent WAV and keep the pipeline working.

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import gradio as gr
import uvicorn
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.api import router
from app.config import load_app_config, resolve_path
from app.logger import setup_logging
from app.readiness import readiness_markdown, readiness_snapshot
from app.system_info import gpu_payload
from pipeline.comfy_pool import any_comfy_healthy
from pipeline.orchestrator import GenerateInput, run_pipeline


def _read_text(p: Path) -> str:
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8", errors="replace")


def _recent_history_text(limit: int = 15) -> str:
    cfg = load_app_config()
    hp = resolve_path(cfg, cfg.paths.outputs_dir) / "history.jsonl"
    if not hp.exists():
        return "(no history yet)"
    lines = hp.read_text(encoding="utf-8", errors="replace").splitlines()[-limit:]
    rows = []
    for ln in reversed(lines):
        try:
            o = json.loads(ln)
            rows.append(f"- {o.get('created_at')} | {o.get('status')} | {o.get('idea','')[:80]}")
        except json.JSONDecodeError:
            continue
    return "\n".join(rows) if rows else "(empty)"


def run_generation(
    idea: str,
    duration: int,
    style: str,
    language: str,
    voice_mode: str,
    music: str,
    progress: gr.Progress = gr.Progress(),
):
    progress(0.05, desc="Validating…")
    cfg = load_app_config()
    comfy_ok = any_comfy_healthy(cfg)
    gpu = gpu_payload()

    progress(0.15, desc="Generating…")
    res = run_pipeline(
        GenerateInput(
            idea=idea,
            duration_seconds=int(duration),
            style=style,
            language=language,
            voice_mode=voice_mode,  # type: ignore[arg-type]
            music=music,
        )
    )

    out = res.output_dir
    script = _read_text(out / "script.json")
    prompt = _read_text(out / "prompt.txt")
    title = _read_text(out / "title.txt")
    desc = _read_text(out / "description.txt")
    tags = _read_text(out / "hashtags.txt")
    logs = _read_text(out / "logs.txt")
    history = _recent_history_text()

    final_p = out / "final.mp4"
    thumb_p = out / "thumbnail.png"

    upload_msg = (
        "Your video is ready. Download final.mp4 and upload it manually."
        if not cfg.platform_upload.enabled
        else "Platform upload is not enabled (manual upload recommended)."
    )

    status_lines = [
        f"Job: {res.job_id}",
        f"Status: {res.status}",
        f"Pipeline stage: {res.stage}",
        f"ComfyUI reachable: {comfy_ok}",
        upload_msg,
    ]

    video_path = str(final_p) if final_p.exists() else None
    thumb_path = str(thumb_p) if thumb_p.exists() else None

    pack_files = [
        str(p)
        for p in (out / "publish_package.json", out / "metadata.json", out / "subtitles.srt")
        if p.exists()
    ]

    return (
        video_path,
        thumb_path,
        title,
        desc,
        tags,
        script,
        prompt,
        logs,
        "\n".join(status_lines),
        json.dumps({"nvidia_smi_head": gpu["nvidia_smi"].splitlines()[:8], "ffmpeg": gpu["ffmpeg"]}, indent=2),
        history,
        pack_files,
    )


def build_app() -> FastAPI:
    setup_logging()
    app = FastAPI(title="AI Shorts Factory")
    app.include_router(router)

    @app.get("/")
    def _root():
        return RedirectResponse(url="/ui", status_code=302)

    styles = [
        "realistic cinematic",
        "funny meme",
        "documentary",
        "dramatic",
        "podcast clip",
        "fake commercial",
    ]
    langs = ["en", "ru", "tr"]
    voices = ["narrator", "dialogue", "no voice"]
    music_opts = ["none", "light background", "dramatic", "funny", "city ambience"]

    with gr.Blocks(title="AI Shorts Factory") as demo:
        gr.Markdown("# AI Shorts Factory\nGenerate vertical 9:16 shorts (placeholder mode works without ComfyUI).")
        readiness_md = gr.Markdown()
        refresh = gr.Button("Refresh system status", variant="secondary")

        def _readiness():
            return readiness_markdown(readiness_snapshot())

        demo.load(_readiness, outputs=readiness_md)
        refresh.click(_readiness, outputs=readiness_md)

        with gr.Row():
            idea = gr.Textbox(label="Main idea / prompt", lines=4)
        with gr.Row():
            duration = gr.Dropdown(choices=[8, 15, 30], value=15, label="Duration (seconds)")
            style = gr.Dropdown(choices=styles, value=styles[0], label="Style")
            language = gr.Dropdown(choices=langs, value="en", label="Language")
        with gr.Row():
            voice_mode = gr.Dropdown(choices=voices, value="narrator", label="Voice mode")
            music = gr.Dropdown(choices=music_opts, value="light background", label="Music")
        gen_btn = gr.Button("Generate", variant="primary")
        status = gr.Textbox(label="Status / stage", lines=6)
        gpu_box = gr.Code(label="GPU / FFmpeg (head)", language="json")
        hist = gr.Textbox(label="Recent generations (history.jsonl)", lines=8)

        with gr.Row():
            video = gr.Video(label="Preview (final.mp4)")
            thumb = gr.Image(label="Thumbnail")
        with gr.Row():
            title_o = gr.Textbox(label="Generated title")
            desc_o = gr.Textbox(label="Description")
            tags_o = gr.Textbox(label="Hashtags")
        script_o = gr.Code(label="script.json", language="json")
        prompt_o = gr.Textbox(label="prompt.txt", lines=8)
        logs_o = gr.Textbox(label="logs.txt", lines=12)
        pack = gr.File(label="Publish pack (json + metadata + srt)", file_count="multiple")

        gen_btn.click(
            fn=run_generation,
            inputs=[idea, duration, style, language, voice_mode, music],
            outputs=[
                video,
                thumb,
                title_o,
                desc_o,
                tags_o,
                script_o,
                prompt_o,
                logs_o,
                status,
                gpu_box,
                hist,
                pack,
            ],
        )

    return gr.mount_gradio_app(app, demo, path="/ui")


app = build_app()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AI Shorts Factory web UI + API")
    parser.add_argument("--host", default=None, help="Bind host (overrides APP_HOST, then config)")
    parser.add_argument("--port", type=int, default=None, help="TCP port (overrides APP_PORT, then config)")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    cfg = load_app_config()
    # Priority: CLI > environment (merged into cfg via load_app_config) > yaml defaults.
    host = args.host if args.host is not None else cfg.server.host
    port = args.port if args.port is not None else cfg.server.port
    uvicorn.run(app, host=host, port=int(port))

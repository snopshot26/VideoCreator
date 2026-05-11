from __future__ import annotations

import json
import shutil
from enum import Enum
from pathlib import Path
from typing import Any

from loguru import logger

from app.config import AppConfig, ModelsConfig, comfy_base_urls, project_root, resolve_path
from pipeline.comfy_client import ComfyUIClient, inject_prompts, strip_meta_keys
from pipeline.comfy_pool import pick_healthy_comfy_base_url
from pipeline.ffmpeg_util import ffmpeg_available, run_ffmpeg


class VideoBackend(str, Enum):
    COMFYUI = "comfyui"
    PLACEHOLDER = "placeholder"


def _workflow_path(cfg: AppConfig) -> Path:
    rel = cfg.comfyui.default_workflow
    return (project_root() / rel).resolve()


def _placeholder_video(output_path: Path, duration: int, width: int, height: int, title_file: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    title_file.write_text("Video generation placeholder\n", encoding="utf-8")
    # Use cwd=output dir so drawtext can load textfile by basename (path escaping).
    out_dir = output_path.parent
    run_ffmpeg(
        [
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"color=c=#111122:s={width}x{height}:d={duration}",
            "-vf",
            f"drawtext=textfile={title_file.name}:fontcolor=white:fontsize=42:x=(w-text_w)/2:y=(h-text_h)/2",
            "-r",
            "24",
            output_path.name,
        ],
        cwd=out_dir,
    )


def generate_raw_video(
    cfg: AppConfig,
    models_cfg: ModelsConfig,
    output_dir: Path,
    *,
    master_prompt: str,
    negative_prompt: str,
    duration_seconds: int,
) -> tuple[Path, VideoBackend, str]:
    """Returns (raw_video_path, backend_used, human_message)."""
    w, h = cfg.video.final_width, cfg.video.final_height
    raw_path = output_dir / "raw_video.mp4"
    title_file = output_dir / "placeholder_overlay.txt"

    backend = (models_cfg.video_backend or "").strip().lower()
    if backend == VideoBackend.PLACEHOLDER.value:
        _placeholder_video(raw_path, duration_seconds, w, h, title_file)
        return (
            raw_path,
            VideoBackend.PLACEHOLDER,
            "VIDEO_BACKEND=placeholder; using placeholder video.",
        )

    use_comfy = (
        cfg.comfyui.enabled
        and backend == VideoBackend.COMFYUI.value
        and ffmpeg_available()
    )

    wf_path = _workflow_path(cfg)
    if not wf_path.exists():
        msg = (
            "Workflow file not found. Add your exported ComfyUI API workflow to "
            f"{cfg.comfyui.default_workflow}."
        )
        logger.error(msg)
        _placeholder_video(raw_path, duration_seconds, w, h, title_file)
        return raw_path, VideoBackend.PLACEHOLDER, msg

    wmap = models_cfg.workflow_map("wan_t2v")
    if wmap is None:
        wmap = models_cfg.workflow_map("wan_i2v")

    prompt_node_id = wmap.prompt_node_id if wmap else None
    if not prompt_node_id:
        if wf_path.exists():
            msg = (
                "ComfyUI workflow is present, but prompt_node_id is not configured in config/models.yaml. "
                "Open your workflow API JSON, find the text prompt node ID, and set it in config/models.yaml."
            )
        else:
            msg = (
                "Prompt node ID is not configured. Open config/models.yaml and set prompt_node_id "
                "for your workflow."
            )
        logger.error(msg)
        _placeholder_video(raw_path, duration_seconds, w, h, title_file)
        return raw_path, VideoBackend.PLACEHOLDER, msg

    if not use_comfy:
        msg = "ComfyUI disabled or video backend not comfyui; using placeholder video."
        _placeholder_video(raw_path, duration_seconds, w, h, title_file)
        return raw_path, VideoBackend.PLACEHOLDER, msg

    bases = comfy_base_urls(cfg)
    base_url = pick_healthy_comfy_base_url(cfg)
    if not base_url:
        joined = ", ".join(bases) if bases else "(none configured)"
        msg = (
            f"No ComfyUI worker responded at: {joined}. "
            "Start workers with bash scripts/start_all.sh (set COMFYUI_MULTI_GPU=true for 2 GPUs) "
            "or switch VIDEO_BACKEND=placeholder."
        )
        logger.error(msg)
        _placeholder_video(raw_path, duration_seconds, w, h, title_file)
        return raw_path, VideoBackend.PLACEHOLDER, msg

    client = ComfyUIClient(base_url)

    try:
        workflow = json.loads(wf_path.read_text(encoding="utf-8"))
        if not isinstance(workflow, dict):
            raise ValueError("Workflow root must be a JSON object")

        injected = inject_prompts(
            workflow,
            prompt_node_id=prompt_node_id,
            positive=master_prompt,
            negative_prompt_node_id=wmap.negative_prompt_node_id if wmap else None,
            negative=negative_prompt,
            width=w,
            height=h,
            width_node_id=wmap.width_node_id if wmap else None,
            height_node_id=wmap.height_node_id if wmap else None,
        )
        injected = strip_meta_keys(injected)

        pid = client.queue_prompt(injected)
        logger.info("ComfyUI queued prompt_id={}", pid)
        result = client.wait_for_completion(pid, cfg.comfyui.timeout_seconds)
        tmp_dir = output_dir / "_comfy_downloads"
        files = client.download_outputs(result, tmp_dir)
        if not files:
            raise RuntimeError("ComfyUI returned no output files to download.")

        # Prefer first mp4-ish output
        mp4s = [Path(f) for f in files if Path(f).suffix.lower() == ".mp4"]
        chosen = mp4s[0] if mp4s else Path(files[0])
        shutil.copy2(chosen, raw_path)
        logger.info("ComfyUI video saved to {} (worker {})", raw_path, base_url)
        return raw_path, VideoBackend.COMFYUI, f"ComfyUI completed job {pid} on {base_url}"
    except Exception as e:
        msg = f"ComfyUI generation failed ({e}). Falling back to placeholder video."
        logger.exception(msg)
        _placeholder_video(raw_path, duration_seconds, w, h, title_file)
        return raw_path, VideoBackend.PLACEHOLDER, msg

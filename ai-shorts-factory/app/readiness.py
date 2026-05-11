from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from app.config import AppConfig, ModelsConfig, comfy_base_urls, load_app_config, load_models_config, project_root
from pipeline.comfy_pool import any_comfy_healthy, comfy_worker_health
from pipeline.ffmpeg_util import ffmpeg_available
from pipeline.video_generator import VideoBackend


def _comfy_models_hint() -> bool:
    """Heuristic: any sizeable model file under COMFYUI_DIR/models."""
    root = Path(os.environ.get("COMFYUI_DIR", "/workspace/ComfyUI")) / "models"
    if not root.is_dir():
        return False
    for pat in ("*.safetensors", "*.ckpt"):
        for p in root.rglob(pat):
            try:
                if p.is_file() and p.stat().st_size > 50_000_000:
                    return True
            except OSError:
                continue
    return False


def _nvidia_detected() -> bool:
    if not shutil.which("nvidia-smi"):
        return False
    try:
        subprocess.run(["nvidia-smi", "-L"], capture_output=True, check=True, timeout=5)
        return True
    except (OSError, subprocess.SubprocessError):
        return False


def readiness_snapshot(cfg: AppConfig | None = None, models: ModelsConfig | None = None) -> dict[str, Any]:
    cfg = cfg or load_app_config()
    models = models or load_models_config()
    urls = comfy_base_urls(cfg)
    health = comfy_worker_health(cfg)
    comfy_ok = any(health.values()) if urls else False
    wf = (project_root() / cfg.comfyui.default_workflow).resolve()
    wf_ok = wf.exists()
    wmap = models.workflow_map("wan_t2v") or models.workflow_map("wan_i2v")
    prompt_ok = bool(wmap and wmap.prompt_node_id)
    ff = ffmpeg_available()
    models_hint = _comfy_models_hint()
    vb = (os.environ.get("VIDEO_BACKEND") or models.video_backend or "comfyui").strip().lower()

    production_ready = bool(
        comfy_ok
        and wf_ok
        and prompt_ok
        and ff
        and models_hint
        and vb == VideoBackend.COMFYUI.value
    )

    out_dir = (project_root() / cfg.paths.outputs_dir).resolve()

    return {
        "app_running": True,
        "comfyui_connected": comfy_ok,
        "video_backend": vb,
        "gpu_detected": _nvidia_detected(),
        "ffmpeg_ok": ff,
        "workflow_file_ok": wf_ok,
        "prompt_node_configured": prompt_ok,
        "comfy_models_heuristic": models_hint,
        "outputs_dir": str(out_dir),
        "production_ready": production_ready,
        "comfyui_urls": urls,
        "comfyui_workers_detail": health,
        "comfyui_url": urls[0] if urls else cfg.comfyui.url,
    }


def readiness_markdown(snap: dict[str, Any]) -> str:
    pr = "yes" if snap.get("production_ready") else "no"
    cu = "connected" if snap.get("comfyui_connected") else "disconnected"
    workers = snap.get("comfyui_workers_detail") or {}
    wdetail = ", ".join(f"{u}: {'up' if ok else 'down'}" for u, ok in workers.items()) or "n/a"
    gpu = "detected" if snap.get("gpu_detected") else "not detected"
    lines = [
        "### System status",
        f"- **App**: running",
        f"- **ComfyUI**: {cu} ({wdetail})",
        f"- **Video backend**: `{snap.get('video_backend', '?')}`",
        f"- **GPU**: {gpu}",
        f"- **FFmpeg**: {'ok' if snap.get('ffmpeg_ok') else 'missing'}",
        f"- **Workflow file**: {'ok' if snap.get('workflow_file_ok') else 'missing'}",
        f"- **prompt_node_id**: {'configured' if snap.get('prompt_node_configured') else 'not configured'}",
        f"- **Models (heuristic)**: {'likely present' if snap.get('comfy_models_heuristic') else 'not detected / small'}",
        f"- **Output directory**: `{snap.get('outputs_dir', '')}`",
        f"- **Production ready**: **{pr}**",
    ]
    return "\n".join(lines)

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from app.config import comfy_base_urls, load_app_config, load_models_config, resolve_path
from app.version import __version__
from app.system_info import gpu_payload
from pipeline.comfy_pool import comfy_worker_health
from pipeline.orchestrator import GenerateInput, JobResult, run_pipeline

router = APIRouter()

_JOBS: dict[str, JobResult] = {}


class GenerateBody(BaseModel):
    idea: str
    duration_seconds: int = Field(15, ge=8, le=30)
    style: str = "realistic cinematic"
    language: str = "en"
    voice_mode: str = "narrator"
    music: str = "light background"


def _outputs_root() -> Path:
    cfg = load_app_config()
    return resolve_path(cfg, cfg.paths.outputs_dir)


def _safe_job_path(job_id: str) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9_\-]+", job_id):
        raise HTTPException(status_code=400, detail="Invalid job_id")
    root = _outputs_root().resolve()
    p = (root / job_id).resolve()
    try:
        p.relative_to(root)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid path") from None
    return p


@router.get("/health")
def health() -> dict[str, Any]:
    cfg = load_app_config()
    models = load_models_config()
    urls = comfy_base_urls(cfg)
    detail = comfy_worker_health(cfg)
    reachable = any(detail.values()) if urls else False
    vb = (models.video_backend or "comfyui").strip().lower()
    return {
        "status": "ok",
        "app": "ai-shorts-factory",
        "version": __version__,
        "video_backend": vb,
        "comfyui_url": urls[0] if urls else cfg.comfyui.url,
        "comfyui_urls": urls,
        "comfyui_workers_detail": detail,
        "comfyui_reachable": reachable,
    }


@router.get("/system/gpu")
def system_gpu() -> dict[str, Any]:
    return gpu_payload()


@router.post("/generate")
def generate(body: GenerateBody) -> JSONResponse:
    inp = GenerateInput(
        idea=body.idea,
        duration_seconds=body.duration_seconds,
        style=body.style,
        language=body.language,
        voice_mode=body.voice_mode,  # type: ignore[arg-type]
        music=body.music,
    )
    res = run_pipeline(inp)
    _JOBS[res.job_id] = res
    payload: dict[str, Any] = {
        "job_id": res.job_id,
        "ok": res.status == "success",
        "status": res.status,
        "output_dir": str(res.output_dir),
        "stage": res.stage,
        "message": res.message,
        "paths": res.paths or {},
    }
    if res.status == "success" and res.paths.get("final"):
        payload["final_mp4"] = res.paths["final"]
    return JSONResponse(payload)


@router.get("/jobs/{job_id}")
def job_status(job_id: str) -> dict[str, Any]:
    res = _JOBS.get(job_id)
    if not res:
        p = _safe_job_path(job_id)
        if (p / "metadata.json").exists():
            meta = json.loads((p / "metadata.json").read_text(encoding="utf-8"))
            return {"job_id": job_id, "status": "unknown", "metadata": meta, "output_dir": str(p)}
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "job_id": res.job_id,
        "status": res.status,
        "stage": res.stage,
        "message": res.message,
        "output_dir": str(res.output_dir),
        "comfy_reachable": res.comfy_reachable,
        "paths": res.paths,
        "logs_tail": res.logs[-8000:],
    }


@router.get("/outputs/{job_id}/final")
def download_final(job_id: str) -> FileResponse:
    p = _safe_job_path(job_id) / "final.mp4"
    if not p.exists():
        raise HTTPException(status_code=404, detail="final.mp4 not found")
    return FileResponse(p, media_type="video/mp4", filename="final.mp4")


@router.get("/outputs/{job_id}/metadata")
def download_metadata(job_id: str) -> JSONResponse:
    p = _safe_job_path(job_id) / "metadata.json"
    if not p.exists():
        raise HTTPException(status_code=404, detail="metadata.json not found")
    return JSONResponse(json.loads(p.read_text(encoding="utf-8")))


@router.get("/history/recent")
def recent_history(limit: int = 20) -> list[dict[str, Any]]:
    cfg = load_app_config()
    path = resolve_path(cfg, cfg.paths.outputs_dir) / "history.jsonl"
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[-limit:]
    out: list[dict[str, Any]] = []
    for ln in lines:
        try:
            out.append(json.loads(ln))
        except json.JSONDecodeError:
            continue
    return list(reversed(out))

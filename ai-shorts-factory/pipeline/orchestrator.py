from __future__ import annotations

import re
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from loguru import logger

from app.config import AppConfig, ModelsConfig, load_app_config, load_models_config, resolve_path
from app.logger import attach_job_log_sink, detach_job_log_sink
from pipeline import metadata as metadata_mod
from pipeline.prompt_builder import build_prompts, save_prompt_artifacts
from pipeline.comfy_pool import any_comfy_healthy
from pipeline.publish_packager import hashtags_from_idea, write_publish_package
from pipeline.renderer import render_final, write_captions_burned_copy
from pipeline.script_generator import generate_script, save_script
from pipeline.safety import check_prompt
from pipeline.subtitles import write_srt
from pipeline.thumbnail import generate_thumbnails
from pipeline.tts_generator import TTSGenerator, save_voiceover_text
from pipeline.video_generator import VideoBackend, generate_raw_video
from pipeline import music_generator
from pipeline.ffmpeg_util import ffmpeg_available


VoiceMode = Literal["narrator", "dialogue", "no voice"]


@dataclass
class GenerateInput:
    idea: str
    duration_seconds: int = 15
    style: str = "realistic cinematic"
    language: str = "en"
    voice_mode: VoiceMode = "narrator"
    music: str = "light background"


@dataclass
class JobResult:
    job_id: str
    output_dir: Path
    status: Literal["success", "failed", "partial"]
    message: str = ""
    stage: str = "Placeholder"
    comfy_reachable: bool = False
    paths: dict[str, str] = field(default_factory=dict)
    logs: str = ""


def _slug(s: str, max_len: int = 40) -> str:
    s = re.sub(r"[^\w\s-]", "", s, flags=re.UNICODE).strip().lower()
    s = re.sub(r"\s+", "_", s)
    return (s[:max_len] or "job").rstrip("_")


def make_job_id(idea: str) -> str:
    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    return f"{ts}_{_slug(idea)}"


def _copy_latest(final: Path, cfg: AppConfig) -> None:
    latest = resolve_path(cfg, cfg.paths.outputs_dir) / "latest"
    latest.mkdir(parents=True, exist_ok=True)
    shutil.copy2(final, latest / "final.mp4")


def _detect_stage(
    *,
    video_backend: VideoBackend,
    comfy_reachable: bool,
    prompt_node_configured: bool,
    tts_provider: str,
) -> str:
    if video_backend == VideoBackend.PLACEHOLDER or not prompt_node_configured or not comfy_reachable:
        return "Placeholder"
    if video_backend == VideoBackend.COMFYUI:
        if tts_provider in ("placeholder",):
            return "Local ComfyUI"
        return "Production"
    return "Placeholder"


def run_pipeline(
    inp: GenerateInput,
    cfg: AppConfig | None = None,
    models_cfg: ModelsConfig | None = None,
    *,
    output_dir: Path | None = None,
    job_id: str | None = None,
) -> JobResult:
    cfg = cfg or load_app_config()
    models_cfg = models_cfg or load_models_config()

    safety = check_prompt(inp.idea, cfg)
    if not safety.allowed:
        jid = job_id or make_job_id(inp.idea or "blocked")
        out = (output_dir or (resolve_path(cfg, cfg.paths.outputs_dir) / jid)).resolve()
        out.mkdir(parents=True, exist_ok=True)
        (out / "logs.txt").write_text(safety.message + "\n", encoding="utf-8")
        return JobResult(
            jid,
            out,
            "failed",
            safety.message,
            "Placeholder",
            paths={"output_dir": str(out), "logs": str(out / "logs.txt")},
        )

    job_id = job_id or make_job_id(inp.idea)
    output_dir = (output_dir or (resolve_path(cfg, cfg.paths.outputs_dir) / job_id)).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    if not ffmpeg_available():
        msg = (
            "FFmpeg is not installed or not on PATH. Install FFmpeg to generate audio/video "
            "(Ubuntu: sudo apt install ffmpeg)."
        )
        (output_dir / "logs.txt").write_text(msg + "\n", encoding="utf-8")
        history_path = resolve_path(cfg, cfg.paths.outputs_dir) / "history.jsonl"
        metadata_mod.append_history(history_path, job_id, inp.idea, "", "failed")
        return JobResult(
            job_id,
            output_dir,
            "failed",
            msg,
            "Placeholder",
            paths={"output_dir": str(output_dir), "logs": str(output_dir / "logs.txt")},
        )

    sink_id = attach_job_log_sink(output_dir)
    try:
        logger.info("Job {} started", job_id)
        if safety.public_figure_warning and safety.message:
            logger.warning("Safety note: {}", safety.message)

        user_input = {
            "idea": inp.idea,
            "duration_seconds": inp.duration_seconds,
            "style": inp.style,
            "language": inp.language,
            "voice_mode": inp.voice_mode,
            "music": inp.music,
        }

        script = generate_script(
            inp.idea,
            inp.duration_seconds,
            inp.style,
            inp.language,
            inp.voice_mode,
            provider=cfg.script.provider,
        )
        save_script(output_dir / "script.json", script)

        built = build_prompts(script, inp.style, inp.duration_seconds)
        save_prompt_artifacts(output_dir, built)

        voice_text = script.get("voiceover_text") or script.get("caption_text") or inp.idea
        if inp.voice_mode == "no voice":
            voice_text = ""

        save_voiceover_text(output_dir / "voiceover.txt", voice_text)

        tts = TTSGenerator(cfg)
        tts.generate(
            voice_text,
            output_dir / "voice.wav",
            voice=cfg.tts.voice,
            voice_mode=inp.voice_mode,
        )

        music_generator.generate_music(cfg, output_dir / "music.wav", float(inp.duration_seconds), inp.music)

        sub_text = voice_text or script.get("caption_text") or inp.idea
        write_srt(output_dir / "subtitles.srt", sub_text, float(inp.duration_seconds))
        # Alias for publishing checklist
        shutil.copy2(output_dir / "subtitles.srt", output_dir / "captions.srt")

        raw_path, vbackend, vmsg = generate_raw_video(
            cfg,
            models_cfg,
            output_dir,
            master_prompt=built["master_prompt"],
            negative_prompt=built["negative_prompt"],
            duration_seconds=inp.duration_seconds,
        )
        logger.info("Video step: {} ({})", vbackend.value, vmsg)

        comfy_reachable = any_comfy_healthy(cfg)
        wmap = models_cfg.workflow_map("wan_t2v") or models_cfg.workflow_map("wan_i2v")
        prompt_node_configured = bool(wmap and wmap.prompt_node_id)

        burn = bool(cfg.subtitles.enabled and cfg.subtitles.burn_in)
        final = render_final(cfg, output_dir, burn_subtitles=burn)
        write_captions_burned_copy(output_dir)

        title = str(script.get("title") or "AI Short")
        desc = (
            f"A fictional AI-generated short based on user idea. Style: {inp.style}. "
            f"{script.get('caption_text','')}".strip()
        )
        tags = hashtags_from_idea(inp.idea, inp.style)
        write_publish_package(output_dir, title=title, description=desc, hashtags=tags, ai_generated=True)

        generate_thumbnails(final, output_dir, title=title)

        stage = _detect_stage(
            video_backend=vbackend,
            comfy_reachable=comfy_reachable,
            prompt_node_configured=prompt_node_configured,
            tts_provider=cfg.tts.provider,
        )

        models_info = {
            "video_backend": models_cfg.video_backend,
            "tts_provider": cfg.tts.provider,
            "music_provider": cfg.music.provider,
            "pipeline_stage": stage,
            "comfy_reachable": comfy_reachable,
            "video_message": vmsg,
        }

        outputs_map = {
            "script": "script.json",
            "prompt": "prompt.txt",
            "voice": "voice.wav",
            "music": "music.wav",
            "raw_video": "raw_video.mp4",
            "subtitles": "subtitles.srt",
            "captions": "captions.srt",
            "final": "final.mp4",
            "captions_burned_in": "captions_burned_in.mp4",
            "thumbnail": "thumbnail.png",
            "thumbnail_clean": "thumbnail_clean.png",
            "title": "title.txt",
            "description": "description.txt",
            "hashtags": "hashtags.txt",
            "publish_package": "publish_package.json",
            "metadata": "metadata.json",
        }

        metadata_mod.write_metadata(
            output_dir / "metadata.json",
            job_id,
            user_input,
            models_info,
            outputs_map,
            ai_generated=True,
        )

        history_path = resolve_path(cfg, cfg.paths.outputs_dir) / "history.jsonl"
        metadata_mod.append_history(history_path, job_id, inp.idea, str(final), "success")
        _copy_latest(final, cfg)

        logs = (output_dir / "logs.txt").read_text(encoding="utf-8", errors="replace")
        return JobResult(
            job_id=job_id,
            output_dir=output_dir,
            status="success",
            message="OK",
            stage=stage,
            comfy_reachable=comfy_reachable,
            paths={k: str(output_dir / v) for k, v in outputs_map.items()},
            logs=logs,
        )
    except Exception as e:
        logger.exception("Job failed: {}", e)
        logf = output_dir / "logs.txt"
        prev = logf.read_text(encoding="utf-8", errors="replace") if logf.exists() else ""
        logf.write_text(prev + f"\nFATAL: {e}\n", encoding="utf-8")

        history_path = resolve_path(cfg, cfg.paths.outputs_dir) / "history.jsonl"
        metadata_mod.append_history(history_path, job_id, inp.idea, "", "failed")
        logs = ""
        if (output_dir / "logs.txt").exists():
            logs = (output_dir / "logs.txt").read_text(encoding="utf-8", errors="replace")
        partial: dict[str, str] = {"output_dir": str(output_dir), "logs": str(output_dir / "logs.txt")}
        for fname, key in (
            ("script.json", "script"),
            ("final.mp4", "final"),
            ("metadata.json", "metadata"),
            ("publish_package.json", "publish_package"),
        ):
            p = output_dir / fname
            if p.exists():
                partial[key] = str(p)
        return JobResult(
            job_id=job_id,
            output_dir=output_dir,
            status="failed",
            message=str(e),
            stage="Placeholder",
            comfy_reachable=False,
            paths=partial,
            logs=logs,
        )
    finally:
        detach_job_log_sink(sink_id)


def _batch_max_parallel(cfg: AppConfig, models_cfg: ModelsConfig) -> int:
    import os

    from app.config import comfy_base_urls
    from pipeline.comfy_client import ComfyUIClient

    w = int(os.environ.get("COMFYUI_WORKERS", str(cfg.comfyui.workers)))
    w = max(1, w)
    backend = (models_cfg.video_backend or "").strip().lower()
    if backend != "comfyui":
        return w
    urls = comfy_base_urls(cfg)
    healthy = sum(1 for u in urls if ComfyUIClient(u).health_check())
    cap = max(1, healthy)
    return max(1, min(w, cap))


def run_batch(lines: list[str], cfg: AppConfig | None = None) -> Path:
    from concurrent.futures import ThreadPoolExecutor

    cfg = cfg or load_app_config()
    models_cfg = load_models_config()
    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    batch_root = resolve_path(cfg, cfg.paths.outputs_dir) / f"batch_{ts}"
    batch_root.mkdir(parents=True, exist_ok=True)
    summary: list[dict[str, Any]] = []

    tasks: list[tuple[int, str, Path, str]] = []
    job_idx = 0
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        job_idx += 1
        sub = batch_root / f"job_{job_idx:03d}"
        jid = f"{ts}_batch_{job_idx:03d}"
        tasks.append((job_idx, line, sub, jid))

    max_p = _batch_max_parallel(cfg, models_cfg)
    max_workers = max(1, min(max_p, len(tasks))) if tasks else 1

    def _run_one(t: tuple[int, str, Path, str]) -> tuple[int, JobResult]:
        jidx, idea, sub, jid = t
        res = run_pipeline(
            GenerateInput(idea=idea),
            cfg=cfg,
            models_cfg=models_cfg,
            output_dir=sub,
            job_id=jid,
        )
        return jidx, res

    if len(tasks) <= 1 or max_workers <= 1:
        results = [_run_one(t) for t in tasks]
    else:
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            results = list(pool.map(_run_one, tasks))

    for job_idx, res in sorted(results, key=lambda x: x[0]):
        summary.append({"job": job_idx, "job_id": res.job_id, "status": res.status, "path": str(res.output_dir)})

    import csv, json as json_lib

    csv_path = batch_root / "batch_summary.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["job", "job_id", "status", "path"])
        w.writeheader()
        for row in summary:
            w.writerow(row)
    (batch_root / "batch_summary.json").write_text(json_lib.dumps(summary, indent=2), encoding="utf-8")
    return batch_root

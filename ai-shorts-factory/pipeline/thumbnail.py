from __future__ import annotations

import shutil
from pathlib import Path

from loguru import logger

from pipeline.ffmpeg_util import ffprobe_duration_seconds, run_ffmpeg


def _fallback_solid_png(path: Path, w: int = 1080, h: int = 1920) -> None:
    """Single-color frame if extraction from video fails."""
    path.parent.mkdir(parents=True, exist_ok=True)
    run_ffmpeg(
        [
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"color=c=#1a1a2e:s={w}x{h}",
            "-frames:v",
            "1",
            path.name,
        ],
        cwd=path.parent,
    )


def generate_thumbnails(final_video: Path, output_dir: Path, title: str) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    clean = output_dir / "thumbnail_clean.png"
    titled = output_dir / "thumbnail.png"
    title_file = output_dir / "thumb_title.txt"
    safe = (title or "Short")[:60].replace("\n", " ")
    title_file.write_text(safe, encoding="utf-8")

    duration = ffprobe_duration_seconds(final_video)
    if duration <= 0:
        duration = max(0.5, 3.0)
    ss = max(0.0, min(duration * 0.5, max(0.0, duration - 0.1)))

    try:
        run_ffmpeg(
            ["-y", "-ss", str(ss), "-i", str(final_video), "-vframes", "1", clean.name],
            cwd=output_dir,
        )
    except Exception as e:
        logger.warning("Thumbnail frame extract failed ({}); using solid fallback", e)
        _fallback_solid_png(clean)

    if not clean.exists():
        _fallback_solid_png(clean)

    try:
        run_ffmpeg(
            [
                "-y",
                "-i",
                clean.name,
                "-vf",
                (
                    f"scale=1080:1920:force_original_aspect_ratio=decrease,"
                    f"pad=1080:1920:(ow-iw)/2:(oh-ih)/2,"
                    f"drawtext=textfile={title_file.name}:fontcolor=white:fontsize=56:"
                    f"box=1:boxcolor=black@0.5:boxborderw=16:x=(w-text_w)/2:y=h*0.78"
                ),
                titled.name,
            ],
            cwd=output_dir,
        )
    except Exception as e:
        logger.warning("Thumbnail titled overlay failed ({}); copying clean frame", e)
        shutil.copy2(clean, titled)

    if not titled.exists():
        shutil.copy2(clean, titled)

    logger.info("Thumbnails written: {}, {}", clean, titled)
    return clean, titled

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Sequence

from loguru import logger


def ffmpeg_bin() -> str:
    return shutil.which("ffmpeg") or "ffmpeg"


def ffprobe_bin() -> str:
    return shutil.which("ffprobe") or "ffprobe"


def run_ffmpeg(args: Sequence[str], cwd: Path | None = None) -> None:
    exe = ffmpeg_bin()
    if shutil.which(exe) is None and exe == "ffmpeg":
        raise RuntimeError(
            "FFmpeg is not installed or not on PATH. Install FFmpeg and retry "
            "(Ubuntu: sudo apt install ffmpeg; Windows: install ffmpeg and add to PATH)."
        )
    cmd = [exe, *args]
    logger.debug("FFmpeg: {}", " ".join(cmd))
    proc = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()
        raise RuntimeError(f"FFmpeg failed ({proc.returncode}): {err}")


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def ffprobe_duration_seconds(path: Path) -> float:
    cmd = [
        ffprobe_bin(),
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        return 0.0
    try:
        return float((proc.stdout or "0").strip())
    except ValueError:
        return 0.0

#!/usr/bin/env python3
"""
Production smoke test: one full placeholder generation + artifact + ffprobe checks.
Does not require ComfyUI. Expects FFmpeg/ffprobe on PATH.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Must be set before project imports that read models config.
os.environ.setdefault("VIDEO_BACKEND", "placeholder")

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

REQUIRED_FILES = (
    "final.mp4",
    "thumbnail.png",
    "title.txt",
    "description.txt",
    "hashtags.txt",
    "subtitles.srt",
    "publish_package.json",
    "metadata.json",
    "logs.txt",
)

PKG_KEYS = ("title", "description", "hashtags", "platforms", "ai_generated", "manual_upload_ready")

FFMPEG_HINT = "FFmpeg is missing. On Ubuntu run: sudo apt install -y ffmpeg"


def _which(name: str) -> str | None:
    return shutil.which(name)


def _fail(msg: str, code: int = 1) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def _run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def _ffprobe_video_size(video: Path) -> tuple[int, int]:
    cmd = [
        _which("ffprobe") or "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height",
        "-of",
        "csv=p=0",
        str(video),
    ]
    p = _run(cmd)
    if p.returncode != 0:
        _fail(f"ffprobe failed on {video}: {p.stderr or p.stdout}")
    line = (p.stdout or "").strip()
    if not line or "," not in line:
        _fail(f"ffprobe returned unexpected output: {line!r}")
    w_s, h_s = line.split(",", 1)
    return int(w_s.strip()), int(h_s.strip())


def _ffprobe_playable(video: Path) -> None:
    """Ensure container has video stream and positive duration."""
    exe = _which("ffprobe") or "ffprobe"
    p = _run(
        [
            exe,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(video),
        ]
    )
    if p.returncode != 0:
        _fail(f"ffprobe (duration) failed: {p.stderr or p.stdout}")
    try:
        dur = float((p.stdout or "0").strip())
    except ValueError:
        dur = 0.0
    if dur <= 0:
        _fail(f"final.mp4 has no positive duration (got {dur!r})")


def main() -> int:
    if not _which("ffmpeg"):
        _fail(FFMPEG_HINT)
    if not _which("ffprobe"):
        _fail("ffprobe is missing. Install ffmpeg (includes ffprobe). On Ubuntu: sudo apt install -y ffmpeg")

    venv = ROOT / ".venv"
    if not venv.is_dir():
        _fail(f"Python venv not found at {venv}. Create with: python3 -m venv .venv && pip install -r requirements.txt")

    from app.config import load_app_config
    from pipeline.orchestrator import GenerateInput, run_pipeline

    print("VIDEO_BACKEND=", os.environ.get("VIDEO_BACKEND", "placeholder"))
    print("Running one full placeholder pipeline…")

    res = run_pipeline(
        GenerateInput(
            idea="A 15-second fake commercial for a programmer energy drink, funny meme style, vertical video.",
            duration_seconds=15,
            style="funny meme",
            language="en",
            voice_mode="narrator",
            music="light background",
        ),
        load_app_config(),
    )

    out = res.output_dir
    print("output_dir:", out)

    if res.status != "success":
        _fail(f"Pipeline status={res.status!r} message={res.message!r}")

    missing = [f for f in REQUIRED_FILES if not (out / f).is_file()]
    if missing:
        _fail(f"Missing files: {missing}")

    final = out / "final.mp4"
    _ffprobe_playable(final)

    w, h = _ffprobe_video_size(final)
    if w != 1080 or h != 1920:
        _fail(f"Expected video 1080x1920, got {w}x{h}")

    pkg_path = out / "publish_package.json"
    try:
        pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        _fail(f"Invalid publish_package.json: {e}")

    for k in PKG_KEYS:
        if k not in pkg:
            _fail(f"publish_package.json missing key: {k!r}")

    if not isinstance(pkg.get("hashtags"), list):
        _fail("publish_package.json: hashtags must be a list")

    if not isinstance(pkg.get("platforms"), dict):
        _fail("publish_package.json: platforms must be an object")

    print()
    print("PASSED: generated playable vertical final.mp4 and complete publish package.")
    print("final_mp4:", final.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

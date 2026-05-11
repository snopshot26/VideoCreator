from __future__ import annotations

import random
from pathlib import Path

from loguru import logger

from app.config import AppConfig, resolve_path
from pipeline.ffmpeg_util import run_ffmpeg

_STYLE_FILES = {
    "none": [],
    "light background": ["calm", "soft", "ambient"],
    "dramatic": ["dramatic", "epic", "cinematic"],
    "funny": ["funny", "quirky", "comedy"],
    "city ambience": ["city", "street", "urban", "traffic"],
}


def generate_music(
    cfg: AppConfig,
    output_path: Path,
    duration_seconds: float,
    music_selection: str,
) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not cfg.music.enabled or music_selection.lower() == "none":
        run_ffmpeg(
            [
                "-y",
                "-f",
                "lavfi",
                "-i",
                "anullsrc=r=44100:cl=stereo",
                "-t",
                str(duration_seconds),
                str(output_path),
            ]
        )
        return output_path

    music_dir = resolve_path(cfg, cfg.paths.assets_music_dir)
    picked = _pick_local_file(music_dir, music_selection)
    if picked:
        run_ffmpeg(["-y", "-i", str(picked), "-t", str(duration_seconds), str(output_path)])
        return output_path

    # Synthetic tone via FFmpeg (no copyrighted material)
    label = music_selection.lower()
    if "city" in label or "ambience" in label:
        freq = "120"
        vol = "0.04"
    elif "dramatic" in label:
        freq = "110"
        vol = "0.05"
    elif "funny" in label:
        freq = "330"
        vol = "0.03"
    else:
        freq = "220"
        vol = "0.03"

    run_ffmpeg(
        [
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency={freq}:sample_rate=48000",
            "-filter:a",
            f"volume={vol}",
            "-t",
            str(duration_seconds),
            str(output_path),
        ]
    )
    logger.info("Generated synthetic music bed for style={}", music_selection)
    return output_path


def _pick_local_file(music_dir: Path, music_selection: str) -> Path | None:
    if not music_dir.exists():
        return None
    files = [p for p in music_dir.rglob("*") if p.suffix.lower() in {".wav", ".mp3", ".ogg", ".flac"}]
    if not files:
        return None
    hints = _STYLE_FILES.get(music_selection.lower(), [])
    scored: list[tuple[int, Path]] = []
    for p in files:
        name = p.stem.lower()
        score = sum(1 for h in hints if h in name)
        scored.append((score, p))
    scored.sort(key=lambda x: (-x[0], x[1].name))
    pool = [p for s, p in scored if s > 0] or [p for _, p in scored]
    return random.choice(pool)

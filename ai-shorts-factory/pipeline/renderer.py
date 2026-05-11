from __future__ import annotations

import shutil
from pathlib import Path

from loguru import logger

from app.config import AppConfig
from pipeline.ffmpeg_util import ffmpeg_available, run_ffmpeg


def render_final(
    cfg: AppConfig,
    output_dir: Path,
    *,
    burn_subtitles: bool,
) -> Path:
    if not ffmpeg_available():
        raise RuntimeError("FFmpeg is not installed. Run: sudo apt install ffmpeg")

    raw = output_dir / "raw_video.mp4"
    voice = output_dir / "voice.wav"
    music = output_dir / "music.wav"
    srt = output_dir / "subtitles.srt"
    final = output_dir / "final.mp4"

    if not raw.exists():
        raise FileNotFoundError(str(raw))
    if not voice.exists():
        raise FileNotFoundError(str(voice))

    w, h = cfg.video.final_width, cfg.video.final_height

    vchain = (
        f"[0:v]scale={w}:{h}:force_original_aspect_ratio=increase,"
        f"crop={w}:{h}"
    )
    # Relative SRT path + cwd=output_dir avoids Windows drive-letter / escaping issues in libavfilter.
    if burn_subtitles and srt.exists():
        vchain += ",subtitles=subtitles.srt"
    vchain += "[vout]"

    if music.exists():
        vol = float(cfg.music.volume)
        achain = (
            f"[1:a]volume=1.0[a1];[2:a]volume={vol}[a2];"
            f"[a1][a2]amix=inputs=2:duration=longest:dropout_transition=0[aout]"
        )
        inputs = ["-y", "-i", str(raw), "-i", str(voice), "-i", str(music)]
    else:
        achain = "[1:a]volume=1.0[aout]"
        inputs = ["-y", "-i", str(raw), "-i", str(voice)]

    fc = f"{vchain};{achain}"
    args = inputs + [
        "-filter_complex",
        fc,
        "-map",
        "[vout]",
        "-map",
        "[aout]",
        "-c:v",
        cfg.render.codec,
        "-crf",
        str(cfg.render.crf),
        "-preset",
        cfg.render.preset,
        "-c:a",
        "aac",
        "-b:a",
        cfg.render.audio_bitrate,
        "-shortest",
        str(final),
    ]

    logger.info("Rendering final.mp4 via FFmpeg (single filter graph)")
    run_ffmpeg(args, cwd=output_dir)
    return final


def write_captions_burned_copy(output_dir: Path) -> Path:
    final = output_dir / "final.mp4"
    cap = output_dir / "captions_burned_in.mp4"
    shutil.copy2(final, cap)
    return cap

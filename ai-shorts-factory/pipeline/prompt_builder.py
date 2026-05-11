from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from loguru import logger

DEFAULT_NEGATIVE = (
    "blurry, low quality, distorted face, extra fingers, unreadable text, watermark, logo, "
    "broken anatomy, duplicated people, flickering, bad lighting"
)


def build_prompts(script: dict[str, Any], style: str, duration_seconds: int) -> dict[str, Any]:
    scenes = script.get("visual_scenes") or []
    scene_prompts: list[dict[str, Any]] = []
    for s in scenes:
        desc = s.get("description", "")
        prompt = (
            f"Vertical 9:16 {style} video, {desc}, expressive characters, shallow depth of field, "
            f"high detail, social media short, {duration_seconds} seconds, smooth camera motion."
        )
        scene_prompts.append({"scene": s.get("scene"), "prompt": prompt.strip()})

    master = " ".join(p["prompt"] for p in scene_prompts) if scene_prompts else (
        f"Vertical 9:16 {style} cinematic social media short, {duration_seconds}s, high detail."
    )
    return {
        "master_prompt": master.strip(),
        "negative_prompt": DEFAULT_NEGATIVE,
        "scene_prompts": scene_prompts,
    }


def save_prompt_artifacts(output_dir: Path, built: dict[str, Any]) -> None:
    (output_dir / "prompt.txt").write_text(built["master_prompt"] + "\n", encoding="utf-8")
    (output_dir / "negative_prompt.txt").write_text(built["negative_prompt"] + "\n", encoding="utf-8")
    (output_dir / "scene_prompts.json").write_text(
        json.dumps(built["scene_prompts"], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    logger.info("Saved prompt.txt, negative_prompt.txt, scene_prompts.json")

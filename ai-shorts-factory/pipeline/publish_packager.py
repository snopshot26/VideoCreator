from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def hashtags_from_idea(idea: str, style: str) -> list[str]:
    base = ["shorts", "tiktok", "reels", "aivideo", "vertical"]
    if "funny" in style.lower() or "meme" in style.lower():
        base += ["comedy", "meme"]
    if "documentary" in style.lower():
        base += ["documentary", "story"]
    if "commercial" in style.lower():
        base += ["ad", "commercial"]
    return list(dict.fromkeys(base))[:12]


def write_publish_package(
    output_dir: Path,
    *,
    title: str,
    description: str,
    hashtags: list[str],
    ai_generated: bool = True,
) -> Path:
    tags_line = " ".join(f"#{t.lstrip('#')}" for t in hashtags)

    (output_dir / "title.txt").write_text(title.strip() + "\n", encoding="utf-8")
    (output_dir / "description.txt").write_text(description.strip() + "\n", encoding="utf-8")
    (output_dir / "hashtags.txt").write_text(tags_line.strip() + "\n", encoding="utf-8")

    pkg: dict[str, Any] = {
        "title": title.strip(),
        "description": description.strip(),
        "hashtags": [t.lstrip("#") for t in hashtags],
        "platforms": {
            "youtube_shorts": {
                "recommended_title": title.strip(),
                "recommended_description": f"{description.strip()} {tags_line}".strip(),
                "status": "ready_for_manual_upload",
            },
            "tiktok": {
                "recommended_caption": f"{title.strip()} 😂 {tags_line}".strip(),
                "status": "ready_for_manual_upload",
            },
            "instagram_reels": {
                "recommended_caption": f"{description.strip()} {tags_line}".strip(),
                "status": "ready_for_manual_upload",
            },
        },
        "ai_generated": ai_generated,
        "manual_upload_ready": True,
        "requires_manual_platform_review": True,
    }
    path = output_dir / "publish_package.json"
    path.write_text(json.dumps(pkg, indent=2, ensure_ascii=False), encoding="utf-8")
    return path

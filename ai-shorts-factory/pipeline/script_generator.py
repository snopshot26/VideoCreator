from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Literal

from loguru import logger

VoiceMode = Literal["narrator", "dialogue", "no voice"]


def _slug_title(idea: str, max_len: int = 48) -> str:
    s = re.sub(r"[^\w\s-]", "", idea, flags=re.UNICODE)
    s = re.sub(r"\s+", " ", s).strip()
    if not s:
        s = "short"
    return s[:max_len].title()


def _lines_for_duration(duration: int, max_lines: int = 6) -> int:
    if duration <= 10:
        return 3
    if duration <= 18:
        return 4
    return min(max_lines, 6)


def generate_script(
    idea: str,
    duration_seconds: int,
    style: str,
    language: str,
    voice_mode: VoiceMode,
    provider: str = "template",
) -> dict[str, Any]:
    """Build script JSON from user idea (template provider for MVP)."""
    _ = provider
    title = _slug_title(idea)
    n = _lines_for_duration(duration_seconds)
    per = max(2, duration_seconds // max(n, 1))

    if voice_mode == "dialogue":
        dialogue = [
            {"speaker": "A", "text": _short_line(idea, language, 0)},
            {"speaker": "B", "text": _short_line(idea, language, 1)},
        ]
        while len(dialogue) < n:
            idx = len(dialogue)
            dialogue.append(
                {
                    "speaker": "A" if idx % 2 == 0 else "B",
                    "text": _short_line(idea, language, idx),
                }
            )
        voiceover_text = " ".join(f'{d["speaker"]}: {d["text"]}' for d in dialogue)
        characters = [
            {"name": "A", "description": "First speaker (fictional)"},
            {"name": "B", "description": "Second speaker (fictional)"},
        ]
    else:
        dialogue = []
        characters = [{"name": "Narrator", "description": "Neutral fictional narrator voice"}]
        parts = [_narration_chunk(idea, language, i) for i in range(n)]
        voiceover_text = " ".join(parts)

    visual_scenes: list[dict[str, Any]] = []
    scene_count = min(4, max(2, n))
    for i in range(scene_count):
        visual_scenes.append(
            {
                "scene": i + 1,
                "duration": max(2, duration_seconds // scene_count),
                "description": _scene_desc(idea, style, language, i),
            }
        )

    caption = _caption(idea, language)

    script = {
        "title": title,
        "duration_seconds": duration_seconds,
        "language": language,
        "characters": characters,
        "dialogue": dialogue,
        "visual_scenes": visual_scenes,
        "voiceover_text": voiceover_text,
        "caption_text": caption,
    }
    logger.info("Script generated (template): title={}", title)
    return script


def _short_line(idea: str, language: str, idx: int) -> str:
    templates = {
        "en": [
            "Wait — this can't be real.",
            "Let me explain in thirty seconds.",
            "That's exactly the problem.",
            "Okay, but hear me out.",
            "This escalated quickly.",
            "And that's the twist.",
        ],
        "ru": [
            "Погоди — это несерьёзно.",
            "Объясню за полминуты.",
            "Вот в чём дело.",
            "Слушай внимательно.",
            "Это быстро зашло слишком далеко.",
            "Вот такой поворот.",
        ],
        "tr": [
            "Dur — bu ciddi olamaz.",
            "Otuz saniyede anlatayım.",
            "Sorun tam olarak bu.",
            "Ama bir dakika.",
            "Bu çabuk çığırından çıktı.",
            "İşte sürpriz burada.",
        ],
    }
    pool = templates.get(language, templates["en"])
    base = pool[idx % len(pool)]
    snippet = idea.strip()[:40].replace("\n", " ")
    if idx == 0 and snippet:
        return f"{base} ({snippet})"[:120]
    return base


def _narration_chunk(idea: str, language: str, idx: int) -> str:
    intro = {
        "en": "Here's a quick vertical story:",
        "ru": "Короткая вертикальная история:",
        "tr": "Kısa dikey bir hikâye:",
    }
    if idx == 0:
        return f'{intro.get(language, intro["en"])} {idea.strip()[:160]}'
    return _short_line(idea, language, idx)


def _scene_desc(idea: str, style: str, language: str, idx: int) -> str:
    base = idea.strip()[:120]
    return (
        f"Vertical 9:16 {style} shot #{idx + 1}, cinematic social media short. "
        f"Subject: {base}. Dynamic camera, high detail, coherent lighting."
    )


def _caption(idea: str, language: str) -> str:
    if language == "ru":
        return idea.strip()[:140] or "Когда идея зашла слишком далеко…"
    if language == "tr":
        return idea.strip()[:140] or "Fikir bir anda büyüdüğünde…"
    return idea.strip()[:140] or "When the idea escalates way too fast…"


def save_script(path: Path, script: dict[str, Any]) -> None:
    path.write_text(json.dumps(script, indent=2, ensure_ascii=False), encoding="utf-8")

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

from loguru import logger


def _split_chunks(text: str, max_chars: int = 42) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks: list[str] = []
    buf = ""
    for s in sentences:
        if not s:
            continue
        if len(buf) + len(s) + 1 <= max_chars:
            buf = f"{buf} {s}".strip()
        else:
            if buf:
                chunks.append(buf)
            buf = s
    if buf:
        chunks.append(buf)
    # Hard-split very long single tokens
    out: list[str] = []
    for c in chunks:
        while len(c) > max_chars:
            out.append(c[:max_chars])
            c = c[max_chars:].lstrip()
        if c:
            out.append(c)
    return out


def _fmt_ts(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    whole = int(s)
    ms = int(round((s - whole) * 1000))
    return f"{h:02d}:{m:02d}:{whole:02d},{ms:03d}"


def build_srt(text: str, duration_seconds: float) -> str:
    chunks = _split_chunks(text)
    if not chunks:
        chunks = [" "]
    n = len(chunks)
    step = max(duration_seconds / n, 0.5)
    lines: list[str] = []
    for i, chunk in enumerate(chunks, start=1):
        t0 = (i - 1) * step
        t1 = min(duration_seconds, i * step)
        lines.append(str(i))
        lines.append(f"{_fmt_ts(t0)} --> {_fmt_ts(t1)}")
        lines.append(chunk)
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def write_srt(path: Path, text: str, duration_seconds: float) -> None:
    path.write_text(build_srt(text, duration_seconds), encoding="utf-8")
    logger.info("Wrote subtitles {}", path)

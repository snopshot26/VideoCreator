from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def write_metadata(
    path: Path,
    job_id: str,
    user_input: dict[str, Any],
    models: dict[str, Any],
    outputs: dict[str, str],
    ai_generated: bool = True,
) -> None:
    payload = {
        "job_id": job_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input": user_input,
        "models": models,
        "outputs": outputs,
        "ai_generated": ai_generated,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def append_history(
    history_path: Path,
    job_id: str,
    idea: str,
    final_path: str,
    status: str,
) -> None:
    history_path.parent.mkdir(parents=True, exist_ok=True)
    line = {
        "job_id": job_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "idea": idea,
        "final_path": final_path,
        "status": status,
    }
    with history_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(line, ensure_ascii=False) + "\n")

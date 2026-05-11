from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger

from app.config import load_app_config, resolve_path


def setup_logging() -> None:
    cfg = load_app_config()
    log_dir = resolve_path(cfg, cfg.paths.logs_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "app.log"

    logger.remove()
    logger.add(
        sys.stderr,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | {message}",
    )
    logger.add(
        log_file,
        rotation="10 MB",
        retention="14 days",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    )


def attach_job_log_sink(job_output_dir: Path) -> int:
    """Append loguru records to outputs/{job_id}/logs.txt. Returns sink id for removal."""
    log_path = job_output_dir / "logs.txt"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    def sink(message) -> None:
        record = message.record
        line = f"{record['time']} | {record['level'].name} | {record['message']}\n"
        with log_path.open("a", encoding="utf-8") as f:
            f.write(line)

    return logger.add(sink, level="DEBUG", format="{message}")


def detach_job_log_sink(sink_id: int) -> None:
    try:
        logger.remove(sink_id)
    except ValueError:
        pass

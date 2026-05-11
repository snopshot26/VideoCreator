#!/usr/bin/env python3
"""Verify required project files exist (for CI / pre-deploy checks)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

REQUIRED_DIRS = [
    "app",
    "pipeline",
    "scripts",
    "config",
    "workflows",
    "platforms",
    "docs",
    "outputs",
    "logs",
    "assets/music",
]

REQUIRED_FILES = [
    "scripts/setup_vast.sh",
    "scripts/start_all.sh",
    "scripts/stop_all.sh",
    "scripts/restart_all.sh",
    "scripts/status.sh",
    "scripts/tail_logs.sh",
    "scripts/install_comfyui.sh",
    "scripts/install_comfyui_custom_nodes.sh",
    "scripts/download_models.sh",
    "scripts/test_placeholder_generation.sh",
    "scripts/test_comfyui_connection.sh",
    "scripts/smoke_test_production.sh",
    "scripts/smoke_test_production.py",
    "app/webui.py",
    "app/api.py",
    "app/main.py",
    "config/default.yaml",
    "config/vast.yaml",
    "config/models.yaml",
    ".env.example",
    ".env.vast.example",
    "docs/VAST_SETUP.md",
    "docs/VAST_TEMPLATE.md",
    "docs/MODEL_DOWNLOADS.md",
    "docs/PRODUCTION_RUNBOOK.md",
]


def main() -> int:
    missing: list[str] = []
    for d in REQUIRED_DIRS:
        p = ROOT / d
        if not p.is_dir():
            missing.append(f"dir: {d}")
    for f in REQUIRED_FILES:
        p = ROOT / f
        if not p.is_file():
            missing.append(f"file: {f}")
    if missing:
        print("MISSING:", file=sys.stderr)
        for m in missing:
            print(" ", m, file=sys.stderr)
        return 1
    print("OK: structure check passed (%d dirs, %d files)" % (len(REQUIRED_DIRS), len(REQUIRED_FILES)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

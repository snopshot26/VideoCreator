from __future__ import annotations

import shutil
import subprocess
from typing import Any


def nvidia_smi_summary() -> str:
    exe = shutil.which("nvidia-smi")
    if not exe:
        return "nvidia-smi not found (no NVIDIA driver or not in PATH)."
    try:
        out = subprocess.check_output([exe], text=True, stderr=subprocess.STDOUT, timeout=5)
        lines = out.splitlines()[:20]
        return "\n".join(lines)
    except Exception as e:
        return f"nvidia-smi failed: {e}"


def ffmpeg_version_head() -> str:
    exe = shutil.which("ffmpeg")
    if not exe:
        return "ffmpeg not found in PATH."
    try:
        out = subprocess.check_output([exe, "-version"], text=True, stderr=subprocess.STDOUT, timeout=5)
        return "\n".join(out.splitlines()[:3])
    except Exception as e:
        return f"ffmpeg check failed: {e}"


def gpu_payload() -> dict[str, Any]:
    return {
        "nvidia_smi": nvidia_smi_summary(),
        "ffmpeg": ffmpeg_version_head(),
    }

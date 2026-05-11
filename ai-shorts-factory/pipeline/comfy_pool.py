"""Round-robin selection across multiple ComfyUI HTTP bases (multi-GPU workers)."""
from __future__ import annotations

import threading
from typing import Optional

from app.config import AppConfig, comfy_base_urls
from pipeline.comfy_client import ComfyUIClient

_lock = threading.Lock()
_rr_index = 0


def comfy_worker_health(cfg: AppConfig) -> dict[str, bool]:
    return {u: ComfyUIClient(u).health_check() for u in comfy_base_urls(cfg)}


def any_comfy_healthy(cfg: AppConfig) -> bool:
    return any(comfy_worker_health(cfg).values())


def pick_healthy_comfy_base_url(cfg: AppConfig) -> Optional[str]:
    """
    Pick next healthy ComfyUI base URL (round-robin among healthy workers).
    Skips workers that fail health_check. Returns None if none are up.
    """
    urls = comfy_base_urls(cfg)
    if not urls:
        return None
    global _rr_index
    with _lock:
        n = len(urls)
        for step in range(n):
            idx = (_rr_index + step) % n
            candidate = urls[idx]
            if ComfyUIClient(candidate).health_check():
                _rr_index = (idx + 1) % n
                return candidate
    return None

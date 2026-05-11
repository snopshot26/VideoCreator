#!/usr/bin/env python3
"""Download models listed in config/model_manifest.yaml (enabled + non-empty URL only)."""
from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "config" / "model_manifest.yaml"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    if not MANIFEST.exists():
        print(f"No manifest at {MANIFEST}", file=sys.stderr)
        return 0
    data = yaml.safe_load(MANIFEST.read_text(encoding="utf-8")) or {}
    models = data.get("models") or []
    for m in models:
        if not isinstance(m, dict):
            continue
        if not m.get("enabled"):
            print(f"Skip (disabled): {m.get('name')}")
            continue
        url = (m.get("url") or "").strip()
        target = Path(m.get("target_path") or "")
        if not url:
            print(f"No URL for {m.get('name')}: fill config/model_manifest.yaml manually.")
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            print(f"Exists, skip: {target}")
            continue
        print(f"Downloading {m.get('name')} -> {target}")
        try:
            import urllib.request

            partial = Path(str(target) + ".partial")
            with urllib.request.urlopen(url, timeout=600) as resp, partial.open("wb") as out:
                while True:
                    chunk = resp.read(1024 * 1024)
                    if not chunk:
                        break
                    out.write(chunk)
            partial.rename(target)
        except Exception as e:
            print(f"WARN: download failed for {m.get('name')}: {e}", file=sys.stderr)
            continue
        expected = (m.get("sha256") or "").strip()
        if expected:
            got = sha256_file(target)
            if got.lower() != expected.lower():
                print(f"WARN: sha256 mismatch for {target}; removing file.", file=sys.stderr)
                target.unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

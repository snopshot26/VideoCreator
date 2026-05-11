from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any

import requests
from loguru import logger


class ComfyUIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def health_check(self) -> bool:
        try:
            r = requests.get(f"{self.base_url}/system_stats", timeout=3)
            return r.status_code == 200
        except requests.RequestException as e:
            logger.debug("ComfyUI health_check failed: {}", e)
            return False

    def queue_prompt(self, workflow: dict[str, Any]) -> str:
        client_id = str(uuid.uuid4())
        body = {"prompt": workflow, "client_id": client_id}
        try:
            r = requests.post(f"{self.base_url}/prompt", json=body, timeout=60)
        except requests.RequestException as e:
            raise RuntimeError(f"ComfyUI connection error: {e}") from e
        if r.status_code != 200:
            raise RuntimeError(f"ComfyUI /prompt HTTP {r.status_code}: {r.text[:500]}")
        data = r.json()
        pid = data.get("prompt_id")
        if not pid:
            raise RuntimeError(f"ComfyUI did not return prompt_id: {data}")
        return str(pid)

    def wait_for_completion(self, prompt_id: str, timeout_seconds: int) -> dict[str, Any]:
        deadline = time.time() + timeout_seconds
        last_hist: dict[str, Any] = {}
        while time.time() < deadline:
            entry: dict[str, Any] | None = None
            try:
                r = requests.get(f"{self.base_url}/history/{prompt_id}", timeout=15)
                if r.status_code == 200:
                    hist = r.json()
                    if isinstance(hist, dict) and hist:
                        last_hist = hist
                        entry = hist.get(prompt_id)
                        if entry is None and "outputs" in hist:
                            entry = hist  # some builds return the record directly
                        elif entry is None:
                            entry = next(iter(hist.values()), None)
            except requests.RequestException as e:
                logger.warning("ComfyUI history poll failed: {}", e)

            if entry and entry.get("outputs"):
                return entry

            try:
                r2 = requests.get(f"{self.base_url}/history", params={"max_items": 200}, timeout=15)
                if r2.status_code == 200:
                    all_h = r2.json()
                    if isinstance(all_h, dict) and prompt_id in all_h:
                        cand = all_h[prompt_id]
                        if cand.get("outputs"):
                            return cand
            except requests.RequestException:
                pass

            time.sleep(1.0)
        raise TimeoutError(
            f"ComfyUI timed out after {timeout_seconds}s (prompt_id={prompt_id}). "
            "Increase comfyui.timeout_seconds in config/default.yaml or fix the workflow. "
            f"Last history snapshot: {last_hist!r}"
        )

    def download_outputs(self, result: dict[str, Any], output_dir: Path) -> list[str]:
        output_dir.mkdir(parents=True, exist_ok=True)
        saved: list[str] = []
        outputs = result.get("outputs") or {}
        for node_id, node_out in outputs.items():
            files = (node_out or {}).get("images") or (node_out or {}).get("gifs") or []
            for item in files:
                filename = item.get("filename")
                subfolder = item.get("subfolder", "")
                typ = item.get("type", "output")
                if not filename:
                    continue
                params = {
                    "filename": filename,
                    "type": typ,
                    "subfolder": subfolder,
                }
                url = f"{self.base_url}/view"
                r = requests.get(url, params=params, timeout=120)
                if r.status_code != 200:
                    raise RuntimeError(f"Failed to download {filename}: HTTP {r.status_code}")
                # Videos often .mp4 or images in some workflows
                ext = Path(filename).suffix.lower() or ".bin"
                out = output_dir / f"comfy_{node_id}{ext}"
                out.write_bytes(r.content)
                saved.append(str(out))
        if not saved:
            # Some workflows store videos under "videos" key (structure varies)
            for node_id, node_out in outputs.items():
                vids = (node_out or {}).get("videos") or []
                for item in vids:
                    filename = item.get("filename")
                    if not filename:
                        continue
                    params = {"filename": filename, "type": "output", "subfolder": item.get("subfolder", "")}
                    r = requests.get(f"{self.base_url}/view", params=params, timeout=300)
                    r.raise_for_status()
                    out = output_dir / filename
                    out.write_bytes(r.content)
                    saved.append(str(out))
        if not saved:
            raise RuntimeError(
                "ComfyUI returned an outputs payload but no downloadable image/video files were found. "
                "Check that your workflow writes to a Save/Video or Preview node and that the API output "
                "structure matches what this client expects."
            )
        return saved


def strip_meta_keys(workflow: dict[str, Any]) -> dict[str, Any]:
    clean: dict[str, Any] = {}
    for k, v in workflow.items():
        if str(k).startswith("_"):
            continue
        clean[k] = v
    return clean


def inject_prompts(
    workflow: dict[str, Any],
    *,
    prompt_node_id: str | None,
    positive: str,
    negative_prompt_node_id: str | None = None,
    negative: str | None = None,
    width: int | None = None,
    height: int | None = None,
    width_node_id: str | None = None,
    height_node_id: str | None = None,
) -> dict[str, Any]:
    wf = json.loads(json.dumps(workflow))  # deep copy via json
    wf = strip_meta_keys(wf)

    def set_text_node(node_id: str, text: str) -> None:
        node = wf.get(node_id)
        if not node:
            raise KeyError(f"Node {node_id} not in workflow")
        inputs = node.setdefault("inputs", {})
        if "text" in inputs:
            inputs["text"] = text
        elif "string" in inputs:
            inputs["string"] = text
        else:
            inputs["text"] = text

    if prompt_node_id:
        set_text_node(prompt_node_id, positive)
    if negative_prompt_node_id and negative is not None:
        set_text_node(negative_prompt_node_id, negative)
    if width_node_id and width is not None:
        node = wf.get(width_node_id)
        if node:
            node.setdefault("inputs", {})["width"] = width
    if height_node_id and height is not None:
        node = wf.get(height_node_id)
        if node:
            node.setdefault("inputs", {})["height"] = height
    return wf

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _load_dotenv_files() -> None:
    root = project_root()
    load_dotenv(root / ".env", override=False)
    # Vast template may only materialize .env later; example is copied in setup_vast.sh
    load_dotenv(root / ".env.vast", override=False)


_load_dotenv_files()


class ServerConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 7860


class PathsConfig(BaseModel):
    outputs_dir: str = "outputs"
    logs_dir: str = "logs"
    workflows_dir: str = "workflows"
    assets_music_dir: str = "assets/music"


class VideoConfig(BaseModel):
    default_duration_seconds: int = 15
    default_aspect_ratio: str = "9:16"
    final_width: int = 1080
    final_height: int = 1920
    fps: int = 24


class ComfyUIConfig(BaseModel):
    enabled: bool = True
    url: str = "http://127.0.0.1:8188"
    urls: list[str] = Field(default_factory=list)
    multi_gpu: bool = False
    workers: int = 1
    default_workflow: str = "workflows/wan_t2v_vertical.json"
    timeout_seconds: int = 3600


class ScriptConfig(BaseModel):
    provider: str = "template"
    language: str = "en"
    style: str = "shorts"


class TTSConfig(BaseModel):
    provider: str = "placeholder"
    voice: str = "default"
    speed: float = 1.0


class MusicConfig(BaseModel):
    enabled: bool = True
    provider: str = "placeholder"
    volume: float = 0.15


class SubtitlesConfig(BaseModel):
    enabled: bool = True
    font_size: int = 64
    position: str = "bottom"
    burn_in: bool = True


class RenderConfig(BaseModel):
    codec: str = "libx264"
    crf: int = 18
    preset: str = "medium"
    audio_bitrate: str = "192k"


class SafetyConfig(BaseModel):
    add_ai_disclaimer_metadata: bool = True
    block_illegal_content: bool = True


class PlatformUploadConfig(BaseModel):
    enabled: bool = False
    provider: str = "manual"


class AppConfig(BaseModel):
    server: ServerConfig = Field(default_factory=ServerConfig)
    paths: PathsConfig = Field(default_factory=PathsConfig)
    video: VideoConfig = Field(default_factory=VideoConfig)
    comfyui: ComfyUIConfig = Field(default_factory=ComfyUIConfig)
    script: ScriptConfig = Field(default_factory=ScriptConfig)
    tts: TTSConfig = Field(default_factory=TTSConfig)
    music: MusicConfig = Field(default_factory=MusicConfig)
    subtitles: SubtitlesConfig = Field(default_factory=SubtitlesConfig)
    render: RenderConfig = Field(default_factory=RenderConfig)
    safety: SafetyConfig = Field(default_factory=SafetyConfig)
    platform_upload: PlatformUploadConfig = Field(default_factory=PlatformUploadConfig)


class WorkflowNodeMap(BaseModel):
    file: str
    prompt_node_id: Optional[str] = None
    negative_prompt_node_id: Optional[str] = None
    width_node_id: Optional[str] = None
    height_node_id: Optional[str] = None
    duration_node_id: Optional[str] = None


class ModelsConfig(BaseModel):
    video_backend: str = "comfyui"
    workflows: dict[str, dict[str, Any]] = Field(default_factory=dict)

    def workflow_map(self, name: str) -> Optional[WorkflowNodeMap]:
        raw = self.workflows.get(name)
        if not raw:
            return None
        return WorkflowNodeMap.model_validate(raw)


def _deep_merge(base: dict, override: dict) -> dict:
    out = dict(base)
    for k, v in override.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        return {}
    return data


def comfy_base_urls(cfg: AppConfig) -> list[str]:
    """Ordered ComfyUI HTTP bases: env COMFYUI_URLS / yaml urls, else single url."""
    raw = [str(u).strip() for u in (cfg.comfyui.urls or []) if str(u).strip()]
    if raw:
        seen: set[str] = set()
        out: list[str] = []
        for u in raw:
            if u not in seen:
                seen.add(u)
                out.append(u)
        return out
    u = (cfg.comfyui.url or "").strip()
    return [u] if u else []


def load_app_config() -> AppConfig:
    root = project_root()
    default_path = root / "config" / "default.yaml"
    data = load_yaml(default_path)
    comfy_url = os.environ.get("COMFYUI_URL")
    if not comfy_url:
        port = os.environ.get("COMFYUI_PORT")
        if port:
            comfy_url = f"http://127.0.0.1:{port}"
    if comfy_url:
        if "comfyui" not in data:
            data["comfyui"] = {}
        data["comfyui"]["url"] = comfy_url

    urls_csv = (os.environ.get("COMFYUI_URLS") or "").strip()
    if urls_csv:
        if "comfyui" not in data:
            data["comfyui"] = {}
        data["comfyui"]["urls"] = [x.strip() for x in urls_csv.split(",") if x.strip()]

    mg = (os.environ.get("COMFYUI_MULTI_GPU") or "").strip().lower()
    if mg in ("1", "true", "yes"):
        if "comfyui" not in data:
            data["comfyui"] = {}
        data["comfyui"]["multi_gpu"] = True

    cw = os.environ.get("COMFYUI_WORKERS")
    if cw and cw.strip().isdigit():
        if "comfyui" not in data:
            data["comfyui"] = {}
        data["comfyui"]["workers"] = int(cw.strip())
    # CLI/env overrides (priority per Vast spec: env after yaml overlays)
    host = os.environ.get("APP_HOST")
    port = os.environ.get("APP_PORT")
    if host or port:
        if "server" not in data:
            data["server"] = {}
        if host:
            data["server"]["host"] = host
        if port:
            data["server"]["port"] = int(port)
    return AppConfig.model_validate(data)


def load_models_config() -> ModelsConfig:
    root = project_root()
    path = root / "config" / "models.yaml"
    data = load_yaml(path)
    vb = os.environ.get("VIDEO_BACKEND")
    if vb:
        data["video_backend"] = vb.strip().lower()
    return ModelsConfig.model_validate(data)


def resolve_path(cfg: AppConfig, relative: str) -> Path:
    return (project_root() / relative).resolve()

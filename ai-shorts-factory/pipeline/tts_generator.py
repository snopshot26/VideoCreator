from __future__ import annotations

from pathlib import Path
from typing import Literal

from loguru import logger

from app.config import AppConfig
from pipeline.ffmpeg_util import run_ffmpeg

Provider = Literal["placeholder", "kokoro", "external_api", "pyttsx3", "piper"]


class TTSGenerator:
    def __init__(self, cfg: AppConfig):
        self.cfg = cfg

    def generate(
        self,
        text: str,
        output_path: Path,
        voice: str = "default",
        *,
        voice_mode: str = "narrator",
    ) -> Path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        provider: Provider = self.cfg.tts.provider  # type: ignore[assignment]

        if not text.strip():
            self._silent_wav(output_path, duration_sec=float(self.cfg.video.default_duration_seconds))
            return output_path

        if provider == "pyttsx3":
            try:
                self._pyttsx3_to_wav(text, output_path, voice)
                return output_path
            except Exception as e:
                logger.warning("pyttsx3 failed ({}), falling back to silent WAV", e)
                self._silent_wav(output_path, duration_sec=max(3.0, min(30.0, len(text) / 12)))
                return output_path

        if provider == "piper":
            if self._try_piper(text, output_path, voice):
                return output_path
            logger.warning("Piper not configured or failed; using silent WAV")

        if provider in ("kokoro", "external_api"):
            logger.warning("TTS provider {} not implemented; using silent WAV", provider)

        est = max(3.0, min(30.0, len(text) / 12))
        self._silent_wav(output_path, duration_sec=est)
        return output_path

    def _silent_wav(self, output_path: Path, duration_sec: float) -> None:
        run_ffmpeg(
            [
                "-y",
                "-f",
                "lavfi",
                "-i",
                f"anullsrc=r=44100:cl=stereo",
                "-t",
                str(duration_sec),
                str(output_path),
            ]
        )

    def _pyttsx3_to_wav(self, text: str, output_path: Path, voice: str) -> None:
        import pyttsx3

        engine = pyttsx3.init()
        if voice and voice != "default":
            for v in engine.getProperty("voices"):
                if voice.lower() in (v.name or "").lower():
                    engine.setProperty("voice", v.id)
                    break
        engine.setProperty("rate", int(200 * float(self.cfg.tts.speed or 1.0)))
        tmp_mp3 = output_path.with_suffix(".tmp.mp3")
        engine.save_to_file(text, str(tmp_mp3))
        engine.runAndWait()
        if not tmp_mp3.exists():
            raise RuntimeError("pyttsx3 did not create audio file")
        run_ffmpeg(["-y", "-i", str(tmp_mp3), str(output_path)])
        tmp_mp3.unlink(missing_ok=True)

    def _try_piper(self, text: str, output_path: Path, voice: str) -> bool:
        import os
        import shutil
        import subprocess

        piper = shutil.which("piper")
        model = os.environ.get("PIPER_MODEL_PATH")
        if not piper or not model or not Path(model).exists():
            return False
        raw = output_path.with_suffix(".raw.wav")
        cmd = [piper, "--model", model, "--output_file", str(raw)]
        proc = subprocess.run(cmd, input=text.encode("utf-8"), capture_output=True)
        if proc.returncode != 0 or not raw.exists():
            return False
        run_ffmpeg(["-y", "-i", str(raw), str(output_path)])
        raw.unlink(missing_ok=True)
        return True


def save_voiceover_text(path: Path, text: str) -> None:
    path.write_text(text.strip() + "\n", encoding="utf-8")

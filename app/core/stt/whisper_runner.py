# -*- coding: utf-8 -*-
"""Whisper transcription helpers (local, offline)."""
from __future__ import annotations
import os
from pathlib import Path
from typing import Optional


def default_models_dir() -> Path:
    """Return default models directory (per-user cache)."""
    local = os.getenv("LOCALAPPDATA")
    if local:
        return Path(local) / "VoiceTransor" / "models" / "whisper"
    return Path.home() / ".cache" / "VoiceTransor" / "models" / "whisper"


def is_model_cached(model: str, models_dir: Path) -> bool:
    """Check if a given Whisper model .pt file has been cached."""
    return (models_dir / f"{model}.pt").exists()


def pick_device(choice: str) -> str:
    """
    Return device according to choice and availability.
    Supports: cpu, cuda (NVIDIA), mps (Apple Silicon), auto
    """
    try:
        import torch  # noqa: F401
        has_cuda = torch.cuda.is_available()
        has_mps = hasattr(torch.backends, 'mps') and torch.backends.mps.is_available()
    except Exception:
        has_cuda = False
        has_mps = False

    if choice == "cpu":
        return "cpu"
    if choice == "cuda":
        return "cuda" if has_cuda else "cpu"
    if choice == "mps":
        return "mps" if has_mps else "cpu"
    # auto: prefer cuda > mps > cpu
    if has_cuda:
        return "cuda"
    if has_mps:
        return "mps"
    return "cpu"


def transcribe(
    audio_path: Path,
    model_name: str = "base",
    language: Optional[str] = None,
    models_dir: Optional[Path] = None,
    device_choice: str = "auto",
) -> str:
    """Transcribe an audio file with Whisper and return plain text.

    Args:
        audio_path: Path to the audio file.
        model_name: Whisper model name ('tiny', 'base', 'small').
        language: Target language code, or None to autodetect.
        models_dir: Directory to cache/download models under.
        device_choice: 'auto' | 'cpu' | 'cuda' | 'mps'.

    Returns:
        Plain text transcript  (punctuated sentences).

    Raises:
        RuntimeError: If model loading, download, or transcription fails.
    """
    try:
        import whisper  # type: ignore
    except Exception as e:
        raise RuntimeError("openai-whisper is not installed. Run: pip install openai-whisper") from e

    models_dir = models_dir or default_models_dir()
    models_dir.mkdir(parents=True, exist_ok=True)
    device = pick_device(device_choice)
    # Use fp16 for CUDA and MPS (both support half precision)
    fp16 = device in ("cuda", "mps")

    try:
        model = whisper.load_model(model_name, device=device, download_root=str(models_dir))
    except Exception as e:
        raise RuntimeError(f"Failed to load/download model: {e}") from e

    try:
        res = model.transcribe(str(audio_path), language=language, task="transcribe", fp16=fp16, verbose=False)
    except Exception as e:
        raise RuntimeError(f"Transcription failed: {e}") from e

    text = (res.get("text") or "").strip()
    return text

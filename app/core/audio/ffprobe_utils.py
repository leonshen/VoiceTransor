# -*- coding: utf-8 -*-
"""Utilities to query audio metadata via ffprobe and present it nicely."""
from __future__ import annotations
import json
import subprocess
from pathlib import Path
from typing import Any, Dict

import logging
log = logging.getLogger(__name__)

class FFprobeError(RuntimeError):
    """Raised when ffprobe invocation or output parsing fails."""


def ffprobe_info(input_path: Path) -> Dict[str, Any]:
    """Run ffprobe and return parsed JSON output.

    Args:
        input_path: Path to audio file.

    Returns:
        Parsed JSON dict containing "format" and "streams".

    Raises:
        FFprobeError: if ffprobe is missing or returns non-zero.
    """
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_format",
        "-show_streams",
        "-print_format", "json",
        str(input_path),
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except FileNotFoundError:
        raise FFprobeError("ffprobe not found. Please install FFmpeg and add it to PATH.")
    except subprocess.CalledProcessError as e:
        raise FFprobeError(f"ffprobe failed: {e.stderr.strip() or e.stdout.strip()}")
    except Exception as e:
        log.debug("encounter ffprobe exception")
        log.debug(e)
        raise FFprobeError(f"ffprobe failed: {e.stderr.strip() or e.stdout.strip()}")
    try:
        return json.loads(res.stdout)
    except json.JSONDecodeError as e:
        raise FFprobeError(f"Failed to parse ffprobe output: {e}")


def _human_time(seconds_str: str | None) -> str:
    """Render seconds as MM:SS or HH:MM:SS."""
    if not seconds_str:
        return "Unknown"
    try:
        total = float(seconds_str)
    except ValueError:
        return "Unknown"
    m, s = divmod(int(total + 0.5), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def _human_bitrate(bit_rate_str: str | None) -> str:
    if not bit_rate_str:
        return "Unknown"
    try:
        br = int(bit_rate_str)
    except ValueError:
        return "Unknown"
    return f"{br // 1000} kbps"


def _human_size(size_bytes_str: str | None) -> str:
    if not size_bytes_str:
        return "Unknown"
    try:
        n = int(size_bytes_str)
    except ValueError:
        return "Unknown"
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} GB"


def format_info(info: Dict[str, Any], src_path: Path) -> str:
    """Return a multi-line text summary of ffprobe info (legacy CLI helper)."""
    fmt = info.get("format", {}) or {}
    streams = info.get("streams", []) or []
    audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), {}) or {}

    duration = _human_time(fmt.get("duration") or audio_stream.get("duration"))
    bit_rate = _human_bitrate(fmt.get("bit_rate") or audio_stream.get("bit_rate"))
    sample_rate = audio_stream.get("sample_rate") or "Unknown"
    channels = audio_stream.get("channels") or "Unknown"
    codec = audio_stream.get("codec_name") or "Unknown"
    container = fmt.get("format_long_name") or fmt.get("format_name") or "Unknown"
    size_h = _human_size(fmt.get("size"))

    lines = [
        f"File: {src_path.name}",
        f"Path: {src_path}",
        f"Container: {container}",
        f"Codec: {codec}",
        f"Channels: {channels}",
        f"Sample rate: {sample_rate} Hz",
        f"Bitrate: {bit_rate}",
        f"Duration: {duration}",
        f"File size: {size_h}",
    ]
    return "\n".join(lines)


def summarize_info(info: Dict[str, Any], src_path: Path) -> Dict[str, str]:
    """Return a dict {label: value} for friendly UI rendering."""
    fmt = info.get("format", {}) or {}
    streams = info.get("streams", []) or []
    audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), {}) or {}

    return {
        "File": src_path.name,
        "Path": str(src_path),
        "Container": fmt.get("format_long_name") or fmt.get("format_name") or "Unknown",
        "Codec": audio_stream.get("codec_name") or "Unknown",
        "Channels": str(audio_stream.get("channels") or "Unknown"),
        "Sample rate": f"{audio_stream.get('sample_rate', 'Unknown')} Hz",
        "Bitrate": _human_bitrate(fmt.get("bit_rate") or audio_stream.get("bit_rate")),
        "Duration": _human_time(fmt.get("duration") or audio_stream.get("duration")),
        "File size": _human_size(fmt.get("size")),
    }

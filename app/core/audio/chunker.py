# -*- coding: utf-8 -*-
"""Silence-based audio chunking (no overlap) using pydub."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Optional

from pydub import AudioSegment
from pydub.silence import detect_silence


@dataclass
class ChunkConfig:
    """Configuration for silence-based chunking."""
    target_s: float = 30.0
    search_window_s: float = 5.0
    min_chunk_s: float = 15.0
    max_chunk_s: float = 40.0
    min_silence_len_ms: int = 300
    silence_thresh_dbfs: int = -35  # relative to segment.dBFS; adjust if needed

# app/core/audio/chunker.py

def _nearest_silence_boundary(
    ms: int,
    window_start: int,
    window_end: int,
    silences: List[Tuple[int, int]]
) -> Optional[int]:
    """
    Pick a cut position (in ms) *inside the intersection* of [window_start, window_end]
    and any silence region. We choose the midpoint of each intersection and then take
    the one nearest to target `ms`. Returns None if no silence intersects the window.
    """
    candidates: List[int] = []
    for s, e in silences:
        # Intersection of the silence region and the window
        a = max(s, window_start)
        b = min(e, window_end)
        if a >= b:
            continue
        center = (a + b) // 2  # strictly inside [a, b]
        candidates.append(center)

    if not candidates:
        return None
    return min(candidates, key=lambda x: abs(x - ms))



def compute_boundaries(audio_path: Path, cfg: ChunkConfig) -> List[Tuple[float, float]]:
    """Compute non-overlapping [start_s, end_s) chunks based on silence; fall back to hard cuts.

    Returns:
        List of (start_seconds, end_seconds) tuples covering the entire audio.
    """
    seg = AudioSegment.from_file(str(audio_path))
    total_ms = len(seg)
    bounds: List[Tuple[int, int]] = []

    pos = 0
    # Precompute silence regions across whole file for simplicity
    silences = detect_silence(
        seg, min_silence_len=cfg.min_silence_len_ms,
        silence_thresh=cfg.silence_thresh_dbfs
    )  # list of [start_ms, end_ms]

    while pos < total_ms:
        target = pos + int(cfg.target_s * 1000)
        min_ms = int(cfg.min_chunk_s * 1000)
        max_ms = int(cfg.max_chunk_s * 1000)
        win_ms = int(cfg.search_window_s * 1000)

        # Clamp the search window; guarantee win_start < win_end
        win_start = max(pos + min_ms, target - win_ms)
        win_end = min(total_ms, min(pos + max_ms, target + win_ms))
        if win_end <= win_start:
            win_end = min(total_ms, win_start + 1)

        cut_ms = _nearest_silence_boundary(target, win_start, win_end, silences)
        if cut_ms is None:
            # No silence in window ⇒ hard cut (bounded by max length)
            cut_ms = min(pos + max_ms, total_ms)

        end_ms = max(cut_ms, pos + 1)  # still keep a tiny guard
        bounds.append((pos, end_ms))
        pos = end_ms

    # Convert to seconds
    return [(s / 1000.0, e / 1000.0) for (s, e) in bounds]

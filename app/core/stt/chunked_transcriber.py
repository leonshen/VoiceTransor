# -*- coding: utf-8 -*-
"""Chunked transcription driver: silence chunking + thermal pacing + resume + SRT."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
import hashlib
import json
import math
import threading
import time
import os

from app.core.audio.chunker import ChunkConfig, compute_boundaries
from app.core.system.thermal import ThermalConfig, get_cpu_temp_c, get_cpu_percent
from app.core.common.workers import WorkerSignals

import logging
log = logging.getLogger(__name__)

import gc

class _ModelManager:
    """
    Manages Whisper model lifecycle with support for dynamic model switching.

    Implements aggressive GPU memory cleanup to enable switching between different
    models without requiring app restart. Supports CUDA (NVIDIA) and MPS (Apple Silicon).

    Uses multi-stage cleanup process including:
    - Model migration to CPU
    - Multiple garbage collection rounds
    - GPU cache clearing (CUDA/MPS)
    - CUDA synchronization and memory statistics reset
    - MPS cache clearing for Apple Silicon devices
    """
    def __init__(self):
        self._key = None
        self._model = None

    def get(self, name: str, device: str, models_dir: Path):
        key = (name, device, str(models_dir))
        if self._key == key and self._model is not None:
            return self._model

        # Try to safely unload existing model before switching
        if self._model is not None:
            log.info(f"Switching model from {self._key} to {key}, attempting to unload...")
            success = self._unload()
            if not success:
                raise RuntimeError("To load the other model, please restart the App.")

        # Load new model
        import whisper  # type: ignore
        log.info(f"Loading model: {name} on device: {device}")
        self._model = whisper.load_model(name, device=device, download_root=str(models_dir))
        self._key = key
        return self._model

    def _unload(self) -> bool:
        """
        Aggressively unload the model and free GPU memory.
        Supports CUDA (NVIDIA) and MPS (Apple Silicon) backends.
        Returns True if successful, False otherwise.
        """
        if self._model is None:
            return True

        try:
            import torch
            log.debug("Starting aggressive model unload...")

            # Step 1: Move model to CPU to release GPU memory
            try:
                has_cuda = torch.cuda.is_available()
                has_mps = hasattr(torch.backends, 'mps') and torch.backends.mps.is_available()

                if has_cuda or has_mps:
                    self._model.to("cpu")
                    log.debug("Model moved to CPU")
            except Exception as e:
                log.warning(f"Failed to move model to CPU: {e}")

            # Step 2: Delete model and clear reference
            model_ref = self._model
            self._model = None
            self._key = None
            del model_ref
            log.debug("Model reference deleted")

            # Step 3: Multiple rounds of garbage collection
            for i in range(3):
                gc.collect()
            log.debug("Garbage collection completed")

            # Step 4: Aggressive GPU cleanup (CUDA or MPS)
            has_cuda = torch.cuda.is_available()
            has_mps = hasattr(torch.backends, 'mps') and torch.backends.mps.is_available()

            if has_cuda:
                try:
                    # CUDA cleanup
                    torch.cuda.synchronize()

                    # Empty cache multiple times
                    for i in range(3):
                        torch.cuda.empty_cache()

                    # Clear IPC collections (shared memory)
                    try:
                        torch.cuda.ipc_collect()
                    except Exception:
                        pass

                    # Reset memory stats
                    try:
                        torch.cuda.reset_peak_memory_stats()
                        torch.cuda.reset_accumulated_memory_stats()
                    except Exception:
                        pass

                    log.debug("CUDA memory cleanup completed")

                    # Step 5: Log memory stats for debugging
                    allocated = torch.cuda.memory_allocated() / 1024**2  # MB
                    reserved = torch.cuda.memory_reserved() / 1024**2    # MB
                    log.info(f"CUDA memory after cleanup - Allocated: {allocated:.1f}MB, Reserved: {reserved:.1f}MB")

                except Exception as e:
                    log.warning(f"CUDA cleanup error: {e}")

            elif has_mps:
                try:
                    # MPS cleanup (Apple Silicon)
                    # Empty MPS cache multiple times
                    for i in range(3):
                        torch.mps.empty_cache()

                    log.debug("MPS memory cleanup completed")

                    # MPS doesn't have detailed memory stats like CUDA
                    log.info("MPS memory cache cleared")

                except Exception as e:
                    log.warning(f"MPS cleanup error: {e}")

            # Step 6: Short wait to let system complete cleanup
            time.sleep(0.5)

            log.info("Model unloaded successfully")
            return True

        except Exception as e:
            log.error(f"Failed to unload model: {e}")
            self._model = None
            self._key = None
            return False

    def close(self):
        self._unload()

MODEL_MANAGER = _ModelManager()

def _emit_safe(signals, name: str, *args) -> None:
    try:
        getattr(signals, name).emit(*args)
    except RuntimeError:
        # GUI likely torn down; ignore
        pass

def _partial_sidecar_path(audio_path: str | Path, with_srt: bool) -> Path:
    """Return sidecar file path to store incremental transcript."""
    p = Path(audio_path)
    # e.g. lecture.mp3.vt.partial.srt / lecture.mp3.vt.partial.txt
    ext = ".vt.partial.srt" if with_srt else ".vt.partial.txt"
    return p.with_name(p.name + ext)

def _append_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(text)
        if not text.endswith("\n"):
            f.write("\n")

# -------------------------
# Options / Progress models
# -------------------------
@dataclass
class TranscribeOptions:
    model: str
    language: Optional[str]
    device: str
    models_dir: Path
    include_timestamps: bool


@dataclass
class Progress:
    percent: int
    secs_done: float
    secs_total: float
    eta_secs: float


# -------------------------
# SRT formatting helpers
# -------------------------
def _fmt_srt_time(seconds: float) -> str:
    """Return HH:MM:SS,mmm from seconds (rounded to ms)."""
    ms = int(round(seconds * 1000.0))
    if ms < 0:
        ms = 0
    s, msec = divmod(ms, 1000)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d},{msec:03d}"


def segments_to_srt(segments: List[Dict[str, Any]]) -> str:
    """Convert a list of {'start','end','text'} segments to SRT string."""
    lines: List[str] = []
    # ensure monotonic times and sane durations
    last_end = 0.0
    for idx, seg in enumerate(segments, start=1):
        start = float(seg.get("start", 0.0))
        end = float(seg.get("end", start))
        text = (seg.get("text") or "").strip()

        if end < start:
            end = start
        # ensure minimal gap
        if start < last_end:
            start = last_end
        if end < start + 0.001:
            end = start + 0.001

        lines.append(str(idx))
        lines.append(f"{_fmt_srt_time(start)} --> {_fmt_srt_time(end)}")
        lines.append(text or "")
        lines.append("")  # blank line
        last_end = end
    return "\n".join(lines).rstrip() + "\n"


# -------------------------
# Checkpointing
# -------------------------
def _checkpoint_dir() -> Path:
    base = os.getenv("LOCALAPPDATA") or str(Path.home() / ".cache")
    return Path(base) / "VoiceTransor" / "cache" / "checkpoints"


def _file_identity(audio_path: Path) -> str:
    st = audio_path.stat()
    raw = f"{audio_path.resolve()}|{st.st_size}|{int(st.st_mtime)}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def _checkpoint_path(audio_path: Path) -> Path:
    d = _checkpoint_dir()
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{_file_identity(audio_path)}.json"


def _load_checkpoint(audio_path: Path) -> Optional[Dict[str, Any]]:
    p = _checkpoint_path(audio_path)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None


def _save_checkpoint(audio_path: Path, payload: Dict[str, Any]) -> None:
    _checkpoint_path(audio_path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


# -------------------------
# Core driver
# -------------------------
def transcribe_chunked(
    audio_path: Path,
    t_opt: TranscribeOptions,
    c_cfg: ChunkConfig,
    th_cfg: ThermalConfig,
    stop_flag: threading.Event,
    signals: WorkerSignals,
    resume: bool = True,
) -> str:
    """Chunked transcription orchestrator with live streaming and resume bootstrap.

    Emits (via _emit_safe):
        - message(str): status text
        - progress(int, secs_done, secs_total, eta_secs): progress and ETA
        - partial_text(str): per-chunk text to append to transcript UI
        - bootstrap_text(str): previously completed text on resume (append to UI first)
        - result(str): final text
        - error(str): on fatal error; raise "__CANCELLED__" for user-cancel
    """
    import time
    from typing import List, Dict, Any

    from app.core.common.workers import _enable_dbg
    _enable_dbg()

    # --- helpers ---
    def _fmt_srt_time(secs: float) -> str:
        # SRT time: HH:MM:SS,mmm (rounded to milliseconds)
        if secs < 0:
            secs = 0.0
        ms_total = int(round(secs * 1000.0))
        h = ms_total // 3_600_000
        rem = ms_total % 3_600_000
        m = rem // 60_000
        rem %= 60_000
        s = rem // 1000
        ms = rem % 1000
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    def _srt_blocks_for_segments(segments: List[Dict[str, Any]], start_index: int) -> str:
        # Build SRT text for a list of segments with a starting index
        parts: List[str] = []
        idx = start_index
        for sg in segments:
            st = float(sg["start"])
            et = float(sg["end"])
            tx = (sg.get("text") or "").strip()
            if not tx:
                continue
            parts.append(
                f"{idx}\n{_fmt_srt_time(st)} --> {_fmt_srt_time(et)}\n{tx}\n"
            )
            idx += 1
        return "\n".join(parts).rstrip() + ("\n" if parts else "")

    # --- Prepare whisper model and audio ---
    try:
        import whisper  # type: ignore
    except Exception as e:
        raise RuntimeError("openai-whisper is not installed. Run: pip install openai-whisper") from e

    # load audio once (16k float32)
    _emit_safe(signals, "message", "Loading audio file...")
    audio_np = whisper.load_audio(str(audio_path))
    duration_s = float(audio_np.shape[-1] / 16000.0)
    _emit_safe(signals, "message", f"Audio loaded: {duration_s:.1f} seconds")

    device = _pick_device(t_opt.device)
    # Use fp16 for CUDA and MPS (both support half precision)
    fp16 = device in ("cuda", "mps")

    try:
        log.debug("load whisper model ...")
        _emit_safe(signals, "message", f"Loading Whisper model '{t_opt.model}' on {device}...")
        # cause crash
        # model = whisper.load_model(t_opt.model, device=device, download_root=str(t_opt.models_dir))
        # cached model, ok
        model = MODEL_MANAGER.get(t_opt.model, device, t_opt.models_dir)
        log.debug("loaded whisper model ok")
        _emit_safe(signals, "message", f"Model '{t_opt.model}' loaded successfully")
    except Exception as e:
        raise RuntimeError(f"Failed to load/download model: {e}") from e

    # --- Determine boundaries, possibly resume ---
    def _progress_callback(msg: str):
        _emit_safe(signals, "message", msg)

    bounds = compute_boundaries(audio_path, c_cfg, progress_callback=_progress_callback)
    _emit_safe(signals, "message", f"Chunking complete: {len(bounds)} chunks created")
    total = duration_s

    ck = _load_checkpoint(audio_path) if resume else None
    done_until = 0.0
    segments_accum: List[Dict[str, Any]] = []
    text_accum_parts: List[str] = []

    if ck and _checkpoint_matches(ck, audio_path, t_opt, c_cfg, th_cfg):
        done_until = float(ck.get("done_until_s", 0.0))
        progress_pct = int(100.0 * done_until / total) if total > 0 else 0
        _emit_safe(signals, "message", f"Resuming from checkpoint ({progress_pct}% completed previously)...")

        if t_opt.include_timestamps:
            segments_accum = list(ck.get("segments_accum", []))
            # Bootstrap previously completed SRT into UI
            if segments_accum:
                try:
                    prev_text = segments_to_srt(segments_accum)
                    if prev_text.strip():
                        _emit_safe(signals, "bootstrap_text", prev_text)
                except Exception:
                    # Fallback: build minimal SRT blocks
                    prev_text = _srt_blocks_for_segments(segments_accum, 1)
                    if prev_text.strip():
                        _emit_safe(signals, "bootstrap_text", prev_text)
        else:
            prev_text = ck.get("text_accum", "") or ""
            if prev_text.strip():
                _emit_safe(signals, "bootstrap_text", prev_text)

        # skip completed chunks
        cut_idx = 0
        while cut_idx < len(bounds) and bounds[cut_idx][1] <= done_until + 1e-3:
            cut_idx += 1
        start_idx = cut_idx
        _emit_safe(signals, "message", f"Skipping {start_idx} completed chunks, continuing from chunk {start_idx+1}/{len(bounds)}")
    else:
        start_idx = 0
        _emit_safe(signals, "message", "Starting transcription from beginning...")

    t0 = time.time()

    # ETA calculation state - use moving average for accuracy
    chunk_times = []  # Track recent chunk processing times
    eta_window_size = 5  # Use last 5 chunks for ETA calculation

    # --- Loop over chunks ---
    for i in range(start_idx, len(bounds)):
        # thermal pacing before each chunk
        _thermal_wait(th_cfg, signals, stop_flag)
        if stop_flag.is_set():
            _persist_checkpoint(audio_path, t_opt, c_cfg, th_cfg, total, done_until, text_accum_parts, segments_accum)
            raise RuntimeError("__CANCELLED__")

        start_s, end_s = bounds[i]
        chunk_len = end_s - start_s

        # slice audio in samples
        s_idx = int(start_s * 16000)
        e_idx = int(end_s * 16000)
        chunk_audio = audio_np[s_idx:e_idx]

        # Track chunk processing time for accurate ETA
        chunk_start_time = time.time()

        # transcribe this chunk
        try:
            res = model.transcribe(
                chunk_audio,
                language=t_opt.language or None,
                task="transcribe",
                fp16=fp16,
                verbose=False,
            )
        except Exception as e:
            raise RuntimeError(f"Transcription failed at {start_s:.2f}s: {e}") from e
        finally:
            # Release chunk audio immediately after transcription
            del chunk_audio

        # Record chunk processing time
        chunk_elapsed = time.time() - chunk_start_time
        chunk_times.append(chunk_elapsed)

        # accumulate + stream to UI
        segs = res.get("segments") or []
        if t_opt.include_timestamps:
            # convert segment times to absolute timeline for this chunk
            new_segments: List[Dict[str, Any]] = []
            for sg in segs:
                st = float(start_s) + float(sg.get("start", 0.0))
                et = float(start_s) + float(sg.get("end", 0.0))
                tx = (sg.get("text") or "").strip()
                if tx:
                    new_segments.append({"start": st, "end": et, "text": tx})

            if new_segments:
                # Stream SRT blocks for just-finished segments (proper numbering continues)
                srt_chunk = _srt_blocks_for_segments(new_segments, start_index=len(segments_accum) + 1)
                _emit_safe(signals, "partial_text", srt_chunk)
                # Accumulate for final output & checkpoint
                segments_accum.extend(new_segments)
        else:
            # Plain text: prefer the model's merged text for the chunk
            chunk_text = (res.get("text") or "").strip()
            if chunk_text:
                text_accum_parts.append(chunk_text)
                _emit_safe(signals, "partial_text", chunk_text)

        done_until = end_s

        # persist checkpoint routinely
        _persist_checkpoint(audio_path, t_opt, c_cfg, th_cfg, total, done_until, text_accum_parts, segments_accum)

        # progress & ETA calculation using moving average
        percent = int(min(100, round(100.0 * done_until / total)))
        remain_chunks = len(bounds) - (i + 1)

        # Calculate ETA based on recent chunk times (more accurate than global average)
        if remain_chunks > 0 and chunk_times:
            # Use last N chunks for ETA (skip first chunk if it's the only one - cold start)
            recent_times = chunk_times[-eta_window_size:] if len(chunk_times) > 1 else chunk_times
            avg_chunk_time = sum(recent_times) / len(recent_times)
            eta = avg_chunk_time * remain_chunks
        else:
            eta = 0.0

        _emit_safe(signals, "progress", percent, done_until, total, eta)
        _emit_safe(signals, "message", f"Processed chunk {i+1}/{len(bounds)} ({chunk_len:.1f}s)")

        # Clean GPU cache after each chunk to prevent memory accumulation
        if (i + 1) % 2 == 0:  # Every 2 chunks
            try:
                import torch
                if device == "cuda" and torch.cuda.is_available():
                    torch.cuda.empty_cache()
                elif device == "mps" and hasattr(torch, 'mps'):
                    torch.mps.empty_cache()
            except Exception:
                pass

        # inter-chunk cooldown (base; thermal path may have waited already)
        time.sleep(0.2)

    # --- Build final output ---
    if t_opt.include_timestamps:
        final_text = segments_to_srt(segments_accum)
    else:
        final_text = "\n".join([p for p in text_accum_parts if p]).strip()

    log.debug("final_text")
    log.debug(final_text)

    # --- Cleanup: Release GPU memory and audio data ---
    try:
        # Delete audio numpy array to free memory
        del audio_np

        # Force GPU memory cleanup if using CUDA or MPS
        import torch
        if device == "cuda" and torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
            log.debug("CUDA memory released after transcription")
        elif device == "mps" and hasattr(torch, 'mps'):
            torch.mps.empty_cache()
            log.debug("MPS memory released after transcription")

        # Force garbage collection
        gc.collect()
    except Exception as e:
        log.warning(f"Failed to cleanup resources: {e}")

    return final_text


# -------------------------
# Helpers
# -------------------------
def _pick_device(choice: str) -> str:
    """
    Select the appropriate device for Whisper model.
    Supports: cpu, cuda (NVIDIA), mps (Apple Silicon), auto
    """
    try:
        import torch  # type: ignore
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


def _checkpoint_matches(ck: Dict[str, Any], audio_path: Path,
                        t_opt: TranscribeOptions, c_cfg: ChunkConfig, th_cfg: ThermalConfig) -> bool:
    """Whether checkpoint belongs to the same file/options."""
    try:
        st = audio_path.stat()
        if ck.get("audio_path") != str(audio_path) or int(ck.get("size", -1)) != st.st_size or int(ck.get("mtime", -1)) != int(st.st_mtime):
            return False
        if ck.get("model") != t_opt.model or ck.get("language") != (t_opt.language or "") or bool(ck.get("with_timestamps")) != bool(t_opt.include_timestamps):
            return False
        # chunking knobs match the essentials
        cc = ck.get("chunk_cfg", {})
        if abs(float(cc.get("target_s", 30.0)) - float(c_cfg.target_s)) > 1e-3:
            return False
        return True
    except Exception:
        return False


def _persist_checkpoint(audio_path: Path, t_opt: TranscribeOptions, c_cfg: ChunkConfig, th_cfg: ThermalConfig,
                        total: float, done_until: float,
                        text_parts: List[str], segments: List[Dict[str, Any]]) -> None:
    st = audio_path.stat()
    payload = {
        "audio_path": str(audio_path),
        "size": st.st_size,
        "mtime": int(st.st_mtime),
        "duration_s": total,
        "model": t_opt.model,
        "language": t_opt.language or "",
        "device": t_opt.device,
        "with_timestamps": t_opt.include_timestamps,
        "chunk_cfg": {
            "target_s": c_cfg.target_s,
            "search_window_s": c_cfg.search_window_s,
            "min_chunk_s": c_cfg.min_chunk_s,
            "max_chunk_s": c_cfg.max_chunk_s,
            "min_silence_len_ms": c_cfg.min_silence_len_ms,
            "silence_thresh_dbfs": c_cfg.silence_thresh_dbfs,
        },
        "thermal_cfg": {
            "enabled": th_cfg.enabled,
            "high_c": th_cfg.high_c,
            "critical_c": th_cfg.critical_c,
        },
        "done_until_s": done_until,
    }
    if segments:
        payload["segments_accum"] = segments
    if text_parts:
        payload["text_accum"] = "\n".join([p for p in text_parts if p]).strip()

    _save_checkpoint(audio_path, payload)


def _thermal_wait(th: ThermalConfig, signals: WorkerSignals, stop_flag: threading.Event) -> None:
    """Adaptive wait based on CPU temperature (or CPU% fallback)."""
    if not th.enabled:
        return

    temp = get_cpu_temp_c()
    log.debug("before task: got cpu temp %s °C", "N/A" if temp is None else f"{temp:.1f}")


    if temp is None and th.fallback_use_cpu_percent:
        # emulate using CPU%
        cpu = get_cpu_percent()
        if cpu >= th.cpu_hot_pct:
            # treat as "hot"
            _emit_safe(signals, "message", f"Cooling down (CPU {cpu:.0f}%) …")
            # and the other cooling message variants
            time.sleep(th.cooldown_ms_hot / 1000.0)
        else:
            time.sleep(th.cooldown_ms_base / 1000.0)
        return

    if temp is None:
        # no data; do base cooldown
        time.sleep(th.cooldown_ms_base / 1000.0)
        return

    if temp >= th.critical_c:
        # pause until cooled below high threshold
        while temp is not None and temp >= (th.high_c - 2):
            if stop_flag.is_set():
                return
            _emit_safe(signals, "message", f"Paused for cooling (CPU {temp:.0f}°C)…")
            time.sleep(th.poll_ms / 1000.0)
            temp = get_cpu_temp_c()
            log.debug("in loop: got cpu temp %s °C", "N/A" if temp is None else f"{temp:.1f}")
        return

    if temp >= th.high_c:
        _emit_safe(signals, "message", f"Cooling down (CPU {temp:.0f}°C)…")
        time.sleep(th.cooldown_ms_hot / 1000.0)
    else:
        time.sleep(th.cooldown_ms_base / 1000.0)

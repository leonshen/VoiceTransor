# -*- coding: utf-8 -*-
import argparse
import datetime as dt
import os
import sys
from pathlib import Path

import torch  # pip install torch (CPU or GPU version depending on environment)
import whisper  # pip install openai-whisper


def timestamp() -> str:
    return dt.datetime.now().strftime("%Y%m%d_%H%M")


def default_models_dir() -> Path:
    # Windows: %LOCALAPPDATA%\VoiceTransor\models\whisper\
    local = os.getenv("LOCALAPPDATA")
    if local:
        return Path(local) / "VoiceTransor" / "models" / "whisper"
    # Fallback for other platforms
    home = Path.home()
    return home / ".cache" / "VoiceTransor" / "models" / "whisper"


def pick_device(choice: str) -> str:
    if choice == "cpu":
        return "cpu"
    if choice == "cuda":
        return "cuda"
    # auto
    return "cuda" if torch.cuda.is_available() else "cpu"


def default_out_path(input_path: Path) -> Path:
    return input_path.with_name(f"VoiceTransor_transcript_{timestamp()}.txt")


def main():
    ap = argparse.ArgumentParser(description="Local Whisper transcription to plain text (no timestamps)")
    ap.add_argument("-i", "--input", required=True, help="Audio file path")
    ap.add_argument("-l", "--lang", default=None, help="Target language code (e.g., zh, en; leave empty for auto-detect)")
    ap.add_argument("-m", "--model", default="base", choices=["tiny", "base", "small"],
                    help="Whisper model (default: base)")
    ap.add_argument("--models-dir", default=str(default_models_dir()),
                    help="Model cache directory (default: local app data directory)")
    ap.add_argument("--device", default="auto", choices=["auto", "cpu", "cuda"],
                    help="Compute device (default: auto)")
    ap.add_argument("-o", "--output", default=None, help="Transcript output file path (.txt)")
    args = ap.parse_args()

    in_path = Path(args.input)
    if not in_path.exists():
        print(f"File does not exist: {in_path}", file=sys.stderr)
        sys.exit(1)

    out_path = Path(args.output) if args.output else default_out_path(in_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    models_dir = Path(args.models_dir)
    models_dir.mkdir(parents=True, exist_ok=True)

    device = pick_device(args.device)
    fp16 = device == "cuda"

    print(f"[Whisper] Model: {args.model} | Device: {device} | Models dir: {models_dir}")
    try:
        model = whisper.load_model(args.model, device=device, download_root=str(models_dir))
    except Exception as e:
        print(f"Failed to load/download model: {e}", file=sys.stderr)
        sys.exit(2)

    # Transcribe
    try:
        result = model.transcribe(str(in_path), language=args.lang, task="transcribe", fp16=fp16, verbose=False)
    except Exception as e:
        print(f"Transcription failed: {e}", file=sys.stderr)
        sys.exit(3)

    text = (result.get("text") or "").strip()

    try:
        out_path.write_text(text, encoding="utf-8")
    except Exception as e:
        print(f"Failed to write file: {out_path} | {e}", file=sys.stderr)
        sys.exit(4)

    print(f"Transcription completed: {out_path}")


if __name__ == "__main__":
    main()

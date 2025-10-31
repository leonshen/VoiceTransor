# -*- coding: utf-8 -*-
import argparse
import json
import subprocess
import sys
from pathlib import Path


def ffprobe_info(input_path: Path) -> dict:
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_format",
        "-show_streams",
        "-print_format", "json",
        str(input_path)
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except FileNotFoundError:
        print("Error: ffprobe not found. Please install FFmpeg and add it to PATH.", file=sys.stderr)
        sys.exit(2)
    except subprocess.CalledProcessError as e:
        print(f"ffprobe call failed: {e.stderr}", file=sys.stderr)
        sys.exit(3)
    try:
        return json.loads(res.stdout)
    except json.JSONDecodeError as e:
        print(f"Failed to parse ffprobe output: {e}", file=sys.stderr)
        sys.exit(4)


def main():
    ap = argparse.ArgumentParser(description="Read audio file information (ffprobe)")
    ap.add_argument("-i", "--input", required=True, help="Audio file path")
    ap.add_argument("--pretty", action="store_true", help="Pretty print JSON")
    args = ap.parse_args()

    p = Path(args.input)
    if not p.exists():
        print(f"File does not exist: {p}", file=sys.stderr)
        sys.exit(1)

    info = ffprobe_info(p)
    if args.pretty:
        print(json.dumps(info, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(info, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    main()

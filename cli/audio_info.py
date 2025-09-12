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
        print("错误：未找到 ffprobe。请安装 FFmpeg 并将其添加到 PATH。", file=sys.stderr)
        sys.exit(2)
    except subprocess.CalledProcessError as e:
        print(f"ffprobe 调用失败：{e.stderr}", file=sys.stderr)
        sys.exit(3)
    try:
        return json.loads(res.stdout)
    except json.JSONDecodeError as e:
        print(f"解析 ffprobe 输出失败：{e}", file=sys.stderr)
        sys.exit(4)


def main():
    ap = argparse.ArgumentParser(description="读取音频文件信息（ffprobe）")
    ap.add_argument("-i", "--input", required=True, help="音频文件路径")
    ap.add_argument("--pretty", action="store_true", help="美化打印 JSON")
    args = ap.parse_args()

    p = Path(args.input)
    if not p.exists():
        print(f"文件不存在：{p}", file=sys.stderr)
        sys.exit(1)

    info = ffprobe_info(p)
    if args.pretty:
        print(json.dumps(info, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(info, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
import argparse
import datetime as dt
import os
import sys
from pathlib import Path

import torch  # pip install torch  (按环境装 CPU/GPU 版)
import whisper  # pip install openai-whisper


def timestamp() -> str:
    return dt.datetime.now().strftime("%Y%m%d_%H%M")


def default_models_dir() -> Path:
    # Windows: %LOCALAPPDATA%\VoiceTransor\models\whisper\
    local = os.getenv("LOCALAPPDATA")
    if local:
        return Path(local) / "VoiceTransor" / "models" / "whisper"
    # 其它平台回退
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
    ap = argparse.ArgumentParser(description="本地 Whisper 转录为纯文本（无时间戳）")
    ap.add_argument("-i", "--input", required=True, help="音频文件路径")
    ap.add_argument("-l", "--lang", default=None, help="目标语言代码（例如 zh, en；留空自动检测）")
    ap.add_argument("-m", "--model", default="base", choices=["tiny", "base", "small"],
                    help="Whisper 模型（默认 base）")
    ap.add_argument("--models-dir", default=str(default_models_dir()),
                    help="模型缓存目录（默认：本地应用数据目录）")
    ap.add_argument("--device", default="auto", choices=["auto", "cpu", "cuda"],
                    help="计算设备（默认 auto）")
    ap.add_argument("-o", "--output", default=None, help="转录结果保存路径（.txt）")
    args = ap.parse_args()

    in_path = Path(args.input)
    if not in_path.exists():
        print(f"文件不存在：{in_path}", file=sys.stderr)
        sys.exit(1)

    out_path = Path(args.output) if args.output else default_out_path(in_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    models_dir = Path(args.models_dir)
    models_dir.mkdir(parents=True, exist_ok=True)

    device = pick_device(args.device)
    fp16 = device == "cuda"

    print(f"[Whisper] 模型: {args.model} | 设备: {device} | 模型目录: {models_dir}")
    try:
        model = whisper.load_model(args.model, device=device, download_root=str(models_dir))
    except Exception as e:
        print(f"加载/下载模型失败：{e}", file=sys.stderr)
        sys.exit(2)

    # 转录
    try:
        result = model.transcribe(str(in_path), language=args.lang, task="transcribe", fp16=fp16, verbose=False)
    except Exception as e:
        print(f"转录失败：{e}", file=sys.stderr)
        sys.exit(3)

    text = (result.get("text") or "").strip()

    try:
        out_path.write_text(text, encoding="utf-8")
    except Exception as e:
        print(f"写入文件失败：{out_path} | {e}", file=sys.stderr)
        sys.exit(4)

    print(f"转录完成：{out_path}")


if __name__ == "__main__":
    main()

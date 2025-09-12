# -*- coding: utf-8 -*-
import argparse
import os
import sys
from pathlib import Path

try:
    from openai import OpenAI  # pip install openai
except Exception as e:
    OpenAI = None


STYLE_HINT = {
    "brief": "写一个非常精简的要点式摘要，100-150字左右，突出关键信息。",
    "normal": "写一个清晰的段落式摘要，覆盖核心信息与结构，200-300字左右。",
    "detailed": "写一个详细摘要，包含关键细节与结构化要点，400-600字左右。"
}


def build_prompt(text: str, style: str) -> str:
    hint = STYLE_HINT.get(style, STYLE_HINT["normal"])
    return (
        f"{hint}\n\n"
        "附加要求：\n"
        "- 保持原语言（若原文为中文就用中文，若为英文就用英文）。\n"
        "- 不要编造事实，不要添加原文没有的结论。\n"
        "- 保持可读性和逻辑清晰。\n\n"
        "以下是原文：\n"
        "----\n"
        f"{text}\n"
        "----\n"
    )


def main():
    ap = argparse.ArgumentParser(description="调用 OpenAI API 对文本生成摘要")
    ap.add_argument("-i", "--input", required=True, help="转录文本文件路径")
    ap.add_argument("-o", "--output", default=None, help="摘要输出文件（可选）")
    ap.add_argument("--style", default="normal", choices=["brief", "normal", "detailed"], help="摘要风格")
    ap.add_argument("--model", default="gpt-4o-mini", help="OpenAI 模型名（默认 gpt-4o-mini）")
    args = ap.parse_args()

    if OpenAI is None:
        print("缺少 openai 包，请先安装：pip install openai", file=sys.stderr)
        sys.exit(2)

    api_key = os.getenv("OPENAI_API_KEY")
    project_Id = os.getenv("OPENAI_PROJECT_ID")
    if not api_key:
        print("未设置 OPENAI_API_KEY 环境变量。", file=sys.stderr)
        sys.exit(1)

    if not project_Id:
        print("未设置 OPENAI_PROJECT_ID 环境变量。", file=sys.stderr)
        sys.exit(1)

    in_path = Path(args.input)
    if not in_path.exists():
        print(f"文件不存在：{in_path}", file=sys.stderr)
        sys.exit(3)

    raw = in_path.read_text(encoding="utf-8")
    # 简单长度保护（如模型上下文限制，可按需调大/切分）
    if len(raw) > 120_000:
        raw = raw[:120_000]

    prompt = build_prompt(raw, args.style)

    # client = OpenAI(api_key=api_key)
    client = OpenAI(api_key=api_key,
                    project = project_Id)

    try:
        resp = client.chat.completions.create(
            model=args.model,
            messages=[
                {"role": "system", "content": "You are a concise and accurate summarizer."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        summary = resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"OpenAI 调用失败：{e}", file=sys.stderr)
        sys.exit(4)

    if args.output:
        out_path = Path(args.output)
        try:
            out_path.write_text(summary, encoding="utf-8")
        except Exception as e:
            print(f"写入摘要失败：{e}", file=sys.stderr)
            sys.exit(5)
        print(f"摘要已保存：{out_path}")
    else:
        print(summary)


if __name__ == "__main__":
    main()

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
    "brief": "Write a very concise bullet-point summary, around 100-150 words, highlighting key information.",
    "normal": "Write a clear paragraph-style summary covering core information and structure, around 200-300 words.",
    "detailed": "Write a detailed summary with key details and structured points, around 400-600 words."
}


def build_prompt(text: str, style: str) -> str:
    hint = STYLE_HINT.get(style, STYLE_HINT["normal"])
    return (
        f"{hint}\n\n"
        "Additional requirements:\n"
        "- Keep the original language (use Chinese if the source is in Chinese, English if in English).\n"
        "- Do not fabricate facts or add conclusions not present in the original text.\n"
        "- Maintain readability and logical clarity.\n\n"
        "Here is the source text:\n"
        "----\n"
        f"{text}\n"
        "----\n"
    )


def main():
    ap = argparse.ArgumentParser(description="Generate text summary using OpenAI API")
    ap.add_argument("-i", "--input", required=True, help="Transcript text file path")
    ap.add_argument("-o", "--output", default=None, help="Summary output file (optional)")
    ap.add_argument("--style", default="normal", choices=["brief", "normal", "detailed"], help="Summary style")
    ap.add_argument("--model", default="gpt-4o-mini", help="OpenAI model name (default: gpt-4o-mini)")
    args = ap.parse_args()

    if OpenAI is None:
        print("Missing openai package. Please install: pip install openai", file=sys.stderr)
        sys.exit(2)

    api_key = os.getenv("OPENAI_API_KEY")
    project_Id = os.getenv("OPENAI_PROJECT_ID")
    if not api_key:
        print("OPENAI_API_KEY environment variable not set.", file=sys.stderr)
        sys.exit(1)

    if not project_Id:
        print("OPENAI_PROJECT_ID environment variable not set.", file=sys.stderr)
        sys.exit(1)

    in_path = Path(args.input)
    if not in_path.exists():
        print(f"File does not exist: {in_path}", file=sys.stderr)
        sys.exit(3)

    raw = in_path.read_text(encoding="utf-8")
    # Simple length protection (model context limit, can be increased or split as needed)
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
        print(f"OpenAI API call failed: {e}", file=sys.stderr)
        sys.exit(4)

    if args.output:
        out_path = Path(args.output)
        try:
            out_path.write_text(summary, encoding="utf-8")
        except Exception as e:
            print(f"Failed to write summary: {e}", file=sys.stderr)
            sys.exit(5)
        print(f"Summary saved: {out_path}")
    else:
        print(summary)


if __name__ == "__main__":
    main()

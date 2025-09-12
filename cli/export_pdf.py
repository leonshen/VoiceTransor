# -*- coding: utf-8 -*-
import argparse
import datetime as dt
from pathlib import Path

from reportlab.lib.pagesizes import A4  # pip install reportlab
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer


def default_out_path(input_txt: Path) -> Path:
    ts = dt.datetime.now().strftime("%Y%m%d_%H%M")
    return input_txt.with_name(f"VoiceTransor_summary_{ts}.pdf")


def build_doc(output_pdf: Path, title: str, body_text: str, font_name: str | None = None):
    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    body_style = styles["BodyText"]

    if font_name:
        title_style = ParagraphStyle("TitleCJK", parent=styles["Title"], fontName=font_name)
        body_style = ParagraphStyle("BodyCJK", parent=styles["BodyText"], fontName=font_name, leading=14)

    story = []
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 8 * mm))

    # 将换行转为 <br/> 以便 Paragraph 正确换行
    safe_text = body_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    safe_text = safe_text.replace("\n", "<br/>")
    story.append(Paragraph(safe_text, body_style))

    doc = SimpleDocTemplate(str(output_pdf), pagesize=A4,
                            leftMargin=20 * mm, rightMargin=20 * mm,
                            topMargin=20 * mm, bottomMargin=20 * mm)
    doc.build(story)


def main():
    ap = argparse.ArgumentParser(description="将摘要文本导出为 PDF（离线）")
    ap.add_argument("-i", "--input", required=True, help="摘要文本文件路径")
    ap.add_argument("-o", "--output", default=None, help="PDF 输出路径（可选）")
    ap.add_argument("--title", default="VoiceTransor Summary", help="PDF 标题")
    ap.add_argument("--font", default=None, help="可选：TTF 字体路径（用于中文等 CJK 文本显示）")
    args = ap.parse_args()

    in_path = Path(args.input)
    if not in_path.exists():
        print(f"文件不存在：{in_path}")
        raise SystemExit(1)

    out_pdf = Path(args.output) if args.output else default_out_path(in_path)
    out_pdf.parent.mkdir(parents=True, exist_ok=True)

    # 如提供 TTF 字体，则注册后使用
    font_name = None
    if args.font:
        font_path = Path(args.font)
        if not font_path.exists():
            print(f"字体文件不存在：{font_path}")
            raise SystemExit(2)
        font_name = "VoiceTransorFont"
        pdfmetrics.registerFont(TTFont(font_name, str(font_path)))

    text = in_path.read_text(encoding="utf-8")
    build_doc(out_pdf, args.title, text, font_name=font_name)
    print(f"PDF 已生成：{out_pdf}")


if __name__ == "__main__":
    main()

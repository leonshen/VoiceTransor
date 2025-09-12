# -*- coding: utf-8 -*-
"""PDF export using ReportLab, with optional CJK font embedding."""
from __future__ import annotations
from pathlib import Path
from typing import Optional

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer


def export_result_to_pdf(output_pdf: Path, title: str, body_text: str, font_path: Optional[Path] = None) -> None:
    """Export a summary as a single-page PDF.

    Args:
        output_pdf: Target PDF file path.
        title: Document title.
        body_text: Summary text (plain).
        font_path: Optional TTF/OTF file to support CJK glyphs.

    Notes:
        ReportLab's default fonts do not include CJK glyphs. If your text
        contains Chinese/Japanese/Korean characters, provide a font such as
        NotoSansSC-Regular.otf to avoid tofu (square boxes).
    """
    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    body_style = styles["BodyText"]

    if font_path:
        font_name = "VoiceTransorFont"
        pdfmetrics.registerFont(TTFont(font_name, str(font_path)))
        title_style = ParagraphStyle("TitleCJK", parent=styles["Title"], fontName=font_name)
        body_style = ParagraphStyle("BodyCJK", parent=styles["BodyText"], fontName=font_name, leading=14)

    story = []
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 8 * mm))

    safe_text = (
        body_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br/>")
    )
    story.append(Paragraph(safe_text, body_style))

    doc = SimpleDocTemplate(str(output_pdf), pagesize=A4,
                            leftMargin=20 * mm, rightMargin=20 * mm,
                            topMargin=20 * mm, bottomMargin=20 * mm)
    doc.build(story)

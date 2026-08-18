"""
Exports the AI summary (or study notes) as a downloadable PDF or TXT file.
"""
from pathlib import Path

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

from config import OUTPUT_FOLDER


def export_txt(job_id: str, title: str, content: str) -> str:
    path = OUTPUT_FOLDER / f"{job_id}_summary.txt"
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"{title}\n{'=' * len(title)}\n\n{content}\n")
    return str(path)


def export_pdf(job_id: str, title: str, content: str) -> str:
    path = OUTPUT_FOLDER / f"{job_id}_summary.pdf"

    doc = SimpleDocTemplate(
        str(path), pagesize=LETTER,
        topMargin=0.9 * inch, bottomMargin=0.9 * inch,
        leftMargin=0.9 * inch, rightMargin=0.9 * inch,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "JarvisTitle", parent=styles["Heading1"],
        textColor=colors.HexColor("#0b3d3d"), spaceAfter=14,
    )
    body_style = ParagraphStyle(
        "JarvisBody", parent=styles["BodyText"],
        leading=16, spaceAfter=10,
    )

    story = [Paragraph(title, title_style), Spacer(1, 6)]
    for para in content.split("\n\n"):
        cleaned = para.strip().replace("\n", "<br/>")
        if cleaned:
            story.append(Paragraph(cleaned, body_style))

    doc.build(story)
    return str(path)

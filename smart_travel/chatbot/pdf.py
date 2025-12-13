from io import BytesIO
from pathlib import Path

from reportlab.lib.enums import TA_CENTER, TA_LEFT  # type: ignore
from reportlab.lib.pagesizes import letter  # type: ignore
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet  # type: ignore
from reportlab.lib.units import inch  # type: ignore
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer  # type: ignore

styles = getSampleStyleSheet()

PDF_PARAMS__PAGE_MARGIN = 72
PDF_PARAMS__TITLE_STYLE = ParagraphStyle(
    "CustomTitle",
    parent=styles["Heading1"],
    fontSize=24,
    textColor="#1a1a1a",
    spaceAfter=30,
    alignment=TA_CENTER,
    fontName="Helvetica-Bold",
)
PDF_PARAMS__BODY_STYLE = ParagraphStyle(
    "CustomBody",
    parent=styles["BodyText"],
    fontSize=11,
    textColor="#333333",
    alignment=TA_LEFT,
    fontName="Helvetica",
    leading=16,  # Line spacing
)


class PDFCreator:
    def __init__(self, title: str, content: str):
        self.title = title
        self.content = content
        self.buffer = BytesIO()

    def create(self) -> BytesIO:
        doc = SimpleDocTemplate(
            self.buffer,
            pagesize=letter,
            rightMargin=PDF_PARAMS__PAGE_MARGIN,
            leftMargin=PDF_PARAMS__PAGE_MARGIN,
            topMargin=PDF_PARAMS__PAGE_MARGIN,
            bottomMargin=PDF_PARAMS__PAGE_MARGIN,
        )

        elements = []

        title_paragraph = Paragraph(self.title, PDF_PARAMS__TITLE_STYLE)
        elements.append(title_paragraph)
        elements.append(Spacer(1, 0.2 * inch))

        for paragraph_text in self.content.split("\n\n"):
            if paragraph_text.strip():
                content_paragraph = Paragraph(
                    paragraph_text.replace("\n", "<br/>"), PDF_PARAMS__BODY_STYLE
                )
                elements.append(content_paragraph)
                elements.append(Spacer(1, 0.15 * inch))

        doc.build(elements)
        self.buffer.seek(0)
        return self.buffer

    def save_to_file(self, path: Path):
        buffer = self.create()
        with open(path, "wb") as f:
            f.write(buffer.read())

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from io import BytesIO


class PDFCreator:
    """
    Creates a PDF document with a title and content.
    Returns a BytesIO buffer suitable for download/response.
    """

    def __init__(self, title: str, content: str):
        self.title = title
        self.content = content
        self.buffer = BytesIO()

    def create(self) -> BytesIO:
        """
        Generate the PDF and return a BytesIO buffer.
        """
        # Create PDF document
        doc = SimpleDocTemplate(
            self.buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
        )

        # Container for PDF elements
        elements = []

        # Get default styles
        styles = getSampleStyleSheet()

        # Create custom title style
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=24,
            textColor="#1a1a1a",
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName="Helvetica-Bold",
        )

        # Create custom body style
        body_style = ParagraphStyle(
            "CustomBody",
            parent=styles["BodyText"],
            fontSize=11,
            textColor="#333333",
            alignment=TA_LEFT,
            fontName="Helvetica",
            leading=16,  # Line spacing
        )

        # Add title
        title_paragraph = Paragraph(self.title, title_style)
        elements.append(title_paragraph)
        elements.append(Spacer(1, 0.2 * inch))

        # Add content (handle multiple paragraphs)
        for paragraph_text in self.content.split("\n\n"):
            if paragraph_text.strip():
                content_paragraph = Paragraph(
                    paragraph_text.replace("\n", "<br/>"), body_style
                )
                elements.append(content_paragraph)
                elements.append(Spacer(1, 0.15 * inch))

        # Build PDF
        doc.build(elements)

        # Reset buffer position to beginning
        self.buffer.seek(0)

        return self.buffer

    def save_to_file(self, filename: str) -> None:
        """
        Save the PDF to a file on disk.
        """
        buffer = self.create()
        with open(filename, "wb") as f:
            f.write(buffer.read())


# Usage examples:

# 1. Create and save to file
pdf = PDFCreator(
    title="Numerical Analysis Report",
    content="""This is the first paragraph of my report.

This is the second paragraph with some more details about the Gauss-Seidel method.

Final paragraph with conclusions.""",
)
pdf.save_to_file("report.pdf")

# 2. Django view example (for downloadable response)
"""
from django.http import HttpResponse

def download_pdf(request):
    pdf = PDFCreator(
        title=request.POST.get('title'),
        content=request.POST.get('content')
    )
    
    buffer = pdf.create()
    
    response = HttpResponse(buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="document.pdf"'
    
    return response
"""

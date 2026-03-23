import pdfplumber
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet


def extract_text_from_pdf(file_path):
    text = ""

    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""

    return text

def create_pdf(output_path, content):
    doc = SimpleDocTemplate(output_path)
    styles = getSampleStyleSheet()

    story = []

    for line in content.split("\n"):
        story.append(Paragraph(line, styles["Normal"]))

    doc.build(story)
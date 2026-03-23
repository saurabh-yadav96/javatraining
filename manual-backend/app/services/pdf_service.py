from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet

def generate_pdf(path, data, images):
    styles = getSampleStyleSheet()
    content = []

    # Title
    content.append(Paragraph(data["title"], styles['Title']))
    content.append(Spacer(1, 12))

    # Sections
    def add_section(title, text):
        if text:
            content.append(Paragraph(title, styles['Heading2']))
            content.append(Spacer(1, 6))
            content.append(Paragraph(text, styles['BodyText']))
            content.append(Spacer(1, 10))

    add_section("1. Introduction", data.get("introduction"))
    add_section("2. Purpose", data.get("purpose"))
    add_section("3. Prerequisites", data.get("prerequisites"))

    # Steps
    content.append(Paragraph("4. Procedure", styles['Heading2']))
    content.append(Spacer(1, 10))

    for i, step in enumerate(data["steps"]):

        content.append(Paragraph(f"Step {i+1}", styles['Heading3']))
        content.append(Spacer(1, 5))

    if i < len(images) and images[i]:
        content.append(Image(images[i], width=400, height=220))
        content.append(Spacer(1, 5))

    content.append(Paragraph(step, styles['BodyText']))
    content.append(Spacer(1, 12))

    doc = SimpleDocTemplate(path)
    doc.build(content)

    return path
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Optional
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from groq import Groq
from fastapi import UploadFile, File
from PyPDF2 import PdfReader
from docx import Document
from reportlab.platypus import PageBreak
from reportlab.pdfgen import canvas
from datetime import datetime

import os
import json
import base64
import asyncio

# PDF
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet

# ================= INIT =================
client = Groq(api_key="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")

app = FastAPI(title="Manual Generator with Screenshots")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = "manual-storage"
os.makedirs(BASE_DIR, exist_ok=True)

# ================= REQUEST MODEL =================
class StepRequest(BaseModel):
    steps: List[Dict]
    frs: Optional[str] = None


# ================= HELPERS =================

def format_steps(steps: List[Dict]) -> str:
    result = []
    for step in steps:
        if step.get("type") == "click":
            text = step.get("text") or "button"
            result.append(f"Click on the {text} button")
        elif step.get("type") == "input":
            field = step.get("field") or "field"
            result.append(f"Enter {field} in the {field} field")
    return "\n".join(result)


def call_groq(prompt: str) -> str:
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )
    return response.choices[0].message.content.strip()


def generate_title(frs: Optional[str]) -> str:
    if not frs:
        return "User Manual"

    prompt = f"""
Generate a short title (max 5 words) for a user manual based on the FRS below.
Respond with only the title, no punctuation, no extra text.

FRS:
{frs}

Example output:
Login Process
"""
    title = call_groq(prompt)
    title = " ".join(title.strip().split())          # collapse whitespace/newlines
    words = title.split()
    if len(words) > 5:
        title = " ".join(words[:5])                  # hard-enforce 5-word limit

    return f"User Manual: {title}" if title else "User Manual"


def generate_intro_purpose(frs: Optional[str]) -> Dict:
    if not frs:
        return {"introduction": "", "purpose": ""}

    prompt = f"""
FRS:
{frs}

Generate:
Introduction (max 5 lines)
Purpose (max 4 lines)

Format:
Introduction: ...
Purpose: ...
"""

    output = call_groq(prompt)

    intro, purpose = "", ""

    for line in output.split("\n"):
        if line.lower().startswith("introduction"):
            intro = line.split(":", 1)[-1].strip()
        elif line.lower().startswith("purpose"):
            purpose = line.split(":", 1)[-1].strip()

    return {"introduction": intro, "purpose": purpose}


def generate_steps(formatted_steps: str) -> List[str]:
    prompt = f"""
You are a senior technical writer at a software company.
Your job is to write one section of a user manual that real people will read.

Each step should:
- Open with a short, action-oriented heading (e.g. "Updating Your File Number", not "Step 1: Initiating File Number Update")
- Follow with 2–3 sentences that feel like a knowledgeable colleague guiding the user
- Mention what the user does AND what they will see or experience afterward
- Use natural English — write the way a human explains something to another human
- Never use phrases like: "initiate", "execute", "proceed to", "click the button", "perform the action"
- Prefer specific, concrete language: "select your file from the list" over "choose the appropriate item"

Tone reference:
Bad:  "Step 1: Initiating File Number Update. Click the update button to initiate the file number update process."
Good: "Updating Your File Number — Find the file you want to change and select Edit from the options next to it.
       A small panel will open on the right where you can type in the new number.
       Once you save, the change takes effect immediately across the system."

Actions to convert:
{formatted_steps}

Output format (repeat for each step, no extra text):
Step N: <short action-oriented heading>
Description: <2–3 natural, human sentences>
"""

    output = call_groq(prompt)

    steps = []
    current_step = ""

    for line in output.split("\n"):
        line = line.strip()

        if line.lower().startswith("step"):
            if current_step:
                steps.append(current_step.strip())
            current_step = line  # start new step

        elif line.lower().startswith("description"):
            desc = line.split(":", 1)[-1].strip()
            current_step += f"\n{desc}"

    if current_step:
        steps.append(current_step.strip())

    return steps


# ================= FILE STORAGE =================

def get_next_version(project_path):
    if not os.path.exists(project_path):
        return 1

    files = os.listdir(project_path)
    versions = [
        int(f.replace("v", "").replace(".json", ""))
        for f in files if f.startswith("v") and f.endswith(".json")
    ]

    return max(versions) + 1 if versions else 1


def save_manual(project_id: int, data: dict):
    project_path = os.path.join(BASE_DIR, f"project_{project_id}")
    os.makedirs(project_path, exist_ok=True)

    version = get_next_version(project_path)

    json_path = os.path.join(project_path, f"v{version}.json")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

    return version, json_path


# ================= SCREENSHOT SAVE =================

def save_screenshot(image_base64, project_id, version, step_index):
    folder = os.path.join(BASE_DIR, f"project_{project_id}", f"v{version}_images")
    os.makedirs(folder, exist_ok=True)

    try:
        image_data = image_base64.split(",")[1]
    except:
        image_data = image_base64

    file_path = os.path.join(folder, f"step_{step_index}.png")

    with open(file_path, "wb") as f:
        f.write(base64.b64decode(image_data))

    return file_path

def add_page_number(canvas, doc):
    page_num = canvas.getPageNumber()
    text = f"Page {page_num}"

    canvas.setFont("Helvetica", 9)
    canvas.drawRightString(550, 20, text)
def add_page_number(canvas, doc):
    if doc.page > 1:
        page_num = canvas.getPageNumber()
        text = f"Page {page_num}"
        canvas.setFont("Helvetica", 9)
        canvas.drawRightString(550, 20, text)
# ================= PDF GENERATION =================

def generate_pdf(project_id, version, data, image_paths):

    print(" generate_pdf called")
    current_date = datetime.now().strftime("%d %b %Y")

    folder = os.path.join(BASE_DIR, f"project_{project_id}")
    os.makedirs(folder, exist_ok=True)

    pdf_path = os.path.join(folder, f"v{version}.pdf")

    styles = getSampleStyleSheet()
    content = []

    try:
        # ================= COVER PAGE =================
        content.append(Spacer(1, 100))

        content.append(Paragraph(data.get("title", "User Manual"), styles['Title']))
        content.append(Spacer(1, 30))

        content.append(Paragraph("Generated User Manual", styles['Heading2']))
        content.append(Spacer(1, 20))

        #Paragraph(f"Generated on: {current_date}", styles['Normal'])
        content.append(Paragraph(f"Generated on: {current_date}", styles['Normal']))

        #content.append(Paragraph("Generated on: " + str(os.popen('date').read()), styles['Normal']))

        # Move to next page
        content.append(PageBreak())

        # Introduction
        if data.get("introduction"):
            content.append(Paragraph("Introduction", styles['Heading2']))
            content.append(Paragraph(data["introduction"], styles['BodyText']))

        # Purpose
        if data.get("purpose"):
            content.append(Paragraph("Purpose", styles['Heading2']))
            content.append(Paragraph(data["purpose"], styles['BodyText']))

        # Prerequisites
        if data.get("prerequisites"):
            content.append(Paragraph("Prerequisites", styles['Heading2']))
            content.append(Paragraph(data["prerequisites"], styles['BodyText']))

        content.append(Spacer(1, 10))

        # Steps
        content.append(Paragraph("Steps", styles['Heading2']))

        for i, step in enumerate(data.get("steps", [])):

            # Safe image handling
            if i < len(image_paths):
                img_path = image_paths[i]

                if img_path and os.path.exists(img_path):
                    try:
                        content.append(Image(img_path, width=300, height=180))
                        content.append(Spacer(1, 5))
                    except Exception as e:
                        print(" Image failed:", e)

            step_parts = step.split("\n", 1)

            title = step_parts[0]
            description = step_parts[1] if len(step_parts) > 1 else ""

            content.append(Paragraph(title, styles['Heading3']))
            content.append(Paragraph(description, styles['BodyText']))
            content.append(Spacer(1, 10))
            content.append(Spacer(1, 10))

        #  CREATE PDF HERE
        doc = SimpleDocTemplate(pdf_path)
        doc.build(content, onFirstPage=add_page_number, onLaterPages=add_page_number)

        print(" PDF CREATED:", pdf_path)

    except Exception as e:
        print(" PDF ERROR:", e)

    return pdf_path


# ================= API =================

@app.get("/")
def home():
    return {"message": " Manual Generator Running"}


@app.post("/generate-manual")
async def generate_manual(req: StepRequest):

    raw_steps = req.steps
    frs = req.frs


    if not raw_steps:
        return {"status": "error", "message": "No steps provided"}

    print("Received steps:", raw_steps)

    formatted_steps = format_steps(raw_steps)

    # AI Generation
    title = generate_title(frs)
    intro_purpose = generate_intro_purpose(frs)
    steps_output = generate_steps(formatted_steps)

    manual_data = {
        "title": title,
        "introduction": intro_purpose["introduction"],
        "purpose": intro_purpose["purpose"],
        "steps": steps_output
    }

    # Save JSON
    project_id = 1
    version, json_path = save_manual(project_id, manual_data)

    # Save screenshots
    image_paths = []
    for i, step in enumerate(raw_steps, start=1):
        if "screenshot" in step and step["screenshot"]:
            path = save_screenshot(step["screenshot"], project_id, version, i)
            image_paths.append(path)
        else:
            image_paths.append(None)

    # Generate PDF with screenshots
    pdf_path = generate_pdf(project_id, version, manual_data, image_paths)

    return {
        "status": "success",
        "version": version,
        "json_path": json_path,
        "pdf_path": pdf_path,
        "data": manual_data
    }


# ================= DOWNLOAD =================

@app.get("/download/pdf/{project_id}/{version}")
def download_pdf(project_id: int, version: int):
    file_path = os.path.join(BASE_DIR, f"project_{project_id}", f"v{version}.pdf")
    return FileResponse(file_path, media_type='application/pdf', filename="manual.pdf")


# ================= RUN =================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)


def extract_text(file: UploadFile):
    filename = file.filename.lower()

    if filename.endswith(".pdf"):
        reader = PdfReader(file.file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text

    elif filename.endswith(".docx"):
        doc = Document(file.file)
        return "\n".join([p.text for p in doc.paragraphs])

    else:
        return file.file.read().decode("utf-8")

def extract_sections_from_frs(frs_text: str):

    prompt = f"""
You are a professional technical writer.

FRS:
{frs_text}

Generate:

Title:
Introduction:
Purpose:
Prerequisites:

STRICT RULES:
- Always use exact labels: Title:, Introduction:, Purpose:, Prerequisites:
- Each section must have content
- No markdown, no bold (**), no extra formatting
"""

    output = call_groq(prompt)

    print("🔥 LLM OUTPUT:\n", output)  # DEBUG

    result = {
        "title": "",
        "introduction": "",
        "purpose": "",
        "prerequisites": ""
    }

    current = None

    for line in output.split("\n"):
        line = line.strip()

        if not line:
            continue

        lower = line.lower()

        if lower.startswith("title"):
            current = "title"
            result["title"] = line.split(":",1)[-1].strip()
            continue

        elif lower.startswith("introduction"):
            current = "introduction"
            result["introduction"] = line.split(":",1)[-1].strip()
            continue

        elif lower.startswith("purpose"):
            current = "purpose"
            result["purpose"] = line.split(":",1)[-1].strip()
            continue

        elif lower.startswith("prerequisites"):
            current = "prerequisites"
            continue

        # 👇 MULTI-LINE SUPPORT (IMPORTANT)
        if current:
            result[current] += " " + line

    # clean spaces
    for key in result:
        result[key] = result[key].strip()

    return result



from fastapi import UploadFile, File, Form

@app.post("/generate-manual-from-frs")
async def generate_manual_from_frs(
    file: UploadFile = File(...),
    steps: str = Form(...)
):

    # 1. Extract FRS text
    frs_text = extract_text(file)

    # 2. Extract sections using AI
    sections = extract_sections_from_frs(frs_text)

    # 3. Parse steps
    try:
        raw_steps = json.loads(steps)
    except:
        raw_steps = []

    if not raw_steps:
        return {"error": "No steps provided"}

    formatted_steps = format_steps(raw_steps)
    steps_output = generate_steps(formatted_steps)

    # 4. Prepare manual
    manual_data = {
        "title": f"User Manual: {sections['title']}",
        "introduction": sections["introduction"],
        "purpose": sections["purpose"],
        "prerequisites": sections["prerequisites"],
        "steps": steps_output
    }

    # 5. Save manual
    project_id = 1
    version, _ = save_manual(project_id, manual_data)

    # 6. Save screenshots
    image_paths = []
    for i, step in enumerate(raw_steps, start=1):
        if "screenshot" in step and step["screenshot"]:
            path = save_screenshot(step["screenshot"], project_id, version, i)
            image_paths.append(path)
        else:
            image_paths.append(None)

    # 7. Generate PDF
    pdf_path = generate_pdf(project_id, version, manual_data, image_paths)
    #pdf_path = await asyncio.to_thread(generate_pdf, project_id, version, manual_data, image_paths)
    return {
        "status": "success",
        "pdf_path": pdf_path
    }
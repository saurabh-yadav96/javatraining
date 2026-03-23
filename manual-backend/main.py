from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Optional
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from groq import Groq
from fastapi import UploadFile, File
from PyPDF2 import PdfReader
from docx import Document

import os
import json
import base64

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
Generate a short title (max 5 words).

FRS:
{frs}

Example:
Login Process
"""

    title = call_groq(prompt)
    return f"User Manual: {title}"


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
You are a professional technical writer.

Convert the following actions into structured user manual steps.

Rules:
- Each step must have a clear title and explanation
- Explain what user should do
- Explain what happens after action
- Use professional tone
- Avoid robotic phrases like "click button"

Actions:
{formatted_steps}

Format:
Step 1: Title
Description: ...
"""

    output = call_groq(prompt)

    steps = []
    for line in output.split("\n"):
        if line.lower().startswith("step"):
            steps.append(line.split(":", 1)[-1].strip())

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


# ================= PDF GENERATION =================

def generate_pdf(project_id, version, data, image_paths):

    print(" generate_pdf called")

    folder = os.path.join(BASE_DIR, f"project_{project_id}")
    os.makedirs(folder, exist_ok=True)

    pdf_path = os.path.join(folder, f"v{version}.pdf")

    styles = getSampleStyleSheet()
    content = []

    try:
        # Title
        content.append(Paragraph(data.get("title", "User Manual"), styles['Title']))
        content.append(Spacer(1, 10))

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

            content.append(Paragraph(f"Step {i+1}: {step}", styles['BodyText']))
            content.append(Spacer(1, 10))

        #  CREATE PDF HERE
        doc = SimpleDocTemplate(pdf_path)
        doc.build(content)

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
You are a professional technical writer creating a user manual for end users.

Based on the following FRS content, generate user-friendly documentation sections.

Focus on:
- Making it easy for a non-technical user to understand
- Explaining purpose in a practical way
- Avoid copying exact lines from FRS
- Write as if guiding a real user

FRS Content:
{frs_text}

Generate the following sections:

Title:
- Short and meaningful (max 6 words)

Introduction:
- 3–4 lines
- Explain what the application does in simple terms
- Focus on user benefit

Purpose:
- 2–3 lines
- Explain why user would use this feature/system

Prerequisites:
- Bullet points
- Mention things user should have before starting (login, access, data, etc.)

Rules:
- Use clear and natural language
- Avoid technical jargon
- Do not sound like AI or documentation template
- Make it feel like a real product manual

Format strictly as:
Title: ...
Introduction: ...
Purpose: ...
Prerequisites:
- ...
- ...
"""

    output = call_groq(prompt)

    result = {
        "title": "",
        "introduction": "",
        "purpose": "",
        "prerequisites": ""
    }

    for line in output.split("\n"):
        if line.lower().startswith("title"):
            result["title"] = line.split(":",1)[-1].strip()
        elif line.lower().startswith("introduction"):
            result["introduction"] = line.split(":",1)[-1].strip()
        elif line.lower().startswith("purpose"):
            result["purpose"] = line.split(":",1)[-1].strip()
        elif line.lower().startswith("prerequisites"):
            result["prerequisites"] = line.split(":",1)[-1].strip()

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

    return {
        "status": "success",
        "pdf_path": pdf_path
    }
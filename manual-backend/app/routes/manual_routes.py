from fastapi import APIRouter
from app.models.request_models import StepRequest
from app.services.step_service import format_steps, generate_steps
from app.services.formatter import enhance_steps, generate_sections
from app.services.storage_service import save_manual
from app.services.pdf_service import generate_pdf

from fastapi import Form, UploadFile, File
import json
router = APIRouter()
@router.post("/generate-manual")
async def generate_manual(
    file: UploadFile = File(...),
    steps: str = Form(...)
):
    # ✅ parse steps
    try:
        steps = json.loads(steps)
    except:
        return {"error": "Invalid steps format"}

    print("🔥 STEPS:", steps)

    formatted = format_steps(steps)

    raw_steps = generate_steps(formatted)
    enhanced_steps = enhance_steps(raw_steps)

    sections = generate_sections("")

    manual = {
        "title": f"User Manual: {sections['title']}",
        "introduction": sections["introduction"],
        "purpose": sections["purpose"],
        "prerequisites": sections["prerequisites"],
        "steps": enhanced_steps
    }

    version, _ = save_manual(1, manual)

    pdf_path = f"manual-storage/project_1/v{version}.pdf"

    generate_pdf(pdf_path, manual, [])

    return {
        "status": "success",
        "version": version,
        "pdf": pdf_path,
        "data": manual
    }
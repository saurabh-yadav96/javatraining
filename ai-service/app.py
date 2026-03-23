from fastapi import FastAPI, UploadFile, File
from rag_pipeline import generate_manual
from pdf_utils import extract_text_from_pdf, create_pdf

app = FastAPI()

@app.post("/generate-from-pdf")
async def generate_from_pdf(file: UploadFile = File(...)):

    # Save uploaded file
    file_path = f"temp_{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())

    # Extract text from PDF
    frs_text = extract_text_from_pdf(file_path)

    # Generate manual
    manual = generate_manual(frs_text, "", "Generate user manual")

    # Save output PDF
    output_path = "user_manual.pdf"
    create_pdf(output_path, manual)

    return {
        "message": "Manual generated",
        "manual_text": manual,
        "pdf_path": output_path
    }
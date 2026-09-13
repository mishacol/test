import io

import pdfplumber
from fastapi import FastAPI, File, HTTPException, UploadFile

from .parser import extract_line_item_tables, parse_invoice_fields

app = FastAPI(title="Extraction Service")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/extract")
async def extract(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only application/pdf is supported")

    raw_bytes = await file.read()
    if not raw_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    try:
        with pdfplumber.open(io.BytesIO(raw_bytes)) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
            tables = extract_line_item_tables(pdf)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Could not parse PDF: {exc}") from exc

    if not text.strip():
        raise HTTPException(
            status_code=422,
            detail="No extractable text found (file may be a scanned image without OCR support)",
        )

    fields = parse_invoice_fields(text)

    return {
        "text": text,
        "fields": fields,
        "line_items": tables,
    }

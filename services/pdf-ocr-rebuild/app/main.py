import io

import pymupdf
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from .ocr import ocr_page_words, render_page_to_image
from .rebuild import build_pdf_from_pages

app = FastAPI(title="PDF OCR Rebuild Service")

DEFAULT_DPI = 300
MIN_CONFIDENCE = 40.0


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/convert")
async def convert(file: UploadFile = File(...), lang: str = "eng", dpi: int = DEFAULT_DPI):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only application/pdf is supported")

    raw_bytes = await file.read()
    if not raw_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    try:
        source_doc = pymupdf.open(stream=raw_bytes, filetype="pdf")
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Could not open PDF: {exc}") from exc

    pages_data = []
    for page in source_doc:
        image = render_page_to_image(page, dpi=dpi)
        words = ocr_page_words(image, lang=lang)
        pages_data.append(
            {
                "width_pt": page.rect.width,
                "height_pt": page.rect.height,
                "dpi": dpi,
                "words": words,
            }
        )
    source_doc.close()

    if not any(p["words"] for p in pages_data):
        raise HTTPException(status_code=422, detail="No text could be recognized on any page")

    new_doc = build_pdf_from_pages(pages_data, min_confidence=MIN_CONFIDENCE)
    output_bytes = new_doc.tobytes()
    new_doc.close()

    base_name = (file.filename or "document").rsplit(".", 1)[0]
    return StreamingResponse(
        io.BytesIO(output_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{base_name}_rebuilt.pdf"'},
    )

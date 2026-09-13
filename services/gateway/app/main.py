import os

import httpx
from fastapi import FastAPI, File, HTTPException, UploadFile

from . import db

EXTRACTION_SERVICE_URL = os.environ.get("EXTRACTION_SERVICE_URL", "http://localhost:8001")

app = FastAPI(title="Gateway Service")


@app.on_event("startup")
def on_startup():
    db.init_db()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/invoices")
async def upload_invoice(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only application/pdf is supported")

    raw_bytes = await file.read()
    invoice_id = db.create_invoice(file.filename)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{EXTRACTION_SERVICE_URL}/extract",
                files={"file": (file.filename, raw_bytes, "application/pdf")},
            )
        response.raise_for_status()
        result = response.json()
    except httpx.HTTPStatusError as exc:
        detail = exc.response.json().get("detail", str(exc))
        db.mark_failed(invoice_id, detail)
        raise HTTPException(status_code=422, detail=detail) from exc
    except httpx.RequestError as exc:
        detail = f"Extraction service unreachable: {exc}"
        db.mark_failed(invoice_id, detail)
        raise HTTPException(status_code=502, detail=detail) from exc

    db.mark_done(invoice_id, result["fields"], result["text"], result["line_items"])
    return db.get_invoice(invoice_id)


@app.get("/invoices")
def get_invoices():
    return db.list_invoices()


@app.get("/invoices/{invoice_id}")
def get_invoice(invoice_id: int):
    invoice = db.get_invoice(invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice

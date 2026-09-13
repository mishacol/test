import re
from datetime import datetime

INVOICE_NUMBER_PATTERNS = [
    r"invoice\s*(?:no\.?|number|#)\s*[:\-]?\s*([A-Z0-9][A-Z0-9\-\/]{2,})",
    r"inv\s*(?:no\.?|#)\s*[:\-]?\s*([A-Z0-9][A-Z0-9\-\/]{2,})",
]

DATE_PATTERNS = [
    r"\b(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})\b",
    r"\b([A-Z][a-z]{2,8}\s+\d{1,2},?\s+\d{4})\b",
]

TOTAL_LABELS = [
    "total due",
    "amount due",
    "balance due",
    "grand total",
    "total amount",
    "total",
]

CURRENCY_AMOUNT = r"[\$€£]?\s?[\d,]+\.\d{2}"


def _find_first(patterns, text, flags=re.IGNORECASE):
    for pattern in patterns:
        match = re.search(pattern, text, flags)
        if match:
            return match.group(1).strip()
    return None


def _find_total(text):
    lines = text.splitlines()
    for label in TOTAL_LABELS:
        for line in lines:
            if label in line.lower():
                amount_match = re.search(CURRENCY_AMOUNT, line)
                if amount_match:
                    return amount_match.group(0).strip()
    return None


def _find_vendor(text):
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return None


def _try_parse_date(raw_date):
    if not raw_date:
        return None
    formats = ["%m/%d/%Y", "%m-%d-%Y", "%d/%m/%Y", "%m/%d/%y", "%B %d, %Y", "%B %d %Y"]
    for fmt in formats:
        try:
            return datetime.strptime(raw_date, fmt).date().isoformat()
        except ValueError:
            continue
    return raw_date


def parse_invoice_fields(text: str) -> dict:
    invoice_number = _find_first(INVOICE_NUMBER_PATTERNS, text)
    raw_date = _find_first(DATE_PATTERNS, text)
    total = _find_total(text)
    vendor = _find_vendor(text)

    return {
        "invoice_number": invoice_number,
        "date": _try_parse_date(raw_date),
        "total": total,
        "vendor": vendor,
    }


def extract_line_item_tables(pdf) -> list:
    tables = []
    for page in pdf.pages:
        for table in page.extract_tables():
            if table and len(table) > 1:
                tables.append(table)
    return tables

import re
from decimal import Decimal, InvalidOperation
from pathlib import Path

import pdfplumber


TOTAL_RE = re.compile(r"(?:grand\s+)?total\s*[:\s]+(?:EUR|€)?\s*([0-9][0-9,]*\.?[0-9]*)", re.I)
INVOICE_NUMBER_RE = re.compile(r"invoice\s*(?:no\.?|number)?\s*[:#\-\s]+([A-Z0-9-]+)", re.I)


def extract_text_from_pdf(path: str) -> str:
    text_parts: list[str] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text_parts.append(page.extract_text() or "")
    return "\n".join(text_parts).strip()


def extract_text(path: str) -> str:
    suffix = Path(path).suffix.lower()
    if suffix == ".pdf":
        return extract_text_from_pdf(path)
    raise ValueError(f"Unsupported file type: {suffix}")


def extract_invoice_stub(text: str) -> dict:
    invoice_number = INVOICE_NUMBER_RE.search(text)
    total = TOTAL_RE.search(text)

    return {
        "invoice_number": invoice_number.group(1) if invoice_number else "UNKNOWN",
        "vendor_name": "UNKNOWN_VENDOR",
        "vendor_iban": None,
        "vat_number": None,
        "issue_date": None,
        "due_date": None,
        "currency": "EUR",
        "subtotal": Decimal("0"),
        "vat_total": Decimal("0"),
        "total": _parse_money(total.group(1)) if total else Decimal("0"),
        "line_items": [],
    }


def _parse_money(value: str) -> Decimal:
    normalized = value.replace(",", "").strip()
    try:
        return Decimal(normalized)
    except InvalidOperation as exc:
        raise ValueError(f"Invalid money amount: {value}") from exc

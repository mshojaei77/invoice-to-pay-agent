"""Legacy text extraction stub.

The graph now uses LiteParse and MinerU adapters via app.services.parser.
This module remains for reference only and is not used in production paths.
"""

import re
from decimal import Decimal, InvalidOperation
from pathlib import Path


TOTAL_RE = re.compile(r"(?:grand\s+)?total\s*[:\s]+(?:EUR|€)?\s*([0-9][0-9,]*\.?[0-9]*)", re.I)
INVOICE_NUMBER_RE = re.compile(r"invoice\s*(?:no\.?|number)?\s*[:#\-\s]+([A-Z0-9-]+)", re.I)


def extract_text(path: str) -> str:
    suffix = Path(path).suffix.lower()
    if suffix == ".pdf":
        raise ValueError("PDF extraction requires LiteParse or MinerU adapter")
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

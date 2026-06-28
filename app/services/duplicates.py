from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path

from rapidfuzz import fuzz


@dataclass(frozen=True)
class DuplicateCandidate:
    invoice_number: str
    vendor_name: str
    total_amount: str
    issue_date: str
    reason: str
    score: float


def load_seen_invoices(path: Path) -> list[dict]:
    if not path.exists():
        return []

    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def check_duplicate(
    vendor_name: str,
    invoice_number: str,
    total_amount: Decimal,
    issue_date: date,
    seen_path: Path = Path("data/processed/seen_invoices.jsonl"),
) -> dict:
    seen = load_seen_invoices(seen_path)
    candidates: list[DuplicateCandidate] = []

    for old in seen:
        vendor_score = fuzz.token_sort_ratio(vendor_name.upper(), old["vendor_name"].upper())

        if vendor_score >= 90 and invoice_number == old["invoice_number"]:
            candidates.append(
                DuplicateCandidate(
                    invoice_number=old["invoice_number"],
                    vendor_name=old["vendor_name"],
                    total_amount=old["total_amount"],
                    issue_date=old["issue_date"],
                    reason="same_vendor_and_invoice_number",
                    score=100.0,
                )
            )

        elif (
            vendor_score >= 85
            and str(total_amount) == old["total_amount"]
            and issue_date.isoformat() == old["issue_date"]
        ):
            candidates.append(
                DuplicateCandidate(
                    invoice_number=old["invoice_number"],
                    vendor_name=old["vendor_name"],
                    total_amount=old["total_amount"],
                    issue_date=old["issue_date"],
                    reason="same_vendor_total_and_issue_date",
                    score=float(vendor_score),
                )
            )

    if any(c.score == 100.0 for c in candidates):
        status = "confirmed_duplicate"
    elif candidates:
        status = "possible_duplicate"
    else:
        status = "clear"

    return {
        "duplicate_status": status,
        "duplicate_candidates": [c.__dict__ for c in candidates],
    }

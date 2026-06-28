import json
from datetime import date
from decimal import Decimal
from pathlib import Path

from app.services.duplicates import check_duplicate


def write_seen(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record) + "\n")


def test_clear_when_no_seen_invoices(tmp_path: Path) -> None:
    path = tmp_path / "seen.jsonl"
    result = check_duplicate("Acme BV", "INV-001", Decimal("121.00"), date(2026, 6, 1), seen_path=path)
    assert result["duplicate_status"] == "clear"
    assert result["duplicate_candidates"] == []


def test_confirmed_duplicate_same_invoice_number(tmp_path: Path) -> None:
    path = tmp_path / "seen.jsonl"
    write_seen(path, [
        {
            "vendor_name": "Acme BV",
            "invoice_number": "INV-001",
            "total_amount": "121.00",
            "issue_date": "2026-06-01",
        }
    ])

    result = check_duplicate("Acme BV", "INV-001", Decimal("121.00"), date(2026, 6, 1), seen_path=path)
    assert result["duplicate_status"] == "confirmed_duplicate"
    assert len(result["duplicate_candidates"]) == 1
    assert result["duplicate_candidates"][0]["score"] == 100.0


def test_possible_duplicate_with_fuzzy_vendor_name(tmp_path: Path) -> None:
    path = tmp_path / "seen.jsonl"
    write_seen(path, [
        {
            "vendor_name": "ACME B.V.",
            "invoice_number": "INV-001",
            "total_amount": "121.00",
            "issue_date": "2026-06-01",
        }
    ])

    result = check_duplicate("Acme BV", "INV-001", Decimal("121.00"), date(2026, 6, 1), seen_path=path)
    assert result["duplicate_status"] == "possible_duplicate"


def test_confirmed_duplicate_same_total_and_date(tmp_path: Path) -> None:
    path = tmp_path / "seen.jsonl"
    write_seen(path, [
        {
            "vendor_name": "ACME BV",
            "invoice_number": "INV-999",
            "total_amount": "121.00",
            "issue_date": "2026-06-01",
        }
    ])

    result = check_duplicate("Acme BV", "INV-001", Decimal("121.00"), date(2026, 6, 1), seen_path=path)
    assert result["duplicate_status"] == "confirmed_duplicate"


def test_different_invoice_clean(tmp_path: Path) -> None:
    path = tmp_path / "seen.jsonl"
    write_seen(path, [
        {
            "vendor_name": "Other Corp",
            "invoice_number": "INV-001",
            "total_amount": "500.00",
            "issue_date": "2026-05-01",
        }
    ])

    result = check_duplicate("Acme BV", "INV-002", Decimal("121.00"), date(2026, 6, 1), seen_path=path)
    assert result["duplicate_status"] == "clear"


def test_multiple_candidates(tmp_path: Path) -> None:
    path = tmp_path / "seen.jsonl"
    write_seen(path, [
        {
            "vendor_name": "Acme BV",
            "invoice_number": "INV-001",
            "total_amount": "121.00",
            "issue_date": "2026-06-01",
        },
        {
            "vendor_name": "Acme BV",
            "invoice_number": "INV-999",
            "total_amount": "121.00",
            "issue_date": "2026-06-01",
        },
    ])

    result = check_duplicate("Acme BV", "INV-001", Decimal("121.00"), date(2026, 6, 1), seen_path=path)
    assert result["duplicate_status"] == "confirmed_duplicate"
    assert len(result["duplicate_candidates"]) >= 1

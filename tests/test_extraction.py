from decimal import Decimal

import pytest

from app.services.extraction import (
    _parse_money,
    extract_invoice_stub,
    extract_text,
)


def test_extract_invoice_stub_finds_invoice_number_and_total() -> None:
    invoice = extract_invoice_stub(
        """
        Invoice Number: INV-2026-001
        Vendor: Acme BV
        Total: EUR 1,234.56
        """
    )

    assert invoice["invoice_number"] == "INV-2026-001"
    assert invoice["total"] == Decimal("1234.56")


def test_extract_invoice_stub_uses_safe_defaults() -> None:
    invoice = extract_invoice_stub("No structured fields here")

    assert invoice["invoice_number"] == "UNKNOWN"
    assert invoice["vendor_name"] == "UNKNOWN_VENDOR"
    assert invoice["total"] == Decimal("0")


def test_extract_text_rejects_all_file_types() -> None:
    with pytest.raises(ValueError, match="Unsupported file type"):
        extract_text("invoice.txt")

    with pytest.raises(ValueError, match="requires LiteParse or MinerU"):
        extract_text("invoice.pdf")


def test_parse_money() -> None:
    assert _parse_money("1,234.56") == Decimal("1234.56")
    assert _parse_money("100") == Decimal("100")
    assert _parse_money("0.99") == Decimal("0.99")

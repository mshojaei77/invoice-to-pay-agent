from datetime import date
from decimal import Decimal
from pathlib import Path

from app.schemas.common import Party
from app.schemas.invoice import Invoice
from app.schemas.parsed_document import ParsedDocument
from app.services.validation import validate_invoice_business_rules


def make_invoice(
    vendor_name: str = "Acme BV",
    iban: str = "NL91ABNA0417164300",
    vat: str = "NL001234567B01",
) -> Invoice:
    return Invoice(
        invoice_number="INV-001",
        vendor=Party(name=vendor_name, iban=iban, vat_number=vat),
        issue_date=date(2026, 6, 1),
        currency="EUR",
        line_items=[
            {
                "description": "Consulting",
                "quantity": Decimal("1"),
                "unit_price": Decimal("100.00"),
                "line_total": Decimal("100.00"),
            }
        ],
        subtotal=Decimal("100.00"),
        tax_amount=Decimal("21.00"),
        total_amount=Decimal("121.00"),
    )


def make_parsed(confidence: float = 0.95, warnings: list[str] | None = None) -> ParsedDocument:
    return ParsedDocument(
        parser_name="liteparse",
        parser_version="2.2.1",
        document_type="invoice",
        text="Invoice text",
        markdown="# Invoice",
        tables=[],
        blocks=[],
        images=[],
        page_count=1,
        confidence=confidence,
        warnings=warnings or [],
        raw_artifact_path=Path("raw.json"),
    )


def test_missing_invoice_returns_high_severity_error() -> None:
    errors = validate_invoice_business_rules(None, [], True, True)
    assert len(errors) == 1
    assert errors[0].code == "missing_invoice"
    assert errors[0].severity == "high"


def test_missing_po_and_delivery_note() -> None:
    errors = validate_invoice_business_rules(make_invoice(), [make_parsed()], False, False)
    codes = {e.code for e in errors}
    assert "missing_po" in codes
    assert "missing_delivery_note" in codes


def test_valid_invoice_has_no_errors() -> None:
    errors = validate_invoice_business_rules(make_invoice(), [make_parsed()], True, True)
    assert len(errors) == 0


def test_missing_vendor_name() -> None:
    inv = Invoice.model_construct(
        invoice_number="INV-001",
        vendor=Party.model_construct(name=""),
        issue_date=date(2026, 6, 1),
        currency="EUR",
        line_items=[
            {
                "description": "Consulting",
                "quantity": Decimal("1"),
                "unit_price": Decimal("100.00"),
                "line_total": Decimal("100.00"),
            }
        ],
        subtotal=Decimal("100.00"),
        tax_amount=Decimal("21.00"),
        total_amount=Decimal("121.00"),
    )
    errors = validate_invoice_business_rules(inv, [make_parsed()], True, True)
    assert any(e.code == "missing_vendor" for e in errors)


def test_missing_iban() -> None:
    inv = make_invoice(iban=None)
    errors = validate_invoice_business_rules(inv, [make_parsed()], True, True)
    assert any(e.code == "missing_iban" for e in errors)


def test_invalid_iban_format() -> None:
    inv = make_invoice(iban="12345")
    errors = validate_invoice_business_rules(inv, [make_parsed()], True, True)
    assert any(e.code == "invalid_iban" for e in errors)


def test_missing_vat() -> None:
    inv = make_invoice(vat=None)
    errors = validate_invoice_business_rules(inv, [make_parsed()], True, True)
    assert any(e.code == "missing_vat" for e in errors)


def test_invalid_vat_format() -> None:
    inv = make_invoice(vat="12345")
    errors = validate_invoice_business_rules(inv, [make_parsed()], True, True)
    assert any(e.code == "invalid_vat" for e in errors)


def test_low_parser_confidence() -> None:
    errors = validate_invoice_business_rules(
        make_invoice(), [make_parsed(confidence=0.5)], True, True
    )
    assert any(e.code == "low_parser_confidence" for e in errors)


def test_high_confidence_passes() -> None:
    errors = validate_invoice_business_rules(
        make_invoice(), [make_parsed(confidence=0.95)], True, True
    )
    assert not any(e.code == "low_parser_confidence" for e in errors)


def test_handwritten_correction() -> None:
    errors = validate_invoice_business_rules(
        make_invoice(), [make_parsed(warnings=["handwriting"])], True, True
    )
    assert any(e.code == "handwritten_correction" for e in errors)


def test_multiple_errors_collected() -> None:
    inv = Invoice.model_construct(
        invoice_number="INV-001",
        vendor=Party.model_construct(name=""),
        issue_date=date(2026, 6, 1),
        currency="EUR",
        line_items=[
            {
                "description": "Consulting",
                "quantity": Decimal("1"),
                "unit_price": Decimal("100.00"),
                "line_total": Decimal("100.00"),
            }
        ],
        subtotal=Decimal("100.00"),
        tax_amount=Decimal("21.00"),
        total_amount=Decimal("121.00"),
    )
    errors = validate_invoice_business_rules(inv, [make_parsed(confidence=0.5)], False, False)
    codes = {e.code for e in errors}
    assert "missing_vendor" in codes
    assert "missing_iban" in codes
    assert "missing_vat" in codes
    assert "low_parser_confidence" in codes
    assert "missing_po" in codes
    assert "missing_delivery_note" in codes

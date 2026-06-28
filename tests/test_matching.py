from datetime import date
from decimal import Decimal

from app.schemas.common import Party
from app.schemas.delivery_note import DeliveryNote
from app.schemas.invoice import Invoice
from app.schemas.purchase_order import PurchaseOrder
from app.services.matching import match_invoice_po_delivery


def make_party(name: str = "Acme BV") -> Party:
    return Party(name=name, iban="NL91ABNA0417164300", vat_number="NL001234567B01")


def make_invoice(
    po_number: str = "PO-001",
    vendor_name: str = "Acme BV",
    currency: str = "EUR",
    subtotal: Decimal = Decimal("100.00"),
    tax: Decimal = Decimal("21.00"),
    total: Decimal = Decimal("121.00"),
) -> Invoice:
    return Invoice(
        invoice_number="INV-001",
        po_number=po_number,
        vendor=make_party(name=vendor_name),
        issue_date=date(2026, 6, 1),
        currency=currency,
        line_items=[
            {
                "description": "Consulting",
                "quantity": Decimal("1"),
                "unit_price": Decimal("100.00"),
                "line_total": Decimal("100.00"),
            }
        ],
        subtotal=subtotal,
        tax_amount=tax,
        total_amount=total,
    )


def make_po(
    po_number: str = "PO-001",
    vendor_name: str = "Acme BV",
    currency: str = "EUR",
    subtotal: Decimal = Decimal("100.00"),
    tax: Decimal = Decimal("21.00"),
    total: Decimal = Decimal("121.00"),
) -> PurchaseOrder:
    return PurchaseOrder(
        po_number=po_number,
        vendor=make_party(name=vendor_name),
        issue_date=date(2026, 5, 1),
        currency=currency,
        line_items=[
            {
                "description": "Consulting",
                "quantity": Decimal("1"),
                "unit_price": Decimal("100.00"),
                "line_total": Decimal("100.00"),
            }
        ],
        subtotal=subtotal,
        tax_amount=tax,
        total_amount=total,
    )


def make_dn(
    po_number: str = "PO-001",
    vendor_name: str = "Acme BV",
    delivery_status: str = "delivered",
) -> DeliveryNote:
    return DeliveryNote(
        delivery_note_number="DN-001",
        po_number=po_number,
        vendor=make_party(name=vendor_name),
        delivery_date=date(2026, 6, 5),
        delivered_items=[
            {
                "description": "Delivered Item",
                "quantity": Decimal("1"),
                "unit_price": Decimal("100.00"),
                "line_total": Decimal("100.00"),
            }
        ],
        delivery_status=delivery_status,
    )


def test_matched_when_all_align() -> None:
    result = match_invoice_po_delivery(
        make_invoice(),
        make_po(),
        make_dn(),
    )
    assert result["match_status"] == "matched"
    assert result["mismatch_reasons"] == []


def test_missing_po() -> None:
    result = match_invoice_po_delivery(make_invoice(), None, make_dn())
    assert result["match_status"] == "mismatch"
    assert "missing_purchase_order" in result["mismatch_reasons"]


def test_missing_delivery_note() -> None:
    result = match_invoice_po_delivery(make_invoice(), make_po(), None)
    assert "missing_delivery_note" in result["mismatch_reasons"]


def test_po_number_mismatch() -> None:
    result = match_invoice_po_delivery(
        make_invoice(po_number="PO-001"),
        make_po(po_number="PO-999"),
        make_dn(po_number="PO-001"),
    )
    assert "po_number_mismatch" in result["mismatch_reasons"]


def test_vendor_mismatch() -> None:
    result = match_invoice_po_delivery(
        make_invoice(vendor_name="Acme BV"),
        make_po(vendor_name="Other Corp"),
        make_dn(),
    )
    assert "vendor_mismatch" in result["mismatch_reasons"]


def test_currency_mismatch() -> None:
    result = match_invoice_po_delivery(
        make_invoice(currency="EUR"),
        make_po(currency="USD"),
        make_dn(),
    )
    assert "currency_mismatch" in result["mismatch_reasons"]


def test_total_mismatch() -> None:
    result = match_invoice_po_delivery(
        make_invoice(total=Decimal("121.00")),
        make_po(total=Decimal("200.00")),
        make_dn(),
    )
    assert "total_mismatch" in result["mismatch_reasons"]


def test_subtotal_mismatch() -> None:
    result = match_invoice_po_delivery(
        make_invoice(subtotal=Decimal("100.00")),
        make_po(subtotal=Decimal("150.00")),
        make_dn(),
    )
    assert "subtotal_mismatch" in result["mismatch_reasons"]


def test_tax_mismatch() -> None:
    result = match_invoice_po_delivery(
        make_invoice(tax=Decimal("21.00")),
        make_po(tax=Decimal("30.00")),
        make_dn(),
    )
    assert "tax_mismatch" in result["mismatch_reasons"]


def test_delivery_po_number_mismatch() -> None:
    result = match_invoice_po_delivery(
        make_invoice(po_number="PO-001"),
        make_po(),
        make_dn(po_number="PO-999"),
    )
    assert "delivery_po_number_mismatch" in result["mismatch_reasons"]


def test_delivery_not_complete() -> None:
    result = match_invoice_po_delivery(
        make_invoice(),
        make_po(),
        make_dn(delivery_status="pending"),
    )
    assert "delivery_not_complete" in result["mismatch_reasons"]


def test_delivery_complete_accepts_variants() -> None:
    for status in ["Delivered", "Complete", "Received", "delivered"]:
        result = match_invoice_po_delivery(
            make_invoice(),
            make_po(),
            make_dn(delivery_status=status),
        )
        assert result["match_status"] == "matched"


def test_multiple_mismatches() -> None:
    result = match_invoice_po_delivery(
        make_invoice(po_number="PO-001", vendor_name="Acme BV", currency="EUR"),
        make_po(po_number="PO-999", vendor_name="Other Corp", currency="USD"),
        make_dn(po_number="PO-999"),
    )
    reasons = result["mismatch_reasons"]
    assert "po_number_mismatch" in reasons
    assert "vendor_mismatch" in reasons
    assert "currency_mismatch" in reasons
    assert "delivery_po_number_mismatch" in reasons

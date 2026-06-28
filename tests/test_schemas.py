from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.invoice import Invoice
from app.schemas.purchase_order import PurchaseOrder


def test_valid_invoice_schema_passes() -> None:
    invoice = Invoice(
        invoice_number="INV-001",
        vendor_name="Acme BV",
        subtotal=Decimal("100.00"),
        vat_total=Decimal("21.00"),
        total=Decimal("121.00"),
        line_items=[
            {
                "description": "Consulting",
                "quantity": 1,
                "unit_price": Decimal("100.00"),
                "line_total": Decimal("100.00"),
            }
        ],
    )

    assert invoice.invoice_number == "INV-001"
    assert invoice.currency == "EUR"


def test_invoice_requires_invoice_number() -> None:
    with pytest.raises(ValidationError):
        Invoice(
            vendor_name="Acme BV",
            subtotal=Decimal("100.00"),
            vat_total=Decimal("21.00"),
            total=Decimal("121.00"),
            line_items=[],
        )


def test_invoice_rejects_negative_total() -> None:
    with pytest.raises(ValidationError):
        Invoice(
            invoice_number="INV-001",
            vendor_name="Acme BV",
            subtotal=Decimal("100.00"),
            vat_total=Decimal("21.00"),
            total=Decimal("-121.00"),
            line_items=[],
        )


def test_valid_purchase_order_schema_passes() -> None:
    po = PurchaseOrder(
        po_number="PO-001",
        vendor_name="Acme BV",
        total=Decimal("100.00"),
        line_items=[
            {
                "sku": "CONSULTING",
                "description": "Consulting",
                "quantity": 1,
                "unit_price": Decimal("100.00"),
                "line_total": Decimal("100.00"),
            }
        ],
    )

    assert po.po_number == "PO-001"
    assert po.currency == "EUR"

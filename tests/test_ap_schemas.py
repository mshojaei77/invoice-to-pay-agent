from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.common import LineItem, MoneyAmount, Party
from app.schemas.delivery_note import DeliveryNote
from app.schemas.invoice import Invoice
from app.schemas.purchase_order import PurchaseOrder


def make_party(name: str = "Acme BV") -> Party:
    return Party(name=name, iban="NL91ABNA0417164300", vat_number="NL001234567B01")


def make_line_item(
    description: str = "Consulting",
    quantity: Decimal = Decimal("1"),
    unit_price: Decimal = Decimal("100.00"),
) -> LineItem:
    return LineItem(
        description=description,
        quantity=quantity,
        unit_price=unit_price,
        line_total=quantity * unit_price,
    )


class TestMoneyAmount:
    def test_valid_money_amount(self) -> None:
        m = MoneyAmount(amount=Decimal("100.00"), currency="EUR")
        assert m.amount == Decimal("100.00")
        assert m.currency == "EUR"

    def test_zero_amount_rejected(self) -> None:
        with pytest.raises(ValidationError):
            MoneyAmount(amount=Decimal("0"), currency="EUR")

    def test_negative_amount_rejected(self) -> None:
        with pytest.raises(ValidationError):
            MoneyAmount(amount=Decimal("-10"), currency="EUR")

    def test_invalid_currency_rejected(self) -> None:
        with pytest.raises(ValidationError):
            MoneyAmount(amount=Decimal("100"), currency="JPY")


class TestLineItem:
    def test_valid_line_item(self) -> None:
        item = make_line_item()
        assert item.line_total == Decimal("100.00")

    def test_line_total_mismatch(self) -> None:
        with pytest.raises(ValidationError):
            LineItem(
                description="Consulting",
                quantity=Decimal("2"),
                unit_price=Decimal("50.00"),
                line_total=Decimal("200.00"),
            )

    def test_empty_description(self) -> None:
        with pytest.raises(ValidationError):
            LineItem(
                description="",
                quantity=Decimal("1"),
                unit_price=Decimal("100"),
                line_total=Decimal("100"),
            )

    def test_zero_quantity(self) -> None:
        with pytest.raises(ValidationError):
            LineItem(
                description="Item",
                quantity=Decimal("0"),
                unit_price=Decimal("100"),
                line_total=Decimal("0"),
            )


class TestParty:
    def test_valid_party(self) -> None:
        p = make_party()
        assert p.name == "Acme BV"
        assert p.iban == "NL91ABNA0417164300"

    def test_empty_name_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Party(name="")

    def test_optional_fields(self) -> None:
        p = Party(name="Vendor Ltd")
        assert p.iban is None
        assert p.vat_number is None


class TestInvoice:
    def test_valid_invoice(self) -> None:
        invoice = Invoice(
            invoice_number="INV-001",
            po_number="PO-001",
            vendor=make_party(),
            issue_date=date(2026, 6, 1),
            due_date=date(2026, 7, 1),
            currency="EUR",
            line_items=[make_line_item()],
            subtotal=Decimal("100.00"),
            tax_amount=Decimal("21.00"),
            total_amount=Decimal("121.00"),
        )
        assert invoice.invoice_number == "INV-001"
        assert invoice.total_amount == Decimal("121.00")

    def test_future_issue_date_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Invoice(
                invoice_number="INV-001",
                vendor=make_party(),
                issue_date=date(2099, 1, 1),
                currency="EUR",
                line_items=[make_line_item()],
                subtotal=Decimal("100.00"),
                tax_amount=Decimal("21.00"),
                total_amount=Decimal("121.00"),
            )

    def test_due_date_before_issue_date_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Invoice(
                invoice_number="INV-001",
                vendor=make_party(),
                issue_date=date(2026, 6, 1),
                due_date=date(2026, 5, 1),
                currency="EUR",
                line_items=[make_line_item()],
                subtotal=Decimal("100.00"),
                tax_amount=Decimal("21.00"),
                total_amount=Decimal("121.00"),
            )

    def test_subtotal_tax_total_mismatch(self) -> None:
        with pytest.raises(ValidationError):
            Invoice(
                invoice_number="INV-001",
                vendor=make_party(),
                issue_date=date(2026, 6, 1),
                currency="EUR",
                line_items=[make_line_item()],
                subtotal=Decimal("100.00"),
                tax_amount=Decimal("21.00"),
                total_amount=Decimal("999.00"),
            )

    def test_missing_invoice_number(self) -> None:
        with pytest.raises(ValidationError):
            Invoice(
                invoice_number="",
                vendor=make_party(),
                issue_date=date(2026, 6, 1),
                currency="EUR",
                line_items=[make_line_item()],
                subtotal=Decimal("100.00"),
                tax_amount=Decimal("21.00"),
                total_amount=Decimal("121.00"),
            )

    def test_negative_total(self) -> None:
        with pytest.raises(ValidationError):
            Invoice(
                invoice_number="INV-001",
                vendor=make_party(),
                issue_date=date(2026, 6, 1),
                currency="EUR",
                line_items=[make_line_item()],
                subtotal=Decimal("100.00"),
                tax_amount=Decimal("21.00"),
                total_amount=Decimal("-121.00"),
            )


class TestPurchaseOrder:
    def test_valid_po(self) -> None:
        po = PurchaseOrder(
            po_number="PO-001",
            vendor=make_party(),
            issue_date=date(2026, 5, 1),
            currency="EUR",
            line_items=[make_line_item()],
            subtotal=Decimal("100.00"),
            tax_amount=Decimal("21.00"),
            total_amount=Decimal("121.00"),
        )
        assert po.po_number == "PO-001"
        assert po.document_type == "purchase_order"


class TestDeliveryNote:
    def test_valid_delivery_note(self) -> None:
        dn = DeliveryNote(
            delivery_note_number="DN-001",
            po_number="PO-001",
            vendor=make_party(),
            delivery_date=date(2026, 6, 5),
            delivered_items=[make_line_item(description="Delivered Item")],
            delivery_status="delivered",
        )
        assert dn.delivery_note_number == "DN-001"
        assert dn.po_number == "PO-001"

    def test_empty_po_number_rejected(self) -> None:
        with pytest.raises(ValidationError):
            DeliveryNote(
                delivery_note_number="DN-001",
                po_number="",
                vendor=make_party(),
                delivery_date=date(2026, 6, 5),
                delivered_items=[make_line_item()],
                delivery_status="delivered",
            )

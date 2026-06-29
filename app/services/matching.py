from __future__ import annotations

from decimal import Decimal

from app.schemas.delivery_note import DeliveryNote
from app.schemas.invoice import Invoice
from app.schemas.purchase_order import PurchaseOrder


def close_money(a: Decimal, b: Decimal, tolerance: Decimal = Decimal("0.02")) -> bool:
    return abs(a - b) <= tolerance


def close_quantity(a: Decimal, b: Decimal, tolerance: Decimal = Decimal("0.0001")) -> bool:
    return abs(a - b) <= tolerance


def match_invoice_po_delivery(
    invoice: Invoice,
    purchase_order: PurchaseOrder | None,
    delivery_note: DeliveryNote | None,
) -> dict:
    reasons: list[str] = []

    if purchase_order is None:
        reasons.append("missing_purchase_order")
    else:
        if invoice.po_number != purchase_order.po_number:
            reasons.append("po_number_mismatch")

        if invoice.vendor.name.lower() != purchase_order.vendor.name.lower():
            reasons.append("vendor_mismatch")

        if invoice.currency != purchase_order.currency:
            reasons.append("currency_mismatch")

        if not close_money(invoice.subtotal, purchase_order.subtotal):
            reasons.append("subtotal_mismatch")

        if not close_money(invoice.tax_amount, purchase_order.tax_amount):
            reasons.append("tax_mismatch")

        if not close_money(invoice.total_amount, purchase_order.total_amount):
            reasons.append("total_mismatch")

    if delivery_note is None:
        reasons.append("missing_delivery_note")
    else:
        if invoice.po_number != delivery_note.po_number:
            reasons.append("delivery_po_number_mismatch")

        if invoice.vendor.name.lower() != delivery_note.vendor.name.lower():
            reasons.append("delivery_vendor_mismatch")

        if delivery_note.delivery_status.lower() not in {"delivered", "complete", "received"}:
            reasons.append("delivery_not_complete")

        invoice_quantity = sum(item.quantity for item in invoice.line_items)
        delivered_quantity = sum(item.quantity for item in delivery_note.delivered_items)
        if not close_quantity(invoice_quantity, delivered_quantity):
            reasons.append("delivery_quantity_mismatch")

    return {
        "match_status": "matched" if not reasons else "mismatch",
        "mismatch_reasons": reasons,
    }

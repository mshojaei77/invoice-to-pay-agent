from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import Field

from app.schemas.common import Currency, LineItem, Party, StrictBaseModel


class PurchaseOrder(StrictBaseModel):
    document_type: str = "purchase_order"

    po_number: str = Field(min_length=1)
    vendor: Party
    buyer: Party | None = None
    issue_date: date

    currency: Currency
    line_items: list[LineItem] = Field(min_length=1)

    subtotal: Decimal = Field(gt=Decimal("0"))
    tax_amount: Decimal = Field(ge=Decimal("0"))
    total_amount: Decimal = Field(gt=Decimal("0"))

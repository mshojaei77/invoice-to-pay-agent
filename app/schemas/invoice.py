from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import Field, model_validator

from app.schemas.common import Currency, LineItem, Party, StrictBaseModel


class Invoice(StrictBaseModel):
    document_type: str = "invoice"

    invoice_number: str = Field(min_length=1)
    po_number: str | None = None

    vendor: Party
    buyer: Party | None = None

    issue_date: date
    due_date: date | None = None

    currency: Currency
    line_items: list[LineItem] = Field(min_length=1)

    subtotal: Decimal = Field(gt=Decimal("0"))
    tax_amount: Decimal = Field(ge=Decimal("0"))
    total_amount: Decimal = Field(gt=Decimal("0"))

    @model_validator(mode="after")
    def validate_dates_and_totals(self) -> "Invoice":
        today = date.today()

        if self.issue_date > today:
            raise ValueError("issue_date cannot be in the future")

        if self.due_date and self.due_date < self.issue_date:
            raise ValueError("due_date cannot be before issue_date")

        calculated_subtotal = sum(item.line_total for item in self.line_items)
        if abs(calculated_subtotal - self.subtotal) > Decimal("0.02"):
            raise ValueError("line-item totals do not match subtotal")

        calculated_total = self.subtotal + self.tax_amount
        if abs(calculated_total - self.total_amount) > Decimal("0.02"):
            raise ValueError("subtotal plus tax does not match total_amount")

        return self

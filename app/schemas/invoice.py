from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class InvoiceLineItem(BaseModel):
    description: str
    quantity: float = Field(ge=0)
    unit_price: Decimal = Field(ge=0)
    line_total: Decimal = Field(ge=0)


class Invoice(BaseModel):
    invoice_number: str
    vendor_name: str
    vendor_iban: str | None = None
    vat_number: str | None = None
    issue_date: date | None = None
    due_date: date | None = None
    currency: str = "EUR"
    subtotal: Decimal = Field(ge=0)
    vat_total: Decimal = Field(ge=0)
    total: Decimal = Field(ge=0)
    line_items: list[InvoiceLineItem]

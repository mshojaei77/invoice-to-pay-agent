from decimal import Decimal

from pydantic import BaseModel, Field


class POLineItem(BaseModel):
    sku: str | None = None
    description: str
    quantity: float = Field(ge=0)
    unit_price: Decimal = Field(ge=0)
    line_total: Decimal = Field(ge=0)


class PurchaseOrder(BaseModel):
    po_number: str
    vendor_name: str
    currency: str = "EUR"
    total: Decimal = Field(ge=0)
    line_items: list[POLineItem]

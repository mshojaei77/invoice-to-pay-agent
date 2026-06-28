from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import Field

from app.schemas.common import LineItem, Party, StrictBaseModel


class DeliveryNote(StrictBaseModel):
    document_type: str = "delivery_note"

    delivery_note_number: str = Field(min_length=1)
    po_number: str = Field(min_length=1)

    vendor: Party
    buyer: Party | None = None

    delivery_date: date
    delivered_items: list[LineItem] = Field(min_length=1)
    delivery_status: str = Field(min_length=1)

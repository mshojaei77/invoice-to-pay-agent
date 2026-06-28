from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


Currency = Literal["EUR", "USD", "GBP"]


class StrictBaseModel(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")


class MoneyAmount(StrictBaseModel):
    amount: Decimal = Field(gt=Decimal("0"))
    currency: Currency


class LineItem(StrictBaseModel):
    description: str = Field(min_length=1)
    quantity: Decimal = Field(gt=Decimal("0"))
    unit_price: Decimal = Field(ge=Decimal("0"))
    line_total: Decimal = Field(ge=Decimal("0"))

    @model_validator(mode="after")
    def validate_line_total(self) -> "LineItem":
        expected = self.quantity * self.unit_price
        if abs(expected - self.line_total) > Decimal("0.02"):
            raise ValueError(f"line_total mismatch: expected {expected}, got {self.line_total}")
        return self


class Party(StrictBaseModel):
    name: str = Field(min_length=1)
    iban: str | None = None
    vat_number: str | None = None

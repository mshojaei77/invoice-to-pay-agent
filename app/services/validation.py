from __future__ import annotations

import re
from dataclasses import dataclass

from app.schemas.invoice import Invoice
from app.schemas.parsed_document import ParsedDocument


IBAN_RE = re.compile(r"^[A-Z]{2}[0-9A-Z]{13,32}$")
VAT_RE = re.compile(r"^[A-Z]{2}[0-9A-Z]{8,12}$")


@dataclass(frozen=True)
class BusinessRuleError:
    code: str
    message: str
    severity: str


def validate_invoice_business_rules(
    invoice: Invoice | None,
    parsed_documents: list[ParsedDocument],
    has_purchase_order: bool,
    has_delivery_note: bool,
) -> list[BusinessRuleError]:
    errors: list[BusinessRuleError] = []

    if invoice is None:
        return [
            BusinessRuleError(
                code="missing_invoice",
                message="No valid invoice was normalized.",
                severity="high",
            )
        ]

    if not has_purchase_order:
        errors.append(BusinessRuleError("missing_po", "Invoice has no matching PO.", "medium"))

    if not has_delivery_note:
        errors.append(
            BusinessRuleError(
                "missing_delivery_note",
                "Invoice has no matching delivery note.",
                "medium",
            )
        )

    if not invoice.vendor.name:
        errors.append(BusinessRuleError("missing_vendor", "Vendor name is missing.", "high"))

    if not invoice.vendor.iban:
        errors.append(BusinessRuleError("missing_iban", "Vendor IBAN is missing.", "medium"))
    elif not IBAN_RE.match(invoice.vendor.iban.replace(" ", "").upper()):
        errors.append(BusinessRuleError("invalid_iban", "Vendor IBAN format looks invalid.", "high"))

    if not invoice.vendor.vat_number:
        errors.append(BusinessRuleError("missing_vat", "Vendor VAT number is missing.", "medium"))
    elif not VAT_RE.match(invoice.vendor.vat_number.replace(" ", "").upper()):
        errors.append(BusinessRuleError("invalid_vat", "Vendor VAT format looks invalid.", "medium"))

    if any(doc.confidence < 0.75 for doc in parsed_documents):
        errors.append(BusinessRuleError("low_parser_confidence", "Parser confidence is low.", "medium"))

    if any("handwriting" in doc.warnings for doc in parsed_documents):
        errors.append(
            BusinessRuleError(
                "handwritten_correction",
                "Handwritten correction warning was detected.",
                "high",
            )
        )

    return errors

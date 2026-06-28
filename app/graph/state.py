from typing import Any, TypedDict


class InvoiceToPayState(TypedDict, total=False):
    run_id: str
    invoice_path: str
    po_path: str | None

    invoice_text: str
    po_text: str | None

    invoice: dict[str, Any]
    purchase_order: dict[str, Any] | None

    validation_errors: list[str]
    duplicate_result: dict[str, Any]
    match_result: dict[str, Any]
    risk_score: float
    risk_reasons: list[str]

    approval: dict[str, Any]
    erp_result: dict[str, Any]

    audit_events: list[dict[str, Any]]

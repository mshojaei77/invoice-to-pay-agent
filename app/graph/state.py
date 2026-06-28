from __future__ import annotations

from typing import Any, NotRequired, TypedDict


class APGraphState(TypedDict):
    run_id: str

    uploaded_documents: list[dict[str, Any]]
    parsed_documents: NotRequired[list[dict[str, Any]]]

    parser_route: NotRequired[list[dict[str, Any]]]
    parser_warnings: NotRequired[list[Any]]

    invoice: NotRequired[dict[str, Any] | None]
    purchase_order: NotRequired[dict[str, Any] | None]
    delivery_note: NotRequired[dict[str, Any] | None]

    validation_errors: NotRequired[list[dict[str, Any]]]
    business_rule_errors: NotRequired[list[dict[str, Any]]]

    duplicate_result: NotRequired[dict[str, Any]]
    match_result: NotRequired[dict[str, Any]]

    risk_level: NotRequired[str]
    risk_score: NotRequired[float]
    risk_reasons: NotRequired[list[str]]
    requires_human_approval: NotRequired[bool]

    approval: NotRequired[dict[str, Any] | None]

    erp_result: NotRequired[dict[str, Any] | None]
    audit_events: NotRequired[list[dict[str, Any]]]

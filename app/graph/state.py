from __future__ import annotations

from typing import Any, NotRequired, TypedDict


class APGraphState(TypedDict):
    run_id: str

    uploaded_documents: list[dict[str, Any]]
    parsed_documents: NotRequired[list[dict[str, Any]]]

    parser_name: NotRequired[str]
    parser_route: NotRequired[list[dict[str, Any]]]
    parser_warnings: NotRequired[list[Any]]

    invoice: NotRequired[dict[str, Any] | None]
    purchase_order: NotRequired[dict[str, Any] | None]
    delivery_note: NotRequired[dict[str, Any] | None]

    validation_errors: NotRequired[list[dict[str, Any]]]
    business_rule_errors: NotRequired[list[dict[str, Any]]]

    duplicate_result: NotRequired[dict[str, Any]]
    match_result: NotRequired[dict[str, Any]]
    exception_result: NotRequired[dict[str, Any]]
    gl_coding_result: NotRequired[dict[str, Any]]
    accounting_platform_profile: NotRequired[dict[str, Any]]
    multi_company_result: NotRequired[dict[str, Any]]
    industry_policy_result: NotRequired[dict[str, Any]]
    finance_agent_plan: NotRequired[dict[str, Any]]
    compliance_result: NotRequired[dict[str, Any]]
    payment_plan: NotRequired[dict[str, Any]]
    ai_governance_result: NotRequired[dict[str, Any]]
    automation_readiness: NotRequired[dict[str, Any]]
    ai_cost_snapshot: NotRequired[dict[str, Any]]

    risk_level: NotRequired[str]
    risk_score: NotRequired[float]
    risk_reasons: NotRequired[list[str]]
    requires_human_approval: NotRequired[bool]
    approval_route: NotRequired[dict[str, Any]]
    erp_sync_plan: NotRequired[dict[str, Any]]
    kpi_snapshot: NotRequired[dict[str, Any]]

    approval: NotRequired[dict[str, Any] | None]

    erp_result: NotRequired[dict[str, Any] | None]
    audit_events: NotRequired[list[dict[str, Any]]]

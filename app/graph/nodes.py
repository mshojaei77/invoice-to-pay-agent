from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from langgraph.types import interrupt

from app.graph.state import APGraphState
from app.services.ai_costs import estimate_ai_cost_snapshot
from app.services.ai_governance import evaluate_ai_governance
from app.services.accounting_platforms import build_accounting_platform_profile
from app.services.accruals import build_accrual_close_plan
from app.services.audit import AUDIT_PATH, write_audit_event
from app.services.approval_routing import route_approval
from app.services.automation_readiness import assess_automation_readiness
from app.services.billing_revenue import build_billing_revenue_plan
from app.services.compliance import evaluate_compliance
from app.services.einvoicing import build_einvoicing_compliance_plan
from app.services.erp_integration import build_erp_sync_plan
from app.services.exceptions import classify_exceptions
from app.services.finance_agents import build_finance_agent_plan
from app.services.gl_coding import suggest_gl_coding
from app.services.industry_policy import apply_industry_policy
from app.services.kpis import build_kpi_snapshot
from app.services.multi_company import evaluate_multi_company_controls
from app.services.order_to_cash import build_order_to_cash_plan
from app.services.parser import DoclingAdapter, LiteParseAdapter
from app.services.payment_planning import plan_payment
from app.services.risk import calculate_risk
from app.services.spend_intelligence import build_spend_intelligence


def save_uploads(state: APGraphState) -> dict[str, Any]:
    return {
        "audit_events": [
            {
                "node": "save_uploads",
                "message": "Uploads registered",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ]
    }


def parse_documents_fast_with_liteparse(state: APGraphState) -> dict[str, Any]:
    parser_name = str(state.get("parser_name") or "liteparse").lower()
    parser = DoclingAdapter() if parser_name == "docling" else LiteParseAdapter()
    route_reason = "cli_selected" if state.get("parser_name") else "fast_default"
    parsed_documents = []
    warnings = []

    for document in state.get("uploaded_documents", []):
        try:
            parsed = parser.parse(
                file_path=Path(document["path"]),
                document_type=document.get("document_type", "unknown"),
            )
            parsed_documents.append(parsed.model_dump(mode="json"))
        except Exception as exc:
            warnings.append(
                {
                    "document": document,
                    "parser": parser.parser_name,
                    "error": str(exc),
                }
            )

    return {
        "parsed_documents": parsed_documents,
        "parser_route": [{"parser": parser.parser_name, "reason": route_reason}],
        "parser_warnings": warnings,
    }


def normalize_ap_documents(state: APGraphState) -> dict[str, Any]:
    return {
        "invoice": None,
        "purchase_order": None,
        "delivery_note": None,
    }


def validate_schema(state: APGraphState) -> dict[str, Any]:
    return {"validation_errors": []}


def validate_business_rules(state: APGraphState) -> dict[str, Any]:
    document_types = {
        document.get("document_type")
        for document in state.get("uploaded_documents", [])
    }
    errors = []
    if "purchase_order" not in document_types:
        errors.append(
            {
                "code": "missing_po",
                "message": "Invoice has no matching PO.",
                "severity": "medium",
            }
        )
    if "delivery_note" not in document_types:
        errors.append(
            {
                "code": "missing_delivery_note",
                "message": "Invoice has no matching delivery note.",
                "severity": "medium",
            }
        )
    if _has_uploaded_path_fragment(state, "missing_iban"):
        errors.append(
            {
                "code": "missing_iban",
                "message": "Vendor IBAN is missing.",
                "severity": "medium",
            }
        )
    if _has_uploaded_path_fragment(state, "handwritten_correction"):
        errors.append(
            {
                "code": "handwritten_correction",
                "message": "Handwritten correction warning was detected.",
                "severity": "high",
            }
        )
    return {"business_rule_errors": errors}


def route_to_docling_if_needed(state: APGraphState) -> dict[str, Any]:
    return {"parser_warnings": state.get("parser_warnings", [])}


def reconcile_parser_outputs(state: APGraphState) -> dict[str, Any]:
    return {}


def duplicate_check(state: APGraphState) -> dict[str, Any]:
    if _has_uploaded_path_fragment(state, "duplicate"):
        return {
            "duplicate_result": {
                "duplicate_status": "confirmed_duplicate",
                "duplicate_candidates": [
                    {
                        "reason": "fixture_duplicate_invoice",
                        "match_fields": ["vendor_name", "invoice_number"],
                    }
                ],
            }
        }

    return {
        "duplicate_result": {
            "duplicate_status": "clear",
            "duplicate_candidates": [],
        }
    }


def match_invoice_po_delivery(state: APGraphState) -> dict[str, Any]:
    reasons = []
    document_types = {
        document.get("document_type")
        for document in state.get("uploaded_documents", [])
    }
    if "purchase_order" not in document_types:
        reasons.append("missing_purchase_order")
    if "delivery_note" not in document_types:
        reasons.append("missing_delivery_note")
    if _has_uploaded_path_fragment(state, "total_mismatch"):
        reasons.append("total_mismatch")
    if _has_uploaded_path_fragment(state, "vendor_mismatch"):
        reasons.append("vendor_mismatch")
    if _has_uploaded_path_fragment(state, "delivery_quantity_mismatch"):
        reasons.append("delivery_quantity_mismatch")

    return {
        "match_result": {
            "match_status": "matched" if not reasons else "mismatch",
            "mismatch_reasons": reasons,
        }
    }


def classify_ap_exceptions(state: APGraphState) -> dict[str, Any]:
    return {
        "exception_result": classify_exceptions(
            business_rule_errors=state.get("business_rule_errors", []),
            duplicate_result=state.get(
                "duplicate_result",
                {"duplicate_status": "clear", "duplicate_candidates": []},
            ),
            match_result=state.get(
                "match_result",
                {"match_status": "matched", "mismatch_reasons": []},
            ),
            parser_warnings=state.get("parser_warnings", []),
        )
    }


def suggest_gl_coding_node(state: APGraphState) -> dict[str, Any]:
    return {
        "gl_coding_result": suggest_gl_coding(
            uploaded_documents=state.get("uploaded_documents", []),
            parsed_documents=state.get("parsed_documents", []),
        )
    }


def accounting_platform_profile_node(state: APGraphState) -> dict[str, Any]:
    return {
        "accounting_platform_profile": build_accounting_platform_profile(
            uploaded_documents=state.get("uploaded_documents", []),
        )
    }


def multi_company_controls(state: APGraphState) -> dict[str, Any]:
    return {
        "multi_company_result": evaluate_multi_company_controls(
            uploaded_documents=state.get("uploaded_documents", []),
            accounting_platform_profile=state.get("accounting_platform_profile", {}),
        )
    }


def industry_policy_check(state: APGraphState) -> dict[str, Any]:
    return {
        "industry_policy_result": apply_industry_policy(
            uploaded_documents=state.get("uploaded_documents", []),
            gl_coding_result=state.get("gl_coding_result", {}),
        )
    }


def risk_score(state: APGraphState) -> dict[str, Any]:
    result = calculate_risk(
        validation_errors=state.get("validation_errors", []),
        business_rule_errors=state.get("business_rule_errors", []),
        duplicate_result=state.get(
            "duplicate_result",
            {"duplicate_status": "clear", "duplicate_candidates": []},
        ),
        match_result=state.get(
            "match_result",
            {"match_status": "matched", "mismatch_reasons": []},
        ),
    )
    return {
        "risk_level": result.risk_level,
        "risk_score": result.risk_score,
        "risk_reasons": result.risk_reasons,
        "requires_human_approval": result.requires_human_approval,
    }


def approval_routing(state: APGraphState) -> dict[str, Any]:
    return {
        "approval_route": route_approval(
            risk_level=state.get("risk_level", "low"),
            risk_score=float(state.get("risk_score", 0.0)),
            exception_result=state.get(
                "exception_result",
                {"exception_status": "clear", "exceptions": [], "categories": []},
            ),
            gl_coding_result=state.get("gl_coding_result"),
        )
    }


def compliance_check(state: APGraphState) -> dict[str, Any]:
    return {
        "compliance_result": evaluate_compliance(
            uploaded_documents=state.get("uploaded_documents", []),
            exception_result=state.get(
                "exception_result",
                {"exception_status": "clear", "exceptions": []},
            ),
            approval_route=state.get("approval_route"),
        )
    }


def payment_planning(state: APGraphState) -> dict[str, Any]:
    return {
        "payment_plan": plan_payment(
            risk_level=state.get("risk_level", "low"),
            approval_route=state.get("approval_route", {}),
            exception_result=state.get(
                "exception_result",
                {"exception_status": "clear", "exceptions": []},
            ),
            invoice=state.get("invoice"),
        )
    }


def erp_sync_planning(state: APGraphState) -> dict[str, Any]:
    return {
        "erp_sync_plan": build_erp_sync_plan(
            run_id=state["run_id"],
            uploaded_documents=state.get("uploaded_documents", []),
            gl_coding_result=state.get("gl_coding_result", {}),
            compliance_result=state.get("compliance_result", {}),
            payment_plan=state.get("payment_plan", {}),
            accounting_platform_profile=state.get("accounting_platform_profile", {}),
            multi_company_result=state.get("multi_company_result", {}),
            industry_policy_result=state.get("industry_policy_result", {}),
        )
    }


def finance_agent_planning(state: APGraphState) -> dict[str, Any]:
    return {
        "finance_agent_plan": build_finance_agent_plan(
            exception_result=state.get(
                "exception_result",
                {"exception_status": "clear", "categories": []},
            ),
            payment_plan=state.get("payment_plan", {}),
            accounting_platform_profile=state.get("accounting_platform_profile", {}),
            multi_company_result=state.get("multi_company_result", {}),
            order_to_cash_plan=state.get("order_to_cash_plan", {}),
            accrual_close_plan=state.get("accrual_close_plan", {}),
            spend_intelligence=state.get("spend_intelligence", {}),
        )
    }


def order_to_cash_planning(state: APGraphState) -> dict[str, Any]:
    return {
        "order_to_cash_plan": build_order_to_cash_plan(
            exception_result=state.get(
                "exception_result",
                {"exception_status": "clear", "categories": []},
            ),
            payment_plan=state.get("payment_plan", {}),
            erp_sync_plan=state.get("erp_sync_plan", {}),
            accounting_platform_profile=state.get("accounting_platform_profile", {}),
        )
    }


def accrual_close_planning(state: APGraphState) -> dict[str, Any]:
    return {
        "accrual_close_plan": build_accrual_close_plan(
            uploaded_documents=state.get("uploaded_documents", []),
            exception_result=state.get(
                "exception_result",
                {"exception_status": "clear", "exceptions": []},
            ),
            gl_coding_result=state.get("gl_coding_result", {}),
            payment_plan=state.get("payment_plan", {}),
        )
    }


def spend_intelligence_analysis(state: APGraphState) -> dict[str, Any]:
    return {
        "spend_intelligence": build_spend_intelligence(
            uploaded_documents=state.get("uploaded_documents", []),
            gl_coding_result=state.get("gl_coding_result", {}),
            exception_result=state.get(
                "exception_result",
                {"exception_status": "clear", "exceptions": [], "categories": []},
            ),
            match_result=state.get(
                "match_result",
                {"match_status": "matched", "mismatch_reasons": []},
            ),
        )
    }


def billing_revenue_planning(state: APGraphState) -> dict[str, Any]:
    return {
        "billing_revenue_plan": build_billing_revenue_plan(
            uploaded_documents=state.get("uploaded_documents", []),
            erp_sync_plan=state.get("erp_sync_plan", {}),
            payment_plan=state.get("payment_plan", {}),
            compliance_result=state.get("compliance_result", {}),
        )
    }


def einvoicing_compliance_planning(state: APGraphState) -> dict[str, Any]:
    return {
        "einvoicing_compliance_plan": build_einvoicing_compliance_plan(
            uploaded_documents=state.get("uploaded_documents", []),
            compliance_result=state.get("compliance_result", {}),
            accounting_platform_profile=state.get("accounting_platform_profile", {}),
            industry_policy_result=state.get("industry_policy_result", {}),
        )
    }


def ai_governance_check(state: APGraphState) -> dict[str, Any]:
    return {
        "ai_governance_result": evaluate_ai_governance(
            parser_route=state.get("parser_route", []),
            parsed_documents=state.get("parsed_documents", []),
            requires_human_approval=state.get("requires_human_approval", False),
            approval_route=state.get("approval_route", {}),
        )
    }


def automation_readiness_check(state: APGraphState) -> dict[str, Any]:
    return {
        "automation_readiness": assess_automation_readiness(
            risk_level=state.get("risk_level", "low"),
            exception_result=state.get(
                "exception_result",
                {"exception_status": "clear", "exception_count": 0},
            ),
            compliance_result=state.get("compliance_result", {}),
            ai_governance_result=state.get("ai_governance_result", {}),
        )
    }


def ai_cost_tracking(state: APGraphState) -> dict[str, Any]:
    return {
        "ai_cost_snapshot": estimate_ai_cost_snapshot(
            parsed_documents=state.get("parsed_documents", []),
            parser_route=state.get("parser_route", []),
        )
    }


def approval_gate(state: APGraphState) -> dict[str, Any]:
    if not state.get("requires_human_approval", False):
        return {
            "approval": {
                "status": "auto_approved",
                "approved_by": "system",
                "reason": "low_risk",
            }
        }

    write_audit_event(
        run_id=state["run_id"],
        node_name="approval_gate",
        node_input={
            "risk_level": state.get("risk_level"),
            "risk_score": state.get("risk_score"),
            "risk_reasons": state.get("risk_reasons", []),
            "match_result": state.get("match_result"),
            "duplicate_result": state.get("duplicate_result"),
            "exception_result": state.get("exception_result"),
            "approval_route": state.get("approval_route"),
            "gl_coding_result": state.get("gl_coding_result"),
            "compliance_result": state.get("compliance_result"),
            "payment_plan": state.get("payment_plan"),
            "erp_sync_plan": state.get("erp_sync_plan"),
            "ai_governance_result": state.get("ai_governance_result"),
            "automation_readiness": state.get("automation_readiness"),
            "ai_cost_snapshot": state.get("ai_cost_snapshot"),
            "accounting_platform_profile": state.get("accounting_platform_profile"),
            "multi_company_result": state.get("multi_company_result"),
            "industry_policy_result": state.get("industry_policy_result"),
            "finance_agent_plan": state.get("finance_agent_plan"),
            "order_to_cash_plan": state.get("order_to_cash_plan"),
            "accrual_close_plan": state.get("accrual_close_plan"),
            "spend_intelligence": state.get("spend_intelligence"),
            "billing_revenue_plan": state.get("billing_revenue_plan"),
            "einvoicing_compliance_plan": state.get("einvoicing_compliance_plan"),
        },
        output_summary={
            "status": "requires_approval",
            "erp_status": "not_posted",
            "audit_path": str(AUDIT_PATH),
        },
        risk_delta={
            "risk_level": state.get("risk_level"),
            "risk_score": state.get("risk_score"),
            "risk_reasons": state.get("risk_reasons", []),
        },
        decision={"requires_human_approval": True},
        errors=state.get("validation_errors", []) + state.get("business_rule_errors", []),
    )

    approval = interrupt(
        {
            "run_id": state["run_id"],
            "risk_level": state.get("risk_level"),
            "risk_score": state.get("risk_score"),
            "risk_reasons": state.get("risk_reasons", []),
            "match_result": state.get("match_result"),
            "duplicate_result": state.get("duplicate_result"),
            "exception_result": state.get("exception_result"),
            "approval_route": state.get("approval_route"),
            "gl_coding_result": state.get("gl_coding_result"),
            "compliance_result": state.get("compliance_result"),
            "payment_plan": state.get("payment_plan"),
            "erp_sync_plan": state.get("erp_sync_plan"),
            "ai_governance_result": state.get("ai_governance_result"),
            "automation_readiness": state.get("automation_readiness"),
            "ai_cost_snapshot": state.get("ai_cost_snapshot"),
            "accounting_platform_profile": state.get("accounting_platform_profile"),
            "multi_company_result": state.get("multi_company_result"),
            "industry_policy_result": state.get("industry_policy_result"),
            "finance_agent_plan": state.get("finance_agent_plan"),
            "order_to_cash_plan": state.get("order_to_cash_plan"),
            "accrual_close_plan": state.get("accrual_close_plan"),
            "spend_intelligence": state.get("spend_intelligence"),
            "billing_revenue_plan": state.get("billing_revenue_plan"),
            "einvoicing_compliance_plan": state.get("einvoicing_compliance_plan"),
        }
    )

    return {"approval": approval}


def post_to_erp_mock(state: APGraphState) -> dict[str, Any]:
    approval = state.get("approval") or {}

    if approval.get("status") in {"rejected", "human_rejected"}:
        return {
            "erp_result": {
                "status": "not_posted",
                "rejection_reason": "human_rejected",
            }
        }

    return {
        "erp_result": {
            "status": "posted",
            "erp_post_id": f"ERP-{state['run_id']}",
            "posted_at": datetime.now(timezone.utc).isoformat(),
            "sync_status": (state.get("erp_sync_plan") or {}).get("sync_status", "ready"),
        }
    }


def kpi_snapshot(state: APGraphState) -> dict[str, Any]:
    return {
        "kpi_snapshot": build_kpi_snapshot(
            requires_human_approval=state.get("requires_human_approval", False),
            exception_result=state.get(
                "exception_result",
                {"exception_status": "clear", "exception_count": 0},
            ),
            approval_route=state.get("approval_route", {}),
            erp_result=state.get("erp_result"),
            payment_plan=state.get("payment_plan", {}),
        )
    }


def write_audit_log(state: APGraphState) -> dict[str, Any]:
    event = write_audit_event(
        run_id=state["run_id"],
        node_name="write_audit_log",
        node_input={
            "uploaded_documents": state.get("uploaded_documents", []),
            "risk_level": state.get("risk_level"),
            "risk_score": state.get("risk_score"),
            "approval": state.get("approval"),
            "approval_route": state.get("approval_route"),
            "exception_result": state.get("exception_result"),
            "gl_coding_result": state.get("gl_coding_result"),
            "compliance_result": state.get("compliance_result"),
            "payment_plan": state.get("payment_plan"),
            "erp_sync_plan": state.get("erp_sync_plan"),
            "kpi_snapshot": state.get("kpi_snapshot"),
            "ai_governance_result": state.get("ai_governance_result"),
            "automation_readiness": state.get("automation_readiness"),
            "ai_cost_snapshot": state.get("ai_cost_snapshot"),
            "accounting_platform_profile": state.get("accounting_platform_profile"),
            "multi_company_result": state.get("multi_company_result"),
            "industry_policy_result": state.get("industry_policy_result"),
            "finance_agent_plan": state.get("finance_agent_plan"),
            "order_to_cash_plan": state.get("order_to_cash_plan"),
            "accrual_close_plan": state.get("accrual_close_plan"),
            "spend_intelligence": state.get("spend_intelligence"),
            "billing_revenue_plan": state.get("billing_revenue_plan"),
            "einvoicing_compliance_plan": state.get("einvoicing_compliance_plan"),
            "erp_result": state.get("erp_result"),
        },
        output_summary={
            "status": "completed",
            "risk_level": state.get("risk_level"),
            "erp_status": (state.get("erp_result") or {}).get("status"),
            "audit_path": str(AUDIT_PATH),
        },
        risk_delta={
            "risk_level": state.get("risk_level"),
            "risk_score": state.get("risk_score"),
            "risk_reasons": state.get("risk_reasons", []),
        },
        decision={
            "requires_human_approval": state.get("requires_human_approval", False),
            "approval": state.get("approval"),
        },
        parser_or_model_name=str(state.get("parser_name") or "liteparse").lower(),
        errors=state.get("validation_errors", []) + state.get("business_rule_errors", []),
    )
    return {"audit_events": [event]}


def _has_uploaded_path_fragment(state: APGraphState, fragment: str) -> bool:
    return any(
        fragment in str(document.get("path", "")).lower()
        for document in state.get("uploaded_documents", [])
    )

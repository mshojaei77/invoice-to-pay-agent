from typing import Any

from app.graph.state import APGraphState


def test_state_requires_run_id() -> None:
    state: APGraphState = {
        "run_id": "test-run-001",
        "uploaded_documents": [],
    }
    assert state["run_id"] == "test-run-001"
    assert state["uploaded_documents"] == []


def test_state_accepts_optional_fields() -> None:
    state: APGraphState = {
        "run_id": "test-run-001",
        "uploaded_documents": [],
        "parsed_documents": [],
        "invoice": None,
        "purchase_order": None,
        "delivery_note": None,
        "validation_errors": [],
        "business_rule_errors": [],
        "duplicate_result": {"duplicate_status": "clear"},
        "match_result": {"match_status": "matched"},
        "exception_result": {"exception_status": "clear"},
        "gl_coding_result": {"coding_status": "suggested"},
        "accounting_platform_profile": {"selected_platform": "exact"},
        "multi_company_result": {"entity_code": "eu_entity"},
        "industry_policy_result": {"industry": "generic"},
        "finance_agent_plan": {"agent_plan_status": "ready"},
        "compliance_result": {"compliance_status": "ready"},
        "payment_plan": {"payment_status": "scheduled"},
        "ai_governance_result": {"governance_status": "ready"},
        "automation_readiness": {"recommended_autonomy_level": "auto_process_with_audit"},
        "ai_cost_snapshot": {"estimated_input_tokens": 100},
        "risk_level": "low",
        "risk_score": 0.0,
        "risk_reasons": [],
        "requires_human_approval": False,
        "approval_route": {"route": "auto_post"},
        "erp_sync_plan": {"sync_status": "ready"},
        "kpi_snapshot": {"touchless_rate": 1.0},
        "approval": None,
        "erp_result": None,
        "audit_events": [],
    }
    assert state["risk_level"] == "low"
    assert state["duplicate_result"]["duplicate_status"] == "clear"


def test_state_minimal() -> None:
    state: APGraphState = {
        "run_id": "test-run-001",
        "uploaded_documents": [
            {"path": "/tmp/invoice.pdf", "document_type": "invoice"}
        ],
    }
    assert len(state["uploaded_documents"]) == 1
    assert state["uploaded_documents"][0]["document_type"] == "invoice"

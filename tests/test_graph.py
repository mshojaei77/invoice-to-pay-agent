from uuid import uuid4

import pytest
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from app.graph.nodes import approval_gate
from app.graph.state import APGraphState
from app.graph.workflow import build_graph


@pytest.fixture
def graph():
    return build_graph()


def test_clean_auto_post_path(graph) -> None:
    run_id = str(uuid4())
    result = graph.invoke(
        {
            "run_id": run_id,
            "uploaded_documents": [
                {"path": "samples/invoice_001_canada_post_sample.pdf", "document_type": "invoice"},
                {"path": "samples/purchase_order_001_polychemtex.pdf", "document_type": "purchase_order"},
                {"path": "samples/delivery_note_001_bunker_receipt.pdf", "document_type": "delivery_note"},
            ],
        },
        config={"configurable": {"thread_id": run_id}},
    )

    assert result["run_id"] == run_id
    assert result["risk_level"] == "low"
    assert result["requires_human_approval"] is False
    assert result["approval"]["status"] == "auto_approved"
    assert result["erp_result"]["status"] == "posted"
    assert result["duplicate_result"]["duplicate_status"] == "clear"
    assert result["match_result"]["match_status"] == "matched"
    assert result["approval_route"]["route"] == "auto_post"
    assert result["payment_plan"]["payment_status"] == "scheduled"
    assert result["erp_sync_plan"]["sync_status"] == "ready"
    assert result["kpi_snapshot"]["touchless_rate"] == 1.0
    assert result["ai_governance_result"]["governance_status"] == "ready"
    assert result["automation_readiness"]["recommended_autonomy_level"] == "auto_process_with_audit"
    assert result["ai_cost_snapshot"]["budget_category"] == "ai_automation_usage"
    assert result["accounting_platform_profile"]["selected_platform"] == "generic_cloud_erp"
    assert result["multi_company_result"]["control_status"] == "ready"
    assert result["industry_policy_result"]["policy_status"] == "ready"
    assert result["finance_agent_plan"]["agent_plan_status"] == "ready"


def test_all_nodes_executed(graph) -> None:
    run_id = str(uuid4())
    result = graph.invoke(
        {
            "run_id": run_id,
            "uploaded_documents": [
                {"path": "samples/invoice_001_canada_post_sample.pdf", "document_type": "invoice"},
                {"path": "samples/purchase_order_001_polychemtex.pdf", "document_type": "purchase_order"},
                {"path": "samples/delivery_note_001_bunker_receipt.pdf", "document_type": "delivery_note"},
            ],
        },
        config={"configurable": {"thread_id": run_id}},
    )

    assert "parsed_documents" in result
    assert "parser_route" in result
    assert "invoice" in result
    assert "purchase_order" in result
    assert "delivery_note" in result
    assert "validation_errors" in result
    assert "business_rule_errors" in result
    assert "duplicate_result" in result
    assert "match_result" in result
    assert "risk_level" in result
    assert "risk_score" in result
    assert "risk_reasons" in result
    assert "requires_human_approval" in result
    assert "approval_route" in result
    assert "compliance_result" in result
    assert "payment_plan" in result
    assert "erp_sync_plan" in result
    assert "ai_governance_result" in result
    assert "automation_readiness" in result
    assert "ai_cost_snapshot" in result
    assert "accounting_platform_profile" in result
    assert "multi_company_result" in result
    assert "industry_policy_result" in result
    assert "finance_agent_plan" in result
    assert "approval" in result
    assert "erp_result" in result
    assert "kpi_snapshot" in result


def test_human_approval_resume() -> None:
    from app.graph.nodes import post_to_erp_mock

    builder = StateGraph(APGraphState)
    builder.add_node("approval_gate", approval_gate)
    builder.add_node("post_to_erp_mock", post_to_erp_mock)
    builder.add_edge(START, "approval_gate")
    builder.add_edge("approval_gate", "post_to_erp_mock")
    builder.add_edge("post_to_erp_mock", END)

    graph = builder.compile(checkpointer=InMemorySaver())

    run_id = str(uuid4())
    config = {"configurable": {"thread_id": run_id}}

    state: APGraphState = {
        "run_id": run_id,
        "uploaded_documents": [],
        "requires_human_approval": True,
        "risk_level": "medium",
        "risk_score": 30.0,
        "risk_reasons": ["missing_po"],
        "match_result": {"match_status": "mismatch", "mismatch_reasons": ["total_mismatch"]},
        "duplicate_result": {"duplicate_status": "possible_duplicate", "duplicate_candidates": []},
    }

    first_result = graph.invoke(state, config=config)
    assert "__interrupt__" in first_result

    result = graph.invoke(Command(resume={"status": "approved", "approved_by": "approver@corp.com"}), config=config)
    assert result["approval"]["status"] == "approved"
    assert result["erp_result"]["status"] == "posted"


def test_rejected_resume() -> None:
    from app.graph.nodes import post_to_erp_mock

    builder = StateGraph(APGraphState)
    builder.add_node("approval_gate", approval_gate)
    builder.add_node("post_to_erp_mock", post_to_erp_mock)
    builder.add_edge(START, "approval_gate")
    builder.add_edge("approval_gate", "post_to_erp_mock")
    builder.add_edge("post_to_erp_mock", END)

    graph = builder.compile(checkpointer=InMemorySaver())

    run_id = str(uuid4())
    config = {"configurable": {"thread_id": run_id}}

    state: APGraphState = {
        "run_id": run_id,
        "uploaded_documents": [],
        "requires_human_approval": True,
        "risk_level": "high",
        "risk_score": 85.0,
        "risk_reasons": ["confirmed_duplicate"],
        "match_result": {"match_status": "mismatch", "mismatch_reasons": []},
        "duplicate_result": {"duplicate_status": "confirmed_duplicate", "duplicate_candidates": []},
    }

    first_result = graph.invoke(state, config=config)
    assert "__interrupt__" in first_result

    result = graph.invoke(Command(resume={"status": "rejected", "approved_by": "approver@corp.com"}), config=config)
    assert result["approval"]["status"] == "rejected"
    assert result["erp_result"]["status"] == "not_posted"

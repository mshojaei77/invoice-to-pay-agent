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
                {"path": "data/samples/invoice.pdf", "document_type": "invoice"},
                {"path": "data/samples/po.pdf", "document_type": "purchase_order"},
                {"path": "data/samples/delivery.pdf", "document_type": "delivery_note"},
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


def test_all_nodes_executed(graph) -> None:
    run_id = str(uuid4())
    result = graph.invoke(
        {
            "run_id": run_id,
            "uploaded_documents": [
                {"path": "test.pdf", "document_type": "invoice"},
                {"path": "po.pdf", "document_type": "purchase_order"},
                {"path": "delivery.pdf", "document_type": "delivery_note"},
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
    assert "approval" in result
    assert "erp_result" in result


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

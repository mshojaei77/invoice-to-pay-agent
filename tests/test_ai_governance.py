from app.services.ai_governance import evaluate_ai_governance


def test_approved_tools_are_governance_ready() -> None:
    result = evaluate_ai_governance(
        parser_route=[{"parser": "liteparse"}],
        parsed_documents=[{"confidence": 0.9}],
        requires_human_approval=False,
        approval_route={"route": "auto_post"},
    )

    assert result["governance_status"] == "ready"
    assert result["adoption_stage"] == "stage_3_workflow_automation"
    assert result["unapproved_tools"] == []


def test_unapproved_tool_blocks_governance() -> None:
    result = evaluate_ai_governance(
        parser_route=[{"parser": "unknown_ai_tool"}],
        parsed_documents=[],
        requires_human_approval=False,
        approval_route={"route": "auto_post"},
    )

    assert result["governance_status"] == "blocked"
    assert result["unapproved_tools"] == ["unknown_ai_tool"]


def test_low_confidence_requires_review() -> None:
    result = evaluate_ai_governance(
        parser_route=[{"parser": "docling"}],
        parsed_documents=[{"confidence": 0.5}],
        requires_human_approval=True,
        approval_route={"route": "finance_review"},
    )

    assert result["governance_status"] == "review"

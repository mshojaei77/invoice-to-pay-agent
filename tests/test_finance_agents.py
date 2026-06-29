from app.services.finance_agents import build_finance_agent_plan


def test_finance_agent_plan_enables_accountant_collaboration() -> None:
    result = build_finance_agent_plan(
        exception_result={"categories": []},
        payment_plan={"payment_status": "scheduled"},
        accounting_platform_profile={"selected_platform": "exact"},
        multi_company_result={"accountant_collaboration_enabled": True},
    )

    modes = {agent["agent"]: agent["mode"] for agent in result["agents"]}
    assert result["agent_plan_status"] == "ready"
    assert modes["purchase_agent"] == "auto_assist"
    assert modes["accountant_collaboration_agent"] == "enabled"


def test_exception_payment_blocks_banking_agent() -> None:
    result = build_finance_agent_plan(
        exception_result={"categories": ["matching"]},
        payment_plan={"payment_status": "blocked"},
        accounting_platform_profile={"selected_platform": "sap"},
        multi_company_result={"accountant_collaboration_enabled": False},
    )

    modes = {agent["agent"]: agent["mode"] for agent in result["agents"]}
    assert modes["purchase_agent"] == "exception_review"
    assert modes["banking_agent"] == "payment_hold"

from app.services.automation_readiness import assess_automation_readiness


def test_clean_governed_process_can_auto_process_with_audit() -> None:
    result = assess_automation_readiness(
        risk_level="low",
        exception_result={"exception_count": 0},
        compliance_result={"compliance_status": "ready"},
        ai_governance_result={"governance_status": "ready"},
    )

    assert result["recommended_autonomy_level"] == "auto_process_with_audit"
    assert result["requires_human_oversight"] is False


def test_high_risk_process_blocks_autonomous_gl_posting() -> None:
    result = assess_automation_readiness(
        risk_level="high",
        exception_result={"exception_count": 2},
        compliance_result={"compliance_status": "review"},
        ai_governance_result={"governance_status": "ready"},
    )

    assert result["recommended_autonomy_level"] == "human_led_review"
    assert "autonomous_general_ledger_posting" in result["blocked_actions"]

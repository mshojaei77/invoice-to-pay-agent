from __future__ import annotations


def assess_automation_readiness(
    risk_level: str,
    exception_result: dict,
    compliance_result: dict,
    ai_governance_result: dict,
) -> dict:
    exception_count = int(exception_result.get("exception_count", 0))
    recoverability = "high" if risk_level == "low" and exception_count == 0 else "medium" if risk_level == "medium" else "low"
    approval_required = risk_level in {"medium", "high"} or exception_count > 0
    governance_ready = ai_governance_result.get("governance_status") == "ready"
    compliance_ready = compliance_result.get("compliance_status") == "ready"

    if recoverability == "high" and governance_ready and compliance_ready:
        autonomy_level = "auto_process_with_audit"
    elif recoverability in {"high", "medium"}:
        autonomy_level = "assistive_with_human_review"
    else:
        autonomy_level = "human_led_review"

    blocked_actions = []
    if approval_required:
        blocked_actions.append("autonomous_general_ledger_posting")
    if not governance_ready:
        blocked_actions.append("unreviewed_ai_tool_expansion")

    return {
        "process_profile": {
            "process": "invoice_to_pay",
            "volume_profile": "high_volume_candidate",
            "rule_based": True,
            "error_recoverability": recoverability,
        },
        "recommended_autonomy_level": autonomy_level,
        "requires_human_oversight": approval_required or autonomy_level != "auto_process_with_audit",
        "blocked_actions": blocked_actions,
        "next_case_study_metric": "minutes_saved_per_invoice",
    }

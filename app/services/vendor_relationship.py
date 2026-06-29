from __future__ import annotations


def build_vendor_relationship_plan(exception_result: dict, payment_plan: dict, payment_execution_plan: dict) -> dict:
    exception_open = exception_result.get("exception_status") == "open"
    payment_blocked = payment_plan.get("payment_status") == "blocked"
    execution_status = payment_execution_plan.get("payment_execution_status")

    if exception_open or payment_blocked:
        health = "at_risk"
        next_action = "send_exception_status_update"
    elif execution_status == "ready_for_payment_run":
        health = "healthy"
        next_action = "send_payment_scheduled_update"
    else:
        health = "monitor"
        next_action = "monitor_payment_status"

    return {
        "vendor_relationship_status": health,
        "next_vendor_action": next_action,
        "late_payment_risk": payment_blocked or exception_open,
        "supplier_reply_agent": {
            "enabled": True,
            "allowed_topics": ["invoice_received", "approval_status", "payment_status", "exception_reason"],
            "blocked_topics": ["bank_detail_change_without_review", "unaudited_payment_commitment"],
        },
    }

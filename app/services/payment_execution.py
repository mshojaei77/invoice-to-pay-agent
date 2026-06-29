from __future__ import annotations


def build_payment_execution_plan(
    payment_plan: dict,
    approval_route: dict,
    fraud_result: dict,
    ledger_visibility_plan: dict,
    erp_sync_plan: dict,
) -> dict:
    fraud_blocked = fraud_result.get("fraud_status") == "blocked"
    payment_scheduled = payment_plan.get("payment_status") == "scheduled"
    vendor_line_blocked = ledger_visibility_plan.get("vendor_line_blocked_for_payment", True)

    if fraud_blocked:
        status = "blocked_for_fraud_review"
    elif vendor_line_blocked:
        status = "blocked_until_final_approval"
    elif payment_scheduled:
        status = "ready_for_payment_run"
    else:
        status = "blocked_until_exception_resolved"

    return {
        "payment_execution_status": status,
        "one_click_approval_enabled": approval_route.get("route") != "auto_post",
        "payment_run_ready": status == "ready_for_payment_run",
        "sync_target": erp_sync_plan.get("target_system", "cloud_erp"),
        "target_payment_date": payment_plan.get("target_payment_date"),
        "release_controls": [
            "final_approval",
            "no_open_exceptions",
            "fraud_controls_clear",
            "erp_sync_ready",
        ],
    }

from __future__ import annotations


def build_kpi_snapshot(
    requires_human_approval: bool,
    exception_result: dict,
    approval_route: dict,
    erp_result: dict | None,
    payment_plan: dict,
) -> dict:
    erp_status = (erp_result or {}).get("status")
    posted = erp_status == "posted"
    exception_count = int(exception_result.get("exception_count", 0))

    return {
        "invoice_count": 1,
        "posted_count": 1 if posted else 0,
        "touchless_rate": 1.0 if posted and not requires_human_approval else 0.0,
        "exception_rate": 1.0 if exception_count else 0.0,
        "exception_count": exception_count,
        "approval_route": approval_route.get("route"),
        "on_time_payment_candidate": payment_plan.get("payment_status") == "scheduled",
        "cashflow_bucket": payment_plan.get("cashflow_bucket"),
        "cycle_status": "posted" if posted else "requires_action",
    }

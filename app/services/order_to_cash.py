from __future__ import annotations


def build_order_to_cash_plan(
    exception_result: dict,
    payment_plan: dict,
    erp_sync_plan: dict,
    accounting_platform_profile: dict,
) -> dict:
    categories = set(exception_result.get("categories", []))
    sync_ready = erp_sync_plan.get("sync_status") == "ready"
    payment_blocked = payment_plan.get("payment_status") == "blocked"

    if payment_blocked or categories:
        service_mode = "exception_follow_up"
        sla_hours = 8
    elif sync_ready:
        service_mode = "continuous_cash_ops"
        sla_hours = 2
    else:
        service_mode = "sync_readiness_review"
        sla_hours = 24

    work_items = [
        {
            "queue": "invoice_resolution",
            "status": "open" if categories else "clear",
            "owner_agent": "receivables_operations_agent",
        },
        {
            "queue": "customer_or_vendor_follow_up",
            "status": "not_required" if not categories else "draft_outreach",
            "owner_agent": "customer_context_agent",
        },
        {
            "queue": "cash_application",
            "status": "monitor" if sync_ready else "blocked_until_sync_ready",
            "owner_agent": "cash_application_agent",
        },
    ]

    return {
        "o2c_status": "ready",
        "service_mode": service_mode,
        "sla_hours": sla_hours,
        "target_system": accounting_platform_profile.get("selected_platform", "cloud_erp"),
        "managed_work_items": work_items,
    }

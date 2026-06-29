from __future__ import annotations


def build_finance_agent_plan(
    exception_result: dict,
    payment_plan: dict,
    accounting_platform_profile: dict,
    multi_company_result: dict,
) -> dict:
    categories = set(exception_result.get("categories", []))
    agents = [
        {
            "agent": "purchase_agent",
            "mode": "exception_review" if categories else "auto_assist",
            "responsibility": "PO, receipt, supplier, and invoice matching.",
        },
        {
            "agent": "banking_agent",
            "mode": "payment_hold" if payment_plan.get("payment_status") == "blocked" else "payment_schedule_assist",
            "responsibility": "Payment timing, cashflow bucket, and payment status sync.",
        },
        {
            "agent": "debtor_management_agent",
            "mode": "not_applicable",
            "responsibility": "Reserved for AR workflows; listed to keep finance-agent boundaries explicit.",
        },
        {
            "agent": "accountant_collaboration_agent",
            "mode": "enabled" if multi_company_result.get("accountant_collaboration_enabled") else "connector_only",
            "responsibility": "Prepare review pack for accountants or external finance specialists.",
        },
    ]

    return {
        "agent_plan_status": "ready",
        "selected_platform": accounting_platform_profile.get("selected_platform"),
        "agents": agents,
    }

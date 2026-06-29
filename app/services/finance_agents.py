from __future__ import annotations


def build_finance_agent_plan(
    exception_result: dict,
    payment_plan: dict,
    accounting_platform_profile: dict,
    multi_company_result: dict,
    order_to_cash_plan: dict | None = None,
    accrual_close_plan: dict | None = None,
    spend_intelligence: dict | None = None,
) -> dict:
    categories = set(exception_result.get("categories", []))
    o2c = order_to_cash_plan or {}
    accruals = accrual_close_plan or {}
    spend = spend_intelligence or {}
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
            "mode": o2c.get("service_mode", "monitor_only"),
            "responsibility": "Order-to-cash exception follow-up, cash-application monitoring, and SLA-managed customer context.",
        },
        {
            "agent": "accountant_collaboration_agent",
            "mode": "enabled" if multi_company_result.get("accountant_collaboration_enabled") else "connector_only",
            "responsibility": "Prepare review pack for accountants or external finance specialists.",
        },
        {
            "agent": "close_agent",
            "mode": accruals.get("accrual_status", "review_required"),
            "responsibility": "Month-end accrual evidence, journal output, and close-action recommendations.",
        },
        {
            "agent": "spend_intelligence_agent",
            "mode": spend.get("spend_status", "monitored"),
            "responsibility": "Supplier invoice analytics, contract leakage, duplicate spend, and consolidation opportunities.",
        },
    ]

    return {
        "agent_plan_status": "ready",
        "selected_platform": accounting_platform_profile.get("selected_platform"),
        "agents": agents,
    }

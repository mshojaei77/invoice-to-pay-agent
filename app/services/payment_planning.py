from __future__ import annotations

from datetime import date, timedelta


def plan_payment(
    risk_level: str,
    approval_route: dict,
    exception_result: dict,
    invoice: dict | None = None,
) -> dict:
    today = date.today()
    due_date = _parse_date((invoice or {}).get("due_date")) or today + timedelta(days=30)
    discount_date = today + timedelta(days=10)

    if risk_level in {"medium", "high"} or exception_result.get("exception_status") == "open":
        recommendation = "hold_for_exception_resolution"
        target_payment_date = None
        cashflow_bucket = "blocked"
    elif discount_date <= due_date:
        recommendation = "pay_by_discount_window"
        target_payment_date = discount_date.isoformat()
        cashflow_bucket = "next_10_days"
    else:
        recommendation = "pay_on_terms"
        target_payment_date = due_date.isoformat()
        cashflow_bucket = "scheduled"

    return {
        "payment_status": "blocked" if target_payment_date is None else "scheduled",
        "recommendation": recommendation,
        "target_payment_date": target_payment_date,
        "due_date": due_date.isoformat(),
        "cashflow_bucket": cashflow_bucket,
        "approval_route": approval_route.get("route"),
    }


def _parse_date(value: object) -> date | None:
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None
    return None

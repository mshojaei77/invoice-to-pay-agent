from __future__ import annotations


def route_approval(
    risk_level: str,
    risk_score: float,
    exception_result: dict,
    gl_coding_result: dict | None = None,
) -> dict:
    categories = set(exception_result.get("categories", []))
    exceptions = exception_result.get("exceptions", [])
    coding_status = (gl_coding_result or {}).get("coding_status")

    if risk_level == "low" and not exceptions and coding_status != "needs_review":
        return {
            "route": "auto_post",
            "approver_role": "system",
            "sla_hours": 0,
            "reason": "low_risk_clean_match",
        }

    if "duplicate_control" in categories:
        return {
            "route": "ap_manager_review",
            "approver_role": "ap_manager",
            "sla_hours": 4,
            "reason": "duplicate_control_exception",
        }

    if "vendor_master_data" in categories:
        return {
            "route": "vendor_master_review",
            "approver_role": "vendor_master_data",
            "sla_hours": 24,
            "reason": "vendor_master_data_exception",
        }

    if "pricing" in categories or "receiving" in categories or "matching" in categories:
        return {
            "route": "buyer_receiving_review",
            "approver_role": "buyer_or_receiving_owner",
            "sla_hours": 24,
            "reason": "three_way_match_exception",
        }

    if coding_status == "needs_review":
        return {
            "route": "finance_coding_review",
            "approver_role": "finance_controller",
            "sla_hours": 24,
            "reason": "gl_coding_uncertain",
        }

    return {
        "route": "finance_review",
        "approver_role": "finance_controller",
        "sla_hours": 24 if risk_score < 70 else 8,
        "reason": "risk_threshold_review",
    }

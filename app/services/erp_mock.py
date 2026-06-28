from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4


def post_invoice_to_erp_mock(
    run_id: str,
    invoice: dict | None,
    approval: dict | None,
    risk_level: str,
    duplicate_result: dict,
    match_result: dict,
    validation_errors: list[dict],
    business_rule_errors: list[dict],
) -> dict:
    if invoice is None:
        return {"status": "rejected", "rejection_reason": "missing_invoice"}

    if validation_errors:
        return {"status": "rejected", "rejection_reason": "invalid_schema"}

    if not invoice.get("invoice_number"):
        return {"status": "rejected", "rejection_reason": "missing_invoice_number"}

    if not invoice.get("vendor"):
        return {"status": "rejected", "rejection_reason": "missing_vendor"}

    if duplicate_result.get("duplicate_status") == "confirmed_duplicate":
        return {"status": "rejected", "rejection_reason": "duplicate_invoice"}

    if "total_mismatch" in match_result.get("mismatch_reasons", []):
        if not approval or approval.get("status") not in {"human_approved", "approved"}:
            return {"status": "rejected", "rejection_reason": "total_mismatch_requires_approval"}

    if risk_level == "high":
        if not approval or approval.get("status") not in {"human_approved", "approved"}:
            return {"status": "rejected", "rejection_reason": "high_risk_requires_approval"}

    return {
        "status": "posted",
        "erp_post_id": f"ERP-{uuid4()}",
        "posted_at": datetime.now(timezone.utc).isoformat(),
        "rejection_reason": None,
    }

from __future__ import annotations


def build_ledger_visibility_plan(
    approval_route: dict,
    payment_plan: dict,
    erp_sync_plan: dict,
    line_approval_plan: dict,
) -> dict:
    route = approval_route.get("route")
    fully_approved = route == "auto_post" and payment_plan.get("payment_status") == "scheduled"
    draft_visible = erp_sync_plan.get("sync_status") == "ready"

    return {
        "ledger_visibility_status": "posted_visible" if fully_approved else "draft_visible_payment_blocked",
        "visible_in_ledger_before_final_approval": draft_visible,
        "vendor_line_blocked_for_payment": not fully_approved,
        "payment_release_condition": "final_approval_and_no_open_exceptions",
        "paid_status_archive_sync": {
            "enabled": True,
            "source": erp_sync_plan.get("target_system", "cloud_erp"),
            "archive_fields": ["invoice_number", "vendor", "amount", "approval_status", "paid_status"],
        },
        "line_edit_sync": {
            "enabled": bool(line_approval_plan.get("supports_line_edits_before_final_approval")),
            "sync_target": "erp_draft_vendor_bill",
            "audited_fields": (line_approval_plan.get("edit_policy") or {}).get("editable_fields", []),
        },
    }

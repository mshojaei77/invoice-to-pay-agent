from __future__ import annotations


def build_line_approval_plan(
    uploaded_documents: list[dict],
    gl_coding_result: dict,
    approval_route: dict,
) -> dict:
    evidence = _evidence_text(uploaded_documents)
    gl_account = gl_coding_result.get("gl_account")
    cost_center = gl_coding_result.get("cost_center")
    route = approval_route.get("route", "finance_review")
    has_large_invoice_signal = any(
        token in evidence
        for token in ("large_lines", "excel", "xlsx", "manual_split", "line_split")
    )

    dimensions = {
        "gl_account": gl_account,
        "cost_center": cost_center,
        "location": _infer_location(evidence),
        "department": cost_center,
    }
    approver_chain = _build_approver_chain(route, dimensions)

    return {
        "line_approval_status": "ready" if gl_account and cost_center else "needs_dimension_review",
        "routing_basis": "gl_account_cost_center_location",
        "supports_multiple_same_level_approvers": True,
        "supports_line_edits_before_final_approval": True,
        "manual_line_split_supported": True,
        "excel_import_recommended": has_large_invoice_signal,
        "dimensions": dimensions,
        "approver_chain": approver_chain,
        "visibility": {
            "show_previous_approvers": True,
            "show_current_approvers": True,
            "show_next_approvers": True,
        },
        "edit_policy": {
            "editable_fields": ["gl_account", "cost_center", "location", "department", "line_split"],
            "sync_edits_to_erp_draft": True,
            "requires_reapproval_on_dimension_change": True,
        },
    }


def _build_approver_chain(route: str, dimensions: dict) -> list[dict]:
    first_role = "asset_owner" if dimensions.get("cost_center") in {"operations", "engineering"} else "requester"
    chain = [
        {"step": 1, "role": first_role, "status": "pending", "same_level_group": "business_owner"},
        {"step": 2, "role": "cost_center_owner", "status": "queued", "same_level_group": "business_owner"},
    ]
    if route != "auto_post":
        chain.append({"step": 3, "role": "finance_controller", "status": "queued", "same_level_group": "finance"})
    return chain


def _infer_location(evidence: str) -> str:
    if "uk" in evidence or "gbp" in evidence:
        return "uk"
    if "eu" in evidence or "eur" in evidence or "swiss" in evidence:
        return "eu"
    if "us" in evidence or "usd" in evidence:
        return "us"
    if "china" in evidence or "cny" in evidence or "chinese" in evidence:
        return "cn"
    return "default"


def _evidence_text(uploaded_documents: list[dict]) -> str:
    return " ".join(
        f"{document.get('filename', '')} {document.get('path', '')}".lower()
        for document in uploaded_documents
    )

from __future__ import annotations


def build_billing_revenue_plan(
    uploaded_documents: list[dict],
    erp_sync_plan: dict,
    payment_plan: dict,
    compliance_result: dict,
) -> dict:
    path_text = " ".join(
        f"{document.get('filename', '')} {document.get('path', '')}".lower()
        for document in uploaded_documents
    )
    has_contract_signal = "contract" in path_text or "rate_card" in path_text
    sync_ready = erp_sync_plan.get("sync_status") == "ready"

    if has_contract_signal and sync_ready:
        billing_action = "validate_usage_or_contract_terms_then_invoice"
    elif sync_ready:
        billing_action = "monitor_invoice_posting_and_payment_terms"
    else:
        billing_action = "block_revenue_action_until_controls_ready"

    return {
        "billing_status": "ready" if sync_ready else "blocked",
        "billing_action": billing_action,
        "contract_signal_detected": has_contract_signal,
        "revenue_controls": {
            "erp_sync_ready": sync_ready,
            "retention_class": compliance_result.get("retention_class"),
            "payment_status": payment_plan.get("payment_status"),
        },
        "analytics": {
            "cashflow_bucket": payment_plan.get("cashflow_bucket"),
            "target_payment_date": payment_plan.get("target_payment_date"),
        },
    }

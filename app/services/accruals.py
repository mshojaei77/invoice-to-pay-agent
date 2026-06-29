from __future__ import annotations


def build_accrual_close_plan(
    uploaded_documents: list[dict],
    exception_result: dict,
    gl_coding_result: dict,
    payment_plan: dict,
) -> dict:
    document_types = {document.get("document_type") for document in uploaded_documents}
    has_receipt_evidence = "delivery_note" in document_types
    has_invoice = "invoice" in document_types
    exceptions_open = exception_result.get("exception_status") == "open"
    coding_ready = gl_coding_result.get("coding_status") == "suggested"

    if has_receipt_evidence and not has_invoice:
        close_action = "book_goods_received_not_invoiced_accrual"
    elif has_invoice and exceptions_open:
        close_action = "hold_accrual_until_exception_resolved"
    elif has_invoice and coding_ready:
        close_action = "reverse_or_clear_accrual_on_invoice_posting"
    else:
        close_action = "controller_review"

    confidence = 0.88 if has_receipt_evidence and coding_ready and not exceptions_open else 0.62

    return {
        "accrual_status": "ready" if confidence >= 0.8 else "review_required",
        "close_action": close_action,
        "confidence": confidence,
        "evidence_sources": sorted(document_types),
        "journal_output": {
            "gl_account": gl_coding_result.get("gl_account"),
            "cost_center": gl_coding_result.get("cost_center"),
            "cashflow_bucket": payment_plan.get("cashflow_bucket"),
            "supporting_documents": [
                document.get("filename") or document.get("path")
                for document in uploaded_documents
            ],
        },
        "audit_ready": has_receipt_evidence and bool(gl_coding_result.get("gl_account")),
    }

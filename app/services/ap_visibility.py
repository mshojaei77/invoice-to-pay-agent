from __future__ import annotations


def build_realtime_ap_visibility(
    uploaded_documents: list[dict],
    exception_result: dict,
    payment_plan: dict,
    payment_execution_plan: dict,
    spend_intelligence: dict,
    kpi_snapshot: dict | None = None,
) -> dict:
    invoice_count = max(1, len([document for document in uploaded_documents if document.get("document_type") == "invoice"]))
    exception_count = int(exception_result.get("exception_count", 0))
    payment_ready = payment_execution_plan.get("payment_run_ready", False)

    return {
        "visibility_status": "real_time_snapshot_ready",
        "cash_flow_visibility": "blocked" if payment_plan.get("payment_status") == "blocked" else "scheduled",
        "invoice_volume_capacity": {
            "current_batch_invoice_count": invoice_count,
            "scale_without_headcount_signal": "10x_ready_for_clean_low_risk_batches" if exception_count == 0 else "exception_staffing_required",
        },
        "open_exception_count": exception_count,
        "payment_run_ready": payment_ready,
        "spend_opportunity_count": spend_intelligence.get("opportunity_count", 0),
        "kpi_snapshot": kpi_snapshot or {},
    }

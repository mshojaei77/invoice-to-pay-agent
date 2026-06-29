from __future__ import annotations


def build_erp_sync_plan(
    run_id: str,
    uploaded_documents: list[dict],
    gl_coding_result: dict,
    compliance_result: dict,
    payment_plan: dict,
) -> dict:
    return {
        "target_system": "cloud_erp",
        "integration_mode": "mock_posting_payload",
        "run_id": run_id,
        "posting_payload": {
            "document_refs": [
                {
                    "filename": document.get("filename"),
                    "path": document.get("path"),
                    "document_type": document.get("document_type"),
                }
                for document in uploaded_documents
            ],
            "gl_account": gl_coding_result.get("gl_account"),
            "cost_center": gl_coding_result.get("cost_center"),
            "allocation": gl_coding_result.get("allocation", []),
            "payment_recommendation": payment_plan.get("recommendation"),
            "target_payment_date": payment_plan.get("target_payment_date"),
            "retention_class": compliance_result.get("retention_class"),
        },
        "sync_status": "ready" if compliance_result.get("compliance_status") != "blocked" else "blocked",
        "single_source_of_truth": True,
    }

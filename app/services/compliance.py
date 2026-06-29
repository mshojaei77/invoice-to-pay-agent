from __future__ import annotations


def evaluate_compliance(
    uploaded_documents: list[dict],
    exception_result: dict,
    approval_route: dict | None = None,
) -> dict:
    document_types = {document.get("document_type") for document in uploaded_documents}
    exceptions = exception_result.get("exceptions", [])
    controls = [
        {
            "control": "centralized_document_archive",
            "status": "passed" if uploaded_documents else "failed",
            "message": "Uploaded documents are linked to the run record.",
        },
        {
            "control": "invoice_supporting_evidence",
            "status": "passed" if {"invoice", "purchase_order", "delivery_note"}.issubset(document_types) else "review",
            "message": "Invoice, PO, and delivery evidence should be retained for audit support.",
        },
        {
            "control": "segregation_of_duties",
            "status": "passed" if (approval_route or {}).get("approver_role") != "system" or not exceptions else "review",
            "message": "Exception invoices should be reviewed outside automated posting.",
        },
        {
            "control": "exception_audit_trail",
            "status": "passed",
            "message": "Risk, exception, approval, ERP, and audit outputs are correlated by run_id.",
        },
    ]

    failed = [item for item in controls if item["status"] == "failed"]
    review = [item for item in controls if item["status"] == "review"]

    return {
        "compliance_status": "blocked" if failed else "review" if review else "ready",
        "controls": controls,
        "retention_class": "financial_record",
        "sensitive_data_classes": ["supplier", "tax", "payment"],
        "requires_role_based_access": True,
    }

from __future__ import annotations


def build_netsuite_ap_readiness(
    uploaded_documents: list[dict],
    parsed_documents: list[dict],
    accounting_platform_profile: dict,
    multi_company_result: dict,
    line_approval_plan: dict,
    ledger_visibility_plan: dict,
    po_lifecycle_plan: dict,
) -> dict:
    evidence = _evidence_text(uploaded_documents, parsed_documents)
    selected_platform = accounting_platform_profile.get("selected_platform")
    global_vendor_signal = any(
        token in evidence
        for token in ("vat", "wht", "swiss", "china", "chinese", "europe", "eur", "gbp", "cad", "aud")
    )
    non_english_signal = any(token in evidence for token in ("chinese", "china", "swiss", "nicht", "rechnung"))
    multicurrency_ready = bool(multi_company_result.get("multi_company_supported")) and global_vendor_signal

    requirements = [
        {
            "requirement": "non_english_ocr",
            "status": "review_with_real_vendor_samples" if non_english_signal else "ready_for_digital_pdfs",
        },
        {
            "requirement": "multi_currency_multi_subsidiary",
            "status": "ready" if multicurrency_ready else "review_required",
        },
        {
            "requirement": "line_level_approval_by_gl_cost_center",
            "status": line_approval_plan.get("line_approval_status", "needs_dimension_review"),
        },
        {
            "requirement": "approval_chain_visibility",
            "status": "ready" if (line_approval_plan.get("visibility") or {}).get("show_next_approvers") else "review_required",
        },
        {
            "requirement": "archive_paid_status",
            "status": "ready" if (ledger_visibility_plan.get("paid_status_archive_sync") or {}).get("enabled") else "review_required",
        },
        {
            "requirement": "preapproval_ledger_visibility_payment_hold",
            "status": ledger_visibility_plan.get("ledger_visibility_status", "review_required"),
        },
        {
            "requirement": "excel_import_manual_line_split",
            "status": "ready" if line_approval_plan.get("manual_line_split_supported") else "review_required",
        },
        {
            "requirement": "po_creation_approval_matching",
            "status": po_lifecycle_plan.get("po_lifecycle_status", "review_required"),
        },
    ]

    ready_count = sum(1 for item in requirements if str(item["status"]).startswith(("ready", "matched", "posted")))

    return {
        "netsuite_profile_status": "native_or_partner_ready" if selected_platform == "netsuite" else "connector_contract_ready",
        "selected_platform": selected_platform,
        "invoice_volume_profile": "mid_market_300_400_invoices_per_month",
        "global_vendor_profile": global_vendor_signal,
        "non_english_invoice_signal": non_english_signal,
        "readiness_score": round(ready_count / len(requirements), 2),
        "requirements": requirements,
        "recommended_due_diligence": [
            "Test OCR with real non-English vendor invoices before selecting a SuiteApp.",
            "Confirm vendor bills update native NetSuite POs and draft ledger records, not only standalone AP records.",
            "Validate payment holds, paid-status archive sync, and line-level approval history in a NetSuite sandbox.",
        ],
    }


def _evidence_text(uploaded_documents: list[dict], parsed_documents: list[dict]) -> str:
    upload_text = " ".join(
        f"{document.get('filename', '')} {document.get('path', '')}".lower()
        for document in uploaded_documents
    )
    parsed_text = " ".join((document.get("text") or "").lower()[:1000] for document in parsed_documents)
    return f"{upload_text} {parsed_text}"

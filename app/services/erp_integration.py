from __future__ import annotations


def build_erp_sync_plan(
    run_id: str,
    uploaded_documents: list[dict],
    gl_coding_result: dict,
    compliance_result: dict,
    payment_plan: dict,
    accounting_platform_profile: dict | None = None,
    multi_company_result: dict | None = None,
    industry_policy_result: dict | None = None,
) -> dict:
    platform = accounting_platform_profile or {}
    multi_company = multi_company_result or {}
    industry_policy = industry_policy_result or {}
    return {
        "target_system": platform.get("selected_platform", "cloud_erp"),
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
            "entity_code": multi_company.get("entity_code"),
            "industry": industry_policy.get("industry"),
            "vat_policy": industry_policy.get("vat_policy"),
            "valuation_policy": industry_policy.get("valuation_policy"),
        },
        "sync_status": "ready" if compliance_result.get("compliance_status") != "blocked" else "blocked",
        "single_source_of_truth": True,
        "connector_contract": platform.get("connector_contract", {}),
    }

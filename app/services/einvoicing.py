from __future__ import annotations


def build_einvoicing_compliance_plan(
    uploaded_documents: list[dict],
    compliance_result: dict,
    accounting_platform_profile: dict,
    industry_policy_result: dict,
) -> dict:
    path_text = " ".join(
        f"{document.get('filename', '')} {document.get('path', '')}".lower()
        for document in uploaded_documents
    )
    cross_border_signal = any(token in path_text for token in ("eu", "swiss", "vat", "wht", "china"))
    platform = accounting_platform_profile.get("selected_platform", "cloud_erp")
    compliance_ready = compliance_result.get("compliance_status") != "blocked"

    requirements = [
        {
            "requirement": "structured_invoice_archive",
            "status": "ready" if compliance_ready else "blocked",
        },
        {
            "requirement": "tax_reporting_payload",
            "status": "review_required" if cross_border_signal else "not_required_for_fixture",
        },
        {
            "requirement": "country_clearance_adapter",
            "status": "connector_required" if cross_border_signal else "not_required_for_fixture",
        },
    ]

    return {
        "einvoicing_status": "review_required" if cross_border_signal else "ready",
        "jurisdiction_signal": "cross_border_or_tax_specific" if cross_border_signal else "domestic_or_unknown",
        "target_platform": platform,
        "vat_policy": industry_policy_result.get("vat_policy"),
        "requirements": requirements,
    }

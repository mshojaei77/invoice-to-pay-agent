from __future__ import annotations


INDUSTRY_RULES = {
    "manufacturing": {
        "valuation_policy": "inventory_receipt_required",
        "vat_policy": "standard_vat_code_required",
        "extra_controls": ["goods_receipt_match", "inventory_valuation_alignment"],
    },
    "wholesale": {
        "valuation_policy": "stock_movement_required",
        "vat_policy": "standard_vat_code_required",
        "extra_controls": ["goods_receipt_match", "landed_cost_review"],
    },
    "construction": {
        "valuation_policy": "project_cost_allocation_required",
        "vat_policy": "domestic_reverse_charge_review",
        "extra_controls": ["project_code_required", "retention_review"],
    },
    "hospitality": {
        "valuation_policy": "location_cost_center_required",
        "vat_policy": "hospitality_tax_rate_review",
        "extra_controls": ["site_cost_center_required"],
    },
    "professional_services": {
        "valuation_policy": "expense_recognition_required",
        "vat_policy": "service_tax_code_required",
        "extra_controls": ["client_or_project_required"],
    },
}


def apply_industry_policy(uploaded_documents: list[dict], gl_coding_result: dict) -> dict:
    evidence = " ".join(
        str(document.get("filename") or document.get("path") or "")
        for document in uploaded_documents
    ).lower()
    industry = next((name for name in INDUSTRY_RULES if name in evidence), "generic")
    policy = INDUSTRY_RULES.get(
        industry,
        {
            "valuation_policy": "expense_or_inventory_review",
            "vat_policy": "tax_code_required",
            "extra_controls": ["vat_code_mapping", "dimension_mapping"],
        },
    )

    missing_controls = []
    if not gl_coding_result.get("gl_account"):
        missing_controls.append("gl_account_required")
    if not gl_coding_result.get("cost_center"):
        missing_controls.append("cost_center_required")

    return {
        "industry": industry,
        "policy_status": "ready" if not missing_controls else "review",
        "missing_controls": missing_controls,
        **policy,
    }

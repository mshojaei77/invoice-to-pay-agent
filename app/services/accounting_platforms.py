from __future__ import annotations


SUPPORTED_PLATFORMS = {
    "exact": {
        "target_market": "sme_and_accountants",
        "connector_style": "accounting_erp_api",
        "supports_multi_company": True,
        "supports_accountant_collaboration": True,
        "posting_objects": ["purchase_invoice", "supplier", "gl_account", "cost_center", "vat_code"],
    },
    "netsuite": {
        "target_market": "mid_market_erp",
        "connector_style": "erp_api",
        "supports_multi_company": True,
        "supports_accountant_collaboration": False,
        "posting_objects": ["vendor_bill", "vendor", "account", "department", "tax_code"],
    },
    "dynamics": {
        "target_market": "mid_market_erp",
        "connector_style": "erp_api",
        "supports_multi_company": True,
        "supports_accountant_collaboration": False,
        "posting_objects": ["vendor_invoice", "vendor", "main_account", "financial_dimension", "sales_tax_group"],
    },
    "sap": {
        "target_market": "enterprise_erp",
        "connector_style": "erp_api",
        "supports_multi_company": True,
        "supports_accountant_collaboration": False,
        "posting_objects": ["supplier_invoice", "business_partner", "gl_account", "cost_center", "tax_code"],
    },
    "quickbooks": {
        "target_market": "small_business_accounting",
        "connector_style": "accounting_api",
        "supports_multi_company": False,
        "supports_accountant_collaboration": True,
        "posting_objects": ["bill", "vendor", "expense_account", "class", "tax_code"],
    },
}


def build_accounting_platform_profile(uploaded_documents: list[dict]) -> dict:
    evidence = " ".join(
        str(document.get("filename") or document.get("path") or "")
        for document in uploaded_documents
    ).lower()
    platform = next((name for name in SUPPORTED_PLATFORMS if name in evidence), "generic_cloud_erp")
    profile = SUPPORTED_PLATFORMS.get(
        platform,
        {
            "target_market": "connector_neutral",
            "connector_style": "adapter_contract",
            "supports_multi_company": True,
            "supports_accountant_collaboration": True,
            "posting_objects": ["invoice", "supplier", "gl_account", "cost_center", "tax_code"],
        },
    )

    return {
        "selected_platform": platform,
        "supported_platforms": sorted(SUPPORTED_PLATFORMS),
        "connector_contract": {
            "capabilities": [
                "validate_supplier",
                "map_dimensions",
                "map_vat_code",
                "post_purchase_invoice",
                "sync_payment_status",
            ],
            "required_fields": ["supplier", "invoice_number", "total_amount", "currency", "gl_account", "tax_code"],
        },
        **profile,
    }

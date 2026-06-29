from app.services.accounting_platforms import build_accounting_platform_profile


def test_detects_exact_platform_from_document_name() -> None:
    result = build_accounting_platform_profile(
        uploaded_documents=[{"filename": "exact_purchase_invoice.pdf"}]
    )

    assert result["selected_platform"] == "exact"
    assert result["supports_accountant_collaboration"] is True
    assert "quickbooks" in result["supported_platforms"]


def test_generic_profile_is_connector_neutral() -> None:
    result = build_accounting_platform_profile(
        uploaded_documents=[{"filename": "invoice.pdf"}]
    )

    assert result["selected_platform"] == "generic_cloud_erp"
    assert result["connector_contract"]["capabilities"]

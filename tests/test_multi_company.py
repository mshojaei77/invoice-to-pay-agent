from app.services.multi_company import evaluate_multi_company_controls


def test_multi_company_ready_for_exact_eu_entity() -> None:
    result = evaluate_multi_company_controls(
        uploaded_documents=[{"filename": "exact_eu_invoice.pdf"}],
        accounting_platform_profile={
            "supports_multi_company": True,
            "supports_accountant_collaboration": True,
        },
    )

    assert result["entity_code"] == "eu_entity"
    assert result["control_status"] == "ready"
    assert result["accountant_collaboration_enabled"] is True


def test_single_company_platform_requires_review_for_specific_entity() -> None:
    result = evaluate_multi_company_controls(
        uploaded_documents=[{"filename": "quickbooks_us_invoice.pdf"}],
        accounting_platform_profile={"supports_multi_company": False},
    )

    assert result["entity_code"] == "us_entity"
    assert result["control_status"] == "review"

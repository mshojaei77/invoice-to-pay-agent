from app.services.industry_policy import apply_industry_policy


def test_manufacturing_policy_requires_inventory_alignment() -> None:
    result = apply_industry_policy(
        uploaded_documents=[{"filename": "manufacturing_invoice.pdf"}],
        gl_coding_result={"gl_account": "5000", "cost_center": "plant"},
    )

    assert result["industry"] == "manufacturing"
    assert result["policy_status"] == "ready"
    assert "inventory_valuation_alignment" in result["extra_controls"]


def test_missing_coding_requires_review() -> None:
    result = apply_industry_policy(
        uploaded_documents=[{"filename": "invoice.pdf"}],
        gl_coding_result={},
    )

    assert result["policy_status"] == "review"
    assert "gl_account_required" in result["missing_controls"]

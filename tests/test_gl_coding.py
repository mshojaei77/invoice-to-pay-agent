from app.services.gl_coding import suggest_gl_coding


def test_suggests_vendor_history_gl_coding() -> None:
    result = suggest_gl_coding(
        uploaded_documents=[{"filename": "invoice_007_aws_europe_vat.pdf"}],
        parsed_documents=[],
    )

    assert result["coding_status"] == "suggested"
    assert result["gl_account"] == "6200-cloud-services"
    assert result["cost_center"] == "engineering"


def test_returns_review_when_no_rule_matches() -> None:
    result = suggest_gl_coding(
        uploaded_documents=[{"filename": "invoice_unknown_vendor.pdf"}],
        parsed_documents=[],
    )

    assert result["coding_status"] == "needs_review"
    assert result["gl_account"] is None

from app.services.erp_mock import post_invoice_to_erp_mock


def make_invoice() -> dict:
    return {
        "invoice_number": "INV-001",
        "vendor": {"name": "Acme BV"},
        "total_amount": "121.00",
    }


def test_clean_invoice_posts() -> None:
    result = post_invoice_to_erp_mock(
        run_id="run-001",
        invoice=make_invoice(),
        approval={"status": "auto_approved"},
        risk_level="low",
        duplicate_result={"duplicate_status": "clear"},
        match_result={"match_status": "matched", "mismatch_reasons": []},
        validation_errors=[],
        business_rule_errors=[],
    )
    assert result["status"] == "posted"
    assert result["erp_post_id"].startswith("ERP-")


def test_missing_invoice_rejected() -> None:
    result = post_invoice_to_erp_mock(
        run_id="run-001",
        invoice=None,
        approval=None,
        risk_level="low",
        duplicate_result={"duplicate_status": "clear"},
        match_result={"match_status": "matched", "mismatch_reasons": []},
        validation_errors=[],
        business_rule_errors=[],
    )
    assert result["status"] == "rejected"
    assert result["rejection_reason"] == "missing_invoice"


def test_invalid_schema_rejected() -> None:
    result = post_invoice_to_erp_mock(
        run_id="run-001",
        invoice=make_invoice(),
        approval=None,
        risk_level="low",
        duplicate_result={"duplicate_status": "clear"},
        match_result={"match_status": "matched", "mismatch_reasons": []},
        validation_errors=[{"field": "total"}],
        business_rule_errors=[],
    )
    assert result["status"] == "rejected"
    assert result["rejection_reason"] == "invalid_schema"


def test_missing_invoice_number_rejected() -> None:
    result = post_invoice_to_erp_mock(
        run_id="run-001",
        invoice={"vendor": {"name": "Acme BV"}},
        approval=None,
        risk_level="low",
        duplicate_result={"duplicate_status": "clear"},
        match_result={"match_status": "matched", "mismatch_reasons": []},
        validation_errors=[],
        business_rule_errors=[],
    )
    assert result["rejection_reason"] == "missing_invoice_number"


def test_missing_vendor_rejected() -> None:
    result = post_invoice_to_erp_mock(
        run_id="run-001",
        invoice={"invoice_number": "INV-001"},
        approval=None,
        risk_level="low",
        duplicate_result={"duplicate_status": "clear"},
        match_result={"match_status": "matched", "mismatch_reasons": []},
        validation_errors=[],
        business_rule_errors=[],
    )
    assert result["rejection_reason"] == "missing_vendor"


def test_confirmed_duplicate_rejected() -> None:
    result = post_invoice_to_erp_mock(
        run_id="run-001",
        invoice=make_invoice(),
        approval=None,
        risk_level="low",
        duplicate_result={"duplicate_status": "confirmed_duplicate"},
        match_result={"match_status": "matched", "mismatch_reasons": []},
        validation_errors=[],
        business_rule_errors=[],
    )
    assert result["rejection_reason"] == "duplicate_invoice"


def test_total_mismatch_requires_approval() -> None:
    result = post_invoice_to_erp_mock(
        run_id="run-001",
        invoice=make_invoice(),
        approval=None,
        risk_level="low",
        duplicate_result={"duplicate_status": "clear"},
        match_result={"match_status": "mismatch", "mismatch_reasons": ["total_mismatch"]},
        validation_errors=[],
        business_rule_errors=[],
    )
    assert result["rejection_reason"] == "total_mismatch_requires_approval"


def test_total_mismatch_with_approval_passes() -> None:
    result = post_invoice_to_erp_mock(
        run_id="run-001",
        invoice=make_invoice(),
        approval={"status": "approved"},
        risk_level="low",
        duplicate_result={"duplicate_status": "clear"},
        match_result={"match_status": "mismatch", "mismatch_reasons": ["total_mismatch"]},
        validation_errors=[],
        business_rule_errors=[],
    )
    assert result["status"] == "posted"


def test_high_risk_requires_approval() -> None:
    result = post_invoice_to_erp_mock(
        run_id="run-001",
        invoice=make_invoice(),
        approval=None,
        risk_level="high",
        duplicate_result={"duplicate_status": "clear"},
        match_result={"match_status": "matched", "mismatch_reasons": []},
        validation_errors=[],
        business_rule_errors=[],
    )
    assert result["rejection_reason"] == "high_risk_requires_approval"


def test_high_risk_with_approval_passes() -> None:
    result = post_invoice_to_erp_mock(
        run_id="run-001",
        invoice=make_invoice(),
        approval={"status": "human_approved"},
        risk_level="high",
        duplicate_result={"duplicate_status": "clear"},
        match_result={"match_status": "matched", "mismatch_reasons": []},
        validation_errors=[],
        business_rule_errors=[],
    )
    assert result["status"] == "posted"

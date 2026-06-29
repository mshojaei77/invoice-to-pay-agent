from app.services.exceptions import classify_exceptions


def test_clear_inputs_return_clear_exception_status() -> None:
    result = classify_exceptions(
        business_rule_errors=[],
        duplicate_result={"duplicate_status": "clear"},
        match_result={"match_status": "matched", "mismatch_reasons": []},
    )

    assert result["exception_status"] == "clear"
    assert result["exception_count"] == 0
    assert result["highest_severity"] == "none"


def test_classifies_duplicate_and_three_way_match_exceptions() -> None:
    result = classify_exceptions(
        business_rule_errors=[{"code": "missing_delivery_note", "severity": "medium"}],
        duplicate_result={"duplicate_status": "possible_duplicate"},
        match_result={"match_status": "mismatch", "mismatch_reasons": ["total_mismatch", "delivery_not_complete"]},
    )

    assert result["exception_status"] == "open"
    assert result["exception_count"] == 4
    assert result["highest_severity"] == "high"
    assert "duplicate_control" in result["categories"]
    assert "pricing" in result["categories"]
    assert "receiving" in result["categories"]

from app.services.risk import calculate_risk


def test_no_issues_returns_low_risk() -> None:
    result = calculate_risk([], [], {"duplicate_status": "clear"}, {"match_status": "matched", "mismatch_reasons": []})
    assert result.risk_level == "low"
    assert result.risk_score == 0.0
    assert result.requires_human_approval is False


def test_validation_errors_score_50() -> None:
    result = calculate_risk(
        [{"field": "total"}],
        [],
        {"duplicate_status": "clear"},
        {"match_status": "matched", "mismatch_reasons": []},
    )
    assert result.risk_score == 50.0
    assert result.risk_level == "medium"


def test_missing_po_scores_15() -> None:
    result = calculate_risk(
        [],
        [{"code": "missing_po"}],
        {"duplicate_status": "clear"},
        {"match_status": "matched", "mismatch_reasons": []},
    )
    assert result.risk_score == 15.0
    assert result.risk_level == "low"


def test_invalid_iban_scores_30() -> None:
    result = calculate_risk(
        [],
        [{"code": "invalid_iban"}],
        {"duplicate_status": "clear"},
        {"match_status": "matched", "mismatch_reasons": []},
    )
    assert result.risk_score == 30.0
    assert result.risk_level == "medium"
    assert result.requires_human_approval is True


def test_confirmed_duplicate_scores_100() -> None:
    result = calculate_risk(
        [],
        [],
        {"duplicate_status": "confirmed_duplicate"},
        {"match_status": "matched", "mismatch_reasons": []},
    )
    assert result.risk_score == 100.0
    assert result.risk_level == "high"
    assert result.requires_human_approval is True


def test_possible_duplicate_scores_30() -> None:
    result = calculate_risk(
        [],
        [],
        {"duplicate_status": "possible_duplicate"},
        {"match_status": "matched", "mismatch_reasons": []},
    )
    assert result.risk_score == 30.0
    assert result.risk_level == "medium"


def test_handwritten_correction_scores_35() -> None:
    result = calculate_risk(
        [],
        [{"code": "handwritten_correction"}],
        {"duplicate_status": "clear"},
        {"match_status": "matched", "mismatch_reasons": []},
    )
    assert result.risk_score == 35.0
    assert result.risk_level == "medium"


def test_mismatch_reasons_add_25_each() -> None:
    result = calculate_risk(
        [],
        [],
        {"duplicate_status": "clear"},
        {"match_status": "mismatch", "mismatch_reasons": ["total_mismatch", "vendor_mismatch"]},
    )
    assert result.risk_score == 50.0
    assert result.risk_level == "medium"


def test_combined_scores_cap_at_100() -> None:
    result = calculate_risk(
        [{"field": "total"}],
        [{"code": "handwritten_correction"}, {"code": "invalid_iban"}],
        {"duplicate_status": "confirmed_duplicate"},
        {"match_status": "mismatch", "mismatch_reasons": ["total_mismatch"]},
    )
    assert result.risk_score == 100.0
    assert result.risk_level == "high"


def test_medium_threshold() -> None:
    result = calculate_risk(
        [],
        [{"code": "missing_po"}, {"code": "missing_iban"}],
        {"duplicate_status": "clear"},
        {"match_status": "matched", "mismatch_reasons": []},
    )
    assert 25 <= result.risk_score < 70
    assert result.risk_level == "medium"


def test_high_threshold() -> None:
    result = calculate_risk(
        [{"field": "total"}],
        [{"code": "invalid_iban"}],
        {"duplicate_status": "clear"},
        {"match_status": "matched", "mismatch_reasons": []},
    )
    assert result.risk_score >= 70
    assert result.risk_level == "high"

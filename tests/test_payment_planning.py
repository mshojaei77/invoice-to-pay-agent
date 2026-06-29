from app.services.payment_planning import plan_payment


def test_clean_invoice_uses_discount_window() -> None:
    result = plan_payment(
        risk_level="low",
        approval_route={"route": "auto_post"},
        exception_result={"exception_status": "clear"},
    )

    assert result["payment_status"] == "scheduled"
    assert result["recommendation"] == "pay_by_discount_window"
    assert result["cashflow_bucket"] == "next_10_days"


def test_exception_invoice_blocks_payment() -> None:
    result = plan_payment(
        risk_level="high",
        approval_route={"route": "ap_manager_review"},
        exception_result={"exception_status": "open"},
    )

    assert result["payment_status"] == "blocked"
    assert result["recommendation"] == "hold_for_exception_resolution"

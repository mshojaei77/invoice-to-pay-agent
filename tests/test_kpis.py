from app.services.kpis import build_kpi_snapshot


def test_clean_posted_invoice_has_touchless_kpi() -> None:
    result = build_kpi_snapshot(
        requires_human_approval=False,
        exception_result={"exception_count": 0},
        approval_route={"route": "auto_post"},
        erp_result={"status": "posted"},
        payment_plan={"payment_status": "scheduled", "cashflow_bucket": "next_10_days"},
    )

    assert result["touchless_rate"] == 1.0
    assert result["exception_rate"] == 0.0
    assert result["cycle_status"] == "posted"


def test_exception_invoice_has_exception_kpi() -> None:
    result = build_kpi_snapshot(
        requires_human_approval=True,
        exception_result={"exception_count": 2},
        approval_route={"route": "buyer_receiving_review"},
        erp_result={"status": "not_posted"},
        payment_plan={"payment_status": "blocked", "cashflow_bucket": "blocked"},
    )

    assert result["touchless_rate"] == 0.0
    assert result["exception_rate"] == 1.0
    assert result["cycle_status"] == "requires_action"

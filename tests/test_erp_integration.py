from app.services.erp_integration import build_erp_sync_plan


def test_builds_cloud_erp_payload() -> None:
    result = build_erp_sync_plan(
        run_id="run-1",
        uploaded_documents=[{"filename": "invoice.pdf", "path": "invoice.pdf", "document_type": "invoice"}],
        gl_coding_result={"gl_account": "5400-postage", "cost_center": "operations", "allocation": []},
        compliance_result={"compliance_status": "ready", "retention_class": "financial_record"},
        payment_plan={"recommendation": "pay_by_discount_window", "target_payment_date": "2026-07-01"},
    )

    assert result["target_system"] == "cloud_erp"
    assert result["sync_status"] == "ready"
    assert result["posting_payload"]["gl_account"] == "5400-postage"
    assert result["single_source_of_truth"] is True

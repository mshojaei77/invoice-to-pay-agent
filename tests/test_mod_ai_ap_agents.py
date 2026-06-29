from app.graph.workflow import build_graph
from app.services.ap_agent_orchestration import build_ap_agent_orchestration
from app.services.ap_visibility import build_realtime_ap_visibility
from app.services.fraud_detection import assess_fraud_controls
from app.services.invoice_capture import build_invoice_capture_plan
from app.services.payment_execution import build_payment_execution_plan
from app.services.vendor_relationship import build_vendor_relationship_plan


def test_invoice_capture_detects_email_portal_and_edi_channels() -> None:
    result = build_invoice_capture_plan(
        uploaded_documents=[
            {"path": "email_supplier_portal_edi_invoice.pdf", "document_type": "invoice"},
        ],
        parser_route=[{"parser": "liteparse", "reason": "fast_default"}],
        parser_warnings=[],
    )

    assert result["capture_status"] == "ready"
    assert set(result["detected_channels"]) == {"email", "supplier_portal", "edi", "manual_upload"}
    assert result["coverage"]["physical_mail"] == "planned"


def test_fraud_detection_blocks_duplicate_and_payment_instruction_change() -> None:
    result = assess_fraud_controls(
        uploaded_documents=[{"path": "urgent_payment_bank_change_duplicate.pdf"}],
        duplicate_result={"duplicate_status": "confirmed_duplicate"},
        match_result={"mismatch_reasons": []},
        business_rule_errors=[],
        risk_level="high",
    )

    assert result["fraud_status"] == "blocked"
    assert {signal["signal"] for signal in result["signals"]} == {
        "duplicate_invoice",
        "payment_instruction_change",
    }


def test_payment_execution_waits_for_fraud_clearance_and_final_approval() -> None:
    fraud_blocked = build_payment_execution_plan(
        payment_plan={"payment_status": "scheduled", "target_payment_date": "2026-07-01"},
        approval_route={"route": "auto_post"},
        fraud_result={"fraud_status": "blocked"},
        ledger_visibility_plan={"vendor_line_blocked_for_payment": False},
        erp_sync_plan={"target_system": "netsuite"},
    )
    approval_blocked = build_payment_execution_plan(
        payment_plan={"payment_status": "scheduled", "target_payment_date": "2026-07-01"},
        approval_route={"route": "finance_review"},
        fraud_result={"fraud_status": "monitored"},
        ledger_visibility_plan={"vendor_line_blocked_for_payment": True},
        erp_sync_plan={"target_system": "netsuite"},
    )

    assert fraud_blocked["payment_execution_status"] == "blocked_for_fraud_review"
    assert approval_blocked["payment_execution_status"] == "blocked_until_final_approval"


def test_vendor_relationship_and_visibility_surface_cash_flow_risk() -> None:
    payment_execution = {"payment_execution_status": "blocked_until_exception_resolved", "payment_run_ready": False}
    vendor = build_vendor_relationship_plan(
        exception_result={"exception_status": "open"},
        payment_plan={"payment_status": "blocked"},
        payment_execution_plan=payment_execution,
    )
    visibility = build_realtime_ap_visibility(
        uploaded_documents=[{"document_type": "invoice"}],
        exception_result={"exception_count": 2},
        payment_plan={"payment_status": "blocked"},
        payment_execution_plan=payment_execution,
        spend_intelligence={"opportunity_count": 1},
    )

    assert vendor["vendor_relationship_status"] == "at_risk"
    assert vendor["late_payment_risk"] is True
    assert visibility["cash_flow_visibility"] == "blocked"
    assert visibility["invoice_volume_capacity"]["scale_without_headcount_signal"] == "exception_staffing_required"


def test_agent_orchestration_tracks_end_to_end_handoffs() -> None:
    result = build_ap_agent_orchestration(
        invoice_capture_plan={"capture_status": "ready"},
        gl_coding_result={"coding_status": "suggested", "confidence": 0.97},
        match_result={"match_status": "matched"},
        fraud_result={"fraud_status": "monitored"},
        approval_route={"route": "auto_post"},
        payment_execution_plan={"payment_execution_status": "ready_for_payment_run"},
    )

    assert result["agent_orchestration_status"] == "running"
    assert [agent["agent"] for agent in result["agents"]] == [
        "capture_agent",
        "coding_agent",
        "matching_agent",
        "fraud_agent",
        "approval_agent",
        "payment_agent",
    ]


def test_graph_includes_mod_ai_agent_outputs() -> None:
    graph = build_graph()
    result = graph.invoke(
        {
            "run_id": "mod-ai-agent-test",
            "uploaded_documents": [
                {"path": "samples/email_supplier_portal_invoice_007_aws_europe_vat.pdf", "document_type": "invoice"},
                {"path": "samples/purchase_order_001_polychemtex.pdf", "document_type": "purchase_order"},
                {"path": "samples/delivery_note_003_en_sample.pdf", "document_type": "delivery_note"},
            ],
        },
        config={"configurable": {"thread_id": "mod-ai-agent-test"}},
    )

    assert "invoice_capture_plan" in result
    assert "fraud_result" in result
    assert "payment_execution_plan" in result
    assert "vendor_relationship_plan" in result
    assert "realtime_ap_visibility" in result
    assert "ap_agent_orchestration" in result
    assert "email" in result["invoice_capture_plan"]["detected_channels"]

from app.graph.workflow import build_graph
from app.services.ledger_visibility import build_ledger_visibility_plan
from app.services.line_approvals import build_line_approval_plan
from app.services.netsuite_readiness import build_netsuite_ap_readiness
from app.services.po_lifecycle import build_po_lifecycle_plan


def test_line_approval_routes_by_gl_cost_center_and_supports_line_edits() -> None:
    result = build_line_approval_plan(
        uploaded_documents=[{"path": "samples/netsuite_large_lines_excel_invoice.xlsx"}],
        gl_coding_result={"gl_account": "1600-fixed-assets", "cost_center": "operations"},
        approval_route={"route": "finance_review"},
    )

    assert result["line_approval_status"] == "ready"
    assert result["routing_basis"] == "gl_account_cost_center_location"
    assert result["supports_multiple_same_level_approvers"] is True
    assert result["excel_import_recommended"] is True
    assert result["edit_policy"]["sync_edits_to_erp_draft"] is True
    assert result["approver_chain"][-1]["role"] == "finance_controller"


def test_ledger_visibility_blocks_vendor_line_until_final_approval() -> None:
    result = build_ledger_visibility_plan(
        approval_route={"route": "buyer_receiving_review"},
        payment_plan={"payment_status": "blocked"},
        erp_sync_plan={"sync_status": "ready", "target_system": "netsuite"},
        line_approval_plan={
            "supports_line_edits_before_final_approval": True,
            "edit_policy": {"editable_fields": ["gl_account", "cost_center"]},
        },
    )

    assert result["visible_in_ledger_before_final_approval"] is True
    assert result["vendor_line_blocked_for_payment"] is True
    assert result["paid_status_archive_sync"]["source"] == "netsuite"
    assert result["line_edit_sync"]["enabled"] is True


def test_po_lifecycle_supports_asset_po_creation_approval_and_matching() -> None:
    result = build_po_lifecycle_plan(
        uploaded_documents=[
            {"document_type": "invoice", "path": "invoice.pdf"},
            {"document_type": "purchase_order", "path": "asset_po.pdf"},
            {"document_type": "delivery_note", "path": "delivery_note.pdf"},
        ],
        match_result={"match_status": "matched", "mismatch_reasons": []},
        approval_route={"route": "auto_post"},
    )

    assert result["supports_po_creation"] is True
    assert result["supports_po_approval"] is True
    assert result["purchase_type"] == "asset_purchase"
    assert result["matching_mode"] == "three_way_match"


def test_netsuite_readiness_flags_global_non_english_due_diligence() -> None:
    line_plan = build_line_approval_plan(
        uploaded_documents=[{"path": "samples/invoice_006_chinese_netsuite.xlsx"}],
        gl_coding_result={"gl_account": "6200-cloud-services", "cost_center": "engineering"},
        approval_route={"route": "auto_post"},
    )
    ledger_plan = build_ledger_visibility_plan(
        approval_route={"route": "auto_post"},
        payment_plan={"payment_status": "scheduled"},
        erp_sync_plan={"sync_status": "ready", "target_system": "netsuite"},
        line_approval_plan=line_plan,
    )
    po_plan = build_po_lifecycle_plan(
        uploaded_documents=[{"document_type": "invoice"}, {"document_type": "purchase_order"}],
        match_result={"match_status": "matched"},
        approval_route={"route": "auto_post"},
    )

    result = build_netsuite_ap_readiness(
        uploaded_documents=[{"path": "samples/invoice_006_chinese_netsuite.xlsx"}],
        parsed_documents=[{"text": "Chinese VAT invoice"}],
        accounting_platform_profile={"selected_platform": "netsuite"},
        multi_company_result={"multi_company_supported": True},
        line_approval_plan=line_plan,
        ledger_visibility_plan=ledger_plan,
        po_lifecycle_plan=po_plan,
    )

    requirements = {item["requirement"]: item["status"] for item in result["requirements"]}
    assert result["netsuite_profile_status"] == "native_or_partner_ready"
    assert result["global_vendor_profile"] is True
    assert result["non_english_invoice_signal"] is True
    assert requirements["non_english_ocr"] == "review_with_real_vendor_samples"
    assert "Validate payment holds" in result["recommended_due_diligence"][2]


def test_graph_includes_netsuite_ap_control_outputs() -> None:
    graph = build_graph()
    result = graph.invoke(
        {
            "run_id": "netsuite-readiness-test",
            "uploaded_documents": [
                {
                    "path": "samples/invoice_007_aws_europe_vat_netsuite.xlsx",
                    "document_type": "invoice",
                },
                {
                    "path": "samples/purchase_order_001_polychemtex.pdf",
                    "document_type": "purchase_order",
                },
                {
                    "path": "samples/delivery_note_003_en_sample.pdf",
                    "document_type": "delivery_note",
                },
            ],
        },
        config={"configurable": {"thread_id": "netsuite-readiness-test"}},
    )

    assert result["accounting_platform_profile"]["selected_platform"] == "netsuite"
    assert result["line_approval_plan"]["supports_multiple_same_level_approvers"] is True
    assert result["ledger_visibility_plan"]["paid_status_archive_sync"]["enabled"] is True
    assert result["po_lifecycle_plan"]["supports_po_creation"] is True
    assert result["netsuite_ap_readiness"]["invoice_volume_profile"] == "mid_market_300_400_invoices_per_month"

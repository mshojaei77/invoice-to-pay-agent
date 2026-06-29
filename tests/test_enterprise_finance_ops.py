from app.graph.workflow import build_graph
from app.services.accruals import build_accrual_close_plan
from app.services.billing_revenue import build_billing_revenue_plan
from app.services.einvoicing import build_einvoicing_compliance_plan
from app.services.order_to_cash import build_order_to_cash_plan
from app.services.spend_intelligence import build_spend_intelligence


def test_o2c_plan_escalates_exception_follow_up() -> None:
    result = build_order_to_cash_plan(
        exception_result={"categories": ["matching"]},
        payment_plan={"payment_status": "blocked"},
        erp_sync_plan={"sync_status": "ready"},
        accounting_platform_profile={"selected_platform": "netsuite"},
    )

    assert result["service_mode"] == "exception_follow_up"
    assert result["managed_work_items"][1]["status"] == "draft_outreach"


def test_accrual_plan_prepares_audit_ready_close_output() -> None:
    result = build_accrual_close_plan(
        uploaded_documents=[
            {"document_type": "invoice", "filename": "invoice.pdf"},
            {"document_type": "delivery_note", "filename": "receipt.pdf"},
        ],
        exception_result={"exception_status": "clear"},
        gl_coding_result={"coding_status": "suggested", "gl_account": "5400", "cost_center": "ops"},
        payment_plan={"cashflow_bucket": "next_10_days"},
    )

    assert result["accrual_status"] == "ready"
    assert result["audit_ready"] is True
    assert result["journal_output"]["gl_account"] == "5400"


def test_spend_intelligence_flags_contract_leakage() -> None:
    result = build_spend_intelligence(
        uploaded_documents=[{"path": "samples/invoice_007_aws_europe_vat.pdf"}],
        gl_coding_result={"gl_account": "6200-software", "cost_center": "engineering"},
        exception_result={"categories": ["pricing"]},
        match_result={"mismatch_reasons": ["total_mismatch"]},
    )

    assert result["spend_status"] == "opportunities_found"
    assert {item["type"] for item in result["opportunities"]} == {
        "contract_leakage",
        "software_spend_consolidation",
    }


def test_billing_and_einvoice_plans_surface_revenue_and_tax_controls() -> None:
    billing = build_billing_revenue_plan(
        uploaded_documents=[{"path": "samples/rate_card_001_tarievenfolder_en.pdf"}],
        erp_sync_plan={"sync_status": "ready"},
        payment_plan={"payment_status": "scheduled", "cashflow_bucket": "scheduled"},
        compliance_result={"retention_class": "financial_record"},
    )
    einvoice = build_einvoicing_compliance_plan(
        uploaded_documents=[{"path": "samples/invoice_007_aws_europe_vat.pdf"}],
        compliance_result={"compliance_status": "ready"},
        accounting_platform_profile={"selected_platform": "sap"},
        industry_policy_result={"vat_policy": "standard_vat_code_required"},
    )

    assert billing["contract_signal_detected"] is True
    assert billing["billing_status"] == "ready"
    assert einvoice["einvoicing_status"] == "review_required"
    assert einvoice["target_platform"] == "sap"


def test_graph_includes_enterprise_finance_ops_outputs() -> None:
    graph = build_graph()
    result = graph.invoke(
        {
            "run_id": "enterprise-finops-test",
            "uploaded_documents": [
                {
                    "path": "samples/invoice_007_aws_europe_vat.pdf",
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
        config={"configurable": {"thread_id": "enterprise-finops-test"}},
    )

    assert "order_to_cash_plan" in result
    assert "accrual_close_plan" in result
    assert "spend_intelligence" in result
    assert "billing_revenue_plan" in result
    assert "einvoicing_compliance_plan" in result
    agent_modes = {agent["agent"]: agent["mode"] for agent in result["finance_agent_plan"]["agents"]}
    assert agent_modes["debtor_management_agent"] == result["order_to_cash_plan"]["service_mode"]

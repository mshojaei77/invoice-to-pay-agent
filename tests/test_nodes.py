from unittest.mock import patch

from app.graph.nodes import (
    approval_routing,
    approval_gate,
    ai_cost_tracking,
    ai_governance_check,
    classify_ap_exceptions,
    compliance_check,
    duplicate_check,
    erp_sync_planning,
    kpi_snapshot,
    automation_readiness_check,
    match_invoice_po_delivery,
    normalize_ap_documents,
    parse_documents_fast_with_liteparse,
    payment_planning,
    post_to_erp_mock,
    reconcile_parser_outputs,
    risk_score,
    route_to_docling_if_needed,
    save_uploads,
    suggest_gl_coding_node,
    validate_business_rules,
    validate_schema,
    write_audit_log,
)
from app.graph.state import APGraphState


def make_state(**overrides: dict) -> APGraphState:
    base: APGraphState = {
        "run_id": "test-run-001",
        "uploaded_documents": [{"path": "invoice.pdf", "document_type": "invoice"}],
    }
    base.update(overrides)  # type: ignore[typeddict-item]
    return base


class TestSaveUploads:
    def test_returns_audit_event(self) -> None:
        result = save_uploads(make_state())
        assert "audit_events" in result
        assert len(result["audit_events"]) == 1
        assert result["audit_events"][0]["node"] == "save_uploads"


class TestParseDocuments:
    def test_returns_parsed_docs(self) -> None:
        parsed = {
            "parser_name": "liteparse",
            "parser_version": "unknown",
            "document_type": "invoice",
            "text": "Invoice INV-001",
            "markdown": "Invoice INV-001",
            "tables": [],
            "blocks": [],
            "images": [],
            "page_count": 1,
            "confidence": 0.8,
            "warnings": [],
            "raw_artifact_path": "data/processed/parser_raw/liteparse-test.json",
        }

        with patch("app.graph.nodes.LiteParseAdapter") as adapter:
            adapter.return_value.parser_name = "liteparse"
            adapter.return_value.parse.return_value.model_dump.return_value = parsed
            result = parse_documents_fast_with_liteparse(make_state())

        assert result["parsed_documents"] == [parsed]
        assert result["parser_route"] == [{"parser": "liteparse", "reason": "fast_default"}]

    def test_returns_warning_when_parser_fails(self) -> None:
        with patch("app.graph.nodes.LiteParseAdapter") as adapter:
            adapter.return_value.parser_name = "liteparse"
            adapter.return_value.parse.side_effect = RuntimeError("parse failed")
            result = parse_documents_fast_with_liteparse(make_state())

        assert result["parsed_documents"] == []
        assert result["parser_warnings"][0]["error"] == "parse failed"

    def test_uses_cli_selected_docling_parser(self) -> None:
        parsed = {
            "parser_name": "docling",
            "parser_version": "unknown",
            "document_type": "invoice",
            "text": "# Invoice",
            "markdown": "# Invoice",
            "tables": [],
            "blocks": [],
            "images": [],
            "page_count": 1,
            "confidence": 0.85,
            "warnings": [],
            "raw_artifact_path": "data/processed/parser_raw/docling-test.json",
        }

        with patch("app.graph.nodes.DoclingAdapter") as adapter:
            adapter.return_value.parser_name = "docling"
            adapter.return_value.parse.return_value.model_dump.return_value = parsed
            result = parse_documents_fast_with_liteparse(
                make_state(parser_name="docling")
            )

        assert result["parsed_documents"] == [parsed]
        assert result["parser_route"] == [{"parser": "docling", "reason": "cli_selected"}]
        adapter.assert_called_once_with()


class TestNormalize:
    def test_returns_none_for_all(self) -> None:
        result = normalize_ap_documents(make_state())
        assert result["invoice"] is None
        assert result["purchase_order"] is None
        assert result["delivery_note"] is None


class TestValidateSchema:
    def test_returns_empty_errors(self) -> None:
        result = validate_schema(make_state())
        assert result["validation_errors"] == []


class TestValidateBusinessRules:
    def test_returns_empty_errors_when_supporting_docs_exist(self) -> None:
        result = validate_business_rules(
            make_state(
                uploaded_documents=[
                    {"path": "invoice.pdf", "document_type": "invoice"},
                    {"path": "po.pdf", "document_type": "purchase_order"},
                    {"path": "delivery.pdf", "document_type": "delivery_note"},
                ]
            )
        )
        assert result["business_rule_errors"] == []

    def test_flags_missing_po_and_delivery_note(self) -> None:
        result = validate_business_rules(make_state())
        codes = {error["code"] for error in result["business_rule_errors"]}
        assert codes == {"missing_po", "missing_delivery_note"}


class TestRouteToDocling:
    def test_passes_warnings_through(self) -> None:
        state = make_state(parser_warnings=["handwriting"])
        result = route_to_docling_if_needed(state)
        assert result["parser_warnings"] == ["handwriting"]

    def test_empty_warnings(self) -> None:
        result = route_to_docling_if_needed(make_state())
        assert result["parser_warnings"] == []


class TestReconcile:
    def test_returns_empty(self) -> None:
        result = reconcile_parser_outputs(make_state())
        assert result == {}


class TestDuplicateCheck:
    def test_returns_clear_by_default(self) -> None:
        result = duplicate_check(make_state())
        assert result["duplicate_result"]["duplicate_status"] == "clear"

    def test_flags_duplicate_fixture(self) -> None:
        result = duplicate_check(
            make_state(uploaded_documents=[{"path": "duplicate_001.pdf", "document_type": "invoice"}])
        )
        assert result["duplicate_result"]["duplicate_status"] == "confirmed_duplicate"


class TestMatchInvoicePoDelivery:
    def test_returns_matched_when_supporting_docs_exist(self) -> None:
        result = match_invoice_po_delivery(
            make_state(
                uploaded_documents=[
                    {"path": "invoice.pdf", "document_type": "invoice"},
                    {"path": "po.pdf", "document_type": "purchase_order"},
                    {"path": "delivery.pdf", "document_type": "delivery_note"},
                ]
            )
        )
        assert result["match_result"]["match_status"] == "matched"

    def test_flags_missing_purchase_order(self) -> None:
        result = match_invoice_po_delivery(make_state())
        assert result["match_result"]["match_status"] == "mismatch"
        assert "missing_purchase_order" in result["match_result"]["mismatch_reasons"]


class TestRiskScore:
    def test_returns_low_by_default(self) -> None:
        result = risk_score(
            make_state(
                validation_errors=[],
                business_rule_errors=[],
                duplicate_result={"duplicate_status": "clear", "duplicate_candidates": []},
                match_result={"match_status": "matched", "mismatch_reasons": []},
            )
        )
        assert result["risk_level"] == "low"
        assert result["risk_score"] == 0.0
        assert result["requires_human_approval"] is False

    def test_returns_medium_for_missing_po(self) -> None:
        result = risk_score(
            make_state(
                validation_errors=[],
                business_rule_errors=[{"code": "missing_po"}],
                duplicate_result={"duplicate_status": "clear", "duplicate_candidates": []},
                match_result={"match_status": "mismatch", "mismatch_reasons": ["missing_purchase_order"]},
            )
        )
        assert result["risk_level"] == "medium"
        assert result["requires_human_approval"] is True


class TestClassifyApExceptions:
    def test_returns_exception_result(self) -> None:
        result = classify_ap_exceptions(
            make_state(
                business_rule_errors=[{"code": "missing_po", "severity": "medium"}],
                duplicate_result={"duplicate_status": "clear"},
                match_result={"match_status": "mismatch", "mismatch_reasons": ["missing_purchase_order"]},
            )
        )
        assert result["exception_result"]["exception_status"] == "open"
        assert "matching" in result["exception_result"]["categories"]


class TestSuggestGlCoding:
    def test_returns_coding_result(self) -> None:
        result = suggest_gl_coding_node(
            make_state(uploaded_documents=[{"path": "invoice_007_aws_europe_vat.pdf", "document_type": "invoice"}])
        )
        assert result["gl_coding_result"]["coding_status"] == "suggested"


class TestApprovalRouting:
    def test_returns_approval_route(self) -> None:
        result = approval_routing(
            make_state(
                risk_level="medium",
                risk_score=40.0,
                exception_result={"categories": ["pricing"], "exceptions": [{"code": "match:total_mismatch"}]},
                gl_coding_result={"coding_status": "suggested"},
            )
        )
        assert result["approval_route"]["route"] == "buyer_receiving_review"


class TestComplianceCheck:
    def test_returns_compliance_result(self) -> None:
        result = compliance_check(
            make_state(
                uploaded_documents=[
                    {"path": "invoice.pdf", "document_type": "invoice"},
                    {"path": "po.pdf", "document_type": "purchase_order"},
                    {"path": "delivery.pdf", "document_type": "delivery_note"},
                ],
                exception_result={"exceptions": []},
                approval_route={"approver_role": "system"},
            )
        )
        assert result["compliance_result"]["compliance_status"] == "ready"


class TestPaymentPlanning:
    def test_returns_payment_plan(self) -> None:
        result = payment_planning(
            make_state(
                risk_level="low",
                approval_route={"route": "auto_post"},
                exception_result={"exception_status": "clear"},
            )
        )
        assert result["payment_plan"]["payment_status"] == "scheduled"


class TestErpSyncPlanning:
    def test_returns_sync_plan(self) -> None:
        result = erp_sync_planning(
            make_state(
                gl_coding_result={"gl_account": "5400-postage", "cost_center": "operations", "allocation": []},
                compliance_result={"compliance_status": "ready", "retention_class": "financial_record"},
                payment_plan={"recommendation": "pay_by_discount_window", "target_payment_date": "2026-07-01"},
            )
        )
        assert result["erp_sync_plan"]["sync_status"] == "ready"


class TestAiGovernanceCheck:
    def test_returns_ai_governance_result(self) -> None:
        result = ai_governance_check(
            make_state(
                parser_route=[{"parser": "liteparse"}],
                parsed_documents=[{"confidence": 0.9}],
                requires_human_approval=False,
                approval_route={"route": "auto_post"},
            )
        )
        assert result["ai_governance_result"]["governance_status"] == "ready"


class TestAutomationReadinessCheck:
    def test_returns_automation_readiness(self) -> None:
        result = automation_readiness_check(
            make_state(
                risk_level="low",
                exception_result={"exception_count": 0},
                compliance_result={"compliance_status": "ready"},
                ai_governance_result={"governance_status": "ready"},
            )
        )
        assert result["automation_readiness"]["recommended_autonomy_level"] == "auto_process_with_audit"


class TestAiCostTracking:
    def test_returns_cost_snapshot(self) -> None:
        result = ai_cost_tracking(
            make_state(
                parsed_documents=[{"text": "abcd" * 20}],
                parser_route=[{"parser": "liteparse"}],
            )
        )
        assert result["ai_cost_snapshot"]["estimated_input_tokens"] == 20


class TestApprovalGate:
    def test_auto_approves_when_not_required(self) -> None:
        result = approval_gate(make_state(requires_human_approval=False))
        assert result["approval"]["status"] == "auto_approved"
        assert result["approval"]["approved_by"] == "system"

    def test_interrupts_when_approval_required(self) -> None:
        state = make_state(
            requires_human_approval=True,
            risk_level="medium",
            risk_score=30.0,
            risk_reasons=["missing_po"],
            match_result={"match_status": "mismatch", "mismatch_reasons": ["total_mismatch"]},
            duplicate_result={"duplicate_status": "clear"},
        )

        with (
            patch("app.graph.nodes.write_audit_event"),
            patch("app.graph.nodes.interrupt", return_value={"status": "approved"}) as mock,
        ):
            result = approval_gate(state)

        mock.assert_called_once()
        assert result["approval"]["status"] == "approved"

    def test_writes_audit_when_approval_required(self) -> None:
        state = make_state(
            requires_human_approval=True,
            risk_level="medium",
            risk_score=30.0,
            risk_reasons=["missing_po"],
            business_rule_errors=[{"code": "missing_po"}],
            match_result={"match_status": "mismatch", "mismatch_reasons": ["missing_purchase_order"]},
            duplicate_result={"duplicate_status": "clear"},
        )

        with (
            patch("app.graph.nodes.write_audit_event") as write_audit_event,
            patch("app.graph.nodes.interrupt", return_value={"status": "approved"}),
        ):
            approval_gate(state)

        write_audit_event.assert_called_once()
        assert write_audit_event.call_args.kwargs["node_name"] == "approval_gate"
        assert write_audit_event.call_args.kwargs["output_summary"]["status"] == "requires_approval"


class TestPostToErpMock:
    def test_posts_when_auto_approved(self) -> None:
        state = make_state(
            approval={"status": "auto_approved", "approved_by": "system"},
        )
        result = post_to_erp_mock(state)
        assert result["erp_result"]["status"] == "posted"

    def test_rejects_when_human_rejected(self) -> None:
        state = make_state(
            approval={"status": "rejected", "approved_by": "human"},
        )
        result = post_to_erp_mock(state)
        assert result["erp_result"]["status"] == "not_posted"

    def test_no_approval_posts_by_default(self) -> None:
        result = post_to_erp_mock(make_state())
        assert result["erp_result"]["status"] == "posted"


class TestWriteAuditLog:
    def test_writes_audit_event(self) -> None:
        event = {"event_id": "event-1", "status": "written"}

        with patch("app.graph.nodes.write_audit_event", return_value=event) as write_audit_event:
            result = write_audit_log(
                make_state(
                    risk_level="low",
                    risk_score=0.0,
                    requires_human_approval=False,
                    approval={"status": "auto_approved"},
                    erp_result={"status": "posted"},
                )
            )

        write_audit_event.assert_called_once()
        assert write_audit_event.call_args.kwargs["node_name"] == "write_audit_log"
        assert result == {"audit_events": [event]}


class TestKpiSnapshot:
    def test_returns_kpi_snapshot(self) -> None:
        result = kpi_snapshot(
            make_state(
                requires_human_approval=False,
                exception_result={"exception_count": 0},
                approval_route={"route": "auto_post"},
                erp_result={"status": "posted"},
                payment_plan={"payment_status": "scheduled", "cashflow_bucket": "next_10_days"},
            )
        )
        assert result["kpi_snapshot"]["touchless_rate"] == 1.0

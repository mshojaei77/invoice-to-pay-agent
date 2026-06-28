from unittest.mock import patch

from app.graph.nodes import (
    approval_gate,
    duplicate_check,
    match_invoice_po_delivery,
    normalize_ap_documents,
    parse_documents_fast_with_liteparse,
    post_to_erp_mock,
    reconcile_parser_outputs,
    risk_score,
    route_to_mineru_if_needed,
    save_uploads,
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
    def test_returns_empty_parsed_docs(self) -> None:
        result = parse_documents_fast_with_liteparse(make_state())
        assert result["parsed_documents"] == []
        assert result["parser_route"] == [{"parser": "liteparse", "reason": "fast_default"}]


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


class TestRouteToMineru:
    def test_passes_warnings_through(self) -> None:
        state = make_state(parser_warnings=["handwriting"])
        result = route_to_mineru_if_needed(state)
        assert result["parser_warnings"] == ["handwriting"]

    def test_empty_warnings(self) -> None:
        result = route_to_mineru_if_needed(make_state())
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

        with patch("app.graph.nodes.interrupt", return_value={"status": "approved"}) as mock:
            result = approval_gate(state)

        mock.assert_called_once()
        assert result["approval"]["status"] == "approved"


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
    def test_returns_empty(self) -> None:
        result = write_audit_log(make_state())
        assert result == {}

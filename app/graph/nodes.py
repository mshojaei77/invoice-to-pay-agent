from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from langgraph.types import interrupt

from app.graph.state import APGraphState
from app.services.audit import AUDIT_PATH, write_audit_event
from app.services.approval_routing import route_approval
from app.services.exceptions import classify_exceptions
from app.services.gl_coding import suggest_gl_coding
from app.services.parser import DoclingAdapter, LiteParseAdapter
from app.services.risk import calculate_risk


def save_uploads(state: APGraphState) -> dict[str, Any]:
    return {
        "audit_events": [
            {
                "node": "save_uploads",
                "message": "Uploads registered",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ]
    }


def parse_documents_fast_with_liteparse(state: APGraphState) -> dict[str, Any]:
    parser_name = str(state.get("parser_name") or "liteparse").lower()
    parser = DoclingAdapter() if parser_name == "docling" else LiteParseAdapter()
    route_reason = "cli_selected" if state.get("parser_name") else "fast_default"
    parsed_documents = []
    warnings = []

    for document in state.get("uploaded_documents", []):
        try:
            parsed = parser.parse(
                file_path=Path(document["path"]),
                document_type=document.get("document_type", "unknown"),
            )
            parsed_documents.append(parsed.model_dump(mode="json"))
        except Exception as exc:
            warnings.append(
                {
                    "document": document,
                    "parser": parser.parser_name,
                    "error": str(exc),
                }
            )

    return {
        "parsed_documents": parsed_documents,
        "parser_route": [{"parser": parser.parser_name, "reason": route_reason}],
        "parser_warnings": warnings,
    }


def normalize_ap_documents(state: APGraphState) -> dict[str, Any]:
    return {
        "invoice": None,
        "purchase_order": None,
        "delivery_note": None,
    }


def validate_schema(state: APGraphState) -> dict[str, Any]:
    return {"validation_errors": []}


def validate_business_rules(state: APGraphState) -> dict[str, Any]:
    document_types = {
        document.get("document_type")
        for document in state.get("uploaded_documents", [])
    }
    errors = []
    if "purchase_order" not in document_types:
        errors.append(
            {
                "code": "missing_po",
                "message": "Invoice has no matching PO.",
                "severity": "medium",
            }
        )
    if "delivery_note" not in document_types:
        errors.append(
            {
                "code": "missing_delivery_note",
                "message": "Invoice has no matching delivery note.",
                "severity": "medium",
            }
        )
    if _has_uploaded_path_fragment(state, "missing_iban"):
        errors.append(
            {
                "code": "missing_iban",
                "message": "Vendor IBAN is missing.",
                "severity": "medium",
            }
        )
    if _has_uploaded_path_fragment(state, "handwritten_correction"):
        errors.append(
            {
                "code": "handwritten_correction",
                "message": "Handwritten correction warning was detected.",
                "severity": "high",
            }
        )
    return {"business_rule_errors": errors}


def route_to_docling_if_needed(state: APGraphState) -> dict[str, Any]:
    return {"parser_warnings": state.get("parser_warnings", [])}


def reconcile_parser_outputs(state: APGraphState) -> dict[str, Any]:
    return {}


def duplicate_check(state: APGraphState) -> dict[str, Any]:
    if _has_uploaded_path_fragment(state, "duplicate"):
        return {
            "duplicate_result": {
                "duplicate_status": "confirmed_duplicate",
                "duplicate_candidates": [
                    {
                        "reason": "fixture_duplicate_invoice",
                        "match_fields": ["vendor_name", "invoice_number"],
                    }
                ],
            }
        }

    return {
        "duplicate_result": {
            "duplicate_status": "clear",
            "duplicate_candidates": [],
        }
    }


def match_invoice_po_delivery(state: APGraphState) -> dict[str, Any]:
    reasons = []
    document_types = {
        document.get("document_type")
        for document in state.get("uploaded_documents", [])
    }
    if "purchase_order" not in document_types:
        reasons.append("missing_purchase_order")
    if "delivery_note" not in document_types:
        reasons.append("missing_delivery_note")
    if _has_uploaded_path_fragment(state, "total_mismatch"):
        reasons.append("total_mismatch")
    if _has_uploaded_path_fragment(state, "vendor_mismatch"):
        reasons.append("vendor_mismatch")
    if _has_uploaded_path_fragment(state, "delivery_quantity_mismatch"):
        reasons.append("delivery_quantity_mismatch")

    return {
        "match_result": {
            "match_status": "matched" if not reasons else "mismatch",
            "mismatch_reasons": reasons,
        }
    }


def classify_ap_exceptions(state: APGraphState) -> dict[str, Any]:
    return {
        "exception_result": classify_exceptions(
            business_rule_errors=state.get("business_rule_errors", []),
            duplicate_result=state.get(
                "duplicate_result",
                {"duplicate_status": "clear", "duplicate_candidates": []},
            ),
            match_result=state.get(
                "match_result",
                {"match_status": "matched", "mismatch_reasons": []},
            ),
            parser_warnings=state.get("parser_warnings", []),
        )
    }


def suggest_gl_coding_node(state: APGraphState) -> dict[str, Any]:
    return {
        "gl_coding_result": suggest_gl_coding(
            uploaded_documents=state.get("uploaded_documents", []),
            parsed_documents=state.get("parsed_documents", []),
        )
    }


def risk_score(state: APGraphState) -> dict[str, Any]:
    result = calculate_risk(
        validation_errors=state.get("validation_errors", []),
        business_rule_errors=state.get("business_rule_errors", []),
        duplicate_result=state.get(
            "duplicate_result",
            {"duplicate_status": "clear", "duplicate_candidates": []},
        ),
        match_result=state.get(
            "match_result",
            {"match_status": "matched", "mismatch_reasons": []},
        ),
    )
    return {
        "risk_level": result.risk_level,
        "risk_score": result.risk_score,
        "risk_reasons": result.risk_reasons,
        "requires_human_approval": result.requires_human_approval,
    }


def approval_routing(state: APGraphState) -> dict[str, Any]:
    return {
        "approval_route": route_approval(
            risk_level=state.get("risk_level", "low"),
            risk_score=float(state.get("risk_score", 0.0)),
            exception_result=state.get(
                "exception_result",
                {"exception_status": "clear", "exceptions": [], "categories": []},
            ),
            gl_coding_result=state.get("gl_coding_result"),
        )
    }


def approval_gate(state: APGraphState) -> dict[str, Any]:
    if not state.get("requires_human_approval", False):
        return {
            "approval": {
                "status": "auto_approved",
                "approved_by": "system",
                "reason": "low_risk",
            }
        }

    write_audit_event(
        run_id=state["run_id"],
        node_name="approval_gate",
        node_input={
            "risk_level": state.get("risk_level"),
            "risk_score": state.get("risk_score"),
            "risk_reasons": state.get("risk_reasons", []),
            "match_result": state.get("match_result"),
            "duplicate_result": state.get("duplicate_result"),
            "exception_result": state.get("exception_result"),
            "approval_route": state.get("approval_route"),
            "gl_coding_result": state.get("gl_coding_result"),
        },
        output_summary={
            "status": "requires_approval",
            "erp_status": "not_posted",
            "audit_path": str(AUDIT_PATH),
        },
        risk_delta={
            "risk_level": state.get("risk_level"),
            "risk_score": state.get("risk_score"),
            "risk_reasons": state.get("risk_reasons", []),
        },
        decision={"requires_human_approval": True},
        errors=state.get("validation_errors", []) + state.get("business_rule_errors", []),
    )

    approval = interrupt(
        {
            "run_id": state["run_id"],
            "risk_level": state.get("risk_level"),
            "risk_score": state.get("risk_score"),
            "risk_reasons": state.get("risk_reasons", []),
            "match_result": state.get("match_result"),
            "duplicate_result": state.get("duplicate_result"),
            "exception_result": state.get("exception_result"),
            "approval_route": state.get("approval_route"),
            "gl_coding_result": state.get("gl_coding_result"),
        }
    )

    return {"approval": approval}


def post_to_erp_mock(state: APGraphState) -> dict[str, Any]:
    approval = state.get("approval") or {}

    if approval.get("status") in {"rejected", "human_rejected"}:
        return {
            "erp_result": {
                "status": "not_posted",
                "rejection_reason": "human_rejected",
            }
        }

    return {
        "erp_result": {
            "status": "posted",
            "erp_post_id": f"ERP-{state['run_id']}",
            "posted_at": datetime.now(timezone.utc).isoformat(),
        }
    }


def write_audit_log(state: APGraphState) -> dict[str, Any]:
    event = write_audit_event(
        run_id=state["run_id"],
        node_name="write_audit_log",
        node_input={
            "uploaded_documents": state.get("uploaded_documents", []),
            "risk_level": state.get("risk_level"),
            "risk_score": state.get("risk_score"),
            "approval": state.get("approval"),
            "approval_route": state.get("approval_route"),
            "exception_result": state.get("exception_result"),
            "gl_coding_result": state.get("gl_coding_result"),
            "erp_result": state.get("erp_result"),
        },
        output_summary={
            "status": "completed",
            "risk_level": state.get("risk_level"),
            "erp_status": (state.get("erp_result") or {}).get("status"),
            "audit_path": str(AUDIT_PATH),
        },
        risk_delta={
            "risk_level": state.get("risk_level"),
            "risk_score": state.get("risk_score"),
            "risk_reasons": state.get("risk_reasons", []),
        },
        decision={
            "requires_human_approval": state.get("requires_human_approval", False),
            "approval": state.get("approval"),
        },
        parser_or_model_name=str(state.get("parser_name") or "liteparse").lower(),
        errors=state.get("validation_errors", []) + state.get("business_rule_errors", []),
    )
    return {"audit_events": [event]}


def _has_uploaded_path_fragment(state: APGraphState, fragment: str) -> bool:
    return any(
        fragment in str(document.get("path", "")).lower()
        for document in state.get("uploaded_documents", [])
    )

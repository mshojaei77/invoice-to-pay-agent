from __future__ import annotations

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from app.graph.nodes import (
    approval_routing,
    approval_gate,
    classify_ap_exceptions,
    compliance_check,
    duplicate_check,
    erp_sync_planning,
    kpi_snapshot,
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


def build_graph():
    builder = StateGraph(APGraphState)

    builder.add_node("save_uploads", save_uploads)
    builder.add_node("parse_documents_fast_with_liteparse", parse_documents_fast_with_liteparse)
    builder.add_node("normalize_ap_documents", normalize_ap_documents)
    builder.add_node("validate_schema", validate_schema)
    builder.add_node("validate_business_rules", validate_business_rules)
    builder.add_node("route_to_docling_if_needed", route_to_docling_if_needed)
    builder.add_node("reconcile_parser_outputs", reconcile_parser_outputs)
    builder.add_node("duplicate_check", duplicate_check)
    builder.add_node("match_invoice_po_delivery", match_invoice_po_delivery)
    builder.add_node("classify_ap_exceptions", classify_ap_exceptions)
    builder.add_node("suggest_gl_coding", suggest_gl_coding_node)
    builder.add_node("risk_score", risk_score)
    builder.add_node("approval_routing", approval_routing)
    builder.add_node("compliance_check", compliance_check)
    builder.add_node("payment_planning", payment_planning)
    builder.add_node("erp_sync_planning", erp_sync_planning)
    builder.add_node("approval_gate", approval_gate)
    builder.add_node("post_to_erp_mock", post_to_erp_mock)
    builder.add_node("kpi_snapshot", kpi_snapshot)
    builder.add_node("write_audit_log", write_audit_log)

    builder.add_edge(START, "save_uploads")
    builder.add_edge("save_uploads", "parse_documents_fast_with_liteparse")
    builder.add_edge("parse_documents_fast_with_liteparse", "normalize_ap_documents")
    builder.add_edge("normalize_ap_documents", "validate_schema")
    builder.add_edge("validate_schema", "validate_business_rules")
    builder.add_edge("validate_business_rules", "route_to_docling_if_needed")
    builder.add_edge("route_to_docling_if_needed", "reconcile_parser_outputs")
    builder.add_edge("reconcile_parser_outputs", "duplicate_check")
    builder.add_edge("duplicate_check", "match_invoice_po_delivery")
    builder.add_edge("match_invoice_po_delivery", "classify_ap_exceptions")
    builder.add_edge("classify_ap_exceptions", "suggest_gl_coding")
    builder.add_edge("suggest_gl_coding", "risk_score")
    builder.add_edge("risk_score", "approval_routing")
    builder.add_edge("approval_routing", "compliance_check")
    builder.add_edge("compliance_check", "payment_planning")
    builder.add_edge("payment_planning", "erp_sync_planning")
    builder.add_edge("erp_sync_planning", "approval_gate")
    builder.add_edge("approval_gate", "post_to_erp_mock")
    builder.add_edge("post_to_erp_mock", "kpi_snapshot")
    builder.add_edge("kpi_snapshot", "write_audit_log")
    builder.add_edge("write_audit_log", END)

    checkpointer = InMemorySaver()
    return builder.compile(checkpointer=checkpointer)

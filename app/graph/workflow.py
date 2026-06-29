from __future__ import annotations

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from app.graph.nodes import (
    ai_cost_tracking,
    ai_governance_check,
    accounting_platform_profile_node,
    accrual_close_planning,
    approval_routing,
    approval_gate,
    automation_readiness_check,
    billing_revenue_planning,
    classify_ap_exceptions,
    compliance_check,
    duplicate_check,
    einvoicing_compliance_planning,
    erp_sync_planning,
    finance_agent_planning,
    industry_policy_check,
    kpi_snapshot,
    ledger_visibility_planning,
    line_approval_planning,
    match_invoice_po_delivery,
    multi_company_controls,
    netsuite_ap_readiness_check,
    normalize_ap_documents,
    parse_documents_fast_with_liteparse,
    payment_planning,
    po_lifecycle_planning,
    post_to_erp_mock,
    reconcile_parser_outputs,
    risk_score,
    route_to_docling_if_needed,
    save_uploads,
    suggest_gl_coding_node,
    order_to_cash_planning,
    spend_intelligence_analysis,
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
    builder.add_node("accounting_platform_profile", accounting_platform_profile_node)
    builder.add_node("multi_company_controls", multi_company_controls)
    builder.add_node("industry_policy_check", industry_policy_check)
    builder.add_node("risk_score", risk_score)
    builder.add_node("approval_routing", approval_routing)
    builder.add_node("line_approval_planning", line_approval_planning)
    builder.add_node("compliance_check", compliance_check)
    builder.add_node("payment_planning", payment_planning)
    builder.add_node("po_lifecycle_planning", po_lifecycle_planning)
    builder.add_node("erp_sync_planning", erp_sync_planning)
    builder.add_node("ledger_visibility_planning", ledger_visibility_planning)
    builder.add_node("netsuite_ap_readiness_check", netsuite_ap_readiness_check)
    builder.add_node("finance_agent_planning", finance_agent_planning)
    builder.add_node("order_to_cash_planning", order_to_cash_planning)
    builder.add_node("accrual_close_planning", accrual_close_planning)
    builder.add_node("spend_intelligence_analysis", spend_intelligence_analysis)
    builder.add_node("billing_revenue_planning", billing_revenue_planning)
    builder.add_node("einvoicing_compliance_planning", einvoicing_compliance_planning)
    builder.add_node("ai_governance_check", ai_governance_check)
    builder.add_node("automation_readiness_check", automation_readiness_check)
    builder.add_node("ai_cost_tracking", ai_cost_tracking)
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
    builder.add_edge("suggest_gl_coding", "accounting_platform_profile")
    builder.add_edge("accounting_platform_profile", "multi_company_controls")
    builder.add_edge("multi_company_controls", "industry_policy_check")
    builder.add_edge("industry_policy_check", "risk_score")
    builder.add_edge("risk_score", "approval_routing")
    builder.add_edge("approval_routing", "line_approval_planning")
    builder.add_edge("line_approval_planning", "compliance_check")
    builder.add_edge("compliance_check", "payment_planning")
    builder.add_edge("payment_planning", "po_lifecycle_planning")
    builder.add_edge("po_lifecycle_planning", "erp_sync_planning")
    builder.add_edge("erp_sync_planning", "ledger_visibility_planning")
    builder.add_edge("ledger_visibility_planning", "netsuite_ap_readiness_check")
    builder.add_edge("netsuite_ap_readiness_check", "order_to_cash_planning")
    builder.add_edge("order_to_cash_planning", "accrual_close_planning")
    builder.add_edge("accrual_close_planning", "spend_intelligence_analysis")
    builder.add_edge("spend_intelligence_analysis", "billing_revenue_planning")
    builder.add_edge("billing_revenue_planning", "einvoicing_compliance_planning")
    builder.add_edge("einvoicing_compliance_planning", "finance_agent_planning")
    builder.add_edge("finance_agent_planning", "ai_governance_check")
    builder.add_edge("ai_governance_check", "automation_readiness_check")
    builder.add_edge("automation_readiness_check", "ai_cost_tracking")
    builder.add_edge("ai_cost_tracking", "approval_gate")
    builder.add_edge("approval_gate", "post_to_erp_mock")
    builder.add_edge("post_to_erp_mock", "kpi_snapshot")
    builder.add_edge("kpi_snapshot", "write_audit_log")
    builder.add_edge("write_audit_log", END)

    checkpointer = InMemorySaver()
    return builder.compile(checkpointer=checkpointer)

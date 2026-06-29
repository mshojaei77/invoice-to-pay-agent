from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.graph.workflow import build_graph


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--invoice", required=True)
    parser.add_argument("--po")
    parser.add_argument("--delivery-note")
    parser.add_argument(
        "--parser",
        default="liteparse",
        type=_normalize_parser_name,
        choices=("liteparse", "docling"),
        help="Document parser to use: liteparse or docling.",
    )
    parser.add_argument(
        "--output-md",
        default=None,
        help="Markdown report path. Defaults to data/processed/reports/<run_id>.md.",
    )
    args = parser.parse_args()

    run_id = str(uuid4())
    graph = build_graph()

    uploaded_documents = [{"path": args.invoice, "document_type": "invoice"}]
    if args.po:
        uploaded_documents.append({"path": args.po, "document_type": "purchase_order"})
    if args.delivery_note:
        uploaded_documents.append({"path": args.delivery_note, "document_type": "delivery_note"})

    result = graph.invoke(
        {
            "run_id": run_id,
            "uploaded_documents": uploaded_documents,
            "parser_name": args.parser,
        },
        config={"configurable": {"thread_id": run_id}},
    )

    markdown_report = write_markdown_report(
        result=result,
        run_id=run_id,
        output_path=Path(args.output_md) if args.output_md else None,
    )

    print(f"run_id={run_id}")
    if "__interrupt__" in result:
        print("final_status=requires_approval")
        print("erp_status=not_posted")
        print_parser_outputs(result)
        print("audit_log=data/processed/audit.jsonl")
        print(f"markdown_report={markdown_report}")
        return

    print("final_status=completed")
    print(f"risk_level={result.get('risk_level')}")
    print(f"erp_status={(result.get('erp_result') or {}).get('status')}")
    print_parser_outputs(result)
    print("audit_log=data/processed/audit.jsonl")
    print(f"markdown_report={markdown_report}")


def print_parser_outputs(result: dict) -> None:
    parsed_documents = result.get("parsed_documents") or []
    parser_warnings = result.get("parser_warnings") or []

    if not parsed_documents:
        print("parsed_documents=0")
    for index, document in enumerate(parsed_documents, start=1):
        preview = " ".join((document.get("text") or "").split())[:180]
        print(f"parsed_document_{index}_type={document.get('document_type')}")
        print(f"parsed_document_{index}_pages={document.get('page_count')}")
        print(f"parsed_document_{index}_raw={document.get('raw_artifact_path')}")
        print(f"parsed_document_{index}_preview={preview}")

    if parser_warnings:
        print(f"parser_warnings={len(parser_warnings)}")
        for warning in parser_warnings:
            print(f"parser_warning={warning}")


def write_markdown_report(
    result: dict[str, Any],
    run_id: str,
    output_path: Path | None = None,
) -> Path:
    report_path = output_path or Path("data/processed/reports") / f"{run_id}.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(build_markdown_report(result, run_id), encoding="utf-8")
    return report_path


def build_markdown_report(result: dict[str, Any], run_id: str) -> str:
    final_status = "requires_approval" if "__interrupt__" in result else "completed"
    erp_status = "not_posted" if "__interrupt__" in result else (result.get("erp_result") or {}).get("status")
    parser_routes = result.get("parser_route") or []
    parsed_documents = result.get("parsed_documents") or []
    parser_warnings = result.get("parser_warnings") or []

    lines = [
        "# Invoice-to-Pay Demo Run",
        "",
        "## Summary",
        "",
        f"- Run ID: `{run_id}`",
        f"- Final status: `{final_status}`",
        f"- Risk level: `{result.get('risk_level')}`",
        f"- ERP status: `{erp_status}`",
        f"- Audit log: `data/processed/audit.jsonl`",
        "",
        "## Parser Route",
        "",
    ]

    if parser_routes:
        for route in parser_routes:
            lines.append(f"- Parser: `{route.get('parser')}`; reason: `{route.get('reason')}`")
    else:
        lines.append("- Parser route was not recorded.")

    lines.extend(["", "## Parsed Documents", ""])
    if not parsed_documents:
        lines.append("No parsed documents were returned.")
    for index, document in enumerate(parsed_documents, start=1):
        preview = " ".join((document.get("text") or "").split())[:300]
        lines.extend(
            [
                f"### Document {index}: {document.get('document_type')}",
                "",
                f"- Parser: `{document.get('parser_name')}`",
                f"- Pages: `{document.get('page_count')}`",
                f"- Confidence: `{document.get('confidence')}`",
                f"- Raw artifact: `{document.get('raw_artifact_path')}`",
                "",
                "#### Preview",
                "",
                preview or "_No text preview available._",
                "",
            ]
        )

    if parser_warnings:
        lines.extend(["## Parser Warnings", ""])
        for warning in parser_warnings:
            lines.append(f"- `{warning}`")
        lines.append("")

    lines.extend(["## Invoice Capture", ""])
    capture = result.get("invoice_capture_plan") or {}
    if capture:
        lines.append(f"- Status: `{capture.get('capture_status')}`")
        lines.append(f"- Detected channels: `{', '.join(capture.get('detected_channels', []))}`")
        lines.append(f"- Warnings count: `{capture.get('warnings_count')}`")
        coverage = capture.get("coverage") or {}
        lines.append(f"- Email capture: `{coverage.get('email')}`")
        lines.append(f"- Supplier portal capture: `{coverage.get('supplier_portals')}`")
        lines.append(f"- EDI capture: `{coverage.get('edi')}`")
        lines.append(f"- Physical mail capture: `{coverage.get('physical_mail')}`")
    else:
        lines.append("- Invoice capture planning was not calculated.")
    lines.append("")

    lines.extend(["## Risk Reasons", ""])
    risk_reasons = result.get("risk_reasons") or []
    if risk_reasons:
        lines.extend(f"- `{reason}`" for reason in risk_reasons)
    else:
        lines.append("No risk reasons were recorded.")
    lines.append("")

    lines.extend(["## Exception Queue", ""])
    exception_result = result.get("exception_result") or {}
    exceptions = exception_result.get("exceptions") or []
    lines.append(f"- Status: `{exception_result.get('exception_status', 'unknown')}`")
    lines.append(f"- Highest severity: `{exception_result.get('highest_severity', 'unknown')}`")
    if exceptions:
        for item in exceptions:
            lines.append(
                f"- `{item.get('code')}` ({item.get('category')}, {item.get('severity')}): {item.get('recommended_action')}"
            )
    else:
        lines.append("- No open exceptions.")
    lines.append("")

    lines.extend(["## Fraud Controls", ""])
    fraud = result.get("fraud_result") or {}
    if fraud:
        lines.append(f"- Status: `{fraud.get('fraud_status')}`")
        lines.append(f"- Signal count: `{fraud.get('signal_count')}`")
        for signal in fraud.get("signals", []):
            lines.append(f"- `{signal.get('signal')}`: `{signal.get('severity')}`")
        for control in fraud.get("controls", []):
            lines.append(f"- `{control.get('control')}`: `{control.get('status')}`")
    else:
        lines.append("- Fraud controls were not calculated.")
    lines.append("")

    lines.extend(["## Approval Route", ""])
    approval_route = result.get("approval_route") or {}
    if approval_route:
        lines.append(f"- Route: `{approval_route.get('route')}`")
        lines.append(f"- Approver role: `{approval_route.get('approver_role')}`")
        lines.append(f"- SLA hours: `{approval_route.get('sla_hours')}`")
        lines.append(f"- Reason: `{approval_route.get('reason')}`")
    else:
        lines.append("- Approval route was not calculated.")
    lines.append("")

    lines.extend(["## GL Coding", ""])
    gl_coding = result.get("gl_coding_result") or {}
    if gl_coding:
        lines.append(f"- Status: `{gl_coding.get('coding_status')}`")
        lines.append(f"- GL account: `{gl_coding.get('gl_account')}`")
        lines.append(f"- Cost center: `{gl_coding.get('cost_center')}`")
        lines.append(f"- Confidence: `{gl_coding.get('confidence')}`")
        lines.append(f"- Reason: `{gl_coding.get('reason')}`")
    else:
        lines.append("- GL coding was not calculated.")
    lines.append("")

    lines.extend(["## Compliance Controls", ""])
    compliance = result.get("compliance_result") or {}
    if compliance:
        lines.append(f"- Status: `{compliance.get('compliance_status')}`")
        lines.append(f"- Retention class: `{compliance.get('retention_class')}`")
        lines.append(f"- Sensitive data: `{', '.join(compliance.get('sensitive_data_classes', []))}`")
        for control in compliance.get("controls", []):
            lines.append(f"- `{control.get('control')}`: `{control.get('status')}`")
    else:
        lines.append("- Compliance controls were not calculated.")
    lines.append("")

    lines.extend(["## Payment Plan", ""])
    payment_plan = result.get("payment_plan") or {}
    if payment_plan:
        lines.append(f"- Status: `{payment_plan.get('payment_status')}`")
        lines.append(f"- Recommendation: `{payment_plan.get('recommendation')}`")
        lines.append(f"- Target payment date: `{payment_plan.get('target_payment_date')}`")
        lines.append(f"- Cashflow bucket: `{payment_plan.get('cashflow_bucket')}`")
    else:
        lines.append("- Payment plan was not calculated.")
    lines.append("")

    lines.extend(["## Payment Execution", ""])
    payment_execution = result.get("payment_execution_plan") or {}
    if payment_execution:
        lines.append(f"- Status: `{payment_execution.get('payment_execution_status')}`")
        lines.append(f"- One-click approval enabled: `{payment_execution.get('one_click_approval_enabled')}`")
        lines.append(f"- Payment run ready: `{payment_execution.get('payment_run_ready')}`")
        lines.append(f"- Sync target: `{payment_execution.get('sync_target')}`")
        lines.append(f"- Target payment date: `{payment_execution.get('target_payment_date')}`")
    else:
        lines.append("- Payment execution planning was not calculated.")
    lines.append("")

    lines.extend(["## Vendor Relationship", ""])
    vendor_relationship = result.get("vendor_relationship_plan") or {}
    if vendor_relationship:
        lines.append(f"- Status: `{vendor_relationship.get('vendor_relationship_status')}`")
        lines.append(f"- Next action: `{vendor_relationship.get('next_vendor_action')}`")
        lines.append(f"- Late payment risk: `{vendor_relationship.get('late_payment_risk')}`")
        reply_agent = vendor_relationship.get("supplier_reply_agent") or {}
        lines.append(f"- Supplier reply agent: `{reply_agent.get('enabled')}`")
    else:
        lines.append("- Vendor relationship planning was not calculated.")
    lines.append("")

    lines.extend(["## ERP Sync Plan", ""])
    erp_sync = result.get("erp_sync_plan") or {}
    if erp_sync:
        lines.append(f"- Target system: `{erp_sync.get('target_system')}`")
        lines.append(f"- Sync status: `{erp_sync.get('sync_status')}`")
        lines.append(f"- Integration mode: `{erp_sync.get('integration_mode')}`")
        lines.append(f"- Single source of truth: `{erp_sync.get('single_source_of_truth')}`")
    else:
        lines.append("- ERP sync plan was not calculated.")
    lines.append("")

    lines.extend(["## Accounting Platform", ""])
    platform = result.get("accounting_platform_profile") or {}
    if platform:
        lines.append(f"- Selected platform: `{platform.get('selected_platform')}`")
        lines.append(f"- Connector style: `{platform.get('connector_style')}`")
        lines.append(f"- Target market: `{platform.get('target_market')}`")
        lines.append(f"- Supported platforms: `{', '.join(platform.get('supported_platforms', []))}`")
    else:
        lines.append("- Accounting platform profile was not calculated.")
    lines.append("")

    lines.extend(["## Line-Level Approval Plan", ""])
    line_approval = result.get("line_approval_plan") or {}
    if line_approval:
        lines.append(f"- Status: `{line_approval.get('line_approval_status')}`")
        lines.append(f"- Routing basis: `{line_approval.get('routing_basis')}`")
        lines.append(f"- Multiple same-level approvers: `{line_approval.get('supports_multiple_same_level_approvers')}`")
        lines.append(f"- Manual line split supported: `{line_approval.get('manual_line_split_supported')}`")
        lines.append(f"- Excel import recommended: `{line_approval.get('excel_import_recommended')}`")
        dimensions = line_approval.get("dimensions") or {}
        lines.append(f"- GL account: `{dimensions.get('gl_account')}`")
        lines.append(f"- Cost center: `{dimensions.get('cost_center')}`")
        for approver in line_approval.get("approver_chain", []):
            lines.append(f"- Step `{approver.get('step')}`: `{approver.get('role')}` (`{approver.get('status')}`)")
    else:
        lines.append("- Line-level approval planning was not calculated.")
    lines.append("")

    lines.extend(["## PO Lifecycle", ""])
    po_lifecycle = result.get("po_lifecycle_plan") or {}
    if po_lifecycle:
        lines.append(f"- Status: `{po_lifecycle.get('po_lifecycle_status')}`")
        lines.append(f"- PO creation supported: `{po_lifecycle.get('supports_po_creation')}`")
        lines.append(f"- PO approval supported: `{po_lifecycle.get('supports_po_approval')}`")
        lines.append(f"- Purchase type: `{po_lifecycle.get('purchase_type')}`")
        lines.append(f"- Matching mode: `{po_lifecycle.get('matching_mode')}`")
        lines.append(f"- Inbound shipment review: `{po_lifecycle.get('inbound_shipment_review')}`")
        lines.append(f"- Next action: `{po_lifecycle.get('next_action')}`")
    else:
        lines.append("- PO lifecycle planning was not calculated.")
    lines.append("")

    lines.extend(["## Ledger And Archive Visibility", ""])
    ledger = result.get("ledger_visibility_plan") or {}
    if ledger:
        lines.append(f"- Status: `{ledger.get('ledger_visibility_status')}`")
        lines.append(f"- Visible before final approval: `{ledger.get('visible_in_ledger_before_final_approval')}`")
        lines.append(f"- Vendor line blocked for payment: `{ledger.get('vendor_line_blocked_for_payment')}`")
        lines.append(f"- Payment release condition: `{ledger.get('payment_release_condition')}`")
        archive = ledger.get("paid_status_archive_sync") or {}
        lines.append(f"- Paid-status archive sync: `{archive.get('enabled')}` from `{archive.get('source')}`")
        edit_sync = ledger.get("line_edit_sync") or {}
        lines.append(f"- Line edit sync target: `{edit_sync.get('sync_target')}`")
    else:
        lines.append("- Ledger and archive visibility planning was not calculated.")
    lines.append("")

    lines.extend(["## NetSuite AP Readiness", ""])
    netsuite = result.get("netsuite_ap_readiness") or {}
    if netsuite:
        lines.append(f"- Status: `{netsuite.get('netsuite_profile_status')}`")
        lines.append(f"- Selected platform: `{netsuite.get('selected_platform')}`")
        lines.append(f"- Invoice volume profile: `{netsuite.get('invoice_volume_profile')}`")
        lines.append(f"- Global vendor profile: `{netsuite.get('global_vendor_profile')}`")
        lines.append(f"- Non-English invoice signal: `{netsuite.get('non_english_invoice_signal')}`")
        lines.append(f"- Readiness score: `{netsuite.get('readiness_score')}`")
        for requirement in netsuite.get("requirements", []):
            lines.append(f"- `{requirement.get('requirement')}`: `{requirement.get('status')}`")
    else:
        lines.append("- NetSuite AP readiness was not calculated.")
    lines.append("")

    lines.extend(["## Multi-Company Controls", ""])
    multi_company = result.get("multi_company_result") or {}
    if multi_company:
        lines.append(f"- Entity code: `{multi_company.get('entity_code')}`")
        lines.append(f"- Control status: `{multi_company.get('control_status')}`")
        lines.append(f"- Accountant collaboration: `{multi_company.get('accountant_collaboration_enabled')}`")
        lines.append(f"- Intercompany review required: `{multi_company.get('intercompany_review_required')}`")
    else:
        lines.append("- Multi-company controls were not calculated.")
    lines.append("")

    lines.extend(["## Industry Policy", ""])
    industry_policy = result.get("industry_policy_result") or {}
    if industry_policy:
        lines.append(f"- Industry: `{industry_policy.get('industry')}`")
        lines.append(f"- Status: `{industry_policy.get('policy_status')}`")
        lines.append(f"- VAT policy: `{industry_policy.get('vat_policy')}`")
        lines.append(f"- Valuation policy: `{industry_policy.get('valuation_policy')}`")
    else:
        lines.append("- Industry policy was not calculated.")
    lines.append("")

    lines.extend(["## Finance Agent Plan", ""])
    agent_plan = result.get("finance_agent_plan") or {}
    if agent_plan:
        lines.append(f"- Status: `{agent_plan.get('agent_plan_status')}`")
        lines.append(f"- Platform: `{agent_plan.get('selected_platform')}`")
        for agent in agent_plan.get("agents", []):
            lines.append(f"- `{agent.get('agent')}`: `{agent.get('mode')}`")
    else:
        lines.append("- Finance agent plan was not calculated.")
    lines.append("")

    lines.extend(["## Order-to-Cash Plan", ""])
    o2c = result.get("order_to_cash_plan") or {}
    if o2c:
        lines.append(f"- Status: `{o2c.get('o2c_status')}`")
        lines.append(f"- Service mode: `{o2c.get('service_mode')}`")
        lines.append(f"- SLA hours: `{o2c.get('sla_hours')}`")
        lines.append(f"- Target system: `{o2c.get('target_system')}`")
        for item in o2c.get("managed_work_items", []):
            lines.append(f"- `{item.get('queue')}`: `{item.get('status')}` via `{item.get('owner_agent')}`")
    else:
        lines.append("- Order-to-cash planning was not calculated.")
    lines.append("")

    lines.extend(["## Accrual Close Plan", ""])
    accruals = result.get("accrual_close_plan") or {}
    if accruals:
        lines.append(f"- Status: `{accruals.get('accrual_status')}`")
        lines.append(f"- Close action: `{accruals.get('close_action')}`")
        lines.append(f"- Confidence: `{accruals.get('confidence')}`")
        lines.append(f"- Audit ready: `{accruals.get('audit_ready')}`")
        journal = accruals.get("journal_output") or {}
        lines.append(f"- Journal GL account: `{journal.get('gl_account')}`")
        lines.append(f"- Journal cost center: `{journal.get('cost_center')}`")
    else:
        lines.append("- Accrual close planning was not calculated.")
    lines.append("")

    lines.extend(["## Spend Intelligence", ""])
    spend = result.get("spend_intelligence") or {}
    if spend:
        lines.append(f"- Status: `{spend.get('spend_status')}`")
        lines.append(f"- Category: `{spend.get('category')}`")
        lines.append(f"- Opportunity count: `{spend.get('opportunity_count')}`")
        for item in spend.get("opportunities", []):
            lines.append(f"- `{item.get('type')}` ({item.get('severity')}): {item.get('recommendation')}")
    else:
        lines.append("- Spend intelligence was not calculated.")
    lines.append("")

    lines.extend(["## Billing Revenue Plan", ""])
    billing = result.get("billing_revenue_plan") or {}
    if billing:
        lines.append(f"- Status: `{billing.get('billing_status')}`")
        lines.append(f"- Action: `{billing.get('billing_action')}`")
        lines.append(f"- Contract signal: `{billing.get('contract_signal_detected')}`")
        analytics = billing.get("analytics") or {}
        lines.append(f"- Cashflow bucket: `{analytics.get('cashflow_bucket')}`")
    else:
        lines.append("- Billing revenue planning was not calculated.")
    lines.append("")

    lines.extend(["## E-Invoicing Compliance", ""])
    einvoicing = result.get("einvoicing_compliance_plan") or {}
    if einvoicing:
        lines.append(f"- Status: `{einvoicing.get('einvoicing_status')}`")
        lines.append(f"- Jurisdiction signal: `{einvoicing.get('jurisdiction_signal')}`")
        lines.append(f"- Target platform: `{einvoicing.get('target_platform')}`")
        lines.append(f"- VAT policy: `{einvoicing.get('vat_policy')}`")
        for requirement in einvoicing.get("requirements", []):
            lines.append(f"- `{requirement.get('requirement')}`: `{requirement.get('status')}`")
    else:
        lines.append("- E-invoicing compliance planning was not calculated.")
    lines.append("")

    lines.extend(["## KPI Snapshot", ""])
    kpis = result.get("kpi_snapshot") or {}
    if kpis:
        lines.append(f"- Touchless rate: `{kpis.get('touchless_rate')}`")
        lines.append(f"- Exception rate: `{kpis.get('exception_rate')}`")
        lines.append(f"- On-time payment candidate: `{kpis.get('on_time_payment_candidate')}`")
        lines.append(f"- Cycle status: `{kpis.get('cycle_status')}`")
    else:
        lines.append("- KPI snapshot was not calculated.")
    lines.append("")

    lines.extend(["## Real-Time AP Visibility", ""])
    visibility = result.get("realtime_ap_visibility") or {}
    if visibility:
        volume = visibility.get("invoice_volume_capacity") or {}
        lines.append(f"- Status: `{visibility.get('visibility_status')}`")
        lines.append(f"- Cash flow visibility: `{visibility.get('cash_flow_visibility')}`")
        lines.append(f"- Current batch invoice count: `{volume.get('current_batch_invoice_count')}`")
        lines.append(f"- Scale signal: `{volume.get('scale_without_headcount_signal')}`")
        lines.append(f"- Open exception count: `{visibility.get('open_exception_count')}`")
        lines.append(f"- Payment run ready: `{visibility.get('payment_run_ready')}`")
    else:
        lines.append("- Real-time AP visibility was not calculated.")
    lines.append("")

    lines.extend(["## AP Agent Orchestration", ""])
    orchestration = result.get("ap_agent_orchestration") or {}
    if orchestration:
        lines.append(f"- Status: `{orchestration.get('agent_orchestration_status')}`")
        lines.append(f"- Autonomy level: `{orchestration.get('autonomy_level')}`")
        lines.append(f"- Blocked agents: `{', '.join(orchestration.get('blocked_agents', [])) or 'none'}`")
        for agent in orchestration.get("agents", []):
            lines.append(f"- `{agent.get('agent')}`: `{agent.get('status')}` -> `{agent.get('handoff')}`")
    else:
        lines.append("- AP agent orchestration was not calculated.")
    lines.append("")

    lines.extend(["## AI Governance", ""])
    governance = result.get("ai_governance_result") or {}
    if governance:
        lines.append(f"- Status: `{governance.get('governance_status')}`")
        lines.append(f"- Adoption stage: `{governance.get('adoption_stage')}`")
        lines.append(f"- Shadow AI policy: `{governance.get('shadow_ai_policy')}`")
        lines.append(f"- Unapproved tools: `{', '.join(governance.get('unapproved_tools', [])) or 'none'}`")
        for guardrail in governance.get("guardrails", []):
            lines.append(f"- `{guardrail.get('control')}`: `{guardrail.get('status')}`")
    else:
        lines.append("- AI governance was not calculated.")
    lines.append("")

    lines.extend(["## Automation Readiness", ""])
    readiness = result.get("automation_readiness") or {}
    if readiness:
        process_profile = readiness.get("process_profile") or {}
        lines.append(f"- Recommended autonomy: `{readiness.get('recommended_autonomy_level')}`")
        lines.append(f"- Human oversight required: `{readiness.get('requires_human_oversight')}`")
        lines.append(f"- Error recoverability: `{process_profile.get('error_recoverability')}`")
        lines.append(f"- Blocked actions: `{', '.join(readiness.get('blocked_actions', [])) or 'none'}`")
    else:
        lines.append("- Automation readiness was not calculated.")
    lines.append("")

    lines.extend(["## AI Cost Snapshot", ""])
    ai_cost = result.get("ai_cost_snapshot") or {}
    if ai_cost:
        lines.append(f"- Budget category: `{ai_cost.get('budget_category')}`")
        lines.append(f"- Estimated input tokens: `{ai_cost.get('estimated_input_tokens')}`")
        lines.append(f"- Estimated cost USD: `{ai_cost.get('estimated_cost_usd')}`")
        lines.append(f"- Cost policy: `{ai_cost.get('cost_policy')}`")
    else:
        lines.append("- AI cost snapshot was not calculated.")
    lines.append("")

    return "\n".join(lines)


def _normalize_parser_name(value: str) -> str:
    normalized = value.strip().lower().replace("_", "")
    if normalized == "docling":
        return "docling"
    if normalized == "liteparse":
        return "liteparse"
    raise argparse.ArgumentTypeError("parser must be liteparse or docling")


if __name__ == "__main__":
    main()

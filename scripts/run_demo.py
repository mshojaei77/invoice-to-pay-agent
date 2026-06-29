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

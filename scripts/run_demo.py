from __future__ import annotations

import argparse
import sys
from pathlib import Path
from uuid import uuid4
from typing import Any

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
        choices=("liteparse", "mineru"),
        help="Document parser to use: liteparse or mineru.",
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

    return "\n".join(lines)


def _normalize_parser_name(value: str) -> str:
    normalized = value.strip().lower().replace("_", "")
    if normalized == "mineru":
        return "mineru"
    if normalized == "liteparse":
        return "liteparse"
    raise argparse.ArgumentTypeError("parser must be liteparse or mineru")


if __name__ == "__main__":
    main()

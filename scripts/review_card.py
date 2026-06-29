from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.graph.workflow import build_graph
from scripts.run_demo import _normalize_parser_name


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Print a compact AP review card for one invoice-to-pay graph run."
    )
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
    args = parser.parse_args()

    run_id = str(uuid4())
    uploaded_documents = [{"path": args.invoice, "document_type": "invoice"}]
    if args.po:
        uploaded_documents.append({"path": args.po, "document_type": "purchase_order"})
    if args.delivery_note:
        uploaded_documents.append({"path": args.delivery_note, "document_type": "delivery_note"})

    result = build_graph().invoke(
        {
            "run_id": run_id,
            "uploaded_documents": uploaded_documents,
            "parser_name": args.parser,
        },
        config={"configurable": {"thread_id": run_id}},
    )

    print(build_review_card(result, run_id))


def build_review_card(result: dict[str, Any], run_id: str) -> str:
    exception_result = result.get("exception_result") or {}
    approval_route = result.get("approval_route") or {}
    payment_plan = result.get("payment_plan") or {}
    erp_result = result.get("erp_result") or {}
    match_result = result.get("match_result") or {}
    fraud_result = result.get("fraud_result") or {}

    final_status = "requires_approval" if "__interrupt__" in result else "completed"
    erp_status = "not_posted" if "__interrupt__" in result else erp_result.get("status", "not_posted")
    exception_count = len(exception_result.get("exceptions") or [])

    rows = [
        ("Run", run_id),
        ("Final status", final_status),
        ("Risk", result.get("risk_level", "unknown")),
        ("Match status", match_result.get("match_status", "unknown")),
        ("Mismatch reasons", ", ".join(match_result.get("mismatch_reasons") or []) or "none"),
        ("Duplicate/fraud signals", str(fraud_result.get("signal_count", 0))),
        ("Open exceptions", str(exception_count)),
        ("Approval route", approval_route.get("route", "unknown")),
        ("Approver role", approval_route.get("approver_role", "unknown")),
        ("Payment status", payment_plan.get("payment_status", "unknown")),
        ("ERP status", erp_status),
        ("Audit log", "data/processed/audit.jsonl"),
    ]

    width = max(len(label) for label, _ in rows)
    lines = ["Invoice-to-Pay Review Card", ""]
    lines.extend(f"{label.ljust(width)} : {value}" for label, value in rows)
    return "\n".join(lines)


if __name__ == "__main__":
    main()

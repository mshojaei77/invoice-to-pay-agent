from __future__ import annotations

import argparse
import sys
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.graph.workflow import build_graph


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--invoice", required=True)
    parser.add_argument("--po")
    parser.add_argument("--delivery-note")
    args = parser.parse_args()

    run_id = str(uuid4())
    graph = build_graph()

    uploaded_documents = [{"path": args.invoice, "document_type": "invoice"}]
    if args.po:
        uploaded_documents.append({"path": args.po, "document_type": "purchase_order"})
    if args.delivery_note:
        uploaded_documents.append({"path": args.delivery_note, "document_type": "delivery_note"})

    result = graph.invoke(
        {"run_id": run_id, "uploaded_documents": uploaded_documents},
        config={"configurable": {"thread_id": run_id}},
    )

    print(f"run_id={run_id}")
    if "__interrupt__" in result:
        print("final_status=requires_approval")
        print("erp_status=not_posted")
        print("audit_log=data/processed/audit.jsonl")
        return

    print("final_status=completed")
    print(f"risk_level={result.get('risk_level')}")
    print(f"erp_status={(result.get('erp_result') or {}).get('status')}")
    print("audit_log=data/processed/audit.jsonl")


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from langgraph.types import Command

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.graph.workflow import build_graph


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()

    graph = build_graph()

    result = graph.invoke(
        Command(resume={"status": "rejected", "approved_by": "cli_approver"}),
        config={"configurable": {"thread_id": args.run_id}},
    )

    print(f"run_id={args.run_id}")
    print(f"approval_status={result.get('approval', {}).get('status')}")
    print(f"erp_status={(result.get('erp_result') or {}).get('status')}")


if __name__ == "__main__":
    main()

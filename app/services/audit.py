from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


AUDIT_PATH = Path("data/processed/audit.jsonl")


def stable_hash(payload: Any) -> str:
    data = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def make_event_id(run_id: str, node_name: str, input_hash: str) -> str:
    raw = f"{run_id}:{node_name}:{input_hash}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:24]


def existing_event_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()

    ids = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            ids.add(json.loads(line)["event_id"])
    return ids


def write_audit_event(
    run_id: str,
    node_name: str,
    node_input: dict,
    output_summary: dict,
    risk_delta: dict | None = None,
    decision: dict | None = None,
    parser_or_model_name: str | None = None,
    errors: list[dict] | None = None,
    path: Path = AUDIT_PATH,
) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)

    input_hash = stable_hash(node_input)
    event_id = make_event_id(run_id, node_name, input_hash)

    if event_id in existing_event_ids(path):
        return {"event_id": event_id, "status": "already_written"}

    event = {
        "event_id": event_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "node_name": node_name,
        "input_hash": input_hash,
        "output_summary": output_summary,
        "risk_delta": risk_delta or {},
        "decision": decision or {},
        "parser_or_model_name": parser_or_model_name,
        "errors": errors or [],
    }

    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, default=str) + "\n")

    return event

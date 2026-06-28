import json
from pathlib import Path

from app.services.audit import existing_event_ids, make_event_id, stable_hash, write_audit_event


def test_stable_hash_is_deterministic() -> None:
    h1 = stable_hash({"a": 1, "b": 2})
    h2 = stable_hash({"b": 2, "a": 1})
    assert h1 == h2


def test_stable_hash_changes_with_data() -> None:
    h1 = stable_hash({"a": 1})
    h2 = stable_hash({"a": 2})
    assert h1 != h2


def test_make_event_id_is_24_chars() -> None:
    event_id = make_event_id("run-1", "parse", stable_hash({"test": True}))
    assert len(event_id) == 24


def test_write_audit_event_writes_to_file(tmp_path: Path) -> None:
    path = tmp_path / "audit.jsonl"
    event = write_audit_event(
        run_id="run-001",
        node_name="parse_documents",
        node_input={"file": "invoice.pdf"},
        output_summary={"status": "ok"},
        path=path,
    )

    assert event["run_id"] == "run-001"
    assert event["node_name"] == "parse_documents"
    assert path.exists()

    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1

    written = json.loads(lines[0])
    assert written["event_id"] == event["event_id"]


def test_duplicate_event_id_returns_already_written(tmp_path: Path) -> None:
    path = tmp_path / "audit.jsonl"
    first = write_audit_event(
        run_id="run-001",
        node_name="parse",
        node_input={"file": "test.pdf"},
        output_summary={"status": "ok"},
        path=path,
    )

    second = write_audit_event(
        run_id="run-001",
        node_name="parse",
        node_input={"file": "test.pdf"},
        output_summary={"status": "ok"},
        path=path,
    )

    assert second["status"] == "already_written"
    assert second["event_id"] == first["event_id"]


def test_different_input_produces_new_event(tmp_path: Path) -> None:
    path = tmp_path / "audit.jsonl"
    write_audit_event(
        run_id="run-001",
        node_name="parse",
        node_input={"file": "test.pdf"},
        output_summary={"status": "ok"},
        path=path,
    )

    second = write_audit_event(
        run_id="run-001",
        node_name="parse",
        node_input={"file": "other.pdf"},
        output_summary={"status": "ok"},
        path=path,
    )

    assert second["event_id"] != ""
    assert len(path.read_text(encoding="utf-8").splitlines()) == 2


def test_existing_event_ids_returns_set(tmp_path: Path) -> None:
    path = tmp_path / "audit.jsonl"
    write_audit_event(
        run_id="run-001",
        node_name="parse",
        node_input={"file": "a.pdf"},
        output_summary={"status": "ok"},
        path=path,
    )
    write_audit_event(
        run_id="run-002",
        node_name="parse",
        node_input={"file": "b.pdf"},
        output_summary={"status": "ok"},
        path=path,
    )

    ids = existing_event_ids(path)
    assert len(ids) == 2


def test_audit_event_optional_fields(tmp_path: Path) -> None:
    path = tmp_path / "audit.jsonl"
    event = write_audit_event(
        run_id="run-001",
        node_name="risk_score",
        node_input={},
        output_summary={"risk_level": "high"},
        risk_delta={"score": 85},
        decision={"requires_approval": True},
        parser_or_model_name="liteparse",
        errors=[{"code": "missing_po"}],
        path=path,
    )

    assert event["risk_delta"]["score"] == 85
    assert event["decision"]["requires_approval"] is True
    assert event["parser_or_model_name"] == "liteparse"
    assert len(event["errors"]) == 1

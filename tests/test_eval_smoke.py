import json
from pathlib import Path

EVAL_MANIFEST = Path("samples/eval_manifest.jsonl")
SAMPLES_DIR = Path("samples")


def test_samples_directory_exists() -> None:
    assert SAMPLES_DIR.is_dir()


def test_sample_manifest_file_exists() -> None:
    assert EVAL_MANIFEST.exists()


def test_sample_manifest_is_valid_jsonl() -> None:
    lines = EVAL_MANIFEST.read_text(encoding="utf-8").splitlines()

    assert len(lines) >= 1

    for line in lines:
        record = json.loads(line)
        assert "case_id" in record
        assert "invoice_path" in record
        assert "po_path" in record
        assert "delivery_note_path" in record
        assert "source" in record
        assert "expected_duplicate_status" in record
        assert "expected_match_status" in record
        assert "expected_requires_human_approval" in record
        assert Path(record["invoice_path"]).exists()
        if record["po_path"] is not None:
            assert Path(record["po_path"]).exists()
        if record["delivery_note_path"] is not None:
            assert Path(record["delivery_note_path"]).exists()


def test_sample_manifest_has_real_world_scenarios() -> None:
    records = [json.loads(line) for line in EVAL_MANIFEST.read_text(encoding="utf-8").splitlines()]

    case_ids = [r["case_id"] for r in records]
    assert "invoice_with_po_and_delivery_note" in case_ids
    assert "invoice_missing_po" in case_ids
    assert "handwritten_invoice" in case_ids
    assert "international_invoice" in case_ids
    assert "non_invoice_statement" in case_ids

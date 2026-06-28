import json
from pathlib import Path

EVAL_DIR = Path("data/eval")


def test_eval_directories_exist() -> None:
    assert (EVAL_DIR / "invoices").is_dir()
    assert (EVAL_DIR / "purchase_orders").is_dir()
    assert (EVAL_DIR / "delivery_notes").is_dir()


def test_ground_truth_file_exists() -> None:
    gt_path = EVAL_DIR / "ground_truth.jsonl"
    assert gt_path.exists()


def test_ground_truth_is_valid_jsonl() -> None:
    gt_path = EVAL_DIR / "ground_truth.jsonl"
    lines = gt_path.read_text(encoding="utf-8").splitlines()

    assert len(lines) >= 1

    for line in lines:
        record = json.loads(line)
        assert "case_id" in record
        assert "invoice_path" in record
        assert "expected_invoice_number" in record
        assert "expected_vendor" in record
        assert "expected_total_amount" in record
        assert "expected_duplicate_status" in record
        assert "expected_match_status" in record
        assert "expected_requires_human_approval" in record
        assert Path(record["invoice_path"]).exists()
        if record["po_path"] is not None:
            assert Path(record["po_path"]).exists()
        if record["delivery_note_path"] is not None:
            assert Path(record["delivery_note_path"]).exists()


def test_ground_truth_has_multiple_scenarios() -> None:
    gt_path = EVAL_DIR / "ground_truth.jsonl"
    records = [json.loads(line) for line in gt_path.read_text(encoding="utf-8").splitlines()]

    case_ids = [r["case_id"] for r in records]
    assert "clean_001" in case_ids
    assert "missing_po_001" in case_ids
    assert "duplicate_001" in case_ids
    assert "total_mismatch_001" in case_ids
    assert "vendor_mismatch_001" in case_ids
    assert "handwritten_correction_001" in case_ids
    assert "missing_iban_001" in case_ids
    assert "delivery_quantity_mismatch_001" in case_ids

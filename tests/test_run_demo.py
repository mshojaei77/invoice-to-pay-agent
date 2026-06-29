from pathlib import Path
import subprocess
import sys

import pytest

from scripts.review_card import build_review_card
from scripts.run_demo import build_markdown_report, write_markdown_report, _normalize_parser_name


def test_normalize_parser_name_accepts_docling() -> None:
    assert _normalize_parser_name("Docling") == "docling"
    assert _normalize_parser_name("liteparse") == "liteparse"


def test_normalize_parser_name_rejects_unknown_parser() -> None:
    with pytest.raises(Exception):
        _normalize_parser_name("unknown")


def test_build_markdown_report_includes_run_summary_and_documents() -> None:
    markdown = build_markdown_report(
        {
            "risk_level": "low",
            "erp_result": {"status": "posted"},
            "parser_route": [{"parser": "liteparse", "reason": "cli_selected"}],
            "parsed_documents": [
                {
                    "document_type": "invoice",
                    "parser_name": "liteparse",
                    "page_count": 2,
                    "confidence": 0.8,
                    "raw_artifact_path": "data/processed/parser_raw/liteparse-test.json",
                    "text": "Invoice preview text",
                }
            ],
            "risk_reasons": [],
        },
        "run-123",
    )

    assert "# Invoice-to-Pay Demo Run" in markdown
    assert "- Run ID: `run-123`" in markdown
    assert "- Parser: `liteparse`; reason: `cli_selected`" in markdown
    assert "### Document 1: invoice" in markdown
    assert "Invoice preview text" in markdown


def test_write_markdown_report_creates_parent_directory(tmp_path: Path) -> None:
    output_path = tmp_path / "nested" / "report.md"
    written_path = write_markdown_report({"parsed_documents": []}, "run-123", output_path)

    assert written_path == output_path
    assert output_path.exists()
    assert "# Invoice-to-Pay Demo Run" in output_path.read_text(encoding="utf-8")


def test_cli_rejects_unknown_parser() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_demo.py",
            "--invoice",
            "samples/invoice_001_canada_post_sample.pdf",
            "--parser",
            "unknown",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "parser must be liteparse or docling" in result.stderr


def test_build_review_card_prioritizes_ap_controls() -> None:
    review_card = build_review_card(
        {
            "risk_level": "medium",
            "match_result": {
                "match_status": "mismatch",
                "mismatch_reasons": ["missing_purchase_order"],
            },
            "exception_result": {"exceptions": [{"code": "missing_po"}]},
            "fraud_result": {"signal_count": 1},
            "approval_route": {
                "route": "human_review",
                "approver_role": "ap_manager",
            },
            "payment_plan": {"payment_status": "held"},
            "__interrupt__": ("approval",),
        },
        "run-123",
    )

    assert "Invoice-to-Pay Review Card" in review_card
    assert "Risk" in review_card
    assert "Match status" in review_card
    assert "missing_purchase_order" in review_card
    assert "Payment status" in review_card
    assert "ERP status" in review_card

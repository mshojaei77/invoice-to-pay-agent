from pathlib import Path

import pytest

from scripts.run_demo import build_markdown_report, write_markdown_report, _normalize_parser_name


def test_normalize_parser_name_accepts_mineru_spellings() -> None:
    assert _normalize_parser_name("MinerU") == "mineru"
    assert _normalize_parser_name("MinerU_") == "mineru"
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

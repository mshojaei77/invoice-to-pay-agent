from pathlib import Path
from unittest.mock import patch

from app.schemas.parsed_document import ParsedDocument
from app.services.parser import LiteParseAdapter

SAMPLE_INVOICE = Path("samples/sample-pdf-invoice.pdf")
SAMPLE_SCAN = Path("samples/handwritten-invoice-no-tax.pdf")


def test_liteparse_adapter_returns_parsed_document(tmp_path: Path) -> None:
    fake_output = {
        "pages": [{"page": 1, "text": "Invoice INV-001"}],
        "tables": [],
        "blocks": [],
        "images": [],
        "confidence": 0.91,
        "warnings": [],
    }

    def fake_run(cmd: list[str], check: bool) -> None:
        output_path = Path(cmd[-1])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(__import__("json").dumps(fake_output), encoding="utf-8")

    with patch("app.services.parser.subprocess.run", side_effect=fake_run):
        result = LiteParseAdapter().parse(SAMPLE_INVOICE, document_type="invoice")

    assert isinstance(result, ParsedDocument)
    assert result.parser_name == "liteparse"
    assert result.document_type == "invoice"
    assert result.text == "Invoice INV-001"
    assert result.page_count == 1


def test_mineru_adapter_returns_parsed_document(tmp_path: Path) -> None:
    def fake_run(cmd: list[str], check: bool) -> None:
        output_dir = Path(cmd[-1])
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "output.md").write_text("# Scanned document", encoding="utf-8")

    with patch("app.services.parser.subprocess.run", side_effect=fake_run):
        from app.services.parser import MinerUAdapter
        result = MinerUAdapter().parse(SAMPLE_SCAN, document_type="invoice")

    assert isinstance(result, ParsedDocument)
    assert result.parser_name == "mineru"
    assert result.document_type == "invoice"


def test_raw_artifact_is_written(tmp_path: Path) -> None:
    from app.services.parser import _write_raw_artifact
    path = _write_raw_artifact("testparser", {"key": "value"})
    assert path.exists()
    assert path.suffix == ".json"
    assert "testparser" in path.name

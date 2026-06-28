from pathlib import Path
from unittest.mock import patch

from app.schemas.parsed_document import ParsedDocument
from app.services.parser import LiteParseAdapter


def test_liteparse_adapter_returns_parsed_document(tmp_path: Path) -> None:
    fake_input = tmp_path / "invoice.pdf"
    fake_input.write_bytes(b"%PDF fake")

    fake_output = {
        "text": "Invoice INV-001",
        "markdown": "# Invoice INV-001",
        "tables": [],
        "blocks": [],
        "images": [],
        "page_count": 1,
        "confidence": 0.91,
        "warnings": [],
    }

    def fake_run(cmd: list[str], check: bool) -> None:
        output_path = Path(cmd[-1])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(__import__("json").dumps(fake_output), encoding="utf-8")

    with patch("app.services.parser.subprocess.run", side_effect=fake_run):
        result = LiteParseAdapter().parse(fake_input, document_type="invoice")

    assert isinstance(result, ParsedDocument)
    assert result.parser_name == "liteparse"
    assert result.document_type == "invoice"


def test_mineru_adapter_returns_parsed_document(tmp_path: Path) -> None:
    fake_input = tmp_path / "scan.pdf"
    fake_input.write_bytes(b"%PDF fake")

    def fake_run(cmd: list[str], check: bool) -> None:
        output_dir = Path(cmd[-1])
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "output.md").write_text("# Scanned document", encoding="utf-8")

    with patch("app.services.parser.subprocess.run", side_effect=fake_run):
        from app.services.parser import MinerUAdapter
        result = MinerUAdapter().parse(fake_input, document_type="invoice")

    assert isinstance(result, ParsedDocument)
    assert result.parser_name == "mineru"
    assert result.document_type == "invoice"


def test_raw_artifact_is_written(tmp_path: Path) -> None:
    from app.services.parser import _write_raw_artifact
    path = _write_raw_artifact("testparser", {"key": "value"})
    assert path.exists()
    assert path.suffix == ".json"
    assert "testparser" in path.name

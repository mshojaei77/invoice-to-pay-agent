from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import patch
import sys

from app.schemas.parsed_document import ParsedDocument
from app.services.parser import DoclingAdapter, LiteParseAdapter

SAMPLE_INVOICE = Path("samples/invoice_001_canada_post_sample.pdf")
SAMPLE_SCAN = Path("samples/invoice_004_handwritten_no_tax.pdf")


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


class FakeDoclingDocument:
    def export_to_markdown(self) -> str:
        return "# Scanned document"

    def export_to_dict(self) -> dict:
        return {
            "pages": {"1": {"size": {"width": 100, "height": 100}}},
            "texts": [{"text": "Scanned document"}],
            "tables": [{"data": []}],
            "pictures": [],
        }


class FakeDoclingResult:
    document = FakeDoclingDocument()


def test_docling_adapter_returns_parsed_document(tmp_path: Path) -> None:
    base_models = ModuleType("docling.datamodel.base_models")
    base_models.InputFormat = SimpleNamespace(PDF="pdf")

    pipeline_options = ModuleType("docling.datamodel.pipeline_options")
    pipeline_options.PdfPipelineOptions = lambda **kwargs: kwargs

    document_converter = ModuleType("docling.document_converter")
    document_converter.DocumentConverter = object
    document_converter.PdfFormatOption = lambda **kwargs: kwargs

    with patch.dict(
        sys.modules,
        {
            "docling.datamodel.base_models": base_models,
            "docling.datamodel.pipeline_options": pipeline_options,
            "docling.document_converter": document_converter,
        },
    ):
        with patch.object(document_converter, "DocumentConverter") as converter:
            converter.return_value.convert.return_value = FakeDoclingResult()
            result = DoclingAdapter().parse(SAMPLE_SCAN, document_type="invoice")

    assert isinstance(result, ParsedDocument)
    assert result.parser_name == "docling"
    assert result.document_type == "invoice"
    assert result.markdown == "# Scanned document"
    assert result.page_count == 1
    assert result.tables == [{"data": []}]


def test_raw_artifact_is_written(tmp_path: Path) -> None:
    from app.services.parser import _write_raw_artifact
    path = _write_raw_artifact("testparser", {"key": "value"})
    assert path.exists()
    assert path.suffix == ".json"
    assert "testparser" in path.name

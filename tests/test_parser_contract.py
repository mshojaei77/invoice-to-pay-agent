from pathlib import Path

import pytest
from pydantic import ValidationError

from app.schemas.parsed_document import ParsedDocument


def test_valid_parser_output_passes() -> None:
    doc = ParsedDocument(
        parser_name="liteparse",
        parser_version="2.2.1",
        document_type="invoice",
        text="Invoice INV-001 total 121.00",
        markdown="# Invoice\n\nTotal: 121.00",
        tables=[],
        blocks=[],
        images=[],
        page_count=1,
        confidence=0.95,
        warnings=[],
        raw_artifact_path=Path("data/processed/raw/liteparse-run-1.json"),
    )

    assert doc.parser_name == "liteparse"
    assert doc.confidence == 0.95


def test_missing_required_fields_fail() -> None:
    with pytest.raises(ValidationError):
        ParsedDocument(
            parser_name="liteparse",
            parser_version="2.2.1",
            document_type="invoice",
            text="Invoice",
            markdown="Invoice",
            tables=[],
            blocks=[],
            images=[],
            page_count=1,
            confidence=0.9,
            warnings=[],
        )


def test_wrong_field_types_fail() -> None:
    with pytest.raises(ValidationError):
        ParsedDocument(
            parser_name="liteparse",
            parser_version="2.2.1",
            document_type="invoice",
            text="Invoice",
            markdown="Invoice",
            tables=[],
            blocks=[],
            images=[],
            page_count="1",
            confidence=0.9,
            warnings=[],
            raw_artifact_path=Path("data/processed/raw/file.json"),
        )

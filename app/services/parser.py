from __future__ import annotations

import json
import os
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.schemas.parsed_document import ParsedDocument


RAW_PARSER_DIR = Path("data/processed/parser_raw")


class ParserAdapter(ABC):
    parser_name: str

    @abstractmethod
    def parse(self, file_path: Path, document_type: str = "unknown") -> ParsedDocument:
        """Parse a document and return the normalized parser contract."""


def _write_raw_artifact(
    parser_name: str,
    raw_payload: dict[str, Any],
) -> Path:
    RAW_PARSER_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_PARSER_DIR / f"{parser_name}-{uuid4()}.json"
    path.write_text(json.dumps(raw_payload, indent=2, default=str), encoding="utf-8")
    return path


class LiteParseAdapter(ParserAdapter):
    parser_name = "liteparse"

    def parse(self, file_path: Path, document_type: str = "unknown") -> ParsedDocument:
        output_path = RAW_PARSER_DIR / f"liteparse-{uuid4()}.json"
        RAW_PARSER_DIR.mkdir(parents=True, exist_ok=True)

        subprocess.run(
            [
                "lit",
                "parse",
                str(file_path),
                "--format",
                "json",
                "-o",
                str(output_path),
            ],
            check=True,
        )

        raw = json.loads(output_path.read_text(encoding="utf-8"))

        pages = raw.get("pages", [])
        page_text = "\n\n".join(
            page.get("text", "")
            for page in pages
            if isinstance(page, dict) and page.get("text")
        )
        text = raw.get("text") or page_text
        markdown = raw.get("markdown") or text
        page_count = raw.get("page_count") or len(pages) or 1

        return ParsedDocument(
            parser_name="liteparse",
            parser_version="unknown",
            document_type=document_type,
            text=text,
            markdown=markdown,
            tables=raw.get("tables", []),
            blocks=raw.get("blocks", []),
            images=raw.get("images", []),
            page_count=max(int(page_count), 1),
            confidence=float(raw.get("confidence", 0.8)),
            warnings=raw.get("warnings", []),
            raw_artifact_path=output_path,
        )


class DoclingAdapter(ParserAdapter):
    parser_name = "docling"

    def parse(self, file_path: Path, document_type: str = "unknown") -> ParsedDocument:
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import PdfPipelineOptions
        from docling.document_converter import DocumentConverter, PdfFormatOption

        pipeline_options = PdfPipelineOptions(
            do_ocr=_env_bool("DOCLING_DO_OCR", True),
            do_table_structure=_env_bool("DOCLING_DO_TABLE_STRUCTURE", True),
        )
        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options),
            }
        )
        result = converter.convert(str(file_path))
        document = result.document
        markdown = document.export_to_markdown()
        raw_document = document.export_to_dict()
        raw_artifact_path = _write_raw_artifact(
            "docling",
            {
                "source": str(file_path),
                "document": raw_document,
                "markdown": markdown,
            },
        )

        return ParsedDocument(
            parser_name="docling",
            parser_version="unknown",
            document_type=document_type,
            text=markdown,
            markdown=markdown,
            tables=_docling_items(raw_document, "tables"),
            blocks=_docling_blocks(raw_document),
            images=_docling_items(raw_document, "pictures"),
            page_count=_docling_page_count(raw_document),
            confidence=0.85,
            warnings=[],
            raw_artifact_path=raw_artifact_path,
        )


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _docling_items(raw_document: dict[str, Any], key: str) -> list[dict[str, Any]]:
    items = raw_document.get(key, [])
    return items if isinstance(items, list) else []


def _docling_blocks(raw_document: dict[str, Any]) -> list[dict[str, Any]]:
    blocks = []
    for key in ("texts", "groups"):
        value = raw_document.get(key, [])
        if isinstance(value, list):
            blocks.extend(item for item in value if isinstance(item, dict))
    return blocks


def _docling_page_count(raw_document: dict[str, Any]) -> int:
    pages = raw_document.get("pages", {})
    if isinstance(pages, dict):
        return max(len(pages), 1)
    if isinstance(pages, list):
        return max(len(pages), 1)
    return 1

from __future__ import annotations

import json
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


class MinerUAdapter(ParserAdapter):
    parser_name = "mineru"

    def parse(self, file_path: Path, document_type: str = "unknown") -> ParsedDocument:
        output_dir = RAW_PARSER_DIR / f"mineru-{uuid4()}"
        output_dir.mkdir(parents=True, exist_ok=True)

        subprocess.run(
            [
                "mineru",
                "-p",
                str(file_path),
                "-o",
                str(output_dir),
                "-b",
                "pipeline",
            ],
            check=True,
        )

        markdown_files = list(output_dir.rglob("*.md"))
        json_files = list(output_dir.rglob("*.json"))

        markdown = markdown_files[0].read_text(encoding="utf-8") if markdown_files else ""
        raw_payload = {
            "output_dir": str(output_dir),
            "markdown_files": [str(p) for p in markdown_files],
            "json_files": [str(p) for p in json_files],
        }
        raw_artifact_path = _write_raw_artifact("mineru", raw_payload)

        return ParsedDocument(
            parser_name="mineru",
            parser_version="unknown",
            document_type=document_type,
            text=markdown,
            markdown=markdown,
            tables=[],
            blocks=[],
            images=[],
            page_count=1,
            confidence=0.85,
            warnings=[],
            raw_artifact_path=raw_artifact_path,
        )

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


ParserName = Literal["liteparse", "docling"]
DocumentType = Literal[
    "invoice",
    "purchase_order",
    "delivery_note",
    "receipt",
    "unknown",
]


class ParsedDocument(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    parser_name: ParserName
    parser_version: str = Field(min_length=1)
    document_type: DocumentType

    text: str
    markdown: str

    tables: list[dict[str, Any]]
    blocks: list[dict[str, Any]]
    images: list[dict[str, Any]]

    page_count: int = Field(ge=1)
    confidence: float = Field(ge=0.0, le=1.0)
    warnings: list[str]

    raw_artifact_path: Path

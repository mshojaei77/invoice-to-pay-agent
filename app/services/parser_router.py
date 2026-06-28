from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.schemas.parsed_document import ParsedDocument


@dataclass(frozen=True)
class ParserRoute:
    first_parser: str
    reason: str
    allow_mineru_retry: bool = True


def choose_initial_parser(
    file_path: Path,
    declared_document_type: str | None = None,
    hints: list[str] | None = None,
) -> ParserRoute:
    hints = hints or []
    suffix = file_path.suffix.lower()

    mineru_hints = {
        "receipt_photo",
        "scanned",
        "dense_tables",
        "handwriting",
        "stamp",
        "signature",
    }

    if suffix in {".png", ".jpg", ".jpeg", ".tiff"}:
        return ParserRoute("mineru", "image_input")

    if declared_document_type == "receipt":
        return ParserRoute("mineru", "receipt")

    if any(h in mineru_hints for h in hints):
        return ParserRoute("mineru", "complex_document_hint")

    return ParserRoute("liteparse", "fast_default")


def should_retry_with_mineru(
    parsed: ParsedDocument,
    validation_errors: list[dict],
    payment_critical_mismatches: list[str],
) -> bool:
    if parsed.parser_name == "mineru":
        return False

    if parsed.confidence < 0.75:
        return True

    if validation_errors:
        return True

    if payment_critical_mismatches:
        return True

    complex_warnings = {"handwriting", "stamp", "signature", "dense_tables", "scanned"}
    return bool(complex_warnings.intersection(set(parsed.warnings)))

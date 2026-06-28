from pathlib import Path

from app.schemas.parsed_document import ParsedDocument
from app.services.parser_router import choose_initial_parser, should_retry_with_mineru


def test_receipt_photo_routes_to_mineru() -> None:
    route = choose_initial_parser(Path("receipt.jpg"), declared_document_type="receipt")
    assert route.first_parser == "mineru"


def test_clean_pdf_routes_to_liteparse() -> None:
    route = choose_initial_parser(Path("invoice.pdf"))
    assert route.first_parser == "liteparse"


def test_image_file_routes_to_mineru() -> None:
    route = choose_initial_parser(Path("scan.png"))
    assert route.first_parser == "mineru"


def test_tiff_file_routes_to_mineru() -> None:
    route = choose_initial_parser(Path("doc.tiff"))
    assert route.first_parser == "mineru"


def test_handwriting_hint_routes_to_mineru() -> None:
    route = choose_initial_parser(Path("invoice.pdf"), hints=["handwriting"])
    assert route.first_parser == "mineru"


def test_stamp_hint_routes_to_mineru() -> None:
    route = choose_initial_parser(Path("invoice.pdf"), hints=["stamp"])
    assert route.first_parser == "mineru"


def test_scanned_hint_routes_to_mineru() -> None:
    route = choose_initial_parser(Path("invoice.pdf"), hints=["scanned"])
    assert route.first_parser == "mineru"


def test_low_confidence_liteparse_retries_mineru(tmp_path: Path) -> None:
    parsed = ParsedDocument(
        parser_name="liteparse",
        parser_version="2.2.1",
        document_type="invoice",
        text="",
        markdown="",
        tables=[],
        blocks=[],
        images=[],
        page_count=1,
        confidence=0.4,
        warnings=[],
        raw_artifact_path=tmp_path / "raw.json",
    )

    assert should_retry_with_mineru(parsed, [], []) is True


def test_high_confidence_liteparse_does_not_retry(tmp_path: Path) -> None:
    parsed = ParsedDocument(
        parser_name="liteparse",
        parser_version="2.2.1",
        document_type="invoice",
        text="Invoice",
        markdown="# Invoice",
        tables=[],
        blocks=[],
        images=[],
        page_count=1,
        confidence=0.95,
        warnings=[],
        raw_artifact_path=tmp_path / "raw.json",
    )

    assert should_retry_with_mineru(parsed, [], []) is False


def test_mineru_output_does_not_retry(tmp_path: Path) -> None:
    parsed = ParsedDocument(
        parser_name="mineru",
        parser_version="3.4.0",
        document_type="invoice",
        text="",
        markdown="",
        tables=[],
        blocks=[],
        images=[],
        page_count=1,
        confidence=0.4,
        warnings=[],
        raw_artifact_path=tmp_path / "raw.json",
    )

    assert should_retry_with_mineru(parsed, [], []) is False


def test_validation_errors_trigger_retry(tmp_path: Path) -> None:
    parsed = ParsedDocument(
        parser_name="liteparse",
        parser_version="2.2.1",
        document_type="invoice",
        text="",
        markdown="",
        tables=[],
        blocks=[],
        images=[],
        page_count=1,
        confidence=0.95,
        warnings=[],
        raw_artifact_path=tmp_path / "raw.json",
    )

    assert should_retry_with_mineru(parsed, [{"field": "total"}], []) is True


def test_payment_critical_mismatch_triggers_retry(tmp_path: Path) -> None:
    parsed = ParsedDocument(
        parser_name="liteparse",
        parser_version="2.2.1",
        document_type="invoice",
        text="",
        markdown="",
        tables=[],
        blocks=[],
        images=[],
        page_count=1,
        confidence=0.95,
        warnings=[],
        raw_artifact_path=tmp_path / "raw.json",
    )

    assert should_retry_with_mineru(parsed, [], ["total_mismatch"]) is True


def test_complex_warning_triggers_retry(tmp_path: Path) -> None:
    parsed = ParsedDocument(
        parser_name="liteparse",
        parser_version="2.2.1",
        document_type="invoice",
        text="",
        markdown="",
        tables=[],
        blocks=[],
        images=[],
        page_count=1,
        confidence=0.95,
        warnings=["handwriting"],
        raw_artifact_path=tmp_path / "raw.json",
    )

    assert should_retry_with_mineru(parsed, [], []) is True

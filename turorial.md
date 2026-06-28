# Invoice-to-Pay Agent: Beginner AI Engineer Tutorial

## 1. What you are building

You are building a controlled **invoice-to-pay agent** for Accounts Payable.

The goal is not “read a PDF with AI.” The goal is:

```text
Upload AP documents
→ parse them
→ normalize them into strict schemas
→ validate finance rules
→ compare invoice / PO / delivery evidence
→ detect duplicates
→ score risk
→ ask a human only when needed
→ post only safe cases to an ERP mock
→ write an audit trail
```

The graph must stay central:

```text
START
  -> save_uploads
  -> parse_documents_fast_with_liteparse
  -> normalize_ap_documents
  -> validate_schema
  -> validate_business_rules
  -> route_to_mineru_if_needed
  -> reconcile_parser_outputs
  -> duplicate_check
  -> match_invoice_po_delivery
  -> risk_score
  -> approval_gate
  -> post_to_erp_mock
  -> write_audit_log
  -> END
```

Everything else is a wrapper:

```text
FastAPI       -> calls the graph
Streamlit     -> calls FastAPI
PostgreSQL    -> stores graph outputs
MinIO         -> stores graph artifacts
MLflow        -> tracks graph/eval metrics
Tracing       -> observes graph runs
PySpark       -> analyzes graph outputs later
```

That separation matters. If you put business logic in FastAPI or Streamlit, you no longer have one auditable product core. Tiny architecture crime, big future migraine.

---

## 2. Install and baseline the repo

Start every milestone with a clean baseline.

```bash
uv sync
uv run pytest
uv run python -m compileall app tests
git status --short
```

Use `uv add <package>` for new dependencies because `uv` is your project manager. The `uv` docs cover project workflows, dependency management, and running project commands through `uv run`. ([Astral Docs][4])

Create a file for baseline notes:

```bash
mkdir -p docs
touch docs/baseline.md
```

Add something like:

```md
# Baseline before milestone 1

Date: 2026-06-28

Commands run:

- uv sync
- uv run pytest
- uv run python -m compileall app tests
- git status --short

Existing failures:

- None / or list them here

Unrelated local changes:

- None / or list them here
```

Also check for old parser paths:

```bash
grep -R "pdfplumber\|pypdf\|pymupdf\|tesseract" app tests || true
```

Keep third parser usage out of the main path. It is okay to mention old code in migration notes, but the graph’s parser services should use only LiteParse and MinerU.

---

# Phase 1 — Parser contracts

## Milestone 1: Create the parser contract

A parser contract is the shape every parser must return. You need this before you build LiteParse or MinerU adapters.

Create:

```text
app/schemas/parsed_document.py
tests/test_parser_contract.py
```

Install/update Pydantic only if needed:

```bash
uv add pydantic
```

Create `app/schemas/parsed_document.py`:

```python
from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


ParserName = Literal["liteparse", "mineru"]
DocumentType = Literal[
    "invoice",
    "purchase_order",
    "delivery_note",
    "receipt",
    "unknown",
]


class ParsedDocument(BaseModel):
    """
    Normalized output from any parser.

    LiteParse and MinerU can have different native outputs.
    The rest of the app should not care.
    The rest of the app only reads ParsedDocument.
    """

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
```

Why strict? Because AP data should not silently coerce `"100.00"` into `100.00` unless you explicitly decide to allow it. Pydantic’s strict mode is designed exactly for “do not quietly coerce types” validation. ([Pydantic][3])

Create `tests/test_parser_contract.py`:

```python
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
            # raw_artifact_path missing
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
            page_count="1",  # strict mode should reject this
            confidence=0.9,
            warnings=[],
            raw_artifact_path=Path("data/processed/raw/file.json"),
        )
```

Run:

```bash
uv run pytest tests/test_parser_contract.py
uv run python -m compileall app tests
```

Commit message:

```text
feat(parser): add strict parsed document contract
```

---

# Phase 2 — Parser adapters and routing

## Milestone 2: Add LiteParse and MinerU adapters

LiteParse is your fast local parser. The current LiteParse docs show both Python usage and CLI usage; the Python package includes the `lit` CLI, supports `lit parse document.pdf --format json`, Markdown output, screenshots, and document complexity checks. ([Developer Documentation][2]) MinerU is your heavier parser for complex layouts, scans, images, handwritten cases, and richer Markdown/JSON outputs; its docs also warn that document parsing is difficult and quality should be tested on real samples. ([OpenDataLab][5])

Add LiteParse:

```bash
uv add liteparse
```

For MinerU, your rule says use `uv add`. The official MinerU quickstart currently shows `uv pip install -U "mineru[all]"`; in this repo, try to keep it project-managed with: ([OpenDataLab][5])

```bash
uv add "mineru[all]"
```

If that fails because of platform/GPU dependency issues, document the failure in `docs/baseline.md` and keep MinerU mocked until the environment is ready.

Create:

```text
app/services/parser.py
tests/test_parser_adapters.py
```

Example `app/services/parser.py`:

```python
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
        """
        Beginner implementation:
        Use LiteParse CLI JSON output first.
        Later you can replace this with direct LiteParse Python API usage.
        """

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

        text = raw.get("text", "")
        markdown = raw.get("markdown", text)

        return ParsedDocument(
            parser_name="liteparse",
            parser_version="unknown",
            document_type=document_type,  # normalize later
            text=text,
            markdown=markdown,
            tables=raw.get("tables", []),
            blocks=raw.get("blocks", []),
            images=raw.get("images", []),
            page_count=max(int(raw.get("page_count", 1)), 1),
            confidence=float(raw.get("confidence", 0.8)),
            warnings=raw.get("warnings", []),
            raw_artifact_path=output_path,
        )


class MinerUAdapter(ParserAdapter):
    parser_name = "mineru"

    def parse(self, file_path: Path, document_type: str = "unknown") -> ParsedDocument:
        """
        Beginner implementation:
        Run MinerU into an output directory and normalize the resulting artifacts.
        """

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

        # Keep this defensive because MinerU output structure may vary by version/config.
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
```

Beginner note: do not let LiteParse/MinerU outputs leak into your graph. Convert everything into `ParsedDocument`.

Mock tests:

```python
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
```

Run:

```bash
uv run pytest tests/test_parser_adapters.py
uv run python -m compileall app tests
```

---

## Milestone 3: Add parser routing

Parser routing decides which parser to use and when to retry with MinerU.

Create:

```text
app/services/parser_router.py
tests/test_parser_router.py
```

Use LiteParse first for clean selectable PDFs and simple PO tables. Use MinerU for receipts, scans, dense tables, handwriting, stamps/signatures, failed schema validation, and low confidence. LiteParse has a documented `is_complex` check that can identify pages needing OCR or heavier processing; that makes it useful as a cheap routing preflight. ([GitHub][6])

Example:

```python
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

    # Do not hide payment-critical mismatches by reparsing forever.
    # Reparse may help extraction, but final mismatch still goes to human review.
    if payment_critical_mismatches:
        return True

    complex_warnings = {"handwriting", "stamp", "signature", "dense_tables", "scanned"}
    return bool(complex_warnings.intersection(set(parsed.warnings)))
```

Tests should cover each routing case:

```python
from pathlib import Path

from app.schemas.parsed_document import ParsedDocument
from app.services.parser_router import choose_initial_parser, should_retry_with_mineru


def test_receipt_photo_routes_to_mineru() -> None:
    route = choose_initial_parser(Path("receipt.jpg"), declared_document_type="receipt")
    assert route.first_parser == "mineru"


def test_clean_pdf_routes_to_liteparse() -> None:
    route = choose_initial_parser(Path("invoice.pdf"))
    assert route.first_parser == "liteparse"


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
```

Run:

```bash
uv run pytest tests/test_parser_router.py
uv run python -m compileall app tests
```

---

# Phase 3 — Strict AP schemas

## Milestone 4: Build invoice, PO, and delivery-note schemas

Create:

```text
app/schemas/common.py
app/schemas/ap_document.py
app/schemas/invoice.py
app/schemas/purchase_order.py
app/schemas/delivery_note.py
tests/test_ap_schemas.py
```

Use `Decimal` for money. Do not use `float` for payment totals. Floats are spicy little gremlins for accounting.

Example `app/schemas/common.py`:

```python
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


Currency = Literal["EUR", "USD", "GBP"]


class StrictBaseModel(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")


class MoneyAmount(StrictBaseModel):
    amount: Decimal = Field(gt=Decimal("0"))
    currency: Currency


class LineItem(StrictBaseModel):
    description: str = Field(min_length=1)
    quantity: Decimal = Field(gt=Decimal("0"))
    unit_price: Decimal = Field(ge=Decimal("0"))
    line_total: Decimal = Field(ge=Decimal("0"))

    @model_validator(mode="after")
    def validate_line_total(self) -> "LineItem":
        expected = self.quantity * self.unit_price
        if abs(expected - self.line_total) > Decimal("0.02"):
            raise ValueError(f"line_total mismatch: expected {expected}, got {self.line_total}")
        return self


class Party(StrictBaseModel):
    name: str = Field(min_length=1)
    iban: str | None = None
    vat_number: str | None = None
```

Example `app/schemas/invoice.py`:

```python
from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import Field, model_validator

from app.schemas.common import Currency, LineItem, Party, StrictBaseModel


class Invoice(StrictBaseModel):
    document_type: str = "invoice"

    invoice_number: str = Field(min_length=1)
    po_number: str | None = None

    vendor: Party
    buyer: Party | None = None

    issue_date: date
    due_date: date | None = None

    currency: Currency
    line_items: list[LineItem] = Field(min_length=1)

    subtotal: Decimal = Field(gt=Decimal("0"))
    tax_amount: Decimal = Field(ge=Decimal("0"))
    total_amount: Decimal = Field(gt=Decimal("0"))

    @model_validator(mode="after")
    def validate_dates_and_totals(self) -> "Invoice":
        today = date.today()

        if self.issue_date > today:
            raise ValueError("issue_date cannot be in the future")

        if self.due_date and self.due_date < self.issue_date:
            raise ValueError("due_date cannot be before issue_date")

        calculated_subtotal = sum(item.line_total for item in self.line_items)
        if abs(calculated_subtotal - self.subtotal) > Decimal("0.02"):
            raise ValueError("line-item totals do not match subtotal")

        calculated_total = self.subtotal + self.tax_amount
        if abs(calculated_total - self.total_amount) > Decimal("0.02"):
            raise ValueError("subtotal plus tax does not match total_amount")

        return self
```

For `purchase_order.py`:

```python
from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import Field

from app.schemas.common import Currency, LineItem, Party, StrictBaseModel


class PurchaseOrder(StrictBaseModel):
    document_type: str = "purchase_order"

    po_number: str = Field(min_length=1)
    vendor: Party
    buyer: Party | None = None
    issue_date: date

    currency: Currency
    line_items: list[LineItem] = Field(min_length=1)

    subtotal: Decimal = Field(gt=Decimal("0"))
    tax_amount: Decimal = Field(ge=Decimal("0"))
    total_amount: Decimal = Field(gt=Decimal("0"))
```

For `delivery_note.py`:

```python
from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import Field

from app.schemas.common import LineItem, Party, StrictBaseModel


class DeliveryNote(StrictBaseModel):
    document_type: str = "delivery_note"

    delivery_note_number: str = Field(min_length=1)
    po_number: str = Field(min_length=1)

    vendor: Party
    buyer: Party | None = None

    delivery_date: date
    delivered_items: list[LineItem] = Field(min_length=1)
    delivery_status: str = Field(min_length=1)
```

Pydantic validators are the right layer for hard schema validity: required fields, date ordering, money positivity, allowed currencies, and total consistency. Business concerns such as “missing PO” or “low parser confidence” should go into a separate validation service, not the schema. ([Pydantic][7])

Run:

```bash
uv run pytest tests/test_ap_schemas.py
uv run python -m compileall app tests
```

---

# Phase 4 — Business validation

## Milestone 5: Add business-rule validation

Schema validation answers:

```text
Is this object structurally valid?
```

Business validation answers:

```text
Even if structurally valid, is it safe for AP?
```

Create:

```text
app/services/validation.py
tests/test_business_validation.py
```

Example:

```python
from __future__ import annotations

import re
from dataclasses import dataclass

from app.schemas.invoice import Invoice
from app.schemas.parsed_document import ParsedDocument


IBAN_RE = re.compile(r"^[A-Z]{2}[0-9A-Z]{13,32}$")
VAT_RE = re.compile(r"^[A-Z]{2}[0-9A-Z]{8,12}$")


@dataclass(frozen=True)
class BusinessRuleError:
    code: str
    message: str
    severity: str  # "low" | "medium" | "high"


def validate_invoice_business_rules(
    invoice: Invoice | None,
    parsed_documents: list[ParsedDocument],
    has_purchase_order: bool,
    has_delivery_note: bool,
) -> list[BusinessRuleError]:
    errors: list[BusinessRuleError] = []

    if invoice is None:
        return [
            BusinessRuleError(
                code="missing_invoice",
                message="No valid invoice was normalized.",
                severity="high",
            )
        ]

    if not has_purchase_order:
        errors.append(BusinessRuleError("missing_po", "Invoice has no matching PO.", "medium"))

    if not has_delivery_note:
        errors.append(
            BusinessRuleError(
                "missing_delivery_note",
                "Invoice has no matching delivery note.",
                "medium",
            )
        )

    if not invoice.vendor.name:
        errors.append(BusinessRuleError("missing_vendor", "Vendor name is missing.", "high"))

    if not invoice.vendor.iban:
        errors.append(BusinessRuleError("missing_iban", "Vendor IBAN is missing.", "medium"))
    elif not IBAN_RE.match(invoice.vendor.iban.replace(" ", "").upper()):
        errors.append(BusinessRuleError("invalid_iban", "Vendor IBAN format looks invalid.", "high"))

    if not invoice.vendor.vat_number:
        errors.append(BusinessRuleError("missing_vat", "Vendor VAT number is missing.", "medium"))
    elif not VAT_RE.match(invoice.vendor.vat_number.replace(" ", "").upper()):
        errors.append(BusinessRuleError("invalid_vat", "Vendor VAT format looks invalid.", "medium"))

    if any(doc.confidence < 0.75 for doc in parsed_documents):
        errors.append(BusinessRuleError("low_parser_confidence", "Parser confidence is low.", "medium"))

    if any("handwriting" in doc.warnings for doc in parsed_documents):
        errors.append(
            BusinessRuleError(
                "handwritten_correction",
                "Handwritten correction warning was detected.",
                "high",
            )
        )

    return errors
```

Keep this service dumb and deterministic. No LLM call needed here. Boring code is exactly what you want near money.

---

# Phase 5 — LangGraph state, nodes, and workflow

## Milestone 6: Define graph state

Create:

```text
app/graph/state.py
tests/test_state_shape.py
```

LangGraph state is usually a `TypedDict`. Nodes read the state and return only the fields they update. LangGraph’s graph API is built around nodes communicating through shared state. ([LangChain Reference Docs][8])

Example:

```python
from __future__ import annotations

from typing import Any, NotRequired, TypedDict


class APGraphState(TypedDict):
    run_id: str

    uploaded_documents: list[dict[str, Any]]
    parsed_documents: NotRequired[list[dict[str, Any]]]

    parser_route: NotRequired[list[dict[str, Any]]]
    parser_warnings: NotRequired[list[str]]

    invoice: NotRequired[dict[str, Any] | None]
    purchase_order: NotRequired[dict[str, Any] | None]
    delivery_note: NotRequired[dict[str, Any] | None]

    validation_errors: NotRequired[list[dict[str, Any]]]
    business_rule_errors: NotRequired[list[dict[str, Any]]]

    duplicate_result: NotRequired[dict[str, Any]]
    match_result: NotRequired[dict[str, Any]]

    risk_level: NotRequired[str]
    risk_score: NotRequired[float]
    risk_reasons: NotRequired[list[str]]
    requires_human_approval: NotRequired[bool]

    approval: NotRequired[dict[str, Any] | None]

    erp_result: NotRequired[dict[str, Any] | None]
    audit_events: NotRequired[list[dict[str, Any]]]
```

Beginner note: keep state JSON-serializable. That makes checkpointing, API responses, audit logs, and debugging easier.

---

## Milestone 7: Implement nodes

Create:

```text
app/graph/nodes.py
tests/test_nodes.py
```

Each node should:

1. Read state.
2. Call one service.
3. Return only updated fields.
4. Avoid non-idempotent side effects.
5. Never mutate state in place.

LangGraph docs explicitly warn that with checkpointers, nodes may re-run after an interrupt/resume, so side effects must be idempotent. ([LangChain Docs][1])

Skeleton:

```python
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from langgraph.types import interrupt

from app.graph.state import APGraphState


def save_uploads(state: APGraphState) -> dict[str, Any]:
    # In early milestones, uploaded_documents can already contain local paths.
    # Later FastAPI/MinIO can save the physical files before invoking the graph.
    return {
        "audit_events": [
            {
                "node": "save_uploads",
                "message": "Uploads registered",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ]
    }


def parse_documents_fast_with_liteparse(state: APGraphState) -> dict[str, Any]:
    # Call LiteParseAdapter here.
    # Return parsed_documents + parser_route + parser_warnings.
    return {
        "parsed_documents": [],
        "parser_route": [{"parser": "liteparse", "reason": "fast_default"}],
        "parser_warnings": [],
    }


def normalize_ap_documents(state: APGraphState) -> dict[str, Any]:
    # Convert ParsedDocument text/markdown/tables into Invoice/PO/Delivery schemas.
    # For MVP, this can be deterministic fixture-based extraction.
    return {
        "invoice": None,
        "purchase_order": None,
        "delivery_note": None,
    }


def validate_schema(state: APGraphState) -> dict[str, Any]:
    return {"validation_errors": []}


def validate_business_rules(state: APGraphState) -> dict[str, Any]:
    return {"business_rule_errors": []}


def route_to_mineru_if_needed(state: APGraphState) -> dict[str, Any]:
    return {"parser_warnings": state.get("parser_warnings", [])}


def reconcile_parser_outputs(state: APGraphState) -> dict[str, Any]:
    # If LiteParse and MinerU both ran, choose field-level evidence.
    return {}


def duplicate_check(state: APGraphState) -> dict[str, Any]:
    return {
        "duplicate_result": {
            "duplicate_status": "clear",
            "duplicate_candidates": [],
        }
    }


def match_invoice_po_delivery(state: APGraphState) -> dict[str, Any]:
    return {
        "match_result": {
            "match_status": "matched",
            "mismatch_reasons": [],
        }
    }


def risk_score(state: APGraphState) -> dict[str, Any]:
    return {
        "risk_level": "low",
        "risk_score": 0.0,
        "risk_reasons": [],
        "requires_human_approval": False,
    }


def approval_gate(state: APGraphState) -> dict[str, Any]:
    if not state.get("requires_human_approval", False):
        return {
            "approval": {
                "status": "auto_approved",
                "approved_by": "system",
                "reason": "low_risk",
            }
        }

    approval = interrupt(
        {
            "run_id": state["run_id"],
            "risk_level": state.get("risk_level"),
            "risk_score": state.get("risk_score"),
            "risk_reasons": state.get("risk_reasons", []),
            "match_result": state.get("match_result"),
            "duplicate_result": state.get("duplicate_result"),
        }
    )

    return {"approval": approval}


def post_to_erp_mock(state: APGraphState) -> dict[str, Any]:
    approval = state.get("approval") or {}

    if approval.get("status") in {"rejected", "human_rejected"}:
        return {
            "erp_result": {
                "status": "not_posted",
                "rejection_reason": "human_rejected",
            }
        }

    return {
        "erp_result": {
            "status": "posted",
            "erp_post_id": f"ERP-{state['run_id']}",
            "posted_at": datetime.now(timezone.utc).isoformat(),
        }
    }


def write_audit_log(state: APGraphState) -> dict[str, Any]:
    # Later this calls app.services.audit.write_audit_event.
    return {}
```

Only `approval_gate` should call `interrupt()`. LangGraph interrupts are made for human-in-the-loop approval workflows and should use JSON-serializable payloads. ([LangChain Docs][9])

---

## Milestone 8: Wire the LangGraph workflow

Create:

```text
app/graph/workflow.py
tests/test_graph.py
```

Install LangGraph:

```bash
uv add langgraph
```

Example:

```python
from __future__ import annotations

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from app.graph.nodes import (
    approval_gate,
    duplicate_check,
    match_invoice_po_delivery,
    normalize_ap_documents,
    parse_documents_fast_with_liteparse,
    post_to_erp_mock,
    reconcile_parser_outputs,
    risk_score,
    route_to_mineru_if_needed,
    save_uploads,
    validate_business_rules,
    validate_schema,
    write_audit_log,
)
from app.graph.state import APGraphState


def build_graph():
    builder = StateGraph(APGraphState)

    builder.add_node("save_uploads", save_uploads)
    builder.add_node("parse_documents_fast_with_liteparse", parse_documents_fast_with_liteparse)
    builder.add_node("normalize_ap_documents", normalize_ap_documents)
    builder.add_node("validate_schema", validate_schema)
    builder.add_node("validate_business_rules", validate_business_rules)
    builder.add_node("route_to_mineru_if_needed", route_to_mineru_if_needed)
    builder.add_node("reconcile_parser_outputs", reconcile_parser_outputs)
    builder.add_node("duplicate_check", duplicate_check)
    builder.add_node("match_invoice_po_delivery", match_invoice_po_delivery)
    builder.add_node("risk_score", risk_score)
    builder.add_node("approval_gate", approval_gate)
    builder.add_node("post_to_erp_mock", post_to_erp_mock)
    builder.add_node("write_audit_log", write_audit_log)

    builder.add_edge(START, "save_uploads")
    builder.add_edge("save_uploads", "parse_documents_fast_with_liteparse")
    builder.add_edge("parse_documents_fast_with_liteparse", "normalize_ap_documents")
    builder.add_edge("normalize_ap_documents", "validate_schema")
    builder.add_edge("validate_schema", "validate_business_rules")
    builder.add_edge("validate_business_rules", "route_to_mineru_if_needed")
    builder.add_edge("route_to_mineru_if_needed", "reconcile_parser_outputs")
    builder.add_edge("reconcile_parser_outputs", "duplicate_check")
    builder.add_edge("duplicate_check", "match_invoice_po_delivery")
    builder.add_edge("match_invoice_po_delivery", "risk_score")
    builder.add_edge("risk_score", "approval_gate")
    builder.add_edge("approval_gate", "post_to_erp_mock")
    builder.add_edge("post_to_erp_mock", "write_audit_log")
    builder.add_edge("write_audit_log", END)

    checkpointer = InMemorySaver()
    return builder.compile(checkpointer=checkpointer)
```

Run a graph with a stable thread:

```python
from uuid import uuid4

from app.graph.workflow import build_graph

graph = build_graph()

run_id = str(uuid4())
config = {"configurable": {"thread_id": run_id}}

result = graph.invoke(
    {
        "run_id": run_id,
        "uploaded_documents": [
            {"path": "data/samples/invoice.pdf", "document_type": "invoice"}
        ],
    },
    config=config,
)
```

For approval resumes, use the same `thread_id`. LangGraph docs are very clear here: the thread ID is the persistent cursor, and using a new one starts a new thread. ([LangChain Docs][9])

---

# Phase 6 — Demo scripts

## Milestone 9: Add CLI demo scripts

Create:

```text
scripts/run_demo.py
scripts/approve_demo.py
scripts/reject_demo.py
```

Example `scripts/run_demo.py`:

```python
from __future__ import annotations

import argparse
from uuid import uuid4

from app.graph.workflow import build_graph


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--invoice", required=True)
    parser.add_argument("--po")
    parser.add_argument("--delivery-note")
    args = parser.parse_args()

    run_id = str(uuid4())
    graph = build_graph()

    uploaded_documents = [{"path": args.invoice, "document_type": "invoice"}]
    if args.po:
        uploaded_documents.append({"path": args.po, "document_type": "purchase_order"})
    if args.delivery_note:
        uploaded_documents.append({"path": args.delivery_note, "document_type": "delivery_note"})

    result = graph.invoke(
        {"run_id": run_id, "uploaded_documents": uploaded_documents},
        config={"configurable": {"thread_id": run_id}},
    )

    print(f"run_id={run_id}")
    print(f"risk_level={result.get('risk_level')}")
    print(f"erp_status={(result.get('erp_result') or {}).get('status')}")
    print("audit_log=data/processed/audit.jsonl")


if __name__ == "__main__":
    main()
```

Run:

```bash
uv run python scripts/run_demo.py \
  --invoice data/samples/clean_invoice.pdf \
  --po data/samples/po.pdf \
  --delivery-note data/samples/delivery_note.pdf
```

---

# Phase 7 — Risk, duplicates, matching, audit, and ERP mock

## Milestone 10: Risk scoring

Create:

```text
app/services/risk.py
tests/test_risk.py
```

Example:

```python
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RiskResult:
    risk_level: str
    risk_score: float
    risk_reasons: list[str]
    requires_human_approval: bool


def calculate_risk(
    validation_errors: list[dict],
    business_rule_errors: list[dict],
    duplicate_result: dict,
    match_result: dict,
) -> RiskResult:
    score = 0.0
    reasons: list[str] = []

    def add(points: float, reason: str) -> None:
        nonlocal score
        score += points
        reasons.append(reason)

    if validation_errors:
        add(50, "schema_validation_errors")

    for err in business_rule_errors:
        code = err.get("code")
        if code in {"missing_po", "missing_delivery_note"}:
            add(15, code)
        elif code in {"invalid_iban", "missing_vendor"}:
            add(30, code)
        elif code in {"missing_iban", "missing_vat", "invalid_vat"}:
            add(15, code)
        elif code in {"handwritten_correction"}:
            add(35, code)
        elif code in {"low_parser_confidence"}:
            add(20, code)

    duplicate_status = duplicate_result.get("duplicate_status")
    if duplicate_status == "possible_duplicate":
        add(30, "possible_duplicate")
    elif duplicate_status == "confirmed_duplicate":
        add(100, "confirmed_duplicate")

    for reason in match_result.get("mismatch_reasons", []):
        add(25, f"match_mismatch:{reason}")

    if score >= 70:
        level = "high"
    elif score >= 25:
        level = "medium"
    else:
        level = "low"

    return RiskResult(
        risk_level=level,
        risk_score=min(score, 100.0),
        risk_reasons=reasons,
        requires_human_approval=level in {"medium", "high"},
    )
```

Rule of thumb:

```text
low risk    -> auto approval eligible
medium risk -> human approval
high risk   -> human approval, never post unless explicitly approved
```

---

## Milestone 11: Duplicate detection

Create:

```text
app/services/duplicates.py
tests/test_duplicates.py
```

Install RapidFuzz:

```bash
uv add rapidfuzz
```

RapidFuzz is a Python/C++ fuzzy string matching library, which fits vendor-name matching where `ACME BV`, `ACME B.V.`, and `Acme Netherlands` may refer to the same supplier. ([GitHub][10])

Start with JSONL storage:

```python
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path

from rapidfuzz import fuzz


@dataclass(frozen=True)
class DuplicateCandidate:
    invoice_number: str
    vendor_name: str
    total_amount: str
    issue_date: str
    reason: str
    score: float


def load_seen_invoices(path: Path) -> list[dict]:
    if not path.exists():
        return []

    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def check_duplicate(
    vendor_name: str,
    invoice_number: str,
    total_amount: Decimal,
    issue_date: date,
    seen_path: Path = Path("data/processed/seen_invoices.jsonl"),
) -> dict:
    seen = load_seen_invoices(seen_path)
    candidates: list[DuplicateCandidate] = []

    for old in seen:
        vendor_score = fuzz.token_sort_ratio(vendor_name, old["vendor_name"])

        if vendor_score >= 90 and invoice_number == old["invoice_number"]:
            candidates.append(
                DuplicateCandidate(
                    invoice_number=old["invoice_number"],
                    vendor_name=old["vendor_name"],
                    total_amount=old["total_amount"],
                    issue_date=old["issue_date"],
                    reason="same_vendor_and_invoice_number",
                    score=100.0,
                )
            )

        elif (
            vendor_score >= 85
            and str(total_amount) == old["total_amount"]
            and issue_date.isoformat() == old["issue_date"]
        ):
            candidates.append(
                DuplicateCandidate(
                    invoice_number=old["invoice_number"],
                    vendor_name=old["vendor_name"],
                    total_amount=old["total_amount"],
                    issue_date=old["issue_date"],
                    reason="same_vendor_total_and_issue_date",
                    score=float(vendor_score),
                )
            )

    if any(c.score == 100.0 for c in candidates):
        status = "confirmed_duplicate"
    elif candidates:
        status = "possible_duplicate"
    else:
        status = "clear"

    return {
        "duplicate_status": status,
        "duplicate_candidates": [c.__dict__ for c in candidates],
    }
```

Later, PostgreSQL unique constraints should enforce this durably.

---

## Milestone 12: PO and delivery matching

Create:

```text
app/services/matching.py
tests/test_matching.py
```

Matching service should return mismatch reasons, not just `True/False`.

```python
from __future__ import annotations

from decimal import Decimal

from app.schemas.delivery_note import DeliveryNote
from app.schemas.invoice import Invoice
from app.schemas.purchase_order import PurchaseOrder


def close_money(a: Decimal, b: Decimal, tolerance: Decimal = Decimal("0.02")) -> bool:
    return abs(a - b) <= tolerance


def match_invoice_po_delivery(
    invoice: Invoice,
    purchase_order: PurchaseOrder | None,
    delivery_note: DeliveryNote | None,
) -> dict:
    reasons: list[str] = []

    if purchase_order is None:
        reasons.append("missing_purchase_order")
    else:
        if invoice.po_number != purchase_order.po_number:
            reasons.append("po_number_mismatch")

        if invoice.vendor.name.lower() != purchase_order.vendor.name.lower():
            reasons.append("vendor_mismatch")

        if invoice.currency != purchase_order.currency:
            reasons.append("currency_mismatch")

        if not close_money(invoice.subtotal, purchase_order.subtotal):
            reasons.append("subtotal_mismatch")

        if not close_money(invoice.tax_amount, purchase_order.tax_amount):
            reasons.append("tax_mismatch")

        if not close_money(invoice.total_amount, purchase_order.total_amount):
            reasons.append("total_mismatch")

    if delivery_note is None:
        reasons.append("missing_delivery_note")
    else:
        if invoice.po_number != delivery_note.po_number:
            reasons.append("delivery_po_number_mismatch")

        if delivery_note.delivery_status.lower() not in {"delivered", "complete", "received"}:
            reasons.append("delivery_not_complete")

    return {
        "match_status": "matched" if not reasons else "mismatch",
        "mismatch_reasons": reasons,
    }
```

---

## Milestone 13: JSONL audit logs

Create:

```text
app/services/audit.py
tests/test_audit.py
```

JSON Lines means each line is one valid JSON value, encoded as UTF-8, separated by a newline; this is perfect for append-only local audit logs and easy batch processing later. ([jsonlines.org][11])

Example:

```python
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


AUDIT_PATH = Path("data/processed/audit.jsonl")


def stable_hash(payload: Any) -> str:
    data = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def make_event_id(run_id: str, node_name: str, input_hash: str) -> str:
    raw = f"{run_id}:{node_name}:{input_hash}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:24]


def existing_event_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()

    ids = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            ids.add(json.loads(line)["event_id"])
    return ids


def write_audit_event(
    run_id: str,
    node_name: str,
    node_input: dict,
    output_summary: dict,
    risk_delta: dict | None = None,
    decision: dict | None = None,
    parser_or_model_name: str | None = None,
    errors: list[dict] | None = None,
    path: Path = AUDIT_PATH,
) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)

    input_hash = stable_hash(node_input)
    event_id = make_event_id(run_id, node_name, input_hash)

    if event_id in existing_event_ids(path):
        return {"event_id": event_id, "status": "already_written"}

    event = {
        "event_id": event_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "node_name": node_name,
        "input_hash": input_hash,
        "output_summary": output_summary,
        "risk_delta": risk_delta or {},
        "decision": decision or {},
        "parser_or_model_name": parser_or_model_name,
        "errors": errors or [],
    }

    # Do not include raw OCR/parser text, API keys, IBAN full values, or secrets here.
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, default=str) + "\n")

    return event
```

---

## Milestone 14: ERP mock

Create:

```text
app/services/erp_mock.py
tests/test_erp_mock.py
```

Example:

```python
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4


def post_invoice_to_erp_mock(
    run_id: str,
    invoice: dict | None,
    approval: dict | None,
    risk_level: str,
    duplicate_result: dict,
    match_result: dict,
    validation_errors: list[dict],
    business_rule_errors: list[dict],
) -> dict:
    if invoice is None:
        return {"status": "rejected", "rejection_reason": "missing_invoice"}

    if validation_errors:
        return {"status": "rejected", "rejection_reason": "invalid_schema"}

    if not invoice.get("invoice_number"):
        return {"status": "rejected", "rejection_reason": "missing_invoice_number"}

    if not invoice.get("vendor"):
        return {"status": "rejected", "rejection_reason": "missing_vendor"}

    if duplicate_result.get("duplicate_status") == "confirmed_duplicate":
        return {"status": "rejected", "rejection_reason": "duplicate_invoice"}

    if "total_mismatch" in match_result.get("mismatch_reasons", []):
        if not approval or approval.get("status") not in {"human_approved", "approved"}:
            return {"status": "rejected", "rejection_reason": "total_mismatch_requires_approval"}

    if risk_level == "high":
        if not approval or approval.get("status") not in {"human_approved", "approved"}:
            return {"status": "rejected", "rejection_reason": "high_risk_requires_approval"}

    return {
        "status": "posted",
        "erp_post_id": f"ERP-{uuid4()}",
        "posted_at": datetime.now(timezone.utc).isoformat(),
        "rejection_reason": None,
    }
```

---

# Phase 8 — Evaluation fixtures

## Milestone 15: Add evaluation data

Create:

```text
data/eval/invoices/
data/eval/purchase_orders/
data/eval/delivery_notes/
data/eval/ground_truth.jsonl
tests/test_eval_smoke.py
```

Each line in `ground_truth.jsonl` should describe one scenario:

```json
{"case_id":"clean_001","invoice_path":"data/eval/invoices/clean_001.pdf","po_path":"data/eval/purchase_orders/po_001.pdf","delivery_note_path":"data/eval/delivery_notes/dn_001.pdf","expected_invoice_number":"INV-001","expected_vendor":"ACME BV","expected_total_amount":"121.00","expected_duplicate_status":"clear","expected_match_status":"matched","expected_requires_human_approval":false}
```

Add cases:

```text
clean invoice with matching PO
invoice missing PO
duplicate invoice
total mismatch
vendor mismatch
handwritten correction
missing IBAN
delivery quantity mismatch
```

Metrics:

```text
invoice_number_accuracy
vendor_accuracy
total_amount_accuracy
line_item_accuracy
po_match_accuracy
duplicate_precision
duplicate_recall
approval_routing_accuracy
hallucinated_field_rate
```

For beginner MVP, implement evals as normal pytest first. Add MLflow/DeepEval later.

---

# Phase 9 — FastAPI wrapper

## Milestone 16: Add FastAPI

Install:

```bash
uv add fastapi uvicorn python-multipart
```

FastAPI’s official file upload docs use `File` and `UploadFile`, and note that `python-multipart` is required because uploaded files are form data. ([FastAPI][12])

Create:

```text
app/api/main.py
app/api/routes.py
tests/test_api.py
```

Example:

```python
from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, UploadFile

from app.graph.workflow import build_graph

app = FastAPI(title="Invoice-to-Pay Agent")

RUNS: dict[str, dict] = {}


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/runs")
async def create_run(files: list[UploadFile] = File(...)) -> dict:
    run_id = str(uuid4())
    upload_dir = Path("data/uploads") / run_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    uploaded_documents = []

    for file in files:
        path = upload_dir / file.filename
        path.write_bytes(await file.read())
        uploaded_documents.append(
            {
                "path": str(path),
                "filename": file.filename,
                "document_type": "unknown",
            }
        )

    graph = build_graph()
    result = graph.invoke(
        {"run_id": run_id, "uploaded_documents": uploaded_documents},
        config={"configurable": {"thread_id": run_id}},
    )

    RUNS[run_id] = result

    if result.get("requires_human_approval"):
        status = "requires_approval"
    elif (result.get("erp_result") or {}).get("status") == "posted":
        status = "posted"
    else:
        status = "completed"

    return {"run_id": run_id, "status": status, "result": result}


@app.get("/runs/{run_id}")
def get_run(run_id: str) -> dict:
    return RUNS.get(run_id, {"status": "not_found"})


@app.post("/runs/{run_id}/approve")
def approve_run(run_id: str) -> dict:
    # Later: resume graph with Command(resume={...})
    return {"run_id": run_id, "status": "approval_resume_not_yet_implemented"}


@app.post("/runs/{run_id}/reject")
def reject_run(run_id: str) -> dict:
    # Later: resume graph with Command(resume={...})
    return {"run_id": run_id, "status": "rejection_resume_not_yet_implemented"}


@app.get("/runs/{run_id}/audit")
def get_audit(run_id: str) -> dict:
    audit_path = Path("data/processed/audit.jsonl")
    if not audit_path.exists():
        return {"run_id": run_id, "events": []}

    events = [
        line
        for line in audit_path.read_text(encoding="utf-8").splitlines()
        if f'"run_id": "{run_id}"' in line
    ]
    return {"run_id": run_id, "events": events}
```

Run:

```bash
uv run uvicorn app.api.main:app --reload
```

Keep routes thin. The API should not decide AP outcomes. It should save files, call the graph, return status.

---

# Phase 10 — Persistence and observability

## Milestone 17: PostgreSQL persistence

Install when this milestone starts:

```bash
uv add sqlalchemy psycopg[binary]
```

SQLAlchemy’s ORM quickstart covers declarative models, `mapped_column`, engines, and table creation. ([SQLAlchemy Documentation][13])

Tables:

```text
ap_runs
documents
parsed_documents
invoices
purchase_orders
delivery_notes
duplicate_candidates
approval_tasks
erp_posts
audit_events
```

Start with models only. Add Alembic later after schemas stabilize.

Important constraints:

```text
unique(vendor_name_normalized, invoice_number)
unique(vendor_name_normalized, total_amount, issue_date)
```

But keep JSONL audit logs too. Database persistence is for app state; JSONL audit is a local artifact trail.

---

## Milestone 18: MLflow

Install when needed:

```bash
uv add mlflow
```

MLflow Tracking logs parameters, metrics, code versions, and output files/artifacts, which fits parser versions, schema versions, eval reports, latency, and approval-routing metrics. ([MLflow AI Platform][14])

Track:

```text
parser_version
schema_version
document_type
field_accuracy
latency
validation_failures
approval_routing_accuracy
parsed_documents.jsonl
eval_report.json
confusion_matrix.json
audit_sample.jsonl
```

Example:

```python
import mlflow

with mlflow.start_run(run_name=f"ap-eval-{run_id}"):
    mlflow.log_param("schema_version", "v1")
    mlflow.log_param("parser", "liteparse")
    mlflow.log_metric("invoice_number_accuracy", 0.95)
    mlflow.log_artifact("data/processed/eval_report.json")
```

---

## Milestone 19: GenAI evals

Choose one:

```text
Option A: MLflow GenAI eval
Option B: DeepEval
```

MLflow’s GenAI evaluation docs are aimed at evaluating LLMs and agents throughout development and production. ([MLflow AI Platform][15]) DeepEval provides LLM test cases and pytest-style evaluation workflows. ([DeepEval][16])

For this project, start with deterministic pytest evals. Add GenAI evals only when you introduce LLM-based extraction or reasoning.

Test:

```text
duplicate invoice routes to approval/rejection
total mismatch rejects unless approved
missing IBAN is not invented
handwriting warning is preserved
no ERP post without required approval
audit log survives resume
```

---

## Milestone 20: Tracing

Choose:

```text
Langfuse for LLM/agent-friendly traces
OpenTelemetry for vendor-neutral tracing
```

OpenTelemetry Python docs cover spans, attributes, exceptions, and environment-variable configuration. ([OpenTelemetry][17]) Langfuse has LangChain/LangGraph integrations and can capture LangGraph traces through callbacks / OTEL-style tracing. ([Langfuse][18])

Make tracing optional:

```text
TRACING_ENABLED=false
TRACE_BACKEND=langfuse
```

Tests must pass with tracing disabled.

Trace:

```text
run_id
node name
node duration
parser latency
validation failures
risk score
approval decision
ERP result
```

---

# Phase 11 — Dashboard, Docker, CI, MinIO, cloud, analytics

## Milestone 21: Streamlit dashboard

Install:

```bash
uv add streamlit requests
```

Streamlit has `st.file_uploader` for uploads and an app testing framework for headless tests. ([Streamlit Docs][19])

Pages:

```text
upload page
extracted-field review
PO / delivery match view
duplicate warning view
approve / reject action
audit timeline
eval metrics view
```

Rule: Streamlit calls FastAPI. It does not call services directly.

---

## Milestone 22: Docker Compose

Create:

```text
docker-compose.yml
.env.example
```

Docker Compose services define containers, ports, environment variables, and volumes; named volumes are used for persistent data. ([Docker Documentation][20])

Skeleton:

```yaml
services:
  api:
    build: .
    command: uv run uvicorn app.api.main:app --host 0.0.0.0 --port 8000
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./data:/app/data

  postgres:
    image: postgres:18
    environment:
      POSTGRES_USER: ap
      POSTGRES_PASSWORD: ap
      POSTGRES_DB: invoice_to_pay
    volumes:
      - postgres_data:/var/lib/postgresql/data

  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio_data:/data

volumes:
  postgres_data:
  minio_data:
```

---

## Milestone 23: GitHub Actions CI

Create:

```text
.github/workflows/ci.yml
```

GitHub’s Python CI guide covers building and testing Python projects, and uv has an official GitHub Actions integration through `astral-sh/setup-uv`. ([GitHub Docs][21])

Example:

```yaml
name: CI

on:
  push:
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v6

      - uses: astral-sh/setup-uv@v6

      - name: Set up Python
        run: uv python install 3.11

      - name: Sync dependencies
        run: uv sync

      - name: Ruff
        run: uv run ruff check app tests

      - name: Type check
        run: uv run mypy app

      - name: Pytest
        run: uv run pytest

      - name: Compile
        run: uv run python -m compileall app tests
```

Mock LiteParse and MinerU in normal CI. Heavy parser tests should be opt-in.

---

## Milestone 24: MinIO storage

Install:

```bash
uv add minio
```

The MinIO Python SDK provides high-level APIs for S3-compatible object storage, including bucket creation and object upload. ([MinIO AIStor Documentation][22])

Buckets:

```text
raw-documents
parsed-documents
audit-artifacts
eval-fixtures
```

Object key pattern:

```text
{run_id}/raw/{filename}
{run_id}/parsed/{parser_name}/{artifact}
{run_id}/audit/audit.jsonl
```

Keep local filesystem first. Add MinIO after the graph works.

---

## Milestone 25: Cloud docs

Create:

```text
docs/cloud_mapping.md
```

Keep it short:

```md
# Cloud Mapping

| Local | Azure | GCP |
|---|---|---|
| MinIO | Azure Data Lake | Google Cloud Storage |
| PostgreSQL | Azure PostgreSQL | Cloud SQL |
| FastAPI | Azure Container Apps | GKE |
| MLflow | Databricks MLflow | Vertex/managed MLflow equivalent |
| Batch jobs | Databricks/Spark | Dataproc/Spark |
| Tracing | Managed OTEL/Langfuse | Managed OTEL/Langfuse |
```

This is architecture documentation, not a deployment novel.

---

## Milestone 26: PySpark analytics

Install only when needed:

```bash
uv add pyspark
```

PySpark DataFrames support reading/writing data and aggregations such as group-by reports; Parquet is a compact efficient format for Spark workloads. ([Apache Spark][23])

Reports:

```text
monthly duplicate report
vendor exception report
approval delay report
field extraction quality by vendor
invoice mismatch trend
```

Example report script:

```python
from pyspark.sql import SparkSession
from pyspark.sql.functions import count

spark = SparkSession.builder.appName("ap-analytics").getOrCreate()

audit = spark.read.json("data/processed/audit.jsonl")

vendor_exceptions = (
    audit
    .where("node_name = 'risk_score'")
    .groupBy("run_id")
    .agg(count("*").alias("risk_events"))
)

vendor_exceptions.show()
```

---

# Final definition of done for every milestone

Before marking a milestone done, run:

```bash
uv run pytest
uv run python -m compileall app tests
git status --short
```

Then write a short note:

```md
## Milestone X done

Implemented:
- ...

Tests:
- uv run pytest passed
- uv run python -m compileall app tests passed

Known issues:
- ...

Git status:
- ...

Commit:
- feat(...): ...
```

Use conventional commit messages:

```text
feat(parser): add parsed document contract
feat(graph): wire invoice-to-pay workflow
feat(risk): score AP exception risk
feat(audit): write idempotent JSONL audit events
test(graph): cover approval resume path
```

The most important beginner rule: **make the graph boring, typed, testable, and resumable first.** Then add the shiny stuff. The shiny stuff is only useful if the graph is trustworthy.

[1]: https://docs.langchain.com/oss/python/langgraph/graph-api "https://docs.langchain.com/oss/python/langgraph/graph-api"
[2]: https://developers.llamaindex.ai/liteparse/getting_started/ "https://developers.llamaindex.ai/liteparse/getting_started/"
[3]: https://pydantic.dev/docs/validation/2.0/usage/model_config/ "https://pydantic.dev/docs/validation/2.0/usage/model_config/"
[4]: https://docs.astral.sh/uv/reference/cli/ "https://docs.astral.sh/uv/reference/cli/"
[5]: https://opendatalab.github.io/MinerU/quick_start/ "https://opendatalab.github.io/MinerU/quick_start/"
[6]: https://github.com/run-llama/liteparse/blob/main/packages/python/README.md "https://github.com/run-llama/liteparse/blob/main/packages/python/README.md"
[7]: https://pydantic.dev/docs/validation/2.0/usage/validators/ "https://pydantic.dev/docs/validation/2.0/usage/validators/"
[8]: https://reference.langchain.com/python/langgraph/graphs "https://reference.langchain.com/python/langgraph/graphs"
[9]: https://docs.langchain.com/oss/python/langgraph/interrupts "https://docs.langchain.com/oss/python/langgraph/interrupts"
[10]: https://github.com/rapidfuzz/RapidFuzz "https://github.com/rapidfuzz/RapidFuzz"
[11]: https://jsonlines.org/ "https://jsonlines.org/"
[12]: https://fastapi.tiangolo.com/tutorial/request-files/ "https://fastapi.tiangolo.com/tutorial/request-files/"
[13]: https://docs.sqlalchemy.org/orm/quickstart.html "https://docs.sqlalchemy.org/orm/quickstart.html"
[14]: https://mlflow.org/docs/latest/ml/tracking/ "https://mlflow.org/docs/latest/ml/tracking/"
[15]: https://mlflow.org/docs/latest/genai/eval-monitor/ "https://mlflow.org/docs/latest/genai/eval-monitor/"
[16]: https://deepeval.com/docs/evaluation-test-cases "https://deepeval.com/docs/evaluation-test-cases"
[17]: https://opentelemetry.io/docs/languages/python/instrumentation/ "https://opentelemetry.io/docs/languages/python/instrumentation/"
[18]: https://langfuse.com/integrations/frameworks/langchain "https://langfuse.com/integrations/frameworks/langchain"
[19]: https://docs.streamlit.io/develop/api-reference/widgets/st.file_uploader "https://docs.streamlit.io/develop/api-reference/widgets/st.file_uploader"
[20]: https://docs.docker.com/reference/compose-file/services/ "https://docs.docker.com/reference/compose-file/services/"
[21]: https://docs.github.com/actions/guides/building-and-testing-python "https://docs.github.com/actions/guides/building-and-testing-python"
[22]: https://docs.min.io/aistor/developers/sdk/python/api/ "https://docs.min.io/aistor/developers/sdk/python/api/"
[23]: https://spark.apache.org/docs/latest/api/python/getting_started/quickstart_df.html "https://spark.apache.org/docs/latest/api/python/getting_started/quickstart_df.html"

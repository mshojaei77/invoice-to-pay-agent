"""Tests for ``app.services.csv_export`` — deterministic CSV export of ERP posting payload.

@file test_csv_export.py
@brief Verify that ``export_erp_payload_to_csv`` writes a correct, deterministic,
       and field-sorted CSV from a ``build_erp_sync_plan`` result.
@context Issue #3 — CSV export for vendor-bill field inspection.
@strategy Reuse the same ``build_erp_sync_plan`` call pattern as
          ``test_erp_integration.py``, then read back the CSV and assert field
          presence, order, values, and determinism.
@keywords test, csv, export, erp, deterministic
"""

# GREP_SUMMARY: test_csv_export / export_erp_payload_to_csv / build_erp_sync_plan

from __future__ import annotations

import csv
import io
import json
from pathlib import Path

from app.services.csv_export import export_erp_payload_to_csv
from app.services.erp_integration import build_erp_sync_plan

# ---------------------------------------------------------------------------
# Shared test input — mirrors test_erp_integration.py
# ---------------------------------------------------------------------------
BASE_UPLOADED_DOCUMENTS = [
    {"filename": "invoice.pdf", "path": "invoice.pdf", "document_type": "invoice"},
]

BASE_GL_CODING = {
    "gl_account": "5400-postage",
    "cost_center": "operations",
    "allocation": [],
}

BASE_COMPLIANCE = {
    "compliance_status": "ready",
    "retention_class": "financial_record",
}

BASE_PAYMENT_PLAN = {
    "recommendation": "pay_by_discount_window",
    "target_payment_date": "2026-07-01",
}

BASE_ACCOUNTING_PROFILE = {
    "selected_platform": "exact",
    "connector_contract": {"capabilities": ["post_purchase_invoice"]},
}

BASE_MULTI_COMPANY = {"entity_code": "eu_entity"}

BASE_INDUSTRY_POLICY = {
    "industry": "manufacturing",
    "vat_policy": "standard_vat_code_required",
}


def _build_erp_sync_plan_kwargs() -> dict:
    """Return a standard set of keyword arguments for ``build_erp_sync_plan``."""
    return {
        "run_id": "run-test-csv-export",
        "uploaded_documents": BASE_UPLOADED_DOCUMENTS,
        "gl_coding_result": BASE_GL_CODING,
        "compliance_result": BASE_COMPLIANCE,
        "payment_plan": BASE_PAYMENT_PLAN,
        "accounting_platform_profile": BASE_ACCOUNTING_PROFILE,
        "multi_company_result": BASE_MULTI_COMPANY,
        "industry_policy_result": BASE_INDUSTRY_POLICY,
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_csv_has_header_and_is_deterministic(tmp_path: Path) -> None:
    """Check header row, field presence, and that identical inputs yield
    identical output (determinism)."""
    # --- Arrange -----------------------------------------------------------
    kwargs = _build_erp_sync_plan_kwargs()
    plan1 = build_erp_sync_plan(**kwargs)
    plan2 = build_erp_sync_plan(**kwargs)
    out1 = tmp_path / "out1.csv"
    out2 = tmp_path / "out2.csv"

    # --- Act ---------------------------------------------------------------
    result1 = export_erp_payload_to_csv(plan1, out1)
    _ = export_erp_payload_to_csv(plan2, out2)

    # --- Assert file creation ----------------------------------------------
    assert result1 == out1.resolve(), "Returned path must match the input path"
    assert out1.exists(), "CSV file must be created"
    assert out2.exists(), "CSV file must be created"

    # --- Assert determinism ------------------------------------------------
    assert out1.read_text(encoding="utf-8") == out2.read_text(
        encoding="utf-8"
    ), "Two runs with identical data must produce identical CSV"

    # --- Assert header -----------------------------------------------------
    content = out1.read_text(encoding="utf-8")
    lines = content.strip().splitlines()
    header = lines[0]
    assert header == "field,value", f"Expected header 'field,value', got {header!r}"

    # --- Parse CSV and check fields ----------------------------------------
    reader = csv.DictReader(io.StringIO(content))
    rows = list(reader)
    field_values = {row["field"]: row["value"] for row in rows}

    # Core fields are present
    assert "gl_account" in field_values
    assert "entity_code" in field_values
    assert "document_refs" in field_values
    assert "payment_hold_until_final_approval" in field_values

    # Core field values
    assert field_values["gl_account"] == "5400-postage"
    assert field_values["entity_code"] == "eu_entity"
    assert field_values["payment_hold_until_final_approval"] == "True"

    # --- Assert rows are sorted alphabetically -----------------------------
    field_names = [row["field"] for row in rows]
    assert field_names == sorted(field_names), "CSV rows must be sorted by field"


def test_csv_contains_all_expected_fields(tmp_path: Path) -> None:
    """Verify every top-level key from posting_payload appears in the CSV."""
    kwargs = _build_erp_sync_plan_kwargs()
    plan = build_erp_sync_plan(**kwargs)
    expected_keys = set(plan["posting_payload"].keys())

    out = tmp_path / "out.csv"
    export_erp_payload_to_csv(plan, out)

    content = out.read_text(encoding="utf-8")
    reader = csv.DictReader(io.StringIO(content))
    actual_keys = {row["field"] for row in reader}

    # Every expected key (or its flattened children) should be present.
    # Top-level simple keys map directly; nested keys are flattened.
    # Exception: an empty dict {} produces no rows, so we tolerate its absence.
    payload = plan["posting_payload"]
    for key in expected_keys:
        if isinstance(payload[key], dict) and not payload[key]:
            # Empty dict → no rows produced; skip check.
            continue
        if not any(k.startswith(key) for k in actual_keys):
            # If it has no nested children, it should appear verbatim
            # (e.g. empty list -> JSON "[]")
            assert key in actual_keys, f"Expected key {key!r} not found in {sorted(actual_keys)}"


def test_csv_preserves_list_data_as_json(tmp_path: Path) -> None:
    """Lists should be serialised as JSON arrays, not flattened further."""
    kwargs = _build_erp_sync_plan_kwargs()
    plan = build_erp_sync_plan(**kwargs)

    out = tmp_path / "out.csv"
    export_erp_payload_to_csv(plan, out)

    content = out.read_text(encoding="utf-8")
    reader = csv.DictReader(io.StringIO(content))
    field_values = {row["field"]: row["value"] for row in reader}

    # document_refs is a list — verify it's valid JSON
    doc_refs_raw = field_values["document_refs"]
    doc_refs = json.loads(doc_refs_raw)
    assert isinstance(doc_refs, list)
    assert doc_refs[0]["filename"] == "invoice.pdf"


def test_csv_empty_payload_graceful(tmp_path: Path) -> None:
    """Empty posting_payload should still produce a valid CSV with just the header."""
    out = tmp_path / "empty.csv"
    export_erp_payload_to_csv({"posting_payload": {}}, out)

    content = out.read_text(encoding="utf-8").strip()
    assert content == "field,value"


def test_csv_missing_posting_payload_graceful(tmp_path: Path) -> None:
    """Missing posting_payload key should be treated as empty dict."""
    out = tmp_path / "missing.csv"
    export_erp_payload_to_csv({}, out)

    content = out.read_text(encoding="utf-8").strip()
    assert content == "field,value"

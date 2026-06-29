"""CSV export for ERP posting payload — deterministic, field-value format.

@file csv_export.py
@brief Deterministic CSV export of ``posting_payload`` for inspection without a live ERP connector.
@context Part of the invoice-to-pay agent. Consumed by users and downstream
         automation to inspect vendor bill fields (issue #3).
@strategy Flatten nested dicts with dot-separated keys, serialise lists as JSON
          arrays, sort by key for deterministic output.
@keywords csv, export, erp, deterministic, flatten
"""

# GREP_SUMMARY: export_erp_payload_to_csv / _flatten / csv / posting_payload

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


# region FUNC__flatten


def _flatten(
    d: dict[str, Any],
    parent_key: str = "",
    sep: str = ".",
) -> dict[str, str]:
    """Flatten a nested dict into dot-separated keys with string values.

    @startcontract
    @brief Recursively reduce a nested dict to a single-level dict of strings.
    @invariant Keys in the result never contain the separator before the first level.
    @invariant Lists are always serialised as JSON arrays (never flattened further).
    @param d       Source dictionary (nested allowed).
    @param parent_key  Key prefix accumulated during recursion (internal).
    @param sep         Separator between key levels (default ".").
    @return dict[str, str] — flat key → string value mapping.
    @endcontract
    """
    items: dict[str, str] = {}
    for key, value in d.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key
        if isinstance(value, dict):
            items.update(_flatten(value, new_key, sep=sep))
        elif isinstance(value, list):
            items[new_key] = json.dumps(value, sort_keys=True, default=str, ensure_ascii=False)
        elif value is None:
            items[new_key] = ""
        else:
            items[new_key] = str(value)
    return items


# endregion FUNC__flatten

# region FUNC_export_erp_payload_to_csv


def export_erp_payload_to_csv(
    erp_sync_plan: dict[str, Any],
    output_path: str | Path = "erp_posting_payload.csv",
) -> Path:
    """Write the ``posting_payload`` section of an ERP sync plan to a
    deterministic CSV file (field, value — sorted by field).

    @startcontract
    @brief Accept an ERP sync-plan dict and write a deterministic CSV.
    @invariant Output CSV has exactly two columns: ``field`` and ``value``.
    @invariant Rows are sorted alphabetically by the ``field`` column.
    @invariant The file is written with UTF-8 encoding and CRLF line endings.
    @param erp_sync_plan The dict returned by
           ``app.services.erp_integration.build_erp_sync_plan``.
    @param output_path   Where to write the CSV (default ``erp_posting_payload.csv``).
    @return Absolute ``Path`` of the written file.
    @endcontract

    Args:
        erp_sync_plan: The ERP sync-plan dictionary.
        output_path: Destination file path.

    Returns:
        Absolute path of the written CSV file.
    """
    # [csv_export] [BELIEF: posting_payload may be absent → fallback to {}]
    # | [INPUT: erp_sync_plan dict] | [EXPECTING: valid CSV at output_path]
    payload = erp_sync_plan.get("posting_payload", {})
    flat = _flatten(payload)

    out = Path(output_path)
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["field", "value"])
        for key in sorted(flat):
            writer.writerow([key, flat[key]])

    return out.resolve()


# endregion FUNC_export_erp_payload_to_csv

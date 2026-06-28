# Invoice-to-Pay Agent

Controls-first accounts payable automation built with LangGraph, FastAPI, strict Pydantic contracts, parser routing, risk scoring, approval interrupts, ERP mock posting, audit logs, and pytest-backed scenarios.

This is not a "send a PDF to an LLM" demo. It is a reproducible prototype for the messy middle of invoice operations: validation, duplicate risk, PO and delivery-note matching, approval routing, and auditability before anything gets posted.

## Table of Contents

- [Why This Exists](#why-this-exists)
- [Features](#features)
- [Current Status](#current-status)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [API](#api)
- [Testing](#testing)
- [Evaluation Data](#evaluation-data)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [Security](#security)
- [License](#license)

## Why This Exists

Accounts payable teams do not lose time only on extraction. They lose time on exceptions, duplicate checks, incomplete support, vendor mismatches, approval chasing, and audit reconstruction.

This project models the decision path finance teams actually care about:

- Was the invoice captured into a typed AP contract?
- Is there a purchase order?
- Is there proof of delivery?
- Does the invoice match PO and delivery evidence?
- Is this a duplicate or possible duplicate?
- Are payment-critical fields missing or suspicious?
- Can low-risk invoices move automatically?
- Can medium/high-risk invoices pause for a human?
- Can an auditor inspect the run after the fact?

The answer is encoded as a graph, not hidden in a prompt.

## Features

- FastAPI service with health, run creation, run lookup, approval, rejection, and audit endpoints.
- LangGraph workflow with in-memory checkpointing and a single approval interrupt.
- Strict Pydantic v2 schemas for invoices, purchase orders, delivery notes, parsed documents, and audit records.
- Parser routing service designed for LiteParse-first and MinerU fallback decisions.
- Deterministic business validation, duplicate detection, invoice/PO/delivery matching, and risk scoring.
- ERP mock service for controlled post/reject outcomes.
- Demo scripts for command-line invoice-to-pay scenarios.
- Real PDF sample corpus and JSONL eval manifest for smoke-level scenario coverage.
- Pytest suite covering API, graph, parser routing, schemas, validation, matching, duplicate handling, audit, and eval smoke tests.

## Current Status

This is an early but runnable prototype.

Implemented:

- `uv`-managed Python 3.11 project.
- End-to-end graph execution for deterministic AP scenarios.
- API and CLI demo paths.
- Approval and rejection resume flow.
- Audit log helper behavior.
- Test coverage across the main service and workflow boundaries.

Known limitations:

- Parser graph nodes are still deterministic/stub oriented. Parser adapters and routing services exist, but real LiteParse/MinerU extraction is not yet wired end-to-end through graph execution.
- Active API runs use in-memory storage and are lost when the server restarts.
- ERP integration is intentionally mocked.
- No review UI is included yet.
- The repository currently documents MIT licensing, but a root `LICENSE` file should be added before publishing as a polished open source release.

## Architecture

```text
Upload invoice / PO / delivery note
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
```

The graph shape is the product architecture:

- Nodes before `approval_gate` gather evidence and calculate risk.
- `approval_gate` is the single human interrupt for medium/high-risk runs.
- Nodes after approval perform the controlled post or reject outcome.
- Every run has a `run_id` so API state, approval, ERP result, and audit records can be correlated.

### Risk Model

Risk output is intentionally simple and inspectable:

```text
risk_level: low | medium | high
risk_score: float
risk_reasons: list[str]
requires_human_approval: bool
```

Current risk triggers include:

- Schema validation errors.
- Missing PO.
- Missing delivery note.
- Missing or invalid payment-critical vendor fields.
- Handwritten correction signal.
- Low parser confidence signal.
- Possible or confirmed duplicate.
- PO, vendor, delivery, quantity, subtotal, tax, or total mismatches.

Low-risk runs can auto-approve. Medium/high-risk runs pause at the LangGraph interrupt and must be approved or rejected through the API or a future UI.

## Quick Start

### Prerequisites

- Python 3.11 or newer.
- [`uv`](https://docs.astral.sh/uv/) for dependency management.

Install dependencies:

```bash
uv sync
```

Run the test suite:

```bash
uv run pytest
```

Run a low-risk invoice-to-pay scenario:

```bash
uv run python scripts/run_demo.py --invoice samples/invoice_001_canada_post_sample.pdf --po samples/purchase_order_001_polychemtex.pdf --delivery-note samples/delivery_note_001_bunker_receipt.pdf
```

Choose a parser and write a Markdown report:

```bash
uv run python scripts/run_demo.py --invoice samples/invoice_001_canada_post_sample.pdf --po samples/purchase_order_001_polychemtex.pdf --delivery-note samples/delivery_note_001_bunker_receipt.pdf --parser liteparse --output-md data/processed/reports/demo-liteparse.md
```

`--parser` accepts `liteparse` or `mineru`; `MinerU_` is normalized to `mineru`.
When `--output-md` is omitted, the demo writes `data/processed/reports/<run_id>.md`.

Expected shape:

```text
run_id=<generated-id>
final_status=completed
risk_level=low
erp_status=posted
audit_log=data/processed/audit.jsonl
markdown_report=data/processed/reports/<run_id>.md
```

Run a missing-support scenario that requires approval:

```bash
uv run python scripts/run_demo.py --invoice samples/invoice_002_tax_sample_local_supply.pdf
```

Expected shape:

```text
run_id=<generated-id>
final_status=requires_approval
erp_status=not_posted
audit_log=data/processed/audit.jsonl
```

## Usage

### Start the API

```bash
uv run invoice-to-pay-agent
```

The server listens on `http://localhost:8000`.

Health check:

```bash
curl.exe http://localhost:8000/health
```

Expected response:

```json
{"status":"ok"}
```

### Submit Documents

Open a second terminal while the API server is running:

```bash
curl.exe -X POST http://localhost:8000/runs -F "files=@samples/invoice_001_canada_post_sample.pdf" -F "files=@samples/purchase_order_001_polychemtex.pdf" -F "files=@samples/delivery_note_001_bunker_receipt.pdf"
```

Important response fields:

```json
{
  "run_id": "...",
  "status": "posted",
  "result": {
    "risk_level": "low",
    "erp_result": {
      "status": "posted"
    }
  }
}
```

### Approval Flow

Submit an invoice without PO or delivery support:

```bash
curl.exe -X POST http://localhost:8000/runs -F "files=@samples/invoice_002_tax_sample_local_supply.pdf"
```

Expected status:

```json
{
  "run_id": "...",
  "status": "requires_approval"
}
```

Approve the waiting run:

```bash
curl.exe -X POST http://localhost:8000/runs/YOUR_RUN_ID_HERE/approve
```

Reject the waiting run:

```bash
curl.exe -X POST http://localhost:8000/runs/YOUR_RUN_ID_HERE/reject
```

Replace `YOUR_RUN_ID_HERE` with the actual `run_id` from the create-run response.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Liveness check. |
| `POST` | `/runs` | Upload one or more AP documents and start a graph run. |
| `GET` | `/runs/{run_id}` | Inspect latest in-memory run state. |
| `POST` | `/runs/{run_id}/approve` | Resume a waiting run with approval. |
| `POST` | `/runs/{run_id}/reject` | Resume a waiting run with rejection. |
| `GET` | `/runs/{run_id}/audit` | Return matching audit events when present. |

Interactive API docs are available while the server is running:

```text
http://localhost:8000/docs
```

## Testing

Run all tests:

```bash
uv run pytest
```

Run one focused test module:

```bash
uv run pytest tests/test_graph.py
```

Check Python compilation:

```bash
uv run python -m compileall app tests scripts
```

The suite is designed to keep the prototype honest at the contract and workflow level. It currently covers:

- API run, approval, rejection, and audit behavior.
- Graph state transitions.
- Pydantic schema validation.
- Parser route decisions.
- Business-rule errors.
- Risk scoring thresholds and reasons.
- Duplicate outcomes.
- Invoice, PO, and delivery-note matching.
- Eval manifest smoke checks.

## Evaluation Data

The sample corpus lives in `samples/`, with scenario metadata in `samples/eval_manifest.jsonl`.

Current eval coverage includes:

- Clean invoice with PO and delivery note.
- Invoice missing PO support.
- Handwritten invoice scenario.
- International invoice scenario.
- Non-invoice statement scenario.

Future eval work should measure:

- Invoice number accuracy.
- Vendor accuracy.
- Total and tax accuracy.
- Line-item accuracy.
- PO match accuracy.
- Delivery match accuracy.
- Duplicate precision and recall.
- Approval routing correctness.
- ERP post/reject correctness.
- Hallucinated-field rate.
- Parser fallback rate and latency.

## Project Structure

```text
app/
  api/          FastAPI routes and app wiring
  graph/        LangGraph state, nodes, workflow construction
  schemas/      Strict AP contracts for invoices, POs, delivery notes, parser output, audit
  services/     parser routing, extraction, validation, matching, duplicate checks, risk, ERP mock, audit
  storage/      placeholder boundary for durable storage
  evals/        evaluation package boundary

scripts/
  run_demo.py      run an AP graph scenario from local file paths
  approve_demo.py  exercise approval-oriented flow
  reject_demo.py   exercise rejection-oriented flow

samples/
  *.pdf             sample invoices, POs, delivery notes, and reference documents
  eval_manifest.jsonl

tests/
  API, graph, schema, parser, risk, matching, duplicate, audit, and eval smoke tests
```

## Configuration

The current prototype does not require secrets for deterministic demo execution.

`.env.example` is intentionally minimal:

```text
# OpenAI and storage settings will be added when LLM extraction and persistence are implemented.
```

Use `pyproject.toml` and `uv.lock` as the source of truth for dependencies. Add packages with:

```bash
uv add <package>
```

## Parser Strategy

The intended parser policy is conservative:

- LiteParse first for clean digital PDFs and fast extraction.
- MinerU first for images, receipts, scans, dense tables, handwriting, stamps, and signatures.
- MinerU retry when LiteParse output has low confidence, validation errors, payment-critical mismatches, or complex-document warnings.

The point is not parser maximalism. The point is routing documents by operational risk and keeping parser choice explainable.

## Design Principles

- Keep controls explicit.
- Keep API routes thin.
- Keep business logic in services.
- Keep graph nodes small and inspectable.
- Use strict schemas before decisions.
- Use human interrupts only where business approval is required.
- Treat parser fallback as a risk-control mechanism.
- Prefer deterministic tests and scenario evals over impressive demos.

## Roadmap

Near-term:

- Wire real LiteParse and MinerU adapters into graph execution.
- Persist runs, uploaded documents, parser outputs, approvals, and ERP mock results.
- Write audit events from graph nodes, not only helper tests.
- Maintain the downloaded sample corpus under `samples/` and expand `samples/eval_manifest.jsonl`.
- Add CI for tests and compile checks.
- Add a root `LICENSE` file for MIT release hygiene.

Product track:

- Streamlit or lightweight web approval console.
- Durable Postgres storage.
- MinIO or object-storage document archive.
- Vendor and PO master-data mocks.
- Exception queue and reviewer assignment.
- Batch analytics for duplicate trends and approval delays.

AI engineering track:

- Parser-version tracking.
- MLflow or equivalent eval tracking.
- Langfuse/OpenTelemetry tracing.
- Scenario benchmark script for clean, missing-support, parser-challenge, and rejection flows.
- Documented parser confidence and fallback metrics.

Enterprise track:

- ERP connector interface.
- Role-based approval policy.
- Audit export.
- Cloud deployment guide.
- Data retention and PII handling notes.

## Contributing

Contributions are welcome while the project is still in prototype stage. Please keep changes aligned with the existing architecture:

- Use `uv` for dependency changes and commit both `pyproject.toml` and `uv.lock`.
- Keep API routes thin and move business logic into `app/services/`.
- Keep graph nodes small and inspectable.
- Add or update tests for behavior changes.
- Prefer scenario-level evidence for workflow changes.
- Do not replace deterministic controls with opaque LLM decisions.

Before opening a pull request, run:

```bash
uv run pytest
uv run python -m compileall app tests scripts
```

## Security

This prototype processes financial documents and may contain sensitive vendor, bank, tax, or payment details in real deployments.

- Do not commit real invoices, credentials, bank details, or customer data.
- Keep secrets out of source control and use environment variables when integrations are added.
- Treat uploaded documents and audit logs as sensitive operational data.
- Report security issues privately to the maintainer instead of opening a public issue.

## References

- LiteParse: <https://github.com/run-llama/liteparse>
- MinerU: <https://github.com/opendatalab/MinerU>
- LangGraph interrupts: <https://docs.langchain.com/oss/python/langgraph/interrupts>
- FastAPI file uploads: <https://fastapi.tiangolo.com/tutorial/request-files/>
- Pydantic strict mode: <https://docs.pydantic.dev/latest/concepts/strict_mode/>

## License

This project is intended to be released under the MIT License.

Before publishing, add a root `LICENSE` file containing the MIT License text and make sure package metadata declares the license consistently. The MIT License allows broad reuse, modification, distribution, and private use while preserving copyright and license notice requirements.

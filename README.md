# Invoice-to-Pay Agent

Open-source accounts-payable automation prototype built with FastAPI, LangGraph,
Pydantic, LiteParse, and Docling.

The project models the invoice-to-payment control path around typed data,
deterministic checks, human approval, ERP-ready posting payloads, and audit
evidence.

[![CI](https://github.com/mshojaei77/invoice-to-pay-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/mshojaei77/invoice-to-pay-agent/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![FastAPI](https://img.shields.io/badge/FastAPI-ready-009688)
![LangGraph](https://img.shields.io/badge/LangGraph-agentic-purple)

## What It Does

The workflow accepts invoice support documents and runs them through a finance
control graph:

```text
upload
  -> parse with LiteParse / Docling
  -> normalize AP documents
  -> validate schema and business rules
  -> duplicate check
  -> PO / delivery matching
  -> exception and fraud controls
  -> approval routing
  -> payment and ERP sync planning
  -> mock ERP post
  -> audit log
```

It is intended for engineers, AP managers, controllers, ERP consultants, and
finance automation reviewers who want a runnable reference implementation of an
invoice-to-pay agent.

## Features

- FastAPI service for run creation, lookup, approval, rejection, and audit lookup.
- LangGraph workflow with an approval interrupt and in-memory checkpointing.
- Strict Pydantic schemas for invoices, purchase orders, delivery notes, parsed
  documents, and audit records.
- Parser routing with LiteParse as the fast path and Docling for heavier parsing.
- Deterministic AP controls for validation, duplicate detection, 2-way / 3-way
  matching, exceptions, fraud, risk, GL coding, compliance, payment planning, and
  mock ERP posting.
- Streamlit review UI for local upload, run inspection, and audit report download.
- Real sample PDFs plus pytest coverage for the graph, services, API, parser
  contracts, schemas, and demo path.

## Quick Start

Prerequisites:

- Python 3.11+
- `uv`

Install and test:

```bash
uv sync
uv run pytest
```

Run the clean invoice demo:

```bash
uv run python scripts/run_demo.py \
  --invoice samples/invoice_001_canada_post_sample.pdf \
  --po samples/purchase_order_001_polychemtex.pdf \
  --delivery-note samples/delivery_note_001_bunker_receipt.pdf \
  --parser liteparse
```

Expected summary:

```text
final_status=completed
risk_level=low
erp_status=posted
```

Run an exception case:

```bash
uv run python scripts/run_demo.py \
  --invoice samples/invoice_002_tax_sample_local_supply.pdf
```

Expected summary:

```text
final_status=requires_approval
erp_status=not_posted
```

Write a markdown report:

```bash
uv run python scripts/run_demo.py \
  --invoice samples/invoice_001_canada_post_sample.pdf \
  --po samples/purchase_order_001_polychemtex.pdf \
  --delivery-note samples/delivery_note_001_bunker_receipt.pdf \
  --output-md data/processed/reports/latest-demo.md
```

## Review UI

Start the local Streamlit review app:

```bash
uv run streamlit run app/ui/streamlit_app.py
```

The UI supports local document upload, graph execution, control inspection, and
markdown audit report download.

## API

Start the FastAPI service:

```bash
uv run invoice-to-pay-agent
```

The server listens on `http://localhost:8000`.

Available routes:

| Method | Route | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Health check |
| `POST` | `/runs` | Upload one or more files and start a run |
| `GET` | `/runs/{run_id}` | Fetch a run result |
| `POST` | `/runs/{run_id}/approve` | Resume an approval-gated run as approved |
| `POST` | `/runs/{run_id}/reject` | Resume an approval-gated run as rejected |
| `GET` | `/runs/{run_id}/audit` | Read audit events for a run |

Example upload:

```bash
curl -F "files=@samples/invoice_001_canada_post_sample.pdf" \
  -F "files=@samples/purchase_order_001_polychemtex.pdf" \
  -F "files=@samples/delivery_note_001_bunker_receipt.pdf" \
  http://localhost:8000/runs
```

## CLI

Main demo command:

```bash
uv run python scripts/run_demo.py --help
```

Current options:

```text
--invoice INVOICE
--po PO
--delivery-note DELIVERY_NOTE
--parser {liteparse,docling}
--output-md OUTPUT_MD
```

Approval helper scripts are available for local graph-resume experiments:

```bash
uv run python scripts/approve_demo.py --run-id <run_id>
uv run python scripts/reject_demo.py --run-id <run_id>
```

## Project Structure

```text
app/
  api/          FastAPI app and routes
  graph/        LangGraph state, workflow, and nodes
  schemas/      Pydantic data contracts
  services/     AP controls, parser routing, ERP mock, risk, matching, audit
  ui/           Streamlit review app
docs/           Demo report, launch notes, release notes
samples/        Sample invoice, PO, delivery, remittance, and reference PDFs
scripts/        CLI demo and approval helpers
tests/          Pytest suite
```

## Configuration

This project currently needs no external service credentials for the default
demo and test path.

Environment placeholders live in `.env.example` for future OpenAI and storage
settings. Keep dependency changes in `pyproject.toml` and `uv.lock`; add Python
packages with:

```bash
uv add <package>
```

## Testing

Run the full suite:

```bash
uv run pytest
```

Useful focused checks:

```bash
uv run pytest tests/test_graph.py
uv run pytest tests/test_api.py
uv run pytest tests/test_parser_router.py
uv run pytest tests/test_run_demo.py
```

## Sample Data

The `samples/` directory contains demo invoices, purchase orders, delivery
notes, statements, remittance advice, credit notes, and reference documents.

`samples/eval_manifest.jsonl` provides smoke-level scenario coverage for the
demo corpus.

## Current Limitations

- Active API runs are stored in memory and are lost when the server restarts.
- The LangGraph checkpointer is in-memory.
- ERP posting is mocked; no live ERP connector is included.
- The review UI is local Streamlit, not a production approval portal.
- Parser behavior is suitable for prototype evaluation and tests, not certified
  financial document processing.
- Payment execution is represented as a control plan; this project does not move
  money.

## Documentation

- [Demo report](docs/demo-report.md)
- [Launch kit](docs/launch-kit.md)
- [Release notes](docs/release-v0.1.0.md)
- [Repository launch checklist](docs/repository-launch-checklist.md)
- [Contributing guide](CONTRIBUTING.md)
- [Security policy](SECURITY.md)
- [Code of conduct](CODE_OF_CONDUCT.md)

## Contributing

Issues and pull requests are welcome. Before opening a PR:

```bash
uv sync
uv run pytest
```

Keep changes focused, update tests when behavior changes, and keep public docs
aligned with the actual command and API surface.

## License

MIT. See [LICENSE](LICENSE).

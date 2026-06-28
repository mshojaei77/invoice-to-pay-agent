# Invoice-to-Pay Agent

Controls-first accounts payable automation, built with LangGraph, FastAPI, strict Pydantic contracts, parser routing, risk scoring, human approval interrupts, ERP mock posting, and pytest-backed scenarios.

This repo is not a "send a PDF to an LLM" demo. It is a reproducible AP workflow prototype for the messy middle of invoice operations: validation, duplicate risk, PO and delivery-note matching, approval routing, and auditability before anything gets posted.

## Why Finance Teams Should Care

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

## Who This Is For

| Audience | Why it is worth a look |
| --- | --- |
| Finance teams | A practical blueprint for reducing invoice exceptions, duplicate-payment risk, and ERP copy-paste work while keeping approvals explicit. |
| CFOs and operators | A small, inspectable automation wedge in a real budget line: AP processing, procurement controls, reconciliation, and compliance. |
| Investors and YC-style analysts | A vertical AI workflow with a clear painkiller use case, measurable operational ROI, and expansion paths into vendor risk, procurement, payments, and audit. |
| AI engineers | A compact LangGraph system with stateful nodes, human interrupts, parser routing, typed schemas, deterministic service tests, and API endpoints. |
| LangGraph builders | A naturally graph-shaped workflow where each node has a business responsibility and the approval gate is the single controlled interrupt. |
| Reddit skeptics | The repo is intentionally boring in the right places: tests, schemas, state, risk reasons, and no magical "autonomous payment" claims. |
| Code geeks | Thin FastAPI routes, focused services, strict models, reproducible `uv` setup, and a test suite covering graph, API, schemas, risk, matching, parser routing, and audit helpers. |
| LinkedIn readers | A concrete example of AI agents doing back-office work where trust, controls, and explainability matter more than a chat interface. |

## Current Status

This is an early but runnable prototype.

Implemented now:

- `uv`-managed Python 3.11 project
- FastAPI app with health, run creation, run lookup, approve, reject, and audit endpoints
- LangGraph workflow with in-memory checkpointing
- Typed graph state for AP runs
- Pydantic schemas for invoices, purchase orders, delivery notes, parsed documents, and audit contracts
- Parser routing service that chooses LiteParse or MinerU based on file type and complexity hints
- Risk scoring with explicit reasons and human-approval thresholding
- Duplicate and matching service logic
- ERP mock post/reject behavior
- Demo scripts for normal, approval, and rejection flows
- Pytest coverage across API, graph, nodes, schemas, parser routing, risk, matching, duplicate handling, business validation, audit, and eval smoke tests

Prototype limitations:

- Parser graph nodes are still deterministic/stub oriented; parser adapters and routing services are present, but real document extraction is not yet wired end-to-end through the graph.
- Persistence is in-memory for active runs; audit helper support exists, but durable production storage is still roadmap work.
- ERP integration is intentionally mocked.
- No UI is included yet.

That honesty is deliberate. Finance automation should earn trust through visible contracts, tests, and controlled rollout.

## Workflow

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
- Nodes after approval perform the controlled post/reject outcome.
- Every run has a `run_id` so API state, approval, ERP result, and audit records can be correlated.

## Architecture

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

tests/
  API, graph, schema, parser, risk, matching, duplicate, audit, and eval smoke tests
```

## Risk Model

Risk output is intentionally simple and inspectable:

```text
risk_level: low | medium | high
risk_score: float
risk_reasons: list[str]
requires_human_approval: bool
```

Current risk triggers include:

- Schema validation errors
- Missing PO
- Missing delivery note
- Missing or invalid payment-critical vendor fields
- Handwritten correction signal
- Low parser confidence signal
- Possible or confirmed duplicate
- PO, vendor, delivery, quantity, subtotal, tax, or total mismatches

Low-risk runs can auto-approve. Medium/high-risk runs pause at the LangGraph interrupt and must be approved or rejected through the API or a future UI.

## API

Start the server:

```bash
uv run invoice-to-pay-agent
```

Useful endpoints:

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Liveness check |
| `POST` | `/runs` | Upload one or more AP documents and start a graph run |
| `GET` | `/runs/{run_id}` | Inspect latest run state |
| `POST` | `/runs/{run_id}/approve` | Resume a waiting run with approval |
| `POST` | `/runs/{run_id}/reject` | Resume a waiting run with rejection |
| `GET` | `/runs/{run_id}/audit` | Return matching audit events when present |

Example upload:

```bash
curl.exe -X POST http://localhost:8000/runs -F "files=@samples/sample-pdf-invoice.pdf" -F "files=@samples/purchase-order-1.pdf" -F "files=@samples/Delivery-Note-Receipt-PDF-Download.pdf"
```

## Run It Step by Step

This section is written for people who do not normally run Python projects. You should be able to copy each command, paste it into a terminal, and see the same kind of result.

### 1. Install the Two Required Tools

You need:

- Python 3.11 or newer
- `uv`, the Python package manager used by this repo


### 2. Open the Project Folder

Open PowerShell, Terminal, or your editor terminal, then move into the project directory.

### 3. Install Project Dependencies

Run:

```bash
uv sync
```

### 4. Run the Test Suite

Run:

```bash
uv run pytest
```

Expected result:

```text
143 passed
```

One dependency warning from FastAPI/Starlette may appear. That warning does not stop the project from running.

### 5. Run a Simple Finance Scenario

This scenario uses a downloaded sample invoice with no matching PO. That should trigger human approval instead of posting to the ERP mock.

```bash
uv run python scripts/run_demo.py --invoice samples/sample-tax-invoice.pdf
```

Expected result:

```text
run_id=<some-generated-id>
final_status=requires_approval
erp_status=not_posted
audit_log=data/processed/audit.jsonl
```

What it means:

- The graph accepted the invoice.
- The project noticed support is missing.
- The invoice was not posted automatically.
- A finance reviewer would need to approve or reject it.

### 6. Run a Clean Invoice-to-Pay Scenario

This scenario includes an invoice, purchase order, and delivery note. It should finish as a low-risk run and post to the ERP mock.

```bash
uv run python scripts/run_demo.py --invoice samples/sample-pdf-invoice.pdf --po samples/purchase-order-1.pdf --delivery-note samples/Delivery-Note-Receipt-PDF-Download.pdf
```

Expected result:

```text
run_id=<some-generated-id>
final_status=completed
risk_level=low
erp_status=posted
audit_log=data/processed/audit.jsonl
```

What it means:

- The invoice had the expected supporting documents.
- The run was scored as low risk.
- The ERP mock received a post action.

### 7. Start the API Server

Use this when you want to try the project as a service instead of a command-line demo.

```bash
uv run invoice-to-pay-agent
```

Expected result:

```text
INFO:     Uvicorn running on http://0.0.0.0:8000
```

Keep this terminal open. The API server is running while this command is active.

Open this URL in your browser:

```text
http://localhost:8000/health
```

Expected browser result:

```json
{"status":"ok"}
```

### 8. Submit Documents to the API

Open a second terminal in the same project folder. Keep the API server running in the first terminal.

Submit one invoice, one PO, and one delivery note:

```bash
curl.exe -X POST http://localhost:8000/runs -F "files=@samples/sample-pdf-invoice.pdf" -F "files=@samples/purchase-order-1.pdf" -F "files=@samples/Delivery-Note-Receipt-PDF-Download.pdf"
```

Expected result:

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

The real response includes more fields. The important parts are `run_id`, `status`, `risk_level`, and `erp_result`.

### 9. Try an Approval Scenario Through the API

Submit an invoice without PO or delivery support:

```bash
curl.exe -X POST http://localhost:8000/runs -F "files=@samples/sample-tax-invoice.pdf"
```

Expected result:

```json
{
  "run_id": "...",
  "status": "requires_approval"
}
```

Copy the `run_id` from the response.

Approve it:

```bash
curl.exe -X POST http://localhost:8000/runs/YOUR_RUN_ID_HERE/approve
```

Or reject it:

```bash
curl.exe -X POST http://localhost:8000/runs/YOUR_RUN_ID_HERE/reject
```

Replace `YOUR_RUN_ID_HERE` with the actual `run_id`.

### 10. Stop the Server

Go back to the terminal running the API server and press:

```text
Ctrl+C
```

The server will stop.

### 11. Useful Checks

Check that Python files still compile:

```bash
uv run python -m compileall app tests
```

Run one focused test file:

```bash
uv run pytest tests/test_graph.py
```

Run all tests again:

```bash
uv run pytest
```

### 12. Common Problems

| Problem | What to do |
| --- | --- |
| `uv is not recognized` | Run `pip install uv`, close the terminal, reopen it, and try `uv --version`. |
| `python is not recognized` | Install Python 3.11+ and make sure "Add Python to PATH" is selected during installation. |
| Port `8000` is already in use | Stop the other app using port 8000, or run with `uv run uvicorn app.api.main:app --host 0.0.0.0 --port 8001`. |
| `curl.exe` is not available | Open `http://localhost:8000/docs` in a browser and use FastAPI's built-in "Try it out" form. |
| The API loses old runs after restart | Current runs are stored in memory. Restarting the server clears active run state. Durable storage is roadmap work. |
| A sample file is hard to classify | The project uses real downloaded PDFs from `samples/`; early graph nodes still score support-document presence deterministically until parser extraction is wired through the graph. |

## Parser Strategy

The intended parser policy is conservative:

- LiteParse first for clean digital PDFs and fast extraction.
- MinerU first for images, receipts, scans, dense tables, handwriting, stamps, and signatures.
- MinerU retry when LiteParse output has low confidence, validation errors, payment-critical mismatches, or complex-document warnings.

The point is not parser maximalism. The point is routing documents by operational risk and keeping parser choice explainable.

## Evaluation Philosophy

AP agents should be judged with business scenarios, not only extraction demos.

The test suite already covers the early contract:

- Schema shape and strict validation
- Parser route decisions
- Business-rule errors
- Risk scoring thresholds and reasons
- Duplicate outcomes
- Invoice / PO / delivery-note matching
- Graph state transitions
- API run, approval, and rejection behavior
- Audit helper behavior

The current eval smoke tests use `samples/eval_manifest.jsonl`, which points at downloaded PDFs in `samples/`. Future eval scenarios should measure:

- Invoice number accuracy
- Vendor accuracy
- Total and tax accuracy
- Line-item accuracy
- PO match accuracy
- Delivery match accuracy
- Duplicate precision and recall
- Approval routing correctness
- ERP post/reject correctness
- Hallucinated-field rate
- Parser fallback rate and latency

## Roadmap

Near-term:

- Wire real LiteParse and MinerU adapters into graph execution
- Persist runs, uploaded documents, parser outputs, approvals, and ERP mock results
- Write audit events from graph nodes, not only helper tests
- Maintain the downloaded sample corpus under `samples/` and expand `samples/eval_manifest.jsonl`
- Add CI for tests and compile checks

Product track:

- Streamlit or lightweight web approval console
- Durable Postgres storage
- MinIO or object-storage document archive
- Vendor and PO master-data mocks
- Exception queue and reviewer assignment
- Batch analytics for duplicate trends and approval delays

AI engineering track:

- Parser-version tracking
- MLflow or equivalent eval tracking
- Langfuse/OpenTelemetry tracing
- Scenario benchmark script for clean, missing-support, parser-challenge, and rejection flows
- Documented parser confidence and fallback metrics

Enterprise track:

- ERP connector interface
- Role-based approval policy
- Audit export
- Cloud deployment guide
- Data retention and PII handling notes

## Tech Stack

- Python 3.11
- `uv`
- FastAPI
- LangGraph
- Pydantic v2
- LiteParse
- MinerU
- rapidfuzz
- pytest

## Design Principles

- Keep controls explicit.
- Keep API routes thin.
- Keep business logic in services.
- Keep graph nodes small and inspectable.
- Use strict schemas before decisions.
- Use human interrupts only where business approval is required.
- Treat parser fallback as a risk-control mechanism.
- Prefer deterministic tests and scenario evals over impressive demos.

## References

- LiteParse: https://github.com/run-llama/liteparse
- MinerU: https://github.com/opendatalab/MinerU
- LangGraph interrupts: https://docs.langchain.com/oss/python/langgraph/interrupts
- FastAPI file uploads: https://fastapi.tiangolo.com/tutorial/request-files/
- Pydantic strict mode: https://docs.pydantic.dev/latest/concepts/strict_mode/

## One-Line Pitch

An invoice-to-pay agent for teams that want AI speed without giving up finance controls.

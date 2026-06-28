# Invoice-to-Pay Agent

AI-assisted accounts payable automation, built as a reproducible LangGraph-first prototype.

This project turns invoices, receipts, purchase orders, and delivery notes into validated, auditable, ERP-ready payment decisions. It is intentionally small enough to inspect, but shaped like a real finance workflow: extract, validate, match, detect duplicates, route approvals, post to ERP, and evaluate quality.

## Why This Exists

Finance teams do not just need better OCR. They need fewer payment mistakes, faster month-end close, traceable approvals, duplicate-invoice protection, and a cleaner handoff into ERP systems.

Most invoice automation demos stop at "we extracted fields from a PDF." Real AP work starts after extraction:

- Is this invoice already in the system?
- Does it match the purchase order?
- Did goods or services arrive?
- Is the IBAN or VAT number plausible?
- Who needs to approve it?
- Can the output be trusted enough to post?
- Can an auditor reconstruct what happened?

`invoice-to-pay-agent` is a practical answer to that full workflow.

## Who It Is For

**Finance teams:** A clear prototype for reducing manual AP review, duplicate payments, invoice exceptions, and copy-paste work across tools.

**Investors and startup analysts:** A focused wedge into a high-budget back-office workflow with expansion paths into procurement, vendor risk, compliance, reconciliation, and ERP integrations.

**AI engineers:** A compact LangGraph project with strict schemas, deterministic baselines, human approval gates, audit logs, and a path toward eval-driven LLM extraction.

**Code geeks:** A repo that starts boring on purpose: typed state, Pydantic contracts, small services, testable extraction, and no premature platform sprawl.

**Reddit skeptics:** This is not "just call an LLM on a PDF." The plan includes validation, duplicate detection, mismatch handling, human review, and evaluation because AP automation fails in the messy edge cases.

**LinkedIn readers:** A clean demo of AI agents doing operational work where accuracy, controls, and traceability matter more than chat UI novelty.

**LangGraph people:** The workflow is naturally graph-shaped: each node updates shared state, risk controls decide the route, and human-in-the-loop approval can pause and resume execution.

## Product Vision

```text
Upload docs
  -> extract strict JSON
  -> validate fields
  -> detect duplicates
  -> match invoice vs PO / delivery note
  -> score risk
  -> request approval when needed
  -> post to ERP mock
  -> write audit trail
  -> report quality metrics
```

The goal is a lightweight, inspectable AP agent that finance teams can trust before it touches real payments.

## Current Prototype Status

Implemented:

- `uv`-managed Python project
- Professional `app/` skeleton
- Strict Pydantic invoice and purchase-order schemas
- PDF text extraction with `pdfplumber`
- Deterministic invoice stub extractor for invoice number and total
- Tests for schema validation and extraction defaults

Next milestone:

- LangGraph state and nodes
- CLI smoke test
- Human approval interrupt
- ERP mock post
- JSONL audit log

## Planned MVP Features

| Capability | Why it matters |
| --- | --- |
| Document upload | Accept invoice PDF/image plus optional PO and delivery note |
| OCR / VLM extraction | Convert documents into strict JSON |
| Schema validation | Catch missing, negative, malformed, or suspicious values |
| Field extraction | Vendor, IBAN, VAT, total, line items, dates, currency |
| 2-way / 3-way matching | Compare invoice against PO and delivery evidence |
| Duplicate detection | Reduce duplicate-payment risk before approval |
| Risk scoring | Route clean invoices automatically and exceptions to humans |
| Approval queue | Keep humans in control for risky or mismatched invoices |
| ERP mock endpoint | Simulate the payment-system handoff |
| Evaluation report | Track extraction accuracy, mismatch detection, and hallucination rate |
| Audit log | Preserve every decision and agent step for review |

## Architecture

```text
app/
  api/          FastAPI endpoints
  graph/        LangGraph state, nodes, workflow
  schemas/      Pydantic invoice, PO, audit contracts
  services/     extraction, matching, duplicates, ERP mock, audit
  storage/      future persistence boundary
  evals/        future evaluation harness
tests/
  schema and extraction tests
data/
  samples, uploads, processed artifacts
```

The first production-quality principle is separation of concerns:

- Schemas define what "valid" means.
- Services do deterministic work.
- Graph nodes orchestrate state transitions.
- API routes stay thin.
- Evals decide whether the agent is improving.

## Workflow Design

```text
START
  -> save_uploads
  -> extract_invoice
  -> extract_po
  -> validate_extraction
  -> duplicate_check
  -> match_invoice_po
  -> risk_score
  -> approval_gate
  -> post_to_erp_mock
  -> write_audit_log
  -> END
```

Why LangGraph:

- Invoice processing is stateful.
- Each step should be observable.
- Human approval requires pause/resume behavior.
- Finance workflows need deterministic routing, not a single opaque prompt.
- Failed or risky states should become review tasks, not silent failures.

## Tech Stack

Current:

- Python 3.11
- `uv`
- Pydantic
- pdfplumber
- pytest

Near-term:

- LangGraph
- FastAPI
- python-multipart
- rapidfuzz
- SQLAlchemy

Later:

- PostgreSQL for durable invoice and duplicate records
- MinIO for document storage
- OpenTelemetry / Langfuse for traces
- MLflow plus Ragas or DeepEval for quality tracking
- Streamlit or Next.js for approval UI
- PySpark for batch AP analytics

## Cloud Mapping

| Local prototype | Cloud-ready target |
| --- | --- |
| Local filesystem | Azure Data Lake or Google Cloud Storage |
| PostgreSQL | Azure PostgreSQL or Cloud SQL |
| FastAPI | Azure Container Apps or GKE |
| Local batch jobs | Databricks or managed Spark |
| MLflow local | Databricks MLflow |
| Local traces | Langfuse / OpenTelemetry backend |

## Run Locally

Install dependencies:

```bash
uv sync
```

Run tests:

```bash
uv run pytest
```

Compile-check the app and tests:

```bash
uv run python -m compileall app tests
```

Run the placeholder CLI entrypoint:

```bash
uv run invoice-to-pay-agent
```

## Engineering Principles

- Start deterministic before adding LLM extraction.
- Validate every model output with Pydantic.
- Keep human approval explicit for risky invoices.
- Make every agent step auditable.
- Prefer small services over giant workflow nodes.
- Add persistence only after the CLI workflow works.
- Measure extraction and matching quality before claiming automation.

## Evaluation Plan

The project will track:

- Field extraction accuracy
- Required-field validation failure rate
- Duplicate detection precision and recall
- PO mismatch detection accuracy
- Hallucinated-field rate
- Human approval routing accuracy
- ERP-post success and rejection reasons

The target is not a flashy demo. The target is an AP workflow that can be inspected, tested, and improved.

## Roadmap

1. Build the working CLI graph with human approval.
2. Add approve/reject resume scripts.
3. Add FastAPI upload endpoints.
4. Add JSONL audit persistence.
5. Add duplicate and matching services.
6. Add deterministic evaluation fixtures.
7. Replace the stub extractor with LLM/VLM extraction behind the same schema.
8. Add PostgreSQL and document storage.
9. Add approval dashboard.
10. Add cloud deployment docs.

## References

- LangGraph docs: https://docs.langchain.com/oss/python/langgraph/overview
- Pydantic docs: https://docs.pydantic.dev/latest/concepts/models/
- FastAPI file uploads: https://fastapi.tiangolo.com/tutorial/request-files/
- pdfplumber: https://github.com/jsvine/pdfplumber


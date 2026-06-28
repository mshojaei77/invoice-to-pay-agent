# Invoice-to-Pay Agent

An auditable invoice-to-pay workflow for finance teams, built as a reproducible LangGraph-first AI agent.

This is not an OCR demo. It is a controlled AP workflow that parses messy finance documents with LiteParse and MinerU, validates extracted fields with strict Pydantic schemas, matches invoice evidence, detects duplicates, routes risky cases to humans, and only posts clean decisions to an ERP mock.

## Why This Exists

Finance teams do not just need better extraction. They need fewer payment mistakes, faster exception handling, duplicate-invoice protection, traceable approvals, and a cleaner handoff into ERP systems.

The real AP problem starts after a document is parsed:

- Is this invoice already in the system?
- Does it match the purchase order?
- Did the goods or services arrive?
- Is the IBAN or VAT number plausible?
- Are handwritten corrections or stamps present?
- Who needs to approve the exception?
- Can the ERP post be trusted?
- Can an auditor reconstruct every decision?

`invoice-to-pay-agent` is designed around those controls.

## Who It Is For

**Finance teams:** A practical automation blueprint for reducing manual AP review, duplicate payments, invoice exceptions, and ERP copy-paste work.

**Investors and YC-style startup analysts:** A focused wedge into an existing budget line with expansion paths into procurement, vendor risk, compliance, reconciliation, and ERP integrations.

**AI engineers:** A compact LangGraph system with strict schemas, human interrupts, risk scoring, eval fixtures, MLflow tracking, and optional tracing.

**Code geeks:** A repo that values boring production shape: typed contracts, thin APIs, inspectable state, deterministic tests, and reusable services.

**Reddit skeptics:** The point is not "send a PDF to an LLM." The point is validation, mismatch detection, duplicate protection, approval routing, audit logs, and measurable evals.

**LinkedIn readers:** A clean demo of AI agents doing operational work where controls, accuracy, and traceability matter more than chat UI novelty.

**LangGraph people:** The core workflow is naturally graph-shaped: each node updates shared state, human approval pauses at one explicit interrupt, and resumable execution protects real-world actions.

## Product Vision

```text
Upload invoice / PO / delivery note
  -> store raw documents
  -> parse fast with LiteParse
  -> normalize to AP document schemas
  -> validate schema and business rules
  -> if incomplete, scanned, table-heavy, handwritten, or risky: reparse with MinerU
  -> reconcile parser outputs
  -> detect duplicates
  -> run 2-way / 3-way match
  -> score risk
  -> request approval when needed
  -> post or reject through ERP mock
  -> write audit trail
  -> track evals, metrics, and traces
```

The goal is a lightweight AP agent that finance teams can inspect before it touches real payments.

## Current Prototype Status

Implemented:

- `uv`-managed Python project
- Professional `app/` skeleton
- Initial Pydantic invoice and purchase-order schemas
- Initial extraction tests and schema tests

Planned change:

- Replace the temporary parser path with LiteParse and MinerU only.
- Expand schemas into strict AP document contracts.
- Build the LangGraph workflow as the core product before adding UI/storage layers.

## Core Workflow

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

Only `approval_gate` should use a human interrupt. Everything before it prepares evidence; everything after it performs or records a controlled decision.

## Planned MVP Features

| Capability | Why it matters |
| --- | --- |
| LiteParse fast parsing | Fast local parsing for clean digital AP documents |
| MinerU heavy parsing | Heavy local parsing for scans, dense tables, handwriting, and complex layouts |
| Strict Pydantic AP schemas | Reject wrong or incomplete finance data before decisions |
| LangGraph workflow | Make the AP process stateful, resumable, and inspectable |
| Risk scoring | Explain which invoices need human review |
| Duplicate detection | Reduce duplicate-payment risk |
| 2-way / 3-way matching | Compare invoice, PO, and delivery evidence |
| JSONL audit logs | Keep an inspectable local trail from day one |
| FastAPI endpoints | Expose uploads, run status, approvals, rejection, and audit |
| PostgreSQL persistence | Store durable runs, documents, approvals, duplicates, and posts |
| ERP mock logic | Simulate realistic post/reject behavior |
| Evaluation fixtures | Measure extraction, matching, duplicate, and approval quality |
| MLflow tracking | Track parser versions, schema versions, metrics, cost, and latency |
| DeepEval / GenAI evals | Test agent decisions and hallucination-sensitive behavior |
| Langfuse or OpenTelemetry traces | Inspect graph, parser, validation, approval, and ERP timing |
| Streamlit dashboard | Give humans an approval and audit review surface |
| Docker Compose | Run the local stack reproducibly |
| GitHub Actions CI | Keep schema, graph, eval, and smoke tests honest |
| MinIO document storage | Store raw documents, parsed outputs, and audit artifacts |
| Cloud deployment docs | Map the local stack to Azure/GCP/Databricks-style targets |
| PySpark batch analytics | Analyze duplicates, exceptions, approval delays, and quality trends |

## Architecture

```text
app/
  api/          FastAPI routes
  graph/        LangGraph state, nodes, workflow
  schemas/      Strict Pydantic AP contracts
  services/     parser, validation, matching, duplicates, ERP mock, audit
  storage/      PostgreSQL and MinIO boundaries
  evals/        fixtures, metrics, DeepEval / MLflow GenAI checks
tests/
  schema, parser contract, graph, matching, audit, eval smoke tests
data/
  samples, uploads, processed artifacts, eval fixtures
docs/
  cloud mapping and operating notes
```

Design rules:

- LiteParse and MinerU are the only parser paths.
- LiteParse runs first for clean digital PDFs and quick preflight.
- MinerU runs for scans, dense tables, handwritten/signature cases, failed validation, or high-risk parser output.
- Pydantic schemas define what valid AP data means.
- Services do focused business work.
- LangGraph nodes orchestrate state transitions.
- API routes stay thin.
- Audit logs, MLflow runs, and traces all share the same `run_id`.

## Risk Model

Output:

```text
risk_level: low | medium | high
risk_score: float
risk_reasons: list[str]
requires_human_approval: bool
```

Risk triggers include:

- Missing PO or delivery note
- Duplicate candidate found
- Invoice total mismatch
- Line-item total mismatch
- Vendor mismatch between invoice and PO
- Missing or invalid-looking IBAN/VAT
- Handwritten correction detected
- Low parser confidence
- Schema or business-rule validation errors

## Evaluation Plan

The project will track:

- Invoice number accuracy
- Vendor accuracy
- Total amount accuracy
- Line-item accuracy
- PO match accuracy
- Duplicate detection precision and recall
- Approval routing accuracy
- Hallucinated-field rate
- ERP rejection correctness

Evaluation fixtures live under:

```text
data/eval/
  invoices/
  purchase_orders/
  delivery_notes/
  ground_truth.jsonl
```

## Tech Stack

Current:

- Python 3.11
- `uv`
- Pydantic
- pytest

Next:

- LiteParse
- MinerU
- LangGraph
- FastAPI
- rapidfuzz
- SQLAlchemy

Production-shaped additions:

- PostgreSQL
- MinIO
- MLflow
- DeepEval or MLflow GenAI evaluation
- Langfuse or OpenTelemetry
- Streamlit
- Docker Compose
- GitHub Actions
- PySpark

## Cloud Mapping

| Local prototype | Cloud-ready target |
| --- | --- |
| MinIO | Azure Data Lake or Google Cloud Storage |
| PostgreSQL | Azure PostgreSQL or Cloud SQL |
| FastAPI | Azure Container Apps or GKE |
| MLflow local | Databricks MLflow |
| Local batch jobs | Databricks or managed Spark |
| Langfuse / OpenTelemetry | Managed observability backend |

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

## Roadmap

1. Replace parser path with LiteParse and MinerU only.
2. Define strict Pydantic AP schemas.
3. Build LangGraph state and nodes.
4. Add risk scoring.
5. Add duplicate detection.
6. Add PO / delivery-note matching.
7. Add JSONL audit logs.
8. Add FastAPI endpoints.
9. Add PostgreSQL persistence.
10. Add ERP mock post/reject logic.
11. Add evaluation fixtures.
12. Add MLflow tracking.
13. Add DeepEval / GenAI eval tests.
14. Add traces with Langfuse or OpenTelemetry.
15. Add Streamlit approval dashboard.
16. Add Docker Compose.
17. Add GitHub Actions CI.
18. Add MinIO document storage.
19. Add cloud deployment docs.
20. Add PySpark batch analytics.

## References

- LiteParse: https://github.com/run-llama/liteparse
- MinerU: https://github.com/opendatalab/MinerU
- Pydantic strict mode: https://docs.pydantic.dev/latest/concepts/strict_mode/
- LangGraph interrupts: https://docs.langchain.com/oss/python/langgraph/interrupts
- FastAPI file uploads: https://fastapi.tiangolo.com/tutorial/request-files/
- MLflow tracking: https://mlflow.org/docs/latest/ml/tracking/
- MLflow GenAI evaluation: https://mlflow.org/docs/latest/genai/eval-monitor/

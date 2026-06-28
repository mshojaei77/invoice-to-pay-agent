# Invoice-to-Pay Agent - Ordered Implementation Plan

This is the canonical build order for the prototype. Keep the project message simple:

> This is not an OCR demo. It is an auditable invoice-to-pay workflow that parses messy AP documents, validates extracted fields, matches invoice evidence, detects duplicates, routes risky cases to humans, and only posts clean decisions to an ERP mock.

## Architecture Rule

Use LangGraph as the product core. The API, dashboard, storage, tracing, and batch analytics should wrap the graph instead of duplicating business logic.

Final graph order:

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

Use a human interrupt only at `approval_gate`.

---

## 1. Replace Parser Path With LiteParse And MinerU Only

Replace the current `pdfplumber` path with exactly two local parser adapters: LiteParse for fast local parsing and MinerU for heavy local parsing.

Why first: every downstream decision depends on reliable document parsing. LiteParse is the fast path for clean digital PDFs and simple POs. MinerU is the heavy path for scanned documents, dense tables, image-heavy files, handwriting, signatures, stamps, and other complex AP layouts.

Implement:

```text
app/services/parser.py
app/services/parser_router.py
app/schemas/parsed_document.py
tests/test_parser_contract.py
```

Normalized output:

```text
ParsedDocument:
  parser_name
  parser_version
  document_type
  text
  markdown
  tables
  blocks
  images
  page_count
  confidence
  warnings
  raw_artifact_path
```

Rules:

- Do not add a third parser to the main path.
- LiteParse runs first for clean digital PDFs, simple invoices, and normal POs.
- MinerU runs for scanned/image-based documents, dense or malformed tables, handwritten/signature/stamp cases, low-confidence output, or failed validation.
- Keep parser configuration in environment variables.
- Store the raw parser response for audit/debug.
- Convert parser output to strict internal schemas before any matching or posting.

Parser routing rules:

```text
digital PDF with selectable text        -> LiteParse
simple PO table                         -> LiteParse first
receipt photo or scanned invoice        -> MinerU
dense / merged / multi-page table       -> MinerU
handwriting, stamp, or signature        -> MinerU
missing totals, VAT, IBAN, line items   -> MinerU retry
payment-critical mismatch               -> human review, not auto-post
```

---

## 2. Define Strict Pydantic AP Schemas

Every parser output must pass through Pydantic v2 strict validation before the graph treats it as business data.

Implement:

```text
app/schemas/ap_document.py
app/schemas/invoice.py
app/schemas/purchase_order.py
app/schemas/delivery_note.py
app/schemas/common.py
tests/test_schemas.py
```

Required validation rules:

```text
total_amount > 0
currency in allowed list
invoice_number required for invoice
po_number required for purchase order
delivery_note_number required for delivery note
issue_date <= today
due_date >= issue_date
line_items total approximately equals subtotal
subtotal + tax_amount approximately equals total_amount
```

Use strict types and explicit validators. Finance workflows should reject wrong types instead of silently coercing them.

---

## 3. Build LangGraph State And Nodes

Build the graph before the UI. The graph is the workflow engine and the audit boundary.

Implement:

```text
app/graph/state.py
app/graph/nodes.py
app/graph/workflow.py
scripts/run_demo.py
scripts/approve_demo.py
scripts/reject_demo.py
tests/test_graph.py
```

State should include:

```text
run_id
uploaded_documents
parsed_documents
parser_route
parser_warnings
invoice
purchase_order
delivery_note
validation_errors
business_rule_errors
duplicate_result
match_result
risk_level
risk_score
risk_reasons
requires_human_approval
approval
erp_result
audit_events
```

Rules:

- Every node returns only the fields it updates.
- Keep side effects idempotent because interrupted nodes may rerun.
- Compile with a checkpointer and pass a stable `thread_id`.

---

## 4. Add Risk Scoring

Do not make the system binary. Add a risk model that explains why a run needs review.

Output:

```text
risk_level: low | medium | high
risk_score: float
risk_reasons: list[str]
requires_human_approval: bool
```

Risk triggers:

```text
missing PO
missing delivery note
duplicate candidate found
total mismatch
IBAN missing or invalid-looking
VAT missing or invalid-looking
handwritten correction detected
low parser confidence
line-item total mismatch
vendor mismatch between invoice and PO
schema validation errors
business rule validation errors
```

Suggested routing:

```text
low risk     -> auto-approve allowed
medium risk  -> human approval required
high risk    -> human approval required, ERP post blocked unless explicitly approved
```

---

## 5. Add Duplicate Detection

Duplicate protection is one of the most business-relevant AP features.

Use:

```text
vendor_name + invoice_number
vendor_name + total_amount + issue_date
rapidfuzz similarity on vendor names
PostgreSQL unique constraints later
```

Output:

```text
duplicate_status: clear | possible_duplicate | confirmed_duplicate
duplicate_candidates: [...]
```

Start with an in-memory or JSONL-backed implementation only for the CLI demo. Move the durable version into PostgreSQL in step 9.

---

## 6. Add PO / Delivery-Note Matching

Implement both 2-way and 3-way matching.

2-way match:

```text
invoice vs purchase_order
```

3-way match:

```text
invoice vs purchase_order vs delivery_note
```

Compare:

```text
vendor
PO number
line items
quantity
unit price
subtotal
tax
total
delivery status
```

Route mismatches to human approval.

---

## 7. Add JSONL Audit Logs

Before PostgreSQL, write simple JSONL audit logs.

Implement:

```text
app/services/audit.py
data/processed/audit.jsonl
tests/test_audit.py
```

Each graph node should append an event shaped like:

```json
{
  "run_id": "...",
  "timestamp": "...",
  "node": "match_invoice_po_delivery",
  "input_hash": "...",
  "output_summary": "...",
  "risk_delta": "...",
  "decision": "...",
  "model_or_parser": "liteparse|mineru",
  "errors": []
}
```

Rules:

- Include stable event IDs so resume/retry flows do not duplicate side effects.
- Never write secrets or raw API keys into audit logs.
- Keep raw parser artifacts separately from summarized audit events.

---

## 8. Add FastAPI Endpoints

Expose the graph through thin FastAPI routes after the CLI graph works.

Endpoints:

```text
POST /runs
GET  /runs/{run_id}
POST /runs/{run_id}/approve
POST /runs/{run_id}/reject
GET  /runs/{run_id}/audit
GET  /health
```

Rules:

- Routes save files and call the graph.
- Business logic stays in services and graph nodes.
- File upload support requires `python-multipart`.
- Return clear run status: `completed`, `requires_approval`, `rejected`, `posted`, or `failed`.

---

## 9. Add PostgreSQL Persistence

Move from JSONL-only to durable records.

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

Rules:

- Keep JSONL audit logs as a local artifact even after Postgres exists.
- Add unique constraints for duplicate protection.
- Use migrations once the schema stabilizes.

---

## 10. Add ERP Mock Post / Reject Logic

Keep it fake but realistic.

ERP mock should reject:

```text
missing approval
high risk without explicit approval
duplicate invoice
total mismatch
invalid schema
missing vendor
missing invoice number
```

ERP mock should return:

```text
erp_post_id
status
rejection_reason
posted_at
```

Tests:

```text
approved clean invoice posts
rejected invoice does not post
duplicate invoice does not post
total mismatch does not post unless explicitly approved
invalid schema never posts
```

---

## 11. Add Evaluation Fixtures

Create a small, versioned evaluation dataset.

Layout:

```text
data/eval/
  invoices/
  purchase_orders/
  delivery_notes/
  ground_truth.jsonl
```

Metrics:

```text
invoice_number_accuracy
vendor_accuracy
total_amount_accuracy
line_item_accuracy
po_match_accuracy
duplicate_detection_precision
duplicate_detection_recall
approval_routing_accuracy
hallucinated_field_rate
```

Use real-world mini scenarios:

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

---

## 12. Add MLflow Tracking

Use MLflow for parser, extraction, and evaluation runs.

Track:

```text
parser_version
prompt_version
schema_version
document_type
field_accuracy
latency
cost
validation_failures
approval_routing_accuracy
```

Store artifacts:

```text
parsed_documents.jsonl
eval_report.json
confusion_matrix.json
audit_sample.jsonl
```

---

## 13. Add DeepEval / GenAI Eval Tests

Add evals for extraction and decision quality.

Test cases:

```text
Should route duplicate invoice to human
Should reject total mismatch
Should not invent missing IBAN
Should flag handwritten correction
Should not post without approval
Should preserve audit log
```

Use DeepEval or MLflow GenAI evaluation. Keep the evaluator runnable from CI in a smoke mode.

---

## 14. Add Traces With Langfuse Or OpenTelemetry

Add traces after graph and evals work.

Track:

```text
graph run
node duration
parser latency
LLM call
validation failure
risk score
approval decision
ERP mock result
```

Rules:

- Make tracing optional through environment variables.
- Do not require tracing services for local tests.
- Keep run IDs aligned across graph, API, audit, MLflow, and traces.

---

## 15. Add Streamlit Approval Dashboard

Only add UI after API and graph are stable.

Pages:

```text
Upload documents
Review extracted fields
Show PO / delivery match
Show duplicate warning
Approve / reject
View audit timeline
View eval metrics
```

Use Streamlit first. Next.js can come later if a polished product demo is needed.

---

## 16. Add Docker Compose

Services:

```text
api
postgres
minio
mlflow
langfuse or otel-collector
streamlit
```

Rules:

- Keep `docker compose up` as the recruiter-friendly entrypoint.
- Use `.env.example` for required variables.
- Mount `./data` for local artifacts.

---

## 17. Add GitHub Actions CI

CI should run:

```text
ruff
mypy or pyright
pytest
compileall
schema tests
graph smoke test
eval smoke test
```

Rules:

- Keep MinerU heavy-parser integration tests optional unless the local runtime is available.
- Use mocked LiteParse and MinerU parser fixtures for normal CI.
- Fail on schema regressions and graph smoke failures.

---

## 18. Add MinIO Document Storage

Store original files and parsed outputs.

Buckets:

```text
raw-documents
parsed-documents
audit-artifacts
eval-fixtures
```

Rules:

- Store raw uploads before parsing.
- Store normalized parser output.
- Keep object keys tied to `run_id`.

---

## 19. Add Cloud Deployment Docs

Do not overbuild cloud in week one. Add a professional mapping document.

Implement:

```text
docs/cloud_mapping.md
```

Include:

```text
MinIO -> Azure Data Lake / GCS
PostgreSQL -> Azure PostgreSQL / Cloud SQL
FastAPI -> Azure Container Apps / GKE
MLflow -> Databricks MLflow
Local batch jobs -> Databricks / Spark
Langfuse/OpenTelemetry -> managed observability backend
```

---

## 20. Add PySpark Batch Analytics

Do this last, after the core AP agent works.

Batch jobs:

```text
monthly duplicate report
vendor exception report
approval delay report
field extraction quality by vendor
invoice mismatch trend
```

This helps with Databricks/Spark job matching without making the MVP heavy.

---

## Dependency Policy

Use `uv` only:

```bash
uv add liteparse pydantic langgraph fastapi uvicorn python-multipart rapidfuzz sqlalchemy pytest
```

Add heavier dependencies only when their implementation step begins:

```bash
uv add mlflow deepeval streamlit boto3 psycopg[binary] opentelemetry-sdk
```

Do not add PySpark, MinIO clients, MLflow, Langfuse, or dashboard dependencies before their step is active.

---

## Reference Docs

- LiteParse: https://github.com/run-llama/liteparse
- MinerU: https://github.com/opendatalab/MinerU
- Pydantic strict mode: https://docs.pydantic.dev/latest/concepts/strict_mode/
- LangGraph interrupts: https://docs.langchain.com/oss/python/langgraph/interrupts
- FastAPI file uploads: https://fastapi.tiangolo.com/tutorial/request-files/
- MLflow tracking: https://mlflow.org/docs/latest/ml/tracking/
- MLflow GenAI evaluation: https://mlflow.org/docs/latest/genai/eval-monitor/

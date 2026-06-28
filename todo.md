# Invoice-to-Pay Agent TODO

Tiny implementation steps for turning the prototype into an auditable invoice-to-pay workflow.

Keep the product rule simple: this is not an OCR demo. The graph must parse AP documents, validate strict schemas, match evidence, detect duplicates, route risky cases to humans, post only clean decisions to an ERP mock, and write an audit trail.

## Working Rules

- [ ] Keep LangGraph as the product core.
- [ ] Keep API, dashboard, storage, tracing, and batch jobs as wrappers around the graph.
- [ ] Use a human interrupt only at `approval_gate`.
- [ ] Use LiteParse and MinerU as the only parser paths.
- [ ] Use `uv add <package>` for dependencies.
- [ ] Add or update tests with each feature step.
- [ ] Run `uv run pytest` before marking a milestone done.
- [ ] Run `uv run python -m compileall app tests` before marking a milestone done.

## Target Graph

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

## 0. Repo Baseline

- [x] Run `uv sync`.
- [x] Run `uv run pytest`.
- [x] Run `uv run python -m compileall app tests`.
- [x] Note any existing failures before changing code.
- [x] Check `git status --short`.
- [x] Keep unrelated local changes untouched.

## 1. Parser Contracts

- [ ] Create `app/schemas/parsed_document.py`.
- [ ] Add a `ParsedDocument` schema.
- [ ] Add `parser_name`.
- [ ] Add `parser_version`.
- [ ] Add `document_type`.
- [ ] Add `text`.
- [ ] Add `markdown`.
- [ ] Add `tables`.
- [ ] Add `blocks`.
- [ ] Add `images`.
- [ ] Add `page_count`.
- [ ] Add `confidence`.
- [ ] Add `warnings`.
- [ ] Add `raw_artifact_path`.
- [ ] Add `tests/test_parser_contract.py`.
- [ ] Test that valid parser output passes.
- [ ] Test that missing required fields fail.
- [ ] Test that wrong field types fail.
- [ ] Run parser contract tests.

## 2. Parser Adapters

- [ ] Create `app/services/parser.py`.
- [ ] Define a shared parser adapter interface.
- [ ] Add a LiteParse adapter stub.
- [ ] Add a MinerU adapter stub.
- [ ] Return `ParsedDocument` from both adapters.
- [ ] Store raw parser responses for debugging.
- [ ] Keep parser config in environment variables.
- [ ] Remove the old `pdfplumber` main parser path if present.
- [ ] Verify no third parser is used in the main path.
- [ ] Add mocked adapter tests.
- [ ] Run parser tests.

## 3. Parser Routing

- [ ] Create `app/services/parser_router.py`.
- [ ] Route selectable-text PDFs to LiteParse first.
- [ ] Route simple PO tables to LiteParse first.
- [ ] Route receipt photos to MinerU.
- [ ] Route scanned invoices to MinerU.
- [ ] Route dense tables to MinerU.
- [ ] Route handwriting cases to MinerU.
- [ ] Route stamp or signature cases to MinerU.
- [ ] Route low-confidence LiteParse output to MinerU.
- [ ] Route failed validation output to MinerU retry.
- [ ] Keep payment-critical mismatches for human review.
- [ ] Add routing tests for each case.
- [ ] Run parser routing tests.

## 4. Strict AP Schemas

- [ ] Create `app/schemas/common.py`.
- [ ] Create `app/schemas/ap_document.py`.
- [ ] Create `app/schemas/invoice.py`.
- [ ] Create `app/schemas/purchase_order.py`.
- [ ] Create `app/schemas/delivery_note.py`.
- [ ] Use Pydantic v2 strict validation.
- [ ] Add money fields with strict numeric handling.
- [ ] Add date fields with explicit validation.
- [ ] Require `invoice_number` for invoices.
- [ ] Require `po_number` for purchase orders.
- [ ] Require `delivery_note_number` for delivery notes.
- [ ] Validate `total_amount > 0`.
- [ ] Validate allowed currencies.
- [ ] Validate `issue_date <= today`.
- [ ] Validate `due_date >= issue_date`.
- [ ] Validate line-item totals against subtotal.
- [ ] Validate subtotal plus tax against total.
- [ ] Add schema tests for valid documents.
- [ ] Add schema tests for invalid documents.
- [ ] Run schema tests.

## 5. Business Rule Validation

- [ ] Create or extend a validation service.
- [ ] Check missing PO.
- [ ] Check missing delivery note.
- [ ] Check missing vendor.
- [ ] Check missing IBAN.
- [ ] Check invalid-looking IBAN.
- [ ] Check missing VAT number.
- [ ] Check invalid-looking VAT number.
- [ ] Check low parser confidence.
- [ ] Check handwritten correction warnings.
- [ ] Return structured business-rule errors.
- [ ] Add tests for each rule.
- [ ] Run validation tests.

## 6. LangGraph State

- [ ] Create `app/graph/state.py`.
- [ ] Add `run_id`.
- [ ] Add `uploaded_documents`.
- [ ] Add `parsed_documents`.
- [ ] Add `parser_route`.
- [ ] Add `parser_warnings`.
- [ ] Add `invoice`.
- [ ] Add `purchase_order`.
- [ ] Add `delivery_note`.
- [ ] Add `validation_errors`.
- [ ] Add `business_rule_errors`.
- [ ] Add `duplicate_result`.
- [ ] Add `match_result`.
- [ ] Add `risk_level`.
- [ ] Add `risk_score`.
- [ ] Add `risk_reasons`.
- [ ] Add `requires_human_approval`.
- [ ] Add `approval`.
- [ ] Add `erp_result`.
- [ ] Add `audit_events`.
- [ ] Add state shape tests.

## 7. LangGraph Nodes

- [ ] Create `app/graph/nodes.py`.
- [ ] Add `save_uploads`.
- [ ] Add `parse_documents_fast_with_liteparse`.
- [ ] Add `normalize_ap_documents`.
- [ ] Add `validate_schema`.
- [ ] Add `validate_business_rules`.
- [ ] Add `route_to_mineru_if_needed`.
- [ ] Add `reconcile_parser_outputs`.
- [ ] Add `duplicate_check`.
- [ ] Add `match_invoice_po_delivery`.
- [ ] Add `risk_score`.
- [ ] Add `approval_gate`.
- [ ] Add `post_to_erp_mock`.
- [ ] Add `write_audit_log`.
- [ ] Make each node return only updated fields.
- [ ] Keep side effects idempotent.
- [ ] Add unit tests for each node.

## 8. LangGraph Workflow

- [ ] Create `app/graph/workflow.py`.
- [ ] Wire nodes in the target graph order.
- [ ] Add a checkpointer.
- [ ] Pass a stable `thread_id`.
- [ ] Add the human interrupt at `approval_gate`.
- [ ] Add `tests/test_graph.py`.
- [ ] Test a clean auto-post path.
- [ ] Test a human approval path.
- [ ] Test a rejected path.
- [ ] Test resume after approval.
- [ ] Run graph tests.

## 9. Demo Scripts

- [ ] Create `scripts/run_demo.py`.
- [ ] Create `scripts/approve_demo.py`.
- [ ] Create `scripts/reject_demo.py`.
- [ ] Keep CLI commands short.
- [x] Add sample input paths.
- [ ] Print `run_id`.
- [ ] Print final status.
- [ ] Print audit log path.
- [ ] Add a README snippet for demo usage if needed.
- [x] Run the demo with a clean sample.
- [x] Run the demo with a risky sample.

## 10. Risk Scoring

- [ ] Create or extend a risk service.
- [ ] Output `risk_level`.
- [ ] Output `risk_score`.
- [ ] Output `risk_reasons`.
- [ ] Output `requires_human_approval`.
- [ ] Score missing PO.
- [ ] Score missing delivery note.
- [ ] Score duplicate candidates.
- [ ] Score total mismatches.
- [ ] Score missing or invalid-looking IBAN.
- [ ] Score missing or invalid-looking VAT.
- [ ] Score handwritten corrections.
- [ ] Score low parser confidence.
- [ ] Score line-item total mismatches.
- [ ] Score vendor mismatches.
- [ ] Score schema validation errors.
- [ ] Score business-rule validation errors.
- [ ] Route low risk to auto-approval eligibility.
- [ ] Route medium risk to human approval.
- [ ] Route high risk to human approval.
- [ ] Block high-risk ERP posts unless explicitly approved.
- [ ] Add risk tests.

## 11. Duplicate Detection

- [ ] Create or extend duplicate service.
- [ ] Start with in-memory or JSONL-backed storage.
- [ ] Match on `vendor_name + invoice_number`.
- [ ] Match on `vendor_name + total_amount + issue_date`.
- [ ] Add `rapidfuzz` with `uv add rapidfuzz` when implementing.
- [ ] Use fuzzy vendor-name matching.
- [ ] Output `duplicate_status`.
- [ ] Output `duplicate_candidates`.
- [ ] Add clear duplicate tests.
- [ ] Add possible duplicate tests.
- [ ] Add confirmed duplicate tests.
- [ ] Keep durable PostgreSQL constraints for a later step.

## 12. PO And Delivery Matching

- [ ] Create or extend matching service.
- [ ] Add 2-way invoice-to-PO matching.
- [ ] Add 3-way invoice-to-PO-to-delivery matching.
- [ ] Compare vendor.
- [ ] Compare PO number.
- [ ] Compare line-item descriptions.
- [ ] Compare quantities.
- [ ] Compare unit prices.
- [ ] Compare subtotal.
- [ ] Compare tax.
- [ ] Compare total.
- [ ] Compare delivery status.
- [ ] Return structured mismatch reasons.
- [ ] Route mismatches to human approval.
- [ ] Add matching tests.

## 13. JSONL Audit Logs

- [ ] Create `app/services/audit.py`.
- [ ] Create `data/processed/` if needed.
- [ ] Write audit events to `data/processed/audit.jsonl`.
- [ ] Add stable event IDs.
- [ ] Add timestamp.
- [ ] Add `run_id`.
- [ ] Add node name.
- [ ] Add input hash.
- [ ] Add output summary.
- [ ] Add risk delta.
- [ ] Add decision.
- [ ] Add parser or model name.
- [ ] Add errors list.
- [ ] Prevent duplicate events on resume.
- [ ] Keep secrets out of audit logs.
- [ ] Keep raw parser artifacts separate.
- [ ] Add `tests/test_audit.py`.
- [ ] Run audit tests.

## 14. ERP Mock

- [ ] Create or extend ERP mock service.
- [ ] Reject missing approval when approval is required.
- [ ] Reject high risk without explicit approval.
- [ ] Reject duplicate invoices.
- [ ] Reject total mismatches.
- [ ] Reject invalid schemas.
- [ ] Reject missing vendors.
- [ ] Reject missing invoice numbers.
- [ ] Return `erp_post_id`.
- [ ] Return `status`.
- [ ] Return `rejection_reason`.
- [ ] Return `posted_at`.
- [ ] Test approved clean invoice posts.
- [ ] Test rejected invoice does not post.
- [ ] Test duplicate invoice does not post.
- [ ] Test total mismatch does not post unless explicitly approved.
- [ ] Test invalid schema never posts.

## 15. Evaluation Fixtures

- [ ] Create `data/eval/invoices/`.
- [ ] Create `data/eval/purchase_orders/`.
- [ ] Create `data/eval/delivery_notes/`.
- [ ] Create `data/eval/ground_truth.jsonl`.
- [ ] Add clean invoice with matching PO.
- [ ] Add invoice missing PO.
- [ ] Add duplicate invoice.
- [ ] Add total mismatch.
- [ ] Add vendor mismatch.
- [x] Add handwritten correction.
- [x] Add missing IBAN.
- [x] Add delivery quantity mismatch.
- [ ] Define invoice-number accuracy.
- [ ] Define vendor accuracy.
- [ ] Define total amount accuracy.
- [ ] Define line-item accuracy.
- [ ] Define PO match accuracy.
- [ ] Define duplicate precision and recall.
- [ ] Define approval routing accuracy.
- [ ] Define hallucinated-field rate.
- [ ] Add an eval smoke test.

## 16. FastAPI

- [x] Add FastAPI with `uv add fastapi uvicorn python-multipart`.
- [ ] Create or extend `app/api/`.
- [ ] Add `POST /runs`.
- [ ] Add `GET /runs/{run_id}`.
- [x] Add `POST /runs/{run_id}/approve`.
- [x] Add `POST /runs/{run_id}/reject`.
- [ ] Add `GET /runs/{run_id}/audit`.
- [ ] Add `GET /health`.
- [ ] Keep routes thin.
- [ ] Save uploaded files before graph execution.
- [ ] Return `completed` status.
- [ ] Return `requires_approval` status.
- [ ] Return `rejected` status.
- [ ] Return `posted` status.
- [ ] Return `failed` status.
- [ ] Add API tests.

## 17. PostgreSQL Persistence

- [ ] Add SQLAlchemy when this milestone starts.
- [ ] Create database settings.
- [ ] Add `ap_runs` table.
- [ ] Add `documents` table.
- [ ] Add `parsed_documents` table.
- [ ] Add `invoices` table.
- [ ] Add `purchase_orders` table.
- [ ] Add `delivery_notes` table.
- [ ] Add `duplicate_candidates` table.
- [ ] Add `approval_tasks` table.
- [ ] Add `erp_posts` table.
- [ ] Add `audit_events` table.
- [ ] Add duplicate-protection unique constraints.
- [ ] Keep JSONL audit logs as local artifacts.
- [ ] Add migration tooling after schema stabilizes.
- [ ] Add persistence tests.

## 18. MLflow

- [ ] Add MLflow when this milestone starts.
- [ ] Track parser version.
- [ ] Track prompt version if prompts exist.
- [ ] Track schema version.
- [ ] Track document type.
- [ ] Track field accuracy.
- [ ] Track latency.
- [ ] Track cost if applicable.
- [ ] Track validation failures.
- [ ] Track approval routing accuracy.
- [ ] Store `parsed_documents.jsonl`.
- [ ] Store `eval_report.json`.
- [ ] Store `confusion_matrix.json`.
- [ ] Store `audit_sample.jsonl`.
- [ ] Add an MLflow smoke test.

## 19. GenAI Evals

- [ ] Choose DeepEval or MLflow GenAI evaluation.
- [ ] Add the dependency only when implementing.
- [ ] Test duplicate invoice routing.
- [ ] Test total mismatch rejection.
- [ ] Test no invented missing IBAN.
- [ ] Test handwritten correction flagging.
- [ ] Test no post without approval.
- [ ] Test audit log preservation.
- [ ] Add CI-friendly smoke mode.

## 20. Tracing

- [ ] Choose Langfuse or OpenTelemetry.
- [ ] Make tracing optional.
- [ ] Configure tracing through environment variables.
- [ ] Trace graph runs.
- [ ] Trace node duration.
- [ ] Trace parser latency.
- [ ] Trace LLM calls if any.
- [ ] Trace validation failures.
- [ ] Trace risk score.
- [ ] Trace approval decision.
- [ ] Trace ERP mock result.
- [ ] Keep `run_id` aligned across graph, API, audit, MLflow, and traces.
- [ ] Verify local tests pass with tracing disabled.

## 21. Streamlit Dashboard

- [ ] Add Streamlit when this milestone starts.
- [ ] Add upload page.
- [ ] Add extracted-field review page.
- [ ] Add PO and delivery match view.
- [ ] Add duplicate warning view.
- [ ] Add approve action.
- [ ] Add reject action.
- [ ] Add audit timeline.
- [ ] Add eval metrics view.
- [ ] Keep UI behind the API and graph.
- [ ] Run a dashboard smoke test.

## 22. Docker Compose

- [ ] Add `.env.example`.
- [ ] Add API service.
- [ ] Add PostgreSQL service.
- [ ] Add MinIO service.
- [ ] Add MLflow service.
- [ ] Add tracing service if selected.
- [ ] Add Streamlit service.
- [ ] Mount `./data` for local artifacts.
- [ ] Document `docker compose up`.
- [ ] Run the local stack.
- [ ] Run a smoke workflow in the stack.

## 23. GitHub Actions CI

- [ ] Add workflow file.
- [ ] Run `ruff`.
- [ ] Run type checks with mypy or pyright.
- [ ] Run `pytest`.
- [ ] Run compile checks.
- [ ] Run schema tests.
- [ ] Run graph smoke test.
- [ ] Run eval smoke test.
- [ ] Mock LiteParse in normal CI.
- [ ] Mock MinerU in normal CI.
- [ ] Keep heavy parser tests optional.
- [ ] Fail CI on schema regressions.
- [ ] Fail CI on graph smoke failures.

## 24. MinIO Storage

- [ ] Add MinIO client dependency when implementing.
- [ ] Create `raw-documents` bucket.
- [ ] Create `parsed-documents` bucket.
- [ ] Create `audit-artifacts` bucket.
- [ ] Create `eval-fixtures` bucket.
- [ ] Store raw uploads before parsing.
- [ ] Store normalized parser output.
- [ ] Store audit artifacts.
- [ ] Tie object keys to `run_id`.
- [ ] Add storage tests with a local or mocked client.

## 25. Cloud Docs

- [ ] Create `docs/cloud_mapping.md`.
- [ ] Map MinIO to Azure Data Lake.
- [ ] Map MinIO to Google Cloud Storage.
- [ ] Map PostgreSQL to Azure PostgreSQL.
- [ ] Map PostgreSQL to Cloud SQL.
- [ ] Map FastAPI to Azure Container Apps.
- [ ] Map FastAPI to GKE.
- [ ] Map local MLflow to Databricks MLflow.
- [ ] Map local batch jobs to Databricks or managed Spark.
- [ ] Map tracing to a managed observability backend.
- [ ] Keep the doc practical and short.

## 26. PySpark Analytics

- [ ] Add PySpark only when this milestone starts.
- [ ] Add monthly duplicate report.
- [ ] Add vendor exception report.
- [ ] Add approval delay report.
- [ ] Add field extraction quality by vendor.
- [ ] Add invoice mismatch trend.
- [ ] Add sample input data.
- [ ] Add a local smoke command.
- [ ] Add batch analytics docs.

## Definition Of Done For Any Milestone

- [ ] Code is implemented in the existing architecture.
- [ ] New dependencies were added with `uv add`.
- [ ] Tests cover the new behavior.
- [ ] Realistic mini scenario was run for large changes.
- [ ] `uv run pytest` passes or failures are documented.
- [ ] `uv run python -m compileall app tests` passes or failures are documented.
- [ ] `git status --short` was checked.
- [ ] A conventional commit message is prepared.

# Invoice-to-Pay Agent

Controls-first finance operations automation built with LangGraph, FastAPI, strict Pydantic contracts, parser routing, risk scoring, exception classification, approval routing, line-level approval planning, GL coding hints, NetSuite AP readiness checks, accounting-platform profiling, multi-company controls, industry policy checks, finance-agent planning, order-to-cash work queues, accrual close planning, spend intelligence, billing/revenue controls, e-invoicing compliance planning, cloud ERP sync planning, pre-approval ledger visibility, payment holds, AI governance, automation readiness, token-cost tracking, payment timing, KPI snapshots, compliance controls, ERP mock posting, audit logs, and pytest-backed scenarios.

This is not a "send a PDF to an LLM" demo. It is a reproducible prototype for the messy middle of enterprise finance operations: validation, duplicate risk, PO and delivery-note matching, line-level approvals, accrual evidence, spend leakage signals, tax reporting readiness, cash-operation follow-up, NetSuite-style ledger/payment controls, and auditability before anything gets posted.

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
- Can approval be routed by line-level GL, cost center, location, and department?
- Can finance see who approved before, who is approving now, and who is next?
- Can the vendor bill be visible in the ledger before final approval while payment remains blocked?
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
- Parser routing service designed for LiteParse-first and Docling fallback decisions.
- Deterministic business validation, duplicate detection, invoice/PO/delivery matching, and risk scoring.
- Exception queue classification for missing support, 3-way match failures, duplicate controls, vendor master-data problems, pricing mismatches, receiving issues, and parser warnings.
- Approval routing that sends clean invoices to auto-post and routes duplicate, vendor-master, pricing, receiving, matching, and GL-coding exceptions to the right reviewer role with an SLA hint.
- Line-level approval planning by GL account, cost center, department, and location, including same-level approver groups, approver-chain visibility, editable dimensions before final approval, and reapproval triggers.
- Excel/manual line-split readiness for large vendor invoices that cannot arrive as XML.
- GL coding and allocation suggestions based on vendor history and invoice text/path keywords, with finance-review fallback when coding is uncertain.
- Accounting-platform profile for connector-neutral Exact, NetSuite, Dynamics, SAP, QuickBooks, and generic cloud ERP posting contracts.
- NetSuite AP readiness checks for multi-currency, non-English OCR due diligence, multi-subsidiary controls, line approvals, paid-status archive sync, pre-approval ledger visibility, payment holds, and native PO matching expectations.
- Multi-company and accountant-collaboration controls for group reporting, entity selection, intercompany review, and accountant-facing workflows.
- Industry policy checks for manufacturing, wholesale, construction, hospitality, professional services, and generic VAT/valuation requirements.
- Finance-agent plan for purchase, banking, debtor-management boundary, and accountant-collaboration responsibilities.
- Order-to-cash plan for SLA-managed invoice resolution, customer/vendor follow-up, and cash-application monitoring.
- Accrual close plan that turns invoice, receipt, GL, and exception evidence into audit-ready month-end close recommendations.
- Spend intelligence that mines supplier invoice context for contract leakage, duplicate spend, software-spend consolidation, and off-contract review signals.
- Billing and revenue plan for contract/rate-card signals, invoice-posting readiness, payment analytics, and revenue-control status.
- E-invoicing compliance plan for structured archive readiness, tax-reporting payload needs, cross-border signals, and connector requirements.
- Cloud ERP sync plan that builds a posting payload with document references, GL coding, payment recommendation, retention class, and single-source-of-truth metadata.
- PO lifecycle plan for asset-purchase PO creation, PO approval, receiving evidence, inbound-shipment review, and invoice matching.
- Ledger/archive visibility plan that keeps draft vendor bills visible before final approval while blocking vendor payment lines until approval and exception resolution.
- AI governance output with approved tool inventory, shadow-AI policy, adoption stage, guardrails, and low-confidence review signals.
- Automation readiness assessment that separates safe workflow automation from human-led review and blocks autonomous GL posting when risk is not recoverable.
- AI cost snapshot that estimates parser text tokens and records AI automation usage as a finance budget line item.
- Payment planning that blocks exception invoices and schedules clean invoices into cashflow buckets.
- KPI snapshot for touchless rate, exception rate, posted count, on-time-payment candidate, approval route, and cycle status.
- Compliance readiness checks for centralized document archive, supporting evidence, segregation of duties, audit trail, retention class, and sensitive data classes.
- Delivery quantity and delivery vendor checks as part of richer 3-way matching.
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
- Exception queue, approval route, and GL coding outputs in graph/API/demo results.
- Cloud ERP sync plan, payment plan, compliance controls, and KPI snapshot outputs in graph/API/demo results.
- AI governance, automation-readiness, and AI cost outputs in graph/API/demo results.
- Accounting-platform profile, NetSuite AP readiness, line-level approvals, PO lifecycle, ledger/archive visibility, multi-company controls, industry policy, finance-agent plan, order-to-cash, accrual close, spend intelligence, billing/revenue, and e-invoicing outputs in graph/API/demo results.
- Test coverage across the main service and workflow boundaries.

Known limitations:

- Parser graph nodes are still deterministic/stub oriented. Parser adapters and routing services exist, but real LiteParse/Docling extraction is not yet wired end-to-end through graph execution.
- Active API runs use in-memory storage and are lost when the server restarts.
- ERP integration is intentionally mocked.
- NetSuite readiness is a deterministic sandbox-planning output, not a certified SuiteApp integration.
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
  -> route_to_docling_if_needed
  -> reconcile_parser_outputs
  -> duplicate_check
  -> match_invoice_po_delivery
  -> classify_ap_exceptions
  -> suggest_gl_coding
  -> accounting_platform_profile
  -> multi_company_controls
  -> industry_policy_check
  -> risk_score
  -> approval_routing
  -> line_approval_planning
  -> compliance_check
  -> payment_planning
  -> po_lifecycle_planning
  -> erp_sync_planning
  -> ledger_visibility_planning
  -> netsuite_ap_readiness_check
  -> order_to_cash_planning
  -> accrual_close_planning
  -> spend_intelligence_analysis
  -> billing_revenue_planning
  -> einvoicing_compliance_planning
  -> finance_agent_planning
  -> ai_governance_check
  -> automation_readiness_check
  -> ai_cost_tracking
  -> approval_gate
  -> post_to_erp_mock
  -> kpi_snapshot
  -> write_audit_log
```

The graph shape is the product architecture:

- Nodes before `approval_gate` gather evidence and calculate risk.
- `classify_ap_exceptions` converts raw errors and mismatches into an AP-facing work queue.
- `suggest_gl_coding` proposes a GL account, cost center, and allocation when deterministic rules match.
- `accounting_platform_profile` chooses a connector-neutral ERP/accounting contract for Exact, NetSuite, Dynamics, SAP, QuickBooks, or generic cloud ERP.
- `multi_company_controls` records entity, intercompany, consolidation, and accountant-collaboration context.
- `industry_policy_check` applies VAT, valuation, and dimension controls by industry.
- `approval_routing` decides whether the run can auto-post or should go to AP manager, vendor-master, buyer/receiving, or finance review.
- `line_approval_planning` prepares line-level routing by GL account, cost center, department, and location, with approver-chain visibility and editable dimension policy.
- `compliance_check` records audit-readiness and role-based-access requirements before posting.
- `payment_planning` turns approved/blocked invoice state into a cashflow recommendation.
- `po_lifecycle_planning` records asset-purchase PO creation, approval, receiving, inbound-shipment review, and invoice matching status.
- `erp_sync_planning` builds a cloud-ERP posting payload and sync readiness status.
- `ledger_visibility_planning` records draft-ledger visibility, paid-status archive sync, editable-line sync, and payment holds before final approval.
- `netsuite_ap_readiness_check` summarizes NetSuite-specific due diligence for multi-currency, non-English OCR, line approvals, PO matching, paid archive status, and sandbox payment controls.
- `order_to_cash_planning` creates SLA-managed work queues for invoice resolution, follow-up, and cash application.
- `accrual_close_planning` prepares month-end accrual or reversal recommendations from invoice, receipt, exception, and GL evidence.
- `spend_intelligence_analysis` surfaces supplier-spend opportunities such as contract leakage, duplicate spend, and software consolidation.
- `billing_revenue_planning` records contract/rate-card signals, payment analytics, and revenue-control readiness.
- `einvoicing_compliance_planning` identifies structured archive, tax-reporting, and country-clearance connector requirements.
- `finance_agent_planning` describes purchase, banking, debtor-management, close, spend-intelligence, and accountant-collaboration agent boundaries.
- `ai_governance_check` records approved tools, shadow-AI posture, and guardrail status.
- `automation_readiness_check` decides whether the run is safe for audited automation, assistive review, or human-led review.
- `ai_cost_tracking` estimates token usage so AI automation spend can be tracked explicitly.
- `approval_gate` is the single human interrupt for medium/high-risk runs.
- Nodes after approval perform the controlled post/reject outcome and calculate AP KPI telemetry.
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

### Exception Handling

Extraction quality is treated as an input, not the product. After parsing and validation, the workflow creates a deterministic exception queue:

```text
exception_status: clear | open
exception_count: int
highest_severity: none | low | medium | high | critical
categories: list[str]
exceptions: list[code, category, severity, message, recommended_action]
```

Current exception categories include:

- `matching` for missing PO and PO-number failures.
- `pricing` for subtotal, tax, or total mismatches.
- `receiving` for missing delivery evidence, incomplete delivery, or quantity differences.
- `duplicate_control` for possible or confirmed duplicate invoices.
- `vendor_master_data` for missing/invalid payment-critical vendor fields or vendor mismatches.
- `extraction_quality` for parser warnings that deserve review.

This mirrors the practical accounts-payable pattern: auto-process clean work and send only exceptions to humans with a clear reason and next action.

### Approval Routing

Approval routing is rule-based and inspectable:

```text
route: auto_post | ap_manager_review | vendor_master_review | buyer_receiving_review | finance_coding_review | finance_review
approver_role: system | ap_manager | vendor_master_data | buyer_or_receiving_owner | finance_controller
sla_hours: int
reason: str
```

Examples:

- Clean low-risk runs route to `auto_post`.
- Duplicate exceptions route to `ap_manager_review`.
- Vendor-master-data issues route to `vendor_master_review`.
- 3-way match exceptions route to `buyer_receiving_review`.
- Uncertain GL coding routes to `finance_coding_review`.

### GL Coding

The prototype includes deterministic GL coding/allocation suggestions:

```text
coding_status: suggested | needs_review
gl_account: str | null
cost_center: str | null
allocation: list[{cost_center, percentage}]
confidence: float
reason: vendor_history | description_keyword | no_vendor_or_description_rule
```

Current rules are intentionally simple and transparent. They can be replaced later by vendor history, ERP master data, or account-distribution learning without changing the graph contract.

### Accounting Platform Profile

The workflow now creates a connector-neutral accounting platform profile before ERP sync:

```text
selected_platform: exact | netsuite | dynamics | sap | quickbooks | generic_cloud_erp
supported_platforms: exact, netsuite, dynamics, quickbooks, sap
connector_style: accounting_api | accounting_erp_api | erp_api | adapter_contract
posting_objects: list[str]
connector_contract:
  capabilities
  required_fields
```

This keeps the project aligned with real implementation work where consultants may see Exact, NetSuite, Microsoft Dynamics, SAP, QuickBooks, or a generic cloud ERP across different clients. The current platform selection is deterministic and evidence-based, but the contract is the important part: upstream AP controls do not need to be rewritten for each accounting system.

### NetSuite AP Readiness

The NetSuite readiness output is shaped around practical AP automation evaluation criteria raised by NetSuite operators:

```text
netsuite_profile_status: native_or_partner_ready | connector_contract_ready
invoice_volume_profile: mid_market_300_400_invoices_per_month
global_vendor_profile: bool
non_english_invoice_signal: bool
readiness_score: float
requirements:
  non_english_ocr
  multi_currency_multi_subsidiary
  line_level_approval_by_gl_cost_center
  approval_chain_visibility
  archive_paid_status
  preapproval_ledger_visibility_payment_hold
  excel_import_manual_line_split
  po_creation_approval_matching
recommended_due_diligence: list[str]
```

The project does not claim that NetSuite's native OCR is globally sufficient. The readiness plan explicitly flags non-English and global-vendor invoices for real sample testing, and it asks implementers to validate whether the workflow updates native NetSuite POs and draft vendor bills rather than creating isolated AP records.

### Line-Level Approval Planning

Line approval is modeled separately from document-level approval because real AP workflows often route by line dimensions:

```text
line_approval_status: ready | needs_dimension_review
routing_basis: gl_account_cost_center_location
supports_multiple_same_level_approvers: bool
supports_line_edits_before_final_approval: bool
manual_line_split_supported: bool
excel_import_recommended: bool
dimensions:
  gl_account
  cost_center
  location
  department
approver_chain:
  step
  role
  status
  same_level_group
visibility:
  show_previous_approvers
  show_current_approvers
  show_next_approvers
edit_policy:
  editable_fields
  sync_edits_to_erp_draft
  requires_reapproval_on_dimension_change
```

This covers the common requirement that an invoice can have multiple same-level approvers, approvers can see the approval chain before and after them, and GL/location/cost-center edits made during approval stay synchronized with the draft vendor bill.

### PO Lifecycle And Matching

The PO lifecycle plan keeps asset-purchase PO work visible without assuming stock/inventory complexity:

```text
po_lifecycle_status: matched | review_required
supports_po_creation: bool
supports_po_approval: bool
purchase_type: asset_purchase
po_present: bool
receiving_evidence_present: bool
inbound_shipment_review: required | not_required_for_fixture
matching_mode: three_way_match | exception_match
next_action: release_to_invoice_approval | create_or_attach_po
```

This makes the gap explicit when an AP tool only creates standalone vendor bills instead of updating the purchase order and matching against receiving evidence.

### Ledger And Archive Visibility

The ledger visibility plan handles the workflow where a vendor bill should appear in the ledger before final approval, while payment remains blocked:

```text
ledger_visibility_status: posted_visible | draft_visible_payment_blocked
visible_in_ledger_before_final_approval: bool
vendor_line_blocked_for_payment: bool
payment_release_condition: final_approval_and_no_open_exceptions
paid_status_archive_sync:
  enabled
  source
  archive_fields
line_edit_sync:
  enabled
  sync_target
  audited_fields
```

This also supports the invoice archive requirement: users should be able to see whether an invoice has been paid after the ERP payment status sync runs.

### Multi-Company And Accountant Controls

The multi-company output keeps entity and accountant collaboration explicit:

```text
entity_code: default_entity | eu_entity | uk_entity | us_entity
intercompany_review_required: bool
accountant_collaboration_enabled: bool
multi_company_supported: bool
control_status: ready | review
consolidation_note: str
```

This supports finance professionals and accounting firms that work across multiple administrations, subsidiaries, or client books. It also avoids burying entity selection inside a posting payload.

### Industry Policy Checks

Industry-specific controls are kept as policy output instead of hard-coded ERP assumptions:

```text
industry: generic | manufacturing | wholesale | construction | hospitality | professional_services
policy_status: ready | review
vat_policy: str
valuation_policy: str
extra_controls: list[str]
missing_controls: list[str]
```

Examples include goods-receipt and inventory valuation checks for manufacturing, landed-cost review for wholesale, project-code controls for construction, site cost centers for hospitality, and client/project allocation for professional services.

### Finance Agent Plan

The finance-agent plan describes the boundaries of specialized agents without giving them uncontrolled authority:

```text
agent_plan_status: ready
selected_platform: str
agents:
  purchase_agent
  banking_agent
  debtor_management_agent
  close_agent
  spend_intelligence_agent
  accountant_collaboration_agent
```

Purchase and banking agents assist AP workflow automation. Debtor management now tracks order-to-cash service mode without taking uncontrolled cash actions. Close and spend-intelligence agents expose month-end and procurement analytics work. Accountant collaboration is enabled only when the selected platform/profile supports that workflow.

### Order-to-Cash Plan

The order-to-cash output models continuous operations work that keeps cash moving:

```text
o2c_status: ready
service_mode: continuous_cash_ops | exception_follow_up | sync_readiness_review
sla_hours: int
target_system: str
managed_work_items:
  invoice_resolution
  customer_or_vendor_follow_up
  cash_application
```

This mirrors enterprise finance workflows where the next action is often buried in exceptions, portals, email, or customer context. The output is deterministic and inspectable, so it can later drive a real queue or reviewer UI.

### Accrual Close Plan

The accrual close plan turns invoice and receipt evidence into month-end close recommendations:

```text
accrual_status: ready | review_required
close_action: str
confidence: float
evidence_sources: list[str]
journal_output:
  gl_account
  cost_center
  cashflow_bucket
  supporting_documents
audit_ready: bool
```

This targets the month-end bottleneck: missing invoices, goods-received-not-invoiced support, and journal evidence that needs to be audit-ready instead of spreadsheet-only.

### Spend Intelligence

Spend intelligence mines supplier invoice context and control outputs for procurement signals:

```text
spend_status: monitored | opportunities_found
category: str
gl_account: str | null
opportunity_count: int
opportunities:
  contract_leakage
  duplicate_spend
  software_spend_consolidation
```

The current implementation detects leakage and consolidation signals from deterministic evidence such as pricing exceptions, duplicates, and software/SaaS vendor hints. It is intentionally conservative and designed to be expanded with contracts, vendor master data, and rate-card history.

### Billing And Revenue Plan

The billing/revenue plan keeps revenue-adjacent controls visible when contract or rate-card signals appear:

```text
billing_status: ready | blocked
billing_action: str
contract_signal_detected: bool
revenue_controls:
  erp_sync_ready
  retention_class
  payment_status
analytics:
  cashflow_bucket
  target_payment_date
```

This gives the project a path beyond AP capture into contract-based billing checks, invoice readiness, and payment analytics without weakening the existing AP controls.

### E-Invoicing Compliance

The e-invoicing plan flags structured archive and local tax-reporting readiness:

```text
einvoicing_status: ready | review_required
jurisdiction_signal: domestic_or_unknown | cross_border_or_tax_specific
target_platform: str
vat_policy: str
requirements:
  structured_invoice_archive
  tax_reporting_payload
  country_clearance_adapter
```

The plan does not pretend to implement country clearance networks. It records when a real connector or local reporting payload would be required before production use.

### Cloud ERP Sync Plan

The workflow now prepares a cloud-ERP-oriented sync plan before posting:

```text
target_system: cloud_erp
integration_mode: mock_posting_payload
sync_status: ready | blocked
single_source_of_truth: bool
posting_payload:
  document_refs
  gl_account
  cost_center
  allocation
  payment_recommendation
  target_payment_date
  retention_class
  entity_code
  industry
  vat_policy
  valuation_policy
  line_approval_dimensions
  line_approval_chain
  po_lifecycle_status
  payment_hold_until_final_approval
```

This keeps the AP automation layer aligned with the ERP as the financial system of record. The current implementation is a mock payload, but the contract is shaped so a real SAP, NetSuite, Microsoft Dynamics, or other cloud ERP connector can replace it without changing upstream controls.

### Payment And Cashflow Planning

Clean invoices receive a payment recommendation and cashflow bucket. Exception invoices are blocked from payment planning until the exception is resolved:

```text
payment_status: scheduled | blocked
recommendation: pay_by_discount_window | pay_on_terms | hold_for_exception_resolution
target_payment_date: date | null
cashflow_bucket: next_10_days | scheduled | blocked
```

This gives finance a basic view of upcoming liabilities instead of only a posted/not-posted result.

### KPI Snapshot

Each completed run emits a compact AP automation KPI snapshot:

```text
invoice_count
posted_count
touchless_rate
exception_rate
exception_count
approval_route
on_time_payment_candidate
cashflow_bucket
cycle_status
```

The first version is per-run. It is intentionally shaped to roll up later into dashboards for invoice cycle time, touchless rate, exception rate, on-time payment rate, DPO, and discount-capture analysis.

### Compliance Controls

Compliance output records whether the run is ready, needs review, or is blocked:

```text
compliance_status: ready | review | blocked
controls: list[{control, status, message}]
retention_class: financial_record
sensitive_data_classes: supplier, tax, payment
requires_role_based_access: bool
```

Current controls cover centralized document archive, supporting evidence, segregation of duties for exceptions, and exception audit trail readiness.

### AI Governance And Automation Readiness

The workflow treats AI adoption as an operating-control and capital-allocation problem, not only a parser choice. Each run records:

```text
ai_governance_result:
  governance_status: ready | review | blocked
  adoption_stage: stage_3_workflow_automation
  approved_tool_inventory
  unapproved_tools
  shadow_ai_policy: shut_down_or_formally_adopt
  guardrails

automation_readiness:
  process_profile
  recommended_autonomy_level: auto_process_with_audit | assistive_with_human_review | human_led_review
  requires_human_oversight: bool
  blocked_actions
  next_case_study_metric: minutes_saved_per_invoice
```

The current guardrails enforce these principles:

- Inventory every parser or automation component used by the run.
- Treat unapproved AI tools as blocked until formally adopted or removed.
- Keep medium/high-risk and exception cases under human review.
- Block autonomous general-ledger posting when recoverability is low.
- Use document routing, matching, exception review, and pre-post controls as safer starting points than autonomous ledger writes.

### AI Cost Tracking

Finance leaders need cost visibility before ROI debates become useful. Each run emits a compact AI cost snapshot:

```text
budget_category: ai_automation_usage
estimated_input_tokens: int
estimated_cost_usd: float
cost_model: character_estimate
parser_calls: int
cost_policy: track_tokens_as_finance_line_item
```

The estimate is deliberately simple and deterministic. It creates the reporting hook needed to track token spend over time without introducing a paid model dependency into the prototype.

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

`--parser` accepts `liteparse` or `docling`.
When `--output-md` is omitted, the demo writes `data/processed/reports/<run_id>.md`.

Use Docling as the heavy parser for complex layout, OCR, and table evidence:

```powershell
uv run python scripts/run_demo.py --invoice samples/invoice_001_canada_post_sample.pdf --po samples/purchase_order_001_polychemtex.pdf --delivery-note samples/delivery_note_001_bunker_receipt.pdf --parser docling --output-md data/processed/reports/demo-docling.md
```

Docling runs in-process through its Python `DocumentConverter`; there is no parser API service to start.
The adapter stores Docling Markdown and structured JSON evidence under `data/processed/parser_raw/`.

For faster Docling runs, set `DOCLING_DO_OCR=false` or `DOCLING_DO_TABLE_STRUCTURE=false`.

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
- Exception classification.
- Approval routing.
- GL coding suggestions and review fallback.
- Accounting-platform profiling.
- Multi-company and accountant-collaboration controls.
- Industry VAT and valuation policy checks.
- Finance-agent planning.
- Compliance controls.
- Payment and cashflow planning.
- Cloud ERP sync payload planning.
- AP KPI snapshots.
- AI governance and approved-tool inventory.
- Automation readiness and recoverability gating.
- AI token/cost tracking.
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
- Exception classification precision and reviewer routing accuracy.
- GL coding/account-distribution accuracy.
- Accounting platform detection and connector contract completeness.
- NetSuite AP readiness requirements for non-English OCR, multi-currency subsidiaries, line approvals, paid archive status, and native PO matching.
- Line-level approval routing accuracy for GL account, cost center, location, department, and same-level approver groups.
- Draft-ledger visibility and payment-hold correctness before final approval.
- Entity selection, intercompany review, and accountant-collaboration accuracy.
- Industry VAT, valuation, and dimension policy accuracy.
- Finance-agent routing and boundary correctness.
- Compliance-control false positive and false negative rates.
- Payment recommendation and cashflow bucket accuracy.
- Touchless rate, exception rate, and on-time payment rollups.
- AI governance guardrail coverage and unapproved-tool detection.
- Automation readiness accuracy for recoverable versus non-recoverable workflows.
- AI usage/token spend trend accuracy.
- ERP post/reject correctness.
- Hallucinated-field rate.
- Parser fallback rate and latency.

## Project Structure

```text
app/
  api/          FastAPI routes and app wiring
  graph/        LangGraph state, nodes, workflow construction
  schemas/      Strict AP contracts for invoices, POs, delivery notes, parser output, audit
  services/     parser routing, extraction, validation, matching, exceptions, approval routing, line approvals, ledger visibility, PO lifecycle, NetSuite readiness, GL coding, accounting platforms, multi-company controls, industry policy, finance agents, order-to-cash, accrual close, spend intelligence, billing/revenue, e-invoicing, AI governance, automation readiness, cost tracking, compliance, payment planning, ERP sync, KPIs, duplicate checks, risk, ERP mock, audit
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
  API, graph, schema, parser, risk, matching, duplicate, audit, NetSuite AP readiness, enterprise finance-ops, and eval smoke tests
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
- Docling first for images, receipts, scans, dense tables, handwriting, stamps, and signatures.
- Docling retry when LiteParse output has low confidence, validation errors, payment-critical mismatches, or complex-document warnings.

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

- Wire real LiteParse and Docling adapters into graph execution.
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
- Approval SLA tracking and out-of-office delegation.
- GL coding history from prior invoices and vendor defaults.
- Cloud ERP connector adapters for SAP, NetSuite, Microsoft Dynamics, and generic REST/CSV posting.
- Payment run and reconciliation status sync.
- Batch analytics for duplicate trends and approval delays.
- Native NetSuite sandbox adapter for vendor bill drafts, PO updates, paid-status sync, and line-level approval history.
- Excel import parser for large invoice line splits and configurable line-distribution templates.
- Approval-chain UI showing previous, current, and next approvers per invoice line.
- Durable order-to-cash queues with customer context, portal/email action history, and SLA reporting.
- Accrual rollforward reports and month-end close package exports.
- Contract/rate-card ingestion for spend leakage and billing validation.
- Country-specific e-invoicing clearance adapters and tax-reporting payload validation.

AI engineering track:

- Parser-version tracking.
- MLflow or equivalent eval tracking.
- Langfuse/OpenTelemetry tracing.
- Scenario benchmark script for clean, missing-support, parser-challenge, and rejection flows.
- Documented parser confidence and fallback metrics.
- KPI rollup jobs for touchless rate, exception rate, on-time payment rate, DPO, and discount capture.
- Predictive payment timing and anomaly detection experiments.
- AI adoption case-study reports for minutes saved per workflow.
- Token spend trend reports and budget-threshold alerts.
- Shadow-AI discovery import and enterprise-tool approval workflow.

Enterprise track:

- ERP connector interface.
- Role-based approval policy.
- Audit export.
- Cloud deployment guide.
- Data retention and PII handling notes.
- Encryption and secrets-management guidance for financial document storage.

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
- Docling: <https://github.com/docling-project/docling>
- LangGraph interrupts: <https://docs.langchain.com/oss/python/langgraph/interrupts>
- FastAPI file uploads: <https://fastapi.tiangolo.com/tutorial/request-files/>
- Pydantic strict mode: <https://docs.pydantic.dev/latest/concepts/strict_mode/>

## License

This project is intended to be released under the MIT License.

Before publishing, add a root `LICENSE` file containing the MIT License text and make sure package metadata declares the license consistently. The MIT License allows broad reuse, modification, distribution, and private use while preserving copyright and license notice requirements.

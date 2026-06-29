# Repository Launch Checklist

Use this before sharing the project on LinkedIn, Hacker News, Reddit, or with AP/ERP reviewers.

## GitHub Profile

- Add repository description: `Open-source AP automation prototype for invoice capture, PO/receipt matching, exception routing, fraud controls, approval gates, and ERP-ready audit logs.`
- Add topics: `accounts-payable`, `invoice-processing`, `ap-automation`, `finance-automation`, `procure-to-pay`, `invoice-to-pay`, `langgraph`, `fastapi`, `pydantic`, `document-ai`, `erp`, `netsuite`, `sap`, `mlops`, `llm-agents`.
- Confirm the root `LICENSE` file is present.
- Add a short demo GIF or video to the README once recorded.
- Link [docs/demo-report.md](demo-report.md) from any launch post.

## Launch Message

Lead with the workflow pain:

```text
I built an open-source Invoice-to-Pay Agent.

Not another "send PDF to LLM" demo.

The painful part of accounts payable is usually not extraction.
It is missing PO support, duplicate invoice risk, vendor/payment mismatches,
approval chasing, unclear GL coding, payment holds, and audit reconstruction.
```

Ask for feedback, not stars:

```text
For AP managers, controllers, NetSuite/SAP/Dynamics consultants, and finance automation builders:
what is the AP exception that still wastes the most time in real companies?
```

## Demo Assets

- Clean invoice path: PO matched, delivery matched, low risk, auto-post candidate.
- Exception path: missing PO/delivery evidence, human approval required, payment held, ERP not posted.
- Technical proof: LangGraph workflow, FastAPI routes, Pydantic schemas, approval interrupt, audit log, pytest scenarios.

## Good First Issues

- Build a review UI that shows run status, PO/delivery match, duplicate risk, approval route, payment status, and audit events.
- Add persisted API run storage behind the current in-memory `RUNS` map.
- Wire real LiteParse/Docling extraction through graph execution instead of deterministic parser fixtures.
- Add ERP connector contracts for NetSuite, SAP, Dynamics, Exact, and Odoo without moving money.

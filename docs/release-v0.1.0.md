# v0.1.0 - Runnable AP Automation Prototype

First public release of the Invoice-to-Pay Agent.

## Highlights

- LangGraph invoice-to-pay workflow with explicit graph nodes.
- FastAPI service for run creation, lookup, approval, rejection, and audit retrieval.
- CLI demo for clean and exception invoice scenarios.
- LiteParse and Docling parser routing boundary.
- Deterministic AP controls for validation, duplicate checks, matching, fraud signals, approval routing, payment readiness, ERP mock posting, and audit logs.
- Pydantic v2 schemas for invoice, PO, delivery note, parsed document, and audit contracts.
- Scenario-oriented pytest suite and sample PDF corpus.
- Streamlit review UI for local demos.

## Install

```bash
uv sync
uv run pytest
```

## Demo

```bash
uv run python scripts/run_demo.py --invoice samples/invoice_001_canada_post_sample.pdf --po samples/purchase_order_001_polychemtex.pdf --delivery-note samples/delivery_note_001_bunker_receipt.pdf
uv run streamlit run app/ui/streamlit_app.py
```

## Notes

This is a prototype. ERP posting is mocked, active API runs are in memory, and real production deployments need durable storage, access controls, secrets management, and private document handling.

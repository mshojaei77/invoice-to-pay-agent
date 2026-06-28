Below is a **tiny-step coding TODO** for the first prototype. I’m keeping it LangGraph-first and MVP-focused: upload docs → extract structured invoice/PO JSON → validate → duplicate check → match → human approval → mock ERP post → audit/eval. This follows your uploaded MVP/stack plan. 

---

# Invoice-to-Pay Agent — tiny coding TODO

## 0. Start with the smallest useful architecture

Use **LangGraph `StateGraph`** because this workflow is naturally stateful: each node reads/writes shared state, and edges decide the next step. LangGraph’s docs describe nodes as the work units and edges as the control flow, with graph state evolving over time. ([LangChain Docs][1])

Your first graph:

```text
START
  ↓
save_uploads
  ↓
extract_invoice
  ↓
extract_po
  ↓
validate_extraction
  ↓
duplicate_check
  ↓
match_invoice_po
  ↓
risk_score
  ↓
approval_gate   ← human-in-loop interrupt
  ↓
post_to_erp_mock
  ↓
write_audit_log
  ↓
END
```

---

# 1. Create repo skeleton

```bash
mkdir invoice-to-pay-agent
cd invoice-to-pay-agent

mkdir -p app/{api,graph,schemas,services,storage,evals}
mkdir -p tests data/{samples,uploads,processed} docs
touch README.md .env.example docker-compose.yml
touch app/main.py
touch app/graph/state.py app/graph/nodes.py app/graph/workflow.py
touch app/schemas/invoice.py app/schemas/purchase_order.py app/schemas/audit.py
touch app/services/extraction.py app/services/matching.py app/services/duplicates.py
touch app/services/erp_mock.py app/services/audit.py
touch tests/test_matching.py tests/test_schemas.py
```

---

# 2. Install minimal dependencies

Start lean. Do **not** add PySpark, MLflow, MinIO, Kubernetes yet.

```bash
python -m venv .venv
source .venv/bin/activate

pip install -U langgraph langchain langchain-openai fastapi uvicorn pydantic python-multipart python-dotenv
pip install -U pdfplumber pillow pytesseract rapidfuzz sqlalchemy pytest
```

Why these first:

* `langgraph`: workflow orchestration.
* `fastapi`: upload/API layer; FastAPI supports file uploads through `UploadFile` and `File`. ([FastAPI][2])
* `pydantic`: strict invoice/PO schemas; Pydantic models validate parsed data and can emit JSON Schema. ([Pydantic][3])
* `pdfplumber/pytesseract`: cheap first OCR/text extraction.
* `rapidfuzz`: duplicate/vendor fuzzy matching.

---

# 3. Define strict Pydantic schemas

Create `app/schemas/invoice.py`.

```python
from datetime import date
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field


class InvoiceLineItem(BaseModel):
    description: str
    quantity: float = Field(ge=0)
    unit_price: Decimal = Field(ge=0)
    line_total: Decimal = Field(ge=0)


class Invoice(BaseModel):
    invoice_number: str
    vendor_name: str
    vendor_iban: Optional[str] = None
    vat_number: Optional[str] = None
    issue_date: Optional[date] = None
    due_date: Optional[date] = None
    currency: str = "EUR"
    subtotal: Decimal = Field(ge=0)
    vat_total: Decimal = Field(ge=0)
    total: Decimal = Field(ge=0)
    line_items: List[InvoiceLineItem]
```

Create `app/schemas/purchase_order.py`.

```python
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field


class POLineItem(BaseModel):
    sku: Optional[str] = None
    description: str
    quantity: float = Field(ge=0)
    unit_price: Decimal = Field(ge=0)
    line_total: Decimal = Field(ge=0)


class PurchaseOrder(BaseModel):
    po_number: str
    vendor_name: str
    currency: str = "EUR"
    total: Decimal = Field(ge=0)
    line_items: List[POLineItem]
```

Tiny task:

```bash
pytest tests/test_schemas.py
```

Test only schema validation first.

---

# 4. Define LangGraph state

LangGraph supports state schemas using `TypedDict`, Pydantic models, or dataclasses. For this MVP, use `TypedDict` because it is simple and readable. ([LangChain Docs][4])

Create `app/graph/state.py`.

```python
from typing import Any, Dict, List, Optional, TypedDict


class InvoiceToPayState(TypedDict, total=False):
    run_id: str
    invoice_path: str
    po_path: Optional[str]

    invoice_text: str
    po_text: Optional[str]

    invoice: Dict[str, Any]
    purchase_order: Optional[Dict[str, Any]]

    validation_errors: List[str]
    duplicate_result: Dict[str, Any]
    match_result: Dict[str, Any]
    risk_score: float
    risk_reasons: List[str]

    approval: Dict[str, Any]
    erp_result: Dict[str, Any]

    audit_events: List[Dict[str, Any]]
```

Tiny rule: every node returns only the fields it updates.

---

# 5. Add text extraction service

Create `app/services/extraction.py`.

```python
from pathlib import Path
import pdfplumber


def extract_text_from_pdf(path: str) -> str:
    text_parts = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text_parts.append(page.extract_text() or "")
    return "\n".join(text_parts).strip()


def extract_text(path: str) -> str:
    suffix = Path(path).suffix.lower()
    if suffix == ".pdf":
        return extract_text_from_pdf(path)
    raise ValueError(f"Unsupported file type: {suffix}")
```

Tiny TODO:

* Add PDF only first.
* Add image OCR later.
* Add VLM later.

---

# 6. Build simple deterministic extractors before LLM extraction

Do not start with an LLM. Start with crude regex + fallback. This makes testing easier.

Create `app/services/extraction.py` additions:

```python
import re
from decimal import Decimal


def extract_invoice_stub(text: str) -> dict:
    invoice_number = re.search(r"(invoice\s*(no|number)?[:\s#-]+)([A-Z0-9-]+)", text, re.I)
    total = re.search(r"(total[:\s]+)(€?\s*[0-9,.]+)", text, re.I)

    return {
        "invoice_number": invoice_number.group(3) if invoice_number else "UNKNOWN",
        "vendor_name": "UNKNOWN_VENDOR",
        "vendor_iban": None,
        "vat_number": None,
        "issue_date": None,
        "due_date": None,
        "currency": "EUR",
        "subtotal": Decimal("0"),
        "vat_total": Decimal("0"),
        "total": Decimal(total.group(2).replace("€", "").replace(",", "").strip()) if total else Decimal("0"),
        "line_items": [],
    }
```

Tiny TODO:

* Get graph running with stub extraction.
* Replace with LLM/VLM later.

---

# 7. Add LangGraph nodes

Create `app/graph/nodes.py`.

```python
from uuid import uuid4
from app.graph.state import InvoiceToPayState
from app.services.extraction import extract_text, extract_invoice_stub
from app.schemas.invoice import Invoice


def save_uploads_node(state: InvoiceToPayState) -> InvoiceToPayState:
    return {
        "run_id": state.get("run_id") or str(uuid4()),
        "audit_events": [{"event": "run_started"}],
    }


def extract_invoice_node(state: InvoiceToPayState) -> InvoiceToPayState:
    text = extract_text(state["invoice_path"])
    invoice_dict = extract_invoice_stub(text)
    return {
        "invoice_text": text,
        "invoice": invoice_dict,
        "audit_events": state.get("audit_events", []) + [{"event": "invoice_extracted"}],
    }


def extract_po_node(state: InvoiceToPayState) -> InvoiceToPayState:
    if not state.get("po_path"):
        return {
            "purchase_order": None,
            "audit_events": state.get("audit_events", []) + [{"event": "po_missing"}],
        }

    text = extract_text(state["po_path"])
    return {
        "po_text": text,
        "purchase_order": None,
        "audit_events": state.get("audit_events", []) + [{"event": "po_extracted"}],
    }


def validate_extraction_node(state: InvoiceToPayState) -> InvoiceToPayState:
    errors = []
    try:
        Invoice(**state["invoice"])
    except Exception as e:
        errors.append(str(e))

    return {
        "validation_errors": errors,
        "audit_events": state.get("audit_events", []) + [{"event": "validation_done", "errors": len(errors)}],
    }
```

---

# 8. Add duplicate check

Create `app/services/duplicates.py`.

```python
from app.schemas.invoice import Invoice


_seen_invoice_keys: set[str] = set()


def check_duplicate(invoice: dict) -> dict:
    parsed = Invoice(**invoice)
    key = f"{parsed.vendor_name.lower()}::{parsed.invoice_number}::{parsed.total}"

    is_duplicate = key in _seen_invoice_keys
    if not is_duplicate:
        _seen_invoice_keys.add(key)

    return {
        "is_duplicate": is_duplicate,
        "duplicate_key": key,
    }
```

Add node:

```python
from app.services.duplicates import check_duplicate


def duplicate_check_node(state: InvoiceToPayState) -> InvoiceToPayState:
    result = check_duplicate(state["invoice"])
    return {
        "duplicate_result": result,
        "audit_events": state.get("audit_events", []) + [{"event": "duplicate_check_done", **result}],
    }
```

Tiny TODO later:

* Replace in-memory set with PostgreSQL unique index.
* Add fuzzy duplicate check by vendor + amount + date.

---

# 9. Add invoice-vs-PO matching

Create `app/services/matching.py`.

```python
from decimal import Decimal


def match_invoice_po(invoice: dict, purchase_order: dict | None) -> dict:
    if purchase_order is None:
        return {
            "match_type": "invoice_only",
            "matched": False,
            "mismatches": ["missing_purchase_order"],
        }

    mismatches = []

    invoice_total = Decimal(str(invoice["total"]))
    po_total = Decimal(str(purchase_order["total"]))

    if invoice_total != po_total:
        mismatches.append({
            "field": "total",
            "invoice": str(invoice_total),
            "purchase_order": str(po_total),
        })

    return {
        "match_type": "2_way",
        "matched": len(mismatches) == 0,
        "mismatches": mismatches,
    }
```

Add node:

```python
from app.services.matching import match_invoice_po


def match_invoice_po_node(state: InvoiceToPayState) -> InvoiceToPayState:
    result = match_invoice_po(state["invoice"], state.get("purchase_order"))
    return {
        "match_result": result,
        "audit_events": state.get("audit_events", []) + [{"event": "matching_done", "matched": result["matched"]}],
    }
```

---

# 10. Add risk scoring

```python
def risk_score_node(state: InvoiceToPayState) -> InvoiceToPayState:
    score = 0.0
    reasons = []

    if state.get("validation_errors"):
        score += 0.3
        reasons.append("schema_validation_errors")

    if state.get("duplicate_result", {}).get("is_duplicate"):
        score += 0.5
        reasons.append("possible_duplicate_invoice")

    if not state.get("match_result", {}).get("matched"):
        score += 0.4
        reasons.append("invoice_po_mismatch")

    return {
        "risk_score": min(score, 1.0),
        "risk_reasons": reasons,
        "audit_events": state.get("audit_events", []) + [{"event": "risk_scored", "risk_score": min(score, 1.0)}],
    }
```

Tiny rule:

```text
risk_score >= 0.4 → human approval required
risk_score < 0.4  → can auto-post to ERP mock
```

---

# 11. Add human approval with LangGraph interrupt

Use LangGraph `interrupt()` for the approval queue. Official docs say interrupts pause graph execution, save graph state through persistence, and resume later with `Command(resume=...)`. ([LangChain Docs][5])

```python
from langgraph.types import interrupt


def approval_gate_node(state: InvoiceToPayState) -> InvoiceToPayState:
    if state.get("risk_score", 1.0) < 0.4:
        return {
            "approval": {"status": "auto_approved", "reviewer": "system"},
            "audit_events": state.get("audit_events", []) + [{"event": "auto_approved"}],
        }

    decision = interrupt({
        "message": "Invoice requires human approval",
        "invoice": state["invoice"],
        "duplicate_result": state.get("duplicate_result"),
        "match_result": state.get("match_result"),
        "risk_score": state.get("risk_score"),
        "risk_reasons": state.get("risk_reasons"),
    })

    return {
        "approval": decision,
        "audit_events": state.get("audit_events", []) + [{"event": "human_decision_received", "decision": decision}],
    }
```

Important implementation detail: compile the graph with a checkpointer and pass a `thread_id`, because LangGraph checkpointers persist graph state and are required for human-in-the-loop resume flows. ([LangChain Docs][6])

---

# 12. Add ERP mock

Create `app/services/erp_mock.py`.

```python
def post_invoice_to_erp(invoice: dict, approval: dict) -> dict:
    if approval.get("status") not in {"approved", "auto_approved"}:
        return {
            "posted": False,
            "reason": "not_approved",
        }

    return {
        "posted": True,
        "erp_document_id": f"ERP-{invoice['invoice_number']}",
    }
```

Add node:

```python
from app.services.erp_mock import post_invoice_to_erp


def post_to_erp_mock_node(state: InvoiceToPayState) -> InvoiceToPayState:
    result = post_invoice_to_erp(state["invoice"], state["approval"])
    return {
        "erp_result": result,
        "audit_events": state.get("audit_events", []) + [{"event": "erp_post_attempted", **result}],
    }
```

---

# 13. Build the graph

Create `app/graph/workflow.py`.

```python
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

from app.graph.state import InvoiceToPayState
from app.graph.nodes import (
    save_uploads_node,
    extract_invoice_node,
    extract_po_node,
    validate_extraction_node,
    duplicate_check_node,
    match_invoice_po_node,
    risk_score_node,
    approval_gate_node,
    post_to_erp_mock_node,
)


def build_graph():
    builder = StateGraph(InvoiceToPayState)

    builder.add_node("save_uploads", save_uploads_node)
    builder.add_node("extract_invoice", extract_invoice_node)
    builder.add_node("extract_po", extract_po_node)
    builder.add_node("validate_extraction", validate_extraction_node)
    builder.add_node("duplicate_check", duplicate_check_node)
    builder.add_node("match_invoice_po", match_invoice_po_node)
    builder.add_node("risk_score", risk_score_node)
    builder.add_node("approval_gate", approval_gate_node)
    builder.add_node("post_to_erp_mock", post_to_erp_mock_node)

    builder.add_edge(START, "save_uploads")
    builder.add_edge("save_uploads", "extract_invoice")
    builder.add_edge("extract_invoice", "extract_po")
    builder.add_edge("extract_po", "validate_extraction")
    builder.add_edge("validate_extraction", "duplicate_check")
    builder.add_edge("duplicate_check", "match_invoice_po")
    builder.add_edge("match_invoice_po", "risk_score")
    builder.add_edge("risk_score", "approval_gate")
    builder.add_edge("approval_gate", "post_to_erp_mock")
    builder.add_edge("post_to_erp_mock", END)

    checkpointer = InMemorySaver()
    return builder.compile(checkpointer=checkpointer)


graph = build_graph()
```

For production later, replace `InMemorySaver` with durable persistence. LangGraph docs explicitly separate checkpointers for thread state from stores for longer-term application data. ([LangChain Docs][6])

---

# 14. Add a CLI smoke test before FastAPI

Create `scripts/run_demo.py`.

```bash
mkdir scripts
touch scripts/run_demo.py
```

```python
from app.graph.workflow import graph

config = {"configurable": {"thread_id": "demo-invoice-001"}}

result = graph.invoke(
    {
        "invoice_path": "data/samples/invoice_001.pdf",
        "po_path": None,
    },
    config=config,
)

print(result)
```

Run:

```bash
python scripts/run_demo.py
```

Goal:

* graph runs
* interrupt appears if risk is high
* no API yet

---

# 15. Add resume-after-approval script

LangGraph resumes an interrupted graph by invoking again with `Command(resume=...)`. ([LangChain Docs][5])

Create `scripts/approve_demo.py`.

```python
from langgraph.types import Command
from app.graph.workflow import graph

config = {"configurable": {"thread_id": "demo-invoice-001"}}

result = graph.invoke(
    Command(resume={"status": "approved", "reviewer": "mohammad"}),
    config=config,
)

print(result)
```

Run:

```bash
python scripts/approve_demo.py
```

---

# 16. Add FastAPI upload endpoint

Create `app/main.py`.

```python
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, UploadFile
from langgraph.types import Command

from app.graph.workflow import graph

app = FastAPI(title="Invoice-to-Pay Agent")

UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@app.post("/runs")
async def create_run(
    invoice: UploadFile = File(...),
    po: UploadFile | None = File(None),
):
    run_id = str(uuid4())

    invoice_path = UPLOAD_DIR / f"{run_id}_{invoice.filename}"
    invoice_path.write_bytes(await invoice.read())

    po_path = None
    if po:
        po_path = UPLOAD_DIR / f"{run_id}_{po.filename}"
        po_path.write_bytes(await po.read())

    config = {"configurable": {"thread_id": run_id}}

    result = graph.invoke(
        {
            "run_id": run_id,
            "invoice_path": str(invoice_path),
            "po_path": str(po_path) if po_path else None,
        },
        config=config,
    )

    return {"run_id": run_id, "result": result}


@app.post("/runs/{run_id}/approve")
async def approve_run(run_id: str):
    config = {"configurable": {"thread_id": run_id}}

    result = graph.invoke(
        Command(resume={"status": "approved", "reviewer": "api_user"}),
        config=config,
    )

    return {"run_id": run_id, "result": result}


@app.post("/runs/{run_id}/reject")
async def reject_run(run_id: str):
    config = {"configurable": {"thread_id": run_id}}

    result = graph.invoke(
        Command(resume={"status": "rejected", "reviewer": "api_user"}),
        config=config,
    )

    return {"run_id": run_id, "result": result}
```

Run:

```bash
uvicorn app.main:app --reload
```

Test upload:

```bash
curl -X POST "http://localhost:8000/runs" \
  -F "invoice=@data/samples/invoice_001.pdf"
```

---

# 17. Add streaming later, not now

After the basic API works, add streaming so the UI can show each node update. LangGraph supports streaming state updates with `stream_mode="updates"` and full state values with `stream_mode="values"`. ([LangChain Docs][7])

TODO later:

```text
POST /runs/stream
GET /runs/{run_id}/events
```

---

# 18. Add tests in this order

## `tests/test_schemas.py`

* valid invoice passes
* missing invoice number fails
* negative total fails

## `tests/test_matching.py`

* matching total passes
* mismatch total fails
* missing PO returns `invoice_only`

## `tests/test_graph.py`

* low-risk invoice auto-approves
* high-risk invoice interrupts
* approved invoice posts to ERP mock
* rejected invoice does not post

---

# 19. Add audit log

First version: JSONL file.

Create `app/services/audit.py`.

```python
import json
from pathlib import Path

AUDIT_PATH = Path("data/processed/audit.jsonl")
AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)


def write_audit_events(run_id: str, events: list[dict]) -> None:
    with AUDIT_PATH.open("a", encoding="utf-8") as f:
        for event in events:
            f.write(json.dumps({"run_id": run_id, **event}, default=str) + "\n")
```

Add `write_audit_log_node` later.

Important LangGraph note: when graphs resume after interrupts, node code may rerun from the beginning of the node, so side effects should be idempotent. Use append IDs, upserts, or “already written?” checks before writing to DB/files. ([LangChain Docs][1])

---

# 20. Add LLM extraction only after deterministic baseline works

Replace `extract_invoice_stub()` with:

```text
extract_invoice_llm(text) -> Invoice
```

Tiny TODO:

* Give model the Pydantic JSON schema.
* Ask for JSON only.
* Validate with `Invoice.model_validate_json(...)`.
* If validation fails, run one repair prompt.
* If repair fails, route to human review.

Pydantic is useful here because it gives both runtime validation and JSON Schema generation. ([Pydantic][8])

---

# 21. Add Docker Compose

First services:

```yaml
services:
  api:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./data:/app/data
```

Later add:

```text
postgres
minio
mlflow
langfuse
```

Do not add everything on day 1. That is how one-week prototypes go to die. Tiny monster, then bigger monster.

---

# 22. GitHub README checklist

Your README should show hiring managers the production thinking:

```text
# Invoice-to-Pay Agent

## Problem
Finance teams waste time on invoice extraction, PO matching, duplicate checks, approvals, and ERP handoff.

## Demo
GIF / screenshots

## Architecture
LangGraph workflow diagram

## Features
- Upload invoice + PO
- Extract strict JSON
- Validate with Pydantic
- Duplicate check
- 2-way match
- Risk score
- Human approval with LangGraph interrupt
- ERP mock post
- Audit log

## Run locally
docker compose up

## Evaluation
- extraction accuracy
- validation failure rate
- duplicate detection
- mismatch detection
- approval routing accuracy

## Production roadmap
- PostgreSQL persistence
- MinIO storage
- Azure Blob / ADLS mapping
- Databricks/Spark batch processing
- MLflow eval tracking
- Langfuse tracing
```

---

# Your first coding order

Do exactly this:

1. Create repo skeleton.
2. Add Pydantic invoice/PO schemas.
3. Add text extraction from PDF.
4. Add deterministic invoice stub extractor.
5. Add LangGraph state.
6. Add graph nodes one by one.
7. Compile graph with `InMemorySaver`.
8. Run CLI smoke test.
9. Add interrupt approval.
10. Add approve/reject resume scripts.
11. Add FastAPI upload endpoint.
12. Add tests.
13. Add JSONL audit log.
14. Add Docker.
15. Replace stub extraction with LLM extraction.
16. Add PostgreSQL.
17. Add Streamlit approval dashboard.
18. Add MLflow/Ragas evals.
19. Add MinIO.
20. Add PySpark/Databricks-style batch processing.

The **first deliverable** should be a working CLI graph with human approval. Once that works, the API/UI/storage layers are just boring engineering — the good kind.

[1]: https://docs.langchain.com/oss/python/langgraph/graph-api?utm_source=chatgpt.com "Graph API overview - Docs by LangChain"
[2]: https://fastapi.tiangolo.com/tutorial/request-files/?utm_source=chatgpt.com "Request Files"
[3]: https://pydantic.dev/docs/validation/latest/concepts/models/?utm_source=chatgpt.com "Models | Pydantic Docs"
[4]: https://docs.langchain.com/oss/python/langgraph/use-graph-api?utm_source=chatgpt.com "Use the graph API - Docs by LangChain"
[5]: https://docs.langchain.com/oss/python/langgraph/interrupts?utm_source=chatgpt.com "Interrupts - Docs by LangChain"
[6]: https://docs.langchain.com/oss/python/langgraph/persistence?utm_source=chatgpt.com "Persistence - Docs by LangChain"
[7]: https://docs.langchain.com/oss/python/langgraph/streaming?utm_source=chatgpt.com "Streaming - Docs by LangChain"
[8]: https://pydantic.dev/docs/validation/latest/concepts/json_schema/?utm_source=chatgpt.com "JSON Schema | Pydantic Docs"

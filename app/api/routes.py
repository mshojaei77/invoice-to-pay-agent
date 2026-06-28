from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, UploadFile
from langgraph.types import Command

from app.graph.workflow import build_graph

router = APIRouter()

RUNS: dict[str, dict] = {}
RUN_GRAPHS: dict[str, object] = {}


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.post("/runs")
async def create_run(files: list[UploadFile] = File(...)) -> dict:
    run_id = str(uuid4())
    upload_dir = Path("data/uploads") / run_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    uploaded_documents = []

    for file in files:
        path = upload_dir / file.filename
        path.write_bytes(await file.read())
        uploaded_documents.append(
            {
                "path": str(path),
                "filename": file.filename,
                "document_type": "unknown",
            }
        )

    graph = build_graph()
    result = graph.invoke(
        {"run_id": run_id, "uploaded_documents": uploaded_documents},
        config={"configurable": {"thread_id": run_id}},
    )

    RUNS[run_id] = result
    RUN_GRAPHS[run_id] = graph

    if result.get("requires_human_approval"):
        status = "requires_approval"
    elif (result.get("erp_result") or {}).get("status") == "posted":
        status = "posted"
    else:
        status = "completed"

    return {"run_id": run_id, "status": status, "result": result}


@router.get("/runs/{run_id}")
def get_run(run_id: str) -> dict:
    return RUNS.get(run_id, {"status": "not_found"})


@router.post("/runs/{run_id}/approve")
def approve_run(run_id: str) -> dict:
    return _resume_run(
        run_id,
        {"status": "approved", "approved_by": "api"},
    )


@router.post("/runs/{run_id}/reject")
def reject_run(run_id: str) -> dict:
    return _resume_run(
        run_id,
        {"status": "rejected", "approved_by": "api"},
    )


@router.get("/runs/{run_id}/audit")
def get_audit(run_id: str) -> dict:
    audit_path = Path("data/processed/audit.jsonl")
    if not audit_path.exists():
        return {"run_id": run_id, "events": []}

    events = [
        line
        for line in audit_path.read_text(encoding="utf-8").splitlines()
        if f'"run_id": "{run_id}"' in line
    ]
    return {"run_id": run_id, "events": events}


def _resume_run(run_id: str, approval: dict) -> dict:
    graph = RUN_GRAPHS.get(run_id)
    if graph is None:
        return {"run_id": run_id, "status": "not_found"}

    current = RUNS.get(run_id, {})
    if "__interrupt__" not in current:
        return {
            "run_id": run_id,
            "status": "not_waiting_for_approval",
            "result": current,
        }

    result = graph.invoke(
        Command(resume=approval),
        config={"configurable": {"thread_id": run_id}},
    )
    RUNS[run_id] = result

    erp_status = (result.get("erp_result") or {}).get("status")
    if approval["status"] == "rejected":
        status = "rejected"
    elif erp_status == "posted":
        status = "posted"
    else:
        status = "completed"

    return {"run_id": run_id, "status": status, "result": result}

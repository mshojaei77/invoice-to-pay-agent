from fastapi.testclient import TestClient
from pathlib import Path

from app.api.main import app
from app.api.routes import RUNS, RUN_GRAPHS

client = TestClient(app)
SAMPLE_INVOICE = Path("samples/invoice_001_canada_post_sample.pdf")


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_run_with_files(tmp_path) -> None:
    import pathlib
    original_cwd = pathlib.Path.cwd
    pathlib.Path.cwd = lambda: tmp_path

    try:
        response = client.post(
            "/runs",
            files=[
                ("files", (SAMPLE_INVOICE.name, SAMPLE_INVOICE.read_bytes(), "application/pdf")),
            ],
        )
        assert response.status_code == 200
        data = response.json()
        assert "run_id" in data
        assert data["status"] in {"posted", "completed", "requires_approval"}
    finally:
        pathlib.Path.cwd = original_cwd


def test_get_run_not_found() -> None:
    response = client.get("/runs/non-existent")
    assert response.status_code == 200
    assert response.json()["status"] == "not_found"


def test_get_audit_empty() -> None:
    response = client.get("/runs/test-run-001/audit")
    assert response.status_code == 200
    assert response.json() == {"run_id": "test-run-001", "events": []}


def test_approve_not_found() -> None:
    RUNS.clear()
    RUN_GRAPHS.clear()

    response = client.post("/runs/test-run-001/approve")
    assert response.status_code == 200
    assert response.json()["status"] == "not_found"


def test_reject_not_found() -> None:
    RUNS.clear()
    RUN_GRAPHS.clear()

    response = client.post("/runs/test-run-001/reject")
    assert response.status_code == 200
    assert response.json()["status"] == "not_found"


def test_approve_resumes_waiting_run() -> None:
    run_id = "waiting-approval-run"
    RUNS.clear()
    RUN_GRAPHS.clear()
    RUNS[run_id] = {"__interrupt__": [{"value": {"run_id": run_id}}]}
    RUN_GRAPHS[run_id] = FakeGraph(
        {
            "run_id": run_id,
            "approval": {"status": "approved", "approved_by": "api"},
            "erp_result": {"status": "posted"},
        }
    )

    response = client.post(f"/runs/{run_id}/approve")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "posted"
    assert RUNS[run_id]["approval"]["status"] == "approved"


def test_reject_resumes_waiting_run() -> None:
    run_id = "waiting-reject-run"
    RUNS.clear()
    RUN_GRAPHS.clear()
    RUNS[run_id] = {"__interrupt__": [{"value": {"run_id": run_id}}]}
    RUN_GRAPHS[run_id] = FakeGraph(
        {
            "run_id": run_id,
            "approval": {"status": "rejected", "approved_by": "api"},
            "erp_result": {"status": "not_posted"},
        }
    )

    response = client.post(f"/runs/{run_id}/reject")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "rejected"
    assert RUNS[run_id]["approval"]["status"] == "rejected"


class FakeGraph:
    def __init__(self, result: dict) -> None:
        self.result = result

    def invoke(self, command, config: dict) -> dict:
        assert command.resume["status"] in {"approved", "rejected"}
        assert config["configurable"]["thread_id"] == self.result["run_id"]
        return self.result

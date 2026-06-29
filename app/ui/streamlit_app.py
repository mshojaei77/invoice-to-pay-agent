from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any
from uuid import uuid4

import streamlit as st

from app.graph.workflow import build_graph
from scripts.run_demo import build_markdown_report


st.set_page_config(
    page_title="Invoice-to-Pay Agent",
    page_icon="I2P",
    layout="wide",
)


def main() -> None:
    st.title("Invoice-to-Pay Agent")
    st.caption("Upload invoice support, run the AP controls graph, and review the posting decision.")

    with st.sidebar:
        parser_name = st.selectbox("Parser", ["liteparse", "docling"], index=0)
        st.markdown("### Sample Scenarios")
        clean_demo = st.button("Load clean demo paths", use_container_width=True)
        exception_demo = st.button("Load exception demo path", use_container_width=True)

    if clean_demo:
        st.session_state["sample_paths"] = {
            "invoice": "samples/invoice_001_canada_post_sample.pdf",
            "po": "samples/purchase_order_001_polychemtex.pdf",
            "delivery_note": "samples/delivery_note_001_bunker_receipt.pdf",
        }
    if exception_demo:
        st.session_state["sample_paths"] = {
            "invoice": "samples/invoice_002_tax_sample_local_supply.pdf",
            "po": "",
            "delivery_note": "",
        }

    sample_paths = st.session_state.get("sample_paths", {})

    invoice_file = st.file_uploader("Invoice PDF", type=["pdf"])
    po_file = st.file_uploader("Purchase order PDF", type=["pdf"])
    delivery_file = st.file_uploader("Delivery note PDF", type=["pdf"])

    with st.expander("Use local sample paths"):
        invoice_path = st.text_input("Invoice path", value=sample_paths.get("invoice", ""))
        po_path = st.text_input("PO path", value=sample_paths.get("po", ""))
        delivery_path = st.text_input("Delivery note path", value=sample_paths.get("delivery_note", ""))

    if st.button("Run AP review", type="primary"):
        uploaded_documents = _build_uploaded_documents(
            invoice_file=invoice_file,
            po_file=po_file,
            delivery_file=delivery_file,
            invoice_path=invoice_path,
            po_path=po_path,
            delivery_path=delivery_path,
        )
        if not uploaded_documents:
            st.error("Provide at least an invoice PDF or invoice sample path.")
            return

        result = _run_graph(uploaded_documents, parser_name)
        st.session_state["latest_result"] = result
        st.session_state["latest_run_id"] = result["run_id"]

    latest = st.session_state.get("latest_result")
    if latest:
        _render_result(latest["result"], latest["run_id"])


def _build_uploaded_documents(
    *,
    invoice_file: Any,
    po_file: Any,
    delivery_file: Any,
    invoice_path: str,
    po_path: str,
    delivery_path: str,
) -> list[dict[str, str]]:
    documents: list[dict[str, str]] = []
    temp_dir = Path(tempfile.mkdtemp(prefix="invoice_to_pay_ui_"))

    for file_obj, document_type in [
        (invoice_file, "invoice"),
        (po_file, "purchase_order"),
        (delivery_file, "delivery_note"),
    ]:
        if file_obj is None:
            continue
        target = temp_dir / file_obj.name
        target.write_bytes(file_obj.getbuffer())
        documents.append({"path": str(target), "document_type": document_type})

    for path, document_type in [
        (invoice_path, "invoice"),
        (po_path, "purchase_order"),
        (delivery_path, "delivery_note"),
    ]:
        cleaned = path.strip()
        if cleaned:
            documents.append({"path": cleaned, "document_type": document_type})

    return documents


def _run_graph(uploaded_documents: list[dict[str, str]], parser_name: str) -> dict[str, Any]:
    run_id = str(uuid4())
    graph = build_graph()
    result = graph.invoke(
        {
            "run_id": run_id,
            "uploaded_documents": uploaded_documents,
            "parser_name": parser_name,
        },
        config={"configurable": {"thread_id": run_id}},
    )
    return {"run_id": run_id, "result": result}


def _render_result(result: dict[str, Any], run_id: str) -> None:
    final_status = "requires_approval" if "__interrupt__" in result else "completed"
    erp_status = "not_posted" if "__interrupt__" in result else (result.get("erp_result") or {}).get("status")
    exception_result = result.get("exception_result") or {}
    match_result = result.get("match_result") or {}
    approval_route = result.get("approval_route") or {}
    payment_plan = result.get("payment_plan") or {}
    fraud_result = result.get("fraud_result") or {}

    cols = st.columns(4)
    cols[0].metric("Final status", final_status)
    cols[1].metric("Risk", result.get("risk_level", "unknown"))
    cols[2].metric("ERP", erp_status or "unknown")
    cols[3].metric("Exceptions", exception_result.get("exception_count", 0))

    st.subheader("Controls")
    control_cols = st.columns(3)
    control_cols[0].write("**Match**")
    control_cols[0].json(match_result)
    control_cols[1].write("**Approval Route**")
    control_cols[1].json(approval_route)
    control_cols[2].write("**Payment Plan**")
    control_cols[2].json(payment_plan)

    st.subheader("Risk and Fraud")
    left, right = st.columns(2)
    left.write("**Risk reasons**")
    left.write(result.get("risk_reasons") or ["No risk reasons recorded."])
    right.write("**Fraud controls**")
    right.json(fraud_result)

    st.subheader("Audit Report")
    report = build_markdown_report(result, run_id)
    st.download_button(
        label="Download Markdown report",
        data=report,
        file_name=f"{run_id}-invoice-to-pay-report.md",
        mime="text/markdown",
    )
    st.markdown(report)


if __name__ == "__main__":
    main()

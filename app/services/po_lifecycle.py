from __future__ import annotations


def build_po_lifecycle_plan(
    uploaded_documents: list[dict],
    match_result: dict,
    approval_route: dict,
) -> dict:
    evidence = " ".join(
        f"{document.get('filename', '')} {document.get('path', '')}".lower()
        for document in uploaded_documents
    )
    document_types = {document.get("document_type") for document in uploaded_documents}
    has_po = "purchase_order" in document_types
    has_delivery = "delivery_note" in document_types
    inbound_signal = "inbound_shipment" in evidence or "shipment" in evidence

    return {
        "po_lifecycle_status": "matched" if match_result.get("match_status") == "matched" else "review_required",
        "supports_po_creation": True,
        "supports_po_approval": True,
        "purchase_type": "asset_purchase",
        "po_present": has_po,
        "receiving_evidence_present": has_delivery,
        "inbound_shipment_review": "required" if inbound_signal else "not_required_for_fixture",
        "matching_mode": "three_way_match" if has_po and has_delivery else "exception_match",
        "next_action": "release_to_invoice_approval" if has_po and has_delivery else "create_or_attach_po",
        "approval_route": approval_route.get("route"),
    }

from app.services.compliance import evaluate_compliance


def test_clean_supporting_documents_are_compliance_ready() -> None:
    result = evaluate_compliance(
        uploaded_documents=[
            {"document_type": "invoice"},
            {"document_type": "purchase_order"},
            {"document_type": "delivery_note"},
        ],
        exception_result={"exceptions": []},
        approval_route={"approver_role": "system"},
    )

    assert result["compliance_status"] == "ready"
    assert result["requires_role_based_access"] is True


def test_missing_support_requires_review() -> None:
    result = evaluate_compliance(
        uploaded_documents=[{"document_type": "invoice"}],
        exception_result={"exceptions": [{"code": "missing_po"}]},
        approval_route={"approver_role": "buyer_or_receiving_owner"},
    )

    assert result["compliance_status"] == "review"
    statuses = {control["control"]: control["status"] for control in result["controls"]}
    assert statuses["invoice_supporting_evidence"] == "review"

from __future__ import annotations


def build_spend_intelligence(
    uploaded_documents: list[dict],
    gl_coding_result: dict,
    exception_result: dict,
    match_result: dict,
) -> dict:
    path_text = " ".join(
        f"{document.get('filename', '')} {document.get('path', '')}".lower()
        for document in uploaded_documents
    )
    categories = set(exception_result.get("categories", []))
    mismatch_reasons = set(match_result.get("mismatch_reasons", []))

    opportunities = []
    if "pricing" in categories or "total_mismatch" in mismatch_reasons:
        opportunities.append(
            {
                "type": "contract_leakage",
                "severity": "high",
                "recommendation": "Compare invoice totals against contract or rate-card terms before posting.",
            }
        )
    if "duplicate_control" in categories:
        opportunities.append(
            {
                "type": "duplicate_spend",
                "severity": "critical",
                "recommendation": "Block payment and reconcile against prior invoice references.",
            }
        )
    if "aws" in path_text or "saas" in path_text or "plugin" in path_text:
        opportunities.append(
            {
                "type": "software_spend_consolidation",
                "severity": "medium",
                "recommendation": "Review vendor ownership and renewal terms for consolidation or cancellation.",
            }
        )

    return {
        "spend_status": "opportunities_found" if opportunities else "monitored",
        "category": gl_coding_result.get("cost_center") or "uncategorized",
        "gl_account": gl_coding_result.get("gl_account"),
        "opportunity_count": len(opportunities),
        "opportunities": opportunities,
    }

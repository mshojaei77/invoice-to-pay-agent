from __future__ import annotations


def evaluate_multi_company_controls(
    uploaded_documents: list[dict],
    accounting_platform_profile: dict,
) -> dict:
    evidence = " ".join(
        str(document.get("filename") or document.get("path") or "")
        for document in uploaded_documents
    ).lower()
    entity = "default_entity"
    if "uk" in evidence or "gbp" in evidence:
        entity = "uk_entity"
    elif "eu" in evidence or "eur" in evidence:
        entity = "eu_entity"
    elif "us" in evidence or "usd" in evidence:
        entity = "us_entity"

    supports_multi_company = bool(accounting_platform_profile.get("supports_multi_company"))
    return {
        "entity_code": entity,
        "intercompany_review_required": "intercompany" in evidence,
        "accountant_collaboration_enabled": bool(accounting_platform_profile.get("supports_accountant_collaboration")),
        "multi_company_supported": supports_multi_company,
        "control_status": "ready" if supports_multi_company or entity == "default_entity" else "review",
        "consolidation_note": "Entity, tax, and dimensions should remain explicit for group reporting.",
    }

from __future__ import annotations


VENDOR_RULES = {
    "aws": {"gl_account": "6200-cloud-services", "cost_center": "engineering", "confidence": 0.9},
    "fedex": {"gl_account": "5400-freight", "cost_center": "operations", "confidence": 0.85},
    "canada post": {"gl_account": "5400-postage", "cost_center": "operations", "confidence": 0.85},
    "wordpress": {"gl_account": "6250-software-subscriptions", "cost_center": "marketing", "confidence": 0.8},
}

KEYWORD_RULES = {
    "freight": {"gl_account": "5400-freight", "cost_center": "operations", "confidence": 0.75},
    "shipping": {"gl_account": "5400-freight", "cost_center": "operations", "confidence": 0.75},
    "software": {"gl_account": "6250-software-subscriptions", "cost_center": "engineering", "confidence": 0.7},
    "consulting": {"gl_account": "6100-professional-services", "cost_center": "finance", "confidence": 0.7},
    "maintenance": {"gl_account": "6300-maintenance", "cost_center": "operations", "confidence": 0.7},
}


def suggest_gl_coding(uploaded_documents: list[dict], parsed_documents: list[dict] | None = None) -> dict:
    evidence = " ".join(
        [
            *(str(document.get("filename") or document.get("path") or "") for document in uploaded_documents),
            *(str(document.get("text") or document.get("markdown") or "") for document in parsed_documents or []),
        ]
    ).lower()

    for vendor_hint, coding in VENDOR_RULES.items():
        if vendor_hint in evidence:
            return _result(coding, "vendor_history", vendor_hint)

    for keyword, coding in KEYWORD_RULES.items():
        if keyword in evidence:
            return _result(coding, "description_keyword", keyword)

    return {
        "coding_status": "needs_review",
        "gl_account": None,
        "cost_center": None,
        "allocation": [],
        "confidence": 0.0,
        "reason": "no_vendor_or_description_rule",
    }


def _result(coding: dict, rule_type: str, matched_rule: str) -> dict:
    return {
        "coding_status": "suggested",
        "gl_account": coding["gl_account"],
        "cost_center": coding["cost_center"],
        "allocation": [{"cost_center": coding["cost_center"], "percentage": 100}],
        "confidence": coding["confidence"],
        "reason": rule_type,
        "matched_rule": matched_rule,
    }

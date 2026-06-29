from __future__ import annotations


def assess_fraud_controls(
    uploaded_documents: list[dict],
    duplicate_result: dict,
    match_result: dict,
    business_rule_errors: list[dict],
    risk_level: str,
) -> dict:
    evidence = " ".join(
        f"{document.get('filename', '')} {document.get('path', '')}".lower()
        for document in uploaded_documents
    )
    signals = []

    if duplicate_result.get("duplicate_status") != "clear":
        signals.append({"signal": "duplicate_invoice", "severity": "critical"})
    if any("vendor_mismatch" in reason for reason in match_result.get("mismatch_reasons", [])):
        signals.append({"signal": "vendor_mismatch", "severity": "high"})
    if any(error.get("code") in {"missing_iban", "invalid_iban", "missing_vendor"} for error in business_rule_errors):
        signals.append({"signal": "vendor_payment_master_gap", "severity": "high"})
    if any(token in evidence for token in ("bank_change", "new_bank", "urgent_payment", "wire_change")):
        signals.append({"signal": "payment_instruction_change", "severity": "critical"})
    if risk_level == "high" and not signals:
        signals.append({"signal": "high_process_risk", "severity": "medium"})

    return {
        "fraud_status": "blocked" if any(item["severity"] == "critical" for item in signals) else "monitored",
        "signal_count": len(signals),
        "signals": signals,
        "controls": [
            {"control": "duplicate_detection", "status": duplicate_result.get("duplicate_status", "unknown")},
            {"control": "vendor_match", "status": "review" if any("vendor" in reason for reason in match_result.get("mismatch_reasons", [])) else "clear"},
            {"control": "payment_instruction_change_review", "status": "review" if any(item["signal"] == "payment_instruction_change" for item in signals) else "clear"},
        ],
    }

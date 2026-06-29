from __future__ import annotations


def classify_exceptions(
    business_rule_errors: list[dict],
    duplicate_result: dict,
    match_result: dict,
    parser_warnings: list | None = None,
) -> dict:
    exceptions: list[dict] = []

    def add(code: str, category: str, severity: str, message: str, action: str) -> None:
        exceptions.append(
            {
                "code": code,
                "category": category,
                "severity": severity,
                "message": message,
                "recommended_action": action,
            }
        )

    for error in business_rule_errors:
        code = str(error.get("code", "business_rule_error"))
        severity = str(error.get("severity", "medium"))
        if code == "missing_po":
            add(code, "matching", severity, "Invoice has no matching purchase order.", "Request PO support or route to non-PO approval.")
        elif code == "missing_delivery_note":
            add(code, "receiving", severity, "Invoice has no delivery or receipt evidence.", "Request delivery note, goods receipt, or service acceptance.")
        elif code in {"missing_iban", "invalid_iban", "missing_vat", "invalid_vat", "missing_vendor"}:
            add(code, "vendor_master_data", severity, "Payment-critical vendor data is missing or invalid.", "Send to vendor-master review before posting.")
        else:
            add(code, "business_rule", severity, str(error.get("message", code)), "Review the source document and supporting evidence.")

    duplicate_status = duplicate_result.get("duplicate_status")
    if duplicate_status == "possible_duplicate":
        add("possible_duplicate", "duplicate_control", "medium", "A similar invoice may already exist.", "Compare vendor, invoice number, amount, and payment history.")
    elif duplicate_status == "confirmed_duplicate":
        add("confirmed_duplicate", "duplicate_control", "critical", "A duplicate invoice was detected.", "Block posting unless finance explicitly overrides.")

    for reason in match_result.get("mismatch_reasons", []):
        category = "matching"
        action = "Investigate the invoice, PO, and receipt before posting."
        if "delivery" in reason:
            category = "receiving"
            action = "Confirm received quantity/status with operations or warehouse."
        elif reason in {"subtotal_mismatch", "tax_mismatch", "total_mismatch"}:
            category = "pricing"
            action = "Check freight, tax, discounts, and partial-order billing."
        elif reason == "vendor_mismatch":
            category = "vendor_master_data"
            action = "Confirm the legal vendor entity and remit-to account."
        add(f"match:{reason}", category, "high", f"3-way match failed: {reason}.", action)

    for warning in parser_warnings or []:
        add("parser_warning", "extraction_quality", "low", f"Parser warning: {warning}", "Review extracted fields if this run is otherwise high value.")

    categories = sorted({item["category"] for item in exceptions})
    highest = _highest_severity([item["severity"] for item in exceptions])

    return {
        "exception_status": "clear" if not exceptions else "open",
        "exception_count": len(exceptions),
        "highest_severity": highest,
        "categories": categories,
        "exceptions": exceptions,
    }


def _highest_severity(severities: list[str]) -> str:
    order = {"low": 1, "medium": 2, "high": 3, "critical": 4}
    if not severities:
        return "none"
    return max(severities, key=lambda item: order.get(item, 0))

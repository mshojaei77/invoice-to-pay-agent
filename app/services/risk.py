from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RiskResult:
    risk_level: str
    risk_score: float
    risk_reasons: list[str]
    requires_human_approval: bool


def calculate_risk(
    validation_errors: list[dict],
    business_rule_errors: list[dict],
    duplicate_result: dict,
    match_result: dict,
) -> RiskResult:
    score = 0.0
    reasons: list[str] = []

    def add(points: float, reason: str) -> None:
        nonlocal score
        score += points
        reasons.append(reason)

    if validation_errors:
        add(50, "schema_validation_errors")

    for err in business_rule_errors:
        code = err.get("code")
        if code in {"missing_po", "missing_delivery_note"}:
            add(15, code)
        elif code in {"invalid_iban", "missing_vendor"}:
            add(30, code)
        elif code in {"missing_iban", "missing_vat", "invalid_vat"}:
            add(15, code)
        elif code in {"handwritten_correction"}:
            add(35, code)
        elif code in {"low_parser_confidence"}:
            add(20, code)

    duplicate_status = duplicate_result.get("duplicate_status")
    if duplicate_status == "possible_duplicate":
        add(30, "possible_duplicate")
    elif duplicate_status == "confirmed_duplicate":
        add(100, "confirmed_duplicate")

    for reason in match_result.get("mismatch_reasons", []):
        add(25, f"match_mismatch:{reason}")

    if score >= 70:
        level = "high"
    elif score >= 25:
        level = "medium"
    else:
        level = "low"

    return RiskResult(
        risk_level=level,
        risk_score=min(score, 100.0),
        risk_reasons=reasons,
        requires_human_approval=level in {"medium", "high"},
    )

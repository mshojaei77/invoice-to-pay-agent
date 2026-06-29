from __future__ import annotations


def estimate_ai_cost_snapshot(
    parsed_documents: list[dict],
    parser_route: list[dict],
    model_cost_per_1k_tokens: float = 0.0,
) -> dict:
    text = "\n".join(
        str(document.get("text") or document.get("markdown") or "")
        for document in parsed_documents
    )
    estimated_tokens = max(1, len(text) // 4) if text else 0
    estimated_cost = round((estimated_tokens / 1000) * model_cost_per_1k_tokens, 6)

    return {
        "budget_category": "ai_automation_usage",
        "estimated_input_tokens": estimated_tokens,
        "estimated_cost_usd": estimated_cost,
        "cost_model": "character_estimate",
        "parser_calls": len(parser_route),
        "cost_policy": "track_tokens_as_finance_line_item",
    }

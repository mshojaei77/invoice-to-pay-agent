from app.services.ai_costs import estimate_ai_cost_snapshot


def test_estimates_tokens_from_parser_text() -> None:
    result = estimate_ai_cost_snapshot(
        parsed_documents=[{"text": "abcd" * 100}],
        parser_route=[{"parser": "liteparse"}],
        model_cost_per_1k_tokens=0.01,
    )

    assert result["estimated_input_tokens"] == 100
    assert result["estimated_cost_usd"] == 0.001
    assert result["cost_policy"] == "track_tokens_as_finance_line_item"

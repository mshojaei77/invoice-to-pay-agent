# Contributing

Thanks for considering a contribution. This project is an early, runnable AP automation prototype, so contributions should keep the workflow inspectable and reproducible.

## Development Setup

```bash
uv sync
uv run pytest
uv run python scripts/run_demo.py --invoice samples/invoice_001_canada_post_sample.pdf --po samples/purchase_order_001_polychemtex.pdf --delivery-note samples/delivery_note_001_bunker_receipt.pdf
```

Use `uv add <package>` for dependency changes and commit both `pyproject.toml` and `uv.lock`.

## Contribution Guidelines

- Keep API routes thin and put business behavior in `app/services/`.
- Keep LangGraph nodes small, typed, and easy to inspect.
- Prefer deterministic controls over hidden prompt decisions.
- Add tests for schema, service, graph, or API behavior changes.
- Use sample PDFs or small fixtures that are safe to publish.
- Do not commit real invoices, credentials, bank details, tax identifiers, or customer data.

## Pull Requests

Before opening a PR, run:

```bash
uv run pytest
uv run python -m compileall app tests scripts
```

For large workflow changes, include a short before/after demo command and the resulting status fields.

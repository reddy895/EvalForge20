# Contributing to EvalForge20

Thanks for helping improve EvalForge20.

## Development setup

1. Fork and clone the repository.
2. Create a virtual environment and install backend dev dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e ".[dev]"
   ```
3. Install frontend dependencies:
   ```bash
   cd frontend && npm ci
   ```

## Before opening a pull request

Run all relevant checks:

```bash
ruff check backend/src tests backend/tests
pytest -v
cd frontend && npx tsc -b && npm test && npm run build
```

Guidelines:

- Keep changes focused and add tests for new behavior.
- Do not commit secrets, `.env` files, databases, uploaded datasets, or build outputs.
- New evaluators must document inputs, scoring methodology, whether they are deterministic or estimates, and include tests.
- Never fabricate benchmark data or emit mock metrics as real measurements.
- Update documentation when behavior or configuration changes.
- Use truthful conventional commit messages.

## Adding an evaluator

1. Implement the evaluator in `backend/src/evalforge/evaluators/`.
2. Register it where evaluator selection is built (see `backend/src/evalforge/experiments/case_runner.py`).
3. Add unit tests with deterministic inputs covering edge cases.
4. Document the metric definition and limitations.

## Adding a provider

1. Implement the adapter against `BaseProvider`.
2. Register it in `backend/src/evalforge/providers/registry.py`.
3. Add configuration settings and `.env.example` entries.
4. Add connection-testing and error-normalization tests.
5. Do not claim a provider is verified unless you have actually run it against the provider.

## Reporting bugs

Include reproduction steps, expected vs actual behavior, environment, and relevant logs (redact secrets).

By contributing, you agree that your contributions are licensed under the project's AGPL-3.0-only license.

# EvalForge20 Testing Strategy

## 1. Overview

EvalForge20 enforces strict test discipline:
- Zero external internet or paid API dependencies required for default test runs.
- Isolated test databases via pytest fixtures (`tmp_path`).
- Mock providers and deterministic mock agents for fast, reproducible CI execution.

## 2. Running Tests

Run the complete test suite:
```bash
./.venv/bin/pytest
```

Run tests with verbose output and duration reporting:
```bash
./.venv/bin/pytest -v --durations=10
```

Run specific test modules:
```bash
# Unit tests
./.venv/bin/pytest tests/unit/

# Integration tests
./.venv/bin/pytest tests/integration/
```

## 3. Code Style & Linting

Format and check with Ruff:
```bash
./.venv/bin/ruff check .
./.venv/bin/ruff format .
```

## 4. Test Coverage Summary

- **Unit Tests**:
  - `test_config_logging.py`: Settings validation and secret redaction.
  - `test_domain_models.py`: State machines and Pydantic domain models.
  - `test_dataset_management.py`: JSONL parsing, validation, duplicate IDs, content hashing.
  - `test_evaluators.py`: Exact match, normalized match, JSON validity, schema, task assertions, summary aggregation.
  - `test_composite_evaluator.py`: Explicitly weighted composite scoring with component transparency.
  - `test_providers.py`: Mock provider, error simulation, Ollama adapter with httpx mocks.
  - `test_runner.py`: Concurrency semaphores, retry policies, streaming persistence.
  - `test_langsmith_integration.py`: Tracing, dataset sync, experiment logging, graceful offline degradation.
  - `test_rag_evaluators.py`: Context precision/recall @ K, hit rate, MRR, groundedness overlap.
  - `test_agent_evaluator.py`: Task completion, trajectory tool accuracy, argument validity, step limits.
  - `test_security_redaction.py`: Redacting secrets and sensitive prompts in JSON reports.
- **Integration Tests**:
  - `test_persistence_reporting.py`: SQLite persistence, migrations, and JSON report generation.
  - `test_api_cli.py`: FastAPI endpoints and Typer CLI commands.
  - `test_full_workflow_regressions.py`: Regression gate detection and candidate run comparisons.

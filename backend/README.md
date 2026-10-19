# EvalForge20 — Python Backend

This directory documents the Python FastAPI backend for EvalForge20. The actual
source code lives in `../app/` at the repository root, as the project was
structured before the `backend/` directory convention was adopted.

## Why `app/` instead of `backend/app/`?

The existing codebase was built with `app/` at the repository root, which is a
valid FastAPI layout. Moving it into `backend/app/` would require updating all
imports, CI workflows, and the installed package path. To preserve working
functionality without introducing breaking regressions, the canonical source
remains at the root-level `app/`.

This `backend/` directory exists as the structural marker required by the spec
and contains the up-to-date runtime documentation, environment template, and
requirements mirror.

## Quick Start

```bash
# From the repository root
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Optional dev dependencies (tests, linting)
pip install -r requirements-dev.txt

# Start the API server (development mode)
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

> **Windows:** Use `.venv\Scripts\activate` instead of `source .venv/bin/activate`.

## Environment Configuration

Copy `.env.example` (at the repository root) to `.env` and edit as needed:

```bash
cp .env.example .env
```

Key variables:

| Variable | Default | Description |
|---|---|---|
| `EVALFORGE20_DATABASE_URL` | `sqlite:///./data/evalforge20.db` | SQLite database path |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Local Ollama server URL |
| `OLLAMA_MODEL` | `qwen2.5:3b` | Default model for evaluations |
| `EVALFORGE20_ENV` | `development` | Environment tag |

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Liveness check |
| GET | `/ready` | Readiness with provider status |
| GET | `/v1/ollama/status` | Real Ollama connection status and installed models |
| GET | `/v1/models` | Detailed list of installed Ollama models |
| POST | `/v1/ollama/models/pull` | Initiate model download (explicit user action) |
| GET | `/v1/catalog/models` | Full model catalog across all providers |
| GET | `/v1/evaluations` | List evaluation runs |
| POST | `/v1/evaluations` | Create and run an evaluation |
| GET | `/v1/evaluations/{run_id}` | Run details and aggregated metrics |
| GET | `/v1/evaluations/{run_id}/results` | Per-case results |
| GET | `/v1/evaluations/{run_id}/failures` | Failure analysis |
| POST | `/v1/compare` | Compare two evaluation runs |
| GET | `/v1/datasets` | List available datasets |
| POST | `/v1/datasets/validate` | Validate dataset content |

Full interactive documentation is available at `http://127.0.0.1:8000/docs`
after starting the server.

## Project Structure

```
app/                        ← Backend source (repository root)
├── main.py                 ← FastAPI application entrypoint
├── config.py               ← Environment-based settings
├── api/routes/             ← HTTP route handlers
│   ├── health.py           ← /health, /ready
│   ├── ollama.py           ← /v1/ollama/*, /v1/models
│   ├── evaluations.py      ← /v1/evaluations/*
│   ├── comparisons.py      ← /v1/compare/*
│   ├── datasets.py         ← /v1/datasets/*
│   ├── catalog.py          ← /v1/catalog/*
│   └── ...
├── providers/              ← Provider adapters
│   ├── ollama.py           ← Local Ollama adapter
│   ├── ollama_diagnostics.py ← Health check with real HTTP probe
│   ├── openai.py           ← OpenAI adapter
│   ├── anthropic.py        ← Anthropic Claude adapter
│   ├── gemini.py           ← Google Gemini adapter
│   ├── nvidia.py           ← NVIDIA NIM adapter
│   ├── mock.py             ← Deterministic mock (no model required)
│   └── custom_openai.py    ← OpenAI-compatible custom endpoint
├── evaluators/             ← Deterministic and LLM-judge evaluators
├── storage/                ← SQLAlchemy models and SQLite persistence
├── runner/                 ← Concurrent evaluation execution engine
├── catalog/                ← Model catalog service
├── pricing/                ← Pricing catalog and cost estimator
└── ...
```

## Running Tests

```bash
# All tests (unit + integration)
pytest -v

# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# With coverage
pytest --cov=app tests/
```

## Linting and Formatting

```bash
# Check
ruff check .
ruff format --check .

# Auto-fix
ruff check --fix .
ruff format .
```

## Ollama Setup

EvalForge20's primary local inference path uses [Ollama](https://ollama.com).

```bash
# Check if installed
ollama --version

# Start the server (if not running as a service)
ollama serve

# List installed models
ollama list

# Pull a small model for testing
ollama pull qwen2.5:3b
```

Common diagnostic states returned by `/v1/ollama/status`:

| `status_label` | Meaning |
|---|---|
| `online` | Ollama is running and has models installed |
| `no_models_installed` | Ollama is running but no models are pulled |
| `offline` | Ollama is not running or OLLAMA_BASE_URL is wrong |

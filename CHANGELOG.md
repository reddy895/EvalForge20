# Changelog

All notable changes to **EvalForge20** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-10-15

### Added
- **Core Domain & State Machine**: Pydantic v2 domain schemas, normalized error taxonomy (`NormalizedErrorCategory`), and lifecycle state transitions (`PENDING`, `RUNNING`, `COMPLETED`, `COMPLETED_WITH_ERRORS`, `FAILED`, `CANCELLED`).
- **Dataset Management**: JSONL parser with line-specific error tracking, duplicate case ID detection, and canonical SHA-256 content hashing.
- **Deterministic Code Evaluators**: Exact Match, Normalized Match, JSON Validity, JSON Schema Validation, Predefined Task Assertions.
- **Weighted Composite Evaluator**: Transparent weighted scoring across component metrics without hiding individual failures.
- **Provider Adapters**: Provider-neutral contract, Deterministic Mock Provider with simulated errors/latency/canned responses, and Ollama HTTP API adapter.
- **Evaluation Runner**: Asynchronous runner with bounded concurrency (`asyncio.Semaphore`), safe retry policy with exponential backoff, and streaming case persistence.
- **Storage & Relational Schema**: SQLite storage with SQLAlchemy 2.0 ORM, Alembic schema migrations, and per-case indexing.
- **Standardized JSON Exporter**: Export reproducible JSON evaluation reports adhering to Section 14 with missing-data limitations tracking and optional secret/prompt redaction.
- **Dual Interfaces**: Typer-based Python CLI (`evalforge20`) and versioned FastAPI REST endpoints (`/v1/*`).
- **Optional LangSmith Integration**: Tracing adapter, connection diagnostics, dataset registration, and experiment synchronization that degrade gracefully offline.
- **Comparison & Regression Gates**: Run-to-run comparison, metric deltas, case-level pass-to-fail flip detection, and configurable quality thresholds.
- **RAG Evaluation**: Retrieval precision @ K, recall @ K, hit rate @ K, MRR @ K, and groundedness token overlap.
- **AI Agent Evaluation**: Task completion rate, tool selection accuracy, argument validity, step efficiency, and controlled deterministic mock agent runtime.

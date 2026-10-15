# EvalForge20 Architecture

## 1. System Overview

EvalForge20 is structured into clean, decoupled layers following Domain-Driven Design (DDD) principles:

```text
                  +---------------------------------------+
                  |         User Interfaces               |
                  |  FastAPI REST API   /   Typer CLI     |
                  +---------------------------------------+
                                      |
                                      v
                  +---------------------------------------+
                  |           Application Layer           |
                  |          EvaluationService            |
                  +---------------------------------------+
                                      |
                 +--------------------+--------------------+
                 |                                         |
                 v                                         v
+---------------------------------+       +---------------------------------+
|      Evaluation Runner          |       |      Persistence & Reporting    |
| - Concurrency (asyncio Sem)     |       | - SQLite / SQLAlchemy           |
| - Safe Retries with Backoff     |       | - Alembic Schema Migrations     |
| - Per-Case Streaming Storage    |       | - Standardized JSON Exporter    |
+---------------------------------+       +---------------------------------+
       |                      |                            |
       v                      v                            v
+--------------+      +-------------------+      +--------------------+
|  Providers   |      |  Evaluator Engine |      | LangSmith (Opt)    |
| - Mock       |      | - Deterministic   |      | - Tracing          |
| - Ollama     |      | - Composite       |      | - Sync Datasets    |
+--------------+      | - RAG & Agent     |      | - Experiment Logs  |
                      +-------------------+      +--------------------+
```

## 2. Core Architectural Layers

1. **API Layer (`app/api/`)**:
   FastAPI router exposing health checks, model provider discovery, dataset validation, evaluation execution, case inspection, run comparisons, JSON reports, and LangSmith diagnostics.

2. **CLI Layer (`app/cli/`)**:
   Rich terminal interface built on Typer providing full parity with the REST API.

3. **Application Layer (`app/application/`)**:
   Shared orchestration service (`EvaluationService`) invoked by both CLI and API to prevent duplicated logic.

4. **Domain Layer (`app/domain/`)**:
   Pure Pydantic models, error classification (`NormalizedErrorCategory`), state machines (`EvaluationRunStatus`), and contracts (`ProviderContract`, `EvaluatorContract`).

5. **Dataset Layer (`app/datasets/`)**:
   JSONL stream parser with line-by-line validation, duplicate ID detection, and SHA-256 canonical content hashing.

6. **Provider Layer (`app/providers/`)**:
   Provider-neutral abstraction with automatic health checks, guarded timeout execution, and adapters for deterministic Mock targets and local Ollama inference.

7. **Evaluator Layer (`app/evaluators/`)**:
   Central registry pattern supporting deterministic code evaluators, weighted composite evaluators, RAG retrieval/groundedness evaluators, and AI agent trajectory evaluators.

8. **Storage Layer (`app/storage/`)**:
   SQLAlchemy ORM models, migration management via Alembic, and normalized relational SQLite schema.

9. **LangSmith Layer (`app/integrations/langsmith/`)**:
   Optional tracing and experiment synchronization that remains non-blocking and completely decoupled from local offline evaluation.

# Product Requirements Document (PRD) — EvalForge20

## 1. Executive Summary

**EvalForge20** is an open-source, local-first platform for evaluating, benchmarking, comparing, and monitoring Large Language Models (LLMs), Retrieval-Augmented Generation (RAG) systems, and AI agents.

EvalForge20 provides developers and teams with transparent, reproducible, and evidence-driven measurements across accuracy, reliability, latency, and resource consumption. Local model execution is natively supported via Ollama, while maintaining an extensible provider-agnostic interface and optional integration with LangSmith for tracing, dataset synchronization, and experiment management.

## 2. Problem Statement & Mission

### 2.1 The Problem
- **Benchmark Mismatch:** Public benchmark leaderboards rarely reflect domain-specific application workloads or custom system prompts.
- **Manual & Ad-hoc Testing:** Comparing model candidates or prompt iterations across hundreds of cases is tedious and error-prone.
- **Agent Failure Obscurity:** Multi-step tool use, reasoning errors, and execution loops are notoriously difficult to diagnose without structured step-by-step traces.
- **Silent Regressions:** Updates to prompts, dependencies, or base model weights frequently introduce subtle regressions.
- **Vendor Lock-in & Privacy Risks:** Commercial evaluation platforms often require streaming sensitive prompts and internal datasets to external cloud services.

### 2.2 The Mission
Empower developers to make evidence-based AI decisions using local-first, reproducible benchmarks, verifiable metrics, and transparent experiment tracking.

## 3. User Personas & Core Workflows

1. **AI Application Engineer:** Evaluates model alternatives (e.g., local Qwen 2.5 vs. hosted models) for a structured-output or classification workload.
2. **RAG Developer:** Measures retrieval context relevance, answer groundedness, and reference-based faithfulness.
3. **AI Agent Developer:** Validates multi-step tool selection, argument validity, task completion rate, and retry behavior.
4. **MLOps / Platform Engineer:** Runs regression tests in CI pipelines, setting pass/fail thresholds before deploying prompt or agent changes.

## 4. System Architecture & Layers

EvalForge20 is organized into clean architectural layers:
- **API Layer:** FastAPI REST endpoints for dataset validation, evaluation runs, comparisons, and reports.
- **CLI Layer:** Typer-based terminal commands mirroring API operations.
- **Application Layer:** Orchestration services coordinating execution workflows.
- **Domain Layer:** Core entity schemas, evaluator contracts, execution states, and error categories.
- **Dataset Layer:** JSONL parsing, line-specific error reporting, schema validation, and content hashing.
- **Provider Layer:** Extensible model adapters (Deterministic Mock, Ollama HTTP API, optional hosted providers).
- **Evaluator Layer:** Common evaluator contract, metric registry, deterministic scorers, LLM-as-judge, composite scorers, and summary evaluators.
- **RAG & Agent Layers:** Specialized retrieval and execution-trace evaluators.
- **LangSmith Layer:** Non-blocking, optional tracing, dataset synchronization, and experiment logging.
- **Storage Layer:** SQLAlchemy ORM models with SQLite persistence.
- **Reporting Layer:** Standardized JSON reports and terminal summaries.

## 5. Functional Requirements

### 5.1 Dataset Management
- Support JSONL import and export with stable example IDs.
- Line-specific syntax and schema validation errors.
- Stable content hashing (SHA-256) and version tracking.
- Metadata, category distributions, and duplicate ID detection.

### 5.2 Provider & Target Abstraction
- Unified execution interface (`generate(request) -> ProviderResponse`).
- Deterministic mock provider for robust, zero-cost CI and offline testing.
- Local inference via Ollama HTTP API (`/api/generate` and `/api/chat`).
- Standardized execution metadata: latency (ms), token usage, and normalized error categories.

### 5.3 Deterministic Metrics
- **Exact Match & Normalized Match:** Case-folding, whitespace trimming, punctuation stripping.
- **JSON Validity & JSON Schema:** Valid syntax and structural validation against target JSON schemas.
- **Task Assertions:** Predefined keyword presence, regex matching, and value constraints.
- **Aggregation:** Accurate denominators distinguishing skipped, failed, and valid observations.

### 5.4 Advanced & Specialized Evaluation
- **Composite Evaluators:** Weighted combinations of component metrics with explicit normalization.
- **Summary Evaluators:** Dataset-level statistics (pass rate, p50/p95 latency, error rates).
- **Pairwise Comparison & Regressions:** Delta calculations and configurable regression thresholds.
- **RAG Evaluation:** Retrieval metrics (precision@k, recall@k, hit rate) and generation metrics (groundedness, faithfulness).
- **Agent Evaluation:** Tool selection accuracy, argument validity, step counts, and task completion.

### 5.5 Optional LangSmith Integration
- Fully optional: zero remote network calls when disabled.
- OpenTelemetry/LangSmith tracing for runs, steps, and tool calls.
- Dataset synchronization and experiment linkage.
- Graceful degradation: local SQLite evaluation continues uninterrupted if remote calls fail.

## 6. Non-Functional Requirements
- **Local-First & Offline Capable:** Core runner, metrics, and persistence operate fully offline.
- **Security & Privacy:** API keys kept out of source control; sensitive prompt/output logging configurable with redaction.
- **Deterministic CI Testing:** Default tests rely exclusively on mocks and local fixtures.
- **Maintainability:** Modular Python 3.11+ code with strict Ruff linting and comprehensive pytest coverage.

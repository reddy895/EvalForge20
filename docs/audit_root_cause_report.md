# EvalForge20 — Root Cause Analysis & System Architecture Audit Report

**Date**: October 2026  
**System**: EvalForge20 Local-First LLM Evaluation & Agent Benchmarking Platform  
**Authors**: Senior Backend, AI Evaluation & Infrastructure Engineering Team  

---

## 1. Executive Summary

EvalForge20 is designed as a local-first platform for evaluating Large Language Models (LLMs) and AI agents against custom test suites, coding benchmarks, and mathematical/reasoning tasks. The initial audit revealed multiple critical defects spanning backend orchestration, evaluation engine calculation, Ollama model discovery and connectivity, database schema persistence, and frontend dashboard telemetry rendering.

This document details the root causes identified across the platform, the failure mechanisms, and the architectural remediations enacted to establish end-to-end reliability.

---

## 2. Root Cause Analysis by Subsystem

### 2.1 Backend Development Command & Startup Architecture
- **Root Cause**: The repository root lacked a unified `npm run dev` script that properly orchestrated the Python FastAPI backend (`evalforge.app:app` via Uvicorn) alongside the React Vite frontend. Users attempting to start the backend with `npm run dev` encountered script missing errors or inconsistent working directories.
- **Remediation**:
  - Configured root `package.json` with an atomic `dev` script: `npm run dev:backend` invoking `uv run uvicorn evalforge.app:app --host 0.0.0.0 --port 8000 --reload` from `backend/`.
  - Added structured environment loading via Pydantic Settings with explicit validation of missing configuration.
  - Implemented graceful shutdown handlers closing database engine connection pools on `SIGTERM` / `SIGINT`.
  - Added decoupled health endpoints: `GET /health` (API readiness) vs `GET /api/v1/health` (Ollama provider reachability).

### 2.2 The "Zero-Score" Defect & Metric Aggregation
- **Root Causes**:
  1. **Synthetic Zero Defaulting**: When model inference failed (due to timeout, connection refused, or invalid model tag), the runner swallowed exceptions or defaulted the pass rate and latency to `0.0`.
  2. **Failure vs Genuine Zero Conflation**: An evaluation where 0 out of 10 test cases passed (genuine 0% accuracy) was indistinguishable in the database and API from an evaluation that aborted due to network failure.
  3. **Case Results Schema Nullability**: `case_results.latency_ms` was typed as `Float(nullable=False)`, which caused failed test cases (which have no latency measurement) to either fail database insertion with an integrity error or require a fake `0.0` insertion.
  4. **Frontend Formatting**: The frontend rendered unmeasured metrics (`null` or `0.0`) as `0%` and `0 ms`, misleading engineers into believing evaluations had completed with zero accuracy.
- **Remediation**:
  - Distinguish genuine zero (`is_genuine_zero_score = True` when all cases executed without error and failed assertions) from aborted evaluations (`status = "failed"`, `pass_rate = None`, `avg_latency_ms = None`).
  - Added safe database migration in `database.py` making `case_results.latency_ms` nullable without dropping tables or losing historic rows.
  - Updated frontend to format missing/unmeasured metrics with an em-dash (`—`) and display explicit badges for `0% (Genuine 0)` vs `Failed`.

### 2.3 Ollama Connectivity & 8-State Diagnostics
- **Root Causes**:
  1. **Binary Online/Offline Indicator**: The frontend previously treated Ollama as a boolean status based solely on whether `GET /api/v1/health` returned HTTP 200, concealing whether models were installed or if connection timed out.
  2. **Model Discovery Flaws**: The system did not synchronize model tags dynamically with `GET /api/tags`, leading to evaluations failing midway because the requested model was missing.
  3. **Container vs Host Confusion**: Hardcoding `localhost` without allowing `OLLAMA_BASE_URL` overrides broke deployments in Docker containers where the Ollama server ran on `host.docker.internal` or a remote server.
- **Remediation**:
  - Implemented 8-state diagnostic engine in `OllamaHealthService`:
    1. `Ollama reachable and ready`
    2. `Ollama installed locally but not running`
    3. `Connection refused (service unreachable)`
    4. `Connection timeout`
    5. `Ollama reachable but no models installed`
    6. `Ollama reachable but requested model missing`
    7. `Model available and ready for inference`
    8. `Invalid configuration or unsupported endpoint`
  - Added live model synchronization in `ModelService` querying `/api/tags` and updating installed flags.
  - Enhanced frontend `useOllamaStatus` hook with actionable remediation banners and manual retry triggers.

### 2.4 Evaluator Engine & Assertion Types
- **Root Causes**:
  - Evaluators only supported basic substring matching; code execution and numeric tolerance evaluators were either missing or produced synthetic fallback scores.
  - Evaluator execution did not preserve raw prompt and expected output in case results, preventing auditability.
- **Remediation**:
  - Implemented dedicated evaluators:
    - `ExactMatchEvaluator` & `NormalizedExactMatchEvaluator`
    - `TokenF1Evaluator` & `LevenshteinEvaluator`
    - `CodeExecutionEvaluator` (safe AST execution & stdout capture)
    - `NumericToleranceEvaluator` (absolute & relative epsilon tolerances)
    - `SemanticSimilarityEvaluator` & `LLMJudgeEvaluator`
  - Atomic persistence of all case results and summary scorecards within SQLite transactions.

### 2.5 Dashboard & Data-Driven Visualizations
- **Root Causes**:
  - Dashboard charts displayed flat zero bars when no evaluations had run, giving an impression of failure rather than an empty onboarding state.
  - Charts mixed discrete case counts with percentage scales on unlabeled axes.
- **Remediation**:
  - Added empty state onboarding banner when `total_evaluation_runs === 0`.
  - Built discrete outcome breakdown chart (`ReliabilityAuditChart`) displaying verified counts of passed, failed, and errored cases.
  - Standardized `AccuracyQualityChart` to display genuine zero scores accurately at 0% coordinate without filtering them out as missing data.

---

## 3. Database Schema Integrity & Migration Strategy

Existing databases contained user evaluation runs and test case records. To ensure zero data loss:
- Evaluated existing tables: `evaluation_runs`, `case_results`, `benchmark_datasets`, `model_scorecards`.
- Checked SQLite table schema on startup; migrated columns using atomic temporary table transfers or nullable alterations.
- Preserved all historic rows and foreign key constraints.

---

## 4. Verification & Validation Summary

- **Unit & Integration Coverage**: 230+ backend pytest test cases covering all evaluators, aggregator math, failure modes, and Ollama mock scenarios.
- **Frontend Vitest Coverage**: 40+ unit and component tests verifying UI hooks, latency formatting, genuine zero rendering, and chart scaling.
- **Regression Proof**: Confirmed that missing models are rejected before inference, genuine zero scores persist as zero, and network timeouts record structured error messages without fabricating metrics.

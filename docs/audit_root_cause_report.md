# EvalForge20 — Root Cause Audit & Remediation Report

**Date:** 2026-10-23  
**Auditor:** Senior Full-Stack & ML Evaluation Architect  
**Repository:** EvalForge20 (Local-First LLM & Agent Evaluation Platform)

---

## Executive Summary

An exhaustive audit of the frontend, FastAPI backend, SQLite persistence layer, evaluation engine, and visualization components revealed multiple structural failure modes that caused models to display identical or suspiciously similar performance, accuracy, and efficiency metrics across the UI.

The root causes do not stem from a single bug, but rather from an architectural disconnect between the frontend UI and the backend execution engine:
1. **Silent Simulation Fallback:** The frontend caught backend evaluation failures and silently fell back to a client-side mock function (`simulateEvaluationRun`) that returned hardcoded constants (100% pass rate, identical 18.4ms / 22.1ms / 25.8ms latencies) for all models.
2. **Dataset Identifier Mismatch:** The frontend requested evaluations using hardcoded string identifiers (`coding_basics`, `structured_json`, etc.), while the backend SQLite schema required UUIDs, causing 100% of real evaluation requests to fail with HTTP 404.
3. **Premature Status Fetching without Polling:** The frontend made a single call to `GET /evaluations/{id}` immediately after dispatching an asynchronous task, reading an incomplete run without `case_results`, triggering the mock fallback.
4. **Hardcoded Peer Benchmarks & Radar Baselines:** Visualizations in `EvaluationResultCharts.tsx`, `LeaderboardView.tsx`, and `AnalyticsPage.tsx` contained static comparison arrays and synthetic formulas (`1000 / meanLatency` for throughput) rather than measured empirical data.
5. **Dropped Ollama Execution Metadata:** The backend `CaseRunner` discarded Ollama's native nanosecond execution telemetry (`load_duration`, `eval_duration`, `eval_count`), preventing calculation of actual generation tokens/second and TTFT.
6. **Mock Provider Contamination in SQLite:** Previous tests and seeds in `evalforge.db` populated evaluation runs using `MockProvider` with a uniform 5.0ms latency and 100% pass rate.

---

## Detailed Root Cause Analysis

### 1. The Client-Side Silent Fallback Trap (`EvaluatePage.tsx` & `benchmarks.ts`)
In `frontend/src/components/evaluations/EvaluatePage.tsx`:
```typescript
try {
  const runResp = await api.createEvaluation(payload);
  if (runResp?.id) {
    const runDetails = await api.getEvaluationDetails(runResp.id);
    // ...
  }
} catch {
  result = null; // Backend error swallowed silently
}
if (!result) {
  result = simulateEvaluationRun(selectedModel.id, selectedModel.name, ...);
}
```
In `frontend/src/data/benchmarks.ts`:
```typescript
const case_results = selectedCases.map((tc) => ({
  actual_output: tc.simulated_response,
  passed: true, // ALWAYS true
  latency_ms: tc.simulated_latency_ms, // Hardcoded: 18.4, 22.1, 25.8
}));
```
Because any failure in `api.createEvaluation` triggered this fallback, all evaluated models (whether Qwen, Llama, Mistral, or DeepSeek) received exactly the same mock numbers.

### 2. Dataset Identifier and Contract Discrepancy
The frontend dispatched `dataset_id: "coding_basics"`. In the database, datasets are stored with UUID primary keys (e.g., `3c14b644-d141-40f8-9432-2af0a6c93c18`). The backend `EvaluationService.create_and_start_run` queries `DatasetRepository.get_with_cases(request.dataset_id)`, which returns `None` and raises `NotFoundError("Dataset", "coding_basics")`. This guaranteed that real evaluation could never succeed from the default UI.

### 3. API Contract and Detail Endpoint Asymmetry
In `backend/src/evalforge/api/v1/evaluations.py`:
- `GET /evaluations/{id}` returns `EvaluationResponse` (summary only; does not include `case_results`).
- `GET /evaluations/{id}/results` returns `EvaluationDetailResponse` (includes `case_results`).
In `frontend/src/services/api.ts`:
`getEvaluationDetails(id)` was mapped to `/evaluations/${id}`, returning no case results even if the run had completed.

### 4. Synthetic Metric Formulas in Frontend Charts
In `frontend/src/charts/EvaluationResultCharts.tsx`:
- Throughput was estimated using `Math.round(1000 / (meanLatency || 20)) tok/s`. This inverted response latency instead of measuring generated tokens divided by generation duration.
- Capability radar scores were synthetically derived from overall `passRatePercent` using arbitrary arithmetic rather than discrete multi-axial test evaluations.
- Comparison peers in the benchmark tab were hardcoded static objects (`Qwen 2.5 7B Instruct` at 88.5%, `Llama 3.2 3B Instruct` at 81.2%, etc.).

### 5. Leaderboard and Chart Disconnect
- `frontend/src/pages/LeaderboardView.tsx` rendered static sample data without querying `/api/analytics/overview` or `/api/evaluations`.
- The specialized charts (`AccuracyQualityChart`, `LatencyComparisonChart`, `EfficiencyMetricsChart`, `HistoricalTrendsChart`, `NormalizedRadarChart`) were orphaned components not bound to live backend telemetry.

### 6. Ollama Metadata Discard in Backend `CaseRunner`
Ollama returns high-resolution execution telemetry:
- `total_duration`: Total time spent generating the response (nanoseconds).
- `load_duration`: Time spent loading the model into memory (nanoseconds).
- `prompt_eval_duration`: Time spent processing the prompt (nanoseconds).
- `eval_duration`: Time spent generating completion tokens (nanoseconds).
- `eval_count`: Number of output tokens generated.
- `prompt_eval_count`: Number of prompt tokens evaluated.

The backend `OllamaProvider.generate` captured these fields into `InferenceResponse.raw_metadata`, but `CaseRunner.execute_case` failed to persist them into `CaseResult` or aggregate them into the run scorecard. This left tokens-per-second uncalculated or based on wall-clock approximations.

---

## Remediation Plan

1. **Local Ollama Integration as Default:**
   - Connect backend to `OLLAMA_BASE_URL` (`http://localhost:11434`).
   - Dynamic model discovery from `/api/tags` with metadata (quantization, size, family, context window).
   - Dedicated Ollama health check endpoint `/api/providers/ollama/health` wired to frontend `useOllamaStatus`.
2. **Dataset Seeding & Resolution:**
   - Seed standard evaluation benchmark datasets with stable slugs (`coding_basics`, `structured_json`, `reasoning_math`, `rag_retrieval`).
   - Allow dataset lookup by both UUID and slug/name in `DatasetRepository` and `EvaluationService`.
3. **Execution Engine & Metric Correctness:**
   - Update `CaseRunner` to record Ollama's nanosecond timing and token counts.
   - Accurately compute `eval_count / (eval_duration_ns / 1e9)` for generation throughput (tok/s).
   - Compute P50, P95, and load duration metrics.
   - Implement polling in frontend with progress tracking and remove `simulateEvaluationRun` fallback.
4. **Chart & Dashboard Unification:**
   - Connect all charts in `EvaluationResultCharts.tsx`, `AnalyticsPage.tsx`, `LeaderboardView.tsx`, and `HistoryPage.tsx` to real API responses.
   - Persist historical runs in SQLite and display real empirical distributions.
5. **Testing & Verification:**
   - Add unit, integration, and E2E tests for the real Ollama workflow and metric calculations.

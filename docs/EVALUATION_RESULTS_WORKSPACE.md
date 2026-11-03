# EvalForge20 — Dedicated Evaluation Results Workspace

## 1. Executive Summary

The EvalForge20 evaluation experience has been upgraded from simple inline Passed/Failed outputs to a dedicated, professional LLM benchmarking analytics workspace available at `/evaluations/[runId]`.

When a user clicks **Evaluate** in the canvas playground:
1. The canvas graph is validated both client-side and backend-side.
2. The real evaluation execution is initiated against the backend execution engine.
3. The real `execution_id` is obtained from `/api/executions`.
4. The user is seamlessly navigated to `/evaluations/[execution_id]`.
5. The workspace connects to the backend Server-Sent Events (SSE) stream (`/api/executions/{id}/events`) and renders live execution progress (current stage, active model, completed steps, elapsed timer, and live logs).
6. Once complete, the workspace automatically presents rich, interactive graphical representations of model performance across accuracy, exact match, latency, throughput, multi-metric grouped comparisons, heatmap matrix, and detailed test case inspection.

---

## 2. Core Architecture & Components

### 2.1 Backend Persistence & Analytics APIs
- **`backend/src/evalforge/api/health.py`**: Fixed `NameError: name 'Any' is not defined` with proper typing import.
- **`backend/src/evalforge/engine/executor.py` & `routes/executions.py`**: Added `ExecutionRecord` persistence for visual canvas runs and exposed `GET /api/executions/{execution_id}/results` returning unified multi-model telemetry:
  - Model summaries: `pass_rate`, `avg_latency_ms`, `median_latency_ms`, `p95_latency_ms`, `tokens_per_second`, `metrics`.
  - Individual test case results with prompt, expected output, actual response, and evaluator breakdown.
  - Multi-model disagreement matrix.
  - Outcome distribution (`passed`, `failed`, `skipped`).
- **`backend/src/evalforge/api/v1/evaluations.py`**: Added unified fallback lookup in `/api/evaluations/{id}/results` supporting lookup across both `WorkflowExecution` records and `EvaluationRun` benchmark runs.

### 2.2 Frontend Routing & State Management
- **`frontend/src/hooks/useAppNavigation.ts`**: Provides HTML5 browser history routing for `/evaluations/[runId]` and `/evaluations`, supporting direct URL navigation, deep linking, and browser back/forward buttons (`popstate`).
- **`frontend/src/hooks/useEvaluationResults.ts`**: Manages SSE streaming connection with automatic elapsed timing, progress tracking, and fallback polling.

### 2.3 Graphical Visualizations & Analytics
1. **`EvaluationSummaryHeader.tsx`**: Header displaying run ID, execution status, dataset name, models evaluated, total/completed/failed test cases, duration, and evaluators. Includes Copy Run ID and Cancel actions.
2. **`LiveExecutionBanner.tsx`**: Live execution banner displaying real-time progress bar, current model/evaluator, elapsed time, and expandable live log terminal.
3. **`AccuracyComparisonChart.tsx`**: Recharts bar chart comparing pass rates across models with clean light developer-tool aesthetic.
4. **`ExactMatchComparisonChart.tsx`**: Bar chart comparing exact-match accuracy with missing-metric handling.
5. **`LatencyComparisonChart.tsx`**: Millisecond inference latency comparison with P50/P95 tooltips.
6. **`ThroughputComparisonChart.tsx`**: Real measured tokens/second chart with explicit missing-telemetry warning (no fabricated values).
7. **`GroupedMetricComparisonChart.tsx`**: Multi-metric grouped bar chart comparing models across evaluators with legends.
8. **`EvaluationDistributionChart.tsx`**: Outcome distribution donut chart and summary cards (Passed, Failed, Skipped).
9. **`MultiModelComparisonTable.tsx`**: Side-by-side scorecard comparing models with disagreement analysis; works seamlessly with both 1 model and multiple models.
10. **`TestCasePerformanceMatrix.tsx`**: Per-test-case heatmap matrix showing pass/fail status per model and prompt.
11. **`TestCaseExplorer.tsx`**: Test case sample explorer with search, multi-criteria filtering (passed, failed, skipped, model, evaluator), and JSON export.
12. **`TestCaseDetailModal.tsx`**: Deep inspection modal displaying prompt, ground truth, model response, telemetry, evaluator score breakdown, and error details.

---

## 3. Data Integrity & Verification

- **No Synthetic Scores**: All chart datasets, numbers, and test cases originate from the backend API.
- **Null Telemetry Distinction**: Missing throughput or metric values are explicitly treated as `null`/`Missing` rather than converted to synthetic zeros.
- **Zero Distinction**: A genuine 0 score is distinguished from a failed or missing evaluator run.
- **Test Suite Results**:
  - Backend: All 272 pytest tests pass (`.venv/bin/python -m pytest`).
  - Frontend: All 10 Vitest test suites (48 tests) pass (`cd frontend && npm test`).
  - Frontend Build: Full TypeScript check and Vite production bundle build succeed with zero errors (`cd frontend && npm run build`).

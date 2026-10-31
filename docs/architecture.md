# EvalForge20 Architecture Documentation

## System Architecture

EvalForge20 is structured with strict separation of concerns, operating as a local-first, privacy-preserving LLM evaluation and visualization platform:

- **Frontend (`frontend/`)**: React 19 + TypeScript + Vite SPA. Features a minimal, professional dashboard styled with a curated Teal accent palette (`#0D9488`, `#14B8A6`), clean typography, dark-mode background (`#0B0F17`), and 2D comparison charts powered by Recharts.
- **Backend (`backend/`)**: FastAPI asynchronous application. Exposes dual `/api` and `/api/v1` routes with robust Pydantic Settings configuration and validation.
- **Inference Layer (`backend/src/evalforge/providers/`)**: Local-first provider architecture prioritizing Ollama (`http://localhost:11434`), verifying model readiness via `/api/tags` and executing real local inference via `/api/generate`.
- **Evaluation Engine (`backend/src/evalforge/evaluators/`)**: Deterministic and semantic scoring pipelines calculating accuracy, latency, throughput, token velocity, and efficiency without synthetic mock metrics.
- **Database Layer (`backend/src/evalforge/storage/`)**: SQLAlchemy 2.0 with async SQLite (`evalforge.db`) storing evaluation runs, test case executions, and efficiency metrics.

---

## Evaluation-to-Visualization Pipeline

The complete pipeline traces end-to-end:

```
[Dataset / Test Cases] 
        │
        ▼
[Evaluation Request] ──► [Model Readiness Validation (Ollama /api/tags)]
        │
        ▼
[Model Inference] ─────► Real Local Inference (Ollama /api/generate)
        │
        ▼
[Metric Calculation] ──► Correctness (pass/fail), Latency (ms), Throughput (tok/s), Efficiency Index
        │
        ▼
[Persistence] ────────► SQLite (EvaluationRun, CaseResult with is_genuine_zero tracking)
        │
        ▼
[API Layer] ──────────► /api/evaluations/{id}, /api/models/comparison, /api/analytics/efficiency
        │
        ▼
[Frontend Dashboard] ──► 5 Real-Time 2D Comparison Visualizations
```

---

## 5 Required 2D Dashboard Visualizations

1. **Model Accuracy Comparison (`AccuracyQualityChart`)**: 2D vertical bar chart presenting benchmark pass rates (0-100%) across evaluated models.
2. **Average Latency Comparison (`LatencyComparisonChart`)**: 2D vertical bar chart visualizing model inference turnaround in milliseconds with standard deviation reference bars.
3. **Throughput Comparison (`EfficiencyMetricsChart`)**: 2D vertical bar chart charting token generation speed (tokens/sec).
4. **Model Efficiency Comparison (`ModelEfficiencyChart`)**: 2D vertical bar chart plotting the composite efficiency index (`tokens_per_second / latency_ms * 1000`) to highlight optimal throughput per latency unit.
5. **Evaluation Reliability Summary (`ReliabilityAuditChart`)**: 2D grouped bar chart displaying passed test cases versus failed executions per model.

---

## UI Design System Specifications

- **Primary Accent**: Teal (`#0D9488`, `#14B8A6`), replacing all legacy orange accents.
- **Backgrounds**: Slate Dark `#0B0F17` and `#111827`, bordered by subtle slate borders `#1F2937` / `#374151`.
- **Status Indicators**: Passing `#10B981`, Genuine Zero `#F59E0B`, Failed/Aborted `#EF4444`.
- **Typography & Consistency**: Clean sans-serif hierarchy, explicit units (`%`, `ms`, `tok/s`), standard zero-baseline axes, and dedicated empty/loading/error states.

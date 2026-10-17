# EvalForge20 — Architecture Audit & Delivery Implementation Plan

## 1. Repository Audit & Baseline Assessment

### 1.1 Git History & Environment
- **Branch**: `main` synced with `origin/main` (`https://github.com/reddy895/EvalForge20.git`).
- **Commits**: 154 prior commits implementing initial backend endpoints, database repositories, evaluators, and frontend shell.
- **Python Runtime**: Python 3.11 virtual environment (`.venv`) with core runtime dependencies: FastAPI, Pydantic, SQLAlchemy, Alembic, HTTPX, Typer, Rich, Jsonschema.
- **Frontend Runtime**: Vite 8.3 + React 19 + TypeScript 6 + Vitest 5 in `frontend/`.

### 1.2 Root-Cause Analysis of CI Failures
- **Issue 1**: In previous CI runs (e.g., Run ID `38862196818`), the workflow failed during step `Run Ruff Format Check` because files were not formatted according to Ruff's style rules. Commit `7844b6e` resolved code formatting via `ruff format`.
- **Issue 2**: The original GitHub Actions CI workflow (`.github/workflows/ci.yml`) only executed Python tests (`pytest`) and Ruff linting, omitting frontend test validation, TypeScript type-checking, and Vite production builds.
- **Issue 3**: Untracked frontend test files (`frontend/src/test/api_client.test.ts`, `frontend/src/test/components.test.tsx`, `frontend/src/test/charts_and_cards.test.tsx`) contained type mismatches (`toBeInTheDocument` missing Vitest matchers, `apiClient` vs `api` naming disparity, and component prop definitions).

### 1.3 Resolution Strategy
- Configure `@testing-library/jest-dom/vitest` in `frontend/src/test/setup.ts` and update `tsconfig.app.json`.
- Export compatible `apiClient` facade from `frontend/src/api/client.ts`.
- Align component test expectations with actual CSS classes and typed props.
- Implement dual-job CI workflow validating both backend (pytest, ruff) and frontend (lint, vitest, tsc build).

---

## 2. Target Architecture

```
EvalForge20/
├── frontend/
│   ├── src/
│   │   ├── api/          # Typed API clients & response schemas
│   │   ├── components/   # UI primitives, shell, eval-flow, compare, dashboard
│   │   ├── context/      # Toast and modal providers
│   │   ├── pages/        # Overview, Evaluate, Catalog, Runs, Compare, Datasets, TaskAnalysis, Settings
│   │   ├── styles/       # Graphite & burnt-orange design tokens, reset, typography
│   │   └── test/         # Vitest component & API unit tests
│   ├── package.json
│   └── vite.config.ts
├── app/
│   ├── api/              # FastAPI routers (health, models, datasets, evaluations, compare, pricing, task-analysis)
│   ├── catalog/          # Unified model catalog service with verified metadata
│   ├── domain/           # Core domain contracts, models, results, state, complexity bands
│   ├── evaluators/       # Deterministic & model-based evaluators
│   ├── pricing/          # Sourced, timestamped pricing catalog & cost calculator
│   ├── providers/        # Local Ollama, OpenAI, Anthropic, Gemini, NVIDIA, Mock adapters
│   ├── runner/           # Bounded-concurrency async evaluation runner & retry engine
│   ├── storage/          # SQLite models, repositories, migrations
│   └── main.py           # Application entrypoint & static SPA mounting
├── docs/                 # Product documentation, guides, and specifications
└── .github/workflows/    # Automated CI workflows
```

---

## 3. Product Delivery Milestones

1. **Milestone 1 (1–5)**: Repository audit, architecture, design system.
2. **Milestone 2 (6–10)**: Frontend shell, navigation, responsive layout.
3. **Milestone 3 (11–15)**: Backend organization, configuration, health and readiness.
4. **Milestone 4 (16–21)**: Ollama health checks, local model discovery, provider abstraction.
5. **Milestone 5 (22–27)**: Cloud provider adapters, model catalog, manual model selection.
6. **Milestone 6 (28–33)**: Dataset validation, storage, deterministic evaluators.
7. **Milestone 7 (34–39)**: Evaluation runner, persistence, per-case metrics.
8. **Milestone 8 (40–44)**: Complexity analysis, performance metrics, cost calculation.
9. **Milestone 9 (45–49)**: Comparison workflows, dashboard, run inspection.
10. **Milestone 10 (50–53)**: Reports, responsive polish, frontend/backend integration.
11. **Milestone 11 (54–57)**: Regression fixes, CI validation, documentation, release readiness.

# EvalForge20 — Architecture Audit & Rebuild Blueprint

## 1. Executive Summary
EvalForge20 is rebuilt from scratch as a local-first, visual AI model benchmarking and evaluation platform.
It eliminates all external dependencies on LangSmith, paid APIs, and cloud evaluation platforms.
All model inference runs locally via Ollama (`http://localhost:11434`), and all evaluation calculations are performed by an independent, registry-driven native Python engine.

## 2. Legacy Codebase Audit Findings
- **Evaluation Engine**: Previously contained disparate evaluation files with scattered metrics and ad-hoc execution logic.
- **Visual Playground**: Frontend had dashboard views but lacked an n8n-style interactive node canvas with drag-and-drop workflow execution.
- **Model Discovery**: Relied on partially hardcoded model lists instead of dynamic live inventory queries to Ollama.
- **Workflow Execution**: Needed a formal graph validator, topological execution scheduler, and Server-Sent Events (SSE) streaming progress.
- **Theme & Design**: Needed a cohesive, professional light theme (#F8FAFC, #FFFFFF, #111827, #2563EB) inspired by modern developer platforms (Linear, n8n, Stripe).

## 3. Rebuilt Architecture Specification
### Backend (`backend/src/evalforge/`):
- `api/routes/`: `health.py`, `models.py`, `workflows.py`, `datasets.py`, `evaluators.py`, `executions.py`, `experiments.py`, `benchmarks.py`, `leaderboard.py`.
- `core/`: `config.py`, `logging.py`, `security.py`.
- `providers/`: `base.py`, `ollama.py`.
- `engine/`: `registry.py`, `executor.py`, `validator.py`, `scheduler.py`, `events.py`.
- `evaluators/`: `base.py`, `accuracy.py`, `classification.py`, `semantic.py`, `reasoning.py`, `coding.py`, `performance.py`, `reliability.py`, `safety.py`, `structured_output.py`, `judge.py`.
- `datasets/`: `loader.py`, `validator.py`, `registry.py`.
- `hardware/`: `monitor.py`.
- `experiments/`: `service.py`, `repository.py`.
- `database/`: `models.py`, `session.py`.
- `schemas/`: `main.py`.

### Frontend (`frontend/src/`):
- `components/layout/`: Header, Navigation Sidebar, Status Indicators.
- `components/canvas/`: React Flow canvas, Node Library, Custom Node components, Top Toolbar, Node Config panel.
- `components/results/`: Live SSE stream, Test Case Inspector, Multi-model comparison charts (Recharts), Export.
- `pages/`: Playground, Experiments, Models, Benchmarks, Datasets, Leaderboard, Settings.

## 4. Non-Negotiable Guarantees
1. No LangSmith or cloud API requirements.
2. Genuine local Ollama model execution.
3. Accurate deterministic and rubric-based evaluations without mock/random scores.
4. Persistent SQLite storage for workflow definitions and experiment runs.

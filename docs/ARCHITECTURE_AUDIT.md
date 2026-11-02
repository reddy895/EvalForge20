# EvalForge20 — Architecture Audit & Execution Path Analysis

**Audit Date:** 2026-11-02  
**Auditor:** EvalForge20 Engineering

---

## Executive Summary

The repository contains a well-structured FastAPI + React Flow evaluation platform. All 259 backend
tests and 42 frontend tests pass. The production build succeeds. However, the end-to-end evaluation
workflow is broken at multiple schema and routing boundaries.

---

## Critical Execution Path Failures

### 1. WorkflowNode Schema: Missing `category` Field Default

`WorkflowNode` in `schemas/main.py` declares `category: str` with no default value, but the
frontend playground serialises nodes without a `category` field. Every execution request from the
playground is rejected by Pydantic validation before reaching the executor.

**File:** `backend/src/evalforge/schemas/main.py` — `WorkflowNode.category`  
**Fix:** Add `category: str = ""` default.

### 2. ExecutionTriggerRequest: Frontend Field Name Mismatch

The frontend sends `{ "name": "...", "workflow_graph": {...} }` to `POST /api/executions`.  
The backend schema expects `{ "graph": {...}, "execution_name": "..." }`.  
No graph is ever extracted; the request always triggers a 400 "Must provide graph or workflow_id".

**File:** `backend/src/evalforge/schemas/main.py` — `ExecutionTriggerRequest`  
**Fix:** Add `workflow_graph` as a schema alias / extra field that normalizes to `graph`.

### 3. WorkflowEdge: Field Name Mismatch

Frontend serializes edges as `{ "source_id": "...", "target_id": "..." }` in the workflow
validator path, but `WorkflowEdge` expects `{ "source": "...", "target": "..." }`.  
The engine's `EngineRegistry` uses `edge.source` and `edge.target` directly.

**File:** `backend/src/evalforge/schemas/main.py` — `WorkflowEdge`  
**Fix:** Accept both `source_id`/`target_id` aliases and canonical `source`/`target`.

### 4. SSE Event Type Mismatch

The `WorkflowExecutor` broadcasts events of type `step_progress`, `completed`, `failed`,
`cancelled`. The frontend SSE handler in `PlaygroundView.tsx` listens for `progress`,
`case_result`, `log`, `finished`, `failed`. Only `failed` is shared; all other event types
are silently dropped, so no UI progress ever updates.

**Frontend file:** `frontend/src/pages/PlaygroundView.tsx` (lines 289–309)  
**Fix:** Align frontend handler to actual backend event schema: `step_progress` → update
progress/cases, `completed` → mark finished, `started` → log.

### 5. Missing Ollama Provider Routes

`api.ts` calls:
- `GET /api/providers/ollama/health` → **404, route does not exist**
- `GET /api/providers/ollama/models` → **404, route does not exist**

The existing `/api/ollama/status` and `/api/health` routes contain the same information but
are not wired into the frontend API client.

**Fix:** Add `/providers/ollama/health` and `/providers/ollama/models` routes or update
the frontend API client to call the correct existing endpoints.

### 6. CI Ruff Lint: 74 Errors + Wrong Install Path

The CI workflow runs `pip install -e ".[dev]"` which does NOT install `ruff` (not in dev
dependencies), then runs `ruff check backend/src tests backend/tests` which fails because:
a) ruff is not installed
b) path `tests` is the root-level tests directory, not `backend/tests`

**File:** `.github/workflows/ci.yml`  
**Fix:** Add `ruff` to `[project.optional-dependencies] dev`, fix CI paths, fix import ordering.

### 7. WorkflowValidator: Called as Both Static and Instance Method

`workflows.py` route calls `WorkflowValidator.validate_graph(payload)` as a static/class
method, but the class defines it as `@classmethod`. The executor instantiates
`WorkflowValidator()` and calls `self.validator.validate_graph(graph)`. Both work, but
the validator method is decorated `@classmethod` which is consistent with both usages.

---

## Complete Execution Path Trace

```
User clicks Evaluate
  ↓ PlaygroundView.handleEvaluate()
  ↓ POST /api/executions with { name, workflow_graph: { nodes, edges } }
  ↓ [BROKEN] backend expects { graph: { nodes, edges } } — 400 returned
  ↓ [BROKEN] WorkflowNode requires category — Pydantic validation fails before engine
  ↓ WorkflowExecutor.execute_workflow(graph)
  ↓ WorkflowValidator.validate_graph(graph)
  ↓ EngineRegistry.build_execution_targets(graph)
  ↓ [BROKEN] edges use source_id/target_id instead of source/target — empty targets
  ↓ OllamaProvider.generate(InferenceRequest)
  ↓ OllamaClient.generate(payload) → POST http://localhost:11434/api/generate
  ↓ [OFFLINE] Ollama not running → ProviderConnectionError raised
  ↓ ExecutionEventBroadcaster.broadcast(failed, ...)
  ↓ SSE stream → EventSource.onmessage(event)
  ↓ [BROKEN] event.type = "step_progress", frontend checks for "progress" → dropped
  ↓ [BROKEN] event.type = "completed", frontend checks for "finished" → dropped
  ↓ No UI state change, no results rendered
```

---

## Provider Status: Ollama Offline

Ollama is not running at `http://localhost:11434`. The `OllamaClient.check_health()` returns
`False`. The backend health endpoint correctly reports `ollama_reachable: false`. The frontend
does not prominently display this; the Evaluate button does not pre-check provider health.

**Required:** Pre-flight Ollama check before submitting evaluation. Clear UI banner when offline.
Instructions: `ollama serve` → `ollama list` → `ollama pull qwen2.5:1.5b`.

---

## What Already Works

- Drag-and-drop canvas with node connections (React Flow)
- Node configuration panel
- Backend API server (FastAPI, SQLAlchemy, SQLite)  
- All 259 backend unit/integration tests
- All 42 frontend tests
- Production build (`npm run build`)
- SSE broadcaster infrastructure
- Ollama client/diagnostics (when Ollama is running)
- Evaluator registry (20+ evaluators)
- Dataset/benchmark registry (6 built-in suites)
- Experiment/result persistence (SQLite via SQLAlchemy)

---

## Implementation Checklist

- [ ] Fix WorkflowNode.category default in schema
- [ ] Fix ExecutionTriggerRequest to accept workflow_graph alias  
- [ ] Fix WorkflowEdge source/target field aliases
- [ ] Align frontend SSE handler to backend event types
- [ ] Add /providers/ollama/health and /providers/ollama/models routes
- [ ] Add pre-flight Ollama check in Evaluate handler
- [ ] Display Ollama offline banner with recovery instructions
- [ ] Fix CI: install ruff, fix paths, fix import ordering
- [ ] Add frontend evaluation workflow tests
- [ ] Add backend integration tests for evaluation path
- [ ] Build evaluation results workspace enhancements
- [ ] Add model comparison visualizations
- [ ] Document local setup and Ollama recovery

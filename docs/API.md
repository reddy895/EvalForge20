# EvalForge20 REST API Reference

## 1. System Endpoints

### `GET /health`
Liveness probe.
- Response: `{"status": "healthy", "version": "0.1.0", "timestamp": "..."}`

### `GET /ready`
Readiness probe verifying database connectivity and essential directory paths.
- Response: `{"status": "ready", "database": "connected"}`

## 2. Discovery Endpoints

### `GET /v1/providers`
Lists all registered model providers (e.g. `mock`, `ollama`).

### `GET /v1/metrics`
Lists all registered evaluation metrics, their categories, descriptions, valid ranges, and parameter schemas.

## 3. Dataset Endpoints

### `POST /v1/datasets/validate`
Validates raw JSONL dataset content with line-specific error tracking.

### `POST /v1/datasets`
Registers a dataset and computes its canonical SHA-256 version hash.

## 4. Evaluation Endpoints

### `POST /v1/evaluations`
Creates and asynchronously executes an evaluation run.
- Request Body: `EvaluationRunConfig`
- Response: `{"run_id": "...", "status": "running"}`

### `GET /v1/evaluations`
Lists historical runs with pagination (`limit`, `offset`).

### `GET /v1/evaluations/{run_id}`
Returns run lifecycle record and computed aggregate metrics.

### `GET /v1/evaluations/{run_id}/results`
Returns paginated per-case outputs, latencies, tokens, and metric evaluations.

### `GET /v1/reports/{run_id}`
Exports complete JSON report with optional `redact_inputs` and `redact_outputs` parameters.

## 5. Comparison Endpoints

### `POST /v1/compare`
Compares a candidate evaluation run against a baseline benchmark and enforces regression thresholds.

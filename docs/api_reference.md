# REST API Reference

All endpoints are dual-mounted under `/api/...` and `/api/v1/...`:

- `GET /api/health`: Health probe and Ollama daemon connectivity.
- `GET /api/providers`: List registered provider names.
- `GET /api/providers/details`: Detailed configuration state for 15 providers.
- `GET /api/models`: Paginated, filterable catalog models.
- `POST /api/models/refresh`: Force resynchronization with local Ollama.
- `GET /api/evaluations`: List historical evaluation runs.
- `POST /api/evaluations`: Dispatch a new evaluation job.
- `GET /api/analytics/overview`: Platform KPIs and pass rate aggregations.
- `GET /api/analytics/commits`: Verified Git activity heatmap and statistics.

## Datasets

- `GET /api/v1/datasets?offset=0&limit=50`: Paginated dataset list.
- `POST /api/v1/datasets`: Create a dataset with optional initial cases.
- `GET /api/v1/datasets/{id}`: Dataset metadata with all cases.
- `PATCH /api/v1/datasets/{id}`: Update metadata (increments version).
- `DELETE /api/v1/datasets/{id}`: Delete dataset and cascade cases.
- `POST /api/v1/datasets/import`: Multipart import of UTF-8 JSONL/CSV (`name`, `format`, `file`).
- `GET /api/v1/datasets/{id}/cases?offset=0&limit=50`: Paginated case listing.
- `GET /api/v1/datasets/{id}/preview?limit=10`: Bounded preview for import verification.
- `GET /api/v1/datasets/{id}/integrity`: Content fingerprint and data-quality report.
- `POST /api/v1/datasets/{id}/duplicate?new_name=...`: Deep-copy a dataset.
- `DELETE /api/v1/datasets/{id}/cases/{case_id}`: Delete a single case.
- `GET /api/v1/datasets/{id}/export?format=jsonl|csv`: Download dataset.

Import responses include `imported_cases`, `failed_rows`, `duplicates_skipped`, `warnings`, and row-level `errors`. Invalid UTF-8 is rejected rather than silently replaced.

## Evaluations and experiments

- `POST /api/v1/evaluations`: Create and start a run.
- `GET /api/v1/evaluations?status=&model_id=&dataset_id=&query=&offset=&limit=`: Filtered listing.
- `GET /api/v1/evaluations/{id}`: Status and aggregate summary.
- `GET /api/v1/evaluations/{id}/results`: Per-case results and metrics.
- `POST /api/v1/evaluations/{id}/cancel`: Cooperative cancellation.
- `GET /api/v1/evaluations/{id}/export?format=json|csv`: Export run evidence.
- `GET /api/v1/experiments`, `POST /api/v1/experiments`, `GET /api/v1/experiments/{id}`: Experiment-oriented aliases.

Run statuses include `queued`, `running`, `completed`, `completed_with_errors`, `failed`, `cancelled`, and `interrupted`. An `interrupted` run was active when the server stopped and must not be treated as successful.

## Error contract

Errors use a consistent envelope:

```json
{
  "error": {
    "code": "VALIDATION_FAILED",
    "message": "Human-readable message",
    "details": {},
    "request_id": "..."
  }
}
```

Common codes: `RESOURCE_NOT_FOUND`, `VALIDATION_FAILED`, `CONFLICT`, `PAYLOAD_TOO_LARGE`, `RATE_LIMITED`, `UNAUTHORIZED`, `PROVIDER_ERROR`, `PROVIDER_UNAVAILABLE`, `PROVIDER_TIMEOUT`.

## Authentication

If `AUTH_TOKEN` is configured, all `/api` routes except health probes require:

```http
Authorization: Bearer <token>
```

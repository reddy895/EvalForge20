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

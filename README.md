# EvalForge20

**Local-first LLM and AI-agent evaluation platform.**

EvalForge20 lets you move from a dataset and a model to reproducible, inspectable evaluation results: **Dataset → Model → Evaluators → Run → Results → Comparison → Export**.

It runs as a FastAPI backend plus a React/Vite single-page frontend, with **Ollama** as the first-class local inference provider. No cloud account is required for local evaluation.

<p align="center">
  <img src="assets/evalforge-playground.png" alt="EvalForge20 visual evaluation playground" width="100%">
</p>

---

## Project status

EvalForge20 is functional software, not a finished commercial product. This README distinguishes verified capabilities from partial or planned work.

### Verified, implemented capabilities

| Area | Status | Notes |
|---|---|---|
| Dataset CRUD, duplication, deletion | Implemented | API + rebuilt dataset workspace |
| JSONL / CSV import | Implemented | UTF-8 validation, row-level errors, duplicate detection |
| Dataset preview and pagination | Implemented | Bounded queries, no full-table dumps |
| Dataset integrity fingerprint | Implemented | SHA-256 over canonical cases |
| Dataset version counter | Implemented | Incremented on metadata/case changes; not full historical snapshots |
| Ollama model discovery and inference | Implemented | Connection diagnostics, model readiness checks |
| OpenAI-compatible / cloud adapter scaffolding | Partial | Adapter interfaces exist; only Ollama and the deterministic mock are exercised in this repo's test suite |
| Deterministic evaluators | Implemented | Exact/normalized match, token F1, keywords, JSON schema, numeric tolerance, code execution |
| Semantic similarity | Partial | Deterministic token-based similarity, not embedding-based |
| LLM-as-a-judge | Implemented | Rubric, prompt version, judge metadata, prompt-injection guard; scores are explicitly marked estimates |
| RAG metrics | Partial | Faithfulness / relevance / context precision / recall implementations with LLM assistance |
| Safety evaluation | Partial | Keyword/heuristic safety checks; not a moderation service |
| Evaluation runs, bounded concurrency, cancellation | Implemented | Per-case isolation and error capture |
| Run persistence and interruption recovery | Implemented | Runs left active by a restart are marked `interrupted` |
| Results, per-case inspection, comparison charts | Implemented | Data originates from persisted case results |
| JSON / CSV exports | Implemented | Per-run evaluation export, dataset export |
| Request IDs, structured logging, redaction | Implemented | Secret-looking keys are redacted |
| Authentication | Optional | Single shared bearer token (`AUTH_TOKEN`); no user accounts or RBAC |
| Docker / Compose deployment | Implemented | Non-root image, healthcheck, optional PostgreSQL profile |
| Database backup / restore scripts | Implemented | SQLite and PostgreSQL |

### Not implemented (be honest about it)

- Multi-tenant user accounts, teams, SSO, and role-based access control.
- Full dataset version history / immutable snapshots beyond the version counter.
- PDF report export.
- A durable external job queue (runs execute in-process; use a single API worker).
- Embedding-based semantic similarity.
- Verified end-to-end tests against every cloud provider.
- Built-in moderation or compliance certification.

See [docs/architecture.md](docs/architecture.md), [docs/providers.md](docs/providers.md), and [docs/faq.md](docs/faq.md).

---

## Architecture

```text
React + TypeScript + Vite (frontend/)
        │  REST / SSE
        ▼
FastAPI + Pydantic + SQLAlchemy async (backend/src/evalforge/)
        ├── Dataset service        → import, validate, fingerprint, export
        ├── Evaluation service     → snapshot, bounded execution, persistence
        ├── Evaluator registry     → deterministic metrics + LLM judge
        ├── Provider registry      → Ollama, mock, OpenAI-compatible, cloud adapters
        └── SQLite (default) / PostgreSQL (optional)
```

Key directories:

```text
backend/src/evalforge/
  api/            versioned REST routers (/api and /api/v1)
  core/           settings, errors, logging, security middleware
  datasets/       importers, validator, exporter, seeder
  engine/         visual workflow validation and scheduling
  evaluation/     runner and metric helpers
  evaluators/     deterministic, semantic, RAG, safety, judge evaluators
  experiments/    case runner, bounded concurrency, lifecycle, recovery
  providers/      provider abstraction, Ollama client, cloud adapters
  services/       application services
  storage/        SQLAlchemy models, repositories, database lifecycle
  tests/          backend unit and integration tests
frontend/src/     React pages, hooks, charts, API client, tests
docs/             architecture, metrics, providers, deployment, security
```

Long-running evaluations execute in the API process using bounded async concurrency. If the process exits mid-run, the next startup marks the run `interrupted`; it is never reported as successful.

---

## Quick start

### Prerequisites

- Python 3.11+
- Node.js 20+
- Ollama (for real local inference; optional if you only use the mock provider)

### 1. Backend

```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env                 # review and edit
uvicorn src.evalforge.main:app --host 127.0.0.1 --port 8000 --reload
```

The backend listens on `http://127.0.0.1:8000`. API docs: `http://127.0.0.1:8000/docs`.

### 2. Frontend

```bash
cd frontend
npm ci
npm run dev
```

Open `http://localhost:5173`. Vite proxies `/api` to `http://127.0.0.1:8000`.

### 3. Ollama (for real local models)

```bash
ollama serve
ollama pull qwen2.5:1.5b
curl http://localhost:11434/api/tags
```

Then refresh models in the UI or call `POST /api/v1/models/refresh`.

---

## Configuration

All settings are environment variables; see [`.env.example`](.env.example) for the full reference.

Critical settings:

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `sqlite+aiosqlite:///./evalforge.db` | SQLite locally; use `postgresql+asyncpg://...` for multi-user deployments |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Local inference endpoint |
| `HOST` / `PORT` | `127.0.0.1` / `8000` | Bind address |
| `AUTH_TOKEN` | empty | Optional shared bearer token for `/api` routes |
| `CORS_ORIGINS` | localhost dev origins | Comma-separated allowed origins |
| `RATE_LIMIT_ENABLED` | `true` | Per-client, per-endpoint-group fixed window |
| `MAX_REQUEST_BODY_BYTES` | 20 MB | Hard request body ceiling |
| `MAX_DATASET_FILE_SIZE_BYTES` | 10 MB | Dataset upload ceiling |
| `MAX_CASES_PER_DATASET` | `2000` | Dataset size ceiling |
| `ENVIRONMENT` | `development` | In `production`, startup rejects debug mode, wildcard CORS, and exposed binds without `AUTH_TOKEN` |

Cloud provider API keys are optional and read from the environment. They are never returned by API responses and are redacted from structured logs.

---

## Evaluation workflow

1. Import or create a dataset (JSONL/CSV) and preview it.
2. Check dataset integrity (empty prompts, duplicates, fingerprint).
3. Choose a local Ollama model (or the deterministic `mock` provider).
4. Choose evaluators (e.g. exact match, JSON schema, LLM judge with a rubric).
5. Start a run; monitor progress and cancel if needed.
6. Inspect per-case prompts, expected/actual outputs, metrics, and errors.
7. Compare compatible runs or export results as JSON/CSV.

### Example JSONL dataset

```jsonl
{"prompt": "What is 2+2?", "expected_output": "4"}
{"prompt": "Reverse the string abc", "expected_output": "cba"}
```

Invalid rows are reported with line numbers; they are never silently discarded. Duplicate prompt/reference/context rows are skipped and reported explicitly.

### Metrics

Deterministic metrics are ground-truth comparisons. LLM-judge metrics are **model-generated estimates** and are labelled as such, including judge model, provider, prompt version, rubric hash, and execution configuration. See [docs/evaluation_metrics_guide.md](docs/evaluation_metrics_guide.md).

---

## Security posture

- Default bind is loopback only.
- Optional shared-secret bearer authentication (`AUTH_TOKEN`) for self-hosted exposure behind a trusted proxy.
- Server-side input validation, parameterized ORM queries, upload size limits, filename sanitization, and rate limiting.
- SSRF validation for provider endpoints resolves DNS and rejects loopback/private/link-local/metadata targets unless private endpoints are explicitly enabled.
- Structured logs redact API keys, tokens, passwords, and authorization headers.
- No secrets are committed; `.env` is ignored and `.env.example` contains placeholders only.

**Not a multi-user SaaS security model.** There are no accounts, per-user ownership checks, or RBAC. For a public multi-tenant deployment, put EvalForge behind an authenticating proxy or add an identity layer, and use PostgreSQL with backups.

Report vulnerabilities privately — see [SECURITY.md](SECURITY.md).

---

## Testing

```bash
# Backend (from repo root, with venv active)
ruff check backend/src tests backend/tests
pytest -v

# Frontend
cd frontend
npx tsc -b
npm test
npm run build
```

The repository's backend suite covers dataset import/validation, evaluators, metric aggregation, provider failure modes, API parity, security middleware, evaluation lifecycle, and persistence. Frontend tests cover rendering, navigation, results workspaces, analytics, and dataset workspace states.

Tests use the deterministic `mock` provider for repeatable evaluation; they do not prove that any cloud provider or a specific Ollama model works on your machine.

---

## Production deployment

A production image is provided in `backend/Dockerfile` (multi-stage, non-root, healthchecked).

```bash
cd backend
docker compose up -d --build
```

For PostgreSQL:

```bash
export POSTGRES_PASSWORD='<strong-password>'
export DATABASE_URL='postgresql+asyncpg://evalforge:<strong-password>@db:5432/evalforge'
docker compose --profile postgres up -d --build
```

Backups:

```bash
DATABASE_URL=sqlite+aiosqlite:///./evalforge.db scripts/backup_db.sh ./backups
DATABASE_URL=sqlite+aiosqlite:///./evalforge.db scripts/restore_db.sh ./backups/evalforge-<stamp>.db
```

See [docs/deployment.md](docs/deployment.md) for HTTPS, reverse proxy, environment, migration, backup, and operational guidance.

> Ollama inference runs on the host's CPU/GPU, not inside the API container by default. A free hosting tier cannot run large local models. Hosted application infrastructure and local model compute are separate concerns.

---

## API overview

| Endpoint | Purpose |
|---|---|
| `GET /api/health`, `/api/health/live`, `/api/health/ready` | Liveness/readiness |
| `GET /api/v1/datasets` | List datasets |
| `POST /api/v1/datasets/import` | Import JSONL/CSV |
| `GET /api/v1/datasets/{id}/preview` | Preview cases |
| `GET /api/v1/datasets/{id}/integrity` | Fingerprint and data-quality report |
| `POST /api/v1/evaluations` | Create and start a run |
| `GET /api/v1/evaluations/{id}/results` | Per-case results |
| `POST /api/v1/evaluations/{id}/cancel` | Cooperative cancellation |
| `GET /api/v1/evaluations/{id}/export?format=json\|csv` | Export a run |
| `GET /api/v1/providers` | Provider status |
| `GET /api/v1/models` | Model catalog |

OpenAPI is available at `/docs` and `/openapi.json`.

---

## Documentation

- [Architecture](docs/architecture.md)
- [Metrics reference](docs/metrics_reference.md)
- [Evaluation metrics guide](docs/evaluation_metrics_guide.md)
- [Providers and Ollama setup](docs/providers.md)
- [Local-first Ollama notes](docs/local_first_ollama.md)
- [Deployment](docs/deployment.md)
- [Metric definitions and limitations](docs/evaluation_metrics_guide.md)
- [FAQ](docs/faq.md)
- [Security policy](SECURITY.md)
- [Privacy](PRIVACY.md)
- [Contributing](CONTRIBUTING.md)
- [Code of conduct](CODE_OF_CONDUCT.md)
- [Changelog](CHANGELOG.md)

---

## License

EvalForge20 is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0-only)**. See [LICENSE](LICENSE).

If you run a modified version as a network service, the AGPL requires you to offer the corresponding source to users of that service.

---

<p align="center">
  <strong>EvalForge20</strong><br>
  Measure AI models. Do not guess.
</p>

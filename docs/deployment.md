# Production Deployment Guide

This guide describes a reproducible self-hosted deployment. It does not claim that EvalForge is a managed multi-tenant service.

## 1. Deployment model

| Component | Recommended |
|---|---|
| API | One container/process running `uvicorn src.evalforge.main:app` |
| Frontend | Static Vite build served by a reverse proxy or static host |
| Database | SQLite for single-user; PostgreSQL for multi-user |
| Workers | Keep the API at **one worker** while evaluations run in-process |
| Model inference | Ollama on the same host or a reachable LAN host with a GPU |

Because evaluations execute as in-process background tasks, do **not** scale the API to multiple workers without first introducing a durable external job queue. On restart, active runs are reconciled to `interrupted` rather than silently completed.

## 2. Container deployment

```bash
cd backend
docker compose up -d --build
```

This builds a multi-stage, non-root image, applies Alembic migrations via the entrypoint, and exposes port 8000.

Healthcheck: `GET /api/health/live`
Readiness: `GET /api/health/ready` (reflects database connectivity and Ollama availability)

### PostgreSQL

```bash
export POSTGRES_PASSWORD='<strong-random-password>'
export DATABASE_URL='postgresql+asyncpg://evalforge:<strong-random-password>@db:5432/evalforge'
docker compose --profile postgres up -d --build
```

Use least-privilege credentials in production. The provided Compose file is a starting point, not a hardened database deployment.

## 3. Environment

Copy `.env.example` to `.env` (never commit it) and set at minimum:

```dotenv
ENVIRONMENT=production
HOST=0.0.0.0
DATABASE_URL=postgresql+asyncpg://...
AUTH_TOKEN=<32+ byte random token>
CORS_ORIGINS=https://your-domain.example
LOG_FORMAT=json
LOG_LEVEL=INFO
ALLOW_PRIVATE_PROVIDER_ENDPOINTS=true   # false if only public cloud providers are used
```

Generate a token:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

`ENVIRONMENT=production` rejects `DEBUG=true`, wildcard CORS, and a non-loopback bind without `AUTH_TOKEN`.

## 4. HTTPS and reverse proxy

Terminate TLS at a reverse proxy (Caddy, nginx, Traefik, or a platform load balancer). Example nginx fragment:

```nginx
server {
    listen 443 ssl;
    server_name evalforge.example.com;

    location / {
        proxy_pass http://127.0.0.1:5173;   # static frontend
        proxy_set_header Host $host;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
    }
}
```

If you do not use `AUTH_TOKEN`, restrict access with proxy-level authentication. Never expose an unauthenticated instance to the public internet.

## 5. Frontend build

```bash
cd frontend
npm ci
npm run build
```

Serve `frontend/dist/` as static files. The API base is `/api`; configure the proxy so `/api` reaches the backend.

## 6. Migrations

```bash
cd backend
alembic upgrade head
alembic current
```

The container entrypoint runs `alembic upgrade head` on start. Back up the database before migrating in production. Test migrations against a production-like copy first.

## 7. Backup and restore

```bash
# SQLite
DATABASE_URL=sqlite+aiosqlite:///./evalforge.db scripts/backup_db.sh ./backups

# PostgreSQL (requires pg_dump)
DATABASE_URL='postgresql+asyncpg://...' scripts/backup_db.sh ./backups

# Restore (stop the API first)
DATABASE_URL=... scripts/restore_db.sh ./backups/<file>
```

Store backups off-host, encrypt them, and test restores periodically. A backup is not verified until a restore has been tested.

## 8. Ollama

Ollama executes models on the host CPU/GPU:

```bash
ollama serve
ollama pull qwen2.5:1.5b
```

From a container, point `OLLAMA_BASE_URL` at `http://host.docker.internal:11434` (Compose adds the host-gateway mapping) or at a LAN inference host. Model size must fit available RAM/VRAM. A free application hosting tier does not provide GPU capacity for large local models.

## 9. Monitoring

- `GET /api/health/live` — process liveness.
- `GET /api/health/ready` — database connectivity and provider availability.
- Structured JSON logs with request IDs; redact secrets before shipping logs to third parties.
- Track evaluation failure rates and provider latency from persisted runs.

Alert on repeated readiness failures, database connection loss, and evaluation runs stuck in `running` (should be reconciled on restart).

## 10. Release checklist

- [ ] Fresh install works.
- [ ] `ruff check` and `pytest` pass.
- [ ] `npx tsc -b`, `npm test`, and `npm run build` pass.
- [ ] Migrations apply to a fresh database.
- [ ] Backup and restore tested.
- [ ] `AUTH_TOKEN` set for any non-loopback deployment.
- [ ] HTTPS enabled.
- [ ] CORS restricted to real origins.
- [ ] Ollama reachable and a real evaluation completes.
- [ ] Results persist across restart; interrupted runs are marked `interrupted`.
- [ ] Exports download correctly.
- [ ] Logs do not contain secrets.

# syntax=docker/dockerfile:1
# EvalForge20 backend production image (multi-stage, non-root).

FROM python:3.11-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

COPY pyproject.toml README.md ./
COPY src/ ./src/
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip \
    && /opt/venv/bin/pip install .

FROM python:3.11-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    HOST=0.0.0.0 \
    PORT=8000 \
    ENVIRONMENT=production \
    LOG_FORMAT=json

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system --gid 10001 evalforge \
    && useradd --system --uid 10001 --gid evalforge --home-dir /app --shell /usr/sbin/nologin evalforge

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY src/ ./src/
COPY migrations/ ./migrations/
COPY alembic.ini ./
COPY docker-entrypoint.sh ./

RUN chmod +x /app/docker-entrypoint.sh \
    && mkdir -p /app/data \
    && chown -R evalforge:evalforge /app

USER evalforge

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -fsS "http://127.0.0.1:${PORT}/api/health/live" || exit 1

ENTRYPOINT ["/app/docker-entrypoint.sh"]

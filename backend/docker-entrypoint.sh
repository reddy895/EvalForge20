#!/bin/sh
set -e

echo "==> Applying database migrations (alembic upgrade head)..."
alembic upgrade head

echo "==> Starting EvalForge20 API server..."
exec uvicorn src.evalforge.main:app \
  --host "${HOST:-0.0.0.0}" \
  --port "${PORT:-8000}" \
  --proxy-headers \
  --forwarded-allow-ips="${FORWARDED_ALLOW_IPS:-127.0.0.1}" \
  --no-server-header

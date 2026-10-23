#!/usr/bin/env bash
# Start EvalForge20 backend and frontend concurrently
set -euo pipefail

echo "==> Starting EvalForge20 Local Development Environment..."
trap 'kill $(jobs -p)' EXIT

# Start FastAPI backend
echo "==> Starting backend on http://127.0.0.1:8000..."
.venv/bin/uvicorn src.evalforge.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload &

# Start Vite frontend
echo "==> Starting frontend on http://localhost:5173..."
cd frontend && npm run dev &

wait

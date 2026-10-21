#!/usr/bin/env bash
# EvalForge20 — One-Command Development Startup Script
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$WORKSPACE_ROOT"

echo "=========================================================="
echo " EvalForge20 — Local-First LLM Evaluation Platform"
echo "=========================================================="

# 1. Check or activate Python virtual environment
if [ -d ".venv" ]; then
    echo "✓ Activating virtual environment (.venv)..."
    source .venv/bin/activate
elif [ -n "$VIRTUAL_ENV" ]; then
    echo "✓ Using active virtual environment ($VIRTUAL_ENV)..."
else
    echo "Creating virtual environment with uv / python3..."
    if command -v uv &> /dev/null; then
        uv venv .venv
        source .venv/bin/activate
        uv pip install -e ".[dev]"
    else
        python3 -m venv .venv
        source .venv/bin/activate
        pip install -e ".[dev]"
    fi
fi

# 2. Check Ollama daemon status
echo "Checking local Ollama service status (http://localhost:11434)..."
if curl -s -f http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✓ Ollama is running and accessible."
else
    echo "! NOTE: Local Ollama is not running at http://localhost:11434."
    echo "  To evaluate local models, start Ollama in another terminal:"
    echo "    $ ollama serve"
    echo "  And pull a local model:"
    echo "    $ ollama pull llama3.2"
    echo "  (Deterministic mock testing is active for offline development without Ollama)."
fi

# 3. Seed initial benchmark datasets if database is new
if [ ! -f "evalforge.db" ]; then
    echo "Initializing database and seeding default benchmarks..."
    python scripts/seed_datasets.py
fi

# 4. Launch FastAPI development server
echo ""
echo "🚀 Starting EvalForge20 API backend on http://127.0.0.1:8000"
echo "   Interactive OpenAPI Documentation: http://127.0.0.1:8000/docs"
echo "   Alternative ReDoc Documentation:  http://127.0.0.1:8000/redoc"
echo "=========================================================="
exec uvicorn src.evalforge.main:app --host 127.0.0.1 --port 8000 --reload

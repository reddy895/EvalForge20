#!/usr/bin/env bash
# Probe local Ollama service and list installed models
set -euo pipefail

OLLAMA_URL="${OLLAMA_BASE_URL:-http://localhost:11434}"
echo "==> Checking Ollama daemon at $OLLAMA_URL..."

if curl -s "$OLLAMA_URL/api/tags" > /dev/null; then
    echo " [OK] Ollama is running."
    echo "==> Installed models:"
    curl -s "$OLLAMA_URL/api/tags" | grep -o '"name":"[^"]*"' | cut -d'"' -f4 || echo "None found."
else
    echo " [FAILED] Ollama is not responding at $OLLAMA_URL."
    echo "Hint: Run 'ollama serve' or download from https://ollama.com."
    exit 1
fi

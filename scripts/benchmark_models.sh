#!/usr/bin/env bash
# Run quick benchmark evaluation against selected local model
set -euo pipefail

MODEL="${1:-qwen2.5:7b}"
echo "==> Initiating batch evaluation for model: $MODEL..."
curl -s -X POST "http://127.0.0.1:8000/api/evaluations"      -H "Content-Type: application/json"      -d "{"model_id": "$MODEL", "benchmark_id": "coding_basics"}" || echo "Backend not running."

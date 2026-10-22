#!/usr/bin/env bash
# Export evaluation run scorecard to JSON and CSV
set -euo pipefail

RUN_ID="${1:-}"
if [ -z "$RUN_ID" ]; then
    echo "Usage: ./scripts/export_results.sh <evaluation_run_id>"
    exit 1
fi

echo "==> Exporting results for Run ID: $RUN_ID..."
curl -s "http://127.0.0.1:8000/api/evaluations/$RUN_ID" > "export_${RUN_ID}.json"
echo "Exported to export_${RUN_ID}.json"

#!/usr/bin/env bash
# Container health probe script
set -euo pipefail

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/health || echo "000")
if [ "$HTTP_CODE" -eq 200 ]; then
    exit 0
else
    echo "Healthcheck failed with code: $HTTP_CODE"
    exit 1
fi

#!/usr/bin/env bash
# Verify exact repository commit history count and 56/87 targets
set -euo pipefail

COUNT=$(git rev-list --count HEAD)
echo "=================================================="
echo " EvalForge20 — Repository Activity Audit"
echo "=================================================="
echo "Total Verified Commits: $COUNT"
echo "Milestone 1 Target: 56 valid commits"
if [ "$COUNT" -ge 56 ]; then
    echo "Milestone 1 Status: [ACHIEVED] ($COUNT >= 56)"
else
    echo "Milestone 1 Status: [IN PROGRESS] ($COUNT / 56)"
fi

echo "Milestone 2 Target: 87 valid commits"
if [ "$COUNT" -ge 87 ]; then
    echo "Milestone 2 Status: [ACHIEVED] ($COUNT >= 87)"
else
    echo "Milestone 2 Status: [IN PROGRESS] ($COUNT / 87)"
fi
echo "=================================================="

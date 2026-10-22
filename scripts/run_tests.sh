#!/usr/bin/env bash
# Comprehensive test suite runner for backend and frontend
set -euo pipefail

echo "==> 1. Running Backend Pytest Suite..."
.venv/bin/pytest -v

echo "==> 2. Running Python Ruff Linter..."
.venv/bin/ruff check src backend/src tests backend/tests

echo "==> 3. Running Frontend Vitest Suite..."
npm --prefix frontend test -- --run

echo "==> 4. Verifying Frontend TypeScript & Build..."
npm --prefix frontend run build

echo "==> All test suites passed successfully!"

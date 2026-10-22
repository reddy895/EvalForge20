#!/usr/bin/env bash
# Seed benchmark fixtures and test datasets into database
set -euo pipefail

echo "==> Running Alembic migrations..."
.venv/bin/alembic upgrade head

echo "==> Seeding verified benchmark suites..."
.venv/bin/python -c '
import asyncio
from src.evalforge.storage.database import init_db
asyncio.run(init_db())
print("Seeding complete.")
'

#!/usr/bin/env bash
# Restore an EvalForge database backup.
# Usage: scripts/restore_db.sh <backup-file>
# WARNING: This replaces the current database. Stop the backend first.
set -euo pipefail

BACKUP="${1:-}"
if [[ -z "$BACKUP" || ! -f "$BACKUP" ]]; then
  echo "Usage: scripts/restore_db.sh <backup-file>" >&2
  exit 1
fi

DATABASE_URL="${DATABASE_URL:-sqlite+aiosqlite:///./evalforge.db}"

if [[ "$DATABASE_URL" == sqlite* ]]; then
  DB_PATH="${DATABASE_URL#*:///}"
  DB_PATH="${DB_PATH#./}"
  mkdir -p "$(dirname "$DB_PATH")"
  rm -f "$DB_PATH-wal" "$DB_PATH-shm"
  cp "$BACKUP" "$DB_PATH"
  echo "SQLite database restored to $DB_PATH"
else
  if [[ "$BACKUP" != *.gz ]]; then
    echo "PostgreSQL restores expect a .sql.gz backup." >&2
    exit 1
  fi
  gunzip -c "$BACKUP" | psql "$DATABASE_URL"
  echo "PostgreSQL database restored."
fi

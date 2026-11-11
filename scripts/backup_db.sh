#!/usr/bin/env bash
# Create a consistent backup of the configured EvalForge database.
# Usage: scripts/backup_db.sh [output-directory]
set -euo pipefail

OUT_DIR="${1:-./backups}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$OUT_DIR"

DATABASE_URL="${DATABASE_URL:-sqlite+aiosqlite:///./evalforge.db}"

if [[ "$DATABASE_URL" == sqlite* ]]; then
  DB_PATH="${DATABASE_URL#*:///}"
  DB_PATH="${DB_PATH#./}"
  if [[ ! -f "$DB_PATH" ]]; then
    echo "SQLite database not found: $DB_PATH" >&2
    exit 1
  fi
  TARGET="$OUT_DIR/evalforge-$STAMP.db"
  # Use the SQLite backup API when available for a consistent snapshot including WAL.
  if command -v sqlite3 >/dev/null 2>&1; then
    sqlite3 "$DB_PATH" ".backup '$TARGET'"
  else
    sqlite3_missing=1
    cp "$DB_PATH" "$TARGET"
    [[ -f "$DB_PATH-wal" ]] && cp "$DB_PATH-wal" "$TARGET-wal" || true
    [[ -f "$DB_PATH-shm" ]] && cp "$DB_PATH-shm" "$TARGET-shm" || true
  fi
  echo "SQLite backup written to $TARGET"
else
  if ! command -v pg_dump >/dev/null 2>&1; then
    echo "pg_dump is required for PostgreSQL backups." >&2
    exit 1
  fi
  TARGET="$OUT_DIR/evalforge-$STAMP.sql.gz"
  pg_dump --no-owner --no-privileges "$DATABASE_URL" | gzip -9 > "$TARGET"
  echo "PostgreSQL backup written to $TARGET"
fi

echo "Restore with: scripts/restore_db.sh <backup-file>"

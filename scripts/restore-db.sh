#!/bin/bash
# PostgreSQL restore script
# Usage: ./scripts/restore-db.sh <backup-file.sql.gz>

set -euo pipefail

BACKUP_FILE="${1:-}"

if [[ -z "$BACKUP_FILE" ]]; then
  echo "Usage: $0 <backup-file.sql.gz>"
  exit 1
fi

if [[ ! -f "$BACKUP_FILE" ]]; then
  echo "Error: File not found: $BACKUP_FILE"
  exit 1
fi

# Load .env if present
if [[ -f "$(dirname "$0")/../.env" ]]; then
  set -a
  source "$(dirname "$0")/../.env"
  set +a
fi

POSTGRES_USER="${POSTGRES_USER:-qubot}"
POSTGRES_DB="${POSTGRES_DB:-qubot_db}"
POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"

echo "[restore] Restoring $BACKUP_FILE → ${POSTGRES_DB}"
echo "[restore] WARNING: This will overwrite the current database!"
read -p "Continue? [y/N] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "[restore] Aborted"
  exit 0
fi

gunzip -c "$BACKUP_FILE" | PGPASSWORD="${POSTGRES_PASSWORD:-}" psql \
  -h "$POSTGRES_HOST" \
  -p "$POSTGRES_PORT" \
  -U "$POSTGRES_USER" \
  "$POSTGRES_DB"

echo "[restore] Complete"

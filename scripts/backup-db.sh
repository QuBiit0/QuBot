#!/bin/bash
# PostgreSQL backup script
# Usage: ./scripts/backup-db.sh
# Schedule with cron: 0 2 * * * /path/to/qubot/scripts/backup-db.sh

set -euo pipefail

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
BACKUP_DIR="${BACKUP_DIR:-./backups}"
KEEP_DAYS="${KEEP_DAYS:-7}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/qubot_${TIMESTAMP}.sql.gz"

mkdir -p "$BACKUP_DIR"

echo "[backup] Starting backup: $BACKUP_FILE"

PGPASSWORD="${POSTGRES_PASSWORD:-}" pg_dump \
  -h "$POSTGRES_HOST" \
  -p "$POSTGRES_PORT" \
  -U "$POSTGRES_USER" \
  "$POSTGRES_DB" \
  | gzip > "$BACKUP_FILE"

echo "[backup] Backup complete: $(du -sh "$BACKUP_FILE" | cut -f1)"

# Optional: upload to S3
if [[ -n "${S3_BUCKET:-}" && -n "${S3_ACCESS_KEY:-}" ]]; then
  echo "[backup] Uploading to s3://${S3_BUCKET}/backups/..."
  AWS_ACCESS_KEY_ID="$S3_ACCESS_KEY" \
  AWS_SECRET_ACCESS_KEY="$S3_SECRET_KEY" \
    aws s3 cp "$BACKUP_FILE" "s3://${S3_BUCKET}/backups/$(basename "$BACKUP_FILE")" \
    --region "${S3_REGION:-us-east-1}"
  echo "[backup] S3 upload complete"
fi

# Prune old backups
echo "[backup] Pruning backups older than ${KEEP_DAYS} days..."
find "$BACKUP_DIR" -name "qubot_*.sql.gz" -mtime +"$KEEP_DAYS" -delete
echo "[backup] Done"

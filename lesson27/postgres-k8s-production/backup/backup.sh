#!/bin/bash
set -euo pipefail

BACKUP_DIR="/tmp/pg-backups"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_NAME="postgres-backup-${TIMESTAMP}"

echo "Starting PostgreSQL backup: $BACKUP_NAME"

mkdir -p "$BACKUP_DIR"

# Get primary pod
PRIMARY_POD=$(kubectl get pod -n database -l app=postgres,role=primary -o jsonpath='{.items[0].metadata.name}')

# Perform backup
kubectl exec -n database "$PRIMARY_POD" -- \
  pg_dump -U postgres -d appdb -Fc -f "/tmp/${BACKUP_NAME}.dump"

# Copy backup from pod
kubectl cp "database/${PRIMARY_POD}:/tmp/${BACKUP_NAME}.dump" \
  "${BACKUP_DIR}/${BACKUP_NAME}.dump"

# Compress backup
gzip "${BACKUP_DIR}/${BACKUP_NAME}.dump"

echo "Backup completed: ${BACKUP_DIR}/${BACKUP_NAME}.dump.gz"
echo "Size: $(du -h ${BACKUP_DIR}/${BACKUP_NAME}.dump.gz | cut -f1)"

# Optional: Upload to S3 (uncomment if needed)
# aws s3 cp "${BACKUP_DIR}/${BACKUP_NAME}.dump.gz" "s3://your-bucket/postgres-backups/"

# Clean up old backups (keep last 7 days)
find "$BACKUP_DIR" -name "postgres-backup-*.dump.gz" -mtime +7 -delete

echo "Backup process complete!"

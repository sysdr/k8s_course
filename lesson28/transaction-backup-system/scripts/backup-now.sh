#!/bin/bash
set -euo pipefail

BACKUP_NAME="manual-backup-$(date +%Y%m%d-%H%M%S)"

echo "📦 Creating backup: $BACKUP_NAME"

velero backup create $BACKUP_NAME \
    --include-namespaces transaction-system \
    --default-volumes-to-restic \
    --wait

echo "✅ Backup created: $BACKUP_NAME"
echo ""
echo "Check status:"
echo "  velero backup describe $BACKUP_NAME"
echo "  velero backup logs $BACKUP_NAME"

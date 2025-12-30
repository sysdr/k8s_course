#!/bin/bash
set -euo pipefail

if [ $# -eq 0 ]; then
    echo "Usage: $0 <backup-name>"
    echo ""
    echo "Available backups:"
    velero backup get
    exit 1
fi

BACKUP_NAME=$1
RESTORE_NAME="restore-$(date +%Y%m%d-%H%M%S)"

echo "🔄 Restoring from backup: $BACKUP_NAME"
echo "⚠️  This will restore to namespace: transaction-system"
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

velero restore create $RESTORE_NAME \
    --from-backup $BACKUP_NAME \
    --wait

echo "✅ Restore complete: $RESTORE_NAME"
echo ""
echo "Check status:"
echo "  velero restore describe $RESTORE_NAME"
echo "  velero restore logs $RESTORE_NAME"
echo ""
echo "Verify application:"
echo "  kubectl get pods -n transaction-system"

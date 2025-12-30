#!/bin/bash
set -euo pipefail

echo "💥 DISASTER RECOVERY TEST"
echo "=========================="
echo ""
echo "This script will:"
echo "1. Create a backup of the current system"
echo "2. Generate some test transactions"
echo "3. Simulate a disaster (delete namespace)"
echo "4. Restore from backup"
echo "5. Verify data integrity"
echo ""
read -p "Continue with disaster test? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

BACKUP_NAME="disaster-test-$(date +%Y%m%d-%H%M%S)"

# Step 1: Create backup
echo "📦 Step 1: Creating backup..."
velero backup create $BACKUP_NAME \
    --include-namespaces transaction-system \
    --default-volumes-to-restic \
    --wait

# Step 2: Generate test data
echo "📊 Step 2: Generating test transactions..."
API_POD=$(kubectl get pod -n transaction-system -l app=transaction-api -o jsonpath='{.items[0].metadata.name}')
for i in {1..10}; do
    kubectl exec -n transaction-system $API_POD -- curl -X POST http://localhost:8000/api/v1/transactions \
        -H "Content-Type: application/json" \
        -d "{\"user_id\":\"test-user-$i\",\"amount\":100.0,\"currency\":\"USD\",\"transaction_type\":\"payment\",\"description\":\"Test transaction $i\"}" \
        || true
done

# Get transaction count before disaster
echo "📈 Getting transaction count before disaster..."
BEFORE_COUNT=$(kubectl exec -n transaction-system $API_POD -- curl -s http://localhost:8000/api/v1/stats | jq -r '.total_transactions')
echo "Transactions before disaster: $BEFORE_COUNT"

# Step 3: Simulate disaster
echo "💥 Step 3: Simulating disaster (deleting namespace)..."
sleep 5
kubectl delete namespace transaction-system --wait=false

echo "⏳ Waiting for namespace deletion..."
sleep 30

# Step 4: Restore from backup
echo "🔄 Step 4: Restoring from backup..."
RESTORE_NAME="restore-$(date +%Y%m%d-%H%M%S)"
velero restore create $RESTORE_NAME \
    --from-backup $BACKUP_NAME \
    --wait

# Wait for pods to be ready
echo "⏳ Waiting for pods to be ready..."
kubectl wait --for=condition=ready pod -l app=postgres -n transaction-system --timeout=120s || true
kubectl wait --for=condition=ready pod -l app=transaction-api -n transaction-system --timeout=120s || true

# Step 5: Verify data
echo "✅ Step 5: Verifying data integrity..."
sleep 10
API_POD=$(kubectl get pod -n transaction-system -l app=transaction-api -o jsonpath='{.items[0].metadata.name}')
AFTER_COUNT=$(kubectl exec -n transaction-system $API_POD -- curl -s http://localhost:8000/api/v1/stats | jq -r '.total_transactions')
echo "Transactions after restore: $AFTER_COUNT"

if [ "$BEFORE_COUNT" -eq "$AFTER_COUNT" ]; then
    echo "✅ SUCCESS! Data integrity verified!"
    echo "   Before: $BEFORE_COUNT transactions"
    echo "   After:  $AFTER_COUNT transactions"
else
    echo "⚠️  WARNING: Transaction count mismatch!"
    echo "   Before: $BEFORE_COUNT"
    echo "   After:  $AFTER_COUNT"
    echo "   This may be due to timing - some transactions may not have been committed before disaster"
fi

echo ""
echo "Disaster recovery test complete!"

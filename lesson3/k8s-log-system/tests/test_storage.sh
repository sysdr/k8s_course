#!/bin/bash
set -euo pipefail

echo "Testing persistent storage patterns..."

# Check PVCs
echo "1. Checking PersistentVolumeClaims..."
kubectl get pvc -n log-system

# Verify StatefulSet volumes
echo "2. Verifying StatefulSet persistent volumes..."
for i in 0 1 2; do
    echo "Checking log-processor-$i..."
    kubectl exec -n log-system log-processor-$i -- df -h /app/buffer || true
done

# Test data persistence
echo "3. Testing data persistence across pod restart..."
POD_NAME="log-processor-0"
kubectl exec -n log-system $POD_NAME -- sh -c 'echo "test-data" > /app/buffer/test.txt'
kubectl delete pod -n log-system $POD_NAME --force
kubectl wait --for=condition=ready pod/$POD_NAME -n log-system --timeout=120s
kubectl exec -n log-system $POD_NAME -- cat /app/buffer/test.txt

echo "Storage tests complete!"

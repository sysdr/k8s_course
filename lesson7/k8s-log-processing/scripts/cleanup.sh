#!/bin/bash
set -euo pipefail

NAMESPACE="log-processing"

echo "Cleaning up log processing system..."

# Delete all resources
kubectl delete namespace $NAMESPACE --wait=true || true

# Delete kind cluster if exists
if command -v kind &> /dev/null; then
    kind delete cluster --name log-processing-cluster || true
fi

echo "✓ Cleanup complete"

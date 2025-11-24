#!/bin/bash
set -euo pipefail

echo "Cleaning up resources..."

# Delete namespace (cascades to all resources)
kubectl delete namespace log-platform --ignore-not-found=true

# Delete kind cluster
if command -v kind &> /dev/null; then
    kind delete cluster --name log-platform 2>/dev/null || true
fi

echo "✓ Cleanup complete"

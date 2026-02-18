#!/bin/bash
set -euo pipefail

echo "🧹 Cleaning up Kubernetes resources..."

# Delete all resources in log-platform namespace
kubectl delete namespace log-platform --ignore-not-found=true

# Delete monitoring namespace
kubectl delete namespace monitoring --ignore-not-found=true

# Delete kind cluster (if exists)
if command -v kind &> /dev/null; then
    kind delete cluster --name log-platform 2>/dev/null || true
fi

echo "✅ Cleanup complete!"

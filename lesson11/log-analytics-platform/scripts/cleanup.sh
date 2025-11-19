#!/bin/bash
set -euo pipefail

NAMESPACE="log-analytics"

echo "Cleaning up Log Analytics Platform..."

# Delete all resources
kubectl delete namespace $NAMESPACE --ignore-not-found

# Optionally delete local cluster
if [[ "${1:-}" == "--full" ]]; then
    kind delete cluster --name log-analytics 2>/dev/null || true
    echo "Cluster deleted"
fi

echo "Cleanup complete!"

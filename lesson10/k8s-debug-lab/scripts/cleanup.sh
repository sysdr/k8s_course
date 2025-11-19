#!/bin/bash
set -euo pipefail

echo "Cleaning up debug lab..."

# Delete namespace and all resources
kubectl delete namespace log-processor --ignore-not-found=true

# Optionally delete the kind cluster
if [ "${1:-}" == "--full" ]; then
    echo "Deleting kind cluster..."
    kind delete cluster --name debug-lab
fi

echo "Cleanup complete!"

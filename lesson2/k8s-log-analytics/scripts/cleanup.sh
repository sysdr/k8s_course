#!/bin/bash
set -euo pipefail

echo "Cleaning up resources..."

# Delete Kubernetes resources
echo "Deleting Kubernetes resources..."
kubectl delete namespace log-analytics --ignore-not-found=true

# Delete kind cluster
echo "Deleting kind cluster..."
kind delete cluster --name log-analytics

echo "✓ Cleanup complete!"

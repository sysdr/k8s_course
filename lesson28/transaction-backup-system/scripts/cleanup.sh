#!/bin/bash
set -euo pipefail

echo "🧹 Cleaning up..."

# Delete namespaces
kubectl delete namespace transaction-system --ignore-not-found=true --wait=false
kubectl delete namespace monitoring --ignore-not-found=true --wait=false
kubectl delete namespace minio --ignore-not-found=true --wait=false
kubectl delete namespace velero --ignore-not-found=true --wait=false

# Delete kind cluster
read -p "Delete kind cluster? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    kind delete cluster --name transaction-system
fi

echo "✅ Cleanup complete!"

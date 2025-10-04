#!/bin/bash
set -euo pipefail

echo "Cleaning up resources..."

# Delete all resources in log-system namespace
kubectl delete namespace log-system --ignore-not-found=true

# Delete monitoring namespace
kubectl delete namespace monitoring --ignore-not-found=true

# Delete kind cluster
read -p "Delete kind cluster? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    kind delete cluster --name log-system
    echo "Cluster deleted!"
fi

echo "Cleanup complete!"

#!/bin/bash
set -euo pipefail

echo "Cleaning up Log Analytics Platform..."

# Delete all resources
kubectl delete namespace log-analytics --ignore-not-found=true

# Delete PVs
kubectl delete pv --all --ignore-not-found=true

echo "Cleanup complete!"

# Optional: Delete kind cluster
read -p "Delete kind cluster? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    kind delete cluster --name log-analytics
    echo "Cluster deleted!"
fi

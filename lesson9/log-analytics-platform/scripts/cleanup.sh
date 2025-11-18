#!/bin/bash
set -euo pipefail

echo "Cleaning up log analytics platform..."

# Delete namespace (this will delete all resources)
kubectl delete namespace log-analytics --ignore-not-found=true

# Delete kind cluster
read -p "Delete kind cluster? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    kind delete cluster --name log-analytics
    echo "Cluster deleted"
fi

echo "Cleanup complete!"

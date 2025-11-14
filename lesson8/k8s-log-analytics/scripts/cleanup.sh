#!/bin/bash
set -euo pipefail

echo "Cleaning up resources..."

# Delete namespace (cascades to all resources)
kubectl delete namespace log-analytics --ignore-not-found=true

# Delete kind cluster
kind delete cluster --name log-analytics

echo "Cleanup complete!"

#!/bin/bash
set -euo pipefail

echo "Cleaning up Secrets Management Platform..."

# Delete all resources
kubectl delete namespace secrets-platform --ignore-not-found=true
kubectl delete namespace secrets-platform-prod --ignore-not-found=true

# Delete kind cluster
kind delete cluster --name secrets-platform

echo "Cleanup complete!"

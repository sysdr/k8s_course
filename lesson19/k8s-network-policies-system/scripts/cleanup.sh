#!/bin/bash
set -euo pipefail

echo "Cleaning up resources..."

# Delete all resources
kubectl delete -f k8s/deployments/frontend/ --ignore-not-found=true
kubectl delete -f k8s/deployments/backend/ --ignore-not-found=true
kubectl delete -f k8s/deployments/data-layer/ --ignore-not-found=true
kubectl delete -f k8s/network-policies/ --ignore-not-found=true
kubectl delete -f istio/ --ignore-not-found=true
kubectl delete -f k8s/namespaces/namespaces.yaml --ignore-not-found=true

echo "✓ Cleanup complete"

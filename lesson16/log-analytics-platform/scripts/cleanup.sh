#!/bin/bash
set -euo pipefail

echo "Cleaning up Log Analytics Platform..."

# Check if Kubernetes cluster is available
if ! kubectl cluster-info &>/dev/null; then
    echo "⚠️  No Kubernetes cluster detected. Skipping Kubernetes resource cleanup."
    echo "✓ Cleanup complete (no cluster to clean)!"
    exit 0
fi

# Delete application resources
echo "Deleting application resources..."
kubectl delete ingress --all --ignore-not-found=true || true
kubectl delete deployment --all --ignore-not-found=true || true
kubectl delete service --all --ignore-not-found=true || true
kubectl delete hpa --all --ignore-not-found=true || true
kubectl delete configmap --all --ignore-not-found=true || true

# Delete NGINX Ingress Controller
echo "Deleting NGINX Ingress Controller..."
kubectl delete namespace ingress-nginx --ignore-not-found=true || true

# Delete monitoring stack
echo "Deleting monitoring stack..."
kubectl delete namespace monitoring --ignore-not-found=true || true

echo "✓ Cleanup complete!"

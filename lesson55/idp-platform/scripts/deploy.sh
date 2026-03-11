#!/bin/bash

set -euo pipefail

echo "=== Deploying IDP Platform ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Deploy platform CRDs
echo "Deploying Custom Resource Definitions..."
kubectl apply -f "$PROJECT_ROOT/k8s/platform-crds/"

# Deploy platform control plane
echo "Deploying platform control plane..."
kubectl apply -f "$PROJECT_ROOT/k8s/platform-system/"

# Wait for platform API
echo "Waiting for platform API..."
kubectl wait --namespace platform-system \
  --for=condition=ready pod \
  --selector=app=platform-api \
  --timeout=120s

# Deploy developer portal
echo "Deploying developer portal..."
kubectl apply -f "$PROJECT_ROOT/k8s/platform-frontend/"

# Configure ArgoCD
echo "Configuring ArgoCD..."
kubectl apply -f "$PROJECT_ROOT/k8s/argocd-setup/"

echo ""
echo "✓ Platform deployed successfully!"
echo ""
echo "Access points:"
echo "- Platform API: kubectl port-forward -n platform-system svc/platform-api 8000:80"
echo "- Developer Portal: kubectl port-forward -n platform-frontend svc/developer-portal 3000:80"
echo "- Grafana: kubectl port-forward -n monitoring svc/prometheus-operator-grafana 3001:80"
echo "- ArgoCD: kubectl port-forward -n argocd svc/argocd-server 8080:443"

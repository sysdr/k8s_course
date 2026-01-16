#!/bin/bash
set -euo pipefail

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "Deploying GitOps platform..."

# Create namespaces
kubectl apply -f "${PROJECT_ROOT}/gitops-repo/infrastructure/namespaces/namespaces.yaml"

# Deploy ArgoCD Applications
kubectl apply -f "${PROJECT_ROOT}/gitops-repo/argocd-apps/dev-application.yaml"
kubectl apply -f "${PROJECT_ROOT}/gitops-repo/argocd-apps/prod-application.yaml"

# Alternatively, use ApplicationSet
# kubectl apply -f ../gitops-repo/argocd-apps/applicationset.yaml

echo "Waiting for applications to sync..."
sleep 10

# Check application status
kubectl get applications -n argocd

echo "============================================"
echo "GitOps platform deployed!"
echo "============================================"
echo "Check ArgoCD UI to see sync status"
echo "Access dashboard:"
echo "  kubectl port-forward svc/dashboard -n gitops-apps-prod 8081:80"

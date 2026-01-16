#!/bin/bash
set -euo pipefail

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "Installing ArgoCD..."

# Create namespace
kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -

# Install ArgoCD
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Wait for ArgoCD to be ready
echo "Waiting for ArgoCD to be ready..."
kubectl wait --for=condition=available --timeout=600s deployment/argocd-server -n argocd

# Apply custom configurations
kubectl apply -f "${PROJECT_ROOT}/k8s/argocd/argocd-cm.yaml"
kubectl apply -f "${PROJECT_ROOT}/k8s/argocd/argocd-rbac-cm.yaml"
kubectl apply -f "${PROJECT_ROOT}/k8s/argocd/argocd-notifications-cm.yaml"

# Get initial admin password
ARGOCD_PASSWORD=$(kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d)

echo "============================================"
echo "ArgoCD installed successfully!"
echo "============================================"
echo "Access ArgoCD UI:"
echo "  kubectl port-forward svc/argocd-server -n argocd 8080:443"
echo ""
echo "Login credentials:"
echo "  Username: admin"
echo "  Password: ${ARGOCD_PASSWORD}"
echo "============================================"

# Save password to file
echo "${ARGOCD_PASSWORD}" > argocd-password.txt
echo "Password saved to: argocd-password.txt"

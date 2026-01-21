#!/bin/bash
set -euo pipefail

echo "Installing ArgoCD..."

# Install ArgoCD
kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

echo "Waiting for ArgoCD to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/argocd-server -n argocd

# Get admin password
ARGOCD_PASSWORD=$(kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d)

echo ""
echo "ArgoCD installed successfully!"
echo "================================"
echo "ArgoCD UI: http://localhost:8080"
echo "Username: admin"
echo "Password: $ARGOCD_PASSWORD"
echo ""
echo "Port-forward with: kubectl port-forward svc/argocd-server -n argocd 8080:443"
echo ""

# Optionally install ArgoCD CLI
if ! command -v argocd &> /dev/null; then
    echo "Installing ArgoCD CLI..."
    curl -sSL -o argocd https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
    chmod +x argocd
    sudo mv argocd /usr/local/bin/
    echo "ArgoCD CLI installed"
fi

#!/bin/bash
set -euo pipefail

echo "Cleaning up GitOps platform..."

# Delete ArgoCD applications
kubectl delete applications --all -n argocd

# Delete namespaces
kubectl delete namespace gitops-apps-dev
kubectl delete namespace gitops-apps-staging
kubectl delete namespace gitops-apps-prod
kubectl delete namespace argocd
kubectl delete namespace monitoring

# Delete kind cluster (optional)
read -p "Delete kind cluster? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    kind delete cluster --name gitops-argocd
    echo "Cluster deleted"
fi

echo "Cleanup complete!"

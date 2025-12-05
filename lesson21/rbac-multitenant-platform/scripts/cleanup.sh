#!/bin/bash
set -euo pipefail

echo "Cleaning up RBAC platform..."

read -p "Are you sure you want to delete everything? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cleanup cancelled."
    exit 0
fi

# Delete namespaces (this cascades to all resources)
kubectl delete namespace analytics --ignore-not-found=true
kubectl delete namespace devops --ignore-not-found=true
kubectl delete namespace developers --ignore-not-found=true
kubectl delete namespace auditors --ignore-not-found=true

# Delete cluster-wide resources
kubectl delete clusterrole devops-team-role --ignore-not-found=true
kubectl delete clusterrole auditor-role --ignore-not-found=true
kubectl delete clusterrole analytics-cluster-reader --ignore-not-found=true
kubectl delete clusterrole rbac-validator --ignore-not-found=true

kubectl delete clusterrolebinding devops-team-binding --ignore-not-found=true
kubectl delete clusterrolebinding auditor-binding --ignore-not-found=true
kubectl delete clusterrolebinding analytics-cluster-reader-binding --ignore-not-found=true
kubectl delete clusterrolebinding rbac-validator-binding --ignore-not-found=true

echo ""
echo "✓ Cleanup complete!"
echo ""
echo "To delete the kind cluster entirely:"
echo "kind delete cluster --name rbac-platform"

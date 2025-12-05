#!/bin/bash
set -euo pipefail

echo "Deploying RBAC Multi-Tenant Platform..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Create namespaces
echo "Creating namespaces..."
kubectl apply -f k8s/namespaces/all-namespaces.yaml

# Create ServiceAccounts
echo "Creating ServiceAccounts..."
kubectl apply -f k8s/serviceaccounts/all-serviceaccounts.yaml

# Create RBAC policies
echo "Creating RBAC policies..."
kubectl apply -f k8s/rbac/roles.yaml
kubectl apply -f k8s/rbac/clusterroles.yaml
kubectl apply -f k8s/rbac/rolebindings.yaml
kubectl apply -f k8s/rbac/clusterrolebindings.yaml

# Deploy services
echo "Deploying services..."
kubectl apply -f k8s/deployments/
kubectl apply -f k8s/services/all-services.yaml

# Apply NetworkPolicies
echo "Applying NetworkPolicies..."
kubectl apply -f k8s/networkpolicies/

echo ""
echo "✓ Deployment complete!"
echo ""
echo "Waiting for pods to be ready..."
kubectl wait --for=condition=ready pod -l app=log-processor -n analytics --timeout=120s
kubectl wait --for=condition=ready pod -l app=analytics-api -n analytics --timeout=120s
kubectl wait --for=condition=ready pod -l app=rbac-validator -n analytics --timeout=120s

echo ""
echo "✓ All pods are ready!"
echo ""
echo "Service endpoints:"
echo "Frontend: http://localhost (once port-forwarded)"
echo ""
echo "To access the frontend:"
echo "kubectl port-forward -n analytics svc/frontend 8080:80"

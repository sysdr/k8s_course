#!/bin/bash
set -euo pipefail

echo "=== Deploying Log Analytics Platform ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Create namespace
echo "Creating namespace..."
kubectl apply -f "${PROJECT_ROOT}/k8s/namespaces/log-analytics.yaml"

# Apply Kubernetes resources
echo "Deploying Kubernetes resources..."
kubectl apply -f "${PROJECT_ROOT}/k8s/secrets/"
kubectl apply -f "${PROJECT_ROOT}/k8s/rbac/"
kubectl apply -f "${PROJECT_ROOT}/k8s/statefulsets/"
kubectl apply -f "${PROJECT_ROOT}/k8s/services/"

echo "Waiting for StatefulSets to be ready..."
kubectl wait --for=condition=ready --timeout=300s pod -l app=kafka -n log-analytics
kubectl wait --for=condition=ready --timeout=300s pod -l app=timescaledb -n log-analytics
kubectl wait --for=condition=ready --timeout=300s pod -l app=redis -n log-analytics

echo "Deploying application services..."
kubectl apply -f "${PROJECT_ROOT}/k8s/deployments/"
kubectl apply -f "${PROJECT_ROOT}/k8s/hpa/"
kubectl apply -f "${PROJECT_ROOT}/k8s/pdb/"
kubectl apply -f "${PROJECT_ROOT}/k8s/networkpolicies/"

# Apply Istio configs
echo "Applying Istio configurations..."
kubectl apply -f "${PROJECT_ROOT}/istio/gateway/"
kubectl apply -f "${PROJECT_ROOT}/istio/virtualservices/"
kubectl apply -f "${PROJECT_ROOT}/istio/destinationrules/"
kubectl apply -f "${PROJECT_ROOT}/istio/peerauthentication/"
kubectl apply -f "${PROJECT_ROOT}/istio/authorizationpolicies/"

echo "Waiting for deployments to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/ingestion-api -n log-analytics
kubectl wait --for=condition=available --timeout=300s deployment/query-api -n log-analytics
kubectl wait --for=condition=available --timeout=300s deployment/dashboard -n log-analytics

echo "✓ Deployment complete!"
echo ""
echo "Access the application:"
echo "  Dashboard: http://localhost"
echo ""
echo "View service mesh:"
echo "  istioctl dashboard kiali"

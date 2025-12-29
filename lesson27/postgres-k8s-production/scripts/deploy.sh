#!/bin/bash
set -euo pipefail

echo "Deploying PostgreSQL HA system..."

# Create namespaces
kubectl apply -f k8s/base/namespace.yaml

# Deploy database layer
kubectl apply -f k8s/base/database/

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
kubectl wait --for=condition=ready pod -l app=postgres -n database --timeout=300s

# Deploy PgBouncer
kubectl apply -f k8s/base/pgbouncer/

# Deploy services
kubectl apply -f k8s/base/services/

# Deploy Istio configurations
kubectl apply -f istio/

# Deploy monitoring
kubectl apply -f monitoring/prometheus/

echo "Deployment complete!"
echo ""
echo "Access the dashboard:"
echo "  kubectl port-forward -n services svc/frontend 8080:80"
echo ""
echo "Check status:"
echo "  kubectl get pods -n database"
echo "  kubectl get pods -n services"

#!/bin/bash
set -euo pipefail

NAMESPACE="log-processing"

echo "Deploying log processing system to Kubernetes..."

# Create namespace
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Apply base manifests
kubectl apply -k k8s/base/

# Wait for deployments
echo "Waiting for deployments to be ready..."
kubectl wait --for=condition=available --timeout=300s \
  deployment/redis \
  deployment/ingestion-api \
  deployment/analytics-engine \
  deployment/dashboard \
  -n $NAMESPACE

# Apply monitoring stack
kubectl apply -f k8s/monitoring/

echo "✓ Deployment complete!"
echo ""
echo "Access the dashboard:"
echo "  kubectl port-forward svc/dashboard-service 8080:80 -n $NAMESPACE"
echo ""
echo "Access Grafana:"
echo "  kubectl port-forward svc/grafana 3000:3000 -n $NAMESPACE"

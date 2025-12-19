#!/bin/bash
set -euo pipefail

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Change to project root (parent of scripts directory)
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

echo "Deploying Secrets Management Platform from: $PROJECT_ROOT"

# Create namespace
kubectl apply -f k8s/base/namespace.yaml

# Deploy PostgreSQL
echo "Deploying PostgreSQL..."
kubectl apply -f k8s/base/postgres.yaml
kubectl wait --for=condition=ready pod -l app=postgres -n secrets-platform --timeout=120s

# Deploy Vault Simulator
echo "Deploying Vault Simulator..."
kubectl apply -f k8s/base/vault-simulator.yaml
kubectl wait --for=condition=ready pod -l app=vault-simulator -n secrets-platform --timeout=60s

# Deploy Services
echo "Deploying microservices..."
kubectl apply -f k8s/base/log-ingestion-service.yaml
kubectl apply -f k8s/base/log-processing-service.yaml
kubectl apply -f k8s/base/analytics-api-service.yaml
kubectl apply -f k8s/base/secrets-rotation-service.yaml

# Deploy Frontend
echo "Deploying frontend..."
kubectl apply -f k8s/base/frontend.yaml

# Deploy Monitoring
echo "Deploying monitoring stack..."
kubectl apply -f monitoring/prometheus/prometheus.yaml
kubectl apply -f monitoring/grafana/grafana.yaml

# Deploy Istio resources
echo "Configuring Istio..."
kubectl apply -f istio/

echo "Deployment complete!"
echo ""
echo "Access the platform:"
echo "  Frontend: Run './scripts/port-forward.sh' to set up port-forward"
echo "    (Will use port 80 if available, otherwise port 8080)"
echo "  Grafana: kubectl port-forward -n secrets-platform svc/grafana 3000:3000"
echo "  Prometheus: kubectl port-forward -n secrets-platform svc/prometheus 9090:9090"
echo ""
echo "Check deployment status:"
echo "  kubectl get pods -n secrets-platform"

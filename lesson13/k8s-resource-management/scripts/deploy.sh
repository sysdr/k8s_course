#!/bin/bash
set -euo pipefail

echo "Deploying log platform to Kubernetes..."

# Apply namespace and quotas
kubectl apply -f k8s/base/namespace.yaml

# Wait for namespace to be active (namespaces don't have Ready condition)
kubectl wait --for=jsonpath='{.status.phase}'=Active namespace/log-platform --timeout=30s || true

# Deploy Redis
kubectl apply -f k8s/base/redis.yaml

# Wait for Redis
echo "Waiting for Redis..."
kubectl wait --for=condition=available --timeout=120s deployment/redis -n log-platform

# Deploy services
kubectl apply -f k8s/base/log-ingest.yaml
kubectl apply -f k8s/base/log-parser.yaml
kubectl apply -f k8s/base/analytics-engine.yaml
kubectl apply -f k8s/base/frontend.yaml

# Deploy monitoring
kubectl apply -f monitoring/prometheus/deployment.yaml
kubectl apply -f monitoring/grafana/deployment.yaml

echo "Waiting for deployments to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment --all -n log-platform

echo ""
echo "✓ Deployment complete!"
echo ""
echo "Services:"
kubectl get pods -n log-platform
echo ""
echo "Access the application:"
echo "  Frontend: http://localhost:8080"
echo "  Log Ingest API: http://localhost:8000"
echo "  Prometheus: kubectl port-forward -n log-platform svc/prometheus 9090:9090"
echo "  Grafana: kubectl port-forward -n log-platform svc/grafana 3000:3000"

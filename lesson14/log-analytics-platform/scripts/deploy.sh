#!/bin/bash
set -euo pipefail

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "Deploying Log Analytics Platform to Kubernetes..."
echo "Project root: ${PROJECT_ROOT}"

# Apply namespace and storage
kubectl apply -f "${PROJECT_ROOT}/k8s/base/namespace.yaml"
kubectl apply -f "${PROJECT_ROOT}/k8s/storage/"

# Apply secrets (check if secrets.yaml exists, otherwise use example)
if [ -f "${PROJECT_ROOT}/k8s/secrets/secrets.yaml" ]; then
    kubectl apply -f "${PROJECT_ROOT}/k8s/secrets/secrets.yaml"
else
    echo "Warning: k8s/secrets/secrets.yaml not found!"
    echo "Please create it from k8s/secrets/secrets.yaml.example"
    echo "Or create secrets manually using kubectl"
    read -p "Continue without secrets? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Deploy StatefulSets (in order)
kubectl apply -f "${PROJECT_ROOT}/k8s/statefulsets/timescaledb.yaml"
echo "Waiting for TimescaleDB to be ready..."
kubectl wait --for=condition=ready pod -l app=timescaledb -n log-analytics --timeout=300s || echo "Warning: TimescaleDB not ready yet"

kubectl apply -f "${PROJECT_ROOT}/k8s/statefulsets/kafka.yaml"
echo "Waiting for Kafka to be ready..."
sleep 30

kubectl apply -f "${PROJECT_ROOT}/k8s/statefulsets/minio.yaml"

# Deploy microservices
kubectl apply -f "${PROJECT_ROOT}/k8s/deployments/"

# Deploy monitoring
kubectl apply -f "${PROJECT_ROOT}/monitoring/prometheus/prometheus-config.yaml"
kubectl apply -f "${PROJECT_ROOT}/monitoring/grafana/grafana-config.yaml"

echo "Deployment complete!"
echo ""
echo "Access services:"
echo "  Frontend: kubectl port-forward -n log-analytics svc/frontend 8080:80"
echo "  Grafana: kubectl port-forward -n log-analytics svc/grafana 3000:3000"
echo "  Prometheus: kubectl port-forward -n log-analytics svc/prometheus 9090:9090"

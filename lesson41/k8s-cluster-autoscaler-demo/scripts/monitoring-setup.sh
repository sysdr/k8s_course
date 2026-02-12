#!/bin/bash
set -euo pipefail

echo "Deploying monitoring stack..."
kubectl apply -f k8s/monitoring/

echo "Waiting for Prometheus to be ready..."
kubectl wait --for=condition=Ready pod -l app=prometheus -n log-platform --timeout=300s

echo "Waiting for Grafana to be ready..."
kubectl wait --for=condition=Ready pod -l app=grafana -n log-platform --timeout=300s

echo "Monitoring stack deployed successfully"
echo ""
echo "Access monitoring:"
echo "  Prometheus: kubectl port-forward -n log-platform svc/prometheus 9090:9090"
echo "  Grafana: kubectl port-forward -n log-platform svc/grafana 3000:3000"
echo "  Default Grafana credentials: admin/admin"

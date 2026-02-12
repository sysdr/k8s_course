#!/bin/bash

set -euo pipefail

echo "Setting up monitoring stack..."

# Deploy Prometheus and Grafana
kubectl apply -f k8s/monitoring/

# Wait for Prometheus
kubectl wait --for=condition=available --timeout=120s deployment/prometheus -n logging-system

# Wait for Grafana
kubectl wait --for=condition=available --timeout=120s deployment/grafana -n logging-system

# Get Grafana URL
GRAFANA_URL=$(kubectl get svc grafana -n logging-system -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

echo "Monitoring stack deployed successfully!"
echo "Grafana URL: http://${GRAFANA_URL}:3000"
echo "Default credentials: admin/admin"

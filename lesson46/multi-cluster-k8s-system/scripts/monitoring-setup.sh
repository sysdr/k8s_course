#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

echo "Setting up monitoring stack..."

kubectl create namespace monitoring --context kind-control-plane

echo "Installing Prometheus..."
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --kube-context kind-control-plane \
  -f monitoring/prometheus/prometheus-config.yaml

echo "Installing Grafana dashboards..."
kubectl apply -f monitoring/grafana/dashboards/ --context kind-control-plane

echo "Installing Jaeger..."
kubectl apply -f monitoring/jaeger/jaeger-config.yaml --context kind-control-plane

echo "Monitoring stack deployed!"
echo "Access Grafana at: http://localhost:30300"
echo "Access Prometheus at: http://localhost:30900"
echo "Access Jaeger at: http://localhost:31686"

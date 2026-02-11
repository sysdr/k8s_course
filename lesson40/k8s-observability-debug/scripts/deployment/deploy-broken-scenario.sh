#!/bin/bash
set -euo pipefail

echo "🔥 Deploying BROKEN observability scenario..."
echo "This intentionally creates a 'No Data' situation in Grafana"

# Deploy applications
kubectl apply -f k8s/base/applications/

# Deploy BROKEN ServiceMonitor
kubectl apply -f k8s/overlays/broken/servicemonitor-broken.yaml

# Install kube-prometheus-stack
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm upgrade --install kube-prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --values monitoring/prometheus/prometheus-values.yaml \
  --wait

echo ""
echo "✅ Broken scenario deployed!"
echo ""
echo "Expected issues:"
echo "  1. Grafana will show 'No Data'"
echo "  2. Prometheus targets page will show zero log-processor targets"
echo "  3. ServiceMonitor won't be discovered by Prometheus"
echo ""
echo "To diagnose, run: python3 scripts/diagnostics/check-observability-stack.py"
echo ""
echo "Port-forward commands:"
echo "  Grafana:    kubectl port-forward -n monitoring svc/kube-prometheus-grafana 3000:80"
echo "  Prometheus: kubectl port-forward -n monitoring svc/kube-prometheus-prometheus 9090:9090"

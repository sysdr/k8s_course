#!/bin/bash
set -euo pipefail

echo "=== Setting up Monitoring Stack ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Apply Prometheus ServiceMonitors
echo "Deploying Prometheus ServiceMonitors..."
kubectl apply -f "${PROJECT_ROOT}/monitoring/prometheus/"

# Apply Grafana dashboards
echo "Deploying Grafana dashboards..."
kubectl apply -f "${PROJECT_ROOT}/monitoring/grafana/"

echo "✓ Monitoring stack deployed"
echo ""
echo "Access monitoring:"
echo "  Prometheus: kubectl port-forward -n istio-system svc/prometheus 9090:9090"
echo "  Grafana:    istioctl dashboard grafana"
echo "  Jaeger:     istioctl dashboard jaeger"

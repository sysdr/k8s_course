#!/bin/bash

# Setup Prometheus monitoring for cluster autoscaler

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAB_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SERVICEMONITOR_YAML="$LAB_ROOT/kubernetes/monitoring/autoscaler-servicemonitor.yaml"

echo "Installing kube-prometheus-stack..."

# Add Prometheus helm repo
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install Prometheus operator
helm upgrade --install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false \
  --set grafana.adminPassword=admin \
  --wait

echo ""
echo "Applying autoscaler ServiceMonitor..."
kubectl apply -f "$SERVICEMONITOR_YAML"

echo ""
echo "Prometheus is available at: kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090"
echo "Grafana is available at: kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80"
echo "Grafana credentials: admin/admin"

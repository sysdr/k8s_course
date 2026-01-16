#!/bin/bash
set -euo pipefail

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "Setting up monitoring stack..."

# Install Prometheus Operator
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

# Install using Helm
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false

# Apply ServiceMonitors
kubectl apply -f "${PROJECT_ROOT}/k8s/monitoring/servicemonitor.yaml"
kubectl apply -f "${PROJECT_ROOT}/k8s/monitoring/prometheusrule.yaml"

# Apply Grafana dashboard
kubectl apply -f "${PROJECT_ROOT}/gitops-repo/infrastructure/monitoring/grafana-dashboard.yaml"

echo "============================================"
echo "Monitoring stack deployed!"
echo "============================================"
echo "Access Grafana:"
echo "  kubectl port-forward svc/prometheus-grafana -n monitoring 8082:80"
echo "  Username: admin"
echo "  Password: prom-operator"

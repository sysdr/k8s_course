#!/bin/bash
set -euo pipefail

echo "Setting up monitoring stack..."

# Create monitoring namespace
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

# Install Prometheus using Helm
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm upgrade --install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false

echo "Monitoring stack deployed!"
echo "Access Grafana:"
echo "kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80"
echo "Default credentials: admin/prom-operator"

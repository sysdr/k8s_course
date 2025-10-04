#!/bin/bash
set -euo pipefail

echo "Setting up monitoring stack..."

# Install Prometheus using Helm
echo "Installing Prometheus..."
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm install prometheus prometheus-community/kube-prometheus-stack \
    --namespace monitoring \
    --create-namespace \
    --values monitoring/prometheus/prometheus.yaml \
    --wait

echo "✓ Prometheus installed"

echo ""
echo "Access Grafana:"
echo "  kubectl port-forward -n monitoring svc/prometheus-grafana 3001:80"
echo "  Username: admin"
echo "  Password: $(kubectl get secret -n monitoring prometheus-grafana -o jsonpath='{.data.admin-password}' | base64 -d)"

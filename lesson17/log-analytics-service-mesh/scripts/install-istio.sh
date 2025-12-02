#!/bin/bash
set -euo pipefail

echo "=== Installing Istio Service Mesh ==="

# Check if istioctl is installed
if ! command -v istioctl &> /dev/null; then
    echo "Installing istioctl..."
    curl -L https://istio.io/downloadIstio | sh -
    cd istio-*
    export PATH=$PWD/bin:$PATH
    cd ..
fi

# Install Istio
echo "Installing Istio with demo profile..."
istioctl install --set profile=demo -y

# Enable sidecar injection for log-analytics namespace
echo "Enabling automatic sidecar injection..."
kubectl label namespace log-analytics istio-injection=enabled --overwrite

# Install addons
echo "Installing Istio addons (Kiali, Prometheus, Grafana, Jaeger)..."
kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.20/samples/addons/prometheus.yaml
kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.20/samples/addons/grafana.yaml
kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.20/samples/addons/jaeger.yaml
kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.20/samples/addons/kiali.yaml

echo "Waiting for Istio components to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/istiod -n istio-system
kubectl wait --for=condition=available --timeout=300s deployment/kiali -n istio-system || true

echo "✓ Istio installed successfully"
echo ""
echo "Access dashboards:"
echo "  Kiali:      istioctl dashboard kiali"
echo "  Grafana:    istioctl dashboard grafana"
echo "  Jaeger:     istioctl dashboard jaeger"

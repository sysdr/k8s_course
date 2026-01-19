#!/bin/bash

set -euo pipefail

echo "Deploying Progressive Delivery system..."

# Create namespace
kubectl apply -f k8s/base/namespace.yaml

# Deploy base services
echo "Deploying services..."
kubectl apply -f k8s/base/

# Deploy Istio configurations
echo "Configuring Istio..."
kubectl apply -f k8s/istio/

# Deploy monitoring
echo "Deploying monitoring stack..."
kubectl apply -f k8s/monitoring/

# Wait for deployments
echo "Waiting for deployments to be ready..."
kubectl wait --for=condition=available --timeout=300s \
  deployment/order-service \
  deployment/payment-gateway \
  -n progressive-delivery

echo "Waiting for monitoring..."
kubectl wait --for=condition=available --timeout=300s \
  deployment/prometheus \
  deployment/grafana \
  -n progressive-delivery

# Deploy Flagger canary
echo "Deploying Flagger canary configuration..."
kubectl apply -f k8s/canary/loadtester.yaml
kubectl apply -f k8s/canary/servicemonitor.yaml
kubectl apply -f k8s/canary/flagger-canary.yaml

echo ""
echo "✓ Deployment complete!"
echo ""
echo "Access points:"
echo "  Order Service: http://localhost/orders"
echo "  Grafana: http://localhost:30300"
echo "  Prometheus: kubectl port-forward -n progressive-delivery svc/prometheus 9090:9090"
echo ""
echo "Monitor canary status:"
echo "  kubectl get canary -n progressive-delivery -w"

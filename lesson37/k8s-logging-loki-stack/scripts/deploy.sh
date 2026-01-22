#!/bin/bash

set -euo pipefail

echo "Deploying Kubernetes Logging System..."

# Create namespace
kubectl apply -f k8s/namespace.yaml

echo "Waiting for namespace to be ready..."
sleep 2

# Deploy Loki
echo "Deploying Loki..."
kubectl apply -f k8s/base/loki/configmap.yaml
kubectl apply -f k8s/base/loki/statefulset.yaml

echo "Waiting for Loki to be ready..."
kubectl wait --for=condition=ready pod -l app=loki -n logging-system --timeout=120s || true
sleep 10

# Deploy Promtail
echo "Deploying Promtail..."
kubectl apply -f k8s/base/promtail/configmap.yaml
kubectl apply -f k8s/base/promtail/daemonset.yaml

# Deploy Grafana
echo "Deploying Grafana..."
kubectl apply -f k8s/base/grafana/configmap.yaml
kubectl apply -f k8s/base/grafana/deployment.yaml

echo "Waiting for Grafana to be ready..."
kubectl wait --for=condition=ready pod -l app=grafana -n logging-system --timeout=120s || true

# Deploy microservices
echo "Deploying microservices..."
kubectl apply -f k8s/base/api-gateway/deployment.yaml
kubectl apply -f k8s/base/order-service/deployment.yaml
kubectl apply -f k8s/base/payment-service/deployment.yaml

echo "Waiting for services to be ready..."
kubectl wait --for=condition=ready pod -l app=api-gateway -n logging-system --timeout=120s || true
kubectl wait --for=condition=ready pod -l app=order-service -n logging-system --timeout=120s || true
kubectl wait --for=condition=ready pod -l app=payment-service -n logging-system --timeout=120s || true

echo ""
echo "Deployment complete!"
echo ""
echo "Access points:"
echo "  Grafana UI: kubectl port-forward -n logging-system svc/grafana 3000:3000"
echo "  Loki API: kubectl port-forward -n logging-system svc/loki 3100:3100"
echo "  API Gateway: kubectl port-forward -n logging-system svc/api-gateway 8000:8000"
echo ""
echo "Grafana credentials:"
echo "  Username: admin"
echo "  Password: admin123"

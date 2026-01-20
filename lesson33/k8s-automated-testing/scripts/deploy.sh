#!/bin/bash

set -euo pipefail

echo "Deploying E-Commerce Platform..."

# Create namespace
kubectl apply -f k8s/base/namespace.yaml

# Apply RBAC
kubectl apply -f k8s/base/rbac.yaml

# Deploy services
kubectl apply -f k8s/base/redis.yaml
kubectl apply -f k8s/base/product-service.yaml
kubectl apply -f k8s/base/order-service.yaml
kubectl apply -f k8s/base/payment-service.yaml
kubectl apply -f k8s/base/test-results-aggregator.yaml

echo "Waiting for deployments to be ready..."
kubectl wait --for=condition=available --timeout=300s \
  deployment/product-service \
  deployment/order-service \
  deployment/payment-service \
  -n ecommerce

echo "✓ All services deployed successfully"

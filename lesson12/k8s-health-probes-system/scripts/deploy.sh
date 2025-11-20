#!/bin/bash
set -euo pipefail

echo "Deploying to Kubernetes..."

# Apply base manifests
kubectl apply -k k8s/base/

# Wait for infrastructure
echo "Waiting for infrastructure..."
kubectl wait --for=condition=ready pod -l app=redis -n log-analytics --timeout=120s
kubectl wait --for=condition=ready pod -l app=kafka -n log-analytics --timeout=120s

# Wait for services
echo "Waiting for services to be ready..."
kubectl wait --for=condition=ready pod -l app=log-collector -n log-analytics --timeout=180s
kubectl wait --for=condition=ready pod -l app=log-processor -n log-analytics --timeout=180s
kubectl wait --for=condition=ready pod -l app=analytics-api -n log-analytics --timeout=120s
kubectl wait --for=condition=ready pod -l app=frontend -n log-analytics --timeout=120s

echo "Deployment complete!"
kubectl get pods -n log-analytics

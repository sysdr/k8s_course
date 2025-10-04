#!/bin/bash
set -euo pipefail

echo "Deploying log aggregation system..."

# Apply base manifests
kubectl apply -f k8s/base/namespace.yaml
kubectl apply -f k8s/base/secrets.yaml
kubectl apply -f k8s/base/rbac.yaml
kubectl apply -f k8s/base/storage-class.yaml

# Deploy database and cache
kubectl apply -f k8s/base/timescaledb-statefulset.yaml
kubectl apply -f k8s/base/redis-deployment.yaml

# Wait for database to be ready
echo "Waiting for TimescaleDB to be ready..."
kubectl wait --for=condition=ready pod -l app=timescaledb -n log-system --timeout=300s

# Deploy application services
kubectl apply -f k8s/base/log-processor-statefulset.yaml
kubectl apply -f k8s/base/log-producer-deployment.yaml
kubectl apply -f k8s/base/frontend-deployment.yaml

# Apply autoscaling and policies
kubectl apply -f k8s/base/hpa.yaml
kubectl apply -f k8s/base/pdb.yaml
kubectl apply -f k8s/base/network-policy.yaml

echo "Deployment complete!"
echo "Waiting for pods to be ready..."
kubectl wait --for=condition=ready pod -l app=log-processor -n log-system --timeout=180s
kubectl wait --for=condition=ready pod -l app=log-producer -n log-system --timeout=180s
kubectl wait --for=condition=ready pod -l app=frontend -n log-system --timeout=180s

echo "All services are ready!"
kubectl get pods -n log-system

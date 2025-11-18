#!/bin/bash
set -euo pipefail

echo "Deploying log analytics platform to Kubernetes..."

# Create namespace
echo "Creating namespace..."
kubectl apply -f k8s/base/namespace.yaml

# Deploy all services
echo "Deploying services..."
kubectl apply -f k8s/base/
kubectl apply -f k8s/services/
kubectl apply -f k8s/networking/

# Wait for deployments
echo "Waiting for deployments to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment --all -n log-analytics

echo "Deployment complete!"
echo ""
echo "Access the application:"
echo "  Frontend:     http://localhost:30081"
echo "  API Gateway:  http://localhost:30080"
echo ""
echo "Check status:"
echo "  kubectl get pods -n log-analytics"
echo "  kubectl get svc -n log-analytics"

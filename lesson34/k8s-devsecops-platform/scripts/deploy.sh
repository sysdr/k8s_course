#!/bin/bash

set -euo pipefail

echo "Deploying DevSecOps platform..."

# Create namespace
kubectl apply -f k8s/base/namespace.yaml

# Apply security policies
echo "Applying security policies..."
kubectl apply -f k8s/security/

# Wait for Kyverno to process policies
sleep 5

# Apply network policies
echo "Applying network policies..."
kubectl apply -f k8s/network-policies/

# Apply base resources
echo "Deploying services..."
kubectl apply -f k8s/base/

# Wait for deployments
echo "Waiting for deployments to be ready..."
kubectl wait --for=condition=available --timeout=300s \
  deployment --all -n devsecops

echo "Deployment complete!"
echo ""
echo "Access the application:"
echo "  Frontend: http://localhost"
echo "  API Gateway: http://localhost:8000"
echo ""
echo "Get service status:"
echo "  kubectl get pods -n devsecops"

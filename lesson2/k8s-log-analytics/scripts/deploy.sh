#!/bin/bash
set -euo pipefail

echo "Deploying Log Analytics Platform to Kubernetes..."

# Apply Kubernetes manifests
echo "Applying Kubernetes manifests..."
kubectl apply -f k8s/base/

echo "Waiting for deployments to be ready..."
kubectl wait --for=condition=available --timeout=300s \
    deployment/redis \
    deployment/api-service \
    deployment/frontend \
    deployment/log-processor \
    -n log-analytics

echo ""
echo "✓ Deployment complete!"
echo ""
echo "Access the application:"
echo "  Frontend: kubectl port-forward -n log-analytics svc/frontend 3000:3000"
echo "  API: kubectl port-forward -n log-analytics svc/api-service 8000:8000"
echo ""
echo "View logs:"
echo "  kubectl logs -n log-analytics -l app=api-service -f"
echo ""
echo "Check pod status:"
echo "  kubectl get pods -n log-analytics"

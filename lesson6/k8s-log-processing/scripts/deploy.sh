#!/bin/bash
set -euo pipefail

echo "Deploying to Kubernetes..."
kubectl apply -f kubernetes/base/
kubectl apply -f istio/
kubectl apply -f monitoring/

kubectl wait --for=condition=available --timeout=300s deployment --all -n log-processing

echo "Deployment complete!"
echo "Access: kubectl port-forward -n log-processing svc/log-ingestion-api 8080:8000"

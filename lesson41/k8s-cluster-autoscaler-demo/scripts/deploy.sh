#!/bin/bash
set -euo pipefail

echo "Deploying infrastructure components..."
kubectl apply -f k8s/base/redis.yaml
kubectl apply -f k8s/base/kafka.yaml

echo "Waiting for infrastructure to be ready..."
kubectl wait --for=condition=Ready pod -l app=redis -n log-platform --timeout=300s
kubectl wait --for=condition=Ready pod -l app=kafka -n log-platform --timeout=300s

echo "Deploying application services..."
kubectl apply -f k8s/base/log-ingestion.yaml
kubectl apply -f k8s/base/log-processor.yaml
kubectl apply -f k8s/base/analytics-api.yaml
kubectl apply -f k8s/base/frontend.yaml

echo "Deploying autoscaling resources..."
kubectl apply -f k8s/autoscaling/

echo "Waiting for application pods to be ready..."
kubectl wait --for=condition=Ready pod -l app=log-ingestion -n log-platform --timeout=300s

echo "Deployment complete!"
echo ""
echo "Access the application:"
echo "  Frontend: http://localhost (once LoadBalancer is ready)"
echo ""
echo "Check status:"
echo "  kubectl get pods -n log-platform"

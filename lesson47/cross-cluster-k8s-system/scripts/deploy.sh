#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

echo "Deploying cross-cluster logging system (project root: $PROJECT_ROOT)..."

# Deploy to Cluster A
echo "Deploying to Cluster A..."
kubectl config use-context kind-cluster-a
kubectl apply -f cluster-a/k8s/base/namespace.yaml
kubectl apply -f infrastructure/kafka/
kubectl apply -f infrastructure/redis/
kubectl apply -f cluster-a/k8s/base/

echo "Waiting for Cluster A LoadBalancer..."
kubectl wait --for=condition=ready pod -l app=log-ingestion -n logging --timeout=300s

# Get LoadBalancer IP
LOADBALANCER_IP=$(kubectl get svc log-ingestion-lb -n logging -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
echo "Cluster A LoadBalancer IP: $LOADBALANCER_IP"

# Deploy to Cluster B
echo "Deploying to Cluster B..."
kubectl config use-context kind-cluster-b
kubectl apply -f cluster-b/k8s/base/namespace.yaml
kubectl apply -f infrastructure/postgres/
kubectl apply -f cluster-b/k8s/base/

# Update Cluster B config with LoadBalancer IP and restart pods to pick up new config
kubectl patch configmap log-processor-config -n logging \
    -p "{\"data\":{\"cluster_a_url\":\"http://$LOADBALANCER_IP:8000\"}}"
kubectl rollout restart deployment/log-processor -n logging --context kind-cluster-b 2>/dev/null || true

echo "Deployment complete!"
echo "Cluster A LoadBalancer: http://$LOADBALANCER_IP:8000"

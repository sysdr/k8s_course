#!/bin/bash
set -euo pipefail

echo "Deploying Pod Security Standards Log Platform..."

# Create namespaces with Pod Security Standards labels
echo "Creating namespaces with security policies..."
kubectl apply -f kubernetes/namespaces/

# Wait for namespaces to be ready
sleep 2

# Deploy supporting infrastructure
echo "Deploying Redis..."
kubectl apply -f kubernetes/logs-public/redis-deployment.yaml

# Wait for Redis to be ready
kubectl wait --for=condition=Ready pod -l app=redis -n logs-public --timeout=120s

# Deploy services
echo "Deploying log services..."
kubectl apply -f kubernetes/logs-public/log-ingestion-deployment.yaml
kubectl apply -f kubernetes/logs-payment/log-processor-deployment.yaml
kubectl apply -f kubernetes/logs-public/log-query-deployment.yaml

# Deploy frontend
echo "Deploying security dashboard..."
kubectl apply -f kubernetes/logs-public/security-dashboard-deployment.yaml

# Deploy RBAC
echo "Configuring RBAC..."
kubectl apply -f kubernetes/logs-public/rbac.yaml

# Deploy network policies
echo "Applying network policies..."
kubectl apply -f kubernetes/logs-payment/network-policy.yaml

echo "Waiting for all pods to be ready..."
kubectl wait --for=condition=Ready pod --all -n logs-public --timeout=300s
kubectl wait --for=condition=Ready pod --all -n logs-payment --timeout=300s

echo "Deployment complete!"
echo ""
echo "Service endpoints:"
kubectl get svc -n logs-public
echo ""
echo "Pod status:"
kubectl get pods --all-namespaces -l security-policy
echo ""
echo "Pod Security Standards:"
kubectl get namespaces -L pod-security.kubernetes.io/enforce

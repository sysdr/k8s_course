#!/bin/bash
set -euo pipefail

NAMESPACE="log-platform"

echo "Deploying log platform to Kubernetes..."

# Create namespace
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Deploy infrastructure
echo "Deploying infrastructure components..."
kubectl apply -f infrastructure/kafka/ -n $NAMESPACE
kubectl apply -f infrastructure/postgresql/ -n $NAMESPACE
kubectl apply -f infrastructure/redis/ -n $NAMESPACE

# Wait for infrastructure
echo "Waiting for infrastructure to be ready..."
sleep 30

# Deploy application
echo "Deploying application components..."
# Apply all resources except VPA files first
find k8s/base/ -type f -name "*.yaml" ! -name "*vpa*.yaml" -exec kubectl apply -f {} -n $NAMESPACE \;

# Conditionally deploy VPA if CRD is available
if kubectl get crd verticalpodautoscalers.autoscaling.k8s.io &> /dev/null; then
    echo "VPA CRD found, deploying VPA resources..."
    find k8s/base/ -type f -name "*vpa*.yaml" -exec kubectl apply -f {} -n $NAMESPACE \;
else
    echo "VPA CRD not found, skipping VPA deployment"
fi

# Deploy monitoring
echo "Deploying monitoring stack..."
kubectl apply -f monitoring/prometheus/ -n $NAMESPACE
kubectl apply -f monitoring/grafana/ -n $NAMESPACE
kubectl apply -f monitoring/jaeger/ -n $NAMESPACE

# Deploy Istio configuration
if kubectl get namespace istio-system &> /dev/null; then
    echo "Deploying Istio configuration..."
    kubectl apply -f istio/ -n $NAMESPACE
fi

echo "Deployment complete!"
echo "Check status with: kubectl get pods -n $NAMESPACE"

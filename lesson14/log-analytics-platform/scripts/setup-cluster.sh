#!/bin/bash
set -euo pipefail

echo "Setting up local Kubernetes cluster..."

# Check if kind is installed
if ! command -v kind &> /dev/null; then
    echo "kind not found. Please install kind: https://kind.sigs.k8s.io/docs/user/quick-start/#installation"
    exit 1
fi

# Create kind cluster
kind create cluster --name log-analytics --config - <<CLUSTER_CONFIG
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  extraPortMappings:
  - containerPort: 30080
    hostPort: 30080
    protocol: TCP
  - containerPort: 30090
    hostPort: 30090
    protocol: TCP
  - containerPort: 30030
    hostPort: 30030
    protocol: TCP
CLUSTER_CONFIG

# Load images into kind
echo "Loading Docker images into kind cluster..."
kind load docker-image log-ingester:1.0.0 --name log-analytics
kind load docker-image query-api:1.0.0 --name log-analytics
kind load docker-image aggregator:1.0.0 --name log-analytics
kind load docker-image frontend:1.0.0 --name log-analytics

echo "Cluster setup complete!"
kubectl cluster-info --context kind-log-analytics

#!/bin/bash
set -euo pipefail

echo "Setting up local Kubernetes cluster..."

# Check if kind is installed
if ! command -v kind &> /dev/null; then
    echo "kind is not installed. Please install kind first:"
    echo "https://kind.sigs.k8s.io/docs/user/quick-start/#installation"
    exit 1
fi

# Create kind cluster
echo "Creating kind cluster..."
kind create cluster --name log-analytics --config - <<CLUSTER_CONFIG
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  extraPortMappings:
  - containerPort: 30000
    hostPort: 30000
    protocol: TCP
- role: worker
- role: worker
CLUSTER_CONFIG

echo "Cluster created successfully!"
kubectl cluster-info --context kind-log-analytics

# Load images into kind cluster
echo "Loading images into cluster..."
kind load docker-image api-service:latest --name log-analytics
kind load docker-image frontend:latest --name log-analytics
kind load docker-image log-processor:latest --name log-analytics

echo "✓ Cluster setup complete!"

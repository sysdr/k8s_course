#!/bin/bash
set -euo pipefail

echo "Setting up local Kubernetes cluster..."

# Check if kind is installed
if ! command -v kind &> /dev/null; then
    echo "Error: kind is not installed. Install from https://kind.sigs.k8s.io/"
    exit 1
fi

# Create kind cluster
cat <<KINDEOF | kind create cluster --name log-platform --config=-
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  extraPortMappings:
  - containerPort: 30000
    hostPort: 8000
  - containerPort: 30080
    hostPort: 8080
- role: worker
- role: worker
KINDEOF

echo "✓ Cluster created"

# Load images into kind
echo "Loading Docker images into kind cluster..."
kind load docker-image log-ingest:latest --name log-platform
kind load docker-image log-parser:latest --name log-platform
kind load docker-image analytics-engine:latest --name log-platform
kind load docker-image frontend:latest --name log-platform

echo "✓ Images loaded into cluster"

# Install metrics-server (required for HPA)
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
kubectl patch deployment metrics-server -n kube-system --type='json' \
  -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--kubelet-insecure-tls"}]'

echo "✓ Metrics server installed"
echo ""
echo "Cluster ready! Run './scripts/deploy.sh' to deploy the application"

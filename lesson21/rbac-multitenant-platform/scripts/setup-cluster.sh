#!/bin/bash
set -euo pipefail

echo "Setting up local Kubernetes cluster..."

# Check if kind is installed
if ! command -v kind &> /dev/null; then
    echo "kind is not installed. Please install it first:"
    echo "https://kind.sigs.k8s.io/docs/user/quick-start/#installation"
    exit 1
fi

# Check if cluster already exists
if kind get clusters 2>/dev/null | grep -q "rbac-platform"; then
    echo "Cluster 'rbac-platform' already exists."
    read -p "Do you want to delete and recreate it? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        kind delete cluster --name rbac-platform
    else
        echo "Using existing cluster."
        exit 0
    fi
fi

# Create kind cluster
cat <<KINDCONFIG | kind create cluster --name rbac-platform --config=-
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  kubeadmConfigPatches:
  - |
    kind: InitConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        node-labels: "ingress-ready=true"
  extraPortMappings:
  - containerPort: 80
    hostPort: 80
    protocol: TCP
  - containerPort: 443
    hostPort: 443
    protocol: TCP
- role: worker
- role: worker
KINDCONFIG

echo ""
echo "✓ Cluster created successfully!"
echo ""
echo "Loading Docker images into kind cluster..."

# Load images
kind load docker-image log-processor:latest --name rbac-platform || true
kind load docker-image analytics-api:latest --name rbac-platform || true
kind load docker-image audit-service:latest --name rbac-platform || true
kind load docker-image rbac-validator:latest --name rbac-platform || true
kind load docker-image rbac-frontend:latest --name rbac-platform || true

echo ""
echo "✓ Setup complete!"
echo ""
echo "Cluster info:"
kubectl cluster-info --context kind-rbac-platform

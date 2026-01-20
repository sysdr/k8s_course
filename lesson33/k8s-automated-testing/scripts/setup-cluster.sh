#!/bin/bash

set -euo pipefail

echo "Setting up Kubernetes cluster..."

# Check if kind is installed
if ! command -v kind &> /dev/null; then
    echo "kind not found. Installing..."
    curl -Lo ./kind https://kind.sigs.k8s.io/dl/latest/kind-linux-amd64
    chmod +x ./kind
    sudo mv ./kind /usr/local/bin/kind
fi

# Create kind cluster
if kind get clusters | grep -q "ecommerce-testing"; then
    echo "Cluster already exists. Deleting..."
    kind delete cluster --name ecommerce-testing
fi

echo "Creating new cluster..."
cat <<CLUSTER_CONFIG | kind create cluster --name ecommerce-testing --config=-
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
CLUSTER_CONFIG

echo "✓ Cluster created successfully"

# Load images into kind
echo "Loading images into kind cluster..."
kind load docker-image product-service:latest --name ecommerce-testing
kind load docker-image order-service:latest --name ecommerce-testing
kind load docker-image payment-service:latest --name ecommerce-testing
kind load docker-image test-results-aggregator:latest --name ecommerce-testing
kind load docker-image test-runner:latest --name ecommerce-testing

echo "✓ Images loaded"

#!/bin/bash
set -euo pipefail

echo "Setting up local Kubernetes cluster..."

# Check if kind is installed
if ! command -v kind &> /dev/null; then
    echo "kind not found. Installing kind..."
    curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
    chmod +x ./kind
    sudo mv ./kind /usr/local/bin/kind
fi

# Create kind cluster with specific configuration
cat <<EOL | kind create cluster --name pod-security-demo --config=-
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  kubeadmConfigPatches:
  - |
    kind: ClusterConfiguration
    apiServer:
      extraArgs:
        "feature-gates": "PodSecurity=true"
- role: worker
- role: worker
EOL

echo "Cluster created successfully!"

# Wait for nodes to be ready
kubectl wait --for=condition=Ready nodes --all --timeout=300s

echo "Cluster is ready!"
kubectl get nodes

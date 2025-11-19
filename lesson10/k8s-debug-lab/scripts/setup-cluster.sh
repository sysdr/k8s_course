#!/bin/bash
set -euo pipefail

echo "Setting up local Kubernetes cluster for debugging lab..."

# Check if kind is installed
if ! command -v kind &> /dev/null; then
    echo "Installing kind..."
    curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
    chmod +x ./kind
    sudo mv ./kind /usr/local/bin/kind
fi

# Check if cluster exists
if kind get clusters | grep -q "debug-lab"; then
    echo "Cluster 'debug-lab' already exists"
else
    # Create cluster with multiple nodes
    cat << 'CLUSTER_CONFIG' | kind create cluster --name debug-lab --config=-
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
- role: worker
  kubeadmConfigPatches:
  - |
    kind: JoinConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        node-labels: "node-type=general"
- role: worker
  kubeadmConfigPatches:
  - |
    kind: JoinConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        node-labels: "node-type=general"
- role: worker
  kubeadmConfigPatches:
  - |
    kind: JoinConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        node-labels: "node-type=general"
CLUSTER_CONFIG
fi

# Add taint to one node for debugging exercise
echo "Adding taint to worker node for debugging exercise..."
kubectl taint nodes debug-lab-worker3 dedicated=analytics:NoSchedule --overwrite || true

echo "Cluster setup complete!"
kubectl get nodes

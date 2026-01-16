#!/bin/bash
set -euo pipefail

echo "Setting up local Kubernetes cluster..."

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if kind is installed, use local binary if available
if command -v kind &> /dev/null; then
    KIND_CMD="kind"
elif [ -f "${SCRIPT_DIR}/kind" ]; then
    KIND_CMD="${SCRIPT_DIR}/kind"
    chmod +x "${KIND_CMD}"
else
    echo "Installing kind..."
    curl -Lo "${SCRIPT_DIR}/kind" https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
    chmod +x "${SCRIPT_DIR}/kind"
    KIND_CMD="${SCRIPT_DIR}/kind"
fi

# Check if cluster already exists
if ${KIND_CMD} get clusters 2>/dev/null | grep -q "gitops-argocd"; then
    echo "Cluster 'gitops-argocd' already exists. Skipping creation."
    kubectl cluster-info --context kind-gitops-argocd
    exit 0
fi

# Create kind cluster
cat <<CLUSTER_CONFIG | ${KIND_CMD} create cluster --name gitops-argocd --config=-
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
    hostPort: 30080
    protocol: TCP
  - containerPort: 443
    hostPort: 30443
    protocol: TCP
- role: worker
- role: worker
CLUSTER_CONFIG

echo "Cluster created successfully!"
kubectl cluster-info

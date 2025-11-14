#!/bin/bash
set -euo pipefail

CLUSTER_NAME="log-processing-cluster"

echo "Setting up local Kubernetes cluster with kind..."

# Check if kind is installed
if ! command -v kind &> /dev/null; then
    echo "Error: kind is not installed. Please install from https://kind.sigs.k8s.io/"
    exit 1
fi

# Create cluster config
cat > /tmp/kind-config.yaml << YAML
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
YAML

# Create cluster
kind create cluster --name $CLUSTER_NAME --config /tmp/kind-config.yaml

# Load Docker images into kind
echo "Loading Docker images into kind cluster..."
kind load docker-image ingestion-api:latest --name $CLUSTER_NAME
kind load docker-image analytics-engine:latest --name $CLUSTER_NAME
kind load docker-image analytics-engine-init:latest --name $CLUSTER_NAME
kind load docker-image dashboard:latest --name $CLUSTER_NAME

echo "✓ Cluster setup complete!"
echo "Cluster name: $CLUSTER_NAME"
echo "Nodes:"
kubectl get nodes

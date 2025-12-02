#!/bin/bash
set -euo pipefail

echo "=== Setting up local Kubernetes cluster ==="

# Check if kind is installed
if ! command -v kind &> /dev/null; then
    echo "Error: kind is not installed. Please install from https://kind.sigs.k8s.io/"
    exit 1
fi

# Create cluster
echo "Creating kind cluster..."
kind create cluster --name log-analytics --config - <<CLUSTER_CONFIG
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
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

# Install metrics server
echo "Installing metrics server..."
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
kubectl patch deployment metrics-server -n kube-system --type='json' -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--kubelet-insecure-tls"}]'

echo "✓ Metrics server installed"

echo ""
echo "Cluster setup complete!"
echo "Run: kubectl cluster-info"

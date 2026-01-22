#!/bin/bash

set -euo pipefail

echo "Setting up local Kubernetes cluster..."

# Check if kind is installed
if ! command -v kind &> /dev/null; then
    echo "kind not found. Installing..."
    curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
    chmod +x ./kind
    sudo mv ./kind /usr/local/bin/kind
fi

# Create kind cluster
echo "Creating kind cluster 'logging-demo'..."
cat <<CLUSTER_CONFIG | kind create cluster --name logging-demo --config=-
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
- role: worker
- role: worker
CLUSTER_CONFIG

# Load images into kind
echo "Loading images into kind cluster..."
kind load docker-image api-gateway:latest --name logging-demo
kind load docker-image order-service:latest --name logging-demo
kind load docker-image payment-service:latest --name logging-demo

echo "Cluster setup complete!"
echo "Cluster name: logging-demo"
echo ""
echo "Next steps:"
echo "  1. Run: ./scripts/deploy.sh"
echo "  2. Access Grafana: kubectl port-forward -n logging-system svc/grafana 3000:3000"

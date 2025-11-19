#!/bin/bash
set -euo pipefail

CLUSTER_NAME="log-analytics"

echo "Setting up local Kubernetes cluster..."

# Check if kind is installed
if ! command -v kind &> /dev/null; then
    echo "Installing kind..."
    curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
    chmod +x ./kind
    sudo mv ./kind /usr/local/bin/kind
fi

# Create cluster config
cat > /tmp/kind-config.yaml << 'KINDEOF'
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  extraPortMappings:
  - containerPort: 30080
    hostPort: 80
  - containerPort: 30443
    hostPort: 443
- role: worker
- role: worker
KINDEOF

# Create cluster
if kind get clusters | grep -q "^${CLUSTER_NAME}$"; then
    echo "Cluster ${CLUSTER_NAME} already exists"
else
    kind create cluster --name $CLUSTER_NAME --config /tmp/kind-config.yaml
fi

# Load images into cluster
echo "Loading images into cluster..."
kind load docker-image log-collector:latest --name $CLUSTER_NAME || true
kind load docker-image log-processor:latest --name $CLUSTER_NAME || true
kind load docker-image log-api:latest --name $CLUSTER_NAME || true
kind load docker-image log-frontend:latest --name $CLUSTER_NAME || true

echo "Cluster setup complete!"
kubectl cluster-info --context kind-$CLUSTER_NAME

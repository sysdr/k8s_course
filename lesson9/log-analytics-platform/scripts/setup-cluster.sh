#!/bin/bash
set -euo pipefail

echo "Setting up local Kubernetes cluster for log analytics platform..."

# Check if kind is installed
if ! command -v kind &> /dev/null; then
    echo "kind not found. Please install kind: https://kind.sigs.k8s.io/docs/user/quick-start/#installation"
    exit 1
fi

# Create kind cluster
echo "Creating kind cluster..."
cat <<EOK | kind create cluster --name log-analytics --config=-
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
  - containerPort: 30080
    hostPort: 30080
    protocol: TCP
  - containerPort: 30081
    hostPort: 30081
    protocol: TCP
- role: worker
- role: worker
EOK

echo "Cluster created successfully!"
echo "Waiting for nodes to be ready..."
kubectl wait --for=condition=Ready nodes --all --timeout=300s

echo "Installing metrics-server..."
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
kubectl patch deployment metrics-server -n kube-system --type='json' -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--kubelet-insecure-tls"}]'

echo "Cluster setup complete!"
echo "Run './scripts/deploy.sh' to deploy the application"

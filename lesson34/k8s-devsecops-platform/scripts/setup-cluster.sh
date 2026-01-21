#!/bin/bash

set -euo pipefail

echo "Setting up local Kubernetes cluster..."

# Check if kind is installed
if ! command -v kind &> /dev/null; then
    echo "Installing kind..."
    curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
    chmod +x ./kind
    sudo mv ./kind /usr/local/bin/kind
fi

# Create cluster
echo "Creating kind cluster..."
cat <<EOT | kind create cluster --name devsecops-cluster --config=-
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
EOT

echo "Cluster created successfully"

# Install Kyverno
echo "Installing Kyverno..."
kubectl create namespace kyverno || true
kubectl apply -f https://github.com/kyverno/kyverno/releases/download/v1.11.0/install.yaml

echo "Waiting for Kyverno to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/kyverno -n kyverno

# Install metrics server
echo "Installing metrics server..."
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Patch metrics server for kind
kubectl patch deployment metrics-server -n kube-system --type='json' \
  -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--kubelet-insecure-tls"}]'

echo "Cluster setup complete!"
echo "Run 'kubectl cluster-info' to verify"

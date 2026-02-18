#!/bin/bash
set -euo pipefail

echo "🎯 Setting up local Kubernetes cluster..."

# Check if kind is installed
if ! command -v kind &> /dev/null; then
    echo "❌ kind not found. Installing..."
    curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
    chmod +x ./kind
    sudo mv ./kind /usr/local/bin/kind
fi

# Create cluster
echo "🏗️  Creating kind cluster..."
cat <<CLUSTERCONFIG | kind create cluster --name log-platform --config=-
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
CLUSTERCONFIG

# Load images into kind
echo "📦 Loading images into cluster..."
kind load docker-image log-ingestion:latest --name log-platform
kind load docker-image log-processor:latest --name log-platform
kind load docker-image analytics-api:latest --name log-platform
kind load docker-image frontend:latest --name log-platform

# Install metrics server
echo "📊 Installing metrics-server..."
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Patch metrics server for kind
kubectl patch deployment metrics-server -n kube-system --type='json' \
  -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--kubelet-insecure-tls"}]'

echo "✅ Cluster setup complete!"
kubectl get nodes

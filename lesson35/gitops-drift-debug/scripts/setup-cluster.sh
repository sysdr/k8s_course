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
if kind get clusters | grep -q "gitops-drift"; then
    echo "Cluster 'gitops-drift' already exists"
else
    echo "Creating kind cluster..."
    cat <<EOF | kind create cluster --name gitops-drift --config=-
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
EOF
fi

# Create namespaces
echo "Creating namespaces..."
kubectl create namespace production --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -

echo "Cluster setup complete!"

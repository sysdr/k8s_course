#!/bin/bash
set -euo pipefail

echo "Setting up local Kubernetes cluster..."

# Check for kind or minikube
if command -v kind &> /dev/null; then
    echo "Using kind..."
    kind create cluster --name log-platform --config - <<KINDEOF
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
- role: worker
- role: worker
- role: worker
KINDEOF
elif command -v minikube &> /dev/null; then
    echo "Using minikube..."
    minikube start --cpus=4 --memory=8192 --nodes=3
else
    echo "Please install kind or minikube"
    exit 1
fi

echo "Cluster setup complete!"
kubectl cluster-info

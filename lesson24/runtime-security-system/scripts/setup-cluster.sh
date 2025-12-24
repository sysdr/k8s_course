#!/bin/bash
set -euo pipefail

echo "Setting up local Kubernetes cluster..."

if command -v kind &> /dev/null; then
    echo "Using kind..."
    kind create cluster --name runtime-security --config - <<KINDEOF
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
- role: worker
- role: worker
KINDEOF
elif command -v minikube &> /dev/null; then
    echo "Using minikube..."
    minikube start --nodes 3 --cpus 4 --memory 8192
else
    echo "Error: Neither kind nor minikube found. Please install one."
    exit 1
fi

echo "✓ Cluster created successfully"

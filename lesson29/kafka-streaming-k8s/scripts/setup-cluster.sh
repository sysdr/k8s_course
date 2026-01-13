#!/bin/bash
set -euo pipefail

echo "Setting up Kubernetes cluster..."

# Create namespace
kubectl apply -f k8s/base/namespace.yaml

# Wait for namespace
kubectl wait --for=condition=Active namespace/kafka-pipeline --timeout=30s || true

echo "Namespace created successfully"

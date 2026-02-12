#!/bin/bash
set -euo pipefail

echo "Creating kind cluster..."
kind create cluster --config infrastructure/kind-config.yaml

echo "Waiting for cluster to be ready..."
kubectl wait --for=condition=Ready nodes --all --timeout=300s

echo "Creating namespace..."
kubectl create namespace log-platform --dry-run=client -o yaml | kubectl apply -f -

echo "Cluster setup complete"

#!/bin/bash
set -euo pipefail

echo "Cleaning up Kubernetes resources..."

kubectl delete namespace log-platform --ignore-not-found=true

if command -v kind &> /dev/null; then
    kind delete cluster --name log-platform
elif command -v minikube &> /dev/null; then
    minikube delete
fi

echo "Cleanup complete!"

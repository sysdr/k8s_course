#!/bin/bash
set -euo pipefail

echo "Cleaning up resources..."

echo "Deleting namespace..."
kubectl delete namespace log-platform --ignore-not-found=true

echo "Deleting kind cluster..."
kind delete cluster --name log-platform-cluster

echo "Cleanup complete"

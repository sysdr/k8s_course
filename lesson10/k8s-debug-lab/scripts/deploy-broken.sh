#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Deploying broken Kubernetes scenarios..."

# Create namespace
kubectl apply -f "${PROJECT_ROOT}/k8s/base/namespace.yaml"

# Deploy broken scheduling scenarios
echo ""
echo "Deploying broken scheduling scenarios..."
kubectl apply -f "${PROJECT_ROOT}/k8s/broken-scheduling/"

# Deploy broken networking scenarios
echo ""
echo "Deploying broken networking scenarios..."
kubectl apply -f "${PROJECT_ROOT}/k8s/broken-networking/"

echo ""
echo "=========================================="
echo "Broken scenarios deployed!"
echo "=========================================="
echo ""
echo "Check Pod status with:"
echo "  kubectl get pods -n log-processor"
echo ""
echo "Debug specific Pods with:"
echo "  kubectl describe pod <pod-name> -n log-processor"
echo ""
echo "Check events with:"
echo "  kubectl get events -n log-processor --sort-by='.lastTimestamp'"

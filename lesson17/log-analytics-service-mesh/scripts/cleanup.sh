#!/bin/bash
set -euo pipefail

echo "=== Cleaning up resources ==="

echo "Deleting namespace..."
kubectl delete namespace log-analytics --ignore-not-found

echo "Deleting kind cluster..."
kind delete cluster --name log-analytics

echo "✓ Cleanup complete"

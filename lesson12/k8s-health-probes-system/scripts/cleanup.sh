#!/bin/bash
set -euo pipefail

echo "Cleaning up..."

# Delete namespace
kubectl delete namespace log-analytics --ignore-not-found=true

# Delete kind cluster if exists
kind delete cluster --name health-probes 2>/dev/null || true

echo "Cleanup complete"

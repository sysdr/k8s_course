#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
cd "$BASE_DIR"

echo "Cleaning up FinOps platform..."

kubectl delete -f kubernetes/autoscaling/ || true
kubectl delete -f kubernetes/applications/ --all || true
kubectl delete -f kubernetes/monitoring/ --all || true
kubectl delete -f kubernetes/base/quotas/ || true
kubectl delete -f kubernetes/base/namespaces/ || true

echo "Cleanup complete!"

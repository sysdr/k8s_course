#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
cd "$BASE_DIR"
echo "Deploy: kubectl apply -k k8s/base/ (ensure cluster and images exist)"
kubectl apply -k k8s/base/ 2>/dev/null || echo "kubectl not configured or k8s/base missing"

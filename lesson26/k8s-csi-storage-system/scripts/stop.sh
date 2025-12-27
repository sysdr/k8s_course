#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "Stopping Log Analytics System..."

kubectl delete -f "${BASE_DIR}/k8s/apps/" --ignore-not-found=true
kubectl delete -f "${BASE_DIR}/k8s/rbac/" --ignore-not-found=true
kubectl delete -f "${BASE_DIR}/k8s/storage/classes/" --ignore-not-found=true

echo "System stopped."

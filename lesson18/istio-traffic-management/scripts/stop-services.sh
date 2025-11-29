#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
K8S_DIR="${PROJECT_ROOT}/k8s/base"

log_info() {
    echo "[INFO] $1"
}

log_info "Stopping all services..."

kubectl delete -f "${K8S_DIR}/frontend-deployment.yaml" || true
kubectl delete -f "${K8S_DIR}/api-gateway-service.yaml" || true
kubectl delete -f "${K8S_DIR}/api-gateway-v3-deployment.yaml" || true
kubectl delete -f "${K8S_DIR}/api-gateway-v2-deployment.yaml" || true
kubectl delete -f "${K8S_DIR}/api-gateway-v1-deployment.yaml" || true
kubectl delete -f "${K8S_DIR}/rate-limiter-deployment.yaml" || true
kubectl delete -f "${K8S_DIR}/analytics-deployment.yaml" || true
kubectl delete -f "${K8S_DIR}/redis-deployment.yaml" || true

log_info "All services stopped!"

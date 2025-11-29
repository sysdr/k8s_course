#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
K8S_DIR="${PROJECT_ROOT}/k8s/base"

log_info() {
    echo "[INFO] $1"
}

log_error() {
    echo "[ERROR] $1" >&2
}

log_info "Starting all services..."

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    log_error "kubectl is not installed or not in PATH"
    exit 1
fi

# Apply manifests in order
log_info "Deploying Redis..."
kubectl apply -f "${K8S_DIR}/redis-deployment.yaml"

log_info "Waiting for Redis to be ready..."
kubectl wait --for=condition=ready pod -l app=redis --timeout=60s || true

log_info "Deploying Analytics Service..."
kubectl apply -f "${K8S_DIR}/analytics-deployment.yaml"

log_info "Deploying Rate Limiter..."
kubectl apply -f "${K8S_DIR}/rate-limiter-deployment.yaml"

log_info "Waiting for supporting services..."
sleep 5

log_info "Deploying API Gateway v1..."
kubectl apply -f "${K8S_DIR}/api-gateway-v1-deployment.yaml"

log_info "Deploying API Gateway v2..."
kubectl apply -f "${K8S_DIR}/api-gateway-v2-deployment.yaml"

log_info "Deploying API Gateway v3..."
kubectl apply -f "${K8S_DIR}/api-gateway-v3-deployment.yaml"

log_info "Deploying API Gateway Service..."
kubectl apply -f "${K8S_DIR}/api-gateway-service.yaml"

log_info "Deploying Frontend..."
kubectl apply -f "${K8S_DIR}/frontend-deployment.yaml"

log_info "Waiting for all pods to be ready..."
kubectl wait --for=condition=ready pod -l app=api-gateway --timeout=120s || true
kubectl wait --for=condition=ready pod -l app=frontend --timeout=60s || true

log_info "All services started!"
kubectl get pods

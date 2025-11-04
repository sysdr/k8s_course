#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

log_info() { echo -e "\033[0;32m[INFO]\033[0m $1"; }
log_error() { echo -e "\033[0;31m[ERROR]\033[0m $1" >&2; }

log_info "Starting Kubernetes Log Processing System"

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    log_error "kubectl is not installed. Please install kubectl first."
    exit 1
fi

# Check if cluster is accessible
if ! kubectl cluster-info &>/dev/null; then
    log_error "Kubernetes cluster is not accessible. Please ensure your cluster is running."
    log_info "To start a local cluster, you can use:"
    log_info "  - minikube start"
    log_info "  - kind create cluster"
    log_info "  - k3d cluster create"
    exit 1
fi

# Check if namespace exists
if ! kubectl get namespace log-processor &>/dev/null; then
    log_info "Creating namespace..."
    kubectl apply -f k8s/base/namespace.yaml
fi

# Deploy Redis
log_info "Deploying Redis..."
kubectl apply -f k8s/base/redis-deployment.yaml

# Wait for Redis
log_info "Waiting for Redis to be ready..."
kubectl wait --for=condition=ready pod -l app=redis -n log-processor --timeout=60s || true

# Deploy services
log_info "Deploying log ingestion..."
kubectl apply -f k8s/base/log-ingestion-deployment.yaml

log_info "Deploying log analytics..."
kubectl apply -f k8s/base/log-analytics-deployment.yaml

log_info "Deploying dashboard..."
kubectl apply -f k8s/base/dashboard-deployment.yaml

log_info "Waiting for services to be ready..."
sleep 10

log_info "System startup complete!"
log_info "Dashboard available at: kubectl port-forward -n log-processor svc/dashboard-service 8080:80"

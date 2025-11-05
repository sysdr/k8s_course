#!/bin/bash
set -euo pipefail

# Comprehensive startup script for the log platform
# This script orchestrates the entire deployment and startup process

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    log_error "kubectl is not installed. Please install it first."
    exit 1
fi

# Check if docker is available
if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed. Please install it first."
    exit 1
fi

# Check for existing cluster
log_info "Checking for Kubernetes cluster..."
if ! kubectl cluster-info &> /dev/null; then
    log_warning "No Kubernetes cluster found. Setting up cluster..."
    if [ -f "$SCRIPT_DIR/setup-cluster.sh" ]; then
        bash "$SCRIPT_DIR/setup-cluster.sh"
    else
        log_error "setup-cluster.sh not found"
        exit 1
    fi
else
    log_info "Kubernetes cluster is available"
fi

# Check for duplicate services
log_info "Checking for duplicate services..."
NAMESPACE="log-platform"
EXISTING_PODS=$(kubectl get pods -n "$NAMESPACE" 2>/dev/null | wc -l || echo "0")
if [ "$EXISTING_PODS" -gt 1 ]; then
    log_warning "Found existing pods in namespace $NAMESPACE"
    kubectl get pods -n "$NAMESPACE"
    read -p "Do you want to clean up existing deployment? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Cleaning up existing deployment..."
        kubectl delete namespace "$NAMESPACE" --ignore-not-found=true
        sleep 5
    fi
fi

# Build Docker images
log_info "Building Docker images..."
if [ -f "$SCRIPT_DIR/build.sh" ]; then
    bash "$SCRIPT_DIR/build.sh"
else
    log_error "build.sh not found"
    exit 1
fi

# Load images into cluster (for kind/minikube)
if kubectl get nodes -o jsonpath='{.items[0].spec.taints[?(@.key=="node-role.kubernetes.io/control-plane")]}' &> /dev/null; then
    log_info "Loading images into cluster..."
    if command -v kind &> /dev/null; then
        kind load docker-image log-ingestion:latest log-processor:latest frontend:latest 2>/dev/null || true
    elif command -v minikube &> /dev/null; then
        minikube image load log-ingestion:latest log-processor:latest frontend:latest 2>/dev/null || true
    fi
fi

# Deploy to Kubernetes
log_info "Deploying to Kubernetes..."
if [ -f "$SCRIPT_DIR/deploy.sh" ]; then
    bash "$SCRIPT_DIR/deploy.sh"
else
    log_error "deploy.sh not found"
    exit 1
fi

# Wait for deployments to be ready
log_info "Waiting for deployments to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/log-ingestion -n "$NAMESPACE" || log_warning "log-ingestion deployment not ready"
kubectl wait --for=condition=available --timeout=300s deployment/log-processor -n "$NAMESPACE" || log_warning "log-processor deployment not ready"
kubectl wait --for=condition=available --timeout=300s deployment/frontend -n "$NAMESPACE" || log_warning "frontend deployment not ready"

# Check pod status
log_info "Checking pod status..."
kubectl get pods -n "$NAMESPACE"

# Setup port forwarding in background
log_info "Setting up port forwarding..."
log_info "Port forwarding will run in the background. Use 'pkill -f port-forward' to stop them."

# Kill existing port forwards
pkill -f "kubectl port-forward.*log-platform" || true
sleep 2

# Start port forwarding
kubectl port-forward -n "$NAMESPACE" svc/log-ingestion 8000:8000 > /dev/null 2>&1 &
kubectl port-forward -n "$NAMESPACE" svc/frontend 3000:80 > /dev/null 2>&1 &
kubectl port-forward -n "$NAMESPACE" svc/grafana 3001:3000 > /dev/null 2>&1 &
kubectl port-forward -n "$NAMESPACE" svc/prometheus 9090:9090 > /dev/null 2>&1 &

sleep 3

log_info "=========================================="
log_info "Startup Complete!"
log_info "=========================================="
log_info "Services are available at:"
log_info "  - Frontend Dashboard: http://localhost:3000"
log_info "  - Log Ingestion API: http://localhost:8000"
log_info "  - Grafana: http://localhost:3001 (admin/admin123)"
log_info "  - Prometheus: http://localhost:9090"
log_info ""
log_info "To generate demo data, run:"
log_info "  cd $PROJECT_DIR"
log_info "  bash scripts/demo.sh"
log_info ""
log_info "To stop port forwarding:"
log_info "  pkill -f 'kubectl port-forward.*log-platform'"
log_info "=========================================="


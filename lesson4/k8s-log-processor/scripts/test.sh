#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

log_info() { echo -e "\033[0;32m[INFO]\033[0m $1"; }
log_error() { echo -e "\033[0;31m[ERROR]\033[0m $1" >&2; }
log_warn() { echo -e "\033[1;33m[WARN]\033[0m $1"; }

log_info "Running tests..."

# Check if kubectl and cluster are available
if ! command -v kubectl &> /dev/null; then
    log_error "kubectl is not installed"
    exit 1
fi

if ! kubectl cluster-info &>/dev/null; then
    log_warn "Kubernetes cluster is not accessible. Tests require a running cluster."
    log_info "To start a local cluster: kind create cluster"
    exit 1
fi

# Test 1: Check if services are running
log_info "Test 1: Checking services..."
if kubectl get deployment -n log-processor log-ingestion &>/dev/null; then
    log_info "✓ log-ingestion deployment exists"
else
    log_error "✗ log-ingestion deployment missing"
    exit 1
fi

if kubectl get deployment -n log-processor log-analytics &>/dev/null; then
    log_info "✓ log-analytics deployment exists"
else
    log_error "✗ log-analytics deployment missing"
    exit 1
fi

if kubectl get deployment -n log-processor dashboard &>/dev/null; then
    log_info "✓ dashboard deployment exists"
else
    log_error "✗ dashboard deployment missing"
    exit 1
fi

# Test 2: Check pod health
log_info "Test 2: Checking pod health..."
INGESTION_READY=$(kubectl get deployment -n log-processor log-ingestion -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
if [ "$INGESTION_READY" -gt 0 ]; then
    log_info "✓ log-ingestion pods ready: $INGESTION_READY"
else
    log_error "✗ log-ingestion pods not ready"
    exit 1
fi

# Test 3: Test ingestion endpoint
log_info "Test 3: Testing ingestion endpoint..."
INGESTION_POD=$(kubectl get pod -n log-processor -l app=log-ingestion -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
if [ -n "$INGESTION_POD" ]; then
    if kubectl exec -n log-processor "$INGESTION_POD" -- curl -s http://localhost:8000/health | grep -q healthy; then
        log_info "✓ ingestion health check passed"
    else
        log_error "✗ ingestion health check failed"
        exit 1
    fi
fi

# Test 4: Test analytics endpoint
log_info "Test 4: Testing analytics endpoint..."
ANALYTICS_POD=$(kubectl get pod -n log-processor -l app=log-analytics -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
if [ -n "$ANALYTICS_POD" ]; then
    if kubectl exec -n log-processor "$ANALYTICS_POD" -- curl -s http://localhost:8001/health | grep -q healthy; then
        log_info "✓ analytics health check passed"
    else
        log_error "✗ analytics health check failed"
        exit 1
    fi
fi

log_info "All tests passed!"

#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

log_info() { echo -e "\033[0;32m[INFO]\033[0m $1"; }
log_error() { echo -e "\033[0;31m[ERROR]\033[0m $1" >&2; }
log_warn() { echo -e "\033[1;33m[WARN]\033[0m $1"; }

log_info "Checking for duplicate services..."

if ! command -v kubectl &> /dev/null; then
    log_error "kubectl is not installed"
    exit 1
fi

if ! kubectl cluster-info &>/dev/null; then
    log_warn "Kubernetes cluster is not accessible. Skipping duplicate check."
    exit 0
fi

# Check for duplicate deployments
duplicates=0
for namespace in log-processor default kube-system; do
    if kubectl get namespace "$namespace" &>/dev/null; then
        deployments=$(kubectl get deployments -n "$namespace" -o jsonpath='{.items[*].metadata.name}' 2>/dev/null || echo "")
        for dep in $deployments; do
            count=$(kubectl get deployment "$dep" -n "$namespace" -o jsonpath='{.spec.replicas}' 2>/dev/null || echo "0")
            if [ "$count" -gt 10 ]; then
                log_warn "Deployment $dep in namespace $namespace has $count replicas (possibly a duplicate)"
                duplicates=$((duplicates + 1))
            fi
        done
    fi
done

# Check for multiple pods with same labels
for namespace in log-processor default; do
    if kubectl get namespace "$namespace" &>/dev/null; then
        for app in log-ingestion log-analytics dashboard; do
            pod_count=$(kubectl get pods -n "$namespace" -l app="$app" --no-headers 2>/dev/null | wc -l)
            expected=$(kubectl get deployment "$app" -n "$namespace" -o jsonpath='{.spec.replicas}' 2>/dev/null || echo "0")
            if [ "$pod_count" -gt "$expected" ] && [ "$expected" -gt 0 ]; then
                log_warn "Found $pod_count pods for app=$app, expected $expected (possible duplicates)"
                duplicates=$((duplicates + 1))
            fi
        done
    fi
done

if [ "$duplicates" -eq 0 ]; then
    log_info "No duplicate services detected"
else
    log_warn "Found $duplicates potential duplicate service(s)"
fi

exit 0


#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

log_info() { echo -e "\033[0;32m[INFO]\033[0m $1"; }
log_error() { echo -e "\033[0;31m[ERROR]\033[0m $1" >&2; }
log_warn() { echo -e "\033[1;33m[WARN]\033[0m $1"; }

log_info "Validating dashboard metrics and demo..."

if ! command -v kubectl &> /dev/null; then
    log_error "kubectl is not installed"
    exit 1
fi

if ! kubectl cluster-info &>/dev/null; then
    log_warn "Kubernetes cluster is not accessible. Cannot validate dashboard."
    exit 1
fi

# Check if dashboard is running
if ! kubectl get deployment -n log-processor dashboard &>/dev/null; then
    log_error "Dashboard deployment not found"
    exit 1
fi

DASHBOARD_POD=$(kubectl get pod -n log-processor -l app=dashboard -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
if [ -z "$DASHBOARD_POD" ]; then
    log_error "Dashboard pod not found"
    exit 1
fi

# Check if analytics service is accessible
ANALYTICS_POD=$(kubectl get pod -n log-processor -l app=log-analytics -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
if [ -z "$ANALYTICS_POD" ]; then
    log_error "Analytics pod not found"
    exit 1
fi

# Test analytics endpoint
log_info "Testing analytics endpoint..."
ANALYTICS_RESPONSE=$(kubectl exec -n log-processor "$ANALYTICS_POD" -- python3 -c "import urllib.request; import json; response = urllib.request.urlopen('http://localhost:8001/analytics/summary'); print(response.read().decode())" 2>/dev/null || echo "")
if [ -z "$ANALYTICS_RESPONSE" ]; then
    log_error "Analytics endpoint not responding"
    exit 1
fi

# Check if metrics are non-zero or have data
TOTAL_LOGS=$(echo "$ANALYTICS_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('total_logs', 0))" 2>/dev/null || echo "0")

if [ "$TOTAL_LOGS" -eq 0 ]; then
    log_warn "No logs found in analytics. Running demo to generate logs..."
    # Run demo script
    "$SCRIPT_DIR/demo.sh" || log_warn "Demo script failed, but continuing..."
    sleep 5
    
    # Check again
    ANALYTICS_RESPONSE=$(kubectl exec -n log-processor "$ANALYTICS_POD" -- python3 -c "import urllib.request; import json; response = urllib.request.urlopen('http://localhost:8001/analytics/summary'); print(response.read().decode())" 2>/dev/null || echo "")
    TOTAL_LOGS=$(echo "$ANALYTICS_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('total_logs', 0))" 2>/dev/null || echo "0")
fi

if [ "$TOTAL_LOGS" -gt 0 ]; then
    log_info "✓ Dashboard metrics are updating: $TOTAL_LOGS total logs"
    
    # Check for level distribution
    LEVELS=$(echo "$ANALYTICS_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data.get('by_level', {})))" 2>/dev/null || echo "0")
    if [ "$LEVELS" -gt 0 ]; then
        log_info "✓ Level distribution available: $LEVELS level(s)"
    fi
    
    # Check for source distribution
    SOURCES=$(echo "$ANALYTICS_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data.get('by_source', {})))" 2>/dev/null || echo "0")
    if [ "$SOURCES" -gt 0 ]; then
        log_info "✓ Source distribution available: $SOURCES source(s)"
    fi
    
    log_info "✓ Dashboard validation passed!"
else
    log_error "Dashboard metrics are still zero. Demo may not be working correctly."
    exit 1
fi


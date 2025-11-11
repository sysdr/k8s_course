#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$BASE_DIR" || exit 1

echo "Starting Log Processing System..."

# Check if services are already running
if kubectl get namespace log-processing &>/dev/null; then
    echo "Namespace log-processing already exists. Checking for running services..."
    
    RUNNING_PODS=$(kubectl get pods -n log-processing --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l)
    if [ "$RUNNING_PODS" -gt 0 ]; then
        echo "Warning: Found $RUNNING_PODS running pods in log-processing namespace"
        echo "Checking for duplicate services..."
        kubectl get pods -n log-processing
    fi
fi

# Run setup-cluster.sh if cluster doesn't exist
if ! kind get clusters | grep -q "log-processing"; then
    echo "Cluster not found. Running setup-cluster.sh..."
    "$SCRIPT_DIR/setup-cluster.sh"
fi

# Build images
echo "Building Docker images..."
"$SCRIPT_DIR/build.sh"

# Deploy
echo "Deploying to Kubernetes..."
"$SCRIPT_DIR/deploy.sh"

# Wait for services to be ready
echo "Waiting for all services to be ready..."
kubectl wait --for=condition=ready pod --all -n log-processing --timeout=300s || true

# Check for duplicate services
echo ""
echo "Checking for duplicate services..."
DUPLICATES=$(kubectl get pods -n log-processing -o json | jq -r '.items[] | select(.status.phase=="Running") | .metadata.name' | sort | uniq -d)
if [ -n "$DUPLICATES" ]; then
    echo "Warning: Found duplicate running services:"
    echo "$DUPLICATES"
else
    echo "✓ No duplicate services found"
fi

echo ""
echo "Startup complete!"
echo ""
echo "To access services:"
echo "  API: kubectl port-forward -n log-processing svc/log-ingestion-api 8080:8000"
echo "  Dashboard: kubectl port-forward -n log-processing svc/analytics-dashboard 3000:80"
echo "  Prometheus: kubectl port-forward -n monitoring svc/prometheus 9090:9090"
echo "  Grafana: kubectl port-forward -n monitoring svc/grafana 3001:3000"

#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "Running tests..."

# Test producer health
PRODUCER_POD=$(kubectl get pods -n kafka-pipeline -l app=producer -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
if [ -n "$PRODUCER_POD" ]; then
    echo "Testing producer health..."
    kubectl exec -n kafka-pipeline "$PRODUCER_POD" -- curl -s http://localhost:8000/health || echo "Producer health check failed"
fi

# Test API health
API_POD=$(kubectl get pods -n kafka-pipeline -l app=api -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
if [ -n "$API_POD" ]; then
    echo "Testing API health..."
    kubectl exec -n kafka-pipeline "$API_POD" -- curl -s http://localhost:8002/health || echo "API health check failed"
fi

# Check pod status
echo "Checking pod status..."
kubectl get pods -n kafka-pipeline

echo "Tests completed"

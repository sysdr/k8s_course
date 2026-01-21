#!/bin/bash

set -euo pipefail

echo "Running integration tests..."

API_GATEWAY_URL="http://localhost:8000"

# Test health endpoints
echo "Testing health endpoints..."

for service in "api-gateway:8000" "auth-service:8001" "log-processor:8002" "analytics-service:8003"; do
    service_name=$(echo $service | cut -d: -f1)
    port=$(echo $service | cut -d: -f2)
    
    kubectl port-forward -n devsecops svc/$service_name $port:$port &
    PID=$!
    sleep 2
    
    if curl -sf "http://localhost:$port/health" > /dev/null; then
        echo "✓ $service_name health check passed"
    else
        echo "✗ $service_name health check failed"
        kill $PID 2>/dev/null || true
        exit 1
    fi
    
    kill $PID 2>/dev/null || true
done

echo "All tests passed!"

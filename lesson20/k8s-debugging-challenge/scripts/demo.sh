#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NAMESPACE="debugging-challenge"

echo "🎬 Running E-Commerce Demo..."
echo "============================="

# Function to generate traffic
generate_traffic() {
    local service=$1
    local endpoint=$2
    local count=${3:-10}
    
    echo "Generating ${count} requests to ${service}${endpoint}..."
    
    for i in $(seq 1 ${count}); do
        kubectl run curl-${service}-${i} --rm -i --restart=Never \
            --image=curlimages/curl:latest \
            -n ${NAMESPACE} \
            -- curl -s -o /dev/null -w "%{http_code}" \
            http://${service}:8080${endpoint} 2>/dev/null || echo "000" &
    done
    wait
}

# Check if backend is ready
echo "Checking backend readiness..."
if ! kubectl wait --for=condition=ready pod -l app=backend -n ${NAMESPACE} --timeout=60s 2>/dev/null; then
    echo "⚠️  Backend pods not ready. Waiting..."
    sleep 10
fi

# Generate traffic to various endpoints
echo ""
echo "📊 Generating metrics..."

# Health checks
echo "  - Health checks..."
generate_traffic "backend-service" "/health" 5

# Products endpoint
echo "  - Product catalog requests..."
generate_traffic "backend-service" "/products" 20

# Individual products
echo "  - Individual product requests..."
for i in 1 2 3 4 5; do
    kubectl run curl-product-${i} --rm -i --restart=Never \
        --image=curlimages/curl:latest \
        -n ${NAMESPACE} \
        -- curl -s -o /dev/null http://backend-service:8080/products/${i} 2>/dev/null || true &
done
wait

# Metrics endpoint
echo "  - Metrics endpoint requests..."
generate_traffic "backend-service" "/metrics" 5

# Root endpoint
echo "  - Root endpoint requests..."
generate_traffic "backend-service" "/" 5

echo ""
echo "✅ Demo complete! Metrics should be updated."
echo ""
echo "📊 Check metrics:"
echo "  kubectl port-forward -n ${NAMESPACE} svc/backend-service 8080:8080"
echo "  curl http://localhost:8080/metrics"
echo ""
echo "📈 Check Prometheus (if deployed):"
echo "  kubectl port-forward -n ${NAMESPACE} svc/prometheus-service 9090:9090"
echo "  Open http://localhost:9090 in browser"

#!/bin/bash
set -euo pipefail

API_URL="${API_URL:-http://localhost:8080}"

echo "Testing Log Ingestion API..."

# Test health endpoint
echo "Testing /health endpoint..."
if curl -f -s "${API_URL}/health" > /dev/null; then
    echo "✓ Health check passed"
else
    echo "✗ Health check failed"
    exit 1
fi

# Test readiness endpoint
echo "Testing /ready endpoint..."
if curl -f -s "${API_URL}/ready" > /dev/null; then
    echo "✓ Readiness check passed"
else
    echo "✗ Readiness check failed"
    exit 1
fi

# Test log ingestion
echo "Testing log ingestion..."
for i in {1..10}; do
    LEVEL=$((RANDOM % 5))
    case $LEVEL in
        0) LEVEL="DEBUG" ;;
        1) LEVEL="INFO" ;;
        2) LEVEL="WARNING" ;;
        3) LEVEL="ERROR" ;;
        4) LEVEL="CRITICAL" ;;
    esac
    
    RESPONSE=$(curl -s -X POST "${API_URL}/api/v1/logs" \
        -H "Content-Type: application/json" \
        -d "{\"level\":\"${LEVEL}\",\"service\":\"test-service\",\"message\":\"Test log message ${i}\",\"metadata\":{\"test\":true}}")
    
    if echo "$RESPONSE" | grep -q "accepted"; then
        echo "✓ Log ${i} ingested successfully (${LEVEL})"
    else
        echo "✗ Log ${i} ingestion failed"
        exit 1
    fi
    
    sleep 0.5
done

# Test metrics endpoint
echo "Testing /metrics endpoint..."
if curl -f -s "${API_URL}/metrics" | grep -q "logs_ingested_total"; then
    echo "✓ Metrics endpoint working"
else
    echo "✗ Metrics endpoint not working correctly"
    exit 1
fi

echo ""
echo "All tests passed!"

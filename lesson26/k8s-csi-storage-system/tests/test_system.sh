#!/bin/bash
set -euo pipefail

API_URL="${API_URL:-http://localhost:30080}"
FAILED=0

test_endpoint() {
    local endpoint=$1
    local expected_status=$2
    local name=$3
    
    echo "Testing $name..."
    status=$(curl -s -o /dev/null -w "%{http_code}" "${API_URL}${endpoint}" || echo "000")
    
    if [ "$status" = "$expected_status" ]; then
        echo "✓ $name passed"
    else
        echo "✗ $name failed (got $status, expected $expected_status)"
        FAILED=1
    fi
}

test_metrics() {
    echo "Testing metrics endpoint..."
    response=$(curl -s "${API_URL}/metrics" || echo "{}")
    
    if echo "$response" | grep -q "total_logs"; then
        echo "✓ Metrics endpoint returns valid data"
    else
        echo "✗ Metrics endpoint failed"
        FAILED=1
    fi
}

test_endpoint "/health" "200" "Health check"
test_metrics

if [ $FAILED -eq 0 ]; then
    echo "All tests passed!"
    exit 0
else
    echo "Some tests failed!"
    exit 1
fi
